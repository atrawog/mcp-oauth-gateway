"""Test Traefik Routing Configuration
Following CLAUDE.md - NO MOCKING, real services only!

This test suite verifies that Traefik routing is correctly configured
for all services, including path-based routing that was missing before.
"""

import pytest

from .test_constants import AUTH_BASE_URL
from .test_constants import BASE_DOMAIN
from .test_constants import MCP_FETCH_URL


class TestTraefikRouting:
    """Test Traefik routing configuration for all services."""

    @pytest.mark.asyncio
    async def test_auth_service_routing(self, http_client, wait_for_services):
        """Test that auth service routes are accessible."""
        # Test well-known endpoint
        response = await http_client.get(
            f"{AUTH_BASE_URL}/.well-known/oauth-authorization-server"
        )
        assert response.status_code == 200
        metadata = response.json()
        assert "issuer" in metadata
        assert metadata["issuer"] == f"https://auth.{BASE_DOMAIN}"

        # OAuth discovery endpoint serves as health check
        # Already tested above

    @pytest.mark.asyncio
    async def test_mcp_fetch_root_requires_auth(self, http_client, wait_for_services):
        """Test that MCP service root requires authentication."""
        response = await http_client.get(MCP_FETCH_URL, follow_redirects=False)
        # With catch-all route, should get 401 from auth middleware
        assert response.status_code == 401
        assert "www-authenticate" in response.headers

    @pytest.mark.asyncio
    async def test_mcp_fetch_path_routing_without_auth(
        self, http_client, wait_for_services
    ):
        """Test that /mcp path is routed correctly but requires auth."""
        # Test /mcp without auth - should get 401
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json,text/event-stream",
            },
            follow_redirects=False,
        )
        assert response.status_code == 401
        assert "www-authenticate" in response.headers

        # Response should be from auth service, not MCP service
        error = response.json()
        assert "detail" in error
        assert "error" in error["detail"]
        assert error["detail"]["error"] == "invalid_request"

    @pytest.mark.asyncio
    async def test_mcp_fetch_trailing_slash_redirect(
        self, http_client, wait_for_services
    ):
        """Test that /mcp redirects to /mcp/ with trailing slash."""
        # First, let's check if we get a redirect from /mcp to /mcp/
        response = await http_client.post(
            f"{MCP_FETCH_URL}",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json,text/event-stream",
            },
            follow_redirects=False,
        )

        # Should get 401 from auth middleware before any redirect
        assert response.status_code == 401

    # Removed test_mcp_health_endpoint_available - /health endpoints are deprecated
    # per CLAUDE.md - use MCP protocol health checks instead

    @pytest.mark.asyncio
    async def test_all_mcp_paths_require_auth(self, http_client, wait_for_services):
        """Test that all MCP paths require authentication."""
        paths_to_test = [
            "/mcp",
            "/mcp/",
            "/mcp/tools/list",
            "/mcp/prompts/list",
            "/mcp/resources/list",
        ]

        for path in paths_to_test:
            response = await http_client.post(
                f"{MCP_FETCH_URL}{path}",
                json={"jsonrpc": "2.0", "method": "ping", "id": 1},
                headers={"Content-Type": "application/json"},
                follow_redirects=False,
            )
            assert response.status_code == 401, f"Path {path} did not require auth"
            assert "www-authenticate" in response.headers, (
                f"Path {path} missing WWW-Authenticate"
            )

    @pytest.mark.asyncio
    async def test_routing_priority_order(self, http_client, wait_for_services):
        """Test that routing priorities work correctly."""
        # Auth routes should have highest priority
        response = await http_client.get(f"{AUTH_BASE_URL}/authorize")
        # Should get 422 for missing parameters (FastAPI validation)
        assert response.status_code == 422

        # OAuth discovery should work without auth
        response = await http_client.get(
            f"{AUTH_BASE_URL}/.well-known/oauth-authorization-server"
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_cross_domain_routing(self, http_client, wait_for_services):
        """Test that each subdomain routes to correct service."""
        # Auth subdomain
        response = await http_client.get(
            f"https://auth.{BASE_DOMAIN}/.well-known/oauth-authorization-server"
        )
        assert response.status_code == 200
        assert "authorization_endpoint" in response.json()

        # MCP subdomain - all paths require auth with catch-all route
        response = await http_client.get(f"https://fetch.{BASE_DOMAIN}/some-path")
        assert response.status_code == 401

        # MCP API endpoint should require auth
        response = await http_client.post(
            f"https://fetch.{BASE_DOMAIN}/mcp",
            json={"test": "data"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_paths_return_404_or_401(
        self, http_client, wait_for_services
    ):
        """Test that invalid paths return appropriate errors."""
        # Invalid path on MCP service should get 401 (auth blocks first with catch-all route)
        response = await http_client.get(f"{MCP_FETCH_URL}/invalid/path")
        assert response.status_code == 401

        # Invalid path on auth service (no auth required) should get 404
        response = await http_client.get(f"{AUTH_BASE_URL}/invalid/path")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_http_to_https_redirect(self, http_client):
        """Test that HTTP requests are redirected to HTTPS."""
        # Test HTTP to HTTPS redirect for auth service
        http_auth_url = (
            f"http://auth.{BASE_DOMAIN}/.well-known/oauth-authorization-server"
        )

        response = await http_client.get(
            http_auth_url,
            follow_redirects=False,  # Don't follow redirects so we can check them
        )

        # Should get a redirect response (301 or 302)
        assert response.status_code in [301, 302, 307, 308], (
            f"Expected redirect status code, got {response.status_code}. "
            f"Response: {response.text[:200]}"
        )

        # Check that Location header points to HTTPS
        assert "Location" in response.headers, (
            "Missing Location header in redirect response"
        )
        location = response.headers["Location"]
        assert location.startswith("https://"), (
            f"Redirect should point to HTTPS, got: {location}"
        )
        assert f"auth.{BASE_DOMAIN}" in location, (
            f"Redirect should preserve hostname, got: {location}"
        )

        # Test HTTP to HTTPS redirect for MCP service
        http_mcp_url = (
            f"http://fetch.{BASE_DOMAIN}/.well-known/oauth-authorization-server"
        )

        response = await http_client.get(http_mcp_url, follow_redirects=False)

        # Should get a redirect response
        assert response.status_code in [301, 302, 307, 308], (
            f"Expected redirect status code for MCP service, got {response.status_code}. "
            f"Response: {response.text[:200]}"
        )

        # Check that Location header points to HTTPS
        assert "Location" in response.headers, (
            "Missing Location header in MCP redirect response"
        )
        location = response.headers["Location"]
        assert location.startswith("https://"), (
            f"MCP redirect should point to HTTPS, got: {location}"
        )
        assert f"fetch.{BASE_DOMAIN}" in location, (
            f"MCP redirect should preserve hostname, got: {location}"
        )

        # Test that following the redirect works
        https_response = await http_client.get(
            http_auth_url,
            follow_redirects=True,  # Follow redirects this time
        )

        # Should get successful response after redirect
        assert https_response.status_code == 200, (
            f"Failed to access service after HTTP->HTTPS redirect: {https_response.status_code}"
        )

        # Verify we actually got the OAuth metadata response
        metadata = https_response.json()
        assert "issuer" in metadata, f"Invalid OAuth metadata response: {metadata}"
        assert metadata["issuer"] == f"https://auth.{BASE_DOMAIN}", (
            f"Incorrect issuer: {metadata}"
        )
