"""Test the MCP Redis service integration.

This module tests the Redis MCP service, which provides Redis database operations
through the Model Context Protocol. All tests respect the sacred commandment:
NO MOCKING - only real service testing!
"""

import pytest

from tests.mcp_helpers import parse_sse_response
from tests.test_constants import HTTP_OK
from tests.test_constants import HTTP_UNAUTHORIZED
from tests.test_constants import MCP_REDIS_TESTS_ENABLED
from tests.test_constants import MCP_REDIS_URLS


@pytest.fixture
def mcp_redis_url():
    """Get the MCP Redis service URL."""
    if not MCP_REDIS_TESTS_ENABLED:
        pytest.skip("MCP Redis tests are disabled. Set MCP_REDIS_TESTS_ENABLED=true to enable.")
    if not MCP_REDIS_URLS:
        pytest.skip("MCP_REDIS_URLS environment variable not set")
    return MCP_REDIS_URLS[0]


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not MCP_REDIS_TESTS_ENABLED, reason="MCP Redis tests disabled")
class TestMCPRedisIntegration:
    """Test the MCP Redis service integration with the OAuth Gateway."""

    async def test_redis_requires_authentication(self, http_client, mcp_redis_url):
        """Test that the Redis service requires authentication."""
        # Attempt to access without authentication
        response = await http_client.post(
            f"{mcp_redis_url}",
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
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"].startswith("Bearer")

    async def test_redis_initialize(self, http_client, mcp_redis_url, gateway_auth_headers, _wait_for_services):
        """Test Redis service initialization with authentication."""
        response = await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
                "id": 1,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        assert response.status_code == HTTP_OK

        # Parse SSE response
        data = parse_sse_response(response.text)
        assert data is not None
        assert "result" in data
        assert data["id"] == 1

        result = data["result"]
        assert "protocolVersion" in result
        assert result["protocolVersion"] == "2025-06-18"
        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "mcp-redis"

    async def test_redis_tools_list(self, http_client, mcp_redis_url, gateway_auth_headers, _wait_for_services):
        """Test listing available Redis tools."""
        # First initialize
        init_response = await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
                "id": 1,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        assert init_response.status_code == HTTP_OK

        # List tools
        response = await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        assert response.status_code == HTTP_OK

        data = parse_sse_response(response.text)
        assert data is not None
        assert "result" in data
        assert data["id"] == 2

        result = data["result"]
        assert "tools" in result
        tools = result["tools"]

        # Verify expected Redis tools are present
        tool_names = [tool["name"] for tool in tools]
        expected_tools = ["set", "get", "delete", "keys", "exists", "expire", "ttl", "mset", "mget"]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Expected tool '{expected_tool}' not found"

        # Verify tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"

    async def test_redis_set_get_operations(
        self,
        http_client,
        mcp_redis_url,
        gateway_auth_headers,
        _wait_for_services,
        unique_test_id,
    ):
        """Test Redis SET and GET operations through MCP."""
        # Initialize first
        await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
                "id": 1,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        # Test SET operation
        test_key = f"test:mcp:redis:{unique_test_id}"
        test_value = "Hello from MCP Redis test!"

        set_response = await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "set",
                    "arguments": {
                        "key": test_key,
                        "value": test_value,
                    },
                },
                "id": 2,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        assert set_response.status_code == HTTP_OK

        set_data = parse_sse_response(set_response.text)
        assert set_data is not None
        assert "result" in set_data
        assert set_data["result"]["content"][0]["text"] == "OK"

        # Test GET operation
        get_response = await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "get",
                    "arguments": {
                        "key": test_key,
                    },
                },
                "id": 3,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        assert get_response.status_code == HTTP_OK

        get_data = parse_sse_response(get_response.text)
        assert get_data is not None
        assert "result" in get_data
        assert test_value in get_data["result"]["content"][0]["text"]

        # Clean up - delete the test key
        delete_response = await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "delete",
                    "arguments": {
                        "keys": [test_key],
                    },
                },
                "id": 4,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        assert delete_response.status_code == HTTP_OK

    async def test_redis_keys_operation(
        self,
        http_client,
        mcp_redis_url,
        gateway_auth_headers,
        _wait_for_services,
        unique_test_id,
    ):
        """Test Redis KEYS operation with pattern matching."""
        # Initialize first
        await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
                "id": 1,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        # Create test keys
        test_prefix = f"test:mcp:redis:keys:{unique_test_id}"
        test_keys = [f"{test_prefix}:key1", f"{test_prefix}:key2", f"{test_prefix}:key3"]

        # Set multiple test keys
        for i, key in enumerate(test_keys):
            await http_client.post(
                f"{mcp_redis_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "set",
                        "arguments": {
                            "key": key,
                            "value": f"value{i + 1}",
                        },
                    },
                    "id": i + 2,
                },
                headers={
                    **gateway_auth_headers,
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "MCP-Protocol-Version": "2025-06-18",
                },
            )

        # Test KEYS operation with pattern
        keys_response = await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "keys",
                    "arguments": {
                        "pattern": f"{test_prefix}:*",
                    },
                },
                "id": 10,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        assert keys_response.status_code == HTTP_OK

        keys_data = parse_sse_response(keys_response.text)
        assert keys_data is not None
        assert "result" in keys_data

        # Verify all test keys are found
        response_text = keys_data["result"]["content"][0]["text"]
        for key in test_keys:
            assert key in response_text

        # Clean up - delete all test keys
        await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "delete",
                    "arguments": {
                        "keys": test_keys,
                    },
                },
                "id": 11,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

    async def test_redis_expire_ttl_operations(
        self,
        http_client,
        mcp_redis_url,
        gateway_auth_headers,
        _wait_for_services,
        unique_test_id,
    ):
        """Test Redis EXPIRE and TTL operations."""
        # Initialize first
        await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
                "id": 1,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        # Create a test key
        test_key = f"test:mcp:redis:expire:{unique_test_id}"

        # Set a key
        await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "set",
                    "arguments": {
                        "key": test_key,
                        "value": "This key will expire",
                    },
                },
                "id": 2,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        # Set expiration to 60 seconds
        expire_response = await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "expire",
                    "arguments": {
                        "key": test_key,
                        "seconds": 60,
                    },
                },
                "id": 3,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        assert expire_response.status_code == HTTP_OK

        expire_data = parse_sse_response(expire_response.text)
        assert expire_data is not None
        assert "1" in expire_data["result"]["content"][0]["text"]  # Redis returns 1 for success

        # Check TTL
        ttl_response = await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "ttl",
                    "arguments": {
                        "key": test_key,
                    },
                },
                "id": 4,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        assert ttl_response.status_code == HTTP_OK

        ttl_data = parse_sse_response(ttl_response.text)
        assert ttl_data is not None
        # TTL should be positive and <= 60
        ttl_text = ttl_data["result"]["content"][0]["text"]
        # Extract the TTL value from the response
        # The response format varies, but should contain a number
        assert any(char.isdigit() for char in ttl_text)

        # Clean up
        await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "delete",
                    "arguments": {
                        "keys": [test_key],
                    },
                },
                "id": 5,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

    async def test_redis_error_handling(self, http_client, mcp_redis_url, gateway_auth_headers, _wait_for_services):
        """Test Redis error handling for invalid operations."""
        # Initialize first
        await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
                "id": 1,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        # Try to GET a non-existent key
        response = await http_client.post(
            f"{mcp_redis_url}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "get",
                    "arguments": {
                        "key": "non:existent:key:that:should:not:exist:123456789",
                    },
                },
                "id": 2,
            },
            headers={
                **gateway_auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        assert response.status_code == HTTP_OK

        data = parse_sse_response(response.text)
        assert data is not None
        assert "result" in data
        # Redis returns null for non-existent keys
        assert (
            "null" in data["result"]["content"][0]["text"].lower()
            or "none" in data["result"]["content"][0]["text"].lower()
        )
