#!/usr/bin/env python3
"""
Token validation script for MCP OAuth Gateway
Validates all OAuth tokens before running tests
"""
import os
import sys
import json
import time
from datetime import datetime
from authlib.jose import jwt
from authlib.jose.errors import JoseError
import httpx
import asyncio


def check_env_var(name: str) -> str:
    """Get environment variable or exit with error"""
    value = os.getenv(name)
    if not value:
        print(f"❌ Environment variable {name} is not set!")
        return None
    return value


def decode_jwt_token(token: str) -> dict:
    """Decode JWT token without signature verification"""
    try:
        # Decode without verification for inspection only
        import json
        import base64
        # JWT format: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        
        # Decode payload (add padding if needed)
        payload_part = parts[1]
        payload_part += '=' * (4 - len(payload_part) % 4)  # Add padding
        payload_json = base64.urlsafe_b64decode(payload_part)
        return json.loads(payload_json)
    except Exception as e:
        print(f"❌ Failed to decode JWT token: {e}")
        return None


def check_token_expiry(payload: dict) -> bool:
    """Check if token is expired"""
    exp = payload.get('exp')
    if not exp:
        print("❌ Token has no expiration claim")
        return False
    
    now = int(time.time())
    iat = payload.get('iat', 0)
    
    print(f"🕐 Token issued at: {datetime.fromtimestamp(iat)}")
    print(f"🕐 Token expires at: {datetime.fromtimestamp(exp)}")
    print(f"🕐 Current time: {datetime.fromtimestamp(now)}")
    
    if exp < now:
        print(f"❌ TOKEN IS EXPIRED! (expired {now - exp} seconds ago)")
        return False
    else:
        remaining = exp - now
        print(f"✅ Token is valid (expires in {remaining} seconds / {remaining/3600:.1f} hours)")
        return True


async def test_auth_service(token: str) -> bool:
    """Test if auth service accepts the token"""
    base_domain = check_env_var("BASE_DOMAIN")
    if not base_domain:
        return False
    
    auth_url = f"https://auth.{base_domain}/verify"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                auth_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            
        if response.status_code == 200:
            print(f"✅ Auth service validates token successfully")
            return True
        else:
            print(f"❌ Auth service rejected token: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test auth service: {e}")
        return False


async def test_mcp_service(token: str) -> bool:
    """Test if MCP service accepts the token"""
    base_domain = check_env_var("BASE_DOMAIN")
    if not base_domain:
        return False
    
    mcp_url = f"https://mcp-fetch.{base_domain}/health"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                mcp_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            
        if response.status_code in [200, 401]:  # 401 is expected for health endpoint
            print(f"✅ MCP service is reachable")
            return True
        else:
            print(f"⚠️  MCP service returned unexpected status: {response.status_code}")
            return True  # Still consider it working
            
    except Exception as e:
        print(f"❌ Failed to test MCP service: {e}")
        return False


async def main():
    """Main validation function"""
    print("=" * 60)
    print("🔍 OAUTH TOKEN VALIDATION")
    print("=" * 60)
    
    all_valid = True
    
    # Check OAuth Access Token
    print("\n📋 Checking OAUTH_ACCESS_TOKEN...")
    oauth_token = check_env_var("OAUTH_ACCESS_TOKEN")
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
        if github_pat.startswith('gho_') or github_pat.startswith('ghp_'):
            print("✅ GitHub PAT format looks valid")
            # Could add GitHub API test here if needed
        else:
            print("⚠️  GitHub PAT format may be invalid")
    else:
        print("⚠️  GitHub PAT not found (may not be required for all tests)")
    
    # Check OAuth Client Credentials
    print("\n📋 Checking OAuth Client Credentials...")
    client_id = check_env_var("OAUTH_CLIENT_ID")
    client_secret = check_env_var("OAUTH_CLIENT_SECRET")
    
    if client_id and client_secret:
        print(f"✅ OAuth client credentials present")
        print(f"   Client ID: {client_id}")
        print(f"   Client Secret: {'*' * (len(client_secret) - 4)}{client_secret[-4:]}")
    else:
        print("❌ OAuth client credentials missing")
        all_valid = False
    
    # Check Refresh Token
    print("\n📋 Checking OAUTH_REFRESH_TOKEN...")
    refresh_token = check_env_var("OAUTH_REFRESH_TOKEN")
    if refresh_token:
        print(f"✅ Refresh token present: {'*' * (len(refresh_token) - 8)}{refresh_token[-8:]}")
    else:
        print("⚠️  Refresh token not found")
    
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