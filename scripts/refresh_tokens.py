#!/usr/bin/env python3
"""
Automatically refresh OAuth tokens before running tests.
This ensures all tokens are valid and tests can run successfully.
"""
import os
import sys
import json
import time
import asyncio
import httpx
from datetime import datetime
from pathlib import Path


def load_env_file():
    """Load .env file into environment"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    return True


def check_token_expiry(token: str) -> tuple[bool, int]:
    """Check if JWT token is expired. Returns (is_valid, seconds_until_expiry)"""
    try:
        import base64
        parts = token.split('.')
        if len(parts) != 3:
            return False, 0
        
        # Decode payload
        payload_part = parts[1]
        payload_part += '=' * (4 - len(payload_part) % 4)
        payload_json = base64.urlsafe_b64decode(payload_part)
        payload = json.loads(payload_json)
        
        exp = payload.get('exp', 0)
        now = int(time.time())
        
        if exp <= now:
            return False, 0
        
        return True, exp - now
    except Exception:
        return False, 0


async def refresh_oauth_token():
    """Refresh the OAuth access token using refresh token"""
    print("\n🔄 Refreshing OAuth tokens...")
    
    refresh_token = os.getenv("GATEWAY_OAUTH_REFRESH_TOKEN")
    if not refresh_token:
        print("❌ No refresh token available!")
        return False
    
    client_id = os.getenv("GATEWAY_OAUTH_CLIENT_ID")
    client_secret = os.getenv("GATEWAY_OAUTH_CLIENT_SECRET")
    base_domain = os.getenv("BASE_DOMAIN")
    
    if not all([client_id, client_secret, base_domain]):
        print("❌ Missing OAuth client credentials!")
        return False
    
    token_url = f"https://auth.{base_domain}/token"
    
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        if response.status_code == 200:
            data = response.json()
            new_access_token = data.get("access_token")
            new_refresh_token = data.get("refresh_token", refresh_token)
            
            if new_access_token:
                # Update .env file
                update_env_file("GATEWAY_OAUTH_ACCESS_TOKEN", new_access_token)
                os.environ["GATEWAY_OAUTH_ACCESS_TOKEN"] = new_access_token
                
                if new_refresh_token != refresh_token:
                    update_env_file("GATEWAY_OAUTH_REFRESH_TOKEN", new_refresh_token)
                    os.environ["GATEWAY_OAUTH_REFRESH_TOKEN"] = new_refresh_token
                
                print("✅ OAuth tokens refreshed successfully!")
                return True
            else:
                print(f"❌ No access token in response: {data}")
                return False
        else:
            print(f"❌ Token refresh failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to refresh token: {e}")
        return False


async def refresh_github_token():
    """Refresh GitHub PAT using device flow"""
    print("\n🔄 Checking GitHub PAT...")
    
    github_pat = os.getenv("GITHUB_PAT")
    if not github_pat:
        print("⚠️  No GitHub PAT found")
        return None  # Return None to indicate missing (not invalid)
    
    # Test if current PAT is valid
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {github_pat}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ GitHub PAT is valid for user: {user_data.get('login')}")
            return True
        elif response.status_code == 401:
            print("❌ GitHub PAT is invalid or expired!")
            print("   Attempting to generate new PAT...")
            return await generate_github_pat()
        else:
            print(f"⚠️  GitHub API returned: {response.status_code}")
            return True
            
    except Exception as e:
        print(f"⚠️  Failed to validate GitHub PAT: {e}")
        return True


async def generate_github_pat():
    """Generate GitHub PAT using device flow (non-interactive)"""
    github_client_id = os.getenv("GITHUB_CLIENT_ID")
    
    if not github_client_id:
        print("❌ No GITHUB_CLIENT_ID found!")
        return False
    
    try:
        # Initiate device flow
        async with httpx.AsyncClient(timeout=30.0) as client:
            device_response = await client.post(
                "https://github.com/login/device/code",
                data={
                    "client_id": github_client_id,
                    "scope": "repo read:user"
                },
                headers={"Accept": "application/json"}
            )
            
            if device_response.status_code != 200:
                print(f"❌ Failed to initiate device flow: {device_response.status_code}")
                return False
            
            device_data = device_response.json()
            device_code = device_data["device_code"]
            user_code = device_data["user_code"]
            verification_uri = device_data["verification_uri"]
            
            print(f"\n📱 GitHub Device Authorization Required!")
            print(f"   1. Visit: {verification_uri}")
            print(f"   2. Enter code: {user_code}")
            print(f"   3. Authorize the application")
            print(f"\n⏳ This is required for automated testing.")
            print(f"   Without a valid GitHub PAT, OAuth tests will fail.")
            
            # In non-interactive mode, we can't wait for user input
            print("\n❌ Cannot complete device flow in non-interactive mode!")
            print("   Please run manually: just generate-github-token")
            return False
            
    except Exception as e:
        print(f"❌ Failed to generate GitHub PAT: {e}")
        return False


async def refresh_mcp_client_token():
    """Ensure MCP_CLIENT_ACCESS_TOKEN is set"""
    print("\n🔄 Checking MCP client token...")
    
    mcp_token = os.getenv("MCP_CLIENT_ACCESS_TOKEN")
    if mcp_token:
        # Check if it's valid
        is_valid, ttl = check_token_expiry(mcp_token)
        if is_valid and ttl > 300:  # More than 5 minutes left
            print(f"✅ MCP client token is valid (expires in {ttl/3600:.1f} hours)")
            return True
    
    # Use gateway token as MCP client token if needed
    gateway_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    if gateway_token:
        print("📝 Using gateway token as MCP client token")
        update_env_file("MCP_CLIENT_ACCESS_TOKEN", gateway_token)
        os.environ["MCP_CLIENT_ACCESS_TOKEN"] = gateway_token
        return True
    
    print("❌ No valid MCP client token available!")
    return False


def update_env_file(key: str, value: str):
    """Update a key in the .env file"""
    env_file = Path(".env")
    lines = []
    found = False
    
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
    
    if not found:
        lines.append(f"{key}={value}\n")
    
    with open(env_file, 'w') as f:
        f.writelines(lines)


async def validate_all_tokens():
    """Validate all tokens are properly set"""
    print("\n🔍 Validating all tokens...")
    
    required_tokens = {
        "GATEWAY_OAUTH_ACCESS_TOKEN": "Gateway OAuth access token",
        "MCP_CLIENT_ACCESS_TOKEN": "MCP client access token",
        "BASE_DOMAIN": "Base domain",
        "GITHUB_CLIENT_ID": "GitHub OAuth client ID",
        "GITHUB_CLIENT_SECRET": "GitHub OAuth client secret",
        "GATEWAY_JWT_SECRET": "JWT signing secret"
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
            print(f"❌ Gateway token is expired!")
            all_valid = False
        elif ttl < 300:  # Less than 5 minutes
            print(f"⚠️  Gateway token expires soon ({ttl} seconds)")
            all_valid = False
        else:
            print(f"✅ Gateway token valid for {ttl/3600:.1f} hours")
    
    return all_valid


async def main():
    """Main function to refresh and validate all tokens"""
    print("=" * 60)
    print("🔐 AUTOMATIC TOKEN REFRESH FOR TESTS")
    print("=" * 60)
    
    # Load environment
    if not load_env_file():
        print("❌ Failed to load .env file!")
        sys.exit(1)
    
    # Check current token status
    gateway_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    needs_refresh = False
    
    if not gateway_token:
        print("❌ No gateway token found!")
        needs_refresh = True
    else:
        is_valid, ttl = check_token_expiry(gateway_token)
        if not is_valid:
            print(f"❌ Gateway token is expired!")
            needs_refresh = True
        elif ttl < 3600:  # Less than 1 hour
            print(f"⚠️  Gateway token expires in {ttl/60:.1f} minutes")
            needs_refresh = True
        else:
            print(f"✅ Gateway token valid for {ttl/3600:.1f} hours")
    
    # Refresh if needed
    if needs_refresh:
        if not await refresh_oauth_token():
            print("\n❌ Failed to refresh OAuth tokens!")
            print("   Please run: just generate-github-token")
            sys.exit(1)
    
    # Check GitHub PAT
    github_pat_result = await refresh_github_token()
    if github_pat_result is False:
        print("\n❌ GitHub PAT is invalid!")
        print("   Tests that require GitHub API will fail.")
        print("   To fix: just generate-github-token")
        # Don't exit - let tests fail as user requested
    elif github_pat_result is None:
        print("\n⚠️  No GitHub PAT configured")
        print("   OAuth flow tests will be skipped.")
        print("   To run all tests: just generate-github-token")
    
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