"""
Test MCP Fetch with real content - Following CLAUDE.md
This test attempts to create a valid token and fetch real content
"""
import pytest
import httpx
import secrets
import hashlib
import base64
import json
import time
from jose import jwt
import redis.asyncio as redis
from .test_constants import (
    AUTH_BASE_URL,
    MCP_FETCH_URL,
    TEST_REDIRECT_URI,
    TEST_CLIENT_NAME,
    TEST_CLIENT_SCOPE,
    JWT_SECRET,
    ACCESS_TOKEN_LIFETIME,
    BASE_DOMAIN,
    REDIS_URL
)


class TestMCPFetchRealContent:
    """Test fetching real content through MCP with proper authentication"""
    
    @pytest.mark.asyncio
    async def test_fetch_example_com_content(self, http_client, wait_for_services):
        """Attempt to fetch https://example.com and check for 'Example Domain' text"""
        
        # Step 1: Register an OAuth client
        registration_data = {
            "redirect_uris": [TEST_REDIRECT_URI],
            "client_name": f"{TEST_CLIENT_NAME} - Example.com Fetch",
            "scope": TEST_CLIENT_SCOPE
        }
        
        reg_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data
        )
        
        assert reg_response.status_code == 201
        client = reg_response.json()
        
        # Step 2: SACRED VIOLATION DETECTED!
        # This test is manipulating Redis directly to fake authentication!
        
        pytest.fail(
            "\n"
            "════════════════════════════════════════════════════════════════\n"
            "SACRED VIOLATION! This test manipulates Redis to fake auth!\n"
            "\n"
            "According to CLAUDE.md:\n"
            "'Test against real deployed systems or face eternal debugging!'\n"
            "\n"
            "This test MUST use REAL OAuth tokens from REAL flows!\n"
            "Manipulating Redis directly is FORBIDDEN!\n"
            "\n"
            "To fix this test:\n"
            "1. Run: just generate-github-token\n"
            "2. Use the OAUTH_JWT_TOKEN from .env\n"
            "3. Make REAL authenticated requests\n"
            "4. Verify ACTUAL functionality\n"
            "════════════════════════════════════════════════════════════════\n"
        )
        
    
    @pytest.mark.asyncio
    async def test_mcp_fetch_without_token(self, http_client, wait_for_services):
        """Verify that mcp-fetch properly rejects unauthenticated requests"""
        
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "fetch/fetch",
            "params": {
                "url": "https://example.com"
            },
            "id": 1
        }
        
        # Without authentication
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json=mcp_request
        )
        
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"
        
        # The response should be JSON with error details
        error_data = response.json()
        assert "detail" in error_data
        assert "error" in error_data["detail"]
        # Auth service returns invalid_request for missing auth header
        assert error_data["detail"]["error"] in ["invalid_token", "invalid_request"]