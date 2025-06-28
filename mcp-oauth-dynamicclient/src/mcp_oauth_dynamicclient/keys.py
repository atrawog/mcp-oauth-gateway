"""RSA Key Management for RS256 JWT - The ONLY Blessed Algorithm!"""

import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


class RSAKeyManager:
    """Divine RSA Key Management - RS256 brings cryptographic blessing!"""

    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.private_key_pem = None
        self.public_key_pem = None

    def load_or_generate_keys(self):
        """Load RSA keys from environment variables or generate new ones"""
        # Try to load from environment variables first (preferred method)
        jwt_private_key_b64 = os.getenv("JWT_PRIVATE_KEY_B64")

        if jwt_private_key_b64:
            # Load from environment variable (base64 encoded)
            try:
                self.private_key_pem = base64.b64decode(jwt_private_key_b64)
                self.private_key = serialization.load_pem_private_key(
                    self.private_key_pem,
                    password=None,
                    backend=default_backend(),
                )
                self.public_key = self.private_key.public_key()
                self.public_key_pem = self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                return
            except Exception as e:
                raise ValueError(
                    f"Failed to load RSA private key from JWT_PRIVATE_KEY_B64: {e}",
                ) from e

        # Fallback: Try to load from files (legacy support)
        private_key_path = "/app/keys/private_key.pem"
        public_key_path = "/app/keys/public_key.pem"

        if os.path.exists(private_key_path) and os.path.exists(public_key_path):
            # Load existing blessed keys from files
            with open(private_key_path, "rb") as f:
                self.private_key_pem = f.read()
                self.private_key = serialization.load_pem_private_key(
                    self.private_key_pem,
                    password=None,
                    backend=default_backend(),
                )

            with open(public_key_path, "rb") as f:
                self.public_key_pem = f.read()
                self.public_key = serialization.load_pem_public_key(
                    self.public_key_pem,
                    backend=default_backend(),
                )
            return

        # If no keys found, raise an error instead of generating
        raise ValueError(
            "No RSA keys found! Please run 'just generate-rsa-keys' to create JWT_PRIVATE_KEY_B64 "
            "in your .env file, or provide JWT_PRIVATE_KEY_B64 environment variable.",
        )

    def get_jwk(self):
        """Get JWK representation for JWKS endpoint"""
        from authlib.jose import JsonWebKey

        # Create JWK from public key PEM data
        jwk_data = JsonWebKey.import_key(self.public_key_pem).as_dict()
        # Add required metadata
        jwk_data["use"] = "sig"
        jwk_data["alg"] = "RS256"
        jwk_data["kid"] = "blessed-key-1"  # Key ID for rotation
        return jwk_data
