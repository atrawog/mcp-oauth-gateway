from .test_constants import HTTP_BAD_REQUEST
from .test_constants import HTTP_OK
from .test_fetch_speedup_utils import get_local_test_url


"""Tests for MCP protocol version support validation."""

import os

import httpx
import pytest

from tests.test_constants import BASE_DOMAIN
from tests.test_constants import GATEWAY_OAUTH_ACCESS_TOKEN


@pytest.fixture
def base_domain():
    """Base domain for tests."""
    return BASE_DOMAIN


@pytest.fixture
def valid_token():
    """Valid OAuth token for testing."""
    return GATEWAY_OAUTH_ACCESS_TOKEN


class TestMCPProtocolVersions:
    """Test MCP protocol version compliance."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        """Load protocol version from environment."""
        self.MCP_PROTOCOL_VERSION = os.getenv("MCP_PROTOCOL_VERSION", "2025-06-18")
        # For testing, we still load the supported versions to test rejection of others
        versions_str = os.getenv("MCP_PROTOCOL_VERSIONS_SUPPORTED", "2025-06-18")
        self.MCP_PROTOCOL_VERSIONS_SUPPORTED = [v.strip() for v in versions_str.split(",")]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_supported_version_in_params(self, mcp_fetchs_url, valid_token, _wait_for_services):
        """Test server's protocol version works in initialize params."""
        async with httpx.AsyncClient(verify=True) as client:
            # Test the server's protocol version
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": self.MCP_PROTOCOL_VERSION,
                        "capabilities": {},
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                },
            )

            assert response.status_code == HTTP_OK, f"Version {self.MCP_PROTOCOL_VERSION} should be supported"
            data = response.json()
            assert "result" in data
            assert data["result"]["protocolVersion"] == self.MCP_PROTOCOL_VERSION

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_supported_version_in_header(self, mcp_fetchs_url, valid_token, _wait_for_services):
        """Test server's protocol version works in MCP-Protocol-Version header."""
        async with httpx.AsyncClient(verify=True) as client:
            # Test the server's protocol version
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                    "MCP-Protocol-Version": self.MCP_PROTOCOL_VERSION,
                },
            )

            assert response.status_code == HTTP_OK, f"Version {self.MCP_PROTOCOL_VERSION} should be supported in header"
            data = response.json()
            assert "result" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_unsupported_versions_rejected(self, mcp_fetchs_url, valid_token, _wait_for_services):
        """Test unsupported versions are properly rejected."""
        unsupported_versions = [
            "2024-11-05",  # Old version
            "2025-01-01",  # Different date
            "1.0.0",  # Different format
            "latest",  # Invalid format
        ]

        async with httpx.AsyncClient(verify=True) as client:
            # Test in params
            for version in unsupported_versions:
                response = await client.post(
                    f"{mcp_fetchs_url}",
                    json={
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {"protocolVersion": version, "capabilities": {}},
                        "id": 1,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {valid_token}",
                    },
                )

                assert response.status_code == HTTP_OK, f"Version {version} should return JSON-RPC error"
                data = response.json()
                assert "error" in data
                assert data["error"]["code"] == -32602
                # Check that error mentions the server's supported version
                assert self.MCP_PROTOCOL_VERSION in data["error"]["data"], (
                    f"Error should mention supported version {self.MCP_PROTOCOL_VERSION}"  # TODO: Break long line
                )

            # Test in header
            for version in unsupported_versions:
                response = await client.post(
                    f"{mcp_fetchs_url}",
                    json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {valid_token}",
                        "MCP-Protocol-Version": version,
                    },
                )

                assert response.status_code == HTTP_BAD_REQUEST, f"Version {version} should be rejected in header"
                data = response.json()
                # Check that error mentions the server's supported version
                assert self.MCP_PROTOCOL_VERSION in data["message"], (
                    f"Error should mention supported version {self.MCP_PROTOCOL_VERSION}"  # TODO: Break long line
                )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_response_headers_include_version(self, mcp_fetchs_url, valid_token, _wait_for_services):
        """Test that responses include MCP-Protocol-Version header."""
        async with httpx.AsyncClient(verify=True) as client:
            # Test various methods
            methods = ["initialize", "tools/list", "tools/call"]

            for method in methods:
                params = {}
                if method == "initialize":
                    params = {"protocolVersion": "2025-06-18"}
                elif method == "tools/call":
                    params = {
                        "name": "fetch",
                        "arguments": {"url": get_local_test_url()},
                    }

                response = await client.post(
                    f"{mcp_fetchs_url}",
                    json={
                        "jsonrpc": "2.0",
                        "method": method,
                        "params": params,
                        "id": 1,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {valid_token}",
                    },
                )

                # Should have MCP-Protocol-Version in response
                assert "MCP-Protocol-Version" in response.headers
                assert response.headers["MCP-Protocol-Version"] == self.MCP_PROTOCOL_VERSION

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_version_negotiation(self, mcp_fetchs_url, valid_token, _wait_for_services):
        """Test protocol version negotiation behavior."""
        async with httpx.AsyncClient(verify=True) as client:
            # When client doesn't specify version, server should use default
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        # No protocolVersion specified
                        "capabilities": {}
                    },
                    "id": 1,
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                },
            )

            assert response.status_code == HTTP_OK
            data = response.json()
            # Server should respond with its supported version
            assert data["result"]["protocolVersion"] == self.MCP_PROTOCOL_VERSION

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_case_sensitivity(self, mcp_fetchs_url, valid_token, _wait_for_services):
        """Test that version checking is case-sensitive."""
        async with httpx.AsyncClient(verify=True) as client:
            # Test uppercase header name (should work)
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                    "MCP-Protocol-Version": "2025-06-18",  # Correct case
                },
            )
            assert response.status_code == HTTP_OK

            # Test lowercase header name (should also work per HTTP spec)
            response = await client.post(
                f"{mcp_fetchs_url}",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 2},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_token}",
                    "mcp-protocol-version": "2025-06-18",  # Lowercase header name
                },
            )
            assert response.status_code == HTTP_OK

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_version_in_error_responses(self, mcp_fetchs_url, valid_token, _wait_for_services):
        """Test that error responses still include protocol version header."""
        async with httpx.AsyncClient(verify=True) as client:
            # Trigger various errors
            error_requests = [
                {"jsonrpc": "2.0", "method": "unknown/method", "id": 1},
                {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    # Missing params
                    "id": 2,
                },
                {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": "unknown-tool"},
                    "id": 3,
                },
            ]

            for request in error_requests:
                response = await client.post(
                    f"{mcp_fetchs_url}",
                    json=request,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {valid_token}",
                    },
                )

                # Even error responses should include protocol version
                assert "MCP-Protocol-Version" in response.headers
                assert response.headers["MCP-Protocol-Version"] == self.MCP_PROTOCOL_VERSION
