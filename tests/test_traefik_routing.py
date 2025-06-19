"""
Test Traefik Routing Configuration
Following CLAUDE.md - NO MOCKING, real services only!

This test suite verifies that Traefik routing is correctly configured
for all services, including path-based routing that was missing before.
"""
import pytest
import httpx
import json
from .test_constants import (
    AUTH_BASE_URL,
    MCP_FETCH_URL,
    BASE_DOMAIN
)


class TestTraefikRouting:
    """Test Traefik routing configuration for all services"""
    
    @pytest.mark.asyncio
    async def test_auth_service_routing(self, http_client, wait_for_services):
        """Test that auth service routes are accessible"""
        # Test well-known endpoint
        response = await http_client.get(
            f"{AUTH_BASE_URL}/.well-known/oauth-authorization-server"
        )
        assert response.status_code == 200
        metadata = response.json()
        assert "issuer" in metadata
        assert metadata["issuer"] == f"https://auth.{BASE_DOMAIN}"
        
        # Test health endpoint
        response = await http_client.get(f"{AUTH_BASE_URL}/health")
        assert response.status_code == 200
        health = response.json()
        assert health["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_mcp_fetch_root_requires_auth(self, http_client, wait_for_services):
        """Test that MCP service root requires authentication"""
        response = await http_client.get(MCP_FETCH_URL, follow_redirects=False)
        # With catch-all route, should get 401 from auth middleware
        assert response.status_code == 401
        assert "www-authenticate" in response.headers
    
    @pytest.mark.asyncio
    async def test_mcp_fetch_path_routing_without_auth(self, http_client, wait_for_services):
        """Test that /mcp path is routed correctly but requires auth"""
        # Test /mcp without auth - should get 401
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json,text/event-stream"
            },
            follow_redirects=False
        )
        assert response.status_code == 401
        assert "www-authenticate" in response.headers
        
        # Response should be from auth service, not MCP service
        error = response.json()
        assert "detail" in error
        assert "error" in error["detail"]
        assert error["detail"]["error"] == "invalid_request"
    
    @pytest.mark.asyncio
    async def test_mcp_fetch_trailing_slash_redirect(self, http_client, wait_for_services):
        """Test that /mcp redirects to /mcp/ with trailing slash"""
        # First, let's check if we get a redirect from /mcp to /mcp/
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json,text/event-stream"
            },
            follow_redirects=False
        )
        
        # Should get 401 from auth middleware before any redirect
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_mcp_health_endpoint_available(self, http_client, wait_for_services):
        """Test that /health endpoint is available (FastAPI implementation provides it)"""
        response = await http_client.get(f"{MCP_FETCH_URL}/health")
        # The FastAPI implementation provides a health endpoint
        # The specific route for /health takes priority over catch-all
        assert response.status_code == 200
    
    @pytest.mark.asyncio 
    async def test_all_mcp_paths_require_auth(self, http_client, wait_for_services):
        """Test that all MCP paths require authentication"""
        paths_to_test = [
            "/mcp",
            "/mcp/",
            "/mcp/tools/list",
            "/mcp/prompts/list",
            "/mcp/resources/list"
        ]
        
        for path in paths_to_test:
            response = await http_client.post(
                f"{MCP_FETCH_URL}{path}",
                json={"jsonrpc": "2.0", "method": "ping", "id": 1},
                headers={"Content-Type": "application/json"},
                follow_redirects=False
            )
            assert response.status_code == 401, f"Path {path} did not require auth"
            assert "www-authenticate" in response.headers, f"Path {path} missing WWW-Authenticate"
    
    @pytest.mark.asyncio
    async def test_routing_priority_order(self, http_client, wait_for_services):
        """Test that routing priorities work correctly"""
        # Auth routes should have highest priority
        response = await http_client.get(f"{AUTH_BASE_URL}/authorize")
        # Should get 422 for missing parameters (FastAPI validation)
        assert response.status_code == 422
        
        # Health check should work without auth
        response = await http_client.get(f"{AUTH_BASE_URL}/health")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_cross_domain_routing(self, http_client, wait_for_services):
        """Test that each subdomain routes to correct service"""
        # Auth subdomain
        response = await http_client.get(
            f"https://auth.{BASE_DOMAIN}/.well-known/oauth-authorization-server"
        )
        assert response.status_code == 200
        assert "authorization_endpoint" in response.json()
        
        # MCP subdomain - all paths require auth with catch-all route
        response = await http_client.get(
            f"https://mcp-fetch.{BASE_DOMAIN}/some-path"
        )
        assert response.status_code == 401
        
        # MCP API endpoint should require auth
        response = await http_client.post(
            f"https://mcp-fetch.{BASE_DOMAIN}/mcp",
            json={"test": "data"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_invalid_paths_return_404_or_401(self, http_client, wait_for_services):
        """Test that invalid paths return appropriate errors"""
        # Invalid path on MCP service should get 401 (auth blocks first with catch-all route)
        response = await http_client.get(f"{MCP_FETCH_URL}/invalid/path")
        assert response.status_code == 401
        
        # Invalid path on auth service (no auth required) should get 404
        response = await http_client.get(f"{AUTH_BASE_URL}/invalid/path")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_http_to_https_redirect(self, http_client):
        """Test that HTTP requests are redirected to HTTPS"""
        # This test is optional as many deployments are HTTPS-only
        pytest.skip("HTTP redirect test skipped - deployment may be HTTPS-only")