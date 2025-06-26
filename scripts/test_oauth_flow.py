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
    test_callback_url = os.getenv("TEST_OAUTH_CALLBACK_URL")
    
    print(f"Auth URL: {auth_base_url}")
    print(f"TEST_OAUTH_CALLBACK_URL: {test_callback_url}")
    
    if not test_callback_url:
        print("❌ TEST_OAUTH_CALLBACK_URL must be set in .env")
        return
    
    # Register a new client (no auth required per RFC 7591)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{auth_base_url}/register",
            json={
                "redirect_uris": [test_callback_url],
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