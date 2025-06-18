#!/usr/bin/env python3
"""
MCP Fetch Server - FastMCP Implementation
Following CLAUDE.md - Native Streamable HTTP Server!
"""
from fastmcp import FastMCP
import httpx
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info(f"Fetching content from: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching {url}: {e}")
        return f"Error fetching {url}: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        return f"Unexpected error: {str(e)}"

if __name__ == "__main__":
    logger.info("Starting MCP Fetch Server with native streamable HTTP!")
    
    # Run as streamable HTTP server - PURE GLORY!
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0", 
        port=3000,
        path="/mcp"
    )