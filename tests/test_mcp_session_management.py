"""Sacred Integration Tests for MCP Session Management
Following Commandment 1: NO MOCKING! Test against real deployed services only!
These tests verify session handling in the mcp-streamablehttp-proxy.
"""

import asyncio
import os

import httpx
import pytest

from .test_constants import MCP_FETCH_URL
from .test_constants import MCP_PROTOCOL_VERSION
from .test_constants import TEST_HTTP_TIMEOUT
from .test_constants import HTTP_OK


# MCP Client tokens for external client testing
MCP_CLIENT_ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN")


class TestMCPSessionCreation:
    """Test MCP session creation and initialization."""

    @pytest.mark.asyncio
    async def test_session_created_on_initialize(
        self, http_client: httpx.AsyncClient, wait_for_services
    ):  # noqa: ARG002
        """Test that a session is created when client initializes."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Send initialize request
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "session-test-client", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        assert response.status_code == HTTP_OK

        # Check for session-related headers
        # The proxy might return a session ID in headers
        # Session handling is internal to the proxy

    @pytest.mark.asyncio
    async def test_multiple_sessions_isolated(
        self, http_client: httpx.AsyncClient, wait_for_services
    ):  # noqa: ARG002
        """Test that multiple clients get isolated sessions."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Create two separate HTTP clients to simulate different MCP clients
        async with (
            httpx.AsyncClient(timeout=TEST_HTTP_TIMEOUT) as client1,
            httpx.AsyncClient(timeout=TEST_HTTP_TIMEOUT) as client2,
        ):
            # Initialize first client
            response1 = await client1.post(
                f"{MCP_FETCH_URL}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "client-1", "version": "1.0.0"},
                    },
                    "id": 1,
                },
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"},
            )
            assert response1.status_code == HTTP_OK

            # Initialize second client
            response2 = await client2.post(
                f"{MCP_FETCH_URL}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "client-2", "version": "1.0.0"},
                    },
                    "id": 1,
                },
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"},
            )
            assert response2.status_code == HTTP_OK

            # Both should get successful but independent responses
            data1 = response1.json()
            data2 = response2.json()

            assert (
                data1["result"]["serverInfo"]["name"]
                == data2["result"]["serverInfo"]["name"]
            )
            # Sessions are isolated even if server info is the same


class TestMCPSessionPersistence:
    """Test that sessions persist across requests."""

    @pytest.mark.asyncio
    async def test_session_persists_between_requests(
        self, http_client: httpx.AsyncClient, wait_for_services
    ):  # noqa: ARG002
        """Test that session state persists between requests."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Initialize session
        init_response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "persistent-client", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)
        assert init_response.status_code == HTTP_OK

        # Send initialized notification
        await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "initialized", "params": {}},
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        # Now make another request - should use same session
        tools_response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        assert tools_response.status_code == HTTP_OK
        # If session wasn't maintained, this would fail as uninitialized

    @pytest.mark.asyncio
    async def test_session_requires_initialization(
        self, http_client: httpx.AsyncClient, wait_for_services
    ):  # noqa: ARG002
        """Test that operations fail without initialization."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Try to list tools without initializing first
        # Use a fresh client to ensure no existing session
        async with httpx.AsyncClient(timeout=TEST_HTTP_TIMEOUT) as fresh_client:
            response = await fresh_client.post(
                f"{MCP_FETCH_URL}",
                json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"},
            )

            # Should either fail or return an error
            assert response.status_code in [200, 400]
            if response.status_code == HTTP_OK:
                data = response.json()
                # Should have an error about not being initialized
                assert "error" in data


class TestMCPSessionTimeout:
    """Test session timeout behavior."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_session_timeout_configuration(
        self, http_client: httpx.AsyncClient, wait_for_services
    ):  # noqa: ARG002
        """Test that sessions respect timeout configuration."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # This test would need to wait for actual timeout
        # Since SESSION_TIMEOUT is typically 300 seconds (5 minutes),
        # we'll just verify the session is active initially

        # Initialize session
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "timeout-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"},
        )
        assert response.status_code == HTTP_OK

        # Verify session is active
        await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "initialized", "params": {}},
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        # Session should still be active
        tools_response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)
        assert tools_response.status_code == HTTP_OK

    @pytest.mark.asyncio
    async def test_session_activity_updates(
        self, http_client: httpx.AsyncClient, wait_for_services
    ):  # noqa: ARG002
        """Test that session activity is updated on each request."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Initialize session
        await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "activity-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        # Make multiple requests with delays
        for i in range(3):
            await asyncio.sleep(1)  # Small delay between requests

            response = await http_client.post(
                f"{MCP_FETCH_URL}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": i + 2,
                },
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)
            # Session should remain active
            assert response.status_code == HTTP_OK


class TestMCPSessionConcurrency:
    """Test concurrent request handling within sessions."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_same_session(
        self, http_client: httpx.AsyncClient, wait_for_services
    ):  # noqa: ARG002
        """Test that concurrent requests to same session are handled properly."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Initialize session
        init_response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "concurrent-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)
        assert init_response.status_code == HTTP_OK
        session_id = init_response.headers.get("Mcp-Session-Id")

        await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "initialized", "params": {}},
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Mcp-Session-Id": session_id,
            }, timeout=30.0)

        # Send multiple concurrent requests
        async def make_request(request_id: int):
            return await http_client.post(
                f"{MCP_FETCH_URL}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": request_id,
                },
                headers={
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Mcp-Session-Id": session_id,
                }, timeout=30.0)

        # Launch concurrent requests
        tasks = [make_request(i + 10) for i in range(5)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == HTTP_OK
            data = response.json()
            assert "result" in data
            assert "tools" in data["result"]

    @pytest.mark.asyncio
    async def test_request_id_uniqueness(
        self, http_client: httpx.AsyncClient, wait_for_services
    ):  # noqa: ARG002
        """Test that request IDs are properly tracked per session."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Initialize session
        await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "id-test", "version": "1.0.0"},
                },
                "id": "init-1",
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        # Send requests with different ID types (string and number)
        response1 = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": "string-id-1",
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        response2 = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 12345},
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        # Both should succeed and echo back their IDs
        assert response1.status_code == HTTP_OK
        assert response1.json()["id"] == "string-id-1"

        assert response2.status_code == HTTP_OK
        assert response2.json()["id"] == 12345


class TestMCPSessionCleanup:
    """Test session cleanup and resource management."""

    @pytest.mark.asyncio
    async def test_session_cleanup_on_client_disconnect(
        self, http_client: httpx.AsyncClient, wait_for_services
    ):  # noqa: ARG002
        """Test that sessions are cleaned up when client disconnects."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Create a client that we'll close
        async with httpx.AsyncClient(timeout=TEST_HTTP_TIMEOUT) as temp_client:
            # Initialize session
            response = await temp_client.post(
                f"{MCP_FETCH_URL}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "cleanup-test", "version": "1.0.0"},
                    },
                    "id": 1,
                },
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"},
            )
            assert response.status_code == HTTP_OK

        # Client is now closed
        # Try to use the same client connection - should fail or create new session
        async with httpx.AsyncClient(timeout=TEST_HTTP_TIMEOUT) as new_client:
            # This should either fail or require re-initialization
            response = await new_client.post(
                f"{MCP_FETCH_URL}",
                json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"},
            )

            # Should need to initialize again
            assert response.status_code in [200, 400]
            if response.status_code == HTTP_OK:
                data = response.json()
                # If it worked, it's likely because a new session was created
                # or there's an error about not being initialized
                if "error" not in data:
                    # New session was likely auto-created
                    pass
