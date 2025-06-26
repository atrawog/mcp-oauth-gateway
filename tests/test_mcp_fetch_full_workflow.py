"""FULL MCP Fetch Workflow Test - Testing ACTUAL functionality with REAL OAuth
This test verifies the COMPLETE workflow from OAuth authentication to fetching content.
"""

import json
import os

import pytest

from .mcp_helpers import call_mcp_tool
from .mcp_helpers import initialize_mcp_session
from .mcp_helpers import list_mcp_tools
from .test_constants import AUTH_BASE_URL
from .test_constants import HTTP_OK
from .test_constants import HTTP_UNAUTHORIZED
from .test_constants import MCP_PROTOCOL_VERSIONS_SUPPORTED
from .test_fetch_speedup_utils import get_local_test_url


@pytest.mark.asyncio
async def test_full_mcp_fetch_workflow_with_real_oauth(http_client, _wait_for_services, mcp_fetch_url):
    """Test the COMPLETE MCP fetch workflow:

    1. Use REAL OAuth token
    2. Initialize MCP session
    3. Fetch REAL content from a URL
    4. Verify the content is correct.
    """
    # Get REAL OAuth token
    oauth_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    if not oauth_token:
        pytest.fail("This test REQUIRES a REAL OAuth token! Run: just generate-github-token")

    print("\n=== TESTING FULL MCP FETCH WORKFLOW ===")
    print(f"Using OAuth token: {oauth_token[:20]}...")

    # Step 1: Initialize MCP session properly
    print("\nStep 1: Initializing MCP session...")
    try:
        # Try with default protocol version first, then fallback to supported versions
        session_id, init_result = await initialize_mcp_session(http_client, mcp_fetch_url, oauth_token)
        print(f"✓ MCP session initialized: {session_id}")
        print(f"✓ Server info: {init_result.get('serverInfo', {})}")
    except RuntimeError as e:
        # Try with alternative supported version
        if len(MCP_PROTOCOL_VERSIONS_SUPPORTED) > 1:
            alt_version = MCP_PROTOCOL_VERSIONS_SUPPORTED[1]  # Try the second supported version
            print(f"Retrying with alternative protocol version: {alt_version}")
            session_id, init_result = await initialize_mcp_session(http_client, mcp_fetch_url, oauth_token, alt_version)
            print(f"✓ MCP session initialized with {alt_version}: {session_id}")
        else:
            raise e

    # Step 2: List available tools
    print("\nStep 2: Listing available tools...")
    try:
        tools_result = await list_mcp_tools(http_client, mcp_fetch_url, oauth_token, session_id)
        print(f"Tools response: {json.dumps(tools_result, indent=2)}")
    except RuntimeError as e:
        print(f"Warning: Could not list tools: {e}")

    # Step 3: Call the fetch tool
    print("\nStep 3: Calling fetch local test URL...")
    try:
        fetch_result = await call_mcp_tool(
            http_client,
            mcp_fetch_url,
            oauth_token,
            session_id,
            "fetch",
            {"url": get_local_test_url()},
            "fetch-1",
        )

        print(
            f"Fetch response (first 1000 chars): {json.dumps(fetch_result, indent=2)[:1000]}"  # TODO: Break long line
        )

        # Check the result directly (no need to parse JSON again)
        data = fetch_result

    except RuntimeError as e:
        print(f"Fetch failed! Error: {e}")
        pytest.fail(f"Failed to fetch content: {e}")

    # Parse the response
    if "result" in data:
        result = data["result"]

        # The result contains content array with text items
        if "content" in result and isinstance(result["content"], list):
            for item in result["content"]:
                if item.get("type") == "text" and "text" in item:
                    content = item["text"]

                    # Verify we got example.com content
                    assert "MCP OAuth Gateway" in content or "example" in content.lower(), (
                        f"Didn't get expected content from example.com! Got: {content[:200]}"  # TODO: Break long line
                    )

                    print("\n✅ SUCCESS! fetch local test URL")
                    print(f"✅ Content preview: {content[:200]}...")
                    print("✅ MCP Fetch is working with REAL OAuth!")
                    return
    elif "error" in data:
        pytest.fail(f"MCP returned an error: {data['error']}")

    # If we got here, we didn't find the expected content
    pytest.fail("Failed to find fetched content in response!")


@pytest.mark.asyncio
async def test_mcp_fetch_unauthorized_fails(http_client, _wait_for_services, mcp_test_url):
    """Verify that MCP fetch REQUIRES proper authentication."""
    # Try to access without token
    response = await http_client.post(f"{mcp_test_url}", json={"jsonrpc": "2.0", "method": "test", "id": 1})

    assert response.status_code == HTTP_UNAUTHORIZED, f"Expected 401, got {response.status_code}"
    assert "WWW-Authenticate" in response.headers
    print("✅ MCP fetch correctly rejects unauthorized requests")


@pytest.mark.asyncio
async def test_oauth_token_validation(http_client, _wait_for_services):
    """Verify the OAuth token is properly validated by the auth service."""
    oauth_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    if not oauth_token:
        pytest.fail("No OAuth token available - TESTS MUST NOT BE SKIPPED!")

    # Test the /verify endpoint directly
    response = await http_client.get(f"{AUTH_BASE_URL}/verify", headers={"Authorization": f"Bearer {oauth_token}"})

    if response.status_code == HTTP_OK:
        print("✅ OAuth token is valid and verified by auth service")
        # The /verify endpoint returns 200 with no body when successful
        print("   Token validation successful!")
    else:
        print(f"❌ OAuth token validation failed: {response.status_code}")
        print(f"   Response: {response.text}")
        pytest.fail("OAuth token is not valid!")
