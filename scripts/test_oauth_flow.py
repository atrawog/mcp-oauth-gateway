#!/usr/bin/env python3
"""Test OAuth flow with proper redirect URIs"""
import os
import httpx
import asyncio

async def test_oauth_registration():
    """Test OAuth client registration with proper redirect URIs"""
    base_domain = os.getenv("BASE_DOMAIN", "atratest.org")
    auth_base_url = f"https://auth.{base_domain}"
    
    # Get redirect URIs from environment
    test_callback_url = os.getenv("TEST_CALLBACK_URL")
    test_redirect_uri = os.getenv("TEST_REDIRECT_URI")
    
    print(f"Auth URL: {auth_base_url}")
    print(f"TEST_CALLBACK_URL: {test_callback_url}")
    print(f"TEST_REDIRECT_URI: {test_redirect_uri}")
    
    if not test_callback_url or not test_redirect_uri:
        print("❌ TEST_CALLBACK_URL and TEST_REDIRECT_URI must be set in .env")
        return
    
    # Register a new client (no auth required per RFC 7591)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{auth_base_url}/register",
            json={
                "redirect_uris": [test_callback_url, test_redirect_uri],
                "client_name": "OAuth Flow Test Client",
                "scope": "openid profile email",
            },
        )
        
        print(f"\nRegistration response: {response.status_code}")
        if response.status_code == 201:
            client_data = response.json()
            print(f"✅ Client registered: {client_data['client_id']}")
            print(f"   Redirect URIs: {client_data['redirect_uris']}")
        else:
            print(f"❌ Registration failed: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_oauth_registration())