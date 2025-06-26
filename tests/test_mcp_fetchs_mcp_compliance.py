from .test_constants import HTTP_BAD_REQUEST
from .test_constants import HTTP_OK
from .test_fetch_speedup_utils import get_local_test_url


"""Strict MCP 2025-06-18 protocol compliance tests for mcp-fetchs."""

import httpx
import pytest

from tests.test_constants import BASE_DOMAIN
from tests.test_constants import GATEWAY_OAUTH_ACCESS_TOKEN


@pytest.fixture
def base_domain():
    """Base domain for tests."""
    return BASE_DOMAIN


@pytest.fixture
def valid_token():
    """Valid OAuth token for testing."""
    return GATEWAY_OAUTH_ACCESS_TOKEN


class TestMCPFetchsCompliance:
    """Strict MCP 2025-06-18 compliance tests."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_initialize_protocol_negotiation(
        self, mcp_fetchs_url, valid_token, _wait_for_services, unique_test_id
    ):
        """Test protocol version negotiation per MCP 2025-06-18."""
        # Test supported version
        async with httpx.AsyncClient(verify=True) as client:
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": f"test-{unique_test_id}", "version": "1.0.0"},
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                    "MCP-Protocol-Version": "2025-06-18",
                },
            )

            assert response.status_code == HTTP_OK
            data = response.json()
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 1
            assert "result" in data
            result = data["result"]

            # Check required fields
            assert result["protocolVersion"] == "2025-06-18"
            assert "capabilities" in result
            assert "serverInfo" in result
            assert "name" in result["serverInfo"]
            assert "version" in result["serverInfo"]

            # Check capabilities structure
            assert "tools" in result["capabilities"]
            assert isinstance(result["capabilities"]["tools"], dict)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_unsupported_protocol_version(self, mcp_fetchs_url, valid_token, _wait_for_services, unique_test_id):
        """Test rejection of unsupported protocol versions."""
        async with httpx.AsyncClient(verify=True) as client:
            # Test unsupported version in params
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",  # Old version
                        "capabilities": {},
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                },
            )

            assert response.status_code == HTTP_OK  # JSON-RPC errors return 200
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == -32602  # Invalid params
            assert "Unsupported protocol version" in data["error"]["data"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_protocol_version_header(self, mcp_fetchs_url, valid_token, _wait_for_services, unique_test_id):
        """Test MCP-Protocol-Version header handling."""
        async with httpx.AsyncClient(verify=True) as client:
            # Test mismatched header version
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                    "MCP-Protocol-Version": "2024-11-05",  # Old version
                },
            )

            assert response.status_code == HTTP_BAD_REQUEST
            data = response.json()
            assert "2025-06-18" in data["message"]
            assert "2024-11-05" in data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tools_list_pagination(self, mcp_fetchs_url, valid_token, _wait_for_services, unique_test_id):
        """Test tools/list pagination support per MCP 2025-06-18."""
        async with httpx.AsyncClient(verify=True) as client:
            # Test without cursor
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                },
            )

            assert response.status_code == HTTP_OK
            data = response.json()
            assert "result" in data
            assert "tools" in data["result"]
            assert isinstance(data["result"]["tools"], list)

            # Test with cursor (should work even if no pagination)
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {"cursor": "test-cursor"},
                    "id": 2,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                },
            )

            assert response.status_code == HTTP_OK

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_definition_schema(self, mcp_fetchs_url, valid_token, _wait_for_services, unique_test_id):
        """Test tool definitions match MCP 2025-06-18 schema."""
        async with httpx.AsyncClient(verify=True) as client:
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                },
            )

            assert response.status_code == HTTP_OK
            data = response.json()
            tools = data["result"]["tools"]

            # Check each tool has required fields
            for tool in tools:
                assert "name" in tool, "Tool must have name"
                assert "inputSchema" in tool, "Tool must have inputSchema"

                # Check inputSchema is valid JSON Schema
                schema = tool["inputSchema"]
                assert "type" in schema
                assert schema["type"] == "object"

                # Optional fields
                if "description" in tool:
                    assert isinstance(tool["description"], str)
                if "title" in tool and tool["title"] is not None:
                    assert isinstance(tool["title"], str)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tools_call_validation(self, mcp_fetchs_url, valid_token, _wait_for_services, unique_test_id):
        """Test tools/call parameter validation per MCP 2025-06-18."""
        async with httpx.AsyncClient(verify=True) as client:
            # Test missing params
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={"jsonrpc": "2.0", "method": "tools/call", "id": 1},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                },
            )

            assert response.status_code == HTTP_OK
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == -32602  # Invalid params

            # Test missing name
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"arguments": {}},
                    "id": 2,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                },
            )

            assert response.status_code == HTTP_OK
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == -32602
            assert "name" in data["error"]["data"]

            # Test unknown tool
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": "nonexistent-tool", "arguments": {}},
                    "id": 3,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                },
            )

            assert response.status_code == HTTP_OK
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == -32602

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_execution_response_format(
        self, mcp_fetchs_url, valid_token, _wait_for_services, unique_test_id
    ):
        """Test tool execution response format per MCP 2025-06-18."""
        async with httpx.AsyncClient(verify=True) as client:
            # Successful tool call
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {"url": get_local_test_url()},
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                },
            )

            assert response.status_code == HTTP_OK
            data = response.json()
            assert "result" in data
            result = data["result"]

            # Check response structure
            assert "content" in result
            assert isinstance(result["content"], list)
            assert "isError" in result
            assert result["isError"] is False

            # Check content format
            for content in result["content"]:
                assert "type" in content
                assert content["type"] in ["text", "image", "audio", "resource"]
                if content["type"] == "text":
                    assert "text" in content
                elif content["type"] == "image":
                    assert "data" in content
                    assert "mimeType" in content

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_execution_error_format(self, mcp_fetchs_url, valid_token, _wait_for_services, unique_test_id):
        """Test tool execution error format per MCP 2025-06-18."""
        async with httpx.AsyncClient(verify=True) as client:
            # Tool execution error (invalid URL)
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {
                            "url": "ftp://invalid-scheme.com"  # Unsupported scheme
                        },
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                },
            )

            assert response.status_code == HTTP_OK
            data = response.json()
            assert "result" in data
            result = data["result"]

            # Check error response structure
            assert "content" in result
            assert "isError" in result
            assert result["isError"] is True

            # Error should still have content
            assert len(result["content"]) > 0
            assert result["content"][0]["type"] == "text"
            assert "Tool execution failed" in result["content"][0]["text"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_session_id_handling(self, mcp_fetchs_url, valid_token, _wait_for_services, unique_test_id):
        """Test Mcp-Session-Id header handling per MCP 2025-06-18."""
        async with httpx.AsyncClient(verify=True) as client:
            # First request should return session ID
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18"},
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                },
            )

            assert response.status_code == HTTP_OK
            assert "Mcp-Session-Id" in response.headers
            session_id = response.headers["Mcp-Session-Id"]

            # Session ID should be ASCII printable characters
            assert session_id.isprintable()
            assert all(32 <= ord(c) <= 126 for c in session_id)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_streamable_http_endpoints(self, mcp_fetchs_url, valid_token, _wait_for_services, unique_test_id):
        """Test Streamable HTTP transport endpoints per MCP 2025-06-18."""
        async with httpx.AsyncClient(verify=True) as client:
            # POST /mcp should work
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                },
            )
            assert response.status_code == HTTP_OK

            # GET /mcp for SSE (may not be implemented)
            response = await client.get(
                f"{mcp_fetchs_url}",
                headers={
                    "Authorization": f"Bearer {valid_token}",
                    "Accept": "text/event-stream",
                },
            )
            # Either 501 (not implemented) or 200 (if SSE is supported)
            assert response.status_code in [200, 501]
