#!/usr/bin/env python3
"""Generate RSA private key and add it to .env file.

Following CLAUDE.md Commandment 0: Root Cause Analysis - validates existing keys
and auto-regenerates invalid/placeholder keys to prevent startup failures.

Following CLAUDE.md Commandment 4: Configure Only Through .env Files.
"""

import base64
import os
import re
import sys

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def validate_existing_jwt_key(env_content):
    """Validate if existing JWT_PRIVATE_KEY_B64 is a valid RSA private key.

    Returns:
        tuple: (is_valid: bool, key_value: str|None, reason: str)

    """
    # Extract canonical or compatibility JWT key value
    jwt_key_pattern = r"^(?:OAUTH_)?JWT_PRIVATE_KEY_B64=(.*)$"
    existing_match = re.search(jwt_key_pattern, env_content, re.MULTILINE)

    if not existing_match:
        return False, None, "JWT_PRIVATE_KEY_B64 not found"

    key_value = existing_match.group(1).strip()

    # Check for placeholder values
    placeholder_patterns = [
        "your_base64_encoded_private_key_here",
        "YOUR_BASE64_ENCODED_PRIVATE_KEY_HERE",
        "placeholder",
        "PLACEHOLDER",
        "",
    ]

    if key_value in placeholder_patterns:
        return False, key_value, f"Placeholder value detected: '{key_value}'"

    # Validate base64 encoding
    try:
        decoded_key = base64.b64decode(key_value, validate=True)
    except Exception as e:
        return False, key_value, f"Invalid base64 encoding: {e}"

    # Validate RSA private key format
    try:
        private_key = serialization.load_pem_private_key(
            decoded_key, password=None, backend=default_backend()
        )

        # Verify it's actually an RSA key
        if not isinstance(private_key, rsa.RSAPrivateKey):
            return False, key_value, "Not an RSA private key"

        # Additional sanity check - ensure key size is reasonable
        key_size = private_key.key_size
        if key_size < 2048:
            return False, key_value, f"Key size too small: {key_size} bits (minimum 2048)"

    except Exception as e:
        return False, key_value, f"Invalid RSA private key: {e}"

    return True, key_value, "Valid RSA private key"


def generate_rsa_key_to_env(force=False):
    """Generate RSA private key and add/update it in .env file."""
    # Read existing .env file
    env_file_path = ".env"
    if not os.path.exists(env_file_path):
        print(f"❌ {env_file_path} not found!")
        print("Run this script from the project root directory.")
        sys.exit(1)

    with open(env_file_path) as f:
        env_content = f.read()

    # Validate existing JWT_PRIVATE_KEY_B64
    is_valid, key_value, reason = validate_existing_jwt_key(env_content)
    jwt_key_pattern = r"^JWT_PRIVATE_KEY_B64=.*$"
    oauth_jwt_key_pattern = r"^OAUTH_JWT_PRIVATE_KEY_B64=.*$"
    existing_match = re.search(jwt_key_pattern, env_content, re.MULTILINE)
    existing_oauth_match = re.search(oauth_jwt_key_pattern, env_content, re.MULTILINE)

    if is_valid and not force:
        # Key exists and is valid - do nothing
        print("✅ JWT_PRIVATE_KEY_B64 already exists and is valid. No action needed.")
        print(f"   Validation: {reason}")
        return
    if existing_match and not is_valid:
        # Key exists but is invalid - explain why we're regenerating
        print(f"⚠️  JWT_PRIVATE_KEY_B64 exists but is invalid: {reason}")
        print("🔄 Auto-regenerating to fix the issue...")
    elif force and existing_match:
        # Force mode - regenerating valid key
        print("🚨 Force mode: regenerating existing key...")
    elif not existing_match:
        # No key exists
        print("➕ JWT_PRIVATE_KEY_B64 not found, generating new key...")

    # Generate new RSA key
    print("\n🔑 Generating new RSA key for RS256 JWT signing...")
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # Serialize private key
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Base64 encode for .env storage (single line)
    private_key_b64 = base64.b64encode(private_key_pem).decode("utf-8")

    if existing_oauth_match:
        print("🔄 Updating existing OAUTH_JWT_PRIVATE_KEY_B64 in .env...")
        env_content = re.sub(
            oauth_jwt_key_pattern,
            f"OAUTH_JWT_PRIVATE_KEY_B64={private_key_b64}",
            env_content,
            flags=re.MULTILINE,
        )
    else:
        print("➕ Adding OAUTH_JWT_PRIVATE_KEY_B64 to .env...")
        if not env_content.endswith("\n"):
            env_content += "\n"
        env_content += f"OAUTH_JWT_PRIVATE_KEY_B64={private_key_b64}\n"

    if existing_match:
        print("🔄 Updating existing JWT_PRIVATE_KEY_B64 in .env...")
        env_content = re.sub(
            jwt_key_pattern,
            f"JWT_PRIVATE_KEY_B64={private_key_b64}",
            env_content,
            flags=re.MULTILINE,
        )
    else:
        print("➕ Adding JWT_PRIVATE_KEY_B64 to .env...")
        if not env_content.endswith("\n"):
            env_content += "\n"
        env_content += f"JWT_PRIVATE_KEY_B64={private_key_b64}\n"

    # Write back to .env file
    with open(env_file_path, "w") as f:
        f.write(env_content)

    print("✅ RSA private key successfully added to .env file!")
    print("🔐 The private key is base64 encoded for safe storage in environment variables.")

    # Also show the public key for verification
    public_key = private_key.public_key()
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    print("\n📋 New public key (for verification):")
    print(public_key_pem.decode("utf-8"))

    print("🚀 You can now restart the auth service to use the new RSA key!")
    print("   Run: just down && just up")
    print("\n⚠️  WARNING: All existing JWT tokens are now invalid!")
    print("   You will need to regenerate tokens with: just generate-github-token")


if __name__ == "__main__":
    # Check for --force flag
    force = "--force" in sys.argv
    if force:
        print("🚨 Force mode enabled - will overwrite existing RSA key without confirmation!")
    generate_rsa_key_to_env(force=force)
