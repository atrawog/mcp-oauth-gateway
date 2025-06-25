#!/usr/bin/env python3
"""Generate a test JWT token for non-interactive environments."""

import base64
import os
import sys
import time
from pathlib import Path

from authlib.jose import jwt


def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent.parent / ".env"
    env_vars = {}
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove inline comments
                    if '#' in value and not (value.startswith('"') and value.endswith('"')):
                        value = value.split('#', 1)[0]
                    # Strip quotes if present
                    value = value.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                        value = value[1:-1]
                    env_vars[key.strip()] = value
    return env_vars


def main():
    """Generate a test JWT token."""
    # Load environment
    env_vars = load_env()
    os.environ.update(env_vars)
    
    # Get required variables
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "RS256")
    
    if jwt_algorithm == "RS256":
        # Get RSA private key
        private_key_b64 = os.getenv("JWT_PRIVATE_KEY_B64")
        if not private_key_b64:
            print("❌ JWT_PRIVATE_KEY_B64 not found in environment")
            sys.exit(1)
        
        # Decode base64 private key
        private_key = base64.b64decode(private_key_b64).decode('utf-8')
        secret = private_key
    else:
        # Get JWT secret for HS256
        secret = os.getenv("GATEWAY_JWT_SECRET")
        if not secret:
            print("❌ GATEWAY_JWT_SECRET not found in environment")
            sys.exit(1)
    
    # Create test payload
    now = int(time.time())
    payload = {
        "sub": "test-user",
        "username": "test-user",
        "email": "test@example.com",
        "name": "Test User",
        "user_id": "12345",
        "iat": now,
        "exp": now + 86400,  # 24 hours
        "scope": "openid profile email",
        "client_id": os.getenv("GATEWAY_OAUTH_CLIENT_ID", "test-client"),
        "jti": f"test-{now}"
    }
    
    # Create header
    header = {"alg": jwt_algorithm}
    
    # Encode token
    token = jwt.encode(header, payload, secret)
    
    # Convert bytes to string if needed
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    
    print(f"Generated test token: {token}")
    
    # Save to .env
    env_file = Path(__file__).parent.parent / ".env"
    lines = []
    found = False
    
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip().startswith("GATEWAY_OAUTH_ACCESS_TOKEN="):
                    lines.append(f"GATEWAY_OAUTH_ACCESS_TOKEN={token}\n")
                    found = True
                else:
                    lines.append(line)
    
    if not found:
        lines.append(f"\nGATEWAY_OAUTH_ACCESS_TOKEN={token}\n")
    
    with open(env_file, "w") as f:
        f.writelines(lines)
    
    print("✅ Token saved to .env")


if __name__ == "__main__":
    main()