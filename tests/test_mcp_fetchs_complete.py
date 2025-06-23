"""Comprehensive integration tests for mcp-fetchs native implementation."""

import json

import httpx
import pytest

from tests.test_constants import BASE_DOMAIN
from tests.test_constants import GATEWAY_OAUTH_ACCESS_TOKEN
from tests.test_constants import MCP_CLIENT_ACCESS_TOKEN


@pytest.fixture
def base_domain():
    """Base domain for tests."""
    return BASE_DOMAIN


@pytest.fixture
def gateway_token():
    """Gateway OAuth token for testing."""
    return GATEWAY_OAUTH_ACCESS_TOKEN


@pytest.fixture
def client_token():
    """MCP client access token for testing."""
    return MCP_CLIENT_ACCESS_TOKEN


class TestMCPFetchsComplete:
    """Comprehensive tests for mcp-fetchs matching mcp-fetch test coverage."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_complete_oauth_flow_integration(
        self, mcp_fetchs_url, gateway_token, wait_for_services
    ):
        """Test complete OAuth flow from authentication to content fetching."""
        # Step 1: Verify authentication is required
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={"jsonrpc": "2.0", "method": "initialize", "id": 1},
                headers={"Content-Type": "application/json"},
            )
            assert response.status_code == 401
            assert response.headers["WWW-Authenticate"] == "Bearer"

        # Step 2: Initialize MCP session with authentication
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18", "capabilities": {}},
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_token}",
                    "MCP-Protocol-Version": "2025-06-18",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 1
            assert "result" in data

            result = data["result"]
            assert result["protocolVersion"] == "2025-06-18"
            assert result["serverInfo"]["name"] == "mcp-fetch-streamablehttp"
            assert "Mcp-Session-Id" in response.headers
            session_id = response.headers["Mcp-Session-Id"]

        # Step 3: List available tools
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 2},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_token}",
                    "Mcp-Session-Id": session_id,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 2
            assert "result" in data

            tools = data["result"]["tools"]
            assert len(tools) >= 1
            fetch_tool = next((t for t in tools if t["name"] == "fetch"), None)
            assert fetch_tool is not None
            assert fetch_tool["description"] == "Fetch a URL and return its contents"

        # Step 4: Fetch actual content
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {"url": "https://example.com", "method": "GET"},
                    },
                    "id": 3,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_token}",
                    "Mcp-Session-Id": session_id,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 3
            assert "result" in data

            result = data["result"]
            assert "content" in result
            assert len(result["content"]) >= 1

            content = result["content"][0]
            assert content["type"] == "text"
            assert "Example Domain" in content["text"]
            assert content.get("title") == "Example Domain"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_with_mcp_client_token(
        self, mcp_fetchs_url, client_token, wait_for_services
    ):
        """Test fetchs using MCP client access token."""
        async with httpx.AsyncClient(verify=False) as client:
            # Initialize session
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18", "capabilities": {}},
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {client_token}",
                    "MCP-Protocol-Version": "2025-06-18",
                },
            )

            assert response.status_code == 200
            session_id = response.headers.get("Mcp-Session-Id")

            # Fetch content
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {
                            "url": "https://httpbin.org/html",
                            "method": "GET",
                        },
                    },
                    "id": 2,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {client_token}",
                    "Mcp-Session-Id": session_id,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 2
            assert "result" in data

            content = data["result"]["content"][0]
            assert content["type"] == "text"
            assert "Herman Melville" in content["text"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_url_parameter_validation(
        self, mcp_fetchs_url, gateway_token, wait_for_services
    ):
        """Test URL parameter validation in fetchs."""
        async with httpx.AsyncClient(verify=False) as client:
            # Test missing URL
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": "fetch", "arguments": {"method": "GET"}},
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_token}",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            assert data["result"]["isError"] is True
            assert "Tool execution failed" in data["result"]["content"][0]["text"]

            # Test invalid URL scheme
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {
                            "url": "ftp://example.com/file.txt",
                            "method": "GET",
                        },
                    },
                    "id": 2,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_token}",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            assert data["result"]["isError"] is True
            assert "Tool execution failed" in data["result"]["content"][0]["text"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_max_length_parameter(
        self, mcp_fetchs_url, gateway_token, wait_for_services
    ):
        """Test max_length parameter handling."""
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {
                            "url": "https://httpbin.org/html",
                            "method": "GET",
                            "max_length": 100,  # Very small limit
                        },
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_token}",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 1
            assert "result" in data

            content = data["result"]["content"][0]
            assert content["type"] == "text"
            assert len(content["text"]) <= 200  # Should be truncated
            assert "truncated" in content["text"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_custom_headers_and_user_agent(
        self, mcp_fetchs_url, gateway_token, wait_for_services
    ):
        """Test custom headers and user agent support."""
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {
                            "url": "https://httpbin.org/headers",
                            "method": "GET",
                            "headers": {"X-Custom-Header": "test-value"},
                            "user_agent": "MCP-Fetchs-Test/1.0",
                        },
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_token}",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 1
            assert "result" in data

            content = data["result"]["content"][0]
            assert content["type"] == "text"
            # httpbin returns the headers it received
            assert "X-Custom-Header" in content["text"]
            assert "test-value" in content["text"]
            assert "MCP-Fetchs-Test/1.0" in content["text"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_post_method_with_body(
        self, mcp_fetchs_url, gateway_token, wait_for_services
    ):
        """Test POST method with request body."""
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {
                            "url": "https://httpbin.org/post",
                            "method": "POST",
                            "body": json.dumps({"test": "data", "fetchs": True}),
                            "headers": {"Content-Type": "application/json"},
                        },
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_token}",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 1
            assert "result" in data

            content = data["result"]["content"][0]
            assert content["type"] == "text"
            # httpbin echoes back the posted data
            assert '"test": "data"' in content["text"]
            assert '"fetchs": true' in content["text"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_error_handling(
        self, mcp_fetchs_url, gateway_token, wait_for_services
    ):
        """Test error handling for various failure scenarios."""
        async with httpx.AsyncClient(verify=False) as client:
            # Test 404 response
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {
                            "url": "https://httpbin.org/status/404",
                            "method": "GET",
                        },
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_token}",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            assert data["result"]["isError"] is True
            # Accept either 404 (from httpbin.org) or 502 (if httpbin.org is unreachable)
            error_text = data["result"]["content"][0]["text"]
            assert "404" in error_text or "502" in error_text

            # Test invalid domain
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {
                            "url": "https://this-domain-definitely-does-not-exist-12345.com",
                            "method": "GET",
                        },
                    },
                    "id": 2,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_token}",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            assert data["result"]["isError"] is True
            error_text = data["result"]["content"][0]["text"].lower()
            assert "request failed" in error_text or "resolve" in error_text

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_protocol_version_negotiation(
        self, mcp_fetchs_url, gateway_token, wait_for_services
    ):
        """Test protocol version negotiation."""
        async with httpx.AsyncClient(verify=False) as client:
            # Try with older protocol version
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {"protocolVersion": "1.0", "capabilities": {}},
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_token}",
                    # Don't send MCP-Protocol-Version header to test protocol-level negotiation
                },
            )

            assert response.status_code == 200
            data = response.json()
            # Server should respond with an error for unsupported version
            assert "error" in data
            assert data["error"]["code"] == -32602  # Invalid params
            assert data["error"]["message"] == "Invalid params"
            assert "Unsupported protocol version" in data["error"]["data"]
            assert (
                "1.0" in data["error"]["data"]
            )  # Should mention the attempted version
            assert (
                "2025-06-18" in data["error"]["data"]
            )  # Should mention supported version

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_session_management(
        self, mcp_fetchs_url, gateway_token, wait_for_services
    ):
        """Test session management behavior."""
        async with httpx.AsyncClient(verify=False) as client:
            # Create two separate initialization requests
            responses = []
            for i in range(2):
                response = await client.post(
                    f"{mcp_fetchs_url}",
                    json={
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {"protocolVersion": "2025-06-18", "capabilities": {}},
                        "id": i + 1,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {gateway_token}",
                        "MCP-Protocol-Version": "2025-06-18",
                    },
                )

                assert response.status_code == 200
                responses.append(response)

            # Both should have session IDs (implementation may return same ID for stateless)
            session_ids = [r.headers.get("Mcp-Session-Id") for r in responses]
            assert all(sid is not None for sid in session_ids)

            # Verify sessions work (regardless of whether they're the same)
            for idx, session_id in enumerate(session_ids):
                response = await client.post(
                    f"{mcp_fetchs_url}",
                    json={"jsonrpc": "2.0", "method": "tools/list", "id": idx + 10},
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {gateway_token}",
                        "Mcp-Session-Id": session_id,
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["id"] == idx + 10

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_concurrent_requests(
        self, mcp_fetchs_url, gateway_token, wait_for_services
    ):
        """Test concurrent request handling."""
        import asyncio

        async def make_fetch_request(client, request_id):
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {
                            "url": "https://httpbin.org/delay/1",
                            "method": "GET",
                        },
                    },
                    "id": request_id,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_token}",
                },
            )
            return response

        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            # Make 5 concurrent requests
            tasks = [make_fetch_request(client, i) for i in range(1, 6)]
            responses = await asyncio.gather(*tasks)

            # All should succeed
            for idx, response in enumerate(responses):
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == idx + 1
                assert "result" in data or "error" in data
