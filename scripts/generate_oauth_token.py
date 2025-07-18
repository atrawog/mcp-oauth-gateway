#!/usr/bin/env python3
"""Sacred GitHub Token Generation Script - REAL OAuth Flow ONLY!

Following CLAUDE.md Commandment 1: NO MOCKING, NO SIMULATION, REAL TESTS ONLY!

This script generates ALL required OAuth tokens by completing REAL OAuth flows.
Uses REAL GitHub OAuth, REAL callback URLs, and REAL token exchanges.
"""

import asyncio
import base64
import hashlib
import os
import secrets
import sys
import webbrowser
from pathlib import Path
from urllib.parse import urlencode

import httpx


# Load environment variables
ENV_FILE = Path(__file__).parent.parent / ".env"


def load_env():
    """Load environment variables from .env file."""
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove inline comments
                    if "#" in value and not (value.startswith('"') and value.endswith('"')):
                        # Only remove comments if the value is not quoted
                        value = value.split("#", 1)[0]
                    # Strip quotes if present
                    value = value.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                        value = value[1:-1]
                    env_vars[key.strip()] = value
    return env_vars


def save_env_var(key: str, value: str):
    """Save or update an environment variable in .env file."""
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


async def check_existing_token(token: str) -> bool:
    """Check if an existing token is still valid."""
    if not token:
        return False

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            return response.status_code == 200
        except:
            return False


async def register_oauth_client_with_user_token(base_url: str, user_jwt_token: str) -> dict[str, str]:
    """Register OAuth client using a valid user JWT token."""
    # Get OAuth callback URL from environment - MUST be set properly!
    oauth_callback_url = os.getenv("TEST_OAUTH_CALLBACK_URL")

    if not oauth_callback_url:
        raise Exception(
            "TEST_OAUTH_CALLBACK_URL must be set in .env\n"
            "Example: TEST_OAUTH_CALLBACK_URL=https://auth.yourdomain.com/success",
        )

    # Always verify SSL - no exceptions for localhost per CLAUDE.md
    verify_ssl = True

    async with httpx.AsyncClient(verify=verify_ssl) as client:
        response = await client.post(
            f"{base_url}/register",
            json={
                "redirect_uris": [oauth_callback_url],
                "client_name": "MCP OAuth Token Generator",
                "scope": "openid profile email",
            },
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        if response.status_code != 201:
            raise Exception(f"Failed to register client: {response.text}")

        return response.json()


async def github_device_flow() -> str:
    """Perform REAL GitHub device flow authentication."""
    print("\n🔐 Starting REAL GitHub Device Flow Authentication...")

    github_client_id = os.getenv("GITHUB_CLIENT_ID")
    if not github_client_id:
        raise Exception("GITHUB_CLIENT_ID not set in .env")

    async with httpx.AsyncClient() as client:
        # Step 1: Get device code from GitHub
        response = await client.post(
            "https://github.com/login/device/code",
            headers={"Accept": "application/json"},
            data={"client_id": github_client_id, "scope": "user:email"},
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get device code: {response.text}")

        device_data = response.json()

        print(f"\n📱 Please visit: {device_data['verification_uri']}")
        print(f"📝 Enter code: {device_data['user_code']}")
        print("\n⏳ Waiting for authentication...")

        # Automatically open browser
        try:
            webbrowser.open(device_data["verification_uri"])
            print("🌐 Opened browser automatically")
        except:
            print("⚠️  Could not open browser automatically")

        # Step 2: Poll for token
        interval = device_data.get("interval", 5)

        while True:
            await asyncio.sleep(interval)

            poll_response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": github_client_id,
                    "device_code": device_data["device_code"],
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
            )

            poll_data = poll_response.json()

            if "access_token" in poll_data:
                print("✅ GitHub authentication successful!")
                return poll_data["access_token"]
            if poll_data.get("error") == "authorization_pending":
                print("⏳ Still waiting for authorization...")
                continue
            if poll_data.get("error") == "slow_down":
                interval = poll_data.get("interval", interval + 5)
                print(f"⏸️  Slowing down polling to {interval}s")
            else:
                raise Exception(f"Device flow failed: {poll_data}")


async def complete_real_oauth_flow(auth_base_url: str, client_id: str, client_secret: str) -> tuple[str, str]:
    """Complete REAL OAuth flow using the actual authorization endpoint."""
    print("\n🔐 Starting REAL OAuth Flow...")

    # Step 1: Generate REAL PKCE challenge
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip("=")

    state = secrets.token_urlsafe(16)

    # Step 2: Construct REAL authorization URL
    callback_url = os.getenv("TEST_OAUTH_CALLBACK_URL")
    if not callback_url:
        raise Exception("TEST_OAUTH_CALLBACK_URL must be set in .env - No defaults allowed per CLAUDE.md!")

    auth_params = {
        "client_id": client_id,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    auth_url = f"{auth_base_url}/authorize?{urlencode(auth_params)}"

    # Generate a unique session identifier for this OAuth flow
    session_id = secrets.token_urlsafe(8)[:8]

    print("\n🌐 Please complete REAL OAuth flow:")
    print(f"📌 Session ID: {session_id} (use this to identify the correct browser tab)")
    print(f"1. Visit: {auth_url}")
    print("2. Complete GitHub authentication")
    print(f"3. You'll be redirected to {callback_url}")
    print("4. Copy the 'code' parameter from the redirect URL")
    print("\n⚠️  IMPORTANT: Close any old browser tabs from previous attempts!")
    print("⚠️  Only use the NEW tab that opens now!")

    # Automatically open browser
    try:
        webbrowser.open(auth_url)
        print(f"🌐 Opened browser automatically (Session: {session_id})")
    except:
        print("⚠️  Could not open browser automatically")

    # Wait for user to complete OAuth flow and provide authorization code
    print(
        f"\n📝 After completing OAuth in the tab for Session {session_id}, copy the authorization code from the success page:",
    )
    print("   (If you see an 'expired state' error, close that tab and run this command again)")
    auth_code = input("Authorization code: ").strip()

    if not auth_code:
        raise Exception("No authorization code provided")

    # Step 3: Exchange code for tokens
    # Always verify SSL - no exceptions for localhost per CLAUDE.md
    verify_ssl = True

    async with httpx.AsyncClient(verify=verify_ssl) as client:
        token_response = await client.post(
            f"{auth_base_url}/token",
            data={
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": callback_url,
                "client_id": client_id,
                "client_secret": client_secret,
                "code_verifier": code_verifier,
            },
        )

        if token_response.status_code != 200:
            raise Exception(f"Token exchange failed ({token_response.status_code}): {token_response.text}")

        tokens = token_response.json()

        if "access_token" not in tokens:
            raise Exception(f"No access token in response: {tokens}")

        print("✅ OAuth flow completed successfully!")
        return tokens["access_token"], tokens.get("refresh_token", "")


async def main():
    """Main token generation flow - REAL OAuth only!"""
    print("🚀 Sacred GitHub Token Generator - REAL OAuth Only!")
    print("==================================================")

    # Load environment
    env_vars = load_env()
    os.environ.update(env_vars)

    # Check for required GitHub OAuth app credentials
    if not os.getenv("GITHUB_CLIENT_ID") or not os.getenv("GITHUB_CLIENT_SECRET"):
        print("❌ Missing GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET in .env")
        print("Please configure your GitHub OAuth app first.")
        sys.exit(1)

    base_domain = os.getenv("BASE_DOMAIN")
    if not base_domain:
        print("❌ Missing BASE_DOMAIN in .env")
        sys.exit(1)

    auth_base_url = f"https://auth.{base_domain}"

    # Step 1: Check existing GitHub PAT
    existing_pat = os.getenv("GITHUB_PAT")
    if existing_pat:
        print("🔍 Checking existing GitHub PAT...")
        if await check_existing_token(existing_pat):
            print("✅ Existing GitHub PAT is still valid!")
        else:
            print("❌ Existing GitHub PAT is invalid or expired")
            existing_pat = None

    # Step 2: Get GitHub PAT if needed
    if not existing_pat:
        github_pat = await github_device_flow()
        save_env_var("GITHUB_PAT", github_pat)
        print("💾 Saved GitHub PAT to .env")
    else:
        github_pat = existing_pat

    # Step 3: Check if we have existing OAuth client credentials
    client_id = os.getenv("GATEWAY_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GATEWAY_OAUTH_CLIENT_SECRET")
    existing_access_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")

    # First, validate that the client credentials are actually valid
    if client_id and client_secret:
        print(f"🔍 Validating OAuth client credentials: {client_id}...")

        # Try to use the client credentials with a dummy auth code to see if client is valid
        # Always verify SSL - no exceptions for localhost per CLAUDE.md
        verify_ssl = True
        async with httpx.AsyncClient(verify=verify_ssl) as client:
            try:
                # Try token endpoint with client credentials to validate them
                response = await client.post(
                    f"{auth_base_url}/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": "dummy_code",  # This will fail, but we'll get different errors
                        "redirect_uri": os.getenv("TEST_OAUTH_CALLBACK_URL", "https://example.com/callback"),
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "code_verifier": "dummy_verifier",
                    },
                )

                # Check the error response to determine if client is valid
                if response.status_code == 400:
                    error_data = response.json()
                    error_code = error_data.get("error", "")
                    error_detail = error_data.get("detail", {})

                    # If detail is a dict, get the error from it
                    if isinstance(error_detail, dict):
                        error_code = error_detail.get("error", error_code)

                    # If we get "invalid_grant", the client is valid but code is bad (expected)
                    if error_code == "invalid_grant":
                        print("✅ OAuth client credentials are valid!")
                    # If we get "invalid_client", the client doesn't exist or secret is wrong
                    elif error_code == "invalid_client":
                        print("❌ OAuth client credentials are invalid or not registered!")
                        print("   The client was likely cleared from Redis.")
                        client_id = None
                        client_secret = None
                    else:
                        print(f"⚠️  Unexpected error: {error_code}")
                        print(f"   Full response: {error_data}")
                        # Assume client is invalid to be safe
                        client_id = None
                        client_secret = None
                elif response.status_code == 401:
                    # 401 also indicates invalid client
                    print("❌ OAuth client credentials are invalid (401 Unauthorized)!")
                    client_id = None
                    client_secret = None
                else:
                    print(f"❌ Unexpected response validating client: {response.status_code}")
                    print(f"   Response: {response.text}")
                    client_id = None
                    client_secret = None

            except Exception as e:
                print(f"❌ Error validating client credentials: {e}")
                client_id = None
                client_secret = None

    # If we have everything, check if the access token is still valid
    if (
        client_id
        and client_secret
        and existing_access_token
        and existing_access_token != "PLACEHOLDER_NEEDS_REAL_OAUTH_FLOW"
    ):
        print(f"✅ Using existing OAuth client: {client_id}")
        print("🔍 Checking existing GATEWAY_OAUTH_ACCESS_TOKEN...")

        # Test if the token is valid by calling /verify
        # Always verify SSL - no exceptions for localhost per CLAUDE.md
        verify_ssl = True
        async with httpx.AsyncClient(verify=verify_ssl) as client:
            try:
                response = await client.get(
                    f"{auth_base_url}/verify",
                    headers={"Authorization": f"Bearer {existing_access_token}"},
                )
                if response.status_code == 200:
                    print("✅ GATEWAY_OAUTH_ACCESS_TOKEN is still valid!")
                else:
                    print("❌ GATEWAY_OAUTH_ACCESS_TOKEN is invalid or expired")
                    existing_access_token = None
            except Exception as e:
                print(f"❌ Error validating token: {e}")
                existing_access_token = None
    else:
        existing_access_token = None

    # If we don't have a valid access token, we need to get one
    if not existing_access_token:
        print("\n🔐 Need to complete OAuth flow for client registration...")

        # Check if we have a client to use for OAuth flow
        if not client_id or not client_secret:
            print("❌ No valid OAuth client credentials found!")
            print("\n🔧 Registering new OAuth client (no auth required)...")

            # Register a new client - no authentication needed!
            # Always verify SSL - no exceptions for localhost per CLAUDE.md
            verify_ssl = True

            async with httpx.AsyncClient(verify=verify_ssl) as client:
                response = await client.post(
                    f"{auth_base_url}/register",
                    json={
                        "redirect_uris": [
                            os.getenv("TEST_OAUTH_CALLBACK_URL"),
                        ],
                        "client_name": "MCP OAuth Gateway Client",
                        "scope": "openid profile email",
                    },
                )

                if response.status_code == 201:
                    client_data = response.json()
                    print("✅ Successfully registered new OAuth client!")

                    # Save the new client credentials
                    client_id = client_data["client_id"]
                    client_secret = client_data["client_secret"]
                    save_env_var("GATEWAY_OAUTH_CLIENT_ID", client_id)
                    save_env_var("GATEWAY_OAUTH_CLIENT_SECRET", client_secret)
                    print("💾 Saved new OAuth client credentials to .env")
                    print(f"   Client ID: {client_id}")
                else:
                    print(f"❌ Failed to register client: {response.status_code}")
                    print(f"   Response: {response.text}")
                    sys.exit(1)

        # We have client credentials but need a fresh user token
        print(f"🔄 Need fresh OAuth token for client: {client_id}")

        # Complete OAuth flow to get user JWT token
        access_token, refresh_token = await complete_real_oauth_flow(auth_base_url, client_id, client_secret)

        # Save the tokens
        save_env_var("GATEWAY_OAUTH_ACCESS_TOKEN", access_token)
        if refresh_token:
            save_env_var("GATEWAY_OAUTH_REFRESH_TOKEN", refresh_token)

        print("💾 Saved new OAuth tokens to .env")
        existing_access_token = access_token

    print("\n✨ Token generation complete!")
    print("\nThe following tokens are now available in .env:")
    print("  ✅ GITHUB_PAT: GitHub Personal Access Token")
    print("  ✅ GATEWAY_OAUTH_CLIENT_ID: OAuth client ID")
    print("  ✅ GATEWAY_OAUTH_CLIENT_SECRET: OAuth client secret")

    if os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN"):
        print("  ✅ GATEWAY_OAUTH_ACCESS_TOKEN: OAuth access token")
    if os.getenv("GATEWAY_OAUTH_REFRESH_TOKEN"):
        print("  ✅ GATEWAY_OAUTH_REFRESH_TOKEN: OAuth refresh token")

    print("\n🎉 All tests should now pass!")
    print("Run: just test")


if __name__ == "__main__":
    asyncio.run(main())
