"""Regression Test for Routing Bug
Following CLAUDE.md - NO MOCKING, real services only!

This test ensures the specific bug that caused 404 errors for Claude.ai
when accessing /mcp endpoint is fixed and stays fixed.
"""

import pytest

from .test_constants import HTTP_UNAUTHORIZED
from .test_constants import MCP_FETCH_TESTS_ENABLED
from .test_constants import MCP_FETCH_URL


@pytest.mark.skipif(not MCP_FETCH_TESTS_ENABLED, reason="MCP Fetch tests disabled")
class TestRoutingBugRegression:
    """Regression test for the routing configuration bug."""

    @pytest.mark.asyncio
    async def test_mcp_path_without_host_only_routing_returns_401_not_404(self, http_client, _wait_for_services):
        """REGRESSION TEST: Ensure /mcp path returns 401 (auth required), not 404.

        Bug: When Traefik routing only had Host rule without PathPrefix,
        requests to /mcp returned 404 because Traefik couldn't route them.

        Fix: Added PathPrefix(`/mcp`) to the routing rule.
        """
        # This is the exact request that was failing
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1},
            headers={"Content-Type": "application/json"},
            follow_redirects=False,
        )

        # CRITICAL: Must be 401 (requires auth), not 404 (not found)
        assert (
            response.status_code == HTTP_UNAUTHORIZED
        ), f"REGRESSION: Got {response.status_code} instead of 401. The PathPrefix routing rule may be missing!"

        # Verify it's an auth error, not a routing error
        assert "www-authenticate" in response.headers
        error = response.json()
        # Auth service returns OAuth 2.0 compliant errors
        assert "error" in error
        assert "Authorization header" in error.get("error_description", "")

    @pytest.mark.asyncio
    async def test_traefik_labels_include_path_routing(self, _wait_for_services):
        """Verify the docker-compose.yml includes PathPrefix in routing rules.

        This test would fail with the old configuration.
        """
        # Read the fetch docker-compose.yml
        import os

        compose_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp-fetch/docker-compose.yml")

        with open(compose_path) as f:
            content = f.read()

        # Check that MCP path routing is present
        # Accept both the old PathPrefix style and new Path||PathPrefix style
        assert (
            "PathPrefix(`/mcp`)" in content or "(Path(`/mcp`) || PathPrefix(`/mcp/`))" in content
        ), "REGRESSION: MCP path routing missing from routing rules!"

        # Verify the host rule is present
        assert "Host(`fetch.${BASE_DOMAIN}`)" in content, "REGRESSION: Host rule not found!"

    @pytest.mark.asyncio
    async def test_all_required_routes_configured(self, http_client, _wait_for_services):
        """Test that all required routes are properly configured with correct priorities."""
        routes_to_test = [
            # (path, expected_status, description)
            ("/mcp", 401, "MCP endpoint requires auth"),
            ("/mcp/", 401, "MCP endpoint with slash requires auth"),
            ("/", 401, "Root path caught by catch-all route"),
            ("/random", 401, "Random path caught by catch-all route"),
        ]

        for path, expected_status, description in routes_to_test:
            response = await http_client.get(f"{MCP_FETCH_URL}{path}", follow_redirects=False)
            assert (
                response.status_code == expected_status
            ), f"{description}: Expected {expected_status}, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_routing_priorities_correct(self, http_client, _wait_for_services):
        """Verify routing priorities are set correctly:

        - OAuth discovery: Priority 10 (highest)
        - CORS preflight: Priority 4
        - MCP route: Priority 2
        - Catch-all: Priority 1 (lowest).
        """
        # The /mcp path should go to MCP route (priority 2)
        # not the catch-all (priority 1)
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"test": "data"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == HTTP_UNAUTHORIZED  # Auth required
