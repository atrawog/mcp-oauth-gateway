"""
FULL MCP Fetch Workflow Test - Testing ACTUAL functionality with REAL OAuth
This test verifies the COMPLETE workflow from OAuth authentication to fetching content
"""
import pytest
import httpx
import os
import json
from .test_constants import MCP_FETCH_URL, AUTH_BASE_URL


@pytest.mark.asyncio
async def test_full_mcp_fetch_workflow_with_real_oauth(http_client, wait_for_services):
    """
    Test the COMPLETE MCP fetch workflow:
    1. Use REAL OAuth token
    2. Initialize MCP session
    3. Fetch REAL content from a URL
    4. Verify the content is correct
    """
    
    # Get REAL OAuth token
    oauth_token = os.getenv("OAUTH_ACCESS_TOKEN")
    if not oauth_token:
        pytest.fail("This test REQUIRES a REAL OAuth token! Run: just generate-github-token")
    
    print("\n=== TESTING FULL MCP FETCH WORKFLOW ===")
    print(f"Using OAuth token: {oauth_token[:20]}...")
    
    # Step 1: Initialize MCP session
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        },
        "id": "init-1"
    }
    
    print("\nStep 1: Initializing MCP session...")
    init_response = await http_client.post(
        f"{MCP_FETCH_URL}/mcp/",
        json=init_request,
        headers={
            "Authorization": f"Bearer {oauth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        },
        follow_redirects=True
    )
    
    print(f"Init response status: {init_response.status_code}")
    print(f"Init response headers: {dict(init_response.headers)}")
    
    if init_response.status_code != 200:
        print(f"Init failed! Response: {init_response.text}")
        pytest.fail(f"Failed to initialize MCP session: {init_response.status_code}")
    
    # Parse SSE response
    response_text = init_response.text
    print(f"Init response (first 500 chars): {response_text[:500]}")
    
    # Extract session ID if provided
    session_id = init_response.headers.get('mcp-session-id')
    if session_id:
        print(f"Got session ID: {session_id}")
    
    # Step 2: Send initialized notification
    initialized_notification = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    
    headers = {
        "Authorization": f"Bearer {oauth_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    
    print("\nStep 2: Sending initialized notification...")
    await http_client.post(
        f"{MCP_FETCH_URL}/mcp/",
        json=initialized_notification,
        headers=headers,
        follow_redirects=True
    )
    
    # Step 3: List available tools
    list_tools_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": "list-tools-1"
    }
    
    print("\nStep 3: Listing available tools...")
    tools_response = await http_client.post(
        f"{MCP_FETCH_URL}/mcp/",
        json=list_tools_request,
        headers=headers,
        follow_redirects=True
    )
    
    if tools_response.status_code == 200:
        print(f"Tools response: {tools_response.text[:500]}")
    
    # Step 4: Call the fetch tool
    fetch_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "fetch",
            "arguments": {
                "url": "https://example.com"
            }
        },
        "id": "fetch-1"
    }
    
    print("\nStep 4: Calling fetch tool to get https://example.com...")
    fetch_response = await http_client.post(
        f"{MCP_FETCH_URL}/mcp/",
        json=fetch_request,
        headers=headers,
        follow_redirects=True
    )
    
    print(f"Fetch response status: {fetch_response.status_code}")
    
    if fetch_response.status_code != 200:
        print(f"Fetch failed! Response: {fetch_response.text}")
        pytest.fail(f"Failed to fetch content: {fetch_response.status_code}")
    
    # Parse the response
    response_text = fetch_response.text
    print(f"Fetch response (first 1000 chars): {response_text[:1000]}")
    
    # Parse the JSON response
    try:
        data = json.loads(response_text)
        if "result" in data:
            result = data["result"]
            
            # The result contains content array with text items
            if "content" in result and isinstance(result["content"], list):
                for item in result["content"]:
                    if item.get("type") == "text" and "text" in item:
                        content = item["text"]
                        
                        # Verify we got example.com content
                        assert "Example Domain" in content or "example" in content.lower(), \
                            f"Didn't get expected content from example.com! Got: {content[:200]}"
                        
                        print(f"\n✅ SUCCESS! Fetched content from example.com")
                        print(f"✅ Content preview: {content[:200]}...")
                        print(f"✅ MCP Fetch is working with REAL OAuth!")
                        return
        elif "error" in data:
            pytest.fail(f"MCP returned an error: {data['error']}")
            
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse response as JSON: {e}")
    
    # If we got here, we didn't find the expected content
    pytest.fail("Failed to find fetched content in response!")


@pytest.mark.asyncio
async def test_mcp_fetch_unauthorized_fails(http_client, wait_for_services):
    """Verify that MCP fetch REQUIRES proper authentication"""
    
    # Try to access without token
    response = await http_client.post(
        f"{MCP_FETCH_URL}/mcp/",
        json={"jsonrpc": "2.0", "method": "test", "id": 1}
    )
    
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    assert "WWW-Authenticate" in response.headers
    print("✅ MCP fetch correctly rejects unauthorized requests")


@pytest.mark.asyncio
async def test_oauth_token_validation(http_client, wait_for_services):
    """Verify the OAuth token is properly validated by the auth service"""
    
    oauth_token = os.getenv("OAUTH_ACCESS_TOKEN")
    if not oauth_token:
        pytest.skip("No OAuth token available")
    
    # Test the /verify endpoint directly
    response = await http_client.get(
        f"{AUTH_BASE_URL}/verify",
        headers={"Authorization": f"Bearer {oauth_token}"}
    )
    
    if response.status_code == 200:
        print("✅ OAuth token is valid and verified by auth service")
        # The /verify endpoint returns 200 with no body when successful
        print("   Token validation successful!")
    else:
        print(f"❌ OAuth token validation failed: {response.status_code}")
        print(f"   Response: {response.text}")
        pytest.fail("OAuth token is not valid!")