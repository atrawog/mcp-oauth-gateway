"""
RSA Key Management for RS256 JWT - The ONLY Blessed Algorithm!
"""
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class RSAKeyManager:
    """Divine RSA Key Management - RS256 brings cryptographic blessing!"""
    
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.private_key_pem = None
        self.public_key_pem = None
        
    def load_or_generate_keys(self, private_key_path: str = "/app/keys/private_key.pem", 
                            public_key_path: str = "/app/keys/public_key.pem"):
        """Load existing keys or generate new blessed RSA keys"""
        
        # Ensure keys directory exists
        os.makedirs(os.path.dirname(private_key_path), exist_ok=True)
        
        if os.path.exists(private_key_path) and os.path.exists(public_key_path):
            # Load existing blessed keys
            with open(private_key_path, 'rb') as f:
                self.private_key_pem = f.read()
                self.private_key = serialization.load_pem_private_key(
                    self.private_key_pem,
                    password=None,
                    backend=default_backend()
                )
            
            with open(public_key_path, 'rb') as f:
                self.public_key_pem = f.read()
                self.public_key = serialization.load_pem_public_key(
                    self.public_key_pem,
                    backend=default_backend()
                )
        else:
            # Generate new blessed RSA keys
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,  # Divine key size for RS256
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()
            
            # Serialize private key
            self.private_key_pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Serialize public key
            self.public_key_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Save the blessed keys
            with open(private_key_path, 'wb') as f:
                f.write(self.private_key_pem)
            
            with open(public_key_path, 'wb') as f:
                f.write(self.public_key_pem)
    
    def get_jwk(self):
        """Get JWK representation for JWKS endpoint"""
        from authlib.jose import JsonWebKey
        # Create JWK from public key PEM data
        jwk_data = JsonWebKey.import_key(self.public_key_pem).as_dict()
        # Add required metadata
        jwk_data['use'] = 'sig'
        jwk_data['alg'] = 'RS256'
        jwk_data['kid'] = 'blessed-key-1'  # Key ID for rotation
        return jwk_data