"""
Debug test to understand MCP fetch authentication with real OAuth token
"""
import pytest
import httpx
import os
import json

@pytest.mark.asyncio
async def test_debug_mcp_fetch_with_real_oauth(http_client, wait_for_services, mcp_fetch_url):
    """Debug test to see what's happening with real OAuth token"""
    
    oauth_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    if not oauth_token:
        pytest.fail("No GATEWAY_OAUTH_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")
    
    print(f"\n=== DEBUGGING MCP FETCH WITH REAL OAUTH ===")
    print(f"OAuth token (first 20 chars): {oauth_token[:20]}...")
    print(f"MCP Fetch URL: {mcp_fetch_url}")
    
    # Try different endpoints
    endpoints = [
        "/mcp",
        "/"
    ]
    
    for endpoint in endpoints:
        print(f"\n--- Testing endpoint: {endpoint} ---")
        
        # First try a simple GET
        try:
            response = await http_client.get(
                f"{mcp_fetch_url}{endpoint}",
                headers={
                    "Authorization": f"Bearer {oauth_token}"
                },
                follow_redirects=True
            )
            print(f"GET {endpoint}: Status {response.status_code}")
            if response.status_code != 404:
                print(f"GET Response: {response.text[:200] if response.text else 'No body'}")
        except Exception as e:
            print(f"GET {endpoint} failed: {e}")
        
        # Then try POST with initialization
        try:
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                },
                "id": "debug-init-1"
            }
            
            response = await http_client.post(
                f"{mcp_fetch_url}{endpoint}",
                json=init_request,
                headers={
                    "Authorization": f"Bearer {oauth_token}",
                    "Content-Type": "application/json"
                },
                follow_redirects=True
            )
            print(f"POST {endpoint} (init): Status {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            if response.status_code == 200:
                print(f"Response body: {response.text}")
                
                # If we got a session ID, try a fetch request
                if 'mcp-session-id' in response.headers:
                    session_id = response.headers['mcp-session-id']
                    print(f"Got session ID: {session_id}")
                    
                    # Try fetch request
                    fetch_request = {
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "fetch",
                            "arguments": {
                                "url": "https://example.com"
                            }
                        },
                        "id": "debug-fetch-1"
                    }
                    
                    fetch_response = await http_client.post(
                        f"{mcp_fetch_url}{endpoint}",
                        json=fetch_request,
                        headers={
                            "Authorization": f"Bearer {oauth_token}",
                            "Content-Type": "application/json",
                            "Mcp-Session-Id": session_id
                        }
                    )
                    print(f"Fetch request status: {fetch_response.status_code}")
                    print(f"Fetch response: {fetch_response.text}")
                    
        except Exception as e:
            print(f"POST {endpoint} failed: {e}")
    
    # Check if we can access without auth
    print(f"\n--- Testing without auth ---")
    response = await http_client.post(
        f"{mcp_fetch_url}/mcp",
        json={"jsonrpc": "2.0", "method": "test", "id": 1}
    )
    print(f"No auth status: {response.status_code}")
    
    # The test always passes - it's just for debugging
    assert True