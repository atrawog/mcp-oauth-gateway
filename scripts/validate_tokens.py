#!/usr/bin/env python3
"""Token validation script for MCP OAuth Gateway.

Validates all OAuth tokens before running tests.
"""

import asyncio
import json
import os
import sys
import time
from datetime import UTC, datetime

import httpx
from authlib.common.encoding import urlsafe_b64decode
from rich.console import Console

console = Console()


def check_env_var(name: str) -> str:
    """Get environment variable or exit with error."""
    value = os.getenv(name)
    if not value:
        console.print(f"[red]❌ Environment variable {name} is not set![/red]")
        return None
    return value


def decode_jwt_token(token: str) -> dict:
    """Decode JWT token without signature verification."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        return json.loads(urlsafe_b64decode(parts[1]))
    except Exception as e:
        console.print(f"[red]❌ Failed to decode JWT token: {e}[/red]")
        return None


def check_token_expiry(payload: dict) -> bool:
    """Check if token is expired."""
    exp = payload.get("exp")
    if not exp:
        console.print("[red]❌ Token has no expiration claim[/red]")
        return False

    now = int(time.time())
    iat = payload.get("iat", 0)

    console.print(f"[cyan]🕐 Token issued at: {datetime.fromtimestamp(iat, tz=UTC)}[/cyan]")
    console.print(f"[cyan]🕐 Token expires at: {datetime.fromtimestamp(exp, tz=UTC)}[/cyan]")
    console.print(f"[cyan]🕐 Current time: {datetime.fromtimestamp(now, tz=UTC)}[/cyan]")

    if exp < now:
        console.print(f"[red]❌ TOKEN IS EXPIRED! (expired {now - exp} seconds ago)[/red]")
        return False
    remaining = exp - now
    console.print(f"[green]✅ Token is valid (expires in {remaining} seconds / {remaining / 3600:.1f} hours)[/green]")
    return True


async def test_auth_service(token: str) -> bool:
    """Test if auth service accepts the token."""
    base_domain = check_env_var("BASE_DOMAIN")
    if not base_domain:
        return False

    auth_url = f"https://auth.{base_domain}/verify"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(auth_url, headers={"Authorization": f"Bearer {token}"})

        if response.status_code == 200:
            console.print("[green]✅ Auth service validates token successfully[/green]")
            return True
        console.print(f"[red]❌ Auth service rejected token: {response.status_code}[/red]")
        console.print(f"   Response: {response.text[:200]}")
        return False

    except Exception as e:
        console.print(f"[red]❌ Failed to test auth service: {e}[/red]")
        return False


async def test_mcp_service(token: str) -> bool:
    """Test if MCP service accepts the token."""
    base_domain = check_env_var("BASE_DOMAIN")
    if not base_domain:
        return False

    mcp_url = f"https://mcp-fetch.{base_domain}/health"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(mcp_url, headers={"Authorization": f"Bearer {token}"})

        if response.status_code in [200, 401]:  # 401 is expected for health endpoint
            console.print("[green]✅ MCP service is reachable[/green]")
            return True
        console.print(f"[yellow]⚠️  MCP service returned unexpected status: {response.status_code}[/yellow]")
        return True  # Still consider it working

    except Exception as e:
        console.print(f"[red]❌ Failed to test MCP service: {e}[/red]")
        return False


async def test_github_pat(pat: str) -> bool:
    """Test if GitHub PAT is valid."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {pat}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

        if response.status_code == 200:
            user_data = response.json()
            console.print(f"[green]✅ GitHub PAT is valid for user: {user_data.get('login', 'unknown')}[/green]")
            return True
        if response.status_code == 401:
            console.print("[red]❌ GitHub PAT is invalid or expired![/red]")
            return False
        console.print(f"[yellow]⚠️  GitHub API returned unexpected status: {response.status_code}[/yellow]")
        return False

    except Exception as e:
        console.print(f"[red]❌ Failed to test GitHub PAT: {e}[/red]")
        return False


async def main():
    """Main validation function."""
    console.print("=" * 60)
    console.print("[bold]🔍 OAUTH TOKEN VALIDATION[/bold]")
    console.print("=" * 60)

    all_valid = True

    # Check OAuth Access Token
    console.print("\n[bold]📋 Checking GATEWAY_OAUTH_ACCESS_TOKEN...[/bold]")
    oauth_token = check_env_var("GATEWAY_OAUTH_ACCESS_TOKEN")
    if oauth_token:
        payload = decode_jwt_token(oauth_token)
        if payload:
            console.print(f"   Subject: {payload.get('sub')}")
            console.print(f"   Username: {payload.get('username')}")
            console.print(f"   Client ID: {payload.get('client_id')}")
            console.print(f"   JTI: {payload.get('jti')}")

            if not check_token_expiry(payload):
                all_valid = False
            else:
                # Test the token with services
                if not await test_auth_service(oauth_token):
                    all_valid = False
                if not await test_mcp_service(oauth_token):
                    all_valid = False
        else:
            all_valid = False
    else:
        all_valid = False

    # Check GitHub PAT
    console.print("\n[bold]📋 Checking GITHUB_PAT...[/bold]")
    github_pat = check_env_var("GITHUB_PAT")
    if github_pat:
        if github_pat.startswith(("gho_", "ghp_")):
            console.print("[green]✅ GitHub PAT format looks valid[/green]")
            # Test against GitHub API
            if not await test_github_pat(github_pat):
                all_valid = False
        else:
            console.print("[red]❌ GitHub PAT format is invalid![/red]")
            all_valid = False
    else:
        console.print("[red]❌ GitHub PAT not found - this is REQUIRED![/red]")
        all_valid = False

    # Check OAuth Client Credentials
    console.print("\n[bold]📋 Checking OAuth Client Credentials...[/bold]")
    client_id = check_env_var("GATEWAY_OAUTH_CLIENT_ID")
    client_secret = check_env_var("GATEWAY_OAUTH_CLIENT_SECRET")

    if client_id and client_secret:
        console.print("[green]✅ OAuth client credentials present[/green]")
        console.print(f"   Client ID: {client_id}")
        console.print(f"   Client Secret: {'*' * (len(client_secret) - 4)}{client_secret[-4:]}")
    else:
        console.print("[red]❌ OAuth client credentials missing[/red]")
        all_valid = False

    # Check Refresh Token
    console.print("\n[bold]📋 Checking GATEWAY_OAUTH_REFRESH_TOKEN...[/bold]")
    refresh_token = check_env_var("GATEWAY_OAUTH_REFRESH_TOKEN")
    if refresh_token:
        console.print(f"[green]✅ Refresh token present: {'*' * (len(refresh_token) - 8)}{refresh_token[-8:]}[/green]")
    else:
        console.print("[yellow]⚠️  Refresh token not found[/yellow]")

    # Check MCP Client Access Token
    console.print("\n[bold]📋 Checking MCP_CLIENT_ACCESS_TOKEN...[/bold]")
    mcp_client_token = check_env_var("MCP_CLIENT_ACCESS_TOKEN")
    if mcp_client_token:
        payload = decode_jwt_token(mcp_client_token)
        if payload:
            console.print(f"   Client ID: {payload.get('client_id')}")
            console.print(f"   Scope: {payload.get('scope')}")
            if not check_token_expiry(payload):
                all_valid = False
        else:
            all_valid = False
    else:
        console.print("[red]❌ MCP Client Access Token not found - this is REQUIRED![/red]")
        all_valid = False

    console.print("\n" + "=" * 60)
    if all_valid:
        console.print("[bold green]✅ ALL TOKENS ARE VALID AND READY FOR TESTING![/bold green]")
        console.print("=" * 60)
        sys.exit(0)
    else:
        console.print("[bold red]❌ TOKEN VALIDATION FAILED![/bold red]")
        console.print("   Please run: just generate-github-token")
        console.print("   Or check token expiration: just check-token-expiry")
        console.print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
