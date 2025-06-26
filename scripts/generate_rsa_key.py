#!/usr/bin/env python3
"""Generate RSA private key for .env file."""

import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_rsa_key():
    """Generate RSA private key and return as base64 encoded string for .env."""
    # Generate new RSA key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

    # Serialize private key
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Base64 encode for .env storage (single line)
    private_key_b64 = base64.b64encode(private_key_pem).decode("utf-8")

    print("# Add this to your .env file:")
    print(f"JWT_PRIVATE_KEY_B64={private_key_b64}")

    # Also show the public key for verification
    public_key = private_key.public_key()
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    print("\n# Private key (PEM format):")
    print(private_key_pem.decode("utf-8"))

    print("\n# Public key (PEM format):")
    print(public_key_pem.decode("utf-8"))


if __name__ == "__main__":
    generate_rsa_key()
