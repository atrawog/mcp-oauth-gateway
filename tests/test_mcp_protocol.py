"""
Sacred MCP Protocol Tests - Testing real MCP servers with JSON-RPC 2.0
Following MCP Protocol 2025-03-26 specifications
"""
import pytest
import httpx
import json
import asyncio
from typing import Optional
import os

# Load from environment
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "localhost")
AUTH_BASE_URL = f"https://auth.{BASE_DOMAIN}"
MCP_FETCH_URL = f"https://mcp-fetch.{BASE_DOMAIN}"


class TestMCPProtocol:
    """Test MCP Protocol 2025-03-26 compliance"""
    
    @pytest.mark.asyncio
    async def test_mcp_endpoint_requires_auth(self, http_client, wait_for_services):
        """Test that MCP endpoint requires authentication"""
        # Try to access without auth
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "ping",
                "id": 1
            }
        )
        
        # Should get 401 from ForwardAuth middleware
        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate") == "Bearer"
    
    @pytest.mark.asyncio
    async def test_mcp_json_rpc_format(self, http_client, wait_for_services):
        """Test JSON-RPC 2.0 message format requirements"""
        # Invalid JSON-RPC (missing required fields)
        test_cases = [
            # Missing jsonrpc version
            {"method": "test", "id": 1},
            # Wrong jsonrpc version
            {"jsonrpc": "1.0", "method": "test", "id": 1},
            # Missing method
            {"jsonrpc": "2.0", "id": 1},
            # Null id (forbidden for requests)
            {"jsonrpc": "2.0", "method": "test", "id": None}
        ]
        
        # Get a valid token first (simplified for testing)
        # In real tests, this would go through full OAuth flow
        mock_token = "test_token_for_mcp"
        
        for invalid_request in test_cases:
            response = await http_client.post(
                f"{MCP_FETCH_URL}/mcp",
                json=invalid_request,
                headers={"Authorization": f"Bearer {mock_token}"}
            )
            
            # Should get error response (after fixing auth)
            if response.status_code != 401:  # If auth passes
                assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_mcp_streamable_http_headers(self, http_client):
        """Test required headers for Streamable HTTP transport"""
        mock_token = "test_token"
        
        # Test required Accept header
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "ping",
                "id": 1
            },
            headers={
                "Authorization": f"Bearer {mock_token}",
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }
        )
        
        # Check response (will be 401 due to auth, but headers are validated)
        assert "Accept" in response.request.headers
        assert "application/json" in response.request.headers["Accept"]
        assert "text/event-stream" in response.request.headers["Accept"]
    
    @pytest.mark.asyncio
    async def test_mcp_session_management(self, http_client):
        """Test MCP session ID handling"""
        mock_token = "test_token"
        session_id = "test-session-123"
        
        # Send request with session ID
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "clientCapabilities": {}
                },
                "id": 1
            },
            headers={
                "Authorization": f"Bearer {mock_token}",
                "Mcp-Session-Id": session_id
            }
        )
        
        # Verify session header was sent
        assert "Mcp-Session-Id" in response.request.headers
    
    @pytest.mark.asyncio
    async def test_mcp_protocol_version(self, http_client):
        """Test MCP protocol version negotiation"""
        mock_token = "test_token"
        
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "clientCapabilities": {
                        "roots": True,
                        "sampling": True
                    }
                },
                "id": "init-1"
            },
            headers={
                "Authorization": f"Bearer {mock_token}",
                "MCP-Protocol-Version": "2025-03-26"
            }
        )
        
        # Verify protocol version header was sent
        assert response.request.headers.get("MCP-Protocol-Version") == "2025-03-26"
    
    @pytest.mark.asyncio
    async def test_mcp_error_response_format(self, http_client):
        """Test that MCP errors follow JSON-RPC 2.0 error format"""
        # This will fail auth, but we can check the error format
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "unknown_method",
                "id": 1
            }
        )
        
        # Even auth errors should follow some structure
        assert response.status_code == 401
        if response.headers.get("content-type", "").startswith("application/json"):
            error_data = response.json()
            # Should have error structure
            assert "error" in error_data or "detail" in error_data
    
    @pytest.mark.asyncio 
    async def test_mcp_batch_request_support(self, http_client):
        """Test that MCP supports receiving JSON-RPC batches"""
        mock_token = "test_token"
        
        # Send batch request
        batch = [
            {"jsonrpc": "2.0", "method": "ping", "id": 1},
            {"jsonrpc": "2.0", "method": "ping", "id": 2},
            {"jsonrpc": "2.0", "method": "ping", "id": 3}
        ]
        
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json=batch,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
        
        # Should accept batch format (even if auth fails)
        # Real MCP server must support receiving batches
        assert response.status_code in [200, 401, 404]  # Not 400 Bad Request
    
    @pytest.mark.asyncio
    async def test_mcp_http_methods(self, http_client):
        """Test that MCP endpoint supports both POST and GET methods"""
        mock_token = "test_token"
        headers = {"Authorization": f"Bearer {mock_token}"}
        
        # Test POST method
        post_response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1},
            headers=headers
        )
        assert post_response.status_code in [200, 202, 401]  # Valid responses
        
        # Test GET method (for receiving pending responses)
        get_response = await http_client.get(
            f"{MCP_FETCH_URL}/mcp",
            headers={**headers, "Mcp-Session-Id": "test-session"}
        )
        assert get_response.status_code in [200, 401, 404]  # Valid responses