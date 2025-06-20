"""
Test fetching example.com through MCP with proper OAuth
Following CLAUDE.md - NO MOCKING, real services only!
"""
import pytest
import httpx
import secrets
import json
import time

import redis.asyncio as redis
from .jwt_test_helper import encode as jwt_encode
from .test_constants import (
    AUTH_BASE_URL,
    MCP_FETCH_URL,
    TEST_REDIRECT_URI,
    GATEWAY_JWT_SECRET,
    ACCESS_TOKEN_LIFETIME,
    BASE_DOMAIN,
    REDIS_URL,
    MCP_PROTOCOL_VERSIONS_SUPPORTED,
    MCP_CLIENT_ACCESS_TOKEN
)
from .mcp_helpers import initialize_mcp_session, call_mcp_tool

class TestMCPFetchExampleCom:
    """Test fetching example.com content with proper MCP protocol"""
    
    @pytest.mark.asyncio
    async def test_fetch_example_com_with_mcp_protocol(self, http_client, wait_for_services):
        """Test fetching https://example.com and verify 'Example Domain' is in content"""
        
        # MUST have MCP client access token - test FAILS if not available
        assert MCP_CLIENT_ACCESS_TOKEN, "MCP_CLIENT_ACCESS_TOKEN not available - run: just mcp-client-token"
        
        # Step 2: Initialize MCP session properly
        try:
            session_id, init_result = await initialize_mcp_session(
                http_client, MCP_FETCH_URL, MCP_CLIENT_ACCESS_TOKEN
            )
            print(f"✓ MCP session initialized: {session_id}")
            
        except RuntimeError:
            # Try with alternative supported version if available
            if len(MCP_PROTOCOL_VERSIONS_SUPPORTED) > 1:
                alt_version = MCP_PROTOCOL_VERSIONS_SUPPORTED[1]
                session_id, init_result = await initialize_mcp_session(
                    http_client, MCP_FETCH_URL, MCP_CLIENT_ACCESS_TOKEN, alt_version
                )
                print(f"✓ MCP session initialized with {alt_version}: {session_id}")
            else:
                raise
        
        # Step 3: Fetch example.com using proper tool call
        try:
            response_data = await call_mcp_tool(
                http_client, MCP_FETCH_URL, MCP_CLIENT_ACCESS_TOKEN, session_id,
                "fetch", {"url": "https://example.com"}, "fetch-1"
            )
            
            print(f"Fetch result: {json.dumps(response_data, indent=2)}")
            
            # Check if we got a successful result
            if "result" in response_data:
                # Extract content from the result structure
                result = response_data["result"]
                content_text = ""
                
                # Handle the MCP content format
                if isinstance(result, dict) and "content" in result:
                    content_items = result["content"]
                    if isinstance(content_items, list):
                        for item in content_items:
                            if isinstance(item, dict) and item.get("type") == "text":
                                content_text += item.get("text", "")
                else:
                    content_text = str(result)
                
                # Check for "Example Domain"
                assert "Example Domain" in content_text, \
                    f"Expected 'Example Domain' in fetched content, but got: {content_text[:500]}..."
                
                print("✅ SUCCESS! Found 'Example Domain' in fetched content!")
                return  # Test passed!
                
            elif "error" in response_data:
                pytest.fail(
                    f"SACRED VIOLATION: MCP fetch returned error: {response_data['error']}\n"
                    f"Tests MUST verify actual functionality, not just authentication!\n"
                    f"This test requires successful fetching of example.com content!"
                )
        
        except RuntimeError as e:
            pytest.fail(
                f"SACRED VIOLATION: Tool call failed: {e}\n"
                f"Tests MUST verify complete functionality!\n"
                f"This test requires successful fetching and content validation!"
            )
        
        # If we reach here without returning, the test FAILED to verify content
        pytest.fail(
            "SACRED VIOLATION: Failed to verify 'Example Domain' content!\n"
            "Tests MUST verify actual functionality, not just authentication!\n"
            "This test requires successful content fetching and validation!"
        )