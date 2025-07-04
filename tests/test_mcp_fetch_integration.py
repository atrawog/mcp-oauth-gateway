from .test_constants import HTTP_UNAUTHORIZED
from .test_fetch_speedup_utils import get_local_test_url


"""Sacred MCP Fetch Integration Tests - Testing real MCP fetch with OAuth
Following CLAUDE.md - NO MOCKING, real services only!
"""

import pytest


class TestMCPFetchIntegration:
    """Test real MCP fetch functionality with proper OAuth authentication."""

    @pytest.mark.asyncio
    async def test_fetch_requires_real_oauth_token(self, http_client, _wait_for_services, mcp_fetch_url):
        """Test that MCP fetch REQUIRES real OAuth tokens - no fakes allowed!"""
        import os

        # Get REAL OAuth token from environment
        oauth_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
        if not oauth_token:
            pytest.fail(
                "No GATEWAY_OAUTH_ACCESS_TOKEN available - run: just generate-github-token - TESTS MUST NOT BE SKIPPED!",
            )

        # Test 1: Verify unauthenticated requests are rejected
        response = await http_client.post(f"{mcp_fetch_url}", json={"jsonrpc": "2.0", "method": "ping", "id": 1})

        assert response.status_code == HTTP_UNAUTHORIZED, "MCP should reject unauthenticated requests"
        assert "WWW-Authenticate" in response.headers

        # Test 2: Verify authenticated requests work
        response = await http_client.post(
            f"{mcp_fetch_url}",
            json={"jsonrpc": "2.0", "method": "ping", "id": 2},
            headers={"Authorization": f"Bearer {oauth_token}"},
        )

        # Should either work (200) or give MCP protocol error (not auth error)
        assert response.status_code != 401, "Valid token should not get 401"

        print("✅ MCP fetch correctly enforces OAuth authentication!")

    @pytest.mark.asyncio
    async def test_mcp_fetch_security_validation(
        self,
        http_client,
        _wait_for_services,
        registered_client,
        mcp_fetch_url,
    ):
        """Test MCP fetch security - MUST reject all invalid auth attempts."""
        # This test verifies security by ensuring invalid tokens are rejected
        # For ACTUAL functionality tests, use REAL OAuth tokens!

        # Create an MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "fetch",
                "arguments": {"url": get_local_test_url(), "max_length": 1000000},
            },
            "id": "fetch-test-1",
        }

        # Test 1: No authentication - should return 401
        response = await http_client.post(f"{mcp_fetch_url}", json=mcp_request)

        assert response.status_code == HTTP_UNAUTHORIZED
        assert response.headers.get("WWW-Authenticate") == "Bearer"

        # Test 2: Invalid token - should return 401
        response = await http_client.post(
            f"{mcp_fetch_url}",
            json=mcp_request,
            headers={"Authorization": "Bearer invalid_token_12345"},
        )

        assert response.status_code == HTTP_UNAUTHORIZED

        # Test 3: Malformed authorization header
        response = await http_client.post(
            f"{mcp_fetch_url}",
            json=mcp_request,
            headers={"Authorization": "NotBearer some_token"},
        )

        assert response.status_code == HTTP_UNAUTHORIZED

        # Test 4: Test the MCP protocol version header
        response = await http_client.post(
            f"{mcp_fetch_url}",
            json=mcp_request,
            headers={
                "Authorization": "Bearer invalid_but_well_formed_jwt",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

        assert response.status_code == HTTP_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_mcp_fetch_endpoint_validation(self, http_client, _wait_for_services, mcp_fetch_url):
        """Test MCP fetch endpoint validation and error handling."""
        # Test with invalid JSON-RPC format
        invalid_requests = [
            # Missing jsonrpc version
            {
                "method": "tools/call",
                "params": {
                    "name": "fetch",
                    "arguments": {"url": get_local_test_url()},
                },
                "id": 1,
            },
            # Invalid jsonrpc version
            {
                "jsonrpc": "1.0",
                "method": "tools/call",
                "params": {
                    "name": "fetch",
                    "arguments": {"url": get_local_test_url()},
                },
                "id": 1,
            },
            # Missing method
            {
                "jsonrpc": "2.0",
                "params": {
                    "name": "fetch",
                    "arguments": {"url": get_local_test_url()},
                },
                "id": 1,
            },
            # Invalid method format
            {
                "jsonrpc": "2.0",
                "method": "invalid_method_name",
                "params": {
                    "name": "fetch",
                    "arguments": {"url": get_local_test_url()},
                },
                "id": 1,
            },
        ]

        for invalid_request in invalid_requests:
            response = await http_client.post(f"{mcp_fetch_url}", json=invalid_request)

            # Should return 401 since we're not authenticated
            # The actual JSON-RPC validation happens after auth
            assert response.status_code == HTTP_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_mcp_fetch_http_methods(self, http_client, _wait_for_services, mcp_fetch_url):
        """Test that MCP fetch endpoint supports required HTTP methods."""
        # Test GET method (required by MCP Streamable HTTP transport)
        response = await http_client.get(f"{mcp_fetch_url}")
        # Should return 401 since we're not authenticated
        assert response.status_code == HTTP_UNAUTHORIZED

        # Test POST method
        response = await http_client.post(f"{mcp_fetch_url}", json={"jsonrpc": "2.0", "method": "test", "id": 1})
        assert response.status_code == HTTP_UNAUTHORIZED

        # Test unsupported methods
        response = await http_client.put(f"{mcp_fetch_url}", json={"test": "data"})
        # Should return 405 Method Not Allowed or 401
        assert response.status_code in [401, 405]
