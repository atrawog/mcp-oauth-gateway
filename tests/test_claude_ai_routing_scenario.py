"""Test Claude.ai Routing Scenario
Following CLAUDE.md - NO MOCKING, real services only!

This test specifically verifies the scenario that caused the 404 error:
When Claude.ai tries to access the MCP endpoint at /mcp
"""

import httpx
import pytest

from .test_constants import BASE_DOMAIN
from .test_constants import HTTP_OK
from .test_constants import HTTP_CREATED
from .test_constants import HTTP_NO_CONTENT
from .test_constants import HTTP_UNAUTHORIZED
from .test_constants import HTTP_NOT_FOUND
from .test_constants import HTTP_UNPROCESSABLE_ENTITY
from .test_constants import MCP_FETCH_URL


class TestClaudeAIRoutingScenario:
    """Test the exact scenario that Claude.ai uses for MCP connections."""

    @pytest.mark.asyncio
    async def test_claude_ai_mcp_endpoint_discovery(
        self,
        http_client,
        wait_for_services
    ):  # noqa: ARG002
        """Test the exact flow Claude.ai uses:

        1. Try to access /mcp endpoint
        2. Get 401 with WWW-Authenticate header
        3. Should NOT get 404!
        """
        # This is what Claude.ai does - tries to POST to /mcp
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "claude-ai-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json,text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            },
            follow_redirects=False,
        , timeout=30.0)

        # CRITICAL: Should get 401, not 404!
        assert response.status_code == HTTP_UNAUTHORIZED, f"Expected 401, got {response.status_code}"

        # Should have WWW-Authenticate header for OAuth discovery
        assert "www-authenticate" in response.headers, "Missing WWW-Authenticate header"
        assert response.headers["www-authenticate"].lower() == "bearer"

        # Should get proper error response
        error = response.json()
        assert "detail" in error
        assert "error" in error["detail"]
        assert error["detail"]["error"] == "invalid_request"
        assert "Authorization header" in error["detail"]["error_description"]

    @pytest.mark.asyncio
    async def test_mcp_path_accessible_with_and_without_trailing_slash(
        self,
        http_client,
        wait_for_services
    ):  # noqa: ARG002
        """Test that /mcp works with and without trailing slash."""
        paths = ["/mcp", "/mcp/"]

        for path in paths:
            response = await http_client.post(
                f"{MCP_FETCH_URL}{path}",
                json={"jsonrpc": "2.0", "method": "ping", "id": 1},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json,text/event-stream",
                },
                follow_redirects=True,  # Allow following redirects
            , timeout=30.0)

            # Should eventually get 401 (after any redirects)
            assert response.status_code == HTTP_UNAUTHORIZED, (
                f"Path {path} returned {response.status_code}"
            )

    @pytest.mark.asyncio
    async def test_traefik_path_routing_exists(self, http_client, wait_for_services):  # noqa: ARG002
        """Test that Traefik routing includes PathPrefix rule.

        This is the test that would have caught our bug!
        """
        # Test different paths to ensure PathPrefix routing works
        test_cases = [
            {
                "path": "/mcp",
                "expected": 401,  # Should route to service and get auth error
                "description": "Base MCP path",
            },
            {
                "path": "/mcp/",
                "expected": 401,  # Should route to service and get auth error
                "description": "MCP path with trailing slash",
            },
            {
                "path": "/mcp/tools/list",
                "expected": 401,  # Should route to service and get auth error
                "description": "MCP subpath",
            },
            {
                "path": "/health",
                "expected": 401,  # Health checks should use /mcp per divine CLAUDE.md
                "description": "Health endpoint (requires auth like all non-OAuth paths)",
            },
            {
                "path": "/nonexistent",
                "expected": 401,  # Should hit auth middleware first
                "description": "Non-existent path",
            },
        ]

        for test in test_cases:
            if test["path"].startswith("/mcp"):
                # POST request for MCP endpoints
                response = await http_client.post(
                    f"{MCP_FETCH_URL}{test['path']}",
                    json={"jsonrpc": "2.0", "method": "ping", "id": 1},
                    headers={"Content-Type": "application/json"},
                    follow_redirects=True,
                , timeout=30.0)
            else:
                # GET request for other endpoints
                response = await http_client.get(
                    f"{MCP_FETCH_URL}{test['path']}", follow_redirects=True
                , timeout=30.0)

            assert response.status_code == test["expected"], (
                f"{test['description']} ({test['path']}) returned {response.status_code}, expected {test['expected']}"  # TODO: Break long line
            )

    @pytest.mark.asyncio
    async def test_base_domain_without_path_requires_auth(
        self,
        http_client,
        wait_for_services
    ):  # noqa: ARG002
        """Test that accessing base domain without path requires auth."""
        # Just accessing the base domain should trigger auth
        response = await http_client.get(MCP_FETCH_URL, timeout=30.0)
        assert response.status_code == HTTP_UNAUTHORIZED

        # Same for POST
        response = await http_client.post(
            MCP_FETCH_URL,
            json={"test": "data"},
            headers={"Content-Type": "application/json"},
        , timeout=30.0)
        assert response.status_code == HTTP_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_exact_claude_ai_error_scenario(self, http_client, wait_for_services):  # noqa: ARG002
        """Reproduce the EXACT error Claude.ai encountered.

        This test would FAIL with the old configuration!
        """
        # Simulate Claude.ai's exact request
        url = f"https://fetch.{BASE_DOMAIN}/mcp"

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                url,
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {"tools": {}},
                        "clientInfo": {"name": "claude-ai", "version": "1.0.0"},
                    },
                    "id": "init-1",
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json,text/event-stream",
                    "User-Agent": "Claude-AI/1.0",
                },
                follow_redirects=False,
                timeout=10.0,
            )

            # The bug was: this returned 404 instead of 401
            # With proper PathPrefix routing, should get 401
            assert response.status_code != 404, (
                "Got 404 - Traefik routing is not configured for /mcp path! "
                "Make sure fetch router includes PathPrefix(`/mcp`) in the rule."
            )

            assert response.status_code == HTTP_UNAUTHORIZED, (
                f"Expected 401 Unauthorized, got {response.status_code}"
            )

            # Verify it's a proper OAuth error response
            assert "www-authenticate" in response.headers
            assert response.headers["www-authenticate"].lower() == "bearer"
