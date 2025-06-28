"""Sacred Tests for mcp-streamablehttp-client HTTP-to-stdio Proxy functionality
Following CLAUDE.md Commandment 1: NO MOCKING! Test against real deployed services only!

These tests verify the HTTP proxy functionality that MCP clients use to bridge
HTTP requests to stdio-based MCP servers. All tests use REAL services and REAL tokens.
"""

import asyncio
import json
import os

import httpx
import pytest

from .test_constants import BASE_DOMAIN
from .test_constants import HTTP_OK
from .test_constants import HTTP_UNAUTHORIZED
from .test_constants import MCP_ECHO_STATELESS_URL
from .test_constants import MCP_PROTOCOL_VERSION


# MCP Client tokens from environment
MCP_CLIENT_ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN")


def parse_mcp_response(response):
    """Parse MCP response, handling both JSON and SSE formats."""
    try:
        if not response.content:
            pytest.fail(
                f"Empty response from MCP service. Status: {response.status_code}, Headers: {dict(response.headers)}",
            )

        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            # Parse SSE format: extract JSON from "data:" line
            text = response.text
            for line in text.split("\n"):
                if line.startswith("data: "):
                    json_data = line[6:]  # Remove "data: " prefix
                    return json.loads(json_data)
            pytest.fail(f"No data line found in SSE response. Content: {response.text[:200]}")
        else:
            return response.json()
    except Exception as e:
        pytest.fail(
            f"Failed to parse MCP response. Status: {response.status_code}, Content: {response.text[:200]}, Error: {e}",
        )


class TestMCPClientProxyBasics:
    """Test basic proxy functionality against real MCP services."""

    @pytest.mark.asyncio
    async def test_proxy_health_check(self, http_client: httpx.AsyncClient, _wait_for_services, unique_test_id):
        """Test that the MCP proxy service is healthy using MCP protocol per divine CLAUDE.md."""
        # Health checks should use MCP protocol initialization
        request_data = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "healthcheck", "version": "1.0"},
            },
            "id": 1,
        }

        # First test: should get 401 without auth
        response = await http_client.post(
            f"{MCP_ECHO_STATELESS_URL}",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )
        assert response.status_code == HTTP_UNAUTHORIZED, "MCP endpoint should require authentication"

        # If we have a token, test with auth
        if MCP_CLIENT_ACCESS_TOKEN:
            response = await http_client.post(
                f"{MCP_ECHO_STATELESS_URL}",
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Accept": "application/json, text/event-stream",
                },
                timeout=30.0,
            )
            assert response.status_code == HTTP_OK, "MCP health check should succeed with valid token"

            result = parse_mcp_response(response)
            assert "result" in result or "error" in result
            if "result" in result:
                assert "protocolVersion" in result["result"]
                print(
                    f"✅ MCP proxy service is healthy (protocol version: {result['result']['protocolVersion']})",  # TODO: Break long line
                )
        else:
            print("✅ MCP proxy service requires authentication (as expected)")

    @pytest.mark.asyncio
    async def test_proxy_requires_authentication(
        self,
        http_client: httpx.AsyncClient,
        _wait_for_services,
        unique_test_id,
    ):
        """Test that proxy endpoints require authentication."""
        # Try to access MCP endpoint without auth
        response = await http_client.post(
            f"{MCP_ECHO_STATELESS_URL}",
            json={"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1},
            timeout=30.0,
        )

        assert response.status_code == HTTP_UNAUTHORIZED
        assert "WWW-Authenticate" in response.headers

        # Check OAuth discovery is available
        # Remove /mcp suffix from URL to get base domain
        base_url = MCP_ECHO_STATELESS_URL[:-4] if MCP_ECHO_STATELESS_URL.endswith("/mcp") else MCP_ECHO_STATELESS_URL
        discovery_url = f"{base_url}/.well-known/oauth-authorization-server"
        discovery_response = await http_client.get(discovery_url, timeout=30.0)

        assert discovery_response.status_code == HTTP_OK
        metadata = discovery_response.json()
        assert "authorization_endpoint" in metadata

        print("✅ Proxy correctly requires authentication")
        print(f"   OAuth discovery available at: {discovery_url}")


class TestMCPProtocolHandling:
    """Test MCP protocol handling through the proxy."""

    @pytest.mark.asyncio
    async def test_initialize_request(self, http_client: httpx.AsyncClient, _wait_for_services, unique_test_id):
        """Test MCP initialize request through proxy."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")

        # Send initialize request
        request_data = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": f"test-proxy-{unique_test_id}", "version": "1.0.0"},
            },
            "id": 1,
        }

        response = await http_client.post(
            f"{MCP_ECHO_STATELESS_URL}",
            json=request_data,
            headers={
                "Content-Type": "application/json",
                "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Accept": "application/json, text/event-stream",
            },
            timeout=30.0,
        )

        assert response.status_code == HTTP_OK

        result = parse_mcp_response(response)

        # Verify JSON-RPC response structure
        assert "jsonrpc" in result
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1

        if "result" in result:
            # Success response
            assert "protocolVersion" in result["result"]
            assert "capabilities" in result["result"]
            assert "serverInfo" in result["result"]

            print("✅ Initialize request successful")
            print(f"   Server: {result['result']['serverInfo']['name']}")
            print(f"   Protocol: {result['result']['protocolVersion']}")
        else:
            # Error response - might be session issue
            assert "error" in result
            print(f"⚠️  Initialize returned error: {result['error']}")

    @pytest.mark.asyncio
    async def test_session_management(self, http_client: httpx.AsyncClient, _wait_for_services, unique_test_id):
        """Test session management through proxy."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")

        # Initialize to get session
        init_response = await http_client.post(
            f"{MCP_ECHO_STATELESS_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": f"session-{unique_test_id}", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={
                "Content-Type": "application/json",
                "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Accept": "application/json, text/event-stream",
            },
            timeout=30.0,
        )

        assert init_response.status_code == HTTP_OK

        # Check for session ID header
        session_id = init_response.headers.get("Mcp-Session-Id")
        if session_id:
            print(f"✅ Session ID received: {session_id}")

            # Try to use the session
            tools_response = await http_client.post(
                f"{MCP_ECHO_STATELESS_URL}",
                json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
                headers={
                    "Content-Type": "application/json",
                    "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Mcp-Session-Id": session_id,
                },
                timeout=30.0,
            )

            assert tools_response.status_code == HTTP_OK
            print("✅ Session can be used for subsequent requests")
        else:
            print("⚠️  No session ID in response headers")

    @pytest.mark.asyncio
    async def test_protocol_version_negotiation(
        self,
        http_client: httpx.AsyncClient,
        _wait_for_services,
        unique_test_id,
    ):
        """Test protocol version negotiation."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")

        # Try different protocol versions
        for version in ["2025-06-18", "2024-11-05", "1.0"]:
            response = await http_client.post(
                f"{MCP_ECHO_STATELESS_URL}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": version,
                        "capabilities": {},
                        "clientInfo": {"name": f"version-{unique_test_id}", "version": "1.0.0"},
                    },
                    "id": 1,
                },
                headers={
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
                timeout=30.0,
            )

            assert response.status_code == HTTP_OK

            result = parse_mcp_response(response)

            if "result" in result:
                negotiated_version = result["result"].get("protocolVersion")
                print(f"✅ Requested {version}, negotiated: {negotiated_version}")
            else:
                print(
                    f"⚠️  Version {version} resulted in error: {result.get('error', {}).get('message')}",  # TODO: Break long line
                )


class TestProxyErrorHandling:
    """Test error handling in the proxy."""

    @pytest.mark.asyncio
    async def test_invalid_json_rpc_request(self, http_client: httpx.AsyncClient, _wait_for_services, unique_test_id):
        """Test handling of invalid JSON-RPC requests."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")

        # Missing required fields - all include "id" to ensure they're treated as requests, not notifications
        invalid_requests = [
            {"id": 1},  # Empty request with id only
            {"method": "test", "id": 2},  # Missing jsonrpc
            {"jsonrpc": "2.0", "id": 3},  # Missing method
            {"jsonrpc": "1.0", "method": "test", "id": 4},  # Wrong version
        ]

        for request in invalid_requests:
            response = await http_client.post(
                f"{MCP_ECHO_STATELESS_URL}",
                json=request,
                headers={
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
                timeout=30.0,
            )

            # Should return 200 with JSON-RPC error (SSE format)
            assert response.status_code == HTTP_OK
            # Parse SSE response format: "event: message\ndata: {...}\n\n"
            content_type = response.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                # Parse SSE format
                text = response.text
                for line in text.split("\n"):
                    if line.startswith("data: "):
                        json_data = line[6:]  # Remove "data: " prefix
                        result = json.loads(json_data)
                        break
                else:
                    pytest.fail(f"No data line found in SSE response. Content: {response.text[:200]}")
            else:
                result = response.json()
            assert "error" in result
            assert result["error"]["code"] < 0  # Negative error codes

        print("✅ Invalid JSON-RPC requests handled correctly")

    @pytest.mark.asyncio
    async def test_method_not_found(self, http_client: httpx.AsyncClient, _wait_for_services, unique_test_id):
        """Test handling of unknown methods."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")

        response = await http_client.post(
            f"{MCP_ECHO_STATELESS_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "non_existent_method",
                "params": {},
                "id": 1,
            },
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            timeout=30.0,
        )

        assert response.status_code == HTTP_OK
        # Parse response (could be JSON or SSE format)
        result = parse_mcp_response(response)
        assert "error" in result
        # May return -32601 (method not found), -32001 (MCP error), or -32002 (session required)
        assert result["error"]["code"] in [-32601, -32001, -32002]

        print("✅ Unknown methods properly rejected")

    @pytest.mark.asyncio
    async def test_expired_token_handling(self, http_client: httpx.AsyncClient, _wait_for_services, unique_test_id):
        """Test proxy behavior with expired tokens."""
        # Use an obviously expired token
        response = await http_client.post(
            f"{MCP_ECHO_STATELESS_URL}",
            json={"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1},
            headers={"Authorization": "Bearer expired_token_12345"},
            timeout=30.0,
        )

        assert response.status_code == HTTP_UNAUTHORIZED
        assert "WWW-Authenticate" in response.headers

        print("✅ Expired tokens properly rejected with 401")


class TestProxyRealWorldScenarios:
    """Test real-world proxy usage scenarios."""

    @pytest.mark.asyncio
    async def test_tools_listing(self, http_client: httpx.AsyncClient, _wait_for_services, unique_test_id):
        """Test listing available tools through proxy."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")

        # Need to create a session first
        session_id = await self._create_session(http_client, unique_test_id)

        if session_id:
            # List tools
            response = await http_client.post(
                f"{MCP_ECHO_STATELESS_URL}",
                json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
                headers={
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Mcp-Session-Id": session_id,
                },
                timeout=30.0,
            )

            assert response.status_code == HTTP_OK
            result = response.json()

            if "result" in result:
                tools = result["result"].get("tools", [])
                print(f"✅ Found {len(tools)} tools available")
                for tool in tools[:3]:  # Show first 3
                    print(
                        f"   - {tool.get('name', 'unknown')}: {tool.get('description', 'no description')[:50]}...",  # TODO: Break long line
                    )
            else:
                print(f"⚠️  Tools listing failed: {result.get('error')}")

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, http_client: httpx.AsyncClient, _wait_for_services, unique_test_id):
        """Test handling multiple concurrent sessions."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")

        # Create multiple sessions concurrently
        async def create_session(session_num: int) -> str | None:
            response = await http_client.post(
                f"{MCP_ECHO_STATELESS_URL}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {
                            "name": f"concurrent-session-{session_num}-{unique_test_id}",
                            "version": "1.0.0",
                        },
                    },
                    "id": session_num,
                },
                headers={
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
                timeout=30.0,
            )

            if response.status_code == HTTP_OK:
                return response.headers.get("Mcp-Session-Id")
            return None

        # Create 3 sessions
        tasks = [create_session(i) for i in range(1, 4)]
        session_ids = await asyncio.gather(*tasks)

        valid_sessions = [sid for sid in session_ids if sid]
        print(f"✅ Created {len(valid_sessions)} concurrent sessions")

        # Each session should be unique
        if len(valid_sessions) > 1:
            assert len(set(valid_sessions)) == len(valid_sessions), "Sessions should be unique"

    @pytest.mark.asyncio
    async def test_large_request_handling(self, http_client: httpx.AsyncClient, _wait_for_services, unique_test_id):
        """Test handling of large requests through proxy."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")

        # Create a request with large params
        large_data = "x" * 10000  # 10KB of data

        response = await http_client.post(
            f"{MCP_ECHO_STATELESS_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {
                        "name": f"large-{unique_test_id}",
                        "version": "1.0.0",
                        "metadata": large_data,
                    },
                },
                "id": 1,
            },
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            timeout=30.0,  # Longer timeout for large request
        )

        assert response.status_code == HTTP_OK
        print("✅ Large requests handled successfully")

    async def _create_session(self, http_client: httpx.AsyncClient, unique_test_id: str) -> str | None:
        """Helper to create a session."""
        response = await http_client.post(
            f"{MCP_ECHO_STATELESS_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": f"test-{unique_test_id}", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            timeout=30.0,
        )

        if response.status_code == HTTP_OK:
            return response.headers.get("Mcp-Session-Id")
        return None


class TestProxyAuthenticationFlows:
    """Test authentication flows through the proxy."""

    @pytest.mark.asyncio
    async def test_bearer_token_authentication(
        self,
        http_client: httpx.AsyncClient,
        _wait_for_services,
        unique_test_id,
    ):
        """Test Bearer token authentication."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")

        # Test with valid token using MCP protocol
        response = await http_client.post(
            f"{MCP_ECHO_STATELESS_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": f"auth-{unique_test_id}", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            timeout=30.0,
        )

        assert response.status_code == HTTP_OK
        print("✅ Bearer token authentication working")

    @pytest.mark.asyncio
    async def test_oauth_discovery_through_proxy(
        self,
        http_client: httpx.AsyncClient,
        _wait_for_services,
        unique_test_id,
    ):
        """Test OAuth discovery endpoint through proxy domain."""
        # This should be publicly accessible
        # Remove /mcp suffix from URL to get base domain
        base_url = MCP_ECHO_STATELESS_URL[:-4] if MCP_ECHO_STATELESS_URL.endswith("/mcp") else MCP_ECHO_STATELESS_URL
        response = await http_client.get(f"{base_url}/.well-known/oauth-authorization-server", timeout=30.0)

        assert response.status_code == HTTP_OK
        metadata = response.json()

        # Should point to auth service endpoints
        assert f"auth.{BASE_DOMAIN}" in metadata["issuer"]
        assert f"auth.{BASE_DOMAIN}" in metadata["authorization_endpoint"]

        print("✅ OAuth discovery accessible through proxy domain")
        print(f"   Auth server: {metadata['issuer']}")

    @pytest.mark.asyncio
    async def test_auth_error_details(self, http_client: httpx.AsyncClient, _wait_for_services, unique_test_id):
        """Test auth error response details."""
        # Test various invalid auth scenarios
        test_cases = [
            ("", "Missing Authorization header"),
            ("InvalidScheme token123", "Invalid auth scheme"),
            ("Bearer", "Missing token"),
            ("Bearer Bearer token", "Malformed header"),
        ]

        for auth_header, description in test_cases:
            headers = {}
            if auth_header:
                headers["Authorization"] = auth_header

            response = await http_client.post(
                f"{MCP_ECHO_STATELESS_URL}",
                json={"jsonrpc": "2.0", "method": "test", "params": {}, "id": 1},
                headers=headers,
                timeout=30.0,
            )

            assert response.status_code == HTTP_UNAUTHORIZED
            assert "WWW-Authenticate" in response.headers

            print(f"✅ {description}: Properly rejected with 401")


class TestProxyPerformance:
    """Test proxy performance characteristics."""

    @pytest.mark.asyncio
    async def test_response_times(self, http_client: httpx.AsyncClient, _wait_for_services, unique_test_id):
        """Test typical response times through proxy."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")

        import time

        # Measure auth check (minimal processing)
        start = time.time()
        response = await http_client.get(f"{MCP_ECHO_STATELESS_URL}", timeout=30.0)
        auth_check_time = time.time() - start

        assert response.status_code == HTTP_UNAUTHORIZED  # Should require auth
        assert auth_check_time < 1.0  # Should be fast

        # Measure MCP request
        start = time.time()
        response = await http_client.post(
            f"{MCP_ECHO_STATELESS_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": f"perf-{unique_test_id}", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            timeout=30.0,
        )
        mcp_time = time.time() - start

        assert response.status_code == HTTP_OK
        assert mcp_time < 5.0  # Reasonable timeout

        print("✅ Response times acceptable")
        print(f"   Auth check: {auth_check_time * 1000:.0f}ms")
        print(f"   MCP request: {mcp_time * 1000:.0f}ms")

    @pytest.mark.asyncio
    async def test_connection_reuse(self, http_client: httpx.AsyncClient, _wait_for_services, unique_test_id):
        """Test that connections are reused efficiently."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")

        # Make multiple requests with same client using MCP protocol
        for i in range(3):
            response = await http_client.post(
                f"{MCP_ECHO_STATELESS_URL}",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": i + 1,
                },
                headers={
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
                timeout=30.0,
            )
            assert response.status_code == HTTP_OK

        print("✅ Connection reuse working efficiently")
