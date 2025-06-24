"""Integration tests for the MCP Filesystem service following sacred testing commandments."""

import pytest

from .test_constants import BASE_DOMAIN
from .test_constants import GATEWAY_OAUTH_ACCESS_TOKEN
from .test_constants import TEST_HTTP_TIMEOUT
from .test_constants import HTTP_OK
from .test_constants import HTTP_UNAUTHORIZED


class TestMCPFilesystemIntegration:
    """Divine integration tests for MCP Filesystem service."""

    @pytest.mark.asyncio
    async def test_filesystem_health_check_no_auth(
        self, http_client, wait_for_services, mcp_filesystem_url
    ):
        """Test that health check endpoint requires authentication per divine CLAUDE.md."""
        # Health check must require auth per divine CLAUDE.md
        response = await http_client.get(
            f"{mcp_filesystem_url}/health", timeout=TEST_HTTP_TIMEOUT
        )

        assert response.status_code == HTTP_UNAUTHORIZED, (
            f"Health check must require authentication per divine CLAUDE.md: {response.status_code} - {response.text}"  # TODO: Break long line
        )

    @pytest.mark.asyncio
    async def test_filesystem_requires_auth(self, http_client, mcp_filesystem_url):
        """Test that MCP endpoint requires authentication."""
        # Request without auth should return 401
        response = await http_client.post(
            f"{mcp_filesystem_url}",
            json={
                "jsonrpc": "2.0",
                "method": "filesystem/list",
                "params": {"path": "/workspace"},
                "id": 1,
            },
            headers={"Content-Type": "application/json"},
            timeout=TEST_HTTP_TIMEOUT,
        )

        assert response.status_code == HTTP_UNAUTHORIZED, (
            f"Expected 401 without auth, got {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_filesystem_list_directory(self, http_client, mcp_filesystem_url):
        """Test filesystem directory listing with authentication."""
        # Use the gateway token from environment
        token = GATEWAY_OAUTH_ACCESS_TOKEN

        # List workspace directory
        response = await http_client.post(
            f"{mcp_filesystem_url}",
            json={
                "jsonrpc": "2.0",
                "method": "filesystem/list",
                "params": {"path": "/workspace"},
                "id": 1,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18",
            },
            timeout=TEST_HTTP_TIMEOUT,
        )

        assert response.status_code == HTTP_OK, (
            f"List request failed: {response.status_code} - {response.text}"
        )

        result = response.json()
        assert "result" in result or "error" in result, (
            f"Invalid response format: {result}"
        )

    @pytest.mark.asyncio
    async def test_filesystem_read_file(self, http_client, mcp_filesystem_url):
        """Test filesystem file reading with authentication."""
        # Use the gateway token from environment
        token = GATEWAY_OAUTH_ACCESS_TOKEN

        # First initialize the session
        init_response = await http_client.post(
            f"{mcp_filesystem_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "mcp-filesystem-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18",
            },
            timeout=TEST_HTTP_TIMEOUT,
        )

        assert init_response.status_code == HTTP_OK, (
            f"Initialize failed: {init_response.status_code} - {init_response.text}"
        )

        # Extract session ID if provided
        session_id = None
        if "Mcp-Session-Id" in init_response.headers:
            session_id = init_response.headers["Mcp-Session-Id"]

        # Check the initialize response
        init_result = init_response.json()
        assert "result" in init_result, (
            f"Initialize response missing result: {init_result}"
        )

        # Send initialized notification (no ID for notifications)
        initialized_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": "2025-06-18",
        }
        if session_id:
            initialized_headers["Mcp-Session-Id"] = session_id

        # Send notification without expecting a response
        await http_client.post(
            f"{mcp_filesystem_url}",
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
                # No id field for notifications
            },
            headers=initialized_headers,
            timeout=TEST_HTTP_TIMEOUT,
        )

        # Now read the test file
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": "2025-06-18",
        }
        if session_id:
            headers["Mcp-Session-Id"] = session_id

        response = await http_client.post(
            f"{mcp_filesystem_url}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "read_file",
                    "arguments": {"path": "/workspace/test.txt"},
                },
                "id": 2,
            },
            headers=headers,
            timeout=TEST_HTTP_TIMEOUT,
        )

        assert response.status_code == HTTP_OK, (
            f"Read request failed: {response.status_code} - {response.text}"
        )

        result = response.json()
        assert "result" in result or "error" in result, (
            f"Invalid response format: {result}"
        )

        # If successful, content should contain our test text
        if "result" in result:
            result_content = result["result"]
            # The result might be nested differently
            if isinstance(result_content, dict) and "content" in result_content:
                content = result_content["content"]
                if isinstance(content, list) and len(content) > 0:
                    text_content = content[0].get("text", "")
                else:
                    text_content = str(content)
                assert "MCP Filesystem service" in text_content, (
                    f"Test file content not found: {text_content}"
                )

    @pytest.mark.asyncio
    async def test_filesystem_oauth_discovery(self, http_client):
        """Test that OAuth discovery endpoint is accessible on filesystem subdomain."""
        # Use base domain for OAuth discovery, not the /mcp endpoint
        oauth_discovery_url = (
            f"https://filesystem.{BASE_DOMAIN}/.well-known/oauth-authorization-server"
        )

        # OAuth discovery should be publicly accessible
        response = await http_client.get(
            oauth_discovery_url, timeout=TEST_HTTP_TIMEOUT, follow_redirects=False
        )

        # Should either return metadata directly or redirect to auth service
        assert response.status_code in [200, 302, 307], (
            f"OAuth discovery failed: {response.status_code} - {response.text}"
        )

        if response.status_code == HTTP_OK:
            # Verify it's valid OAuth metadata
            metadata = response.json()
            assert "issuer" in metadata, "Missing issuer in OAuth metadata"
            assert "authorization_endpoint" in metadata, (
                "Missing authorization_endpoint"
            )
            assert "token_endpoint" in metadata, "Missing token_endpoint"

    @pytest.mark.asyncio
    async def test_filesystem_cors_preflight(self, http_client, mcp_filesystem_url):
        """Test CORS preflight handling for filesystem service."""
        # OPTIONS request should work without auth
        response = await http_client.options(
            f"{mcp_filesystem_url}",
            headers={
                "Origin": "https://claude.ai",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
            timeout=TEST_HTTP_TIMEOUT,
        )

        # CORS preflight should return 200 or 204
        assert response.status_code in [200, 204], (
            f"CORS preflight failed: {response.status_code}"
        )
