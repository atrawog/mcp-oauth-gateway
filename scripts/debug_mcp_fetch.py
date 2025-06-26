#!/usr/bin/env python
"""Debug script to check MCP fetch service tools."""

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx


# Add parent directory to path to import test helpers
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.mcp_helpers import initialize_mcp_session
from tests.mcp_helpers import list_mcp_tools


async def main():
    """Check what tools are available on the MCP fetch service."""
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
    print(f"🔍 Checking MCP fetch service at: {mcp_url}")

    async with httpx.AsyncClient(verify=True, timeout=30.0) as client:
        try:
            # Initialize session
            print("\n📤 Initializing MCP session...")
            session_id, init_result = await initialize_mcp_session(client, mcp_url, oauth_token, "2025-03-26")
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
                    if "parameters" in tool:
                        print(f"     Parameters: {json.dumps(tool['parameters'], indent=6)}")
            else:
                print(f"❌ Error response: {tools_response}")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
