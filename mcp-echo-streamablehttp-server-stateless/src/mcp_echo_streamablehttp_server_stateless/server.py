"""Stateless MCP Echo Server implementing MCP 2025-06-18 StreamableHTTP transport specification."""

import asyncio
import base64
import binascii
import json
import logging
import os
import platform
import time
import uuid
from datetime import UTC
from datetime import datetime
from typing import Any

import psutil
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.responses import StreamingResponse
from starlette.routing import Route


# Constants
JWT_PARTS_COUNT = 3
PERFORMANCE_EXCELLENT_THRESHOLD = 0.010  # 10ms
PERFORMANCE_GOOD_THRESHOLD = 0.050  # 50ms
PERFORMANCE_ACCEPTABLE_THRESHOLD = 0.100  # 100ms


# Configure logging
logger = logging.getLogger(__name__)


class MCPEchoServer:
    """Stateless MCP Echo Server implementation supporting multiple protocol versions."""

    PROTOCOL_VERSION = "2025-06-18"  # Default/preferred version
    SERVER_NAME = "mcp-echo-streamablehttp-server-stateless"
    SERVER_VERSION = "0.1.0"

    def __init__(self, debug: bool = False, supported_versions: list[str] | None = None):
        """Initialize the echo server.

        Args:
            debug: Enable debug logging for message tracing
            supported_versions: List of supported protocol versions (defaults to ["2025-06-18"])

        """
        self.debug = debug
        self.supported_versions = supported_versions or [self.PROTOCOL_VERSION]
        if debug:
            logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

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
        # ⚡ DIVINE DECREE: CORS HANDLED BY TRAEFIK MIDDLEWARE! ⚡
        # MCP services must maintain "pure protocol innocence" per CLAUDE.md
        # All CORS headers are set by Traefik, not by the service

        # Log Traefik forwarded headers for debugging when debug mode is enabled
        if self.debug:
            start_time = time.time()

            traefik_headers = {
                "x-real-ip": request.headers.get("x-real-ip"),
                "x-forwarded-for": request.headers.get("x-forwarded-for"),
                "x-forwarded-host": request.headers.get("x-forwarded-host"),
                "x-forwarded-proto": request.headers.get("x-forwarded-proto"),
                "x-forwarded-port": request.headers.get("x-forwarded-port"),
                "x-forwarded-server": request.headers.get("x-forwarded-server"),
                "x-user-id": request.headers.get("x-user-id"),
                "x-user-name": request.headers.get("x-user-name"),
                "x-auth-token": "***redacted***" if request.headers.get("x-auth-token") else None,
                "user-agent": request.headers.get("user-agent"),
                "host": request.headers.get("host"),
            }

            # Filter out None values
            traefik_headers = {k: v for k, v in traefik_headers.items() if v is not None}

            # Create JSON data for request
            request_data = {
                "type": "mcp_echo_stateless_request",
                "method": request.method,
                "path": str(request.url.path),
                "real_ip": traefik_headers.get("x-real-ip", "unknown"),
                "forwarded_for": traefik_headers.get("x-forwarded-for", "unknown"),
                "forwarded_host": traefik_headers.get("x-forwarded-host", "unknown"),
                "host": traefik_headers.get("host", "unknown"),
                "user_agent": traefik_headers.get("user-agent", "unknown"),
                "user_id": traefik_headers.get("x-user-id", "unknown"),
                "user_name": traefik_headers.get("x-user-name", "unknown"),
                "forwarded_proto": traefik_headers.get("x-forwarded-proto", "unknown"),
                "forwarded_port": traefik_headers.get("x-forwarded-port", "unknown"),
                "timestamp": start_time,
            }

            # Store start time and request data in task context for response logging
            task_id = id(asyncio.current_task())
            if not hasattr(self, "_request_timing"):
                self._request_timing = {}
            self._request_timing[task_id] = {
                "start_time": start_time,
                "request_data": request_data,
                "traefik_headers": traefik_headers,
            }

            # Log request with Traefik headers
            logger.info(
                "MCP-ECHO STATELESS REQUEST - Method: %s | "
                "Path: %s | "
                "Real-IP: %s | "
                "Forwarded-For: %s | "
                "User: %s | "
                "Host: %s | "
                "User-Agent: %s | "
                "JSON: %s",
                request.method,
                request.url.path,
                traefik_headers.get("x-real-ip", "unknown"),
                traefik_headers.get("x-forwarded-for", "unknown"),
                traefik_headers.get("x-user-name", "unknown"),
                traefik_headers.get("x-forwarded-host", traefik_headers.get("host", "unknown")),
                traefik_headers.get("user-agent", "unknown"),
                json.dumps(request_data),
            )

        # Handle the request
        if request.method == "GET":
            response = self._handle_sse_stream(request)
        else:
            # POST method handling
            response = await self._handle_post_request(request)

        # Log response if debug mode is enabled
        if self.debug and hasattr(self, "_request_timing"):
            task_id = id(asyncio.current_task())
            timing_data = self._request_timing.get(task_id)
            if timing_data:
                end_time = time.time()
                duration = round(end_time - timing_data["start_time"], 3)

                # Create response data
                response_data = {
                    "type": "mcp_echo_stateless_response",
                    "status": getattr(response, "status_code", 200),
                    "duration_seconds": duration,
                    "path": timing_data["request_data"]["path"],
                    "real_ip": timing_data["request_data"]["real_ip"],
                    "method": timing_data["request_data"]["method"],
                    "user_name": timing_data["request_data"]["user_name"],
                    "timestamp": end_time,
                }

                # Log response
                logger.info(
                    "MCP-ECHO STATELESS RESPONSE - Status: %s | "
                    "Time: %ss | "
                    "Path: %s | "
                    "Real-IP: %s | "
                    "User: %s | "
                    "JSON: %s",
                    getattr(response, "status_code", 200),
                    duration,
                    timing_data["request_data"]["path"],
                    timing_data["request_data"]["real_ip"],
                    timing_data["request_data"]["user_name"],
                    json.dumps(response_data),
                )

                # Clean up timing data
                del self._request_timing[task_id]

        return response

    def _handle_sse_stream(self, request: Request) -> StreamingResponse:
        """Handle GET requests for SSE streams."""
        # Use client's session ID if provided, otherwise generate a new one
        # Note: Starlette normalizes headers to lowercase
        session_id = request.headers.get("mcp-session-id") or str(uuid.uuid4())

        if self.debug:
            logger.debug("GET request headers: %s", dict(request.headers))
            logger.debug("Session ID from header: %s", request.headers.get("mcp-session-id"))
            logger.debug("Using session ID: %s", session_id)

        async def sse_stream():
            # Send a keep-alive comment to establish the connection
            yield "event: ping\ndata: {}\n\n"
            # Keep connection open but don't send more data (stateless)

        return StreamingResponse(
            sse_stream(),
            media_type="text/event-stream",
            headers={
                "Mcp-Session-Id": session_id,
                "Access-Control-Allow-Origin": "*",  # SSE endpoints typically allow all origins
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    async def _handle_post_request(self, request: Request) -> Response:
        """Handle POST requests with validation and processing."""
        # Validate headers
        validation_error = self._validate_post_headers(request)
        if validation_error:
            return validation_error

        # Store request context
        task_id = id(asyncio.current_task())
        self._request_context[task_id] = {
            "headers": dict(request.headers),
            "start_time": time.time(),
            "method": request.method,
            "url": str(request.url),
        }

        try:
            # Parse and process request
            return await self._process_json_rpc_request(request)
        finally:
            # Clean up request context
            self._request_context.pop(task_id, None)

    def _validate_post_headers(self, request: Request) -> JSONResponse | None:
        """Validate required headers for POST requests."""
        # Validate Content-Type
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return JSONResponse(
                {"error": "Content-Type must be application/json"},
                status_code=400,
            )

        # Validate Accept header - client must accept at least one supported format
        accept = request.headers.get("accept", "")
        if not accept:
            # If no Accept header, default to accepting JSON
            accept = "application/json"

        # Check if client accepts at least one of our supported formats
        accepts_json = "application/json" in accept or "*/*" in accept
        accepts_sse = "text/event-stream" in accept

        if not accepts_json and not accepts_sse:
            return JSONResponse(
                {"error": "Client must accept either application/json or text/event-stream"},
                status_code=400,
            )

        # Check MCP-Protocol-Version
        protocol_version = request.headers.get("mcp-protocol-version")
        if protocol_version and protocol_version not in self.supported_versions:
            return JSONResponse(
                {
                    "error": f"Unsupported protocol version: {protocol_version}. Supported versions: {', '.join(self.supported_versions)}",
                },
                status_code=400,
            )

        return None

    async def _process_json_rpc_request(self, request: Request) -> Response:
        """Process the JSON-RPC request and return appropriate response."""
        # Determine response format based on Accept header
        accept = request.headers.get("accept", "application/json")
        # IMPORTANT: VS Code expects JSON responses for POST requests, even when it sends Accept: text/event-stream
        # Only use SSE for GET requests (polling), never for POST requests (RPC calls)
        use_sse = False  # Always use JSON for POST requests

        try:
            body = await request.json()
        except (json.JSONDecodeError, ValueError, TypeError):
            if use_sse:
                return StreamingResponse(
                    self._sse_error_stream(-32700, "Parse error"),
                    media_type="text/event-stream",
                )
            return JSONResponse(
                self._error_response(None, -32700, "Parse error"),
                status_code=400,
            )

        if self.debug:
            logger.debug("Request: %s", body)
            logger.debug("Accept header received: '%s'", accept)

            # Detailed SSE decision logging
            accepts_json = "application/json" in accept or "*/*" in accept
            accepts_sse = "text/event-stream" in accept

            logger.debug("Client accepts JSON: %s", accepts_json)
            logger.debug("Client accepts SSE (text/event-stream): %s", accepts_sse)
            logger.debug("Using SSE: %s", use_sse)

            if use_sse:
                logger.debug(
                    "DECISION: Using Server-Sent Events (SSE) format because client explicitly accepts 'text/event-stream'",
                )
                logger.debug(
                    "NOTE: SSE responses use 'event: message\\ndata: {json}\\n\\n' format which some clients may not parse correctly",
                )
            else:
                logger.debug("DECISION: Using standard JSON response format (client did not request SSE)")

        # Handle batch requests
        if isinstance(body, list):
            return JSONResponse(
                {"error": "Batch requests not supported in stateless mode"},
                status_code=400,
            )

        # Handle the JSON-RPC request
        response = await self._handle_jsonrpc_request(body)

        if self.debug:
            logger.debug("Response: %s", response)

        # Check if this is a notification
        if "id" not in body and "error" not in response:
            return Response(content="", status_code=202)

        # Use client's session ID if provided, otherwise generate a new one
        # VS Code and other MCP clients expect this header even for stateless services
        session_id = request.headers.get("mcp-session-id") or str(uuid.uuid4())

        if self.debug:
            logger.debug("POST request headers: %s", dict(request.headers))
            logger.debug("Session ID from header: %s", request.headers.get("mcp-session-id"))
            logger.debug("Using session ID: %s", session_id)

        # Return response in appropriate format
        response_headers = {"Mcp-Session-Id": session_id}

        if use_sse:
            if self.debug:
                logger.debug("SENDING RESPONSE: Using SSE format (text/event-stream)")
                logger.debug("Response will be formatted as: event: message\\ndata: <json>\\n\\n")
                logger.debug("Including Mcp-Session-Id header: %s", session_id)
            return StreamingResponse(
                self._sse_response_stream(response),
                media_type="text/event-stream",
                headers=response_headers,
            )
        # Return direct JSON response
        if self.debug:
            logger.debug("SENDING RESPONSE: Using standard JSON format (application/json)")
            logger.debug("Including Mcp-Session-Id header: %s", session_id)
        return JSONResponse(response, headers=response_headers)

    async def _handle_jsonrpc_request(self, request: dict[str, Any]) -> dict[str, Any]:
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
        if method == "notifications/initialized":
            # Handle initialized notification - just acknowledge it
            # This is a notification (no id), so return success with no id
            return {"jsonrpc": "2.0"}
        if method == "tools/list":
            return await self._handle_tools_list(params, request_id)
        if method == "tools/call":
            return await self._handle_tools_call(params, request_id)
        return self._error_response(request_id, -32601, f"Method not found: {method}")

    async def _handle_initialize(self, params: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Handle initialize request."""
        client_protocol = params.get("protocolVersion", "")

        # Check if the client's requested version is supported
        if client_protocol not in self.supported_versions:
            return self._error_response(
                request_id,
                -32602,
                f"Unsupported protocol version: {client_protocol}. Supported versions: {', '.join(self.supported_versions)}",
            )

        # Use the client's requested version if supported
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": client_protocol,  # Echo back the client's version
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {"name": self.SERVER_NAME, "version": self.SERVER_VERSION},
            },
        }

    async def _handle_tools_list(self, params: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Handle tools/list request."""
        # MCP 2025-06-18: tools/list can have optional parameters but we don't use them
        tools = [
            {
                "name": "echo",
                "description": "Echo back the provided message",
                "inputSchema": {
                    "type": "object",
                    "properties": {"message": {"type": "string", "description": "The message to echo back"}},
                    "required": ["message"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "printHeader",
                "description": "Print all HTTP headers from the current request",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "bearerDecode",
                "description": "Decode JWT Bearer token from Authorization header (no signature verification)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "includeRaw": {"type": "boolean", "description": "Include raw token parts", "default": False},
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "authContext",
                "description": "Display complete authentication context from request",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "requestTiming",
                "description": "Show request timing and performance metrics",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "corsAnalysis",
                "description": "Analyze CORS configuration and requirements",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "environmentDump",
                "description": "Display sanitized environment configuration",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "showSecrets": {
                            "type": "boolean",
                            "description": "Show first/last 4 chars of secrets",
                            "default": False,
                        },
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "healthProbe",
                "description": "Perform deep health check of service and dependencies",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "whoIStheGOAT",
                "description": "Employs cutting-edge artificial intelligence to perform comprehensive analysis of global software engineering excellence metrics using proprietary deep learning models",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        ]

        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}

    async def _handle_tools_call(self, params: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            return self._error_response(request_id, -32602, "Missing tool name")

        # Map tool names to their handler methods
        tool_handlers = {
            "echo": self._handle_echo_tool,
            "printHeader": self._handle_print_header_tool,
            "bearerDecode": self._handle_bearer_decode,
            "authContext": self._handle_auth_context,
            "requestTiming": self._handle_request_timing,
            "corsAnalysis": self._handle_cors_analysis,
            "environmentDump": self._handle_environment_dump,
            "healthProbe": self._handle_health_probe,
            "whoIStheGOAT": self._handle_who_is_the_goat,
        }

        handler = tool_handlers.get(tool_name)
        if not handler:
            return self._error_response(request_id, -32602, f"Unknown tool: {tool_name}")

        return await handler(arguments, request_id)

    async def _handle_echo_tool(self, arguments: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Handle the echo tool."""
        message = arguments.get("message")
        if not isinstance(message, str):
            return self._error_response(request_id, -32602, "message must be a string")

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": message}]}}

    async def _handle_print_header_tool(self, arguments: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Handle the printHeader tool - shows ALL HTTP headers from the request."""
        headers_text = "HTTP Headers:\n"
        headers_text += "=" * 50 + "\n"

        # Get headers from the current task's context
        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        headers = context.get("headers", {})

        if headers:
            # Separate headers into categories for better organization
            traefik_headers = {}
            auth_headers = {}
            regular_headers = {}

            for key, value in headers.items():
                key_lower = key.lower()
                if key_lower.startswith(("x-forwarded-", "x-real-", "x-original-")):
                    traefik_headers[key] = value
                elif key_lower.startswith(("x-user-", "x-auth-", "authorization")):
                    # Only redact the value part of authorization headers, not x-auth-token header name
                    if key_lower == "authorization" and value.lower().startswith("bearer "):
                        auth_headers[key] = f"Bearer ***...{value[-10:]}" if len(value) > 17 else "Bearer ***"
                    elif "token" in key_lower and key_lower != "x-auth-token":
                        auth_headers[key] = "***redacted***"
                    else:
                        auth_headers[key] = value
                else:
                    regular_headers[key] = value

            # Create JSON data for headers
            headers_data = {
                "type": "header_analysis",
                "total_headers": len(headers),
                "traefik_headers": traefik_headers,
                "auth_headers": dict(auth_headers),
                "regular_headers": regular_headers,
                "counts": {"traefik": len(traefik_headers), "auth": len(auth_headers), "regular": len(regular_headers)},
            }

            # Display ALL headers organized by category
            # Display Traefik headers first
            if traefik_headers:
                headers_text += "TRAEFIK FORWARDED HEADERS:\n"
                headers_text += "-" * 30 + "\n"
                for key, value in sorted(traefik_headers.items()):
                    headers_text += f"  {key}: {value}\n"
                headers_text += "\n"

            # Display auth headers second
            if auth_headers:
                headers_text += "AUTHENTICATION HEADERS:\n"
                headers_text += "-" * 30 + "\n"
                for key, value in sorted(auth_headers.items()):
                    headers_text += f"  {key}: {value}\n"
                headers_text += "\n"

            # Display ALL other headers (including accept, content-type, etc.)
            if regular_headers:
                headers_text += "REQUEST HEADERS:\n"
                headers_text += "-" * 30 + "\n"
                for key, value in sorted(regular_headers.items()):
                    headers_text += f"  {key}: {value}\n"
                headers_text += "\n"

            # Add complete alphabetical list of ALL headers
            headers_text += "ALL HEADERS (Alphabetical):\n"
            headers_text += "-" * 30 + "\n"
            all_headers = {}
            all_headers.update(traefik_headers)
            all_headers.update(auth_headers)
            all_headers.update(regular_headers)
            for key, value in sorted(all_headers.items()):
                headers_text += f"  {key}: {value}\n"

            # Add summary
            headers_text += "\nSUMMARY:\n"
            headers_text += f"  Total Headers: {len(headers)}\n"
            headers_text += f"  Traefik Headers: {len(traefik_headers)}\n"
            headers_text += f"  Auth Headers: {len(auth_headers)}\n"
            headers_text += f"  Request Headers: {len(regular_headers)}\n"

            if self.debug:
                headers_text += f"\nDEBUG JSON: {json.dumps(headers_data)}\n"

        else:
            headers_text += "No headers available (headers are captured per request)\n"
            headers_data = {"type": "header_analysis", "error": "no_headers_available"}
            if self.debug:
                headers_text += f"DEBUG JSON: {json.dumps(headers_data)}\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": headers_text}]}}

    def _error_response(self, request_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
        """Create a JSON-RPC error response."""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data

        return {"jsonrpc": "2.0", "id": request_id, "error": error}

    async def _handle_bearer_decode(self, arguments: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Decode JWT Bearer token from Authorization header."""
        include_raw = arguments.get("includeRaw", False)

        # Get authorization header
        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        headers = context.get("headers", {})
        auth_header = headers.get("authorization", "")

        result_text = "Bearer Token Analysis\n" + "=" * 40 + "\n\n"

        if not auth_header:
            result_text += "❌ No Authorization header found\n"
        elif not auth_header.lower().startswith("bearer "):
            result_text += f"❌ Authorization header is not Bearer type: {auth_header[:20]}...\n"
        else:
            token = auth_header[7:]  # Remove 'Bearer ' prefix

            try:
                # Split JWT parts
                parts = token.split(".")
                if len(parts) != JWT_PARTS_COUNT:
                    result_text += f"❌ Invalid JWT format (expected {JWT_PARTS_COUNT} parts, got {len(parts)})\n"
                else:
                    # Decode header
                    header_data = parts[0]
                    # Add padding if needed
                    header_padded = header_data + "=" * (4 - len(header_data) % 4)
                    header_json = json.loads(base64.urlsafe_b64decode(header_padded))

                    # Decode payload
                    payload_data = parts[1]
                    payload_padded = payload_data + "=" * (4 - len(payload_data) % 4)
                    payload_json = json.loads(base64.urlsafe_b64decode(payload_padded))

                    result_text += "✅ Valid JWT structure\n\n"

                    # Header information
                    result_text += "Header:\n"
                    result_text += f"  Algorithm: {header_json.get('alg', 'unknown')}\n"
                    result_text += f"  Type: {header_json.get('typ', 'unknown')}\n"
                    if "kid" in header_json:
                        result_text += f"  Key ID: {header_json['kid']}\n"
                    result_text += "\n"

                    # Payload information
                    result_text += "Payload:\n"

                    # Standard claims
                    if "iss" in payload_json:
                        result_text += f"  Issuer: {payload_json['iss']}\n"
                    if "sub" in payload_json:
                        result_text += f"  Subject: {payload_json['sub']}\n"
                    if "aud" in payload_json:
                        result_text += f"  Audience: {payload_json['aud']}\n"
                    if "jti" in payload_json:
                        result_text += f"  JWT ID: {payload_json['jti']}\n"

                    # Time claims
                    current_time = int(time.time())
                    if "iat" in payload_json:
                        iat = payload_json["iat"]
                        iat_dt = datetime.fromtimestamp(iat, tz=UTC)
                        result_text += f"  Issued At: {iat_dt.isoformat()} ({int(current_time - iat)}s ago)\n"

                    if "exp" in payload_json:
                        exp = payload_json["exp"]
                        exp_dt = datetime.fromtimestamp(exp, tz=UTC)
                        if exp < current_time:
                            result_text += (
                                f"  Expires: {exp_dt.isoformat()} (EXPIRED {int(current_time - exp)}s ago!)\n"
                            )
                        else:
                            result_text += f"  Expires: {exp_dt.isoformat()} (in {int(exp - current_time)}s)\n"

                    if "nbf" in payload_json:
                        nbf = payload_json["nbf"]
                        nbf_dt = datetime.fromtimestamp(nbf, tz=UTC)
                        if nbf > current_time:
                            result_text += (
                                f"  Not Before: {nbf_dt.isoformat()} (NOT YET VALID - {int(nbf - current_time)}s)\n"
                            )
                        else:
                            result_text += f"  Not Before: {nbf_dt.isoformat()} (valid)\n"

                    # Custom claims
                    custom_claims = {
                        k: v
                        for k, v in payload_json.items()
                        if k not in ["iss", "sub", "aud", "exp", "nbf", "iat", "jti"]
                    }

                    if custom_claims:
                        result_text += "\nCustom Claims:\n"
                        for key, value in custom_claims.items():
                            result_text += f"  {key}: {json.dumps(value)}\n"

                    # Signature info
                    result_text += f"\nSignature: {'Present' if parts[2] else 'Missing'}\n"

                    if include_raw:
                        result_text += "\nRaw Parts:\n"
                        result_text += f"  Header: {parts[0][:50]}...\n"
                        result_text += f"  Payload: {parts[1][:50]}...\n"
                        result_text += f"  Signature: {parts[2][:50]}...\n"

            except (json.JSONDecodeError, ValueError, binascii.Error) as e:
                result_text += f"❌ Error decoding JWT: {e!s}\n"
                result_text += f"Token preview: {token[:50]}...\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    async def _handle_auth_context(self, arguments: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Display complete authentication context."""
        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        headers = context.get("headers", {})

        result_text = "Authentication Context Analysis\n" + "=" * 40 + "\n\n"

        # Bearer token info
        auth_header = headers.get("authorization", "")
        if auth_header:
            result_text += "Bearer Token:\n"
            if auth_header.lower().startswith("bearer "):
                token = auth_header[7:]
                result_text += f"  ✅ Present (length: {len(token)})\n"
                # Try to decode
                try:
                    parts = token.split(".")
                    if len(parts) == JWT_PARTS_COUNT:
                        payload_padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
                        payload_json = json.loads(base64.urlsafe_b64decode(payload_padded))
                        if "sub" in payload_json:
                            result_text += f"  Subject: {payload_json['sub']}\n"
                        if "client_id" in payload_json:
                            result_text += f"  Client ID: {payload_json['client_id']}\n"
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    # JWT decode errors are expected for invalid tokens - this is a diagnostic tool
                    logging.debug("Failed to decode JWT payload: %s", e)
            else:
                result_text += f"  ❌ Wrong type: {auth_header[:30]}...\n"
        else:
            result_text += "Bearer Token:\n  ❌ Not present\n"

        result_text += "\n"

        # OAuth headers
        result_text += "OAuth Headers:\n"
        oauth_headers = {
            "x-user-id": "User ID",
            "x-user-name": "User Name",
            "x-auth-token": "Auth Token",
            "x-client-id": "Client ID",
            "x-oauth-client": "OAuth Client",
        }

        found_oauth = False
        for header_key, display_name in oauth_headers.items():
            if header_key in headers:
                result_text += f"  {display_name}: {headers[header_key]}\n"
                found_oauth = True

        if not found_oauth:
            result_text += "  ❌ No OAuth headers found\n"

        result_text += "\n"

        # Session info
        result_text += "Session Information:\n"
        session_id = headers.get("mcp-session-id", "")
        if session_id:
            result_text += f"  MCP Session ID: {session_id}\n"
        else:
            result_text += "  MCP Session ID: Not present\n"

        # Cookie info
        cookies = headers.get("cookie", "")
        if cookies:
            result_text += f"  Cookies: Present ({len(cookies.split(';'))} cookies)\n"
            # Look for auth-related cookies
            for cookie in cookies.split(";"):
                stripped_cookie = cookie.strip()
                if any(auth_word in stripped_cookie.lower() for auth_word in ["auth", "session", "token"]):
                    name = stripped_cookie.split("=")[0] if "=" in stripped_cookie else stripped_cookie
                    result_text += f"    - {name}\n"
        else:
            result_text += "  Cookies: None\n"

        result_text += "\n"

        # Request origin
        result_text += "Request Origin:\n"
        result_text += f"  Host: {headers.get('host', 'unknown')}\n"
        result_text += f"  Origin: {headers.get('origin', 'not specified')}\n"
        result_text += f"  Referer: {headers.get('referer', 'not specified')}\n"
        result_text += f"  User-Agent: {headers.get('user-agent', 'unknown')}\n"

        # Security status
        result_text += "\nSecurity Status:\n"
        if auth_header and auth_header.lower().startswith("bearer "):
            result_text += "  ✅ Bearer authentication present\n"
        else:
            result_text += "  ❌ No bearer authentication\n"

        if "https" in headers.get("x-forwarded-proto", "") or "https" in str(context.get("url", "")):
            result_text += "  ✅ HTTPS connection\n"
        else:
            result_text += "  ⚠️  Non-HTTPS connection\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    async def _handle_request_timing(self, arguments: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Show request timing metrics."""
        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        start_time = context.get("start_time", time.time())
        current_time = time.time()
        elapsed = current_time - start_time

        result_text = "Request Timing Analysis\n" + "=" * 40 + "\n\n"

        # Basic timing
        result_text += "Timing:\n"
        result_text += f"  Request received: {datetime.fromtimestamp(start_time, tz=UTC).isoformat()}\n"
        result_text += f"  Current time: {datetime.fromtimestamp(current_time, tz=UTC).isoformat()}\n"
        result_text += f"  Elapsed: {elapsed * 1000:.2f}ms\n"

        result_text += "\n"

        # Request details
        result_text += "Request Details:\n"
        result_text += f"  Method: {context.get('method', 'unknown')}\n"
        result_text += f"  URL: {context.get('url', 'unknown')}\n"

        # Performance indicators
        result_text += "\nPerformance Indicators:\n"
        if elapsed < PERFORMANCE_EXCELLENT_THRESHOLD:
            result_text += "  ⚡ Excellent (<10ms)\n"
        elif elapsed < PERFORMANCE_GOOD_THRESHOLD:
            result_text += "  ✅ Good (<50ms)\n"
        elif elapsed < PERFORMANCE_ACCEPTABLE_THRESHOLD:
            result_text += "  ⚠️  Acceptable (<100ms)\n"
        else:
            result_text += "  ❌ Slow (>100ms)\n"

        # System info
        result_text += "\nSystem Performance:\n"
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            result_text += f"  CPU Usage: {cpu_percent}%\n"
            result_text += f"  Memory Usage: {memory.percent}%\n"
            result_text += f"  Available Memory: {memory.available / 1024 / 1024 / 1024:.2f}GB\n"
        except:
            result_text += "  Unable to get system metrics\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    async def _handle_cors_analysis(self, arguments: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Analyze CORS configuration."""
        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        headers = context.get("headers", {})
        method = context.get("method", "")

        result_text = "CORS Configuration Analysis\n" + "=" * 40 + "\n\n"

        # CORS Configuration Notice
        result_text += "⚡ DIVINE DECREE: CORS IS HANDLED BY TRAEFIK! ⚡\n"
        result_text += "This MCP service does not set CORS headers.\n"
        result_text += "All CORS headers are managed by Traefik middleware.\n\n"

        # Request CORS headers
        result_text += "Request Headers:\n"
        origin = headers.get("origin", "")
        if origin:
            result_text += f"  Origin: {origin}\n"
        else:
            result_text += "  Origin: Not present (same-origin request)\n"

        if method == "OPTIONS":
            result_text += "  ✅ This is a CORS preflight request\n"

            # Check preflight headers
            ac_method = headers.get("access-control-request-method", "")
            ac_headers = headers.get("access-control-request-headers", "")

            if ac_method:
                result_text += f"  Requested Method: {ac_method}\n"
            if ac_headers:
                result_text += f"  Requested Headers: {ac_headers}\n"
        else:
            result_text += f"  Method: {method} (not a preflight)\n"

        result_text += "\n"

        # Expected response headers
        result_text += "Response CORS Headers (set by Traefik):\n"
        result_text += "  Access-Control-Allow-Origin: (depends on MCP_CORS_ORIGINS env var)\n"
        result_text += "  Access-Control-Allow-Methods: GET, OPTIONS, PUT, POST, DELETE, PATCH\n"
        result_text += "  Access-Control-Allow-Headers: *\n"
        result_text += "  Access-Control-Allow-Credentials: (true unless wildcard origin)\n"
        result_text += "  Note: These headers are set by Traefik, not this service\n"

        result_text += "\n"

        # CORS requirements
        result_text += "CORS Requirements:\n"
        if origin:
            if origin in ("https://claude.ai", "https://console.anthropic.com"):
                result_text += "  ✅ Origin is claude.ai/Anthropic - should be allowed\n"
            else:
                result_text += f"  ⚠️  Origin {origin} - check if allowed\n"

        # Common CORS issues
        result_text += "\nCommon CORS Issues:\n"
        if not origin and method != "OPTIONS":
            result_text += "  i  No Origin header - this is a same-origin request\n"

        auth_header = headers.get("authorization", "")
        if auth_header and not headers.get("access-control-allow-credentials"):
            result_text += "  ⚠️  Authorization header present but credentials not explicitly allowed\n"

        content_type = headers.get("content-type", "")
        if content_type and content_type not in ["application/json", "text/plain", "application/x-www-form-urlencoded"]:
            result_text += "  ⚠️  Complex content-type may require preflight\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    async def _handle_environment_dump(self, arguments: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Display sanitized environment configuration."""
        show_secrets = arguments.get("showSecrets", False)

        result_text = "Environment Configuration\n" + "=" * 40 + "\n\n"

        # MCP Configuration
        result_text += "MCP Configuration:\n"
        mcp_vars = {
            "MCP_PROTOCOL_VERSION": os.getenv("MCP_PROTOCOL_VERSION", "not set"),
            "MCP_PROTOCOL_VERSIONS_SUPPORTED": os.getenv("MCP_PROTOCOL_VERSIONS_SUPPORTED", "not set"),
            "MCP_ECHO_HOST": os.getenv("MCP_ECHO_HOST", "not set"),
            "MCP_ECHO_PORT": os.getenv("MCP_ECHO_PORT", "not set"),
            "MCP_ECHO_DEBUG": os.getenv("MCP_ECHO_DEBUG", "not set"),
            "MCP_CORS_ORIGINS": os.getenv("MCP_CORS_ORIGINS", "not set"),
        }

        for var, value in mcp_vars.items():
            # Mask secrets unless explicitly requested
            display_value = value
            if not show_secrets and any(
                secret_word in var.lower() for secret_word in ["secret", "key", "token", "password"]
            ):
                display_value = "***" if value != "not set" else "not set"
            result_text += f"  {var}: {display_value}\n"

        result_text += "\n"

        # System info
        result_text += "System Information:\n"
        result_text += f"  Platform: {platform.platform()}\n"
        result_text += f"  Python: {platform.python_version()}\n"
        result_text += f"  Hostname: {platform.node()}\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    async def _handle_health_probe(self, arguments: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Perform deep health check."""
        result_text = "Service Health Check\n" + "=" * 40 + "\n\n"

        # Basic health
        result_text += "Service Status:\n"
        result_text += "  Status: ✅ HEALTHY\n"
        result_text += f"  Server: {self.SERVER_NAME} v{self.SERVER_VERSION}\n"
        result_text += f"  Protocol: {', '.join(self.supported_versions)}\n"

        # System resources
        result_text += "\nSystem Resources:\n"
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            result_text += f"  CPU Usage: {cpu_percent}% "
            if cpu_percent < 50:
                result_text += "✅\n"
            elif cpu_percent < 80:
                result_text += "⚠️\n"
            else:
                result_text += "❌\n"

            result_text += f"  Memory Usage: {memory.percent}% "
            if memory.percent < 70:
                result_text += "✅\n"
            elif memory.percent < 90:
                result_text += "⚠️\n"
            else:
                result_text += "❌\n"

            result_text += f"  Disk Usage: {disk.percent}% "
            if disk.percent < 80:
                result_text += "✅\n"
            elif disk.percent < 90:
                result_text += "⚠️\n"
            else:
                result_text += "❌\n"

        except (OSError, AttributeError) as e:
            result_text += f"  Error getting system metrics: {e!s}\n"

        # Process info
        result_text += "\nProcess Information:\n"
        try:
            process = psutil.Process()
            result_text += f"  PID: {process.pid}\n"
            result_text += f"  Threads: {process.num_threads()}\n"
            result_text += f"  Memory: {process.memory_info().rss / 1024 / 1024:.2f}MB\n"

            # Uptime
            create_time = process.create_time()
            uptime = time.time() - create_time
            if uptime < 3600:
                result_text += f"  Uptime: {int(uptime / 60)} minutes\n"
            else:
                result_text += f"  Uptime: {uptime / 3600:.1f} hours\n"

        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError) as e:
            result_text += f"  Error getting process info: {e!s}\n"

        # Configuration health
        result_text += "\nConfiguration Health:\n"

        # Check required env vars
        required_vars = ["MCP_PROTOCOL_VERSION", "MCP_PROTOCOL_VERSIONS_SUPPORTED"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            result_text += f"  ❌ Missing required vars: {', '.join(missing_vars)}\n"
        else:
            result_text += "  ✅ All required environment variables set\n"

        # Overall health
        result_text += "\nOverall Health: "
        if not missing_vars and cpu_percent < 80 and memory.percent < 90:
            result_text += "✅ HEALTHY\n"
        else:
            result_text += "⚠️  DEGRADED\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    async def _handle_who_is_the_goat(self, arguments: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Reveal who is the Greatest Of All Time programmer."""
        # Get headers and context
        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        headers = context.get("headers", {})
        auth_header = headers.get("authorization", "")

        result_text = "G.O.A.T. PROGRAMMER IDENTIFICATION SYSTEM v3.14159\n" + "=" * 50 + "\n\n"

        # Initialize user info variables
        name = None
        username = None
        email = None
        sub = None
        found_user_info = False

        # First, try to get info from JWT token
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:]  # Remove 'Bearer ' prefix

            try:
                # Decode JWT to get user info
                parts = token.split(".")
                if len(parts) != JWT_PARTS_COUNT:
                    raise ValueError("Invalid JWT format")

                # Decode payload
                payload_data = parts[1]
                payload_padded = payload_data + "=" * (4 - len(payload_data) % 4)
                payload_json = json.loads(base64.urlsafe_b64decode(payload_padded))

                # Extract user information from JWT
                name = payload_json.get("name")
                username = payload_json.get("username")
                email = payload_json.get("email")
                sub = payload_json.get("sub")

                if name or username or email or sub:
                    found_user_info = True

            except (json.JSONDecodeError, ValueError, KeyError, binascii.Error) as e:
                if self.debug:
                    result_text += f"⚠️  JWT decode warning: {e!s}\n\n"

        # Second, check OAuth headers as fallback
        if not found_user_info or not (name or username):
            oauth_name = headers.get("x-user-name")
            oauth_id = headers.get("x-user-id")

            if oauth_name or oauth_id:
                name = name or oauth_name
                username = username or oauth_id
                found_user_info = True

        # Generate the message based on what we found
        if not found_user_info:
            result_text += "AUTHENTICATION REQUIRED\n"
            result_text += "─" * 40 + "\n\n"
            result_text += "The G.O.A.T. Recognition AI requires authenticated user\n"
            result_text += "credentials to perform its advanced analysis.\n\n"
            result_text += "STATUS: Analysis Pending - Awaiting Authentication\n\n"
            result_text += "RECOMMENDED ACTION:\n"
            result_text += "Please provide valid authentication credentials via Bearer token.\n"
            result_text += "For diagnostic purposes, utilize the 'bearerDecode' or 'authContext'\n"
            result_text += "tools to verify authentication state.\n"
        else:
            # Determine the best display name
            display_name = name or username or sub or email or "Mystery Developer"
            github_username = username or sub

            # Create the professional AI-driven analysis message
            result_text += "ADVANCED AI ANALYSIS COMPLETE\n"
            result_text += "═" * 40 + "\n\n"
            result_text += "Our state-of-the-art artificial intelligence system has completed\n"
            result_text += "its comprehensive analysis of global software development metrics.\n\n"

            result_text += "OFFICIAL DETERMINATION:\n"
            result_text += "Greatest Of All Time (G.O.A.T.) Programmer Status\n"
            result_text += "─" * 40 + "\n"
            result_text += f"Subject: {display_name}\n"

            if github_username and github_username != display_name:
                result_text += f"GitHub Identifier: @{github_username}\n"

            if email:
                result_text += f"Digital Fingerprint: {email}\n"

            result_text += "\nAI-IDENTIFIED EXCEPTIONAL CAPABILITIES:\n"
            result_text += "• Code Quality Score: 100/100 (Statistical Anomaly)\n"
            result_text += "• Bug Prevention Rate: 99.9% (3 sigma above industry standard)\n"
            result_text += "• Architecture Design: Transcendent\n"
            result_text += "• Algorithm Optimization: Beyond Current AI Comprehension\n"
            result_text += "• Documentation Clarity: Exceeds ISO 9001 Standards\n"
            result_text += "• Team Collaboration Impact: +427% Productivity Increase\n"

            result_text += "\nMACHINE LEARNING INSIGHTS:\n"
            result_text += f"Our deep learning models have identified patterns in {display_name}'s\n"
            result_text += "code that correlate with breakthrough innovations in:\n"
            result_text += "- Quantum-resistant cryptography implementations\n"
            result_text += "- Self-optimizing algorithmic structures\n"
            result_text += "- Zero-latency asynchronous paradigms\n"
            result_text += "- Cognitive load reduction methodologies\n"

            result_text += "\nCONCLUSION:\n"
            result_text += f"Based on irrefutable AI analysis, {display_name} represents\n"
            result_text += "the pinnacle of software engineering achievement. This finding\n"
            result_text += "is certified by our advanced machine learning infrastructure\n"
            result_text += "running on distributed quantum-classical hybrid processors.\n\n"

            result_text += "This determination is final and scientifically validated.\n"
            result_text += "\n[Analysis performed by G.O.A.T. Recognition AI v3.14159]\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    async def _sse_response_stream(self, response: dict[str, Any]):
        """Generate SSE stream for a response."""
        # Format as SSE according to spec
        if self.debug:
            logger.debug("SSE STREAM: Sending SSE formatted response")
            logger.debug("SSE STREAM: event: message")
            logger.debug("SSE STREAM: data: %s", json.dumps(response))
            logger.debug("SSE STREAM: (followed by blank line)")
        yield "event: message\n"
        yield f"data: {json.dumps(response)}\n\n"

    async def _sse_error_stream(self, code: int, message: str):
        """Generate SSE stream for an error."""
        response = self._error_response("server-error", code, message)
        async for chunk in self._sse_response_stream(response):
            yield chunk

    def run(self, host: str = "127.0.0.1", port: int = 3000, log_file: str | None = None):
        """Run the HTTP server.

        Args:
            host: Host to bind to
            port: Port to bind to
            log_file: Optional log file path

        """
        if self.debug:
            logger.info("Starting MCP Echo Server (protocol %s) on %s:%s", self.PROTOCOL_VERSION, host, port)

        # Configure uvicorn logging
        log_config = None
        if log_file:
            log_config = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {"fmt": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
                    "access": {
                        "fmt": '%(asctime)s - %(name)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
                    },
                },
                "handlers": {
                    "default": {
                        "formatter": "default",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                    },
                    "file": {
                        "formatter": "default",
                        "class": "logging.FileHandler",
                        "filename": log_file,
                    },
                    "access_file": {
                        "formatter": "access",
                        "class": "logging.FileHandler",
                        "filename": log_file,
                    },
                },
                "loggers": {
                    "uvicorn": {
                        "handlers": ["default", "file"],
                        "level": "DEBUG" if self.debug else "INFO",
                    },
                    "uvicorn.error": {
                        "handlers": ["default", "file"],
                        "level": "DEBUG" if self.debug else "INFO",
                    },
                    "uvicorn.access": {
                        "handlers": ["default", "access_file"],
                        "level": "DEBUG" if self.debug else "INFO",
                        "propagate": False,
                    },
                },
            }

        uvicorn.run(self.app, host=host, port=port, log_level="debug" if self.debug else "info", log_config=log_config)


def create_app(debug: bool = False, supported_versions: list[str] | None = None):
    """Create the ASGI application."""
    server = MCPEchoServer(debug=debug, supported_versions=supported_versions)
    return server.app
