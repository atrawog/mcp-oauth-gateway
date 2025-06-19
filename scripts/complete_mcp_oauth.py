#!/usr/bin/env python3
"""
Complete MCP OAuth Flow Script
Completes an OAuth flow that was started but not finished, using authorization code from MCP_AUTH_CODE.

This handles the common case where:
1. An OAuth flow was initiated (client may already be registered)
2. User completed authorization and got a code
3. Code exchange wasn't completed yet

The script will:
1. Take auth code from MCP_AUTH_CODE env var
2. Discover OAuth endpoints from the MCP server
3. Check for existing client credentials (from previous registration)
4. Register new client if needed
5. Exchange auth code for tokens
6. Save tokens to .env as MCP_CLIENT_ACCESS_TOKEN and MCP_CLIENT_REFRESH_TOKEN
"""
import os
import sys
import httpx
import asyncio
import json
import hashlib
import base64
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode, urlparse

# Load environment variables
ENV_FILE = Path(__file__).parent.parent / ".env"


def load_env() -> Dict[str, str]:
    """Load environment variables from .env file"""
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


def save_env_var(key: str, value: str):
    """Save or update an environment variable in .env file"""
    lines = []
    found = False
    
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
    
    if not found:
        lines.append(f"\n{key}={value}\n")
    
    with open(ENV_FILE, "w") as f:
        f.writelines(lines)


async def discover_oauth_metadata(mcp_url: str) -> Dict[str, str]:
    """Discover OAuth endpoints from the MCP server's well-known endpoint"""
    print(f"🔍 Discovering OAuth metadata from {mcp_url}")
    
    # Parse the MCP URL to get the base domain
    parsed = urlparse(mcp_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    # Try the well-known endpoint
    discovery_url = f"{base_url}/.well-known/oauth-authorization-server"
    
    verify_ssl = not base_url.startswith("https://localhost") and not "127.0.0.1" in base_url
    
    async with httpx.AsyncClient(verify=verify_ssl) as client:
        try:
            response = await client.get(discovery_url)
            if response.status_code == 200:
                metadata = response.json()
                print("✅ Found OAuth metadata")
                return {
                    "issuer": metadata.get("issuer", ""),
                    "authorization_endpoint": metadata.get("authorization_endpoint", ""),
                    "token_endpoint": metadata.get("token_endpoint", ""),
                    "registration_endpoint": metadata.get("registration_endpoint", ""),
                    "device_authorization_endpoint": metadata.get("device_authorization_endpoint", "")
                }
            else:
                print(f"❌ Failed to fetch metadata: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ Error discovering metadata: {e}")
            return {}


async def check_existing_client() -> Tuple[Optional[str], Optional[str]]:
    """Check if we have existing client credentials in .env"""
    env_vars = load_env()
    
    # Check for MCP client credentials
    client_id = env_vars.get("MCP_CLIENT_ID")
    client_secret = env_vars.get("MCP_CLIENT_SECRET")
    
    if client_id and client_secret:
        print(f"✅ Found existing client credentials: {client_id}")
        return client_id, client_secret
    
    # Also check for generic OAuth client credentials
    client_id = env_vars.get("OAUTH_CLIENT_ID")
    client_secret = env_vars.get("OAUTH_CLIENT_SECRET")
    
    if client_id and client_secret:
        print(f"✅ Found existing OAuth client credentials: {client_id}")
        return client_id, client_secret
    
    return None, None


async def register_oauth_client(registration_url: str, redirect_uri: str) -> Tuple[str, str]:
    """Register a new OAuth client"""
    print("📝 Registering new OAuth client...")
    
    verify_ssl = not registration_url.startswith("https://localhost") and not "127.0.0.1" in registration_url
    
    async with httpx.AsyncClient(verify=verify_ssl) as client:
        response = await client.post(
            registration_url,
            json={
                "redirect_uris": [redirect_uri],
                "client_name": "MCP OAuth Completion Script",
                "scope": "openid profile email"
            }
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to register client: {response.text}")
        
        data = response.json()
        print(f"✅ Client registered: {data['client_id']}")
        
        # Save client credentials
        save_env_var("MCP_CLIENT_ID", data["client_id"])
        save_env_var("MCP_CLIENT_SECRET", data["client_secret"])
        
        return data["client_id"], data["client_secret"]


async def exchange_code_for_tokens(
    token_endpoint: str,
    auth_code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code_verifier: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    """Exchange authorization code for tokens"""
    print("🔄 Exchanging authorization code for tokens...")
    
    verify_ssl = not token_endpoint.startswith("https://localhost") and not "127.0.0.1" in token_endpoint
    
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    # Add PKCE verifier if we have one
    if code_verifier:
        data["code_verifier"] = code_verifier
    
    async with httpx.AsyncClient(verify=verify_ssl) as client:
        response = await client.post(token_endpoint, data=data)
        
        if response.status_code != 200:
            raise Exception(f"Token exchange failed ({response.status_code}): {response.text}")
        
        tokens = response.json()
        
        if "access_token" not in tokens:
            raise Exception(f"No access token in response: {tokens}")
        
        print("✅ Successfully obtained tokens!")
        return tokens["access_token"], tokens.get("refresh_token")


async def main():
    """Main OAuth completion flow"""
    print("🚀 MCP OAuth Flow Completion Script")
    print("===================================")
    
    # Load environment
    env_vars = load_env()
    os.environ.update(env_vars)
    
    # Get required environment variables
    auth_code = os.getenv("MCP_AUTH_CODE")
    if not auth_code:
        print("❌ Missing MCP_AUTH_CODE environment variable")
        print("\nUsage:")
        print("  export MCP_AUTH_CODE='your-auth-code-here'")
        print("  pixi run python scripts/complete_mcp_oauth.py")
        sys.exit(1)
    
    # Get MCP server URL
    base_domain = os.getenv("BASE_DOMAIN")
    if not base_domain:
        print("❌ Missing BASE_DOMAIN in .env")
        sys.exit(1)
    
    mcp_url = f"https://mcp-fetch.{base_domain}/mcp"
    print(f"\n📍 MCP Server URL: {mcp_url}")
    
    # Get redirect URI (should match what was used in the original flow)
    # For MCP client out-of-band flows, this must be exactly "urn:ietf:wg:oauth:2.0:oob"
    redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
    print(f"📍 Redirect URI: {redirect_uri}")
    
    # Check for PKCE verifier if the flow used one
    code_verifier = os.getenv("MCP_CODE_VERIFIER")
    if code_verifier:
        print("🔐 Found PKCE code verifier")
    
    try:
        # Step 1: Discover OAuth endpoints
        metadata = await discover_oauth_metadata(mcp_url)
        if not metadata or not metadata.get("token_endpoint"):
            print("❌ Failed to discover OAuth endpoints")
            print("Falling back to default endpoints...")
            auth_base_url = f"https://auth.{base_domain}"
            token_endpoint = f"{auth_base_url}/token"
            registration_endpoint = f"{auth_base_url}/register"
        else:
            token_endpoint = metadata["token_endpoint"]
            registration_endpoint = metadata.get("registration_endpoint", "")
        
        print(f"\n📍 Token endpoint: {token_endpoint}")
        
        # Step 2: Check for existing client credentials
        client_id, client_secret = await check_existing_client()
        
        # Step 3: Register new client if needed
        if not client_id or not client_secret:
            if not registration_endpoint:
                print("❌ No client credentials and no registration endpoint found")
                print("\nPlease either:")
                print("1. Set MCP_CLIENT_ID and MCP_CLIENT_SECRET in .env")
                print("2. Ensure the OAuth server provides a registration endpoint")
                sys.exit(1)
            
            client_id, client_secret = await register_oauth_client(
                registration_endpoint, redirect_uri
            )
        
        # Step 4: Exchange authorization code for tokens
        access_token, refresh_token = await exchange_code_for_tokens(
            token_endpoint,
            auth_code,
            client_id,
            client_secret,
            redirect_uri,
            code_verifier
        )
        
        # Step 5: Save tokens to .env
        save_env_var("MCP_CLIENT_ACCESS_TOKEN", access_token)
        print("💾 Saved MCP_CLIENT_ACCESS_TOKEN to .env")
        
        if refresh_token:
            save_env_var("MCP_CLIENT_REFRESH_TOKEN", refresh_token)
            print("💾 Saved MCP_CLIENT_REFRESH_TOKEN to .env")
        
        print("\n✨ OAuth flow completed successfully!")
        print("\nYou can now use the MCP client with:")
        print(f"  export OAUTH_ACCESS_TOKEN=$MCP_CLIENT_ACCESS_TOKEN")
        print(f"  pixi run python -m mcp_streamablehttp_client.cli \\")
        print(f"    --server-url {mcp_url}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())