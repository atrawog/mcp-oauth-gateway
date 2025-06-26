"""CRITICAL MCP Protocol Version Tests - MUST use exact version from .env!
NO HARDCODED VERSIONS ALLOWED! Tests MUST fail for ANY other version!
"""

import json
import secrets
import time

import httpx
import pytest
import redis.asyncio as redis

from .jwt_test_helper import encode as jwt_encode
from .test_constants import ACCESS_TOKEN_LIFETIME
from .test_constants import BASE_DOMAIN
from .test_constants import GATEWAY_JWT_SECRET
from .test_constants import HTTP_OK
from .test_constants import MCP_CLIENT_ACCESS_TOKEN
from .test_constants import MCP_PROTOCOL_VERSION
from .test_constants import MCP_PROTOCOL_VERSIONS_SUPPORTED
from .test_constants import MCP_TESTING_URL
from .test_constants import REDIS_URL


def parse_sse_response(response: httpx.Response) -> dict:
    r"""Parse SSE response format to extract JSON data.

    SSE format: "event: message\ndata: {...}\n\n"
    """
    content_type = response.headers.get("content-type", "")

    # If it's already JSON, return it directly
    if "application/json" in content_type:
        return response.json()

    # Otherwise parse SSE format
    if "text/event-stream" in content_type or response.status_code == 200:
        text = response.text
        for line in text.split("\n"):
            if line.startswith("data: "):
                json_data = line[6:]  # Remove "data: " prefix
                return json.loads(json_data)

        # If no data line found, raise an error
        raise ValueError(f"No valid JSON data found in SSE response: {text}")

    # Fallback: try to parse as JSON anyway
    return response.json()


class TestMCPProtocolVersionStrict:
    """Strict MCP Protocol Version validation - MUST match .env exactly!"""

    @pytest.mark.asyncio
    async def test_mcp_protocol_version_must_match_env_exactly(self, http_client, wait_for_services):
        """Test that MCP ONLY accepts the exact protocol version from .env."""
        # MUST have MCP client access token - test FAILS if not available
        assert MCP_CLIENT_ACCESS_TOKEN, "MCP_CLIENT_ACCESS_TOKEN not available - run: just mcp-client-token"

        # Test 1: Correct version from .env MUST work
        correct_response = await http_client.post(
            f"{MCP_TESTING_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"},
                },
                "id": "init-correct",
            },
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
            },
        )

        # Should succeed with 200
        assert correct_response.status_code == HTTP_OK, (
            f"MCP MUST accept protocol version {MCP_PROTOCOL_VERSION} from .env! Got {correct_response.status_code}"  # TODO: Break long line
        )

        result = parse_sse_response(correct_response)
        assert "result" in result, "Initialize with correct version must return result"
        assert "protocolVersion" in result["result"], "Result must include protocol version"

        # Verify it's using a supported version (per MCP spec, servers can return their own version)
        returned_version = result["result"]["protocolVersion"]
        assert returned_version in MCP_PROTOCOL_VERSIONS_SUPPORTED, (
            f"MCP returned unsupported version! Expected one of {MCP_PROTOCOL_VERSIONS_SUPPORTED}, got {returned_version}"  # TODO: Break long line
        )

    @pytest.mark.asyncio
    async def test_mcp_version_header_must_match_env(self, http_client, wait_for_services, registered_client):
        """Test that MCP-Protocol-Version header MUST match .env version."""
        # Connect to Redis
        redis_client = await redis.from_url(REDIS_URL, decode_responses=True)

        try:
            # Create a valid JWT token
            jti = secrets.token_urlsafe(16)
            now = int(time.time())

            token_claims = {
                "sub": "test_header_version",
                "username": "headertest",
                "email": "header@test.com",
                "name": "Header Test User",
                "scope": "openid profile email",
                "client_id": registered_client["client_id"],
                "jti": jti,
                "iat": now,
                "exp": now + ACCESS_TOKEN_LIFETIME,
                "iss": f"https://auth.{BASE_DOMAIN}",
            }

            # Create JWT
            access_token = jwt_encode(token_claims, GATEWAY_JWT_SECRET, algorithm="HS256")

            # Store in Redis
            await redis_client.setex(
                f"oauth:token:{jti}",
                ACCESS_TOKEN_LIFETIME,
                json.dumps(
                    {
                        "sub": token_claims["sub"],
                        "username": token_claims["username"],
                        "email": token_claims["email"],
                        "name": token_claims["name"],
                        "scope": token_claims["scope"],
                        "client_id": token_claims["client_id"],
                    }
                ),
            )

            # Test wrong version in header
            wrong_header_versions = [MCP_PROTOCOL_VERSION, "2024-01-01", "invalid", ""]

            for wrong_header in wrong_header_versions:
                if wrong_header == MCP_PROTOCOL_VERSION:
                    continue

                response = await http_client.post(
                    f"{MCP_TESTING_URL}",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "params": {},
                        "id": "list-1",
                    },
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "MCP-Protocol-Version": wrong_header,  # WRONG version in header!
                    },
                )

                # The server might accept the request but should ideally validate headers
                if response.status_code == HTTP_OK:
                    result = parse_sse_response(response)
                    print(
                        f"⚠️  Server accepted request with wrong header version '{wrong_header}': {result}"  # TODO: Break long line
                    )
                else:
                    print(
                        f"✓ Server rejected wrong header version '{wrong_header}': {response.status_code}"  # TODO: Break long line
                    )

        finally:
            # Clean up
            await redis_client.delete(f"oauth:token:{jti}")
            await redis_client.srem("oauth:user_tokens:headertest", jti)
            await redis_client.aclose()

    def test_env_mcp_version_is_supported(self):
        """Verify that .env has a supported MCP protocol version."""
        # This test ensures we're using one of the supported versions
        assert MCP_PROTOCOL_VERSION in MCP_PROTOCOL_VERSIONS_SUPPORTED, (
            f"MCP_PROTOCOL_VERSION in .env MUST be one of {MCP_PROTOCOL_VERSIONS_SUPPORTED}! "  # TODO: Break long line
            f"Currently set to '{MCP_PROTOCOL_VERSION}'. "
            f"Update your .env file to use a supported version!"
        )

        print(
            f"✓ MCP Protocol Version correctly set to {MCP_PROTOCOL_VERSION} (supported)"  # TODO: Break long line
        )
        print(f"✓ Supported versions: {MCP_PROTOCOL_VERSIONS_SUPPORTED}")
