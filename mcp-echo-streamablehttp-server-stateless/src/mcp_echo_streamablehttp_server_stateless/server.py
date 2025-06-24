"""Stateless MCP Echo Server implementing MCP 2025-06-18 StreamableHTTP transport specification."""

import os
import json
import logging
from typing import Any, Dict, Optional, List
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import StreamingResponse, JSONResponse, Response
from starlette.routing import Route
import asyncio
from contextlib import asynccontextmanager

# Configure logging
logger = logging.getLogger(__name__)


class MCPEchoServer:
    """Stateless MCP Echo Server implementation supporting multiple protocol versions."""
    
    PROTOCOL_VERSION = "2025-06-18"  # Default/preferred version
    SERVER_NAME = "mcp-echo-streamablehttp-server-stateless"
    SERVER_VERSION = "0.1.0"
    
    def __init__(self, debug: bool = False, supported_versions: Optional[List[str]] = None):
        """Initialize the echo server.
        
        Args:
            debug: Enable debug logging for message tracing
            supported_versions: List of supported protocol versions (defaults to ["2025-06-18"])
        """
        self.debug = debug
        self.supported_versions = supported_versions or [self.PROTOCOL_VERSION]
        if debug:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # Store request context per async task for stateless operation
        self._request_context = {}
        
        # Create the Starlette app
        self.app = self._create_app()
    
    def _create_app(self):
        """Create the Starlette application."""
        routes = [
            Route("/mcp", self.handle_mcp_request, methods=["POST", "GET", "OPTIONS"]),
        ]
        
        return Starlette(debug=self.debug, routes=routes)
    
    async def handle_mcp_request(self, request: Request):
        """Handle MCP requests according to 2025-06-18 specification."""
        # Handle CORS preflight
        if request.method == "OPTIONS":
            return Response(
                content="",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, MCP-Protocol-Version, Mcp-Session-Id",
                }
            )
        
        # Handle GET requests (for opening SSE streams)
        if request.method == "GET":
            # For stateless operation, we don't support GET
            return Response(
                content="GET not supported in stateless mode",
                status_code=405,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        # Validate Content-Type header for POST requests
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return JSONResponse(
                {"error": "Content-Type must be application/json"},
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        # Validate Accept header according to spec
        accept = request.headers.get("accept", "")
        if "application/json" not in accept or "text/event-stream" not in accept:
            return JSONResponse(
                {"error": "Client must accept both application/json and text/event-stream"},
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        # Check MCP-Protocol-Version header (required per spec)
        protocol_version = request.headers.get("mcp-protocol-version")
        if protocol_version and protocol_version not in self.supported_versions:
            return JSONResponse(
                {"error": f"Unsupported protocol version: {protocol_version}. Supported versions: {', '.join(self.supported_versions)}"},
                status_code=400,
                headers={"Access-Control-Allow-Origin": "*"}
            )
        
        # Store headers in context for this request
        task_id = id(asyncio.current_task())
        self._request_context[task_id] = dict(request.headers)
        
        try:
            # Parse JSON-RPC request
            try:
                body = await request.json()
            except Exception as e:
                return StreamingResponse(
                    self._sse_error_stream(-32700, "Parse error"),
                    media_type="text/event-stream",
                    headers={"Access-Control-Allow-Origin": "*"}
                )
            
            if self.debug:
                logger.debug(f"Request: {body}")
            
            # Handle batch requests
            if isinstance(body, list):
                # Batch requests are not supported in stateless mode
                return JSONResponse(
                    {"error": "Batch requests not supported in stateless mode"},
                    status_code=400,
                    headers={"Access-Control-Allow-Origin": "*"}
                )
            
            # Handle the JSON-RPC request
            response = await self._handle_jsonrpc_request(body)
            
            if self.debug:
                logger.debug(f"Response: {response}")
            
            # Check if this is a notification (no id field)
            if "id" not in body:
                # Notifications get 202 Accepted per spec
                return Response(
                    content="",
                    status_code=202,
                    headers={"Access-Control-Allow-Origin": "*"}
                )
            
            # Return SSE response for requests with id
            return StreamingResponse(
                self._sse_response_stream(response),
                media_type="text/event-stream",
                headers={"Access-Control-Allow-Origin": "*"}
            )
            
        finally:
            # Clean up request context
            self._request_context.pop(task_id, None)
    
    async def _handle_jsonrpc_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a JSON-RPC 2.0 request according to MCP 2025-06-18."""
        # Validate JSON-RPC structure
        if not isinstance(request, dict):
            return self._error_response(None, -32600, "Invalid Request")
        
        jsonrpc = request.get("jsonrpc")
        if jsonrpc != "2.0":
            return self._error_response(request.get("id"), -32600, "Invalid Request")
        
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        # Route to appropriate handler
        if method == "initialize":
            return await self._handle_initialize(params, request_id)
        elif method == "tools/list":
            return await self._handle_tools_list(params, request_id)
        elif method == "tools/call":
            return await self._handle_tools_call(params, request_id)
        else:
            return self._error_response(request_id, -32601, f"Method not found: {method}")
    
    async def _handle_initialize(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle initialize request."""
        client_protocol = params.get("protocolVersion", "")
        
        # Check if the client's requested version is supported
        if client_protocol not in self.supported_versions:
            return self._error_response(
                request_id, 
                -32602, 
                f"Unsupported protocol version: {client_protocol}. Supported versions: {', '.join(self.supported_versions)}"
            )
        
        # Use the client's requested version if supported
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": client_protocol,  # Echo back the client's version
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": self.SERVER_NAME,
                    "version": self.SERVER_VERSION
                }
            }
        }
    
    async def _handle_tools_list(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle tools/list request."""
        # MCP 2025-06-18: tools/list can have optional parameters but we don't use them
        tools = [
            {
                "name": "echo",
                "description": "Echo back the provided message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message to echo back"
                        }
                    },
                    "required": ["message"],
                    "additionalProperties": False
                }
            },
            {
                "name": "printHeader",
                "description": "Print all HTTP headers from the current request",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools
            }
        }
    
    async def _handle_tools_call(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return self._error_response(request_id, -32602, "Missing tool name")
        
        if tool_name == "echo":
            # Echo tool implementation
            message = arguments.get("message")
            if not isinstance(message, str):
                return self._error_response(request_id, -32602, "message must be a string")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": message
                        }
                    ]
                }
            }
            
        elif tool_name == "printHeader":
            # PrintHeader tool implementation
            headers_text = "HTTP Headers:\n"
            headers_text += "-" * 40 + "\n"
            
            # Get headers from the current task's context
            task_id = id(asyncio.current_task())
            headers = self._request_context.get(task_id, {})
            
            if headers:
                for key, value in sorted(headers.items()):
                    headers_text += f"{key}: {value}\n"
            else:
                headers_text += "No headers available (headers are captured per request)\n"
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": headers_text
                        }
                    ]
                }
            }
            
        else:
            return self._error_response(request_id, -32602, f"Unknown tool: {tool_name}")
    
    def _error_response(self, request_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
        """Create a JSON-RPC error response."""
        error = {
            "code": code,
            "message": message
        }
        if data is not None:
            error["data"] = data
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error
        }
    
    async def _sse_response_stream(self, response: Dict[str, Any]):
        """Generate SSE stream for a response."""
        # Format as SSE according to spec
        yield f"event: message\n"
        yield f"data: {json.dumps(response)}\n\n"
    
    async def _sse_error_stream(self, code: int, message: str):
        """Generate SSE stream for an error."""
        response = self._error_response("server-error", code, message)
        async for chunk in self._sse_response_stream(response):
            yield chunk
    
    def run(self, host: str = "0.0.0.0", port: int = 3000):
        """Run the HTTP server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        if self.debug:
            logger.info(f"Starting MCP Echo Server (protocol {self.PROTOCOL_VERSION}) on {host}:{port}")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="debug" if self.debug else "info"
        )


def create_app(debug: bool = False, supported_versions: Optional[List[str]] = None):
    """Create the ASGI application."""
    server = MCPEchoServer(debug=debug, supported_versions=supported_versions)
    return server.app