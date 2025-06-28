"""RFC 7592 - OAuth 2.0 Dynamic Client Registration Management Protocol
Implementation using Authlib's patterns
"""

import json
import secrets
from typing import Optional

import redis.asyncio as redis
from authlib.oauth2.rfc7592 import ClientConfigurationEndpoint as BaseClientConfigurationEndpoint

from .auth_authlib import OAuth2Client
from .config import Settings


class DynamicClientConfigurationEndpoint(BaseClientConfigurationEndpoint):
    """Divine implementation of RFC 7592 using Authlib!
    Manages the lifecycle of dynamically registered OAuth clients.
    """

    def __init__(self, settings: Settings, redis_client: redis.Redis):
        self.settings = settings
        self.redis_client = redis_client
        super().__init__()

    async def authenticate_token(self, request) -> Optional[str]:
        """Validate registration access token from Authorization header.
        RFC 7592 requires Bearer authentication for client management.
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # Remove "Bearer " prefix
        return token

    async def authenticate_client(self, request, client_id: str) -> Optional[OAuth2Client]:
        """Retrieve and authenticate client by client_id using Bearer token.
        RFC 7592 requires registration_access_token authentication.
        Returns None if authentication fails, raises ValueError if client not found.
        """
        # Get Bearer token from request
        token = await self.authenticate_token(request)
        if not token:
            return None

        # Get client from Redis
        client_data_str = await self.redis_client.get(f"oauth:client:{client_id}")
        if not client_data_str:
            # Client doesn't exist - this should be a 404, not 401
            raise ValueError(f"Client {client_id} not found")

        client_data = json.loads(client_data_str)

        # Validate registration access token
        stored_token = client_data.get("registration_access_token")
        if not stored_token or not secrets.compare_digest(token, stored_token):
            return None

        return OAuth2Client(client_data)

    async def check_permission(self, client: OAuth2Client, request) -> bool:
        """Verify client has permission to modify its registration.
        With Bearer token auth, permission is implicit from successful authentication.
        """
        # Client authenticated via registration_access_token has full permissions
        return True

    async def update_client(self, client: OAuth2Client, client_metadata: dict) -> OAuth2Client:
        """Update client metadata in Redis.
        Returns updated client object.
        """
        client_id = client.get_client_id()

        # Get existing client data
        client_data_str = await self.redis_client.get(f"oauth:client:{client_id}")
        if not client_data_str:
            raise ValueError("Client not found")

        existing_data = json.loads(client_data_str)

        # Update allowed fields from metadata
        allowed_updates = [
            "redirect_uris",
            "client_name",
            "client_uri",
            "logo_uri",
            "contacts",
            "tos_uri",
            "policy_uri",
            "scope",
            "grant_types",
            "response_types",
        ]

        for field in allowed_updates:
            if field in client_metadata:
                if field == "redirect_uris":
                    # Store as JSON string for Redis
                    existing_data[field] = json.dumps(client_metadata[field])
                elif field in ["grant_types", "response_types"]:
                    # Also store as JSON strings
                    existing_data[field] = json.dumps(client_metadata[field])
                else:
                    existing_data[field] = client_metadata[field]

        # Calculate TTL if client has expiration
        if self.settings.client_lifetime > 0:
            ttl = self.settings.client_lifetime
            await self.redis_client.setex(
                f"oauth:client:{client_id}",
                ttl,
                json.dumps(existing_data),
            )
        else:
            # CLIENT_LIFETIME=0 means never expire
            await self.redis_client.set(
                f"oauth:client:{client_id}",
                json.dumps(existing_data),
            )  # TODO: Break long line

        return OAuth2Client(existing_data)

    async def delete_client(self, client: OAuth2Client):
        """Delete client registration from Redis.
        Implements the divine banishment of clients!
        """
        client_id = client.get_client_id()

        # Delete client from Redis
        await self.redis_client.delete(f"oauth:client:{client_id}")

        # Also delete any associated tokens (cleanup)
        # This is beyond RFC 7592 but good practice
        pattern = "oauth:token:*"
        cursor = 0
        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
            for key in keys:
                token_data = await self.redis_client.get(key)
                if token_data:
                    data = json.loads(token_data)
                    if data.get("client_id") == client_id:
                        await self.redis_client.delete(key)
            if cursor == 0:
                break

    async def revoke_access_token(self, client: OAuth2Client, token: str):
        """Revoke all access tokens for this client.
        Beyond RFC 7592 but useful for security.
        """
        # This would revoke all tokens issued to this client
        # Implementation depends on token storage strategy

    def generate_client_configuration_response(self, client: OAuth2Client) -> dict:
        """Generate RFC 7592 compliant response for client configuration."""
        client_data = client._client_data

        response = {
            "client_id": client_data["client_id"],
            "client_secret": client_data.get("client_secret"),
            "redirect_uris": json.loads(client_data.get("redirect_uris", "[]")),
            "grant_types": json.loads(client_data.get("grant_types", '["authorization_code"]')),
            "response_types": json.loads(client_data.get("response_types", '["code"]')),
            "client_name": client_data.get("client_name"),
            "scope": client_data.get("scope"),
        }

        # Add timestamps - REQUIRED by tests and good practice
        if "client_id_issued_at" in client_data:
            response["client_id_issued_at"] = client_data["client_id_issued_at"]

        # Add expiration if set
        if "client_secret_expires_at" in client_data:
            response["client_secret_expires_at"] = client_data["client_secret_expires_at"]

        # Add optional fields if present
        for field in ["client_uri", "logo_uri", "contacts", "tos_uri", "policy_uri"]:
            if field in client_data and client_data[field]:
                response[field] = client_data[field]

        return response
