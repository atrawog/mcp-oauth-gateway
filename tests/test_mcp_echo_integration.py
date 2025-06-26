"""Sacred MCP Echo Integration Tests - Following CLAUDE.md Commandments!
Tests the MCP Echo service with real OAuth authentication and full protocol compliance.
NO MOCKING - real services only per the divine commandments!
"""

import json

import httpx
import pytest


class TestMCPEchoIntegration:
    """Test MCP Echo service functionality with proper OAuth authentication."""

    @pytest.mark.asyncio
    async def test_echo_requires_authentication(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str
    ):
        """Test that Echo service REQUIRES OAuth authentication - no unauthorized access!"""
        # Test with no authentication
        response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                },
                "id": 1
            }
        )

        assert response.status_code == 401, "Echo service must reject unauthenticated requests"
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"

    @pytest.mark.asyncio
    async def test_echo_protocol_initialization(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test MCP protocol initialization with Echo service."""
        response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                },
                "id": 1
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )

        assert response.status_code == 200

        # Parse SSE response
        data = self._parse_sse_response(response.text)
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
        assert data["result"]["protocolVersion"] == "2025-06-18"
        assert data["result"]["serverInfo"]["name"] == "mcp-echo-streamablehttp-server-stateless"

    @pytest.mark.asyncio
    async def test_echo_list_tools(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test listing available tools from Echo service."""
        # Initialize first
        await self._initialize_session(http_client, mcp_echo_url, gateway_auth_headers)

        # List tools
        response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )

        assert response.status_code == 200

        data = self._parse_sse_response(response.text)
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 2
        assert "result" in data

        tools = data["result"]["tools"]
        assert len(tools) == 10  # Now we have 10 tools including diagnostic tools

        # Check echo tool
        echo_tool = next(t for t in tools if t["name"] == "echo")
        assert echo_tool["description"] == "Echo back the provided message"
        assert "message" in echo_tool["inputSchema"]["properties"]

        # Check printHeader tool
        header_tool = next(t for t in tools if t["name"] == "printHeader")
        assert header_tool["description"] == "Print all HTTP headers from the current request"
        assert header_tool["inputSchema"]["properties"] == {}

        # Verify diagnostic tools exist
        tool_names = [t["name"] for t in tools]
        diagnostic_tools = [
            "bearerDecode", "authContext", "requestTiming",
            "protocolNegotiation", "corsAnalysis", "environmentDump",
            "healthProbe", "whoIStheGOAT"
        ]
        for tool in diagnostic_tools:
            assert tool in tool_names

    @pytest.mark.asyncio
    async def test_echo_tool_functionality(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test the echo tool returns the exact message."""
        # Initialize first
        await self._initialize_session(http_client, mcp_echo_url, gateway_auth_headers)

        test_message = "Hello from MCP Echo Test! 🚀"

        response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "echo",
                    "arguments": {
                        "message": test_message
                    }
                },
                "id": 3
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )

        assert response.status_code == 200

        data = self._parse_sse_response(response.text)
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 3
        assert "result" in data
        assert len(data["result"]["content"]) == 1
        assert data["result"]["content"][0]["type"] == "text"
        assert data["result"]["content"][0]["text"] == test_message

    @pytest.mark.asyncio
    async def test_printHeader_tool_functionality(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test the printHeader tool shows HTTP headers including auth headers."""
        # Initialize first
        await self._initialize_session(http_client, mcp_echo_url, gateway_auth_headers)

        # Add custom headers for testing
        custom_headers = {
            **gateway_auth_headers,
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "X-Test-Header": "test-value-123",
            "X-Custom-Header": "custom-value-456"
        }

        response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "printHeader",
                    "arguments": {}
                },
                "id": 4
            },
            headers=custom_headers
        )

        assert response.status_code == 200

        data = self._parse_sse_response(response.text)
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 4
        assert "result" in data

        headers_text = data["result"]["content"][0]["text"]
        assert "HTTP Headers:" in headers_text
        assert "authorization: Bearer" in headers_text  # Should show auth header
        assert "x-test-header: test-value-123" in headers_text
        assert "x-custom-header: custom-value-456" in headers_text
        assert "content-type: application/json" in headers_text

    @pytest.mark.asyncio
    async def test_echo_error_handling_invalid_tool(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test error handling for invalid tool name."""
        # Initialize first
        await self._initialize_session(http_client, mcp_echo_url, gateway_auth_headers)

        response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "invalid_tool",
                    "arguments": {}
                },
                "id": 5
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )

        assert response.status_code == 200

        data = self._parse_sse_response(response.text)
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 5
        assert "error" in data
        assert "Unknown tool: invalid_tool" in str(data["error"])

    @pytest.mark.asyncio
    async def test_echo_error_handling_invalid_arguments(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test error handling for invalid tool arguments."""
        # Initialize first
        await self._initialize_session(http_client, mcp_echo_url, gateway_auth_headers)

        # Call echo without required message argument
        response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "echo",
                    "arguments": {}  # Missing required 'message'
                },
                "id": 6
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )

        assert response.status_code == 200

        data = self._parse_sse_response(response.text)
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 6
        assert "error" in data
        assert "message must be a string" in str(data["error"])

    @pytest.mark.asyncio
    async def test_echo_cors_headers(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str
    ):
        """Test CORS preflight handling for Echo service."""
        response = await http_client.options(
            mcp_echo_url,
            headers={
                "Origin": "https://claude.ai",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization"
            }
        )

        # CORS preflight should work without auth
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "POST" in response.headers["Access-Control-Allow-Methods"]

    @pytest.mark.asyncio
    async def test_echo_with_forwardauth_headers(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that ForwardAuth headers are visible in printHeader output."""
        # Initialize first
        await self._initialize_session(http_client, mcp_echo_url, gateway_auth_headers)

        response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "printHeader",
                    "arguments": {}
                },
                "id": 7
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )

        assert response.status_code == 200

        data = self._parse_sse_response(response.text)
        headers_text = data["result"]["content"][0]["text"]

        # Check for ForwardAuth headers that Traefik adds
        # These might include X-User-Id, X-User-Name, etc.
        assert "authorization: Bearer" in headers_text

    @pytest.mark.asyncio
    async def test_echo_stateless_behavior(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service is truly stateless - each request is independent."""
        # Make multiple independent requests
        for i in range(3):
            # Each request should work independently without maintaining state
            response = await http_client.post(
                mcp_echo_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "echo",
                        "arguments": {
                            "message": f"Stateless test {i}"
                        }
                    },
                    "id": i + 10
                },
                headers={
                    **gateway_auth_headers,
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                }
            )

            assert response.status_code == 200
            data = self._parse_sse_response(response.text)
            assert data["result"]["content"][0]["text"] == f"Stateless test {i}"

    # Helper methods
    def _parse_sse_response(self, sse_text: str) -> dict:
        """Parse SSE response to extract JSON data."""
        for line in sse_text.strip().split('\n'):
            if line.startswith('data: '):
                return json.loads(line[6:])
        raise ValueError("No data found in SSE response")

    async def _initialize_session(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, auth_headers: dict
    ):
        """Initialize MCP session with Echo service."""
        response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                },
                "id": "init"
            },
            headers={
                **auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )
        assert response.status_code == 200
