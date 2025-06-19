#!/usr/bin/env python3
"""
Sacred GitHub Token Generation Script - REAL OAuth Flow ONLY!
Following CLAUDE.md Commandment 1: NO MOCKING, NO SIMULATION, REAL TESTS ONLY!

This script generates ALL required OAuth tokens by completing REAL OAuth flows.
Uses REAL GitHub OAuth, REAL callback URLs, and REAL token exchanges.
"""
import os
import sys
import json
import time
import httpx
import asyncio
import secrets
import hashlib
import base64
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Tuple
from urllib.parse import urlencode, urlparse, parse_qs


# Load environment variables
ENV_FILE = Path(__file__).parent.parent / ".env"


def load_env():
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


async def check_existing_token(token: str) -> bool:
    """Check if an existing token is still valid"""
    if not token:
        return False
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            return response.status_code == 200
        except:
            return False


async def register_oauth_client(base_url: str) -> Dict[str, str]:
    """Register OAuth client with the gateway using REAL FQDN callback URLs"""
    # Get REAL callback URLs from environment - must be REAL FQDNs
    test_callback_url = os.getenv("TEST_CALLBACK_URL")
    test_redirect_uri = os.getenv("TEST_REDIRECT_URI")
    
    if not test_callback_url or not test_redirect_uri:
        raise Exception("TEST_CALLBACK_URL and TEST_REDIRECT_URI must be set in .env with REAL FQDNs")
    
    verify_ssl = not base_url.startswith("https://localhost") and not "127.0.0.1" in base_url
    
    async with httpx.AsyncClient(verify=verify_ssl) as client:
        response = await client.post(
            f"{base_url}/register",
            json={
                "redirect_uris": [
                    test_callback_url,
                    test_redirect_uri
                ],
                "client_name": "MCP OAuth Token Generator",
                "scope": "openid profile email"
            }
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to register client: {response.text}")
        
        return response.json()


async def github_device_flow() -> str:
    """Perform REAL GitHub device flow authentication"""
    print("\n🔐 Starting REAL GitHub Device Flow Authentication...")
    
    github_client_id = os.getenv("GITHUB_CLIENT_ID")
    if not github_client_id:
        raise Exception("GITHUB_CLIENT_ID not set in .env")
    
    async with httpx.AsyncClient() as client:
        # Step 1: Get device code from GitHub
        response = await client.post(
            "https://github.com/login/device/code",
            headers={"Accept": "application/json"},
            data={
                "client_id": github_client_id,
                "scope": "user:email"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get device code: {response.text}")
        
        device_data = response.json()
        
        print(f"\n📱 Please visit: {device_data['verification_uri']}")
        print(f"📝 Enter code: {device_data['user_code']}")
        print("\n⏳ Waiting for authentication...")
        
        # Automatically open browser
        try:
            webbrowser.open(device_data['verification_uri'])
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
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
            )
            
            poll_data = poll_response.json()
            
            if "access_token" in poll_data:
                print("✅ GitHub authentication successful!")
                return poll_data["access_token"]
            elif poll_data.get("error") == "authorization_pending":
                print("⏳ Still waiting for authorization...")
                continue
            elif poll_data.get("error") == "slow_down":
                interval = poll_data.get("interval", interval + 5)
                print(f"⏸️  Slowing down polling to {interval}s")
            else:
                raise Exception(f"Device flow failed: {poll_data}")


async def complete_real_oauth_flow(auth_base_url: str, client_id: str, client_secret: str) -> Tuple[str, str]:
    """Complete REAL OAuth flow using the actual authorization endpoint"""
    print("\n🔐 Starting REAL OAuth Flow...")
    
    # Step 1: Generate REAL PKCE challenge
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    
    state = secrets.token_urlsafe(16)
    
    # Step 2: Construct REAL authorization URL using REAL FQDN
    callback_url = os.getenv("TEST_CALLBACK_URL")
    if not callback_url:
        raise Exception("TEST_CALLBACK_URL must be set in .env with REAL FQDN")
    
    auth_params = {
        "client_id": client_id,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    auth_url = f"{auth_base_url}/authorize?{urlencode(auth_params)}"
    
    print(f"\n🌐 Please complete REAL OAuth flow:")
    print(f"1. Visit: {auth_url}")
    print("2. Complete GitHub authentication")
    print(f"3. You'll be redirected to {callback_url}")
    print("4. Copy the 'code' parameter from the redirect URL")
    
    # Automatically open browser
    try:
        webbrowser.open(auth_url)
        print("🌐 Opened browser automatically")
    except:
        print("⚠️  Could not open browser automatically")
    
    # Wait for user to complete OAuth flow and provide authorization code
    print("\n📝 After completing OAuth, copy the authorization code from the success page:")
    auth_code = input("Authorization code: ").strip()
    
    if not auth_code:
        raise Exception("No authorization code provided")
    
    # Step 3: Exchange code for tokens
    verify_ssl = not auth_base_url.startswith("https://localhost") and not "127.0.0.1" in auth_base_url
    
    async with httpx.AsyncClient(verify=verify_ssl) as client:
        token_response = await client.post(
            f"{auth_base_url}/token",
            data={
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": callback_url,
                "client_id": client_id,
                "client_secret": client_secret,
                "code_verifier": code_verifier
            }
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
    
    # Step 3: Register OAuth client with REAL callback URLs
    client_id = os.getenv("OAUTH_CLIENT_ID")
    client_secret = os.getenv("OAUTH_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("\n📝 Registering OAuth client with REAL callback URLs...")
        try:
            client_data = await register_oauth_client(auth_base_url)
            client_id = client_data["client_id"]
            client_secret = client_data["client_secret"]
            
            save_env_var("OAUTH_CLIENT_ID", client_id)
            save_env_var("OAUTH_CLIENT_SECRET", client_secret)
            print("✅ OAuth client registered successfully!")
            print(f"   Client ID: {client_id}")
            print(f"   Callback URLs: {client_data.get('redirect_uris', [])}")
        except Exception as e:
            print(f"❌ Failed to register OAuth client: {e}")
            print("Make sure the gateway is running with: just up")
            sys.exit(1)
    else:
        print(f"✅ Using existing OAuth client: {client_id}")
    
    # Step 4: Complete REAL OAuth flow to get access tokens
    existing_access_token = os.getenv("OAUTH_ACCESS_TOKEN")
    if existing_access_token:
        print("✅ OAUTH_ACCESS_TOKEN already exists")
    else:
        print("\n🔐 Completing REAL OAuth flow to generate access tokens...")
        try:
            access_token, refresh_token = await complete_real_oauth_flow(
                auth_base_url, client_id, client_secret
            )
            
            save_env_var("OAUTH_ACCESS_TOKEN", access_token)
            if refresh_token:
                save_env_var("OAUTH_REFRESH_TOKEN", refresh_token)
            
            print("✅ OAuth access tokens generated successfully!")
            print("💾 Saved tokens to .env")
            
        except Exception as e:
            print(f"❌ OAuth flow failed: {e}")
            print("You may need to complete this manually or check your configuration.")
            sys.exit(1)
    
    print("\n✨ Token generation complete!")
    print("\nThe following tokens are now available in .env:")
    print("  ✅ GITHUB_PAT: GitHub Personal Access Token")
    print("  ✅ OAUTH_CLIENT_ID: OAuth client ID") 
    print("  ✅ OAUTH_CLIENT_SECRET: OAuth client secret")
    
    if os.getenv("OAUTH_ACCESS_TOKEN"):
        print("  ✅ OAUTH_ACCESS_TOKEN: OAuth access token")
    if os.getenv("OAUTH_REFRESH_TOKEN"):
        print("  ✅ OAUTH_REFRESH_TOKEN: OAuth refresh token")
    
    print("\n🎉 All tests should now pass!")
    print("Run: just test")


if __name__ == "__main__":
    asyncio.run(main())