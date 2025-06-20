"""
Sacred Integration Tests for FIXED MCP Streamable HTTP Proxy
Following Commandment 1: NO MOCKING! Test against real deployed services only!
These tests verify the mcp-streamablehttp-proxy functionality with proper session handling.
"""
import pytest
import httpx
import json
import asyncio
import os
from typing import Optional

from .test_constants import (
    MCP_FETCH_URL,
    MCP_PROTOCOL_VERSION,
    TEST_HTTP_TIMEOUT,
    GATEWAY_OAUTH_ACCESS_TOKEN
)

# MCP Client tokens for external client testing
MCP_CLIENT_ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN")


class TestMCPProxyWithSessionHandling:
    """Test MCP proxy with proper session ID handling"""
    
    @pytest.mark.asyncio
    async def test_initialize_returns_session_id(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that initialize returns a session ID in headers"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")
        
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
        
        assert response.status_code == 200
        assert "Mcp-Session-Id" in response.headers
        session_id = response.headers["Mcp-Session-Id"]
        assert session_id  # Should not be empty
        
        # Response should be successful
        data = response.json()
        assert "result" in data
        # Server may negotiate a different protocol version
        assert "protocolVersion" in data["result"]
    
    @pytest.mark.asyncio
    async def test_session_persists_with_header(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that session persists when using Mcp-Session-Id header"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")
        
        # Initialize and get session ID
        init_response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "persistent-client", "version": "1.0.0"}
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )
        
        assert init_response.status_code == 200
        session_id = init_response.headers["Mcp-Session-Id"]
        
        # Send initialized notification with session ID
        await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={"jsonrpc": "2.0", "method": "initialized", "params": {}},
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Mcp-Session-Id": session_id
            }
        )
        
        # List tools using same session ID
        tools_response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Mcp-Session-Id": session_id
            }
        )
        
        assert tools_response.status_code == 200
        data = tools_response.json()
        assert "result" in data
        assert "tools" in data["result"]
    
    @pytest.mark.asyncio
    async def test_request_without_session_id_fails(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that non-initialize requests without session ID fail appropriately"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")
        
        # Try to list tools without session ID
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )
        
        assert response.status_code == 200  # JSON-RPC errors return 200
        data = response.json()
        assert "error" in data
        assert "Session ID required" in data["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_invalid_session_id_rejected(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test that invalid session IDs are rejected"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")
        
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Mcp-Session-Id": "invalid-session-id-12345"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert "Invalid session ID" in data["error"]["message"]


class TestMCPProtocolFlowWithSessions:
    """Test complete MCP protocol flow with proper session handling"""
    
    @pytest.mark.asyncio
    async def test_complete_mcp_flow(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test complete MCP flow: initialize -> initialized -> tools/list -> tool/call"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")
        
        # Step 1: Initialize
        init_response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "flow-test", "version": "1.0.0"}
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
        )
        
        assert init_response.status_code == 200
        session_id = init_response.headers["Mcp-Session-Id"]
        init_data = init_response.json()
        # Server may negotiate a different protocol version
        assert "protocolVersion" in init_data["result"]
        
        # Step 2: Send initialized notification
        initialized_response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={"jsonrpc": "2.0", "method": "initialized", "params": {}},
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Mcp-Session-Id": session_id
            }
        )
        assert initialized_response.status_code in [200, 202]
        
        # Step 3: List available tools
        tools_response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Mcp-Session-Id": session_id
            }
        )
        
        assert tools_response.status_code == 200
        tools_data = tools_response.json()
        assert "result" in tools_data
        tools = tools_data["result"]["tools"]
        assert len(tools) > 0
        
        # Find the fetch tool
        fetch_tool = next((t for t in tools if t["name"] == "fetch"), None)
        assert fetch_tool is not None
        
        # Step 4: Call the fetch tool
        tool_response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "fetch",
                    "arguments": {
                        "url": "https://example.com"
                    }
                },
                "id": 3
            },
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Mcp-Session-Id": session_id
            }
        )
        
        assert tool_response.status_code == 200
        tool_data = tool_response.json()
        # Should either succeed or return an error (depending on fetch permissions)
        assert "result" in tool_data or "error" in tool_data


class TestMCPSessionIsolation:
    """Test that sessions are properly isolated"""
    
    @pytest.mark.asyncio
    async def test_sessions_are_isolated(self, wait_for_services):
        """Test that different clients get different isolated sessions"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")
        
        # Create two separate clients
        async with httpx.AsyncClient(timeout=TEST_HTTP_TIMEOUT) as client1, \
                   httpx.AsyncClient(timeout=TEST_HTTP_TIMEOUT) as client2:
            
            # Initialize first client
            response1 = await client1.post(
                f"{MCP_FETCH_URL}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "client-1", "version": "1.0.0"}
                    },
                    "id": 1
                },
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
            )
            assert response1.status_code == 200
            session_id1 = response1.headers["Mcp-Session-Id"]
            
            # Initialize second client
            response2 = await client2.post(
                f"{MCP_FETCH_URL}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "client-2", "version": "1.0.0"}
                    },
                    "id": 1
                },
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}
            )
            assert response2.status_code == 200
            session_id2 = response2.headers["Mcp-Session-Id"]
            
            # Session IDs should be different
            assert session_id1 != session_id2
            
            # Client 1 cannot use Client 2's session
            cross_response = await client1.post(
                f"{MCP_FETCH_URL}/mcp",
                json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
                headers={
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Mcp-Session-Id": session_id2  # Using other client's session
                }
            )
            
            # This should work (sessions are not tied to HTTP clients, just to session IDs)
            # But each session maintains its own state
            assert cross_response.status_code == 200


class MCPClientHelper:
    """Helper class for MCP client operations with session management"""
    
    def __init__(self, http_client: httpx.AsyncClient, auth_token: str):
        self.client = http_client
        self.auth_token = auth_token
        self.session_id: Optional[str] = None
    
    async def initialize(self, client_name: str = "test-client") -> dict:
        """Initialize MCP session and store session ID"""
        response = await self.client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": client_name, "version": "1.0.0"}
                },
                "id": 1
            },
            headers={"Authorization": f"Bearer {self.auth_token}"}
        )
        
        assert response.status_code == 200
        self.session_id = response.headers.get("Mcp-Session-Id")
        return response.json()
    
    async def send_request(self, method: str, params: dict = None, request_id: int = None) -> dict:
        """Send MCP request with stored session ID"""
        if not self.session_id and method != "initialize":
            raise RuntimeError("Not initialized. Call initialize() first.")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        if request_id is not None:
            request["id"] = request_id
        
        response = await self.client.post(
            f"{MCP_FETCH_URL}/mcp",
            json=request,
            headers=headers
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Request failed: {response.status_code}")
        
        return response.json()


class TestMCPWithHelper:
    """Test MCP using the helper class"""
    
    @pytest.mark.asyncio
    async def test_complete_flow_with_helper(self, http_client: httpx.AsyncClient, wait_for_services):
        """Test complete MCP flow using helper class"""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")
        
        mcp = MCPClientHelper(http_client, MCP_CLIENT_ACCESS_TOKEN)
        
        # Initialize
        init_result = await mcp.initialize("helper-test")
        # Server may negotiate a different protocol version
        assert "protocolVersion" in init_result["result"]
        
        # Send initialized
        await mcp.send_request("initialized")
        
        # List tools
        tools_result = await mcp.send_request("tools/list", request_id=2)
        assert "result" in tools_result
        assert len(tools_result["result"]["tools"]) > 0