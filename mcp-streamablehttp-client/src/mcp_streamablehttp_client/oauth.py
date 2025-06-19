"""OAuth client implementation with device flow support."""
import asyncio
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode

import httpx
from jose import jwt
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import Settings

logger = logging.getLogger(__name__)
console = Console()


class OAuthClient:
    """OAuth 2.0 client with device flow and dynamic registration support."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = httpx.AsyncClient(verify=settings.verify_ssl)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def ensure_authenticated(self) -> str:
        """
        Ensure we have a valid access token, performing OAuth flow if needed.
        
        Returns:
            str: Valid access token
        """
        # Load any stored credentials
        self.settings.load_credentials()
        
        # Discover OAuth endpoints if not already discovered
        if not self.settings.oauth_token_url:
            console.print("\n[cyan]Discovering OAuth configuration...[/cyan]")
            await self.discover_oauth_configuration()
        
        # Check if we have valid credentials
        if self.settings.has_valid_credentials():
            logger.info("Using existing valid access token")
            return self.settings.oauth_access_token
        
        # Check if we need to refresh token
        if self.settings.oauth_refresh_token and not self.settings.has_valid_credentials():
            logger.info("Access token expired, attempting refresh")
            try:
                await self.refresh_token()
                if self.settings.has_valid_credentials():
                    return self.settings.oauth_access_token
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
        
        # Need to perform full OAuth flow
        console.print("\n[yellow]OAuth authentication required[/yellow]")
        
        # Check if we need client registration
        if self.settings.needs_registration():
            console.print("Registering OAuth client...")
            await self.register_client()
        
        # Perform device flow authentication
        console.print("Starting device authorization flow...")
        await self.device_flow_auth()
        
        # Save credentials for future use
        self.settings.save_credentials()
        
        return self.settings.oauth_access_token
    
    async def register_client(self) -> None:
        """Register a new OAuth client using dynamic registration (RFC 7591)."""
        if not self.settings.oauth_registration_url:
            raise ValueError(
                "OAuth server does not support dynamic client registration. "
                "Please register a client manually and provide credentials."
            )
        
        registration_data = {
            "client_name": self.settings.client_name,
            "client_version": self.settings.client_version,
            "grant_types": ["urn:ietf:params:oauth:grant-type:device_code", "refresh_token"],
            "response_types": ["code"],
            "scope": "read write",
            "token_endpoint_auth_method": "client_secret_basic"
        }
        
        try:
            response = await self.client.post(
                self.settings.oauth_registration_url,
                json=registration_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            self.settings.oauth_client_id = data["client_id"]
            self.settings.oauth_client_secret = data.get("client_secret")
            
            console.print(f"[green]✓[/green] Client registered: {data['client_id']}")
            logger.info(f"Registered OAuth client: {data['client_id']}")
            
        except httpx.HTTPError as e:
            logger.error(f"Client registration failed: {e}")
            raise RuntimeError(f"Failed to register OAuth client: {e}")
    
    async def device_flow_auth(self) -> None:
        """Perform OAuth device flow authentication."""
        if not self.settings.oauth_device_auth_url:
            # Fall back to authorization code flow with manual steps
            await self.manual_auth_flow()
            return
        
        if not self.settings.oauth_token_url:
            raise ValueError("OAuth token endpoint not discovered")
        
        # Step 1: Request device code
        device_data = await self.request_device_code()
        
        # Step 2: Display user code and instructions
        self.display_device_code(device_data)
        
        # Step 3: Poll for authorization
        await self.poll_for_token(device_data)
    
    async def request_device_code(self) -> Dict[str, Any]:
        """Request a device code from the authorization server."""
        data = {
            "client_id": self.settings.oauth_client_id,
            "scope": "read write"
        }
        
        response = await self.client.post(
            self.settings.oauth_device_auth_url,
            data=data
        )
        response.raise_for_status()
        
        return response.json()
    
    def display_device_code(self, device_data: Dict[str, Any]) -> None:
        """Display device code and instructions to user."""
        user_code = device_data.get("user_code", "")
        verification_uri = device_data.get("verification_uri", "")
        
        console.print("\n")
        console.print(Panel.fit(
            f"[bold cyan]Please visit:[/bold cyan]\n{verification_uri}\n\n"
            f"[bold cyan]And enter code:[/bold cyan]\n[bold yellow]{user_code}[/bold yellow]",
            title="Device Authorization",
            border_style="cyan"
        ))
        console.print("\n")
    
    async def poll_for_token(self, device_data: Dict[str, Any]) -> None:
        """Poll authorization server for access token."""
        device_code = device_data["device_code"]
        interval = device_data.get("interval", 5)
        expires_in = device_data.get("expires_in", 600)
        
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
            "client_id": self.settings.oauth_client_id
        }
        
        if self.settings.oauth_client_secret:
            data["client_secret"] = self.settings.oauth_client_secret
        
        start_time = time.time()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Waiting for authorization...", total=None)
            
            while time.time() - start_time < expires_in:
                try:
                    response = await self.client.post(
                        self.settings.oauth_token_url,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        token_data = response.json()
                        self.save_tokens(token_data)
                        progress.update(task, description="[green]✓[/green] Authorization successful!")
                        console.print("\n[green]Authentication completed successfully![/green]")
                        return
                    
                    error_data = response.json()
                    error = error_data.get("error", "")
                    
                    if error == "authorization_pending":
                        # Still waiting for user authorization
                        await asyncio.sleep(interval)
                    elif error == "slow_down":
                        # Increase polling interval
                        interval += 5
                        await asyncio.sleep(interval)
                    else:
                        # Other error
                        raise RuntimeError(f"Device flow error: {error}")
                        
                except httpx.HTTPError as e:
                    logger.error(f"Token polling error: {e}")
                    await asyncio.sleep(interval)
        
        raise RuntimeError("Device authorization timed out")
    
    async def manual_auth_flow(self) -> None:
        """Fallback manual authorization flow."""
        if not self.settings.oauth_authorization_url:
            raise ValueError(
                "OAuth server does not support device flow or authorization code flow. "
                "Please check server configuration."
            )
        
        # Generate PKCE values
        code_verifier = secrets.token_urlsafe(64)
        
        # Build authorization URL
        auth_params = {
            "response_type": "code",
            "client_id": self.settings.oauth_client_id,
            "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
            "scope": "read write",
            "state": secrets.token_urlsafe(16)
        }
        
        auth_url = f"{self.settings.oauth_authorization_url}?{urlencode(auth_params)}"
        
        console.print("\n")
        console.print(Panel.fit(
            f"[bold cyan]Please visit this URL to authorize:[/bold cyan]\n\n{auth_url}",
            title="Manual Authorization",
            border_style="cyan"
        ))
        
        # Wait for user to paste authorization code
        console.print("\n")
        auth_code = console.input("[bold cyan]Enter authorization code:[/bold cyan] ")
        
        # Exchange code for token
        await self.exchange_code_for_token(auth_code, code_verifier)
    
    async def exchange_code_for_token(self, code: str, code_verifier: str) -> None:
        """Exchange authorization code for access token."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
            "client_id": self.settings.oauth_client_id,
            "code_verifier": code_verifier
        }
        
        if self.settings.oauth_client_secret:
            data["client_secret"] = self.settings.oauth_client_secret
        
        response = await self.client.post(
            self.settings.oauth_token_url,
            data=data
        )
        response.raise_for_status()
        
        token_data = response.json()
        self.save_tokens(token_data)
        
        console.print("[green]✓[/green] Token exchange successful!")
    
    async def refresh_token(self) -> None:
        """Refresh the access token using refresh token."""
        if not self.settings.oauth_refresh_token:
            raise ValueError("No refresh token available")
        
        if not self.settings.oauth_token_url:
            raise ValueError("OAuth token endpoint not discovered")
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.settings.oauth_refresh_token,
            "client_id": self.settings.oauth_client_id
        }
        
        if self.settings.oauth_client_secret:
            data["client_secret"] = self.settings.oauth_client_secret
        
        response = await self.client.post(
            self.settings.oauth_token_url,
            data=data
        )
        response.raise_for_status()
        
        token_data = response.json()
        self.save_tokens(token_data)
        
        logger.info("Successfully refreshed access token")
    
    def save_tokens(self, token_data: Dict[str, Any]) -> None:
        """Save tokens from OAuth response."""
        self.settings.oauth_access_token = token_data["access_token"]
        
        if "refresh_token" in token_data:
            self.settings.oauth_refresh_token = token_data["refresh_token"]
        
        # Calculate expiration time
        expires_in = token_data.get("expires_in", 3600)
        self.settings.oauth_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Save to persistent storage
        self.settings.save_credentials()
    
    async def discover_oauth_configuration(self) -> None:
        """Discover OAuth configuration from the MCP server."""
        # First, try to get OAuth info from MCP server's auth challenge
        auth_info = await self._probe_mcp_auth_requirements()
        
        if auth_info and "oauth_metadata_url" in auth_info:
            # Use the metadata URL from auth challenge
            metadata_url = auth_info["oauth_metadata_url"]
        else:
            # Try well-known location based on issuer
            if auth_info and "issuer" in auth_info:
                issuer = auth_info["issuer"].rstrip("/")
                metadata_url = f"{issuer}/.well-known/oauth-authorization-server"
            else:
                # Extract base domain from MCP URL and try common patterns
                from urllib.parse import urlparse
                parsed = urlparse(self.settings.mcp_server_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                
                # Try different well-known locations
                candidates = [
                    f"{base_url}/.well-known/oauth-authorization-server",
                    f"{base_url}/.well-known/openid-configuration",
                    f"{base_url.replace('mcp-', 'auth-')}/.well-known/oauth-authorization-server",
                    f"{parsed.scheme}://auth.{parsed.netloc}/.well-known/oauth-authorization-server",
                ]
                
                metadata_url = None
                for candidate in candidates:
                    try:
                        response = await self.client.get(candidate)
                        if response.status_code == 200:
                            metadata_url = candidate
                            break
                    except Exception:
                        continue
                
                if not metadata_url:
                    raise RuntimeError(
                        "Could not discover OAuth configuration. "
                        "Please check if the server supports OAuth 2.0 metadata discovery."
                    )
        
        # Fetch metadata
        try:
            response = await self.client.get(metadata_url)
            response.raise_for_status()
            metadata = response.json()
            
            # Update settings with discovered endpoints
            self.settings.oauth_metadata_url = metadata_url
            self.settings.oauth_issuer = metadata.get("issuer")
            self.settings.oauth_authorization_url = metadata.get("authorization_endpoint")
            self.settings.oauth_token_url = metadata.get("token_endpoint")
            self.settings.oauth_device_auth_url = metadata.get("device_authorization_endpoint")
            self.settings.oauth_registration_url = metadata.get("registration_endpoint")
            
            # Validate required endpoints
            if not self.settings.oauth_token_url:
                raise ValueError("OAuth metadata missing required token_endpoint")
            
            if not self.settings.oauth_authorization_url and not self.settings.oauth_device_auth_url:
                raise ValueError("OAuth metadata missing both authorization_endpoint and device_authorization_endpoint")
            
            console.print(f"[green]✓[/green] Discovered OAuth configuration from {metadata_url}")
            logger.info(f"OAuth endpoints discovered: issuer={self.settings.oauth_issuer}")
            
            # Save discovered endpoints for offline use
            self.settings.save_credentials()
            
        except Exception as e:
            logger.error(f"Failed to discover OAuth metadata from {metadata_url}: {e}")
            raise RuntimeError(f"OAuth discovery failed: {e}")
    
    async def _probe_mcp_auth_requirements(self) -> Optional[Dict[str, Any]]:
        """Probe MCP server to discover auth requirements from 401 response."""
        try:
            # Make unauthenticated request to trigger 401
            response = await self.client.post(
                self.settings.mcp_server_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {
                            "name": self.settings.client_name,
                            "version": self.settings.client_version
                        }
                    },
                    "id": "probe-auth"
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 401:
                # Parse WWW-Authenticate header
                www_auth = response.headers.get("WWW-Authenticate", "")
                auth_info = self._parse_www_authenticate(www_auth)
                
                # Also check for Link header with metadata
                link_header = response.headers.get("Link", "")
                if "rel=\"oauth-authorization-server\"" in link_header:
                    # Extract URL from Link header
                    import re
                    match = re.search(r'<([^>]+)>.*rel="oauth-authorization-server"', link_header)
                    if match:
                        auth_info["oauth_metadata_url"] = match.group(1)
                
                return auth_info
                
        except Exception as e:
            logger.debug(f"Auth probe failed: {e}")
        
        return None
    
    def _parse_www_authenticate(self, header: str) -> Dict[str, str]:
        """Parse WWW-Authenticate header for OAuth parameters."""
        auth_info = {}
        
        # Basic parsing of Bearer auth-param format
        if header.startswith("Bearer "):
            params_str = header[7:]
            # Parse key="value" pairs
            import re
            for match in re.finditer(r'(\w+)="([^"]+)"', params_str):
                key, value = match.groups()
                auth_info[key] = value
        
        return auth_info