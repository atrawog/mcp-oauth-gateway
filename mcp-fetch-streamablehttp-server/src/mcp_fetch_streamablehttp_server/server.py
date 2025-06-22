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
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

from .transport import StreamableHTTPTransport
from .fetch_handler import FetchHandler

# Use uvloop for better performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Server configuration."""
    
    # Server settings
    server_name: str = Field(..., description="Server name")
    server_version: str = Field(..., description="Server version")
    protocol_version: str = Field(..., description="Protocol version")
    
    # Fetch settings
    fetch_allowed_schemes: List[str] = Field(default=["http", "https"], description="Allowed URL schemes")
    fetch_max_redirects: int = Field(default=5, description="Max redirects")
    fetch_default_user_agent: str = Field(default="ModelContextProtocol/1.0 (Fetch Server)", description="User agent")
    
    # Transport settings
    fetch_enable_sse: bool = Field(default=False, description="SSE support for future implementation")
    
    model_config = ConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        extra="allow"
    )


class StreamableHTTPServer:
    """MCP server with native Streamable HTTP transport."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.transport = StreamableHTTPTransport()
        self.fetch_handler = FetchHandler(
            allowed_schemes=self.settings.fetch_allowed_schemes,
            max_redirects=self.settings.fetch_max_redirects
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
                    "Access-Control-Allow-Headers": "Content-Type, Mcp-Session-Id, MCP-Protocol-Version",
                    "Access-Control-Max-Age": "86400",
                }
            )
            
        # Handle health check (no auth required)
        if method == "GET" and path == "/health":
            return JSONResponse({"status": "healthy", "version": self.settings.server_version})
            
        # ⚡ DIVINE DECREE: NO AUTHENTICATION IN MCP SERVICES! ⚡
        # Authentication is handled by Traefik via ForwardAuth middleware
        # MCP services must maintain "pure protocol innocence" per CLAUDE.md
        # The holy trinity separation demands it!
            
        # Check MCP protocol version header if provided
        mcp_version = headers.get("mcp-protocol-version", headers.get("MCP-Protocol-Version"))
        if mcp_version and mcp_version != self.settings.protocol_version:
            return JSONResponse(
                status_code=400,
                content={"error": "Unsupported protocol version", "message": f"Server only supports MCP version: {self.settings.protocol_version}, got {mcp_version}"}
            )
        
        # For stateless operation, process request directly
        if method == "POST" and path == "/mcp":
            return await self._handle_stateless_request(headers, body)
        elif method == "GET" and path == "/mcp":
            # SSE endpoint - not implemented yet
            return JSONResponse(
                status_code=501,
                content={"error": "Not implemented", "message": "Server-Sent Events not yet supported"}
            )
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "Not found", "message": f"Path {path} not found"}
            )
            
    async def _handle_stateless_request(self, headers: Dict[str, str], body: bytes) -> Response:
        """Handle stateless JSON-RPC request."""
        
        # Note: Be lenient with content type as long as body is valid JSON
        # This allows clients that may send incorrect content types
            
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
                # Handle initialization per MCP 2025-06-18
                # Client should provide protocolVersion in params
                client_protocol = params.get("protocolVersion", self.settings.protocol_version)
                
                # Check if client protocol matches server version
                if client_protocol != self.settings.protocol_version:
                    return JSONResponse(
                        content={
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32602,
                                "message": "Invalid params",
                                "data": f"Unsupported protocol version: {client_protocol}. Server supports: {self.settings.protocol_version}"
                            },
                            "id": request_id
                        },
                        status_code=200,
                        headers={
                            "Content-Type": "application/json",
                            "Mcp-Session-Id": self.transport.session_id,
                            "MCP-Protocol-Version": self.settings.protocol_version,
                        }
                    )
                
                result = {
                    "protocolVersion": self.settings.protocol_version,
                    "capabilities": {
                        "tools": {},  # We support tools
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
                # List available tools per MCP 2025-06-18
                # Support pagination via cursor parameter
                cursor = params.get("cursor")
                
                tools = self.fetch_handler.get_tools()
                # For now, return all tools (no pagination)
                result = {
                    "tools": [tool.model_dump() for tool in tools]
                    # "nextCursor" would be included if we had more tools
                }
            elif method == "tools/call":
                # Call a tool per MCP 2025-06-18
                if not params:
                    return JSONResponse(
                        content={
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32602,
                                "message": "Invalid params",
                                "data": "Missing params for tools/call"
                            },
                            "id": request_id
                        },
                        headers={
                            "Content-Type": "application/json",
                            "Mcp-Session-Id": self.transport.session_id,
                            "MCP-Protocol-Version": self.settings.protocol_version,
                        }
                    )
                    
                tool_name = params.get("name")
                if not tool_name:
                    return JSONResponse(
                        content={
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32602,
                                "message": "Invalid params",
                                "data": "Missing required parameter: name"
                            },
                            "id": request_id
                        },
                        headers={
                            "Content-Type": "application/json",
                            "Mcp-Session-Id": self.transport.session_id,
                            "MCP-Protocol-Version": self.settings.protocol_version,
                        }
                    )
                    
                tool_args = params.get("arguments", {})
                
                if tool_name == "fetch":
                    try:
                        contents = await self.fetch_handler.handle_fetch(tool_args)
                        result = {
                            "content": [content.model_dump() for content in contents],
                            "isError": False
                        }
                    except Exception as tool_error:
                        # Tool execution error (not protocol error)
                        result = {
                            "content": [{
                                "type": "text",
                                "text": f"Tool execution failed: {str(tool_error)}"
                            }],
                            "isError": True
                        }
                else:
                    return JSONResponse(
                        content={
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32602,
                                "message": "Invalid params",
                                "data": f"Unknown tool: {tool_name}"
                            },
                            "id": request_id
                        },
                        headers={
                            "Content-Type": "application/json",
                            "Mcp-Session-Id": self.transport.session_id,
                            "MCP-Protocol-Version": self.settings.protocol_version,
                        }
                    )
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
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Mcp-Session-Id": self.transport.session_id,
                        "MCP-Protocol-Version": self.settings.protocol_version,
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
                },
                headers={
                    "Content-Type": "application/json",
                    "Mcp-Session-Id": self.transport.session_id,
                    "MCP-Protocol-Version": self.settings.protocol_version,
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