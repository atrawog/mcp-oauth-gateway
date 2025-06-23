#!/usr/bin/env python3
"""Show the current RSA public key from .env file."""
import base64
import os
import re
import sys

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


def show_rsa_public_key():
    """Show the current RSA public key from JWT_PRIVATE_KEY_B64 in .env."""
    # Read existing .env file
    env_file_path = '.env'
    if not os.path.exists(env_file_path):
        print(f"❌ {env_file_path} not found!")
        print("Run this script from the project root directory.")
        sys.exit(1)

    with open(env_file_path) as f:
        env_content = f.read()

    # Check if JWT_PRIVATE_KEY_B64 exists
    jwt_key_pattern = r'^JWT_PRIVATE_KEY_B64=.*$'
    existing_match = re.search(jwt_key_pattern, env_content, re.MULTILINE)

    if not existing_match:
        print("❌ JWT_PRIVATE_KEY_B64 not found in .env file!")
        print("Run 'just generate-rsa-keys' to create one.")
        sys.exit(1)

    # Extract and decode the key
    try:
        current_key_b64 = existing_match.group(0).split('=', 1)[1].strip()
        if not current_key_b64:
            print("❌ JWT_PRIVATE_KEY_B64 is empty!")
            sys.exit(1)

        current_key_pem = base64.b64decode(current_key_b64)
        current_private_key = serialization.load_pem_private_key(
            current_key_pem,
            password=None,
            backend=default_backend()
        )
        current_public_key = current_private_key.public_key()
        current_public_pem = current_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        print("📋 Current RSA public key:")
        print(current_public_pem.decode('utf-8'))

        # Also show key fingerprint
        from cryptography.hazmat.primitives import hashes
        key_der = current_public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(key_der)
        fingerprint = digest.finalize()
        fingerprint_hex = ':'.join(f'{b:02x}' for b in fingerprint)

        print(f"\n🔏 Key fingerprint (SHA256): {fingerprint_hex}")

    except Exception as e:
        print(f"❌ Error parsing RSA key: {e}")
        sys.exit(1)

if __name__ == "__main__":
    show_rsa_public_key()
