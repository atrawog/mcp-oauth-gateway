#!/usr/bin/env python3
"""Generate RSA private key and add it to .env file
Following CLAUDE.md Commandment 4: Configure Only Through .env Files.
"""
import base64
import os
import re
import sys

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_rsa_key_to_env(force=False):
    """Generate RSA private key and add/update it in .env file."""
    # Read existing .env file
    env_file_path = '.env'
    if not os.path.exists(env_file_path):
        print(f"❌ {env_file_path} not found!")
        print("Run this script from the project root directory.")
        sys.exit(1)

    with open(env_file_path) as f:
        env_content = f.read()

    # Check if JWT_PRIVATE_KEY_B64 already exists
    jwt_key_pattern = r'^JWT_PRIVATE_KEY_B64=.*$'
    existing_match = re.search(jwt_key_pattern, env_content, re.MULTILINE)

    if existing_match and not force:
        # Key already exists - do nothing
        print("✅ JWT_PRIVATE_KEY_B64 already exists in .env file. No action needed.")
        return

    # Generate new RSA key
    print("\n🔑 Generating new RSA key for RS256 JWT signing...")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Serialize private key
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Base64 encode for .env storage (single line)
    private_key_b64 = base64.b64encode(private_key_pem).decode('utf-8')

    if existing_match:
        # Update existing key
        print("🔄 Updating existing JWT_PRIVATE_KEY_B64 in .env...")
        env_content = re.sub(
            jwt_key_pattern,
            f'JWT_PRIVATE_KEY_B64={private_key_b64}',
            env_content,
            flags=re.MULTILINE
        )
    else:
        # Add new key at the end
        print("➕ Adding JWT_PRIVATE_KEY_B64 to .env...")
        if not env_content.endswith('\n'):
            env_content += '\n'
        env_content += f'JWT_PRIVATE_KEY_B64={private_key_b64}\n'

    # Write back to .env file
    with open(env_file_path, 'w') as f:
        f.write(env_content)

    print("✅ RSA private key successfully added to .env file!")
    print("🔐 The private key is base64 encoded for safe storage in environment variables.")

    # Also show the public key for verification
    public_key = private_key.public_key()
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    print("\n📋 New public key (for verification):")
    print(public_key_pem.decode('utf-8'))

    print("🚀 You can now restart the auth service to use the new RSA key!")
    print("   Run: just down && just up")
    print("\n⚠️  WARNING: All existing JWT tokens are now invalid!")
    print("   You will need to regenerate tokens with: just generate-github-token")

if __name__ == "__main__":
    # Check for --force flag
    force = '--force' in sys.argv
    if force:
        print("🚨 Force mode enabled - will overwrite existing RSA key without confirmation!")
    generate_rsa_key_to_env(force=force)
