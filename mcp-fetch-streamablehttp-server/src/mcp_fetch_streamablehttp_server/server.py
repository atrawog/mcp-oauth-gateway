"""MCP fetch server with native Streamable HTTP transport."""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

import uvloop
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from mcp.server import Server
from mcp.types import TextContent, ImageContent
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

from .transport import StreamableHTTPTransport
from .fetch_handler import FetchHandler

# Use uvloop for better performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Server configuration."""
    
    # Server settings
    server_name: str = "mcp-fetch-streamablehttp"
    server_version: str = "0.1.0"
    protocol_version: str = "2025-06-18"
    
    # Fetch settings
    allowed_schemes: List[str] = ["http", "https"]
    max_redirects: int = 5
    default_user_agent: str = "ModelContextProtocol/1.0 (Fetch Server)"
    
    # Transport settings
    enable_sse: bool = False  # SSE support for future implementation
    
    model_config = ConfigDict(
        env_prefix="MCP_FETCH_",
        env_file=".env"
    )


class StreamableHTTPServer:
    """MCP server with native Streamable HTTP transport."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.transport = StreamableHTTPTransport()
        self.fetch_handler = FetchHandler(
            allowed_schemes=self.settings.allowed_schemes,
            max_redirects=self.settings.max_redirects
        )
        
        # Create MCP server
        self.server = Server(self.settings.server_name)
        
        # Register tools
        self._register_tools()
        
        # Track active sessions
        self.sessions: Dict[str, Any] = {}
        
    def _register_tools(self):
        """Register fetch tool with MCP server."""
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent | ImageContent]:
            """Handle tool calls."""
            
            if name == "fetch":
                return await self.fetch_handler.handle_fetch(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
                
        @self.server.list_tools()
        async def list_tools() -> List[Dict[str, Any]]:
            """List available tools."""
            tools = self.fetch_handler.get_tools()
            return [tool.model_dump() for tool in tools]
            
    async def handle_request(self, request: Request) -> Response:
        """Handle HTTP request and route to transport."""
        
        # Extract method, path, headers, and body
        method = request.method
        path = request.url.path
        headers = dict(request.headers)
        
        # Read body for POST/PUT
        body = None
        if method in ["POST", "PUT"]:
            body = await request.body()
            
        # Handle OPTIONS first (CORS preflight doesn't require auth)
        if method == "OPTIONS":
            # CORS preflight
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, Mcp-Session-Id, MCP-Protocol-Version",
                    "Access-Control-Max-Age": "86400",
                }
            )
            
        # Handle health check (no auth required)
        if method == "GET" and path == "/health":
            return JSONResponse({"status": "healthy", "version": self.settings.server_version})
            
        # Handle authentication for other requests
        auth_header = headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
                content={"error": "Unauthorized", "message": "Bearer token required"}
            )
            
        # For stateless operation, process request directly
        if method == "POST" and path == "/mcp":
            return await self._handle_stateless_request(headers, body)
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "Not found", "message": f"Path {path} not found"}
            )
            
    async def _handle_stateless_request(self, headers: Dict[str, str], body: bytes) -> Response:
        """Handle stateless JSON-RPC request."""
        
        # Validate content type
        content_type = headers.get("content-type", "").lower()
        if not content_type.startswith("application/json"):
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Invalid content type",
                    "message": "Content-Type must be application/json"
                }
            )
            
        # Parse JSON-RPC request
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error",
                        "data": str(e)
                    },
                    "id": None
                }
            )
            
        # Validate JSON-RPC structure
        if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request",
                        "data": "Missing or invalid jsonrpc version"
                    },
                    "id": data.get("id")
                }
            )
            
        # Handle different methods
        method = data.get("method")
        request_id = data.get("id")
        params = data.get("params", {})
        
        try:
            if method == "initialize":
                # Handle initialization
                result = {
                    "protocolVersion": self.settings.protocol_version,
                    "capabilities": {
                        "tools": {},
                        "prompts": None,
                        "resources": None,
                        "logging": None
                    },
                    "serverInfo": {
                        "name": self.settings.server_name,
                        "version": self.settings.server_version
                    }
                }
            elif method == "tools/list":
                # List available tools
                tools = self.fetch_handler.get_tools()
                result = {
                    "tools": [tool.model_dump() for tool in tools]
                }
            elif method == "tools/call":
                # Call a tool
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                if tool_name == "fetch":
                    contents = await self.fetch_handler.handle_fetch(tool_args)
                    result = {
                        "content": [content.model_dump() for content in contents]
                    }
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
            else:
                # Unknown method
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": "Method not found",
                            "data": f"Unknown method: {method}"
                        },
                        "id": request_id
                    }
                )
                
            # Return success response
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id
                },
                headers={
                    "Content-Type": "application/json",
                    "Mcp-Session-Id": self.transport.session_id,
                    "MCP-Protocol-Version": self.settings.protocol_version,
                }
            )
            
        except Exception as e:
            # Return error response
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    },
                    "id": request_id
                }
            )
                    
    def create_app(self) -> FastAPI:
        """Create FastAPI application."""
        
        app = FastAPI(
            title=self.settings.server_name,
            version=self.settings.server_version,
            docs_url=None,  # Disable docs for security
            redoc_url=None,
        )
        
        # Add routes
        app.add_api_route("/mcp", self.handle_request, methods=["GET", "POST", "DELETE", "OPTIONS"])
        app.add_api_route("/health", self.handle_request, methods=["GET"])
        
        return app


def create_server(settings: Optional[Settings] = None) -> StreamableHTTPServer:
    """Create and configure MCP fetch server."""
    return StreamableHTTPServer(settings)


# Create default app for ASGI servers
app = create_server().create_app()