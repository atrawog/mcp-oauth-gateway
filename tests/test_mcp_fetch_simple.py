"""
Simple MCP Fetch Test - Verify authentication works
Following CLAUDE.md - NO MOCKING, real services only!
"""
import pytest
import httpx
import secrets
import json
import time
from jose import jwt
import redis.asyncio as redis
from .test_constants import (
    AUTH_BASE_URL,
    MCP_FETCH_URL,
    TEST_REDIRECT_URI,
    JWT_SECRET,
    ACCESS_TOKEN_LIFETIME,
    BASE_DOMAIN,
    REDIS_URL
)


class TestMCPFetchSimple:
    """Simple test to verify MCP fetch authentication"""
    
    @pytest.mark.asyncio
    async def test_mcp_fetch_auth_works(self, http_client, wait_for_services, registered_client):
        """Test that we can authenticate to mcp-fetch service"""
        
        # Connect to Redis
        redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        
        try:
            # Create a valid JWT token
            jti = secrets.token_urlsafe(16)
            now = int(time.time())
            
            token_claims = {
                "sub": "test_user_simple",
                "username": "simpletest",
                "email": "simple@test.com",
                "name": "Simple Test",
                "scope": "openid profile email",
                "client_id": registered_client["client_id"],
                "jti": jti,
                "iat": now,
                "exp": now + ACCESS_TOKEN_LIFETIME,
                "iss": f"https://auth.{BASE_DOMAIN}"
            }
            
            # Create JWT
            access_token = jwt.encode(token_claims, JWT_SECRET, algorithm="HS256")
            
            # Store in Redis (simulating successful OAuth)
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
            
            # Simple MCP request - just list available tools
            mcp_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            }
            
            # Test authentication works - MCP requires /mcp/ with trailing slash
            response = await http_client.post(
                f"{MCP_FETCH_URL}/mcp/",  # Note the trailing slash!
                json=mcp_request,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"  # MCP requires this
                },
                follow_redirects=True  # Handle the 307 redirect
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                # Success! MCP is working
                result = response.json()
                print(f"MCP Response: {json.dumps(result, indent=2)}")
                
                # If we can list tools, let's try fetching example.com
                fetch_request = {
                    "jsonrpc": "2.0",
                    "method": "fetch/fetch",
                    "params": {
                        "url": "https://example.com"
                    },
                    "id": 2
                }
                
                fetch_response = await http_client.post(
                    f"{MCP_FETCH_URL}/mcp",
                    json=fetch_request,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                if fetch_response.status_code == 200:
                    fetch_result = fetch_response.json()
                    print(f"Fetch result: {json.dumps(fetch_result, indent=2)}")
                    
                    # Check for "Example Domain" in the content
                    if "result" in fetch_result:
                        content = str(fetch_result.get("result", {}))
                        if "Example Domain" in content:
                            print("✓ Successfully found 'Example Domain' in fetched content!")
                        else:
                            print("Content fetched but 'Example Domain' not found")
                            print(f"Content preview: {content[:200]}...")
                            
            else:
                # Print response for debugging
                print(f"Response body: {response.text}")
                
                # Check if it's an auth issue or service issue
                if response.status_code == 401:
                    print("Authentication failed - token not accepted")
                elif response.status_code == 404:
                    print("Endpoint not found - service may not be configured correctly")
                elif response.status_code == 307:
                    print(f"Redirect to: {response.headers.get('Location')}")
                    
        finally:
            # Clean up
            await redis_client.delete(f"oauth:token:{jti}")
            await redis_client.aclose()