#!/usr/bin/env python3
"""Basic usage example for mcp-fetch-streamablehttp-client."""

import asyncio
import json
import os
from mcp_fetch_streamablehttp_client import MCPFetchClient, MCPError


async def main():
    # Get server URL and token from environment or use defaults
    server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
    access_token = os.getenv("MCP_ACCESS_TOKEN")
    
    print(f"Connecting to MCP server at {server_url}")
    
    # Create client with optional authentication
    async with MCPFetchClient(server_url, access_token=access_token) as client:
        try:
            # Initialize the session
            print("\n1. Initializing MCP session...")
            info = await client.initialize()
            
            print(f"   Connected to: {info['serverInfo']['name']} v{info['serverInfo']['version']}")
            print(f"   Protocol version: {info['protocolVersion']}")
            print(f"   Capabilities: {list(info['capabilities'].keys())}")
            
            # Example 1: Fetch a simple webpage
            print("\n2. Fetching example.com...")
            result = await client.fetch("https://example.com")
            print(f"   Status: {result.status}")
            print(f"   Content-Type: {result.mimeType}")
            print(f"   Content length: {len(result.text)} characters")
            print(f"   First 100 chars: {result.text[:100]}...")
            
            # Example 2: Fetch JSON data
            print("\n3. Fetching JSON from httpbin.org...")
            result = await client.fetch("https://httpbin.org/json")
            if result.mimeType and "json" in result.mimeType:
                data = json.loads(result.text)
                print(f"   JSON keys: {list(data.keys())}")
            
            # Example 3: POST request with data
            print("\n4. Making POST request...")
            result = await client.fetch(
                url="https://httpbin.org/post",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps({"hello": "world", "test": True})
            )
            response_data = json.loads(result.text)
            print(f"   Posted data echo: {response_data.get('data')}")
            
            # Example 4: Custom headers
            print("\n5. Fetch with custom headers...")
            result = await client.fetch(
                url="https://httpbin.org/headers",
                headers={
                    "User-Agent": "MCP-Fetch-Client/1.0",
                    "X-Custom-Header": "test-value"
                }
            )
            response_data = json.loads(result.text)
            print(f"   Server saw headers: {response_data.get('headers', {}).get('X-Custom-Header')}")
            
            # Example 5: List available tools
            print("\n6. Listing available tools...")
            tools = await client.list_tools()
            if tools:
                print(f"   Found {len(tools)} tools:")
                for tool in tools:
                    print(f"   - {tool['name']}: {tool.get('description', 'No description')}")
            else:
                print("   No tools available")
            
        except MCPError as e:
            print(f"\n❌ Error: {e}")
            if hasattr(e, 'code'):
                print(f"   Error code: {e.code}")
            if hasattr(e, 'data'):
                print(f"   Error data: {e.data}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())