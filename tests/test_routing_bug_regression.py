"""Regression Test for Routing Bug
Following CLAUDE.md - NO MOCKING, real services only!

This test ensures the specific bug that caused 404 errors for Claude.ai
when accessing /mcp endpoint is fixed and stays fixed.

Routing is handled by SWAG nginx proxy-confs, not Traefik labels.
"""

import pytest

from .test_constants import HTTP_UNAUTHORIZED
from .test_constants import MCP_FETCH_TESTS_ENABLED
from .test_constants import MCP_FETCH_URL


@pytest.mark.skipif(not MCP_FETCH_TESTS_ENABLED, reason="MCP Fetch tests disabled")
class TestRoutingBugRegression:
    """Regression test for the routing configuration bug."""

    @pytest.mark.asyncio
    async def test_mcp_path_without_host_only_routing_returns_401_not_404(
        self, http_client, _wait_for_services
    ):
        """REGRESSION TEST: Ensure /mcp path returns 401 (auth required), not 404.

        Bug: When the SWAG nginx conf only matched the root location without a
        dedicated /mcp location block, requests to /mcp returned 404.

        Fix: The nginx conf includes an explicit `location /mcp` block with
        `auth_request /_oauth_verify` so unauthenticated requests get 401.
        """
        # This is the exact request that was failing
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1},
            headers={"Content-Type": "application/json"},
            follow_redirects=False,
        )

        # CRITICAL: Must be 401 (requires auth), not 404 (not found)
        assert response.status_code == HTTP_UNAUTHORIZED, (
            f"REGRESSION: Got {response.status_code} instead of 401. "
            "The nginx `location /mcp` block or auth_request directive may be missing!"
        )

        # Verify it's an auth error, not a routing error
        assert "www-authenticate" in response.headers
        error = response.json()
        # Auth service returns OAuth 2.0 compliant errors
        assert "error" in error
        assert "Authorization header" in error.get("error_description", "")

    @pytest.mark.asyncio
    async def test_swag_nginx_conf_includes_mcp_location(self, _wait_for_services):
        """Verify the SWAG nginx template conf includes a /mcp location block with auth.

        This test would fail with the old (Traefik-based) configuration.
        SWAG uses static nginx proxy-confs instead of docker labels.
        """
        import os

        conf_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "mcp-template.subdomain.conf"
        )

        with open(conf_path) as f:
            content = f.read()

        # Check that an explicit /mcp location block is present
        assert "location /mcp" in content, (
            "REGRESSION: nginx /mcp location block missing from SWAG conf!"
        )

        # Check that auth_request is used inside the MCP location
        assert "auth_request /_oauth_verify;" in content, (
            "REGRESSION: auth_request /_oauth_verify missing from SWAG conf!"
        )

        # Verify the internal OAuth verify location is defined
        assert "location = /_oauth_verify" in content, (
            "REGRESSION: /_oauth_verify internal location missing from SWAG conf!"
        )

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
            assert response.status_code == expected_status, (
                f"{description}: Expected {expected_status}, got {response.status_code}"
            )

    @pytest.mark.asyncio
    async def test_nginx_location_specificity_correct(self, http_client, _wait_for_services):
        """Verify nginx location specificity routes /mcp correctly.

        nginx does not use numeric priorities; instead, more-specific location
        blocks take precedence.  The explicit `location /mcp` block is matched
        before the catch-all `location /` block, so unauthenticated requests
        are rejected with 401 by auth_request before reaching the MCP backend.
        """
        # The /mcp path should match `location /mcp` (explicit prefix),
        # not the catch-all `location /`
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"test": "data"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == HTTP_UNAUTHORIZED  # Auth required
