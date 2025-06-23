"""Sacred Integration Tests for MCP Streamable HTTP Proxy
Following Commandment 1: NO MOCKING! Test against real deployed services only!
These tests verify the mcp-streamablehttp-proxy functionality using real MCP services.
"""
import os

import httpx
import pytest

from .test_constants import GATEWAY_OAUTH_ACCESS_TOKEN
from .test_constants import MCP_FETCH_URL
from .test_constants import MCP_PROTOCOL_VERSION


# MCP Client tokens for external client testing
MCP_CLIENT_ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN")
MCP_CLIENT_ID = os.getenv("MCP_CLIENT_ID")


class TestMCPProxyBasicFunctionality:
    """Test basic MCP proxy functionality against real services."""

    @pytest.mark.asyncio
    async def test_health_endpoint_accessible(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that the MCP service is accessible (health is checked via MCP protocol)."""
        # According to CLAUDE.md, health checks use MCP protocol, not /health endpoint
        # We test accessibility by checking if auth is required
        response = await http_client.get(f"{MCP_FETCH_URL}")
        assert response.status_code == 401  # Should require auth
        assert "WWW-Authenticate" in response.headers

    @pytest.mark.asyncio
    async def test_mcp_endpoint_requires_auth(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that the MCP endpoint requires authentication."""
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1}
        )
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"].startswith("Bearer")

    @pytest.mark.asyncio
    async def test_invalid_json_rpc_request(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that invalid JSON-RPC requests are properly rejected."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")

        # Send invalid JSON-RPC (missing required fields)
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"invalid": "request"},
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )
        # JSON-RPC errors return 200 with error in response body
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        # The proxy returns -32002 for missing session ID on non-initialize requests
        assert data["error"]["code"] == -32002


class TestMCPProxyAuthentication:
    """Test MCP proxy authentication using real OAuth tokens."""

    @pytest.mark.asyncio
    async def test_gateway_token_authentication(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test authentication using gateway OAuth token."""
        if not GATEWAY_OAUTH_ACCESS_TOKEN:
            pytest.fail("No GATEWAY_OAUTH_ACCESS_TOKEN available - run: just generate-github-token - TESTS MUST NOT BE SKIPPED!")

        # Gateway token should work for authentication
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {GATEWAY_OAUTH_ACCESS_TOKEN}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        # Server may negotiate a different protocol version
        assert "protocolVersion" in data["result"]

    @pytest.mark.asyncio
    async def test_mcp_client_token_authentication(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test authentication using MCP client token."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")

        # MCP client token should work for authentication
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-streamablehttp-client",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        # Server may negotiate a different protocol version
        assert "protocolVersion" in data["result"]

    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that invalid tokens are rejected."""
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1},
            headers={"Authorization": "Bearer invalid-token-12345"}
        )
        assert response.status_code == 401


class TestMCPProtocolInitialization:
    """Test MCP protocol initialization flow with real services."""

    @pytest.mark.asyncio
    async def test_initialize_request(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test the initialize request following MCP 2025-06-18 spec."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")

        # Send initialize request
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure per MCP spec
        assert "jsonrpc" in data
        assert data["jsonrpc"] == "2.0"
        assert "id" in data
        assert data["id"] == 1
        assert "result" in data

        result = data["result"]
        assert "protocolVersion" in result
        # Server may negotiate a different protocol version
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        assert "name" in result["serverInfo"]
        assert "version" in result["serverInfo"]

    @pytest.mark.asyncio
    async def test_initialized_notification(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test sending initialized notification after initialize."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")

        # First initialize
        init_response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )
        assert init_response.status_code == 200

        # Send initialized notification (no id field for notifications)
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialized",
                "params": {}
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )
        # Notifications don't get responses in JSON-RPC
        assert response.status_code in [200, 202]


class TestMCPFetchCapabilities:
    """Test MCP fetch server specific capabilities."""

    @pytest.mark.asyncio
    async def test_fetch_capability_available(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that mcp-server-fetch reports fetch capability."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")

        # Initialize to get capabilities
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )

        assert response.status_code == 200
        data = response.json()
        capabilities = data["result"]["capabilities"]

        # mcp-server-fetch should provide tools capability
        assert "tools" in capabilities

    @pytest.mark.asyncio
    async def test_list_tools(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test listing available tools from mcp-server-fetch."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")

        # Initialize first
        init_response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )
        assert init_response.status_code == 200
        session_id = init_response.headers.get("Mcp-Session-Id")
        assert session_id

        # Send initialized with session ID
        await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "initialized", "params": {}},
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Mcp-Session-Id": session_id
            }
        )

        # List tools with session ID
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Mcp-Session-Id": session_id
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "tools" in data["result"]

        # mcp-server-fetch should have fetch tool
        tools = data["result"]["tools"]
        assert len(tools) > 0
        fetch_tool = next((t for t in tools if t["name"] == "fetch"), None)
        assert fetch_tool is not None
        assert "description" in fetch_tool
        assert "inputSchema" in fetch_tool


class TestMCPProxyErrorHandling:
    """Test error handling in the MCP proxy."""

    @pytest.mark.asyncio
    async def test_method_not_found(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that unknown methods return proper JSON-RPC error."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")

        # Initialize first to get session ID
        init_response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "error-test", "version": "1.0.0"}
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )
        assert init_response.status_code == 200
        session_id = init_response.headers.get("Mcp-Session-Id")

        # Now test non-existent method with session ID
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "nonexistent/method",
                "params": {},
                "id": 2
            },
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Mcp-Session-Id": session_id
            }
        )

        assert response.status_code == 200  # JSON-RPC errors still return 200
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        # Different MCP servers may return different error codes for unknown methods
        # -32601 = Method not found, -32602 = Invalid params
        assert data["error"]["code"] in [-32601, -32602]

    @pytest.mark.asyncio
    async def test_invalid_params(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that invalid parameters return proper error."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")

        # Try to initialize with wrong protocol version
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "1999-01-01",  # Invalid version
                    "clientInfo": {"name": "test", "version": "1.0"}
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "error" in data or data["result"]["protocolVersion"] != "1999-01-01"


class TestMCPProxyHeaders:
    """Test MCP proxy header handling."""

    @pytest.mark.asyncio
    async def test_mcp_protocol_version_header(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that MCP-Protocol-Version header is handled."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")

        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1},
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
            }
        )
        # Should accept the header
        assert response.status_code in [200, 400]  # 400 if ping not supported

    @pytest.mark.asyncio
    async def test_cors_headers_on_options(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test CORS headers on OPTIONS request."""
        response = await http_client.options(
            f"{MCP_FETCH_URL}",
            headers={"Origin": "https://claude.ai"}
        )
        assert response.status_code == 200
        # Check that some CORS headers are present
        assert "Access-Control-Allow-Origin" in response.headers or "access-control-allow-origin" in response.headers
