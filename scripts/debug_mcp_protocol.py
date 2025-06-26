#!/usr/bin/env python3
"""Debug MCP protocol to understand tools/list issue."""

import asyncio

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import ListToolsRequest
from mcp.types import ListToolsResult
from mcp.types import ServerCapabilities
from mcp.types import Tool


# Create a simple server
server = Server("debug-server")

@server.list_tools()
async def list_tools(request: ListToolsRequest) -> ListToolsResult:
    """List available tools."""
    print(f"list_tools request: {request}")
    print(f"request type: {type(request)}")
    print(f"request dict: {request.__dict__ if hasattr(request, '__dict__') else 'no dict'}")

    tools = [
        Tool(
            name="test",
            description="Test tool",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    ]

    result = ListToolsResult(tools=tools)
    print(f"list_tools response: {result}")
    return result

async def test_protocol():
    """Test protocol handling."""
    # Create initialization options
    init_options = InitializationOptions(
        server_name="debug-server",
        server_version="0.1.0",
        capabilities=ServerCapabilities(tools={})
    )

    print(f"InitializationOptions: {init_options}")
    print(f"Available Server methods: {[m for m in dir(server) if not m.startswith('_')]}")

if __name__ == "__main__":
    asyncio.run(test_protocol())
