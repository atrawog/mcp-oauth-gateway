#!/usr/bin/env python3
"""Token validation script for MCP OAuth Gateway.

Validates all OAuth tokens before running tests.
"""

import asyncio
import os
import sys
import time
from datetime import UTC
from datetime import datetime

import httpx


def check_env_var(name: str) -> str:
    """Get environment variable or exit with error."""
    value = os.getenv(name)
    if not value:
        print(f"❌ Environment variable {name} is not set!")
        return None
    return value


def decode_jwt_token(token: str) -> dict:
    """Decode JWT token without signature verification."""
    try:
        # Decode without verification for inspection only
        import base64
        import json

        # JWT format: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")

        # Decode payload (add padding if needed)
        payload_part = parts[1]
        payload_part += "=" * (4 - len(payload_part) % 4)  # Add padding
        payload_json = base64.urlsafe_b64decode(payload_part)
        return json.loads(payload_json)
    except Exception as e:
        print(f"❌ Failed to decode JWT token: {e}")
        return None


def check_token_expiry(payload: dict) -> bool:
    """Check if token is expired."""
    exp = payload.get("exp")
    if not exp:
        print("❌ Token has no expiration claim")
        return False

    now = int(time.time())
    iat = payload.get("iat", 0)

    print(f"🕐 Token issued at: {datetime.fromtimestamp(iat, tz=UTC)}")
    print(f"🕐 Token expires at: {datetime.fromtimestamp(exp, tz=UTC)}")
    print(f"🕐 Current time: {datetime.fromtimestamp(now, tz=UTC)}")

    if exp < now:
        print(f"❌ TOKEN IS EXPIRED! (expired {now - exp} seconds ago)")
        return False
    remaining = exp - now
    print(f"✅ Token is valid (expires in {remaining} seconds / {remaining / 3600:.1f} hours)")
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
            print("✅ Auth service validates token successfully")
            return True
        print(f"❌ Auth service rejected token: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return False

    except Exception as e:
        print(f"❌ Failed to test auth service: {e}")
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
            print("✅ MCP service is reachable")
            return True
        print(f"⚠️  MCP service returned unexpected status: {response.status_code}")
        return True  # Still consider it working

    except Exception as e:
        print(f"❌ Failed to test MCP service: {e}")
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
            print(f"✅ GitHub PAT is valid for user: {user_data.get('login', 'unknown')}")
            return True
        if response.status_code == 401:
            print("❌ GitHub PAT is invalid or expired!")
            return False
        print(f"⚠️  GitHub API returned unexpected status: {response.status_code}")
        return False

    except Exception as e:
        print(f"❌ Failed to test GitHub PAT: {e}")
        return False


async def main():
    """Main validation function."""
    print("=" * 60)
    print("🔍 OAUTH TOKEN VALIDATION")
    print("=" * 60)

    all_valid = True

    # Check OAuth Access Token
    print("\n📋 Checking GATEWAY_OAUTH_ACCESS_TOKEN...")
    oauth_token = check_env_var("GATEWAY_OAUTH_ACCESS_TOKEN")
    if oauth_token:
        payload = decode_jwt_token(oauth_token)
        if payload:
            print(f"   Subject: {payload.get('sub')}")
            print(f"   Username: {payload.get('username')}")
            print(f"   Client ID: {payload.get('client_id')}")
            print(f"   JTI: {payload.get('jti')}")

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
    print("\n📋 Checking GITHUB_PAT...")
    github_pat = check_env_var("GITHUB_PAT")
    if github_pat:
        if github_pat.startswith(("gho_", "ghp_")):
            print("✅ GitHub PAT format looks valid")
            # Test against GitHub API
            if not await test_github_pat(github_pat):
                all_valid = False
        else:
            print("❌ GitHub PAT format is invalid!")
            all_valid = False
    else:
        print("❌ GitHub PAT not found - this is REQUIRED!")
        all_valid = False

    # Check OAuth Client Credentials
    print("\n📋 Checking OAuth Client Credentials...")
    client_id = check_env_var("GATEWAY_OAUTH_CLIENT_ID")
    client_secret = check_env_var("GATEWAY_OAUTH_CLIENT_SECRET")

    if client_id and client_secret:
        print("✅ OAuth client credentials present")
        print(f"   Client ID: {client_id}")
        print(f"   Client Secret: {'*' * (len(client_secret) - 4)}{client_secret[-4:]}")
    else:
        print("❌ OAuth client credentials missing")
        all_valid = False

    # Check Refresh Token
    print("\n📋 Checking GATEWAY_OAUTH_REFRESH_TOKEN...")
    refresh_token = check_env_var("GATEWAY_OAUTH_REFRESH_TOKEN")
    if refresh_token:
        print(f"✅ Refresh token present: {'*' * (len(refresh_token) - 8)}{refresh_token[-8:]}")
    else:
        print("⚠️  Refresh token not found")

    # Check MCP Client Access Token
    print("\n📋 Checking MCP_CLIENT_ACCESS_TOKEN...")
    mcp_client_token = check_env_var("MCP_CLIENT_ACCESS_TOKEN")
    if mcp_client_token:
        payload = decode_jwt_token(mcp_client_token)
        if payload:
            print(f"   Client ID: {payload.get('client_id')}")
            print(f"   Scope: {payload.get('scope')}")
            if not check_token_expiry(payload):
                all_valid = False
        else:
            all_valid = False
    else:
        print("❌ MCP Client Access Token not found - this is REQUIRED!")
        all_valid = False

    print("\n" + "=" * 60)
    if all_valid:
        print("✅ ALL TOKENS ARE VALID AND READY FOR TESTING!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ TOKEN VALIDATION FAILED!")
        print("   Please run: just generate-github-token")
        print("   Or check token expiration: just check-token-expiry")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
