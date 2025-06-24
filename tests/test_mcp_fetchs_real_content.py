from .test_constants import HTTP_OK
"""Real content fetching tests for mcp-fetchs native implementation."""

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


class TestMCPFetchsRealContent:
    """Test fetching real content from various sources."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_example_com_content(
        self, mcp_fetchs_url, gateway_token, wait_for_services
    ):
        """Test fetching example.com and verifying content."""
        async with httpx.AsyncClient(verify=False) as client:
            # Initialize session
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
                    "Authorization": f"Bearer {gateway_token}",
                },
            )

            assert response.status_code == HTTP_OK
            session_id = response.headers.get("Mcp-Session-Id")

            # Fetch example.com
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {"url": "https://example.com", "method": "GET"},
                    },
                    "id": 2,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gateway_token}",
                    "Mcp-Session-Id": session_id,
                },
            )

            assert response.status_code == HTTP_OK
            data = response.json()
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 2
            assert "result" in data

            content = data["result"]["content"][0]
            assert content["type"] == "text"

            # Verify expected content
            text = content["text"]
            assert "Example Domain" in text
            assert "This domain is for use in illustrative examples" in text
            assert "<html" in text
            assert "</html>" in text

            # Check title extraction
            assert content.get("title") == "Example Domain"

    # REMOVED: This test used httpbin.org which violates our testing principles.
    # Per CLAUDE.md: Test against real deployed services (our own), not external ones.
    #
    # @pytest.mark.integration
    # @pytest.mark.asyncio
    # # REMOVED: This test used httpbin.org which violates our testing principles.
 # Per CLAUDE.md: Test against real deployed services (our own), not external ones.
 # async def test_fetchs_httpbin_endpoints(
 #    #     self, mcp_fetchs_url, client_token, wait_for_services
 #    # ):
 #    #     """Test various httpbin.org endpoints for different scenarios."""
 #    #     async with httpx.AsyncClient(verify=False) as client:
 #    #         # Test JSON response
 #    #         response = await client.post(
 #    #             f"{mcp_fetchs_url}",
 #    #             json={
 #    #                 "jsonrpc": "2.0",
 #    #                 "method": "tools/call",
 #    #                 "params": {
 #    #                     "name": "fetch",
 #    #                     "arguments": {
 #    #                         "url": "https://httpbin.org/json",
 #    #                         "method": "GET",
 #    #                     },
 #    #                 },
 #    #                 "id": 1,
 #    #             },
 #    #             headers={
 #    #                 "Content-Type": "application/json",
 #    #                 "Authorization": f"Bearer {client_token}",
 #    #             },
 #    #         )
 #    #
 #    #         assert response.status_code == HTTP_OK
 #    #         data = response.json()
 #    #         content = data["result"]["content"][0]
 #    #         assert content["type"] == "text"
 #    #         assert '"slideshow"' in content["text"]
 #    #
 #    #         # Test user agent reflection
 #    #         response = await client.post(
 #    #             f"{mcp_fetchs_url}",
 #    #             json={
 #    #                 "jsonrpc": "2.0",
 #    #                 "method": "tools/call",
 #    #                 "params": {
 #    #                     "name": "fetch",
 #    #                     "arguments": {
 #    #                         "url": "https://httpbin.org/user-agent",
 #    #                         "method": "GET",
 #    #                         "user_agent": "MCP-Fetchs-Test/2.0",
 #    #                     },
 #    #                 },
 #    #                 "id": 2,
 #    #             },
 #    #             headers={
 #    #                 "Content-Type": "application/json",
 #    #                 "Authorization": f"Bearer {client_token}",
 #    #             },
 #    #         )
 #    #
 #    #         assert response.status_code == HTTP_OK
 #    #         data = response.json()
 #    #         content = data["result"]["content"][0]
 #    #         assert "MCP-Fetchs-Test/2.0" in content["text"]
 #    #
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_auth_service_health(
        self, mcp_fetchs_url, base_domain, gateway_token, wait_for_services
    ):
        """Test fetching from our own auth service."""
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {
                            "url": f"https://auth.{base_domain}/.well-known/oauth-authorization-server",  # TODO: Break long line
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

            assert response.status_code == HTTP_OK
            data = response.json()
            content = data["result"]["content"][0]

            # Should contain OAuth metadata
            assert "issuer" in content["text"]
            assert "authorization_endpoint" in content["text"]
            assert "token_endpoint" in content["text"]
 #
 #    # REMOVED: This test used httpbin.org which violates our testing principles.
 #    # Per CLAUDE.md: Test against real deployed services (our own), not external ones.
 #    #
 #    # @pytest.mark.integration
 #    # @pytest.mark.asyncio
 #    # # REMOVED: This test used httpbin.org which violates our testing principles.
 # Per CLAUDE.md: Test against real deployed services (our own), not external ones.
 # async def test_fetchs_redirect_following(
 # #    #     self, mcp_fetchs_url, gateway_token, wait_for_services
 # #    # ):
 # #    #     """Test automatic redirect following."""
 # #    #     async with httpx.AsyncClient(verify=False) as client:
 # #    #         # httpbin.org/redirect/2 redirects twice
 # #    #         response = await client.post(
 # #    #             f"{mcp_fetchs_url}",
 # #    #             json={
 # #    #                 "jsonrpc": "2.0",
 # #    #                 "method": "tools/call",
 # #    #                 "params": {
 # #    #                     "name": "fetch",
 # #    #                     "arguments": {
 # #    #                         "url": "https://httpbin.org/redirect/2",
 # #    #                         "method": "GET",
 # #    #                     },
 # #    #                 },
 # #    #                 "id": 1,
 # #    #             },
 # #    #             headers={
 # #    #                 "Content-Type": "application/json",
 # #    #                 "Authorization": f"Bearer {gateway_token}",
 # #    #             },
 # #    #         )
 # #    #
 # #    #         assert response.status_code == HTTP_OK
 # #    #         data = response.json()
 # #    #         content = data["result"]["content"][0]
 # #    #
 # #    #         # Should end up at /get endpoint
 # #    #         assert '"url": "https://httpbin.org/get"' in content["text"]
 # #    #
 # #    # @pytest.mark.integration
 # #    #    # REMOVED: This test used httpbin.org which violates our testing principles.
 # #    # Per CLAUDE.md: Test against real deployed services (our own), not external ones.
 # #    # test.mark.asyncio
 # #    # # REMOVED: This test used httpbin.org which violates our testing principles.
 # Per CLAUDE.md: Test against real deployed services (our own), not external ones.
 # async def test_fetchs_different_content_types(
 # # #    #     self, mcp_fetchs_url, gateway_token, wait_for_services
 # # #    # ):
 # # #    #     """Test handling different content types."""
 # # #    #     content_type_tests = [
 # # #    #         ("https://httpbin.org/html", "text/html", "Herman Melville"),
 # # #    #         ("https://httpbin.org/json", "application/json", "slideshow"),
 # # #    #         ("https://httpbin.org/xml", "application/xml", "<?xml"),
 # # #    #     ]
 # # #    #
 # # #    #     async with httpx.AsyncClient(verify=False) as client:
 # # #    #         for url, _expected_type, expected_content in content_type_tests:
 # # #    #             response = await client.post(
 # # #    #                 f"{mcp_fetchs_url}",
 # # #    #                 json={
 # # #    #                     "jsonrpc": "2.0",
 # # #    #                     "method": "tools/call",
 # # #    #                     "params": {
 # # #    #                         "name": "fetch",
 # # #    #                         "arguments": {"url": url, "method": "GET"},
 # # #    #                     },
 # # #    #                     "id": 1,
 # # #    #                 },
 # # #    #                 headers={
 # # #    #                     "Content-Type": "application/json",
 # # #    #                     "Authorization": f"Bearer {gateway_token}",
 # # #    #                 },
 # # #    #             )
 # # #    #
 # # #    #             assert response.status_code == HTTP_OK
 # # #    #             data = response.json()
 # # #    #             content = data["result"]["content"][0]
 # # #    #             assert content["type"] == "text"
 # # #    #             assert expected_content in content["text"]
 # # #    #
 # # #    # @pytest.mark.integration
 # # #    #    # REMOVED: This test used httpbin.org which violates our testing principles.
 # # #    # Per CLAUDE.md: Test against real deployed services (our own), not external ones.
 # # #    # test.mark.asyncio
 # # #    # # REMOVED: This test used httpbin.org which violates our testing principles.
 # Per CLAUDE.md: Test against real deployed services (our own), not external ones.
 # async def test_fetchs_response_size_handling(
 # # # #    #     self, mcp_fetchs_url, gateway_token, wait_for_services
 # # # #    # ):
 # # # #    #     """Test handling of large responses."""
 # # # #    #     async with httpx.AsyncClient(verify=False) as client:
 # # # #    #         # Request 1KB of data
 # # # #    #         response = await client.post(
 # # # #    #             f"{mcp_fetchs_url}",
 # # # #    #             json={
 # # # #    #                 "jsonrpc": "2.0",
 # # # #    #                 "method": "tools/call",
 # # # #    #                 "params": {
 # # # #    #                     "name": "fetch",
 # # # #    #                     "arguments": {
 # # # #    #                         "url": "https://httpbin.org/bytes/1024",
 # # # #    #                         "method": "GET",
 # # # #    #                         "max_length": 500,  # Limit to 500 chars
 # # # #    #                     },
 # # # #    #                 },
 # # # #    #                 "id": 1,
 # # # #    #             },
 # # # #    #             headers={
 # # # #    #                 "Content-Type": "application/json",
 # # # #    #                 "Authorization": f"Bearer {gateway_token}",
 # # # #    #             },
 # # # #    #         )
 # # # #    #
 # # # #    #         assert response.status_code == HTTP_OK
 # # # #    #         data = response.json()
 # # # #    #
 # # # #    #         # Binary data should be represented somehow
 # # # #    #         if "error" not in data:
 # # # #    #             content = data["result"]["content"][0]
 # # # #    #             # Should be truncated
 # # # #    #             assert len(content["text"]) < 600  # Some overhead for representation
 # # # #    #
 # # # #    # @pytest.mark.integration
 # # # #    #    # REMOVED: This test used httpbin.org which violates our testing principles.
 # # # #    # Per CLAUDE.md: Test against real deployed services (our own), not external ones.
 # # # #    # test.mark.asyncio
 # # # #    # # REMOVED: This test used httpbin.org which violates our testing principles.
 # Per CLAUDE.md: Test against real deployed services (our own), not external ones.
 # async def test_fetchs_status_code_handling(
 # # # # #    #     self, mcp_fetchs_url, gateway_token, wait_for_services
 # # # # #    # ):
 # # # # #    #     """Test handling of various HTTP status codes."""
 # # # # #    #     status_codes = [200, 201, 301, 400, 401, 403, 404, 500, 502]
 # # # # #    #
 # # # # #    #     async with httpx.AsyncClient(verify=False) as client:
 # # # # #    #         for status in status_codes:
 # # # # #    #             response = await client.post(
 # # # # #    #                 f"{mcp_fetchs_url}",
 # # # # #    #                 json={
 # # # # #    #                     "jsonrpc": "2.0",
 # # # # #    #                     "method": "tools/call",
 # # # # #    #                     "params": {
 # # # # #    #                         "name": "fetch",
 # # # # #    #                         "arguments": {
 # # # # #    #                             "url": f"https://httpbin.org/status/{status}",
 # # # # #    #                             "method": "GET",
 # # # # #    #                         },
 # # # # #    #                     },
 # # # # #    #                     "id": status,
 # # # # #    #                 },
 # # # # #    #                 headers={
 # # # # #    #                     "Content-Type": "application/json",
 # # # # #    #                     "Authorization": f"Bearer {gateway_token}",
 # # # # #    #                 },
 # # # # #    #             )
 # # # # #    #
 # # # # #    #             assert response.status_code == HTTP_OK
 # # # # #    #             data = response.json()
 # # # # #    #
 # # # # #    #             if status >= 400:
 # # # # #    #                 # Should return error for 4xx and 5xx
 # # # # #    #                 assert "result" in data
 # # # # #    #                 assert data["result"]["isError"] is True
 # # # # #    #                 assert str(status) in data["result"]["content"][0]["text"]
 # # # # #    #             # Should succeed for 2xx and 3xx (after redirect)
 # # # # #    #             elif status not in [301, 302, 303, 307, 308]:  # Redirect codes
 # # # # #    #                 assert "result" in data
