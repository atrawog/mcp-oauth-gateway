#!/usr/bin/env python3
"""
Sacred GitHub Token Generation Script
Smart token generation with device flow support
"""
import os
import sys
import json
import time
import httpx
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urlencode


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
    """Register OAuth client with the gateway"""
    # For development/testing, we may need to skip SSL verification
    # In production, ensure proper SSL certificates are installed
    verify_ssl = not base_url.startswith("https://localhost") and not "127.0.0.1" in base_url
    
    async with httpx.AsyncClient(verify=verify_ssl) as client:
        response = await client.post(
            f"{base_url}/register",
            json={
                "redirect_uris": ["http://localhost:8080/callback"],
                "client_name": "MCP OAuth Token Generator",
                "scope": "mcp:access"
            }
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to register client: {response.text}")
        
        return response.json()


async def github_device_flow() -> str:
    """Perform GitHub device flow authentication"""
    print("\n🔐 Starting GitHub Device Flow Authentication...")
    
    # Get device code
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/device/code",
            headers={"Accept": "application/json"},
            data={
                "client_id": os.getenv("GITHUB_CLIENT_ID"),
                "scope": "user:email"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get device code: {response.text}")
        
        device_data = response.json()
        
        print(f"\n📱 Please visit: {device_data['verification_uri']}")
        print(f"📝 Enter code: {device_data['user_code']}")
        print("\n⏳ Waiting for authentication...")
        
        # Poll for token
        interval = device_data.get("interval", 5)
        
        while True:
            await asyncio.sleep(interval)
            
            poll_response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": os.getenv("GITHUB_CLIENT_ID"),
                    "device_code": device_data["device_code"],
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
            )
            
            poll_data = poll_response.json()
            
            if "access_token" in poll_data:
                print("✅ Authentication successful!")
                return poll_data["access_token"]
            elif poll_data.get("error") == "authorization_pending":
                continue
            elif poll_data.get("error") == "slow_down":
                interval = poll_data.get("interval", interval + 5)
            else:
                raise Exception(f"Device flow failed: {poll_data}")


async def main():
    """Main token generation flow"""
    print("🚀 Sacred GitHub Token Generator")
    print("================================")
    
    # Load environment
    env_vars = load_env()
    os.environ.update(env_vars)
    
    # Check for required GitHub OAuth app credentials
    if not os.getenv("GITHUB_CLIENT_ID") or not os.getenv("GITHUB_CLIENT_SECRET"):
        print("❌ Missing GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET in .env")
        print("Please configure your GitHub OAuth app first.")
        sys.exit(1)
    
    base_domain = os.getenv("BASE_DOMAIN", "localhost")
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
    
    # Step 3: Check for existing OAuth client
    client_id = os.getenv("OAUTH_CLIENT_ID")
    client_secret = os.getenv("OAUTH_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("\n📝 Registering OAuth client with gateway...")
        try:
            client_data = await register_oauth_client(auth_base_url)
            client_id = client_data["client_id"]
            client_secret = client_data["client_secret"]
            
            save_env_var("OAUTH_CLIENT_ID", client_id)
            save_env_var("OAUTH_CLIENT_SECRET", client_secret)
            print("✅ OAuth client registered successfully!")
        except Exception as e:
            print(f"❌ Failed to register OAuth client: {e}")
            print("Make sure the gateway is running!")
            sys.exit(1)
    else:
        print("✅ Using existing OAuth client")
    
    # Step 4: Check for refresh token
    refresh_token = os.getenv("OAUTH_REFRESH_TOKEN")
    jwt_token = os.getenv("OAUTH_JWT_TOKEN")
    
    if refresh_token:
        print("\n🔄 Attempting to refresh JWT token...")
        # TODO: Implement refresh token flow
        print("⚠️  Refresh token flow not yet implemented")
    
    print("\n✨ Token generation complete!")
    print("\nThe following tokens have been saved to .env:")
    print("  - GITHUB_PAT: GitHub Personal Access Token")
    print("  - OAUTH_CLIENT_ID: OAuth client ID") 
    print("  - OAUTH_CLIENT_SECRET: OAuth client secret")
    
    print("\n📋 Next steps:")
    print("1. Start the gateway: just up")
    print("2. Navigate to the authorization URL in your browser")
    print("3. Complete the OAuth flow to get JWT tokens")


if __name__ == "__main__":
    asyncio.run(main())