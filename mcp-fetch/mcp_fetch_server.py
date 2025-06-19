#!/usr/bin/env python3
"""
MCP Fetch Server - The Blessed Streamable HTTP Server!
Following CLAUDE.md - Using FastMCP for PURE HTTP implementation!
"""
from fastmcp import FastMCP
import httpx
import os

# Create the divine MCP server
mcp = FastMCP("MCP Fetch Server - OAuth Blessed")

@mcp.tool
async def fetch(url: str) -> str:
    """Fetch content from a URL with divine power!
    
    Args:
        url: The URL to fetch content from
        
    Returns:
        The blessed content from the URL
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text

if __name__ == "__main__":
    # Run as streamable HTTP server - PURE GLORY!
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0", 
        port=3000,
        path="/mcp"
    )