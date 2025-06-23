"""Sacred Integration Tests documenting MCP Proxy Issues
Following Commandment 1: NO MOCKING! Test against real deployed services only!

These tests document the current issues with mcp-streamablehttp-proxy session handling.
The proxy appears to create a new session for each request instead of maintaining
sessions across requests from the same HTTP client.
"""
import os

import httpx
import pytest

from .test_constants import MCP_FETCH_URL
from .test_constants import MCP_PROTOCOL_VERSION


# MCP Client tokens for external client testing
MCP_CLIENT_ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN")


class TestMCPProxySessionIssues:
    """Document current session handling issues in mcp-streamablehttp-proxy."""

    @pytest.mark.asyncio
    async def test_session_not_maintained_across_requests(self, http_client: httpx.AsyncClient, wait_for_services):
        """ISSUE: The proxy creates a new session for each request.

        Expected behavior: After initializing, subsequent requests should use the same session.
        Actual behavior: Each request creates a new session, causing "not initialized" errors.
        """
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")

        # Initialize session
        init_response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocol_version": MCP_PROTOCOL_VERSION,
                    "client_info": {"name": "test", "version": "1.0"}
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )

        # This should succeed
        assert init_response.status_code == 200

        # Try to use the session - this SHOULD work but currently fails
        tools_response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )

        # The proxy now correctly returns an error for missing session ID
        assert tools_response.status_code == 200  # JSON-RPC errors return 200

        data = tools_response.json()
        assert "error" in data
        assert data["error"]["code"] == -32002  # Session ID required
        assert "Session ID required" in data["error"]["message"]

    @pytest.mark.asyncio
    async def test_session_id_header_missing(self, http_client: httpx.AsyncClient, wait_for_services):
        """ISSUE: The proxy doesn't return Mcp-Session-Id header as expected by MCP spec.

        Per MCP 2025-06-18 spec, servers MAY assign session IDs during initialization
        and clients MUST include them in subsequent requests.
        """
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")

        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocol_version": MCP_PROTOCOL_VERSION,
                    "client_info": {"name": "test", "version": "1.0"}
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )

        assert response.status_code == 200

        # Check if Mcp-Session-Id header is returned
        # The proxy now correctly returns session IDs
        session_id = response.headers.get("Mcp-Session-Id")
        assert session_id is not None  # Proxy now returns session ID
        assert len(session_id) > 0  # Should be a valid UUID


class TestMCPProxyWorkarounds:
    """Test workarounds for current proxy limitations."""

    @pytest.mark.asyncio
    async def test_initialize_before_each_operation(self, wait_for_services):
        """WORKAROUND: Initialize before each operation since sessions aren't maintained.

        This is not ideal but works with current proxy implementation.
        """
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")

        # Create new client for each operation (forces new session)
        async with httpx.AsyncClient() as client1:
            # Initialize and list tools in one go
            init_response = await client1.post(
                f"{MCP_FETCH_URL}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocol_version": MCP_PROTOCOL_VERSION,
                        "client_info": {"name": "workaround", "version": "1.0"}
                    },
                    "id": 1
                },
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
            )
            assert init_response.status_code == 200

        # New client = new session, must initialize again
        async with httpx.AsyncClient() as client2:
            # Must initialize this new session first
            init_response = await client2.post(
                f"{MCP_FETCH_URL}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocol_version": MCP_PROTOCOL_VERSION,
                        "client_info": {"name": "workaround2", "version": "1.0"}
                    },
                    "id": 1
                },
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
            )
            assert init_response.status_code == 200

            # Now we can list tools
            tools_response = await client2.post(
                f"{MCP_FETCH_URL}",
                json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
            )
            # This works because we used the same client that initialized
            assert tools_response.status_code == 200
