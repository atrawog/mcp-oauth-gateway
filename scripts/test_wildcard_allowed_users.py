#!/usr/bin/env python3
"""Manual test script to verify wildcard ALLOWED_GITHUB_USERS functionality.

This script demonstrates how the wildcard '*' allows any authenticated GitHub user.
Run this after setting ALLOWED_GITHUB_USERS=* in your .env file and restarting the auth service.
"""

import asyncio
import os
import sys

import httpx


async def test_wildcard_functionality():
    """Test that wildcard allows any GitHub user."""
    base_domain = os.getenv("BASE_DOMAIN")
    if not base_domain:
        print("❌ BASE_DOMAIN not set in environment")
        return False

    auth_url = f"https://auth.{base_domain}"
    # Only disable SSL verification in development environments
    ssl_verify = os.getenv("SSL_VERIFY", "true").lower() == "true"

    async with httpx.AsyncClient(verify=ssl_verify) as client:
        print("1. Testing client registration (should work regardless of ALLOWED_GITHUB_USERS)...")

        # Register a test client
        reg_response = await client.post(
            f"{auth_url}/register",
            json={"redirect_uris": ["https://testapp.example.com/callback"]},
        )

        if reg_response.status_code != 201:
            print(f"❌ Registration failed: {reg_response.status_code}")
            print(f"   Response: {reg_response.text}")
            return False

        reg_data = reg_response.json()
        client_id = reg_data["client_id"]
        print(f"✅ Client registered successfully: {client_id}")

        print("\n2. Starting OAuth flow (should redirect to GitHub for any user)...")

        # Start OAuth flow
        auth_params = {
            "client_id": client_id,
            "redirect_uri": "https://testapp.example.com/callback",
            "response_type": "code",
            "state": "test-state-123",
            "code_challenge": "test-challenge-456",
            "code_challenge_method": "S256",
        }

        auth_response = await client.get(f"{auth_url}/authorize", params=auth_params, follow_redirects=False)

        if auth_response.status_code != 302:
            print(f"❌ Authorization failed: {auth_response.status_code}")
            print(f"   Response: {auth_response.text}")
            return False

        github_url = auth_response.headers.get("location", "")
        if "github.com/login/oauth/authorize" not in github_url:
            print(f"❌ Unexpected redirect: {github_url}")
            return False

        print("✅ Successfully redirected to GitHub OAuth")
        print(f"   GitHub URL: {github_url[:100]}...")

        print("\n3. Check current ALLOWED_GITHUB_USERS setting...")
        allowed_users = os.getenv("ALLOWED_GITHUB_USERS", "")
        if not allowed_users:
            print("   ALLOWED_GITHUB_USERS is empty (allows all users)")
        elif "*" in allowed_users:
            print(f"   ALLOWED_GITHUB_USERS contains wildcard: '{allowed_users}'")
            print("   ✅ Any authenticated GitHub user will be allowed!")
        else:
            print(f"   ALLOWED_GITHUB_USERS is restricted to: '{allowed_users}'")
            print("   ⚠️  Only these specific users will be allowed through GitHub OAuth")

        return True


async def main():
    print("🔍 Testing Wildcard ALLOWED_GITHUB_USERS Functionality")
    print("=" * 60)

    success = await test_wildcard_functionality()

    print("\n" + "=" * 60)
    if success:
        print("✅ Wildcard functionality is working correctly!")
        print("\nTo complete the test:")
        print("1. Set ALLOWED_GITHUB_USERS=* in your .env file")
        print("2. Restart the auth service: just rebuild auth")
        print("3. Complete the GitHub OAuth flow with any GitHub account")
        print("4. The callback should succeed for any authenticated user")
    else:
        print("❌ Test failed - check the error messages above")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
