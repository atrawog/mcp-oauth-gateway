"""MCP fetch server with native Streamable HTTP transport."""

import asyncio
import json
import logging
from typing import Any

import uvloop
from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from fastapi.responses import JSONResponse
from mcp.server import Server
from mcp.types import ImageContent
from mcp.types import TextContent
from pydantic import ConfigDict
from pydantic import Field
from pydantic_settings import BaseSettings

from .fetch_handler import FetchHandler
from .transport import StreamableHTTPTransport


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
    fetch_allowed_schemes: list[str] = Field(default=["http", "https"], description="Allowed URL schemes")
    fetch_max_redirects: int = Field(default=5, description="Max redirects")
    fetch_default_user_agent: str = Field(default="ModelContextProtocol/1.0 (Fetch Server)", description="User agent")

    # Transport settings
    fetch_enable_sse: bool = Field(default=False, description="SSE support for future implementation")

    model_config = ConfigDict(env_prefix="MCP_", env_file=".env", extra="allow")


class StreamableHTTPServer:
    """MCP server with native Streamable HTTP transport."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.transport = StreamableHTTPTransport()
        self.fetch_handler = FetchHandler(
            allowed_schemes=self.settings.fetch_allowed_schemes,
            max_redirects=self.settings.fetch_max_redirects,
        )

        # Create MCP server
        self.server = Server(self.settings.server_name)

        # Register tools
        self._register_tools()

        # Track active sessions
        self.sessions: dict[str, Any] = {}

    def _register_tools(self):
        """Register fetch tool with MCP server."""

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent | ImageContent]:
            """Handle tool calls."""
            if name == "fetch":
                return await self.fetch_handler.handle_fetch(arguments)
            raise ValueError(f"Unknown tool: {name}")

        @self.server.list_tools()
        async def list_tools() -> list[dict[str, Any]]:
            """List available tools."""
            tools = self.fetch_handler.get_tools()
            # Filter out None values manually since exclude_none doesn't work for explicit None values
            return [{k: v for k, v in tool.model_dump().items() if v is not None} for tool in tools]

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

        # ⚡ DIVINE DECREE: CORS HANDLED BY TRAEFIK MIDDLEWARE! ⚡
        # MCP services must maintain "pure protocol innocence" per CLAUDE.md
        # OPTIONS requests flow through Traefik CORS middleware

        # ⚡ DIVINE DECREE: NO AUTHENTICATION IN MCP SERVICES! ⚡
        # Authentication is handled by Traefik via ForwardAuth middleware
        # MCP services must maintain "pure protocol innocence" per CLAUDE.md
        # The holy trinity separation demands it!

        # Check MCP protocol version header if provided
        mcp_version = headers.get("mcp-protocol-version", headers.get("MCP-Protocol-Version"))
        if mcp_version and mcp_version != self.settings.protocol_version:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Unsupported protocol version",
                    "message": (
                        f"Server only supports MCP version: {self.settings.protocol_version}, got {mcp_version}"
                    ),
                },
            )

        # For stateless operation, process request directly
        if method == "POST" and path == "/mcp":
            return await self._handle_stateless_request(headers, body)
        if method == "GET" and path == "/mcp":
            # SSE endpoint - not implemented yet
            return JSONResponse(
                status_code=501,
                content={
                    "error": "Not implemented",
                    "message": "Server-Sent Events not yet supported",
                },
            )
        return JSONResponse(
            status_code=404,
            content={"error": "Not found", "message": f"Path {path} not found"},
        )

    async def _handle_stateless_request(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> Response:
        """Handle stateless JSON-RPC request."""
        # Note: Be lenient with content type as long as body is valid JSON
        # This allows clients that may send incorrect content types

        # Parse and validate JSON-RPC request
        data, error_response = self._parse_json_rpc_request(body)
        if error_response:
            return error_response

        # Handle the request
        method = data.get("method")
        request_id = data.get("id")
        params = data.get("params", {})

        try:
            result = await self._dispatch_method(method, params, request_id)
            if isinstance(result, JSONResponse):
                return result

            # Return success response
            return self._create_json_rpc_response(result, request_id)

        except Exception as e:
            # Return error response
            return self._create_json_rpc_error(-32603, "Internal error", str(e), request_id)

    def _parse_json_rpc_request(self, body: bytes) -> tuple[dict[str, Any] | None, JSONResponse | None]:
        """Parse and validate JSON-RPC request."""
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            return None, JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error", "data": str(e)},
                    "id": None,
                },
            )

        # Validate JSON-RPC structure
        if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
            return None, JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request",
                        "data": "Missing or invalid jsonrpc version",
                    },
                    "id": data.get("id"),
                },
            )

        return data, None

    async def _dispatch_method(
        self,
        method: str,
        params: dict[str, Any],
        request_id: Any,
    ) -> dict[str, Any] | JSONResponse:
        """Dispatch method to appropriate handler."""
        if method == "initialize":
            return self._handle_initialize(params, request_id)
        if method == "tools/list":
            return self._handle_tools_list(params)
        if method == "tools/call":
            return await self._handle_tools_call(params, request_id)
        return self._create_json_rpc_error(-32601, "Method not found", f"Unknown method: {method}", request_id)

    def _handle_initialize(self, params: dict[str, Any], request_id: Any) -> dict[str, Any] | JSONResponse:
        """Handle initialize method."""
        client_protocol = params.get("protocolVersion", self.settings.protocol_version)

        # Check if client protocol matches server version
        if client_protocol != self.settings.protocol_version:
            return self._create_json_rpc_error(
                -32602,
                "Invalid params",
                f"Unsupported protocol version: {client_protocol}. Server supports: {self.settings.protocol_version}",
                request_id,
            )

        return {
            "protocolVersion": self.settings.protocol_version,
            "capabilities": {
                "tools": {},  # We support tools
                "prompts": None,
                "resources": None,
                "logging": None,
            },
            "serverInfo": {
                "name": self.settings.server_name,
                "version": self.settings.server_version,
            },
        }

    def _handle_tools_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/list method."""
        # Support pagination via cursor parameter
        params.get("cursor")  # For future use

        tools = self.fetch_handler.get_tools()
        # For now, return all tools (no pagination)
        return {
            "tools": [tool.model_dump() for tool in tools],
            # "nextCursor" would be included if we had more tools
        }

    async def _handle_tools_call(self, params: dict[str, Any], request_id: Any) -> dict[str, Any] | JSONResponse:
        """Handle tools/call method."""
        if not params:
            return self._create_json_rpc_error(-32602, "Invalid params", "Missing params for tools/call", request_id)

        tool_name = params.get("name")
        if not tool_name:
            return self._create_json_rpc_error(-32602, "Invalid params", "Missing required parameter: name", request_id)

        tool_args = params.get("arguments", {})

        if tool_name == "fetch":
            try:
                contents = await self.fetch_handler.handle_fetch(tool_args)
                return {
                    "content": [content.model_dump() for content in contents],
                    "isError": False,
                }
            except Exception as tool_error:
                # Tool execution error (not protocol error)
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Tool execution failed: {tool_error!s}",
                        },
                    ],
                    "isError": True,
                }
        else:
            return self._create_json_rpc_error(-32602, "Invalid params", f"Unknown tool: {tool_name}", request_id)

    def _create_json_rpc_response(self, result: dict[str, Any], request_id: Any) -> JSONResponse:
        """Create a JSON-RPC success response."""
        return JSONResponse(
            content={"jsonrpc": "2.0", "result": result, "id": request_id},
            headers={
                "Content-Type": "application/json",
                "Mcp-Session-Id": self.transport.session_id,
                "MCP-Protocol-Version": self.settings.protocol_version,
            },
        )

    def _create_json_rpc_error(self, code: int, message: str, data: str, request_id: Any) -> JSONResponse:
        """Create a JSON-RPC error response."""
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": code,
                    "message": message,
                    "data": data,
                },
                "id": request_id,
            },
            headers={
                "Content-Type": "application/json",
                "Mcp-Session-Id": self.transport.session_id,
                "MCP-Protocol-Version": self.settings.protocol_version,
            },
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

        return app


def create_server(settings: Settings | None = None) -> StreamableHTTPServer:
    """Create and configure MCP fetch server."""
    return StreamableHTTPServer(settings)


# Create default app for ASGI servers
app = create_server().create_app()
