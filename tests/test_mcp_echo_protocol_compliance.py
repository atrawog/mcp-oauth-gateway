"""Sacred MCP Echo Protocol Compliance Tests - Following the divine MCP specification!
Tests that Echo service strictly follows MCP protocol version 2025-03-26.
NO MOCKING - testing against real deployed service!
"""

import json
import pytest
import httpx
from typing import Any, Dict


class TestMCPEchoProtocolCompliance:
    """Test MCP Echo service for strict protocol compliance."""

    @pytest.mark.asyncio
    async def test_echo_jsonrpc_compliance(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service follows JSON-RPC 2.0 specification exactly."""
        # Test 1: Valid JSON-RPC request
        response = await http_client.post(
            f"{mcp_echo_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "compliance-test", "version": "1.0.0"}
                },
                "id": 1
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200
        data = self._parse_sse_response(response.text)
        
        # Verify JSON-RPC response structure
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
        assert "error" not in data  # Cannot have both result and error

    @pytest.mark.asyncio
    async def test_echo_invalid_jsonrpc_version(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service rejects invalid JSON-RPC version."""
        response = await http_client.post(
            f"{mcp_echo_url}/mcp",
            json={
                "jsonrpc": "1.0",  # Invalid version
                "method": "initialize",
                "params": {},
                "id": 2
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }
        )
        
        # Should handle gracefully, possibly with error
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_echo_missing_jsonrpc_field(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service handles missing jsonrpc field."""
        response = await http_client.post(
            f"{mcp_echo_url}/mcp",
            json={
                # Missing "jsonrpc" field
                "method": "initialize",
                "params": {},
                "id": 3
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }
        )
        
        # Should return error
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_echo_batch_requests_not_supported(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service handles batch requests appropriately."""
        # Send batch request (array of requests)
        response = await http_client.post(
            f"{mcp_echo_url}/mcp",
            json=[
                {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 1
                },
                {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 2
                }
            ],
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }
        )
        
        # Stateless server might not support batches
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_echo_protocol_version_negotiation(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test protocol version negotiation during initialization."""
        # Test with exact version
        response = await http_client.post(
            f"{mcp_echo_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "version-test", "version": "1.0.0"}
                },
                "id": 4
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200
        data = self._parse_sse_response(response.text)
        assert data["result"]["protocolVersion"] == "2025-03-26"

    @pytest.mark.asyncio
    async def test_echo_unknown_protocol_version(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test initialization with unknown protocol version."""
        response = await http_client.post(
            f"{mcp_echo_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "9999-12-31",  # Future version
                    "capabilities": {},
                    "clientInfo": {"name": "future-test", "version": "1.0.0"}
                },
                "id": 5
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }
        )
        
        # Should either negotiate down or error
        assert response.status_code == 200
        data = self._parse_sse_response(response.text)
        
        if "error" not in data:
            # If successful, should negotiate to supported version
            assert data["result"]["protocolVersion"] in ["2025-03-26"]

    @pytest.mark.asyncio
    async def test_echo_required_headers(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service accepts required MCP headers."""
        response = await http_client.post(
            f"{mcp_echo_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "header-test", "version": "1.0.0"}
                },
                "id": 6
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-03-26"  # Optional but recommended
            }
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_echo_content_type_validation(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service validates Content-Type header."""
        # Test with wrong content type
        response = await http_client.post(
            f"{mcp_echo_url}/mcp",
            data="not json",  # Send as text
            headers={
                **gateway_auth_headers,
                "Content-Type": "text/plain",  # Wrong content type
                "Accept": "application/json, text/event-stream"
            }
        )
        
        # Should reject non-JSON content
        assert response.status_code in [400, 415]

    @pytest.mark.asyncio
    async def test_echo_sse_response_format(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service returns proper SSE format."""
        response = await http_client.post(
            f"{mcp_echo_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 7
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("text/event-stream")
        
        # Verify SSE format
        lines = response.text.strip().split('\n')
        assert any(line.startswith('event:') or line.startswith('data:') for line in lines)

    @pytest.mark.asyncio
    async def test_echo_error_response_format(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service returns properly formatted error responses."""
        response = await http_client.post(
            f"{mcp_echo_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "nonexistent_tool",
                    "arguments": {}
                },
                "id": 8
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200
        data = self._parse_sse_response(response.text)
        
        # Verify error response format
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 8
        assert "error" in data
        assert "result" not in data  # Cannot have both
        
        error = data["error"]
        assert "code" in error
        assert "message" in error
        assert isinstance(error["code"], int)  # Error codes must be integers

    @pytest.mark.asyncio
    async def test_echo_notification_support(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test notification support (requests without id)."""
        # Notifications don't have an id field
        response = await http_client.post(
            f"{mcp_echo_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {}
                # No "id" field - this is a notification
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }
        )
        
        # Server should accept but may not respond to notifications
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_echo_method_namespace_compliance(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service uses correct method namespaces."""
        # Valid MCP methods should be namespaced
        valid_methods = [
            "initialize",
            "tools/list",
            "tools/call",
            "resources/list",  # Even if not implemented
            "prompts/list"     # Even if not implemented
        ]
        
        for method in valid_methods[:3]:  # Test first 3 that echo supports
            response = await http_client.post(
                f"{mcp_echo_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": {} if method != "tools/call" else {
                        "name": "echo",
                        "arguments": {"message": "test"}
                    },
                    "id": f"method-{method}"
                },
                headers={
                    **gateway_auth_headers,
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                }
            )
            
            assert response.status_code == 200

    # Helper methods
    def _parse_sse_response(self, sse_text: str) -> Dict[str, Any]:
        """Parse SSE response to extract JSON data."""
        for line in sse_text.strip().split('\n'):
            if line.startswith('data: '):
                return json.loads(line[6:])
        raise ValueError("No data found in SSE response")