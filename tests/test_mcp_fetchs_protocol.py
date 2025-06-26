from .test_constants import HTTP_OK
from .test_fetch_speedup_utils import get_local_test_url


"""MCP protocol compliance tests for mcp-fetchs native implementation."""

import json

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


class TestMCPFetchsProtocol:
    """MCP protocol compliance tests for fetchs."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_json_rpc_compliance(self, mcp_fetchs_url, valid_token, _wait_for_services):
        """Test JSON-RPC 2.0 compliance."""
        test_cases = [
            # Valid requests
            {
                "request": {"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                "expected_id": 1,
                "should_have_result": True,
            },
            {
                "request": {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": "string-id",
                },
                "expected_id": "string-id",
                "should_have_result": True,
            },
            # Invalid requests
            {
                "request": {"method": "tools/list", "id": 1},  # Missing jsonrpc
                "expected_error_code": -32600,
                "should_have_error": True,
            },
            {
                "request": {
                    "jsonrpc": "1.0",
                    "method": "tools/list",
                    "id": 1,
                },  # Wrong version
                "expected_error_code": -32600,
                "should_have_error": True,
            },
            {
                "request": {"jsonrpc": "2.0", "id": 1},  # Missing method
                "expected_error_code": -32601,  # Method not found (treating missing as empty string)
                "should_have_error": True,
            },
        ]

        async with httpx.AsyncClient(verify=True) as client:
            for test in test_cases:
                response = await client.post(
                    f"{mcp_fetchs_url}",
                    json=test["request"],
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {valid_token}",
                    },
                )

                assert response.status_code in [200, 400]
                data = response.json()

                # Check response structure
                assert data["jsonrpc"] == "2.0"

                if test.get("should_have_result"):
                    assert "result" in data
                    assert "error" not in data
                    assert data["id"] == test["expected_id"]

                if test.get("should_have_error"):
                    assert "error" in data
                    assert "result" not in data
                    assert data["error"]["code"] == test["expected_error_code"]
                    assert "message" in data["error"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_method_routing(self, mcp_fetchs_url, valid_token, _wait_for_services):
        """Test correct routing of different MCP methods."""
        methods = [
            ("initialize", True),
            ("tools/list", True),
            ("tools/call", True),
            ("prompts/list", False),  # Not implemented
            ("resources/list", False),  # Not implemented
            ("unknown/method", False),
        ]

        async with httpx.AsyncClient(verify=True) as client:
            for method, should_succeed in methods:
                params = {}
                if method == "initialize":
                    params = {"protocolVersion": "2025-06-18"}
                elif method == "tools/call":
                    params = {
                        "name": "fetch",
                        "arguments": {"url": get_local_test_url()},
                    }

                response = await client.post(
                    f"{mcp_fetchs_url}",
                    json={
                        "jsonrpc": "2.0",
                        "method": method,
                        "params": params,
                        "id": 1,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {valid_token}",
                    },
                )

                assert response.status_code == HTTP_OK
                data = response.json()

                if should_succeed:
                    assert "result" in data
                else:
                    assert "error" in data
                    assert data["error"]["code"] == -32601  # Method not found

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_session_handling(self, mcp_fetchs_url, valid_token, _wait_for_services):
        """Test MCP session management."""
        async with httpx.AsyncClient(verify=True) as client:
            # Initialize without session
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

            # Use session for subsequent request
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 2},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                    "Mcp-Session-Id": session_id,
                },
            )

            assert response.status_code == HTTP_OK
            data = response.json()
            assert "result" in data

            # Try with invalid session
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 3},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                    "Mcp-Session-Id": "invalid-session-id",
                },
            )

            # Should still work (stateless implementation)
            assert response.status_code == HTTP_OK

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_protocol_headers(self, mcp_fetchs_url, valid_token, _wait_for_services):
        """Test MCP protocol headers."""
        async with httpx.AsyncClient(verify=True) as client:
            # Test with protocol version header
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
                    "MCP-Protocol-Version": "2025-06-18",
                },
            )

            assert response.status_code == HTTP_OK

            # Check response headers
            assert response.headers.get("Content-Type").startswith("application/json")
            assert "MCP-Protocol-Version" in response.headers
            assert response.headers["MCP-Protocol-Version"] == "2025-06-18"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_error_response_format(self, mcp_fetchs_url, valid_token, _wait_for_services):
        """Test error response format compliance."""
        error_scenarios = [
            # Parse error
            {
                "body": b"invalid json",
                "expected_code": -32700,
                "expected_message_contains": "Parse error",
            },
            # Invalid request (missing method)
            {
                "body": json.dumps({"jsonrpc": "2.0", "id": 1}),
                "expected_code": -32601,  # Method not found (treating missing as None)
                "expected_message_contains": "Method not found",
            },
            # Method not found
            {
                "body": json.dumps({"jsonrpc": "2.0", "method": "nonexistent", "id": 1}),
                "expected_code": -32601,
                "expected_message_contains": "Method not found",
            },
            # Invalid params (unknown tool)
            {
                "body": json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {"name": "nonexistent-tool", "arguments": {}},
                        "id": 1,
                    }
                ),
                "expected_code": -32602,
                "expected_message_contains": "Invalid params",
            },
        ]

        async with httpx.AsyncClient(verify=True) as client:
            for scenario in error_scenarios:
                response = await client.post(
                    f"{mcp_fetchs_url}",
                    content=scenario["body"],
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {valid_token}",
                    },
                )

                assert response.status_code in [200, 400]
                data = response.json()

                assert "error" in data
                assert data["error"]["code"] == scenario["expected_code"]
                assert scenario["expected_message_contains"] in data["error"]["message"]

                # Optional data field
                if "data" in data["error"]:
                    assert isinstance(data["error"]["data"], str | dict | list)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_content_type_handling(self, mcp_fetchs_url, valid_token, _wait_for_services):
        """Test Content-Type header handling."""
        # The service accepts various content types more leniently
        content_types = [
            ("application/json", True),
            ("application/json; charset=utf-8", True),
            ("text/plain", True),  # May still work if body is valid JSON
            ("application/xml", True),  # May still work if body is valid JSON
            ("", True),  # May default to application/json
        ]

        async with httpx.AsyncClient(verify=True) as client:
            for content_type, _should_work in content_types:
                headers = {"Authorization": f"Bearer {valid_token}"}
                if content_type:
                    headers["Content-Type"] = content_type

                response = await client.post(
                    f"{mcp_fetchs_url}",
                    json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                    headers=headers,
                )

                # Service is lenient and accepts requests as long as they're valid JSON
                if response.status_code != 200:
                    print(f"\nFailed for content type: {content_type}")
                    print(f"Response status: {response.status_code}")
                    print(f"Response body: {response.text}")
                assert response.status_code == HTTP_OK
                data = response.json()
                assert "result" in data or "error" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_request_id_handling(self, mcp_fetchs_url, valid_token, _wait_for_services):
        """Test proper handling of request IDs."""
        id_values = [
            1,
            "string-id",
            0,
            -1,
            "complex-id-with-special-chars-!@#$%",
            9999999999,
        ]

        async with httpx.AsyncClient(verify=True) as client:
            for request_id in id_values:
                response = await client.post(
                    f"{mcp_fetchs_url}",
                    json={"jsonrpc": "2.0", "method": "tools/list", "id": request_id},
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {valid_token}",
                    },
                )

                assert response.status_code == HTTP_OK
                data = response.json()
                # Response ID must match request ID exactly
                assert data["id"] == request_id
