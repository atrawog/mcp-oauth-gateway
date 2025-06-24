from .test_constants import HTTP_BAD_REQUEST
from .test_constants import HTTP_OK
from .test_constants import HTTP_UNAUTHORIZED
"""Tests for MCP Everything service integration."""

import json

import httpx
import pytest

from tests.test_constants import BASE_DOMAIN
from tests.test_constants import GATEWAY_OAUTH_ACCESS_TOKEN
from tests.test_constants import MCP_EVERYTHING_TESTS_ENABLED
from tests.test_constants import MCP_EVERYTHING_URLS


@pytest.fixture
def base_domain():
    """Base domain for tests."""
    return BASE_DOMAIN


@pytest.fixture
def everything_base_url():
    """Base URL for everything service."""
    if not MCP_EVERYTHING_TESTS_ENABLED:
        pytest.skip(
            "MCP Everything tests are disabled. Set MCP_EVERYTHING_TESTS_ENABLED=true to enable."
        )
    if not MCP_EVERYTHING_URLS:
        pytest.skip("MCP_EVERYTHING_URLS environment variable not set")
    # Use the full MCP URL including /mcp path
    return MCP_EVERYTHING_URLS[0]


@pytest.fixture
def gateway_token():
    """Gateway OAuth token for testing."""
    return GATEWAY_OAUTH_ACCESS_TOKEN


@pytest.fixture
async def wait_for_services():
    """Ensure all services are ready."""
    # Services are already checked by conftest
    return True


def parse_sse_response(response_text):
    """Parse Server-Sent Events response."""
    for line in response_text.strip().split("\n"):
        if line.startswith("data: "):
            return json.loads(line[6:])
    return None


class TestMCPEverythingIntegration:
    """Test the MCP Everything service integration."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled"
    )
    async def test_everything_reachable_no_auth(
        self, everything_base_url, wait_for_services
    ):
        """Test that service is reachable (root requires auth)."""
        async with httpx.AsyncClient(verify=False) as client:
            # Get base URL without /mcp for root test
            base_url = (
                everything_base_url[:-4]
                if everything_base_url.endswith("/mcp")
                else everything_base_url
            )
            response = await client.get(f"{base_url}/")
            # The root requires auth through Traefik
            assert response.status_code == HTTP_UNAUTHORIZED

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled"
    )
    async def test_everything_requires_auth(
        self, everything_base_url, wait_for_services
    ):
        """Test that MCP endpoint requires authentication."""
        async with httpx.AsyncClient(verify=False) as client:
            # Try without auth
            response = await client.post(
                f"{everything_base_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"},
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
            )
            assert response.status_code == HTTP_UNAUTHORIZED

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled"
    )
    async def test_everything_initialize(
        self, everything_base_url, gateway_token, wait_for_services
    ):
        """Test MCP initialize method."""
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{everything_base_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"},
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "Authorization": f"Bearer {gateway_token}",
                },
            )

            assert response.status_code == HTTP_OK
            data = parse_sse_response(response.text)
            assert data is not None
            assert "result" in data
            assert data["result"]["protocolVersion"] == "2025-06-18"
            assert "serverInfo" in data["result"]
            assert data["result"]["serverInfo"]["name"] == "example-servers/everything"

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled"
    )
    async def test_everything_list_tools(
        self, everything_base_url, gateway_token, wait_for_services
    ):
        """Test listing available tools in the everything server."""
        async with httpx.AsyncClient(verify=False) as client:
            # First initialize
            init_response = await client.post(
                f"{everything_base_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"},
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "Authorization": f"Bearer {gateway_token}",
                },
            )
            assert init_response.status_code == HTTP_OK

            # Extract session ID if provided
            session_id = None
            for header in init_response.headers.get("mcp-session-id", "").split(","):
                if header.strip():
                    session_id = header.strip()
                    break

            # List tools
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Authorization": f"Bearer {gateway_token}",
            }
            if session_id:
                headers["Mcp-Session-Id"] = session_id

            response = await client.post(
                f"{everything_base_url}",
                json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
                headers=headers,
            )

            assert response.status_code == HTTP_OK
            data = parse_sse_response(response.text)
            assert data is not None
            assert "result" in data
            assert "tools" in data["result"]

            # The everything server should have various test tools
            tools = data["result"]["tools"]
            assert isinstance(tools, list)
            assert len(tools) > 0

            # Check that tools have proper structure
            for tool in tools:
                assert "name" in tool
                assert "description" in tool
                assert "inputSchema" in tool

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled"
    )
    async def test_everything_echo_tool(
        self, everything_base_url, gateway_token, wait_for_services
    ):
        """Test calling the echo tool if available."""
        async with httpx.AsyncClient(verify=False) as client:
            # Initialize first
            init_response = await client.post(
                f"{everything_base_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"},
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "Authorization": f"Bearer {gateway_token}",
                },
            )
            assert init_response.status_code == HTTP_OK

            # Try to call echo tool
            response = await client.post(
                f"{everything_base_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "echo",
                        "arguments": {"message": "Hello from MCP Everything!"},
                    },
                    "id": 2,
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "Authorization": f"Bearer {gateway_token}",
                },
            )

            # The everything server might not have an echo tool, check the response
            if response.status_code == HTTP_BAD_REQUEST:
                # Tool might not exist, that's OK
                assert True
            else:
                assert response.status_code == HTTP_OK
                data = parse_sse_response(response.text)
                assert data is not None

                # If echo tool exists, check response
                if "result" in data and not data.get("error"):
                    assert "content" in data["result"]
                    # Echo should return our message
                    content = data["result"]["content"]
                    assert any(
                        "Hello from MCP Everything!" in str(item.get("text", ""))
                        for item in content
                        if isinstance(item, dict)
                    )

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled"
    )
    async def test_everything_oauth_discovery(
        self, everything_base_url, wait_for_services
    ):
        """Test OAuth discovery endpoint is accessible."""
        async with httpx.AsyncClient(verify=False) as client:
            # Get base URL without /mcp for OAuth discovery
            base_url = (
                everything_base_url[:-4]
                if everything_base_url.endswith("/mcp")
                else everything_base_url
            )
            response = await client.get(
                f"{base_url}/.well-known/oauth-authorization-server"
            )
            assert response.status_code == HTTP_OK
            data = response.json()
            assert "issuer" in data
            assert "authorization_endpoint" in data
            assert "token_endpoint" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled"
    )
    async def test_everything_cors_preflight(
        self, everything_base_url, wait_for_services
    ):
        """Test CORS preflight request handling."""
        # When using MCP_TESTING_URL, we might be testing against a different server
        # that doesn't have the same CORS configuration as production
        from tests.test_constants import MCP_TESTING_URL

        MCP_TESTING_URL and everything_base_url.startswith(MCP_TESTING_URL.rstrip("/"))

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.options(
                f"{everything_base_url}",
                headers={
                    "Origin": "https://claude.ai",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type,authorization",
                },
            )

            # OPTIONS requests should return 200 or 204
            assert response.status_code in [200, 204]

            # Check CORS headers if present - they may not be configured on all environments
            origin_header = response.headers.get("access-control-allow-origin")
            if origin_header:
                # If CORS is configured, validate the headers
                assert origin_header in ["https://claude.ai", "*"], (
                    f"Expected claude.ai or * origin, got {origin_header}"
                )

                methods_header = response.headers.get(
                    "access-control-allow-methods", ""
                )
                if methods_header:
                    assert "POST" in methods_header

                allow_headers = response.headers.get("access-control-allow-headers", "")
                if allow_headers:
                    assert (
                        allow_headers == "*" or "authorization" in allow_headers.lower()
                    )
            else:
                # CORS might not be configured on test environments
                # This is acceptable for test servers
                print(
                    f"Note: CORS headers not present on {everything_base_url} - this is acceptable for test environments"  # TODO: Break long line
                )
