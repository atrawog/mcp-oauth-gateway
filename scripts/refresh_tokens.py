#!/usr/bin/env python3
"""Automatically refresh OAuth tokens that can be refreshed before running tests.

Validates all required tokens and fails if any are missing or invalid.
Does NOT attempt to generate tokens that require manual intervention (like GitHub PAT).
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import httpx
from authlib.common.encoding import urlsafe_b64decode
from dotenv import load_dotenv, set_key

ENV_FILE = Path(".env")


def check_token_expiry(token: str) -> tuple[bool, int]:
    """Check if JWT token is expired. Returns (is_valid, seconds_until_expiry)."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False, 0
        payload = json.loads(urlsafe_b64decode(parts[1]))
        exp = payload.get("exp", 0)
        now = int(time.time())
        if exp <= now:
            return False, 0
        return True, exp - now
    except Exception:
        return False, 0


def _set_env(key: str, value: str) -> None:
    """Persist a key/value to .env and update the current process environment."""
    set_key(str(ENV_FILE), key, value, quote_mode="never")
    os.environ[key] = value


async def refresh_oauth_token():
    """Refresh the OAuth access token using refresh token."""
    print("\n🔄 Refreshing OAuth tokens...")

    refresh_token = os.getenv("GATEWAY_OAUTH_REFRESH_TOKEN")
    if not refresh_token:
        print("❌ No refresh token available!")
        return False

    client_id = os.getenv("GATEWAY_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GATEWAY_OAUTH_CLIENT_SECRET")
    base_domain = os.getenv("BASE_DOMAIN")
    # Only disable SSL verification in development environments
    ssl_verify = os.getenv("SSL_VERIFY", "true").lower() == "true"

    if not all([client_id, client_secret, base_domain]):
        print("❌ Missing OAuth client credentials!")
        return False

    token_url = f"https://auth.{base_domain}/token"

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=ssl_verify) as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code == 200:
            data = response.json()
            new_access_token = data.get("access_token")
            new_refresh_token = data.get("refresh_token", refresh_token)

            if new_access_token:
                _set_env("GATEWAY_OAUTH_ACCESS_TOKEN", new_access_token)
                if new_refresh_token != refresh_token:
                    _set_env("GATEWAY_OAUTH_REFRESH_TOKEN", new_refresh_token)
                print("✅ OAuth tokens refreshed successfully!")
                return True
            print(f"❌ No access token in response: {data}")
            return False
        print(f"❌ Token refresh failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    except Exception as e:
        print(f"❌ Failed to refresh token: {e}")
        return False


async def check_github_token():
    """Check if GitHub PAT exists and is valid - DO NOT try to generate it."""
    print("\n🔄 Checking GitHub PAT...")

    github_pat = os.getenv("GITHUB_PAT")
    if not github_pat or github_pat.strip() == "":
        print("❌ No GitHub PAT found!")
        return None  # Return None to indicate missing

    # Test if current PAT is valid
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {github_pat}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ GitHub PAT is valid for user: {user_data.get('login')}")
            return True
        if response.status_code == 401:
            print("❌ GitHub PAT is invalid or expired!")
            return False
        print(f"⚠️  GitHub API returned: {response.status_code}")
        return True

    except Exception as e:
        print(f"⚠️  Failed to validate GitHub PAT: {e}")
        return True


async def refresh_mcp_client_token():
    """Ensure MCP_CLIENT_ACCESS_TOKEN is set."""
    print("\n🔄 Checking MCP client token...")

    mcp_token = os.getenv("MCP_CLIENT_ACCESS_TOKEN")
    if mcp_token:
        # Check if it's valid
        is_valid, ttl = check_token_expiry(mcp_token)
        if is_valid and ttl > 300:  # More than 5 minutes left
            print(f"✅ MCP client token is valid (expires in {ttl / 3600:.1f} hours)")
            return True

    # Use gateway token as MCP client token if needed
    gateway_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    if gateway_token:
        print("📝 Using gateway token as MCP client token")
        _set_env("MCP_CLIENT_ACCESS_TOKEN", gateway_token)
        return True

    print("❌ No valid MCP client token available!")
    return False


async def validate_all_tokens():
    """Validate all tokens are properly set."""
    print("\n🔍 Validating all tokens...")

    required_tokens = {
        "GATEWAY_OAUTH_ACCESS_TOKEN": "Gateway OAuth access token",
        "MCP_CLIENT_ACCESS_TOKEN": "MCP client access token",
        "GITHUB_PAT": "GitHub Personal Access Token",
        "BASE_DOMAIN": "Base domain",
        "GITHUB_CLIENT_ID": "GitHub OAuth client ID",
        "GITHUB_CLIENT_SECRET": "GitHub OAuth client secret",
        "GATEWAY_JWT_SECRET": "JWT signing secret",
    }

    all_valid = True
    for key, desc in required_tokens.items():
        value = os.getenv(key)
        if not value:
            print(f"❌ Missing: {desc} ({key})")
            all_valid = False
        else:
            print(f"✅ Found: {desc}")

    # Check token expiration
    gateway_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    if gateway_token:
        is_valid, ttl = check_token_expiry(gateway_token)
        if not is_valid:
            print("❌ Gateway token is expired!")
            all_valid = False
        elif ttl < 300:  # Less than 5 minutes
            print(f"⚠️  Gateway token expires soon ({ttl} seconds)")
            all_valid = False
        else:
            print(f"✅ Gateway token valid for {ttl / 3600:.1f} hours")

    return all_valid


async def main():
    """Main function to refresh refreshable tokens and validate all tokens."""
    print("=" * 60)
    print("🔐 TOKEN REFRESH AND VALIDATION")
    print("=" * 60)

    # Load environment
    if not ENV_FILE.exists():
        print("❌ .env file not found!")
        sys.exit(1)
    load_dotenv(dotenv_path=ENV_FILE, override=True)

    # Check current token status
    gateway_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    needs_refresh = False

    if not gateway_token:
        print("❌ No gateway token found!")
        needs_refresh = True
    else:
        is_valid, ttl = check_token_expiry(gateway_token)
        if not is_valid:
            print("❌ Gateway token is expired!")
            needs_refresh = True
        elif ttl < 3600:  # Less than 1 hour
            print(f"⚠️  Gateway token expires in {ttl / 60:.1f} minutes")
            needs_refresh = True
        else:
            print(f"✅ Gateway token valid for {ttl / 3600:.1f} hours")

    # Refresh if needed
    if needs_refresh and not await refresh_oauth_token():
        print("\n❌ Failed to refresh OAuth tokens!")
        print("   Please run: just generate-github-token")
        sys.exit(1)

    # Check GitHub PAT - but don't try to generate it
    github_pat_result = await check_github_token()
    if github_pat_result is False:
        print("\n❌ GitHub PAT is invalid or expired!")
        print("   GitHub PAT is REQUIRED for all tests!")
        print("   To fix: just generate-github-token")
        sys.exit(1)  # FAIL HARD - GitHub PAT is REQUIRED!
    elif github_pat_result is None:
        print("\n❌ No GitHub PAT configured!")
        print("   GitHub PAT is REQUIRED for all tests!")
        print("   To configure: just generate-github-token")
        sys.exit(1)  # FAIL HARD - GitHub PAT is REQUIRED!

    # Ensure MCP client token
    if not await refresh_mcp_client_token():
        print("\n❌ Failed to set MCP client token!")
        sys.exit(1)

    # Final validation
    if not await validate_all_tokens():
        print("\n❌ Token validation failed!")
        print("   Some required tokens are missing or invalid.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ ALL TOKENS REFRESHED AND VALIDATED!")
    print("   Tests can now run with fresh tokens.")
    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
