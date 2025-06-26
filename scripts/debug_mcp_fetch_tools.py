#!/usr/bin/env python
"""Debug script to test tool calls on MCP fetch service."""

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx


# Add parent directory to path to import test helpers
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.mcp_helpers import call_mcp_tool
from tests.mcp_helpers import initialize_mcp_session
from tests.mcp_helpers import list_mcp_tools


async def main():
    """Test tool calls on the MCP fetch service."""
    # Get environment variables
    base_domain = os.getenv("BASE_DOMAIN")
    oauth_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")

    if not base_domain:
        print("❌ BASE_DOMAIN not set!")
        return

    if not oauth_token:
        print("❌ GATEWAY_OAUTH_ACCESS_TOKEN not set!")
        return

    mcp_url = f"https://fetch.{base_domain}/mcp"
    print(f"🔍 Testing MCP fetch service at: {mcp_url}")

    async with httpx.AsyncClient(verify=True, timeout=30.0) as client:
        # Test with different protocol versions
        versions_to_test = ["2025-06-18", "2025-03-26"]

        for version in versions_to_test:
            print(f"\n\n{'=' * 60}")
            print(f"Testing with protocol version: {version}")
            print("=" * 60)

            try:
                # Initialize session
                print(f"\n📤 Initializing MCP session with version {version}...")
                session_id, init_result = await initialize_mcp_session(client, mcp_url, oauth_token, version)
                print(f"✅ Session initialized: {session_id}")
                print(f"   Server info: {init_result.get('serverInfo')}")
                print(f"   Protocol version: {init_result.get('protocolVersion')}")

                # List tools
                print("\n📋 Listing available tools...")
                tools_response = await list_mcp_tools(client, mcp_url, oauth_token, session_id)

                if "result" in tools_response:
                    tools = tools_response["result"].get("tools", [])
                    print(f"✅ Found {len(tools)} tools:")
                    for tool in tools:
                        print(f"   - {tool.get('name')}: {tool.get('description', 'No description')}")
                else:
                    print(f"❌ Error listing tools: {tools_response}")
                    continue

                # Try calling the fetch tool
                print("\n🔧 Testing fetch tool call...")
                try:
                    result = await call_mcp_tool(
                        client,
                        mcp_url,
                        oauth_token,
                        session_id,
                        "fetch",
                        {"url": "https://example.com"},
                        f"debug-fetch-{version}",
                    )

                    if "error" in result:
                        print(f"❌ Tool call error: {result['error']}")
                    elif "result" in result:
                        print("✅ Fetch successful!")
                        # Extract content
                        fetch_result = result["result"]
                        if isinstance(fetch_result, dict) and "content" in fetch_result:
                            content_items = fetch_result["content"]
                            if isinstance(content_items, list) and len(content_items) > 0:
                                first_item = content_items[0]
                                if isinstance(first_item, dict) and first_item.get("type") == "text":
                                    text = first_item.get("text", "")
                                    print(f"   Content preview: {text[:100]}...")
                    else:
                        print(f"❓ Unexpected result: {json.dumps(result, indent=2)}")

                except Exception as e:
                    print(f"❌ Tool call failed: {e}")

            except Exception as e:
                print(f"❌ Error with version {version}: {e}")
                import traceback

                traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
