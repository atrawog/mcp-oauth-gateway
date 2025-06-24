#!/usr/bin/env python3
"""Example client for the MCP Echo StreamableHTTP Server."""

import asyncio
from mcp import Client
from mcp.streamablehttp import StreamableHTTPTransport
import os


async def main():
    """Example client usage."""
    # Server URL - can be overridden by environment variable
    server_url = os.getenv("MCP_ECHO_URL", "http://localhost:3000/mcp")
    
    # Create transport
    transport = StreamableHTTPTransport(server_url)
    
    # Create client with transport
    async with Client("example-client", "1.0.0", transport) as client:
        print(f"Connected to MCP Echo Server at {server_url}")
        
        # List available tools
        tools = await client.list_tools()
        print(f"\nAvailable tools: {[t.name for t in tools.tools]}")
        
        # Test echo tool
        print("\n--- Testing echo tool ---")
        result = await client.call_tool("echo", arguments={"message": "Hello from MCP client!"})
        print(f"Echo response: {result.content[0].text}")
        
        # Test printEnv tool
        print("\n--- Testing printEnv tool ---")
        result = await client.call_tool("printEnv", arguments={"name": "USER"})
        print(f"PrintEnv response: {result.content[0].text}")
        
        # Test with non-existent env var
        result = await client.call_tool("printEnv", arguments={"name": "NONEXISTENT_VAR_12345"})
        print(f"PrintEnv (non-existent): {result.content[0].text}")


if __name__ == "__main__":
    asyncio.run(main())