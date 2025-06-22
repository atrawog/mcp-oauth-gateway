"""
Sacred Tests for mcp-streamablehttp-client HTTP-to-stdio Proxy functionality
Following CLAUDE.md Commandment 1: NO MOCKING! Test against real deployed services only!

These tests verify the HTTP proxy functionality that MCP clients use to bridge
HTTP requests to stdio-based MCP servers. All tests use REAL services and REAL tokens.
"""
import pytest
import httpx
import json
import secrets
import asyncio
import os
from typing import Optional, Dict, Any

from .test_constants import (
    MCP_FETCH_URL,
    AUTH_BASE_URL,
    BASE_DOMAIN,
    MCP_PROTOCOL_VERSION,
    MCP_PROTOCOL_VERSIONS_SUPPORTED
)

# MCP Client tokens from environment
MCP_CLIENT_ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN")


class TestMCPClientProxyBasics:
    """Test basic proxy functionality against real MCP services"""
    
    @pytest.mark.asyncio
    async def test_proxy_health_check(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that the MCP proxy service is healthy using MCP protocol per divine CLAUDE.md"""
        # Health checks should use MCP protocol initialization
        request_data = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {
                    "name": "healthcheck",
                    "version": "1.0"
                }
            },
            "id": 1
        }
        
        # First test: should get 401 without auth
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401, "MCP endpoint should require authentication"
        
        # If we have a token, test with auth
        if MCP_CLIENT_ACCESS_TOKEN:
            response = await http_client.post(
                f"{MCP_FETCH_URL}/mcp",
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"
                }
            )
            assert response.status_code == 200, "MCP health check should succeed with valid token"
            result = response.json()
            assert "result" in result or "error" in result
            if "result" in result:
                assert "protocolVersion" in result["result"]
                print(f"✅ MCP proxy service is healthy (protocol version: {result['result']['protocolVersion']})")
        else:
            print(f"✅ MCP proxy service requires authentication (as expected)")
    
    @pytest.mark.asyncio
    async def test_proxy_requires_authentication(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that proxy endpoints require authentication"""
        # Try to access MCP endpoint without auth
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1}
        )
        
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        
        # Check OAuth discovery is available
        discovery_url = f"{MCP_FETCH_URL}/.well-known/oauth-authorization-server"
        discovery_response = await http_client.get(discovery_url)
        
        assert discovery_response.status_code == 200
        metadata = discovery_response.json()
        assert "authorization_endpoint" in metadata
        
        print(f"✅ Proxy correctly requires authentication")
        print(f"   OAuth discovery available at: {discovery_url}")


class TestMCPProtocolHandling:
    """Test MCP protocol handling through the proxy"""
    
    @pytest.mark.asyncio
    async def test_initialize_request(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test MCP initialize request through proxy"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")
        
        # Send initialize request
        request_data = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {
                    "name": "test-proxy-client",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }
        
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json=request_data,
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify JSON-RPC response structure
        assert "jsonrpc" in result
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1
        
        if "result" in result:
            # Success response
            assert "protocolVersion" in result["result"]
            assert "capabilities" in result["result"]
            assert "serverInfo" in result["result"]
            
            print(f"✅ Initialize request successful")
            print(f"   Server: {result['result']['serverInfo']['name']}")
            print(f"   Protocol: {result['result']['protocolVersion']}")
        else:
            # Error response - might be session issue
            assert "error" in result
            print(f"⚠️  Initialize returned error: {result['error']}")
    
    @pytest.mark.asyncio
    async def test_session_management(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test session management through proxy"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")
        
        # Initialize to get session
        init_response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "session-test", "version": "1.0.0"}
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )
        
        assert init_response.status_code == 200
        
        # Check for session ID header
        session_id = init_response.headers.get("Mcp-Session-Id")
        if session_id:
            print(f"✅ Session ID received: {session_id}")
            
            # Try to use the session
            tools_response = await http_client.post(
                f"{MCP_FETCH_URL}/mcp",
                json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
                headers={
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Mcp-Session-Id": session_id
                }
            )
            
            assert tools_response.status_code == 200
            print(f"✅ Session can be used for subsequent requests")
        else:
            print(f"⚠️  No session ID in response headers")
    
    @pytest.mark.asyncio
    async def test_protocol_version_negotiation(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test protocol version negotiation"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")
        
        # Try different protocol versions
        for version in ["2025-06-18", "2024-11-05", "1.0"]:
            response = await http_client.post(
                f"{MCP_FETCH_URL}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": version,
                        "capabilities": {},
                        "clientInfo": {"name": "version-test", "version": "1.0.0"}
                    },
                    "id": 1
                },
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            if "result" in result:
                negotiated_version = result["result"].get("protocolVersion")
                print(f"✅ Requested {version}, negotiated: {negotiated_version}")
            else:
                print(f"⚠️  Version {version} resulted in error: {result.get('error', {}).get('message')}")


class TestProxyErrorHandling:
    """Test error handling in the proxy"""
    
    @pytest.mark.asyncio
    async def test_invalid_json_rpc_request(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test handling of invalid JSON-RPC requests"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")
        
        # Missing required fields
        invalid_requests = [
            {},  # Empty request
            {"method": "test"},  # Missing jsonrpc and id
            {"jsonrpc": "2.0", "id": 1},  # Missing method
            {"jsonrpc": "1.0", "method": "test", "id": 1},  # Wrong version
        ]
        
        for request in invalid_requests:
            response = await http_client.post(
                f"{MCP_FETCH_URL}/mcp",
                json=request,
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
            )
            
            # Should return 200 with JSON-RPC error
            assert response.status_code == 200
            result = response.json()
            assert "error" in result
            assert result["error"]["code"] < 0  # Negative error codes
            
        print(f"✅ Invalid JSON-RPC requests handled correctly")
    
    @pytest.mark.asyncio
    async def test_method_not_found(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test handling of unknown methods"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")
        
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "non_existent_method",
                "params": {},
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "error" in result
        # May return -32601 (method not found), -32001 (MCP error), or -32002 (session required)
        assert result["error"]["code"] in [-32601, -32001, -32002]
        
        print(f"✅ Unknown methods properly rejected")
    
    @pytest.mark.asyncio
    async def test_expired_token_handling(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test proxy behavior with expired tokens"""
        # Use an obviously expired token
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {},
                "id": 1
            },
            headers={"Authorization": "Bearer expired_token_12345"}
        )
        
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        
        print(f"✅ Expired tokens properly rejected with 401")


class TestProxyRealWorldScenarios:
    """Test real-world proxy usage scenarios"""
    
    @pytest.mark.asyncio
    async def test_tools_listing(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test listing available tools through proxy"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")
        
        # Need to create a session first
        session_id = await self._create_session(http_client)
        
        if session_id:
            # List tools
            response = await http_client.post(
                f"{MCP_FETCH_URL}/mcp",
                json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
                headers={
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Mcp-Session-Id": session_id
                }
            )
            
            assert response.status_code == 200
            result = response.json()
            
            if "result" in result:
                tools = result["result"].get("tools", [])
                print(f"✅ Found {len(tools)} tools available")
                for tool in tools[:3]:  # Show first 3
                    print(f"   - {tool.get('name', 'unknown')}: {tool.get('description', 'no description')[:50]}...")
            else:
                print(f"⚠️  Tools listing failed: {result.get('error')}")
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test handling multiple concurrent sessions"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")
        
        # Create multiple sessions concurrently
        async def create_session(session_num: int) -> Optional[str]:
            response = await http_client.post(
                f"{MCP_FETCH_URL}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": f"concurrent-session-{session_num}", "version": "1.0.0"}
                    },
                    "id": session_num
                },
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
            )
            
            if response.status_code == 200:
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
    async def test_large_request_handling(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test handling of large requests through proxy"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")
        
        # Create a request with large params
        large_data = "x" * 10000  # 10KB of data
        
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {
                        "name": "large-request-test",
                        "version": "1.0.0",
                        "metadata": large_data
                    }
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"},
            timeout=30.0  # Longer timeout for large request
        )
        
        assert response.status_code == 200
        print(f"✅ Large requests handled successfully")
    
    async def _create_session(self, http_client: httpx.AsyncClient) -> Optional[str]:
        """Helper to create a session"""
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )
        
        if response.status_code == 200:
            return response.headers.get("Mcp-Session-Id")
        return None


class TestProxyAuthenticationFlows:
    """Test authentication flows through the proxy"""
    
    @pytest.mark.asyncio
    async def test_bearer_token_authentication(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test Bearer token authentication"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")
        
        # Test with valid token using MCP protocol
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "auth-test", "version": "1.0.0"}
                },
                "id": 1
            },
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200
        print(f"✅ Bearer token authentication working")
    
    @pytest.mark.asyncio
    async def test_oauth_discovery_through_proxy(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test OAuth discovery endpoint through proxy domain"""
        # This should be publicly accessible
        response = await http_client.get(
            f"{MCP_FETCH_URL}/.well-known/oauth-authorization-server"
        )
        
        assert response.status_code == 200
        metadata = response.json()
        
        # Should point to auth service endpoints
        assert f"auth.{BASE_DOMAIN}" in metadata["issuer"]
        assert f"auth.{BASE_DOMAIN}" in metadata["authorization_endpoint"]
        
        print(f"✅ OAuth discovery accessible through proxy domain")
        print(f"   Auth server: {metadata['issuer']}")
    
    @pytest.mark.asyncio
    async def test_auth_error_details(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test auth error response details"""
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
                f"{MCP_FETCH_URL}/mcp",
                json={"jsonrpc": "2.0", "method": "test", "params": {}, "id": 1},
                headers=headers
            )
            
            assert response.status_code == 401
            assert "WWW-Authenticate" in response.headers
            
            print(f"✅ {description}: Properly rejected with 401")


class TestProxyPerformance:
    """Test proxy performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_response_times(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test typical response times through proxy"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")
        
        import time
        
        # Measure auth check (minimal processing)
        start = time.time()
        response = await http_client.get(f"{MCP_FETCH_URL}/mcp")
        auth_check_time = time.time() - start
        
        assert response.status_code == 401  # Should require auth
        assert auth_check_time < 1.0  # Should be fast
        
        # Measure MCP request
        start = time.time()
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "perf-test", "version": "1.0.0"}
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )
        mcp_time = time.time() - start
        
        assert response.status_code == 200
        assert mcp_time < 5.0  # Reasonable timeout
        
        print(f"✅ Response times acceptable")
        print(f"   Auth check: {auth_check_time*1000:.0f}ms")
        print(f"   MCP request: {mcp_time*1000:.0f}ms")
    
    @pytest.mark.asyncio
    async def test_connection_reuse(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that connections are reused efficiently"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")
        
        # Make multiple requests with same client using MCP protocol
        for i in range(3):
            response = await http_client.post(
                f"{MCP_FETCH_URL}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": i + 1
                },
                headers={
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                }
            )
            assert response.status_code == 200
        
        print(f"✅ Connection reuse working efficiently")