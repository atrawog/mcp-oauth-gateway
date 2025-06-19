#!/usr/bin/env python3
"""
Run the official MCP fetch server as an HTTP server
Using the mcp package's HTTP server capabilities
"""
import asyncio
import sys
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp_server_fetch import McpServerFetch
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from mcp.server.http import create_sse_handler

async def run_http_server():
    # Create the MCP fetch server instance
    server = await McpServerFetch.create()
    
    # Create SSE handler for the server
    sse_handler = create_sse_handler(server)
    
    # Create Starlette app with routes
    app = Starlette(
        routes=[
            Route("/mcp", endpoint=sse_handler, methods=["POST", "GET"]),
            Route("/health", endpoint=lambda request: {"status": "ok"}, methods=["GET"])
        ]
    )
    
    # Run with uvicorn
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=3000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(run_http_server())