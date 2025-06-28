#!/usr/bin/env python3
"""Basic example of using mcp-streamablehttp-server."""

import asyncio
import json

import httpx


async def test_mcp_server():
    """Test the MCP streamable HTTP server with example requests."""
    base_url = "http://localhost:3000"

    async with httpx.AsyncClient() as client:
        # Initialize session
        print("\nInitializing MCP session...")
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
            "id": 1,
        }

        response = await client.post(
            f"{base_url}/mcp",
            json=init_request,
            headers={"Content-Type": "application/json"},
        )

        print(f"Initialize response: {json.dumps(response.json(), indent=2)}")
        session_id = response.headers.get("Mcp-Session-Id")
        print(f"Session ID: {session_id}")

        # Send initialized notification
        print("\nSending initialized notification...")
        initialized_request = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }

        response = await client.post(
            f"{base_url}/mcp",
            json=initialized_request,
            headers={"Content-Type": "application/json", "Mcp-Session-Id": session_id},
        )

        # List available tools
        print("\nListing available tools...")
        list_tools_request = {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2}

        response = await client.post(
            f"{base_url}/mcp",
            json=list_tools_request,
            headers={"Content-Type": "application/json", "Mcp-Session-Id": session_id},
        )

        print(f"Tools response: {json.dumps(response.json(), indent=2)}")

        # Call a tool (example: fetch)
        print("\nCalling fetch tool...")
        fetch_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "fetch", "arguments": {"url": "https://example.com"}},
            "id": 3,
        }

        response = await client.post(
            f"{base_url}/mcp",
            json=fetch_request,
            headers={"Content-Type": "application/json", "Mcp-Session-Id": session_id},
        )

        print(f"Fetch response: {json.dumps(response.json(), indent=2)}")


if __name__ == "__main__":
    print("MCP Streamable HTTP Server Example")
    print("===================================")
    print("Make sure the server is running with:")
    print("  mcp-streamablehttp-server python -m mcp_server_fetch")
    print()

    asyncio.run(test_mcp_server())
