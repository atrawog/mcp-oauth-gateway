"""OAuth 2.0 Resource Protection using Authlib's ResourceProtector
Following security best practices - NO AD-HOC IMPLEMENTATIONS!
"""

from datetime import datetime, timezone
from typing import Any, Optional

import redis.asyncio as redis
from authlib.jose import JsonWebToken
from authlib.jose.errors import JoseError
from authlib.oauth2 import ResourceProtector
from authlib.oauth2.rfc6750 import BearerTokenValidator
from authlib.oauth2.rfc6750.errors import InvalidTokenError as BearerTokenError

from .config import Settings
from .keys import RSAKeyManager


class JWTBearerTokenValidator(BearerTokenValidator):
    """JWT Bearer token validator for Authlib's ResourceProtector.
    This replaces the custom verify_jwt_token implementation with
    Authlib's battle-tested security framework.
    """

    def __init__(self, settings: Settings, redis_client: redis.Redis, key_manager: RSAKeyManager):
        super().__init__()
        self.settings = settings
        self.redis_client = redis_client
        self.key_manager = key_manager
        self.jwt = JsonWebToken(algorithms=[settings.jwt_algorithm])

    async def authenticate_token(self, token_string: str) -> Optional[dict[str, Any]]:
        """Authenticate the bearer token.
        This method is called by ResourceProtector to validate tokens.

        Returns:
            Token claims if valid, None if invalid

        """
        try:
            # Decode and validate token using Authlib
            if self.settings.jwt_algorithm == "RS256":
                # Use RSA public key for RS256 verification
                claims = self.jwt.decode(
                    token_string,
                    self.key_manager.public_key,
                    claims_options={
                        "iss": {
                            "essential": True,
                            "value": f"https://auth.{self.settings.base_domain}",
                        },
                        "exp": {"essential": True},
                        "jti": {"essential": True},
                    },
                )
            else:
                # HS256 fallback during transition period
                claims = self.jwt.decode(
                    token_string,
                    self.settings.jwt_secret,
                    claims_options={
                        "iss": {
                            "essential": True,
                            "value": f"https://auth.{self.settings.base_domain}",
                        },
                        "exp": {"essential": True},
                        "jti": {"essential": True},
                    },
                )

            # Validate claims
            claims.validate()

            # Check if token exists in Redis (not revoked)
            jti = claims["jti"]
            token_data = await self.redis_client.get(f"oauth:token:{jti}")

            if not token_data:
                # Token has been revoked or doesn't exist
                return None

            # Return claims as dict for ResourceProtector
            return dict(claims)

        except JoseError as e:
            # Token validation failed
            print(f"JWT validation error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error during token validation: {e}")
            return None

    def request_invalid(self, request) -> Optional[str]:
        """Check if the request is invalid.
        Returns an error message if invalid, None if valid.
        """
        # Get authorization header
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            return "Missing Authorization header"

        if not auth_header.startswith("Bearer "):
            return "Authorization header must use Bearer scheme"

        # Token will be validated in authenticate_token
        return None

    def token_revoked(self, token: dict[str, Any]) -> bool:
        """Check if the token has been revoked.
        Since we already check Redis in authenticate_token,
        we can return False here.
        """
        return False


class IntrospectionBearerTokenValidator(JWTBearerTokenValidator):
    """Extended validator for token introspection endpoint.
    Allows introspection of expired tokens.
    """

    async def authenticate_token(self, token_string: str) -> Optional[dict[str, Any]]:
        """Authenticate token for introspection - allows expired tokens."""
        try:
            # Decode without exp validation for introspection
            if self.settings.jwt_algorithm == "RS256":
                claims = self.jwt.decode(
                    token_string,
                    self.key_manager.public_key,
                    claims_options={
                        "iss": {
                            "essential": True,
                            "value": f"https://auth.{self.settings.base_domain}",
                        },
                        "jti": {"essential": True},
                        "exp": {"essential": False},  # Don't require valid exp for introspection
                    },
                )
            else:
                claims = self.jwt.decode(
                    token_string,
                    self.settings.jwt_secret,
                    claims_options={
                        "iss": {
                            "essential": True,
                            "value": f"https://auth.{self.settings.base_domain}",
                        },
                        "jti": {"essential": True},
                        "exp": {"essential": False},
                    },
                )

            # Check if token exists in Redis
            jti = claims.get("jti")
            if jti:
                token_data = await self.redis_client.get(f"oauth:token:{jti}")
                if token_data:
                    # Add active status based on expiration
                    claims["active"] = claims.get("exp", 0) > datetime.now(timezone.utc).timestamp()
                    return dict(claims)

            # Token not in Redis - it's been revoked
            return {"active": False}

        except JoseError:
            # Can't decode token - return inactive
            return {"active": False}


def create_resource_protector(
    settings: Settings,
    redis_client: redis.Redis,
    key_manager: RSAKeyManager,
) -> ResourceProtector:
    """Create and configure a ResourceProtector instance.
    This replaces the manual token validation with Authlib's secure implementation.
    """
    # Create the resource protector
    require_oauth = ResourceProtector()

    # Register our JWT bearer token validator
    validator = JWTBearerTokenValidator(settings, redis_client, key_manager)
    require_oauth.register_token_validator(validator)

    return require_oauth


def create_introspection_protector(
    settings: Settings,
    redis_client: redis.Redis,
    key_manager: RSAKeyManager,
) -> ResourceProtector:
    """Create a ResourceProtector specifically for token introspection.
    This allows inspection of expired tokens.
    """
    # Create the resource protector
    introspect_oauth = ResourceProtector()

    # Register our introspection validator
    validator = IntrospectionBearerTokenValidator(settings, redis_client, key_manager)
    introspect_oauth.register_token_validator(validator)

    return introspect_oauth


# Error handler for OAuth errors
def handle_oauth_error(error: BearerTokenError) -> dict:
    """Convert Authlib OAuth errors to our error format."""
    return {"error": error.error, "error_description": error.description, "error_uri": error.uri}
