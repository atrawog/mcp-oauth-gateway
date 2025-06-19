#!/usr/bin/env python3
"""
Simple MCP Fetch Server using FastMCP
Following CLAUDE.md - Direct streamable HTTP server!
"""
from fastmcp import FastMCP
import httpx
import os

# Create the divine MCP server
mcp = FastMCP("MCP Fetch Server - OAuth Blessed")

@mcp.tool()
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
    # Note: FastMCP 2.1.2 doesn't support all the parameters from newer versions
    import uvicorn
    from mcp.server.app import get_openapi
    
    # Get the app from FastMCP
    app = mcp._get_asgi_app(openapi=get_openapi(mcp))
    
    # Run with uvicorn directly for more control
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=3000,
        log_level="info"
    )