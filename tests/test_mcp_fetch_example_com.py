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
    MCP_PROTOCOL_VERSIONS_SUPPORTED
)
from .mcp_helpers import initialize_mcp_session, call_mcp_tool

class TestMCPFetchExampleCom:
    """Test fetching example.com content with proper MCP protocol"""
    
    @pytest.mark.asyncio
    async def test_fetch_example_com_with_mcp_protocol(self, http_client, wait_for_services, registered_client):
        """Test fetching https://example.com and verify 'Example Domain' is in content"""
        
        # Connect to Redis
        redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        
        try:
            # Create a valid JWT token
            jti = secrets.token_urlsafe(16)
            now = int(time.time())
            
            token_claims = {
                "sub": "test_user_example",
                "username": "examplefetch",
                "email": "example@test.com",
                "name": "Example Fetch Test",
                "scope": "openid profile email",
                "client_id": registered_client["client_id"],
                "jti": jti,
                "iat": now,
                "exp": now + ACCESS_TOKEN_LIFETIME,
                "iss": f"https://auth.{BASE_DOMAIN}"
            }
            
            # Create JWT
            access_token = jwt_encode(token_claims, GATEWAY_JWT_SECRET, algorithm="HS256")
            
            # Store in Redis
            await redis_client.setex(
                f"oauth:token:{jti}",
                ACCESS_TOKEN_LIFETIME,
                json.dumps({
                    "sub": token_claims["sub"],
                    "username": token_claims["username"],
                    "email": token_claims["email"],
                    "name": token_claims["name"],
                    "scope": token_claims["scope"],
                    "client_id": token_claims["client_id"]
                })
            )
            
            # Add to user's tokens
            await redis_client.sadd(f"oauth:user_tokens:{token_claims['username']}", jti)
            
            # Step 2: Initialize MCP session properly
            try:
                session_id, init_result = await initialize_mcp_session(
                    http_client, MCP_FETCH_URL, access_token
                )
                print(f"✓ MCP session initialized: {session_id}")
                
            except RuntimeError:
                # Try with alternative supported version if available
                if len(MCP_PROTOCOL_VERSIONS_SUPPORTED) > 1:
                    alt_version = MCP_PROTOCOL_VERSIONS_SUPPORTED[1]
                    session_id, init_result = await initialize_mcp_session(
                        http_client, MCP_FETCH_URL, access_token, alt_version
                    )
                    print(f"✓ MCP session initialized with {alt_version}: {session_id}")
                else:
                    raise
            
            # Step 3: Fetch example.com using proper tool call
            try:
                response_data = await call_mcp_tool(
                    http_client, MCP_FETCH_URL, access_token, session_id,
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
                
        finally:
            # Clean up
            await redis_client.delete(f"oauth:token:{jti}")
            await redis_client.srem(f"oauth:user_tokens:examplefetch", jti)
            await redis_client.aclose()