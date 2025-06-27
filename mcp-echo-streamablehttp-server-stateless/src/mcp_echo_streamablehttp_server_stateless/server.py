"""Stateless MCP Echo Server implementing MCP 2025-06-18 StreamableHTTP transport specification."""

import asyncio
import base64
import json
import logging
import os
import platform
import time
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

        if request.method == "GET":
            return self._handle_sse_stream()

        # POST method handling
        return await self._handle_post_request(request)

    def _handle_sse_stream(self) -> StreamingResponse:
        """Handle GET requests for SSE streams."""

        async def sse_stream():
            # Send a keep-alive comment to establish the connection
            yield "event: ping\ndata: {}\n\n"
            # Keep connection open but don't send more data (stateless)

        return StreamingResponse(
            sse_stream(),
            media_type="text/event-stream",
            headers={
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
                    "error": f"Unsupported protocol version: {protocol_version}. Supported versions: {', '.join(self.supported_versions)}"
                },
                status_code=400,
            )

        return None

    async def _process_json_rpc_request(self, request: Request) -> Response:
        """Process the JSON-RPC request and return appropriate response."""
        # Determine response format based on Accept header
        accept = request.headers.get("accept", "application/json")
        # Prefer SSE if client explicitly accepts it, otherwise use JSON
        use_sse = "text/event-stream" in accept

        try:
            body = await request.json()
        except Exception:
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
            logger.debug(f"Request: {body}")
            logger.debug(f"Accept header: {accept}, Using SSE: {use_sse}")

        # Handle batch requests
        if isinstance(body, list):
            return JSONResponse(
                {"error": "Batch requests not supported in stateless mode"},
                status_code=400,
            )

        # Handle the JSON-RPC request
        response = await self._handle_jsonrpc_request(body)

        if self.debug:
            logger.debug(f"Response: {response}")

        # Check if this is a notification
        if "id" not in body and "error" not in response:
            return Response(content="", status_code=202)

        # Return response in appropriate format
        if use_sse:
            return StreamingResponse(
                self._sse_response_stream(response),
                media_type="text/event-stream",
            )
        # Return direct JSON response
        return JSONResponse(response)

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
                        "includeRaw": {"type": "boolean", "description": "Include raw token parts", "default": False}
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
                "name": "protocolNegotiation",
                "description": "Analyze MCP protocol version negotiation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "testVersion": {"type": "string", "description": "Test a specific protocol version"}
                    },
                    "additionalProperties": False,
                },
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
                        }
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
            "protocolNegotiation": self._handle_protocol_negotiation,
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
        """Handle the printHeader tool."""
        headers_text = "HTTP Headers:\n"
        headers_text += "-" * 40 + "\n"

        # Get headers from the current task's context
        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        headers = context.get("headers", {})

        if headers:
            for key, value in sorted(headers.items()):
                headers_text += f"{key}: {value}\n"
        else:
            headers_text += "No headers available (headers are captured per request)\n"

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
                if len(parts) != 3:
                    result_text += f"❌ Invalid JWT format (expected 3 parts, got {len(parts)})\n"
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

            except Exception as e:
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
                    if len(parts) == 3:
                        payload_padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
                        payload_json = json.loads(base64.urlsafe_b64decode(payload_padded))
                        if "sub" in payload_json:
                            result_text += f"  Subject: {payload_json['sub']}\n"
                        if "client_id" in payload_json:
                            result_text += f"  Client ID: {payload_json['client_id']}\n"
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    # JWT decode errors are expected for invalid tokens - this is a diagnostic tool
                    logging.debug(f"Failed to decode JWT payload: {e}")
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
        if elapsed < 0.010:  # 10ms
            result_text += "  ⚡ Excellent (<10ms)\n"
        elif elapsed < 0.050:  # 50ms
            result_text += "  ✅ Good (<50ms)\n"
        elif elapsed < 0.100:  # 100ms
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

    async def _handle_protocol_negotiation(self, arguments: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Analyze protocol version negotiation."""
        test_version = arguments.get("testVersion", "")

        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        headers = context.get("headers", {})

        result_text = "MCP Protocol Negotiation Analysis\n" + "=" * 40 + "\n\n"

        # Current request info
        result_text += "Current Request:\n"
        mcp_header = headers.get("mcp-protocol-version", None)
        client_version = mcp_header if mcp_header is not None else "not specified"
        result_text += f"  MCP-Protocol-Version Header: {client_version}\n"
        if mcp_header:
            result_text += "  Header Present: ✅ Yes\n"
        else:
            result_text += "  Header Present: ❌ No\n"
        result_text += f"  Server Supported Versions: {', '.join(self.supported_versions)}\n"
        result_text += f"  Server Default Version: {self.PROTOCOL_VERSION}\n"

        result_text += "\n"

        # All MCP-related headers
        result_text += "MCP-Related Headers in Request:\n"
        mcp_headers_found = False
        for header_name, header_value in headers.items():
            if "mcp" in header_name.lower():
                result_text += f"  {header_name}: {header_value}\n"
                mcp_headers_found = True
        if not mcp_headers_found:
            result_text += "  No MCP-related headers found\n"

        result_text += "\n"

        # Negotiation result
        result_text += "Negotiation Result:\n"
        if client_version == "not specified":
            result_text += "  ⚠️  No protocol version specified by client\n"
            result_text += f"  Server would use default: {self.PROTOCOL_VERSION}\n"
            result_text += "  Note: Actual negotiation happens during 'initialize' request\n"
        elif client_version in self.supported_versions:
            result_text += f"  ✅ Compatible - Client requesting version: {client_version}\n"
            result_text += "  This version would be used if negotiated during 'initialize'\n"
        else:
            result_text += f"  ❌ Incompatible - Client version not supported: {client_version}\n"
            result_text += "  Server would reject this during 'initialize' request\n"

        result_text += "\n"

        # Test specific version
        if test_version:
            result_text += f"Testing Version: {test_version}\n"
            if test_version in self.supported_versions:
                result_text += "  ✅ This version is supported\n"
            else:
                result_text += "  ❌ This version is NOT supported\n"
            result_text += "\n"

        # Version compatibility matrix
        result_text += "Version Compatibility:\n"
        known_versions = ["2024-11-05", "2025-03-26", "2025-06-18"]
        for version in known_versions:
            if version in self.supported_versions:
                result_text += f"  {version}: ✅ Supported\n"
            else:
                result_text += f"  {version}: ❌ Not supported\n"

        result_text += "\n"

        # Feature differences
        result_text += "Protocol Version Features:\n"
        result_text += "  2024-11-05: Original MCP specification\n"
        result_text += "  2025-03-26: Enhanced transport options\n"
        result_text += "  2025-06-18: StreamableHTTP transport, SSE support\n"

        result_text += "\n"

        # How negotiation works
        result_text += "  Note: This is a stateless server, so each request is independent.\n"
        result_text += "  The MCP-Protocol-Version header should match what was negotiated.\n"

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

        except Exception as e:
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

        except Exception as e:
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
                if len(parts) != 3:
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

            except Exception as e:
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
            logger.info(f"Starting MCP Echo Server (protocol {self.PROTOCOL_VERSION}) on {host}:{port}")

        # Configure uvicorn logging
        log_config = None
        if log_file:
            log_config = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {"fmt": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
                    "access": {
                        "fmt": '%(asctime)s - %(name)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s'
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
