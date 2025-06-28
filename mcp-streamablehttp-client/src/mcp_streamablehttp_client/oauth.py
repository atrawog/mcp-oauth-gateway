"""OAuth client implementation using Authlib."""

import asyncio
import logging
import secrets
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Any
from urllib.parse import urlparse

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn

from .config import Settings


logger = logging.getLogger(__name__)
console = Console()


class OAuthClient:
    """OAuth 2.0 client using Authlib."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.http_client = httpx.AsyncClient(verify=settings.verify_ssl)
        self.oauth_client = None
        self._setup_oauth_client()

    def _setup_oauth_client(self):
        """Initialize Authlib OAuth client with current settings."""
        if self.settings.oauth_client_id:
            self.oauth_client = AsyncOAuth2Client(
                client_id=self.settings.oauth_client_id,
                client_secret=self.settings.oauth_client_secret,
                token_endpoint=self.settings.oauth_token_url,
                authorization_endpoint=self.settings.oauth_authorization_url,
                token=self._get_current_token(),
                update_token=self._update_token,
            )

    def _get_current_token(self) -> dict[str, Any] | None:
        """Get current token in Authlib format."""
        if not self.settings.oauth_access_token:
            return None

        token = {
            "access_token": self.settings.oauth_access_token,
            "token_type": "Bearer",
        }

        if self.settings.oauth_refresh_token:
            token["refresh_token"] = self.settings.oauth_refresh_token

        if self.settings.oauth_token_expires_at:
            token["expires_at"] = self.settings.oauth_token_expires_at.timestamp()

        return token

    def _update_token(self, token: dict[str, Any]) -> None:
        """Update token callback for Authlib."""
        self.settings.oauth_access_token = token["access_token"]

        if "refresh_token" in token:
            self.settings.oauth_refresh_token = token["refresh_token"]

        # Calculate expiration time
        if "expires_at" in token:
            self.settings.oauth_token_expires_at = datetime.fromtimestamp(token["expires_at"], tz=UTC)
        elif "expires_in" in token:
            self.settings.oauth_token_expires_at = datetime.now(UTC) + timedelta(seconds=token["expires_in"])

        # Update settings to reflect new values
        self.settings.oauth_access_token = token["access_token"]
        if "refresh_token" in token:
            self.settings.oauth_refresh_token = token["refresh_token"]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()
        if self.oauth_client:
            await self.oauth_client.aclose()

    async def ensure_authenticated(self) -> str:
        """Ensure we have a valid access token, performing OAuth flow if needed.

        Returns:
            str: Valid access token

        """
        # NO CREDENTIAL FILES! Everything comes from .env as commanded!

        # Discover OAuth endpoints if not already discovered
        if not self.settings.oauth_token_url:
            console.print("\n[cyan]Discovering OAuth configuration...[/cyan]")
            await self.discover_oauth_configuration()

        # Check if we have valid credentials
        if self.settings.has_valid_credentials():
            logger.info("Using existing valid access token")
            return self.settings.oauth_access_token

        # Check if we need to refresh token
        if self.settings.oauth_refresh_token:
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

        # Setup OAuth client after registration
        self._setup_oauth_client()

        # Perform authentication flow
        if self.settings.oauth_device_auth_url:
            console.print("Starting device authorization flow...")
            await self.device_flow_auth()
        else:
            console.print("Starting authorization code flow...")
            await self.manual_auth_flow()

        return self.settings.oauth_access_token

    async def register_client(self) -> None:
        """Register a new OAuth client using dynamic registration (RFC 7591)."""
        if not self.settings.oauth_registration_url:
            raise ValueError(
                "OAuth server does not support dynamic client registration. "
                "Please register a client manually and provide credentials.",
            )

        registration_data = {
            "client_name": self.settings.client_name,
            "application_type": "native",
            "grant_types": [
                "authorization_code",
                "refresh_token",
                "urn:ietf:params:oauth:grant-type:device_code",
            ],
            "response_types": ["code"],
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
            "token_endpoint_auth_method": "client_secret_post",
            "scope": "read write",
        }

        try:
            # Perform client registration - should be public per RFC 7591
            response = await self.http_client.post(
                self.settings.oauth_registration_url,
                json=registration_data,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            data = response.json()
            self.settings.oauth_client_id = data["client_id"]
            self.settings.oauth_client_secret = data.get("client_secret")

            # Save RFC 7592 management credentials
            if "registration_access_token" in data:
                self.settings.registration_access_token = data["registration_access_token"]
                logger.info("Saved registration_access_token for client management")

            if "registration_client_uri" in data:
                self.settings.registration_client_uri = data["registration_client_uri"]
                logger.info(f"Saved registration_client_uri: {data['registration_client_uri']}")

            console.print(f"[green]✓[/green] Client registered: {data['client_id']}")
            logger.info(f"Registered OAuth client: {data['client_id']}")

            # Client credentials are now set in settings

        except httpx.HTTPError as e:
            logger.error(f"Client registration failed: {e}")
            raise RuntimeError(f"Failed to register OAuth client: {e}") from e

    async def device_flow_auth(self) -> None:
        """Perform OAuth device flow authentication using Authlib."""
        if not self.oauth_client:
            raise ValueError("OAuth client not initialized")

        # Step 1: Request device code
        device_data = await self._request_device_code()

        # Step 2: Display user code and instructions
        self._display_device_code(device_data)

        # Step 3: Poll for authorization
        await self._poll_for_device_token(device_data)

    async def _request_device_code(self) -> dict[str, Any]:
        """Request device code using Authlib."""
        response = await self.http_client.post(
            self.settings.oauth_device_auth_url,
            data={"client_id": self.settings.oauth_client_id, "scope": "read write"},
        )
        response.raise_for_status()
        return response.json()

    def _display_device_code(self, device_data: dict[str, Any]) -> None:
        """Display device code and instructions to user."""
        user_code = device_data.get("user_code", "")
        verification_uri = device_data.get("verification_uri", "")

        console.print("\n")
        console.print(
            Panel.fit(
                f"[bold cyan]Please visit:[/bold cyan]\n{verification_uri}\n\n"
                f"[bold cyan]And enter code:[/bold cyan]\n[bold yellow]{user_code}[/bold yellow]",  # TODO: Break long line
                title="Device Authorization",
                border_style="cyan",
            ),
        )
        console.print("\n")

    async def _poll_for_device_token(self, device_data: dict[str, Any]) -> None:
        """Poll for device authorization token."""
        device_code = device_data["device_code"]
        interval = device_data.get("interval", 5)
        expires_in = device_data.get("expires_in", 600)

        start_time = asyncio.get_event_loop().time()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Waiting for authorization...", total=None)

            while asyncio.get_event_loop().time() - start_time < expires_in:
                try:
                    # Poll for token
                    response = await self.http_client.post(
                        self.settings.oauth_token_url,
                        data={
                            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                            "device_code": device_code,
                            "client_id": self.settings.oauth_client_id,
                            "client_secret": self.settings.oauth_client_secret,
                        },
                    )

                    if response.status_code == 200:
                        token_data = response.json()
                        self._update_token(token_data)
                        progress.update(
                            task,
                            description="[green]✓[/green] Authorization successful!",
                        )
                        console.print("\n[green]Authentication completed successfully![/green]")
                        return

                    error_data = response.json()
                    error = error_data.get("error", "")

                    if error == "authorization_pending":
                        await asyncio.sleep(interval)
                    elif error == "slow_down":
                        interval += 5
                        await asyncio.sleep(interval)
                    else:
                        raise RuntimeError(f"Device flow error: {error}")

                except httpx.HTTPError as e:
                    logger.error(f"Token polling error: {e}")
                    await asyncio.sleep(interval)

        raise RuntimeError("Device authorization timed out")

    async def manual_auth_flow(self) -> None:
        """Fallback manual authorization flow with PKCE."""
        if not self.settings.oauth_authorization_url:
            raise ValueError("OAuth server does not support authorization code flow")

        # Use Authlib's PKCE support
        code_verifier = secrets.token_urlsafe(64)

        if not self.oauth_client:
            # Create temporary client for auth flow
            self.oauth_client = AsyncOAuth2Client(
                client_id=self.settings.oauth_client_id,
                client_secret=self.settings.oauth_client_secret,
                redirect_uri="urn:ietf:wg:oauth:2.0:oob",
            )

        # Generate authorization URL with PKCE
        auth_url, state = self.oauth_client.create_authorization_url(
            self.settings.oauth_authorization_url,
            redirect_uri="urn:ietf:wg:oauth:2.0:oob",
            scope="read write",
            code_verifier=code_verifier,
        )

        console.print("\n")
        console.print(
            Panel.fit(
                f"[bold cyan]Please visit this URL to authorize:[/bold cyan]\n\n{auth_url}",  # TODO: Break long line
                title="Manual Authorization",
                border_style="cyan",
            ),
        )

        # Wait for user to paste authorization code
        console.print("\n")
        console.print("[bold cyan]Enter authorization code:[/bold cyan] ", end="")
        auth_code = input().strip()

        # Exchange code for token - do it manually to avoid Authlib issues
        response = await self.http_client.post(
            self.settings.oauth_token_url,
            data={
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
                "client_id": self.settings.oauth_client_id,
                "client_secret": self.settings.oauth_client_secret,
                "code_verifier": code_verifier,
            },
        )

        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            raise RuntimeError(f"Token exchange failed: {response.text}")

        token_data = response.json()
        self._update_token(token_data)
        console.print("[green]✓[/green] Token exchange successful!")

    async def refresh_token(self) -> None:
        """Refresh the access token using Authlib."""
        if not self.settings.oauth_refresh_token:
            raise ValueError("No refresh token available")

        if not self.oauth_client:
            self._setup_oauth_client()

        # Use Authlib's refresh token support
        token = await self.oauth_client.refresh_token(
            self.settings.oauth_token_url,
            refresh_token=self.settings.oauth_refresh_token,
        )

        self._update_token(token)
        logger.info("Successfully refreshed access token")

    async def discover_oauth_configuration(self) -> None:
        """Discover OAuth configuration from well-known endpoint."""
        # Try to find OAuth metadata URL
        metadata_url = await self._find_oauth_metadata_url()

        if not metadata_url:
            raise RuntimeError(
                "Could not discover OAuth configuration. "
                "Please check if the server supports OAuth 2.0 metadata discovery.",
            )

        # Fetch metadata
        try:
            response = await self.http_client.get(metadata_url)
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

            console.print(f"[green]✓[/green] Discovered OAuth configuration from {metadata_url}")
            logger.info(f"OAuth endpoints discovered: issuer={self.settings.oauth_issuer}")

            # Endpoints are discovered and set in settings (not persisted)

        except Exception as e:
            logger.error(f"Failed to discover OAuth metadata: {e}")
            raise RuntimeError(f"OAuth discovery failed: {e}") from e

    async def _find_oauth_metadata_url(self) -> str | None:
        """Find OAuth metadata URL by trying various locations."""
        parsed = urlparse(self.settings.mcp_server_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Try OAuth discovery on the same domain first (now that it's fixed!)
        candidates = [
            f"{base_url}/.well-known/oauth-authorization-server",
            f"{base_url}/.well-known/openid-configuration",
        ]

        # Also try auth subdomain as fallback
        if not parsed.netloc.startswith("auth."):
            domain_parts = parsed.netloc.split(".", 1)
            if len(domain_parts) > 1:
                auth_domain = f"auth.{domain_parts[1]}"
                candidates.extend(
                    [
                        f"{parsed.scheme}://{auth_domain}/.well-known/oauth-authorization-server",  # TODO: Break long line
                        f"{parsed.scheme}://{auth_domain}/.well-known/openid-configuration",  # TODO: Break long line
                    ],
                )

        for candidate in candidates:
            try:
                response = await self.http_client.get(candidate)
                if response.status_code == 200:
                    return candidate
            except Exception as e:
                # Continue trying other candidates if this one fails
                logging.debug(f"OAuth discovery failed for {candidate}: {e}")
                continue

        return None

    # RFC 7592 Client Registration Management Methods

    async def get_client_configuration(self) -> dict[str, Any]:
        """Get current client configuration using RFC 7592 endpoint.

        Returns:
            dict: Client configuration data

        Raises:
            RuntimeError: If operation fails or credentials missing

        """
        if not self.settings.registration_access_token or not self.settings.registration_client_uri:
            raise RuntimeError(
                "Missing registration management credentials. Client must be registered with RFC 7592 support.",
            )

        try:
            response = await self.http_client.get(
                self.settings.registration_client_uri,
                headers={"Authorization": f"Bearer {self.settings.registration_access_token}"},
            )

            if response.status_code == 404:
                raise RuntimeError("Client registration not found. Client may have expired.")
            if response.status_code == 401:
                raise RuntimeError("Invalid registration access token")
            if response.status_code == 403:
                raise RuntimeError("Access forbidden - invalid token or permissions")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to get client configuration: {e}")
            raise RuntimeError(f"Failed to get client configuration: {e}") from e

    async def update_client_configuration(self, updates: dict[str, Any]) -> dict[str, Any]:
        """Update client configuration using RFC 7592 endpoint.

        Args:
            updates: Dictionary of fields to update (redirect_uris, client_name, etc.)

        Returns:
            dict: Updated client configuration

        Raises:
            RuntimeError: If operation fails or credentials missing

        """
        if not self.settings.registration_access_token or not self.settings.registration_client_uri:
            raise RuntimeError(
                "Missing registration management credentials. Client must be registered with RFC 7592 support.",
            )

        # Allowed update fields per RFC 7592
        allowed_fields = {
            "redirect_uris",
            "client_name",
            "client_uri",
            "logo_uri",
            "contacts",
            "tos_uri",
            "policy_uri",
            "scope",
            "grant_types",
            "response_types",
        }

        # Filter to only allowed fields
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not filtered_updates:
            raise ValueError("No valid fields to update")

        try:
            response = await self.http_client.put(
                self.settings.registration_client_uri,
                json=filtered_updates,
                headers={
                    "Authorization": f"Bearer {self.settings.registration_access_token}",  # TODO: Break long line
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 404:
                raise RuntimeError("Client registration not found")
            if response.status_code == 401:
                raise RuntimeError("Invalid registration access token")
            if response.status_code == 403:
                raise RuntimeError("Access forbidden")

            response.raise_for_status()

            # Update local client_secret if returned
            data = response.json()
            if "client_secret" in data and data["client_secret"] != self.settings.oauth_client_secret:
                self.settings.oauth_client_secret = data["client_secret"]
                logger.info("Client secret was rotated by server")

            return data

        except httpx.HTTPError as e:
            logger.error(f"Failed to update client configuration: {e}")
            raise RuntimeError(f"Failed to update client configuration: {e}") from e

    async def delete_client_registration(self) -> None:
        """Delete this client registration using RFC 7592 endpoint.

        This is a destructive operation that cannot be undone.
        The client will need to re-register to continue using the service.

        Raises:
            RuntimeError: If operation fails or credentials missing

        """
        if not self.settings.registration_access_token or not self.settings.registration_client_uri:
            raise RuntimeError(
                "Missing registration management credentials. Client must be registered with RFC 7592 support.",
            )

        try:
            response = await self.http_client.delete(
                self.settings.registration_client_uri,
                headers={"Authorization": f"Bearer {self.settings.registration_access_token}"},
            )

            if response.status_code == 404:
                # Already deleted, consider this success
                logger.info("Client registration already deleted")
            elif response.status_code == 401:
                raise RuntimeError("Invalid registration access token")
            elif response.status_code == 403:
                raise RuntimeError("Access forbidden")
            elif response.status_code != 204:
                response.raise_for_status()

            # Clear local credentials after successful deletion
            self.settings.oauth_client_id = None
            self.settings.oauth_client_secret = None
            self.settings.registration_access_token = None
            self.settings.registration_client_uri = None
            self.settings.oauth_access_token = None
            self.settings.oauth_refresh_token = None

            logger.info("Client registration deleted successfully")
            console.print("[green]✓[/green] Client registration deleted")

        except httpx.HTTPError as e:
            logger.error(f"Failed to delete client registration: {e}")
            raise RuntimeError(f"Failed to delete client registration: {e}") from e
