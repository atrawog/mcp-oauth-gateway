#!/usr/bin/env python3
"""
Token expiry checker for MCP OAuth Gateway
Checks if tokens are expired and suggests refresh
"""
import os
import sys
import time
from datetime import datetime
from jose import jwt, JWTError


def check_jwt_expiry(token_name: str, token: str) -> bool:
    """Check JWT token expiry"""
    try:
        payload = jwt.decode(token, key="", options={'verify_signature': False})
        exp = payload.get('exp')
        
        if not exp:
            print(f"⚠️  {token_name}: No expiration claim found")
            return True  # Assume valid if no expiry
        
        now = int(time.time())
        iat = payload.get('iat', 0)
        
        print(f"\n🔍 {token_name}:")
        print(f"   Issued: {datetime.fromtimestamp(iat)}")
        print(f"   Expires: {datetime.fromtimestamp(exp)}")
        print(f"   Current: {datetime.fromtimestamp(now)}")
        
        if exp < now:
            expired_for = now - exp
            print(f"   ❌ EXPIRED {expired_for} seconds ago ({expired_for/3600:.1f} hours)")
            return False
        else:
            remaining = exp - now
            hours_left = remaining / 3600
            days_left = remaining / 86400
            
            if days_left > 1:
                print(f"   ✅ Valid for {days_left:.1f} more days")
            elif hours_left > 1:
                print(f"   ✅ Valid for {hours_left:.1f} more hours")
            else:
                print(f"   ⚠️  Expires soon: {remaining} seconds remaining")
                
            return True
            
    except JWTError as e:
        print(f"❌ {token_name}: Failed to decode JWT - {e}")
        return False


def main():
    """Main expiry check function"""
    print("⏰ TOKEN EXPIRY CHECK")
    print("=" * 50)
    
    all_valid = True
    
    # Check OAuth Access Token
    oauth_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    if oauth_token:
        if not check_jwt_expiry("GATEWAY_OAUTH_ACCESS_TOKEN", oauth_token):
            all_valid = False
    else:
        print("❌ GATEWAY_OAUTH_ACCESS_TOKEN not found in environment")
        all_valid = False
    
    # Check other tokens that might exist
    oauth_jwt = os.getenv("GATEWAY_JWT_SECRET")
    if oauth_jwt:
        if not check_jwt_expiry("GATEWAY_JWT_SECRET", oauth_jwt):
            all_valid = False
    
    print("\n" + "=" * 50)
    
    if all_valid:
        print("✅ All tokens are valid and not expired")
    else:
        print("❌ Some tokens are expired or invalid!")
        print("\n🔧 To fix expired tokens:")
        print("   1. Run: just refresh-tokens")
        print("   2. Or regenerate: just generate-github-token")
        
    return all_valid


if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)