"""Async-compatible ResourceProtector for FastAPI
Since Authlib's ResourceProtector doesn't support async natively,
we create a wrapper that works with FastAPI's async handlers.
"""

from typing import Any, Optional

import redis.asyncio as redis
from fastapi import HTTPException, Request

from .config import Settings
from .keys import RSAKeyManager
from .resource_protector import JWTBearerTokenValidator


class AsyncResourceProtector:
    """Async wrapper for Authlib's ResourceProtector that works with FastAPI.
    This maintains the security benefits of ResourceProtector while supporting async operations.
    """

    def __init__(self, settings: Settings, redis_client: redis.Redis, key_manager: RSAKeyManager):
        self.settings = settings
        self.redis_client = redis_client
        self.key_manager = key_manager
        self.validator = JWTBearerTokenValidator(settings, redis_client, key_manager)

    async def validate_request(self, request: Request) -> Optional[dict[str, Any]]:
        """Validate the request and extract token information.

        Args:
            request: FastAPI Request object

        Returns:
            Token claims if valid, raises HTTPException if invalid

        """
        # Check if request is valid
        error = self.validator.request_invalid(request)
        if error:
            raise HTTPException(
                status_code=401,
                detail={"error": "invalid_request", "error_description": error},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_request",
                    "error_description": "Authorization header must use Bearer scheme",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_string = auth_header[7:]  # Remove "Bearer " prefix

        # Validate token asynchronously
        token_data = await self.validator.authenticate_token(token_string)

        if not token_data:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "invalid_token",
                    "error_description": "The access token is invalid or expired",
                },
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        return token_data


def create_async_resource_protector(
    settings: Settings,
    redis_client: redis.Redis,
    key_manager: RSAKeyManager,
) -> AsyncResourceProtector:
    """Create an async-compatible ResourceProtector instance.

    Args:
        settings: Application settings
        redis_client: Redis client for token storage
        key_manager: RSA key manager for JWT validation

    Returns:
        AsyncResourceProtector instance

    """
    return AsyncResourceProtector(settings, redis_client, key_manager)
