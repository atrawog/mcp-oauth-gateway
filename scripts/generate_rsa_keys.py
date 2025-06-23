#!/usr/bin/env python3
"""Generate RSA key pair for JWT signing."""

import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_rsa_keys():
    """Generate RSA key pair and return base64 encoded versions."""
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # Get private key in PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Get public key
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Base64 encode
    private_b64 = base64.b64encode(private_pem).decode("utf-8")
    public_b64 = base64.b64encode(public_pem).decode("utf-8")

    return private_b64, public_b64


if __name__ == "__main__":
    print("Generating new RSA key pair...")
    private_b64, public_b64 = generate_rsa_keys()

    print("\nAdd this to your .env file:")
    print(f"JWT_PRIVATE_KEY_B64={private_b64}")

    # Save to file for backup
    with open("rsa_keys_backup.txt", "w") as f:
        f.write(f"JWT_PRIVATE_KEY_B64={private_b64}\n")
        f.write("# Public key (for reference):\n")
        f.write(f"# JWT_PUBLIC_KEY_B64={public_b64}\n")

    print("\nKeys also saved to rsa_keys_backup.txt")
