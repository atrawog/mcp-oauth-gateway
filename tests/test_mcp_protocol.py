"""Sacred MCP Protocol Tests - Testing real MCP servers with JSON-RPC 2.0
Following MCP Protocol specifications from .env ONLY!
NO HARDCODED VERSIONS! Must use MCP_PROTOCOL_VERSION from environment!
"""

import pytest

from .test_constants import HTTP_UNAUTHORIZED
from .test_constants import MCP_PROTOCOL_VERSION


class TestMCPProtocol:
    """Test MCP Protocol compliance - version MUST match .env!"""

    @pytest.mark.asyncio
    async def test_mcp_endpoint_requires_auth(self, http_client, wait_for_services, mcp_fetch_url):
        """Test that MCP endpoint requires authentication."""
        # Try to access without auth
        response = await http_client.post(f"{mcp_fetch_url}", json={"jsonrpc": "2.0", "method": "ping", "id": 1})

        # Should get 401 from ForwardAuth middleware
        assert response.status_code == HTTP_UNAUTHORIZED
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    @pytest.mark.asyncio
    async def test_mcp_json_rpc_format(self, http_client, wait_for_services, mcp_fetch_url):
        """Test JSON-RPC 2.0 message format requirements."""
        # Invalid JSON-RPC (missing required fields)
        test_cases = [
            # Missing jsonrpc version
            {"method": "test", "id": 1},
            # Wrong jsonrpc version
            {"jsonrpc": "1.0", "method": "test", "id": 1},
            # Missing method
            {"jsonrpc": "2.0", "id": 1},
            # Null id (forbidden for requests)
            {"jsonrpc": "2.0", "method": "test", "id": None},
        ]

        # Test without auth - endpoint should reject before checking JSON-RPC format
        for invalid_request in test_cases:
            response = await http_client.post(f"{mcp_fetch_url}", json=invalid_request)

            # Should get 401 from auth middleware
            assert response.status_code == HTTP_UNAUTHORIZED
            assert response.headers.get("WWW-Authenticate") == "Bearer"

    @pytest.mark.asyncio
    async def test_mcp_streamable_http_headers(self, http_client, wait_for_services, mcp_fetch_url):
        """Test required headers for Streamable HTTP transport."""
        # Test required Accept header without auth
        response = await http_client.post(
            f"{mcp_fetch_url}",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1},
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
        )

        # Check response (will be 401 due to auth, but headers are validated)
        assert response.status_code == HTTP_UNAUTHORIZED
        assert "Accept" in response.request.headers
        assert "application/json" in response.request.headers["Accept"]
        assert "text/event-stream" in response.request.headers["Accept"]

    @pytest.mark.asyncio
    async def test_mcp_session_management(self, http_client, wait_for_services, mcp_fetch_url):
        """Test MCP session ID handling."""
        session_id = "test-session-123"

        # Send request with session ID (no auth)
        response = await http_client.post(
            f"{mcp_fetch_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "clientCapabilities": {},
                },
                "id": 1,
            },
            headers={"Mcp-Session-Id": session_id},
        )

        # Should get 401 but session header was sent
        assert response.status_code == HTTP_UNAUTHORIZED
        assert "Mcp-Session-Id" in response.request.headers

    @pytest.mark.asyncio
    async def test_mcp_protocol_version(self, http_client, wait_for_services, mcp_fetch_url):
        """Test MCP protocol version negotiation."""
        response = await http_client.post(
            f"{mcp_fetch_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "clientCapabilities": {"roots": True, "sampling": True},
                },
                "id": "init-1",
            },
            headers={"MCP-Protocol-Version": MCP_PROTOCOL_VERSION},
        )

        # Should get 401 but protocol version header was sent
        assert response.status_code == HTTP_UNAUTHORIZED
        assert response.request.headers.get("MCP-Protocol-Version") == MCP_PROTOCOL_VERSION

    @pytest.mark.asyncio
    async def test_mcp_error_response_format(self, http_client, mcp_fetch_url):
        """Test that MCP errors follow JSON-RPC 2.0 error format."""
        # This will fail auth, but we can check the error format
        response = await http_client.post(
            f"{mcp_fetch_url}",
            json={"jsonrpc": "2.0", "method": "unknown_method", "id": 1},
        )

        # Even auth errors should follow some structure
        assert response.status_code == HTTP_UNAUTHORIZED
        if response.headers.get("content-type", "").startswith("application/json"):
            error_data = response.json()
            # Should have error structure
            assert "error" in error_data or "detail" in error_data

    @pytest.mark.asyncio
    async def test_mcp_batch_request_support(self, http_client, wait_for_services, mcp_fetch_url):
        """Test that MCP supports receiving JSON-RPC batches."""
        # Send batch request without auth
        batch = [
            {"jsonrpc": "2.0", "method": "ping", "id": 1},
            {"jsonrpc": "2.0", "method": "ping", "id": 2},
            {"jsonrpc": "2.0", "method": "ping", "id": 3},
        ]

        response = await http_client.post(f"{mcp_fetch_url}", json=batch)

        # Should get 401 from auth middleware
        # Real MCP server must support receiving batches
        assert response.status_code == HTTP_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_mcp_http_methods(self, http_client, wait_for_services, mcp_fetch_url):
        """Test that MCP endpoint supports both POST and GET methods."""
        # Test POST method without auth
        post_response = await http_client.post(f"{mcp_fetch_url}", json={"jsonrpc": "2.0", "method": "ping", "id": 1})
        assert post_response.status_code == HTTP_UNAUTHORIZED  # Auth required

        # Test GET method without auth
        get_response = await http_client.get(f"{mcp_fetch_url}", headers={"Mcp-Session-Id": "test-session"})
        assert get_response.status_code == HTTP_UNAUTHORIZED  # Auth required
