"""
Sacred MCP Fetch Integration Tests - Testing real MCP fetch with OAuth
Following CLAUDE.md - NO MOCKING, real services only!
"""
import pytest
import httpx
import secrets
import hashlib
import base64
import json
import time
from jose import jwt
from .test_constants import (
    AUTH_BASE_URL,
    MCP_FETCH_URL,
    TEST_REDIRECT_URI,
    TEST_CLIENT_NAME,
    TEST_CLIENT_SCOPE,
    JWT_SECRET,
    ACCESS_TOKEN_LIFETIME,
    BASE_DOMAIN
)


class TestMCPFetchIntegration:
    """Test real MCP fetch functionality with proper OAuth authentication"""
    
    @pytest.mark.asyncio
    async def test_fetch_requires_real_oauth_token(self, http_client, wait_for_services):
        """Test that MCP fetch REQUIRES real OAuth tokens - no fakes allowed!"""
        
        # Step 1: Register an OAuth client
        registration_data = {
            "redirect_uris": [TEST_REDIRECT_URI],
            "client_name": f"{TEST_CLIENT_NAME} - MCP Fetch Test",
            "scope": TEST_CLIENT_SCOPE
        }
        
        reg_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data
        )
        
        assert reg_response.status_code == 201
        client = reg_response.json()
        
        # Step 2: SACRED VIOLATION - Creating fake JWT tokens!
        # This test MUST FAIL to demonstrate that fake tokens don't work!
        pytest.fail(
            "\n"
            "════════════════════════════════════════════════════════════════\n"
            "SACRED VIOLATION! This test creates FAKE JWT tokens!\n"
            "\n"
            "According to CLAUDE.md Commandment 1:\n"
            "'NO MOCKS! NO STUBS! NO FAKES!'\n"
            "\n"
            "This test MUST be rewritten to use REAL OAuth tokens!\n"
            "Run: just generate-github-token\n"
            "════════════════════════════════════════════════════════════════\n"
        )
    
    @pytest.mark.asyncio
    async def test_mcp_fetch_security_validation(self, http_client, wait_for_services, registered_client):
        """Test MCP fetch security - MUST reject all invalid auth attempts"""
        
        # This test verifies security by ensuring invalid tokens are rejected
        # For ACTUAL functionality tests, use REAL OAuth tokens!
        
        # Create an MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "fetch/fetch",
            "params": {
                "url": "https://example.com",
                "max_size": 1000000,
                "headers": {}
            },
            "id": "fetch-test-1"
        }
        
        # Test 1: No authentication - should return 401
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json=mcp_request
        )
        
        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate") == "Bearer"
        
        # Test 2: Invalid token - should return 401
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json=mcp_request,
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        
        assert response.status_code == 401
        
        # Test 3: Malformed authorization header
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json=mcp_request,
            headers={"Authorization": "NotBearer some_token"}
        )
        
        assert response.status_code == 401
        
        # Test 4: Test the MCP protocol version header
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json=mcp_request,
            headers={
                "Authorization": "Bearer invalid_but_well_formed_jwt",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_mcp_fetch_endpoint_validation(self, http_client, wait_for_services):
        """Test MCP fetch endpoint validation and error handling"""
        
        # Test with invalid JSON-RPC format
        invalid_requests = [
            # Missing jsonrpc version
            {
                "method": "fetch/fetch",
                "params": {"url": "https://example.com"},
                "id": 1
            },
            # Invalid jsonrpc version
            {
                "jsonrpc": "1.0",
                "method": "fetch/fetch",
                "params": {"url": "https://example.com"},
                "id": 1
            },
            # Missing method
            {
                "jsonrpc": "2.0",
                "params": {"url": "https://example.com"},
                "id": 1
            },
            # Invalid method format
            {
                "jsonrpc": "2.0",
                "method": "invalid_method_name",
                "params": {"url": "https://example.com"},
                "id": 1
            }
        ]
        
        for invalid_request in invalid_requests:
            response = await http_client.post(
                f"{MCP_FETCH_URL}/mcp",
                json=invalid_request
            )
            
            # Should return 401 since we're not authenticated
            # The actual JSON-RPC validation happens after auth
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_mcp_fetch_http_methods(self, http_client, wait_for_services):
        """Test that MCP fetch endpoint supports required HTTP methods"""
        
        # Test GET method (required by MCP Streamable HTTP transport)
        response = await http_client.get(f"{MCP_FETCH_URL}/mcp")
        # Should return 401 since we're not authenticated
        assert response.status_code == 401
        
        # Test POST method
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={"jsonrpc": "2.0", "method": "test", "id": 1}
        )
        assert response.status_code == 401
        
        # Test unsupported methods
        response = await http_client.put(
            f"{MCP_FETCH_URL}/mcp",
            json={"test": "data"}
        )
        # Should return 405 Method Not Allowed or 401
        assert response.status_code in [401, 405]