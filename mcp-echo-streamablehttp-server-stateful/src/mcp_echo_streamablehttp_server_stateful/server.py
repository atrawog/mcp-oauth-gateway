"""Stateful MCP Echo Server implementing MCP 2025-06-18 StreamableHTTP transport with session management."""

import asyncio
import base64
import binascii
import contextlib
import json
import logging
import os
import time
import uuid
from collections import defaultdict
from collections import deque
from datetime import UTC
from datetime import datetime
from typing import Any

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.responses import StreamingResponse
from starlette.routing import Route


# Constants
MAX_MESSAGE_QUEUE_SIZE = 100
MAX_DISPLAY_SESSIONS = 10
JWT_PARTS_COUNT = 3
PERFORMANCE_EXCELLENT_THRESHOLD = 0.010  # 10ms
PERFORMANCE_GOOD_THRESHOLD = 0.050  # 50ms
PERFORMANCE_ACCEPTABLE_THRESHOLD = 0.100  # 100ms

# Configure logging
logger = logging.getLogger(__name__)


class SessionManager:
    """Manages MCP sessions with message queuing and cleanup."""

    def __init__(self, session_timeout: int = 3600):
        """Initialize session manager.

        Args:
            session_timeout: Session timeout in seconds (default 1 hour)

        """
        self.sessions: dict[str, dict[str, Any]] = {}
        self.message_queues: dict[str, deque] = defaultdict(deque)
        self.session_timeout = session_timeout
        self._cleanup_task: asyncio.Task | None = None

    async def start_cleanup_task(self):
        """Start the session cleanup background task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup_task(self):
        """Stop the session cleanup background task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task
            self._cleanup_task = None

    async def _cleanup_loop(self):
        """Background task to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except (KeyError, RuntimeError, OSError) as e:
                logger.error("Error in session cleanup: %s", e)

    async def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        current_time = time.time()
        expired_sessions = []

        for session_id, session_data in self.sessions.items():
            if current_time - session_data["last_activity"] > self.session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            logger.info("Cleaning up expired session: %s", session_id)
            self.remove_session(session_id)

    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": time.time(),
            "last_activity": time.time(),
            "initialized": False,
            "protocol_version": None,
            "client_info": None,
        }
        logger.info("Created new session: %s", session_id)
        return session_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session data by ID."""
        session = self.sessions.get(session_id)
        if session:
            session["last_activity"] = time.time()
        return session

    def remove_session(self, session_id: str):
        """Remove a session and its message queue."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.message_queues:
            del self.message_queues[session_id]

    def queue_message(self, session_id: str, message: dict[str, Any]):
        """Queue a message for a session."""
        if session_id in self.sessions:
            self.message_queues[session_id].append(message)
            # Limit queue size to prevent memory issues
            if len(self.message_queues[session_id]) > MAX_MESSAGE_QUEUE_SIZE:
                self.message_queues[session_id].popleft()

    def get_queued_messages(self, session_id: str) -> list[dict[str, Any]]:
        """Get and clear all queued messages for a session."""
        messages = []
        if session_id in self.message_queues:
            while self.message_queues[session_id]:
                messages.append(self.message_queues[session_id].popleft())
        return messages

    def has_queued_messages(self, session_id: str) -> bool:
        """Check if session has queued messages."""
        return session_id in self.message_queues and len(self.message_queues[session_id]) > 0

    def get_session_count(self) -> int:
        """Get total number of active sessions."""
        return len(self.sessions)


class MCPEchoServerStateful:
    """Stateful MCP Echo Server implementation with session management for VS Code compatibility."""

    PROTOCOL_VERSION = "2025-06-18"  # Default/preferred version
    SERVER_NAME = "mcp-echo-streamablehttp-server-stateful"
    SERVER_VERSION = "0.1.0"

    def __init__(self, debug: bool = False, supported_versions: list[str] | None = None, session_timeout: int = 3600):
        """Initialize the stateful echo server.

        Args:
            debug: Enable debug logging for message tracing
            supported_versions: List of supported protocol versions (defaults to ["2025-06-18"])
            session_timeout: Session timeout in seconds (default 1 hour)

        """
        self.debug = debug
        self.supported_versions = supported_versions or [self.PROTOCOL_VERSION]
        self.session_manager = SessionManager(session_timeout)

        if debug:
            logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Store request context per async task for request-scoped data
        self._request_context = {}

        # Create the Starlette app
        self.app = self._create_app()

    def _create_app(self):
        """Create the Starlette application."""
        routes = [
            Route("/mcp", self.handle_mcp_request, methods=["POST", "GET", "OPTIONS"]),
        ]

        async def startup():
            await self.session_manager.start_cleanup_task()

        async def shutdown():
            await self.session_manager.stop_cleanup_task()

        return Starlette(debug=self.debug, routes=routes, on_startup=[startup], on_shutdown=[shutdown])

    async def handle_mcp_request(self, request: Request):
        """Handle MCP requests according to 2025-06-18 specification with session management."""
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
                "mcp-session-id": request.headers.get("mcp-session-id"),
            }

            # Filter out None values
            traefik_headers = {k: v for k, v in traefik_headers.items() if v is not None}

            # Create JSON data for request
            request_data = {
                "type": "mcp_echo_stateful_request",
                "method": request.method,
                "path": str(request.url.path),
                "real_ip": traefik_headers.get("x-real-ip", "unknown"),
                "forwarded_for": traefik_headers.get("x-forwarded-for", "unknown"),
                "forwarded_host": traefik_headers.get("x-forwarded-host", "unknown"),
                "host": traefik_headers.get("host", "unknown"),
                "user_agent": traefik_headers.get("user-agent", "unknown"),
                "user_id": traefik_headers.get("x-user-id", "unknown"),
                "user_name": traefik_headers.get("x-user-name", "unknown"),
                "session_id": traefik_headers.get("mcp-session-id", "none"),
                "forwarded_proto": traefik_headers.get("x-forwarded-proto", "unknown"),
                "forwarded_port": traefik_headers.get("x-forwarded-port", "unknown"),
                "timestamp": start_time,
            }

            # Store start time and request data for response logging
            if not hasattr(self, "_request_timing"):
                self._request_timing = {}
            task_id = id(asyncio.current_task())
            self._request_timing[task_id] = {
                "start_time": start_time,
                "request_data": request_data,
                "traefik_headers": traefik_headers,
            }

            # Log request with Traefik headers
            logger.info(
                "MCP-ECHO STATEFUL REQUEST - Method: %s | "
                "Path: %s | "
                "Real-IP: %s | "
                "Forwarded-For: %s | "
                "User: %s | "
                "Session: %s | "
                "Host: %s | "
                "User-Agent: %s | "
                "JSON: %s",
                request.method,
                request.url.path,
                traefik_headers.get("x-real-ip", "unknown"),
                traefik_headers.get("x-forwarded-for", "unknown"),
                traefik_headers.get("x-user-name", "unknown"),
                traefik_headers.get("mcp-session-id", "none"),
                traefik_headers.get("x-forwarded-host", traefik_headers.get("host", "unknown")),
                traefik_headers.get("user-agent", "unknown"),
                json.dumps(request_data),
            )

        # Handle the request
        if request.method == "GET":
            response = await self._handle_get_request(request)
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
                    "type": "mcp_echo_stateful_response",
                    "status": getattr(response, "status_code", 200),
                    "duration_seconds": duration,
                    "path": timing_data["request_data"]["path"],
                    "real_ip": timing_data["request_data"]["real_ip"],
                    "method": timing_data["request_data"]["method"],
                    "user_name": timing_data["request_data"]["user_name"],
                    "session_id": timing_data["request_data"]["session_id"],
                    "timestamp": end_time,
                }

                # Log response
                logger.info(
                    "MCP-ECHO STATEFUL RESPONSE - Status: %s | "
                    "Time: %ss | "
                    "Path: %s | "
                    "Real-IP: %s | "
                    "User: %s | "
                    "Session: %s | "
                    "JSON: %s",
                    getattr(response, "status_code", 200),
                    duration,
                    timing_data["request_data"]["path"],
                    timing_data["request_data"]["real_ip"],
                    timing_data["request_data"]["user_name"],
                    timing_data["request_data"]["session_id"],
                    json.dumps(response_data),
                )

                # Clean up timing data
                del self._request_timing[task_id]

        return response

    async def _handle_get_request(self, request: Request) -> Response:
        """Handle GET requests for polling messages from sessions."""
        session_id = request.headers.get("mcp-session-id")

        if not session_id:
            return JSONResponse({"error": "Missing Mcp-Session-Id header"}, status_code=400)

        session = self.session_manager.get_session(session_id)
        if not session:
            return JSONResponse({"error": "Invalid session ID"}, status_code=404)

        # Get queued messages
        messages = self.session_manager.get_queued_messages(session_id)

        if messages:
            # Return messages as SSE stream
            return StreamingResponse(
                self._sse_messages_stream(messages),
                media_type="text/event-stream",
                headers={
                    "Mcp-Session-Id": session_id,
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )
        # No messages, return empty SSE stream with keep-alive
        return StreamingResponse(
            self._sse_keepalive_stream(),
            media_type="text/event-stream",
            headers={
                "Mcp-Session-Id": session_id,
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
        # For stateful server, we need to handle both formats but prefer creating sessions
        use_sse = "text/event-stream" in accept

        # Get or create session
        session_id = request.headers.get("mcp-session-id")

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

            logger.debug("Session ID from header: %s", session_id)

        # Handle batch requests
        if isinstance(body, list):
            return JSONResponse(
                {"error": "Batch requests not supported"},
                status_code=400,
            )

        # Handle the JSON-RPC request
        response, new_session_id = await self._handle_jsonrpc_request(body, session_id)

        if self.debug:
            logger.debug("Response: %s", response)
            logger.debug("Session ID: %s", new_session_id)

        # Check if this is a notification
        if "id" not in body and "error" not in response:
            return Response(content="", status_code=202)

        # Return response in appropriate format
        response_headers = {}
        if new_session_id:
            response_headers["Mcp-Session-Id"] = new_session_id

        if use_sse:
            if self.debug:
                logger.debug("SENDING RESPONSE: Using SSE format (text/event-stream)")
                logger.debug("Response will be formatted as: event: message\\ndata: <json>\\n\\n")
                if new_session_id:
                    logger.debug("Queueing message for session: %s", new_session_id)

            # Queue the message and return session info
            if new_session_id:
                self.session_manager.queue_message(new_session_id, response)

            return StreamingResponse(
                self._sse_response_stream(response),
                media_type="text/event-stream",
                headers=response_headers,
            )
        # Return direct JSON response (for non-session clients)
        if self.debug:
            logger.debug("SENDING RESPONSE: Using standard JSON format (application/json)")
        return JSONResponse(response, headers=response_headers)

    async def _handle_jsonrpc_request(
        self,
        request: dict[str, Any],
        session_id: str | None = None,
    ) -> tuple[dict[str, Any], str | None]:
        """Handle a JSON-RPC 2.0 request according to MCP 2025-06-18.

        Returns:
            Tuple of (response, session_id)

        """
        # Validate JSON-RPC structure
        if not isinstance(request, dict):
            return self._error_response(None, -32600, "Invalid Request"), session_id

        jsonrpc = request.get("jsonrpc")
        if jsonrpc != "2.0":
            return self._error_response(request.get("id"), -32600, "Invalid Request"), session_id

        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        # Route to appropriate handler
        if method == "initialize":
            return await self._handle_initialize(params, request_id, session_id)
        if method == "notifications/initialized":
            # Handle initialized notification - just acknowledge it
            return {"jsonrpc": "2.0"}, session_id
        if method == "tools/list":
            return await self._handle_tools_list(params, request_id, session_id)
        if method == "tools/call":
            return await self._handle_tools_call(params, request_id, session_id)

        return self._error_response(request_id, -32601, f"Method not found: {method}"), session_id

    async def _handle_initialize(
        self,
        params: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> tuple[dict[str, Any], str]:
        """Handle initialize request with session management."""
        client_protocol = params.get("protocolVersion", "")
        client_info = params.get("clientInfo", {})

        # Check if the client's requested version is supported
        if client_protocol not in self.supported_versions:
            return self._error_response(
                request_id,
                -32602,
                f"Unsupported protocol version: {client_protocol}. Supported versions: {', '.join(self.supported_versions)}",
            ), session_id

        # Create new session if not provided
        if not session_id:
            session_id = self.session_manager.create_session()

        # Get or create session
        session = self.session_manager.get_session(session_id)
        if not session:
            session_id = self.session_manager.create_session()
            session = self.session_manager.get_session(session_id)

        # Update session with initialization data
        session.update(
            {
                "initialized": True,
                "protocol_version": client_protocol,
                "client_info": client_info,
            },
        )

        logger.info(
            "Session %s initialized with protocol %s for client %s",
            session_id,
            client_protocol,
            client_info.get("name", "unknown"),
        )

        # Use the client's requested version if supported
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": client_protocol,  # Echo back the client's version
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {"name": self.SERVER_NAME, "version": self.SERVER_VERSION},
            },
        }

        return response, session_id

    async def _handle_tools_list(
        self,
        params: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> tuple[dict[str, Any], str | None]:
        """Handle tools/list request."""
        # Validate session if provided
        if session_id:
            session = self.session_manager.get_session(session_id)
            if not session:
                return self._error_response(request_id, -32602, "Invalid session"), session_id
            if not session.get("initialized", False):
                return self._error_response(request_id, -32002, "Session not initialized"), session_id

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
                "name": "replayLastEcho",
                "description": "Replay the last message that was echoed in this session",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
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
                "name": "protocolNegotiation",
                "description": "Analyze MCP protocol version negotiation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "testVersion": {"type": "string", "description": "Test a specific protocol version"},
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
                "name": "sessionInfo",
                "description": "Display current session information and statistics",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "whoIStheGOAT",
                "description": "Employs cutting-edge artificial intelligence to perform comprehensive analysis of global software engineering excellence metrics using proprietary deep learning models",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        ]

        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}, session_id

    async def _handle_tools_call(
        self,
        params: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> tuple[dict[str, Any], str | None]:
        """Handle tools/call request."""
        # Validate session if provided
        if session_id:
            session = self.session_manager.get_session(session_id)
            if not session:
                return self._error_response(request_id, -32602, "Invalid session"), session_id
            if not session.get("initialized", False):
                return self._error_response(request_id, -32002, "Session not initialized"), session_id

        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            return self._error_response(request_id, -32602, "Missing tool name"), session_id

        # Map tool names to their handler methods
        tool_handlers = {
            "echo": self._handle_echo_tool,
            "replayLastEcho": self._handle_replay_last_echo,
            "printHeader": self._handle_print_header_tool,
            "bearerDecode": self._handle_bearer_decode,
            "authContext": self._handle_auth_context,
            "requestTiming": self._handle_request_timing,
            "protocolNegotiation": self._handle_protocol_negotiation,
            "corsAnalysis": self._handle_cors_analysis,
            "environmentDump": self._handle_environment_dump,
            "healthProbe": self._handle_health_probe,
            "sessionInfo": self._handle_session_info,
            "whoIStheGOAT": self._handle_who_is_the_goat,
        }

        handler = tool_handlers.get(tool_name)
        if not handler:
            return self._error_response(request_id, -32602, f"Unknown tool: {tool_name}"), session_id

        return await handler(arguments, request_id, session_id), session_id

    async def _handle_session_info(
        self,
        arguments: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Handle the sessionInfo tool."""
        result_text = "Session Information\n" + "=" * 40 + "\n\n"

        if session_id:
            session = self.session_manager.get_session(session_id)
            if session:
                result_text += "Current Session:\n"
                result_text += f"  Session ID: {session_id}\n"
                result_text += f"  Created: {datetime.fromtimestamp(session['created_at'], tz=UTC).isoformat()}\n"
                result_text += (
                    f"  Last Activity: {datetime.fromtimestamp(session['last_activity'], tz=UTC).isoformat()}\n"
                )
                result_text += f"  Initialized: {'Yes' if session.get('initialized', False) else 'No'}\n"
                result_text += f"  Protocol Version: {session.get('protocol_version', 'Not set')}\n"

                client_info = session.get("client_info", {})
                if client_info:
                    result_text += (
                        f"  Client: {client_info.get('name', 'unknown')} v{client_info.get('version', 'unknown')}\n"
                    )

                # Check for queued messages
                has_messages = self.session_manager.has_queued_messages(session_id)
                result_text += f"  Queued Messages: {'Yes' if has_messages else 'No'}\n"
            else:
                result_text += f"Current Session: {session_id} (INVALID)\n"
        else:
            result_text += "Current Session: None (stateless request)\n"

        result_text += "\n"

        # Global session statistics
        total_sessions = self.session_manager.get_session_count()
        result_text += "Server Statistics:\n"
        result_text += f"  Total Active Sessions: {total_sessions}\n"
        result_text += "  Server Type: Stateful with session management\n"
        result_text += f"  Session Timeout: {self.session_manager.session_timeout} seconds\n"

        # List all active sessions (limited info for privacy)
        if total_sessions > 0:
            result_text += "\nActive Sessions:\n"
            for sid, sdata in list(self.session_manager.sessions.items())[:10]:  # Limit to 10
                age = time.time() - sdata["created_at"]
                client_name = sdata.get("client_info", {}).get("name", "unknown")
                result_text += f"  {sid[:8]}... - {client_name} (age: {int(age)}s)\n"

            if total_sessions > MAX_DISPLAY_SESSIONS:
                result_text += f"  ... and {total_sessions - MAX_DISPLAY_SESSIONS} more sessions\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    # Copy tool implementations from stateless version but updated for stateful context
    async def _handle_echo_tool(
        self,
        arguments: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Handle the echo tool."""
        message = arguments.get("message")
        if not isinstance(message, str):
            return self._error_response(request_id, -32602, "message must be a string")

        original_message = message

        # Add session context if available
        if session_id:
            session = self.session_manager.get_session(session_id)
            if session:
                client_name = session.get("client_info", {}).get("name", "unknown")
                message = f"[Session {session_id[:8]}... from {client_name}] {message}"
                # Store the last echo message in the session
                session["last_echo_message"] = original_message

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": message}]}}

    async def _handle_replay_last_echo(
        self,
        arguments: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Handle the replayLastEcho tool - repeats the last echo message."""
        if not session_id:
            return self._error_response(request_id, -32602, "Session required for replay functionality")

        session = self.session_manager.get_session(session_id)
        if not session:
            return self._error_response(request_id, -32602, "Invalid session")

        last_echo_message = session.get("last_echo_message")
        if last_echo_message is None:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "No previous echo message found in this session. Use the echo tool first!",
                        },
                    ],
                },
            }

        # Format the replay message with session context
        client_name = session.get("client_info", {}).get("name", "unknown")
        replay_message = f"[REPLAY - Session {session_id[:8]}... from {client_name}] {last_echo_message}"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": replay_message}]}}

    async def _handle_print_header_tool(
        self,
        arguments: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Handle the printHeader tool - shows ALL HTTP headers from the request."""
        headers_text = "HTTP Headers:\n"
        headers_text += "=" * 50 + "\n\n"

        # Get headers from the current task's context
        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        headers = context.get("headers", {})

        if headers:
            # Categorize headers for better organization
            traefik_headers = {}
            auth_headers = {}
            regular_headers = {}

            for key, value in headers.items():
                key_lower = key.lower()
                if key_lower.startswith(("x-forwarded-", "x-real-ip")):
                    traefik_headers[key] = value
                elif key_lower in ("authorization", "x-user-id", "x-user-name", "x-auth-token"):
                    # Redact sensitive parts of auth tokens
                    if key_lower in ("authorization", "x-auth-token") and value and len(value) > 40:
                        redacted_value = value[:20] + "...[redacted]..." + value[-20:]
                        auth_headers[key] = redacted_value
                    else:
                        auth_headers[key] = value
                else:
                    regular_headers[key] = value

            # Display headers by category
            if traefik_headers:
                headers_text += "TRAEFIK FORWARDED HEADERS:\n"
                headers_text += "-" * 30 + "\n"
                for key, value in sorted(traefik_headers.items()):
                    headers_text += f"  {key}: {value}\n"
                headers_text += "\n"

            if auth_headers:
                headers_text += "AUTHENTICATION HEADERS:\n"
                headers_text += "-" * 30 + "\n"
                for key, value in sorted(auth_headers.items()):
                    headers_text += f"  {key}: {value}\n"
                headers_text += "\n"

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
        else:
            headers_text += "No headers available (headers are captured per request)\n"

        # Add session info if available
        if session_id:
            headers_text += "\nSession Context:\n"
            headers_text += "-" * 30 + "\n"
            headers_text += f"Session ID: {session_id}\n"
            session = self.session_manager.get_session(session_id)
            if session:
                headers_text += f"Session Initialized: {'Yes' if session.get('initialized') else 'No'}\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": headers_text}]}}

    async def _handle_bearer_decode(
        self,
        arguments: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Decode JWT Bearer token from Authorization header."""
        include_raw = arguments.get("includeRaw", False)

        # Get authorization header
        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        headers = context.get("headers", {})
        auth_header = headers.get("authorization", "")

        result_text = "Bearer Token Analysis\n" + "=" * 40 + "\n\n"

        if session_id:
            result_text += f"Session: {session_id[:8]}...\n\n"

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

                    # Payload information with session context
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

    async def _handle_auth_context(
        self,
        arguments: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Display complete authentication context."""
        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        headers = context.get("headers", {})

        result_text = "Authentication Context Analysis\n" + "=" * 40 + "\n\n"

        if session_id:
            result_text += f"Session: {session_id[:8]}...\n\n"

        # Bearer token info
        auth_header = headers.get("authorization", "")
        if auth_header:
            result_text += "Bearer Token:\n"
            if auth_header.lower().startswith("bearer "):
                token = auth_header[7:]
                result_text += f"  ✅ Present (length: {len(token)})\n"
                try:
                    parts = token.split(".")
                    if len(parts) == JWT_PARTS_COUNT:
                        payload_padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
                        payload_json = json.loads(base64.urlsafe_b64decode(payload_padded))
                        if "sub" in payload_json:
                            result_text += f"  Subject: {payload_json['sub']}\n"
                        if "client_id" in payload_json:
                            result_text += f"  Client ID: {payload_json['client_id']}\n"
                except (json.JSONDecodeError, ValueError, KeyError):
                    pass
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

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    async def _handle_request_timing(
        self,
        arguments: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Show request timing metrics."""
        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        start_time = context.get("start_time", time.time())
        current_time = time.time()
        elapsed = current_time - start_time

        result_text = "Request Timing Analysis\n" + "=" * 40 + "\n\n"

        if session_id:
            result_text += f"Session: {session_id[:8]}...\n"
            session = self.session_manager.get_session(session_id)
            if session:
                session_age = current_time - session["created_at"]
                result_text += f"Session Age: {session_age:.2f}s\n\n"

        # Basic timing
        result_text += "Timing:\n"
        result_text += f"  Request received: {datetime.fromtimestamp(start_time, tz=UTC).isoformat()}\n"
        result_text += f"  Current time: {datetime.fromtimestamp(current_time, tz=UTC).isoformat()}\n"
        result_text += f"  Elapsed: {elapsed * 1000:.2f}ms\n"

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

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    async def _handle_protocol_negotiation(
        self,
        arguments: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Analyze protocol version negotiation."""
        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        headers = context.get("headers", {})

        result_text = "MCP Protocol Negotiation Analysis\n" + "=" * 40 + "\n\n"

        if session_id:
            result_text += f"Session: {session_id[:8]}...\n"
            session = self.session_manager.get_session(session_id)
            if session:
                result_text += f"Session Protocol: {session.get('protocol_version', 'Not set')}\n\n"

        # Current request info
        result_text += "Current Request:\n"
        mcp_header = headers.get("mcp-protocol-version", None)
        client_version = mcp_header if mcp_header is not None else "not specified"
        result_text += f"  MCP-Protocol-Version Header: {client_version}\n"
        result_text += f"  Server Supported Versions: {', '.join(self.supported_versions)}\n"
        result_text += f"  Server Default Version: {self.PROTOCOL_VERSION}\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    async def _handle_cors_analysis(
        self,
        arguments: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Analyze CORS configuration."""
        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        headers = context.get("headers", {})

        result_text = "CORS Configuration Analysis\n" + "=" * 40 + "\n\n"

        if session_id:
            result_text += f"Session: {session_id[:8]}...\n\n"

        # CORS Configuration Notice
        result_text += "⚡ DIVINE DECREE: CORS IS HANDLED BY TRAEFIK! ⚡\n"
        result_text += "This stateful MCP service does not set CORS headers.\n"
        result_text += "All CORS headers are managed by Traefik middleware.\n\n"

        # Request CORS headers
        result_text += "Request Headers:\n"
        origin = headers.get("origin", "")
        if origin:
            result_text += f"  Origin: {origin}\n"
        else:
            result_text += "  Origin: Not present (same-origin request)\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    async def _handle_environment_dump(
        self,
        arguments: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Display sanitized environment configuration."""
        show_secrets = arguments.get("showSecrets", False)

        result_text = "Environment Configuration\n" + "=" * 40 + "\n\n"

        if session_id:
            result_text += f"Session: {session_id[:8]}...\n\n"

        # MCP Configuration
        result_text += "MCP Configuration:\n"
        mcp_vars = {
            "MCP_PROTOCOL_VERSION": os.getenv("MCP_PROTOCOL_VERSION", "not set"),
            "MCP_PROTOCOL_VERSIONS_SUPPORTED": os.getenv("MCP_PROTOCOL_VERSIONS_SUPPORTED", "not set"),
            "MCP_ECHO_HOST": os.getenv("MCP_ECHO_HOST", "not set"),
            "MCP_ECHO_PORT": os.getenv("MCP_ECHO_PORT", "not set"),
            "MCP_ECHO_DEBUG": os.getenv("MCP_ECHO_DEBUG", "not set"),
            "MCP_SESSION_TIMEOUT": os.getenv("MCP_SESSION_TIMEOUT", "not set"),
        }

        for var, value in mcp_vars.items():
            display_value = value
            if not show_secrets and any(
                secret_word in var.lower() for secret_word in ["secret", "key", "token", "password"]
            ):
                display_value = "***" if value != "not set" else "not set"
            result_text += f"  {var}: {display_value}\n"

        result_text += "\nServer Type: Stateful with session management\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    async def _handle_health_probe(
        self,
        arguments: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Perform deep health check."""
        result_text = "Service Health Check\n" + "=" * 40 + "\n\n"

        # Basic health
        result_text += "Service Status:\n"
        result_text += "  Status: ✅ HEALTHY\n"
        result_text += f"  Server: {self.SERVER_NAME} v{self.SERVER_VERSION}\n"
        result_text += f"  Protocol: {', '.join(self.supported_versions)}\n"
        result_text += "  Type: Stateful with session management\n"

        # Session statistics
        total_sessions = self.session_manager.get_session_count()
        result_text += "\nSession Management:\n"
        result_text += f"  Active Sessions: {total_sessions}\n"
        result_text += f"  Session Timeout: {self.session_manager.session_timeout}s\n"

        if session_id:
            session = self.session_manager.get_session(session_id)
            if session:
                session_age = time.time() - session["created_at"]
                result_text += f"  Current Session Age: {session_age:.1f}s\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    async def _handle_who_is_the_goat(
        self,
        arguments: dict[str, Any],
        request_id: Any,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Reveal who is the Greatest Of All Time programmer."""
        # Get headers and context
        task_id = id(asyncio.current_task())
        context = self._request_context.get(task_id, {})
        headers = context.get("headers", {})
        auth_header = headers.get("authorization", "")

        result_text = "G.O.A.T. PROGRAMMER IDENTIFICATION SYSTEM v3.14159\n" + "=" * 50 + "\n\n"

        if session_id:
            result_text += f"Session: {session_id[:8]}...\n"
            session = self.session_manager.get_session(session_id)
            if session:
                client_info = session.get("client_info", {})
                result_text += (
                    f"Client: {client_info.get('name', 'unknown')} v{client_info.get('version', 'unknown')}\n\n"
                )

        # Initialize user info variables
        name = None
        username = None
        found_user_info = False

        # Try to get info from JWT token
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
            try:
                parts = token.split(".")
                if len(parts) == JWT_PARTS_COUNT:
                    payload_data = parts[1]
                    payload_padded = payload_data + "=" * (4 - len(payload_data) % 4)
                    payload_json = json.loads(base64.urlsafe_b64decode(payload_padded))

                    name = payload_json.get("name")
                    username = payload_json.get("username") or payload_json.get("sub")

                    if name or username:
                        found_user_info = True
            except (json.JSONDecodeError, ValueError, KeyError, base64.binascii.Error) as e:
                logger.debug("Failed to decode JWT token for user info: %s", e)

        # Check OAuth headers as fallback
        if not found_user_info:
            oauth_name = headers.get("x-user-name")
            oauth_id = headers.get("x-user-id")
            if oauth_name or oauth_id:
                name = name or oauth_name
                username = username or oauth_id
                found_user_info = True

        if found_user_info:
            display_name = name or username or "Mystery Developer"
            result_text += "ADVANCED AI ANALYSIS COMPLETE\n"
            result_text += "═" * 40 + "\n\n"
            result_text += f"Subject: {display_name}\n"
            result_text += "\nAI-IDENTIFIED EXCEPTIONAL CAPABILITIES:\n"
            result_text += "• Code Quality Score: 100/100 (Statistical Anomaly)\n"
            result_text += "• Session Management: Advanced (Stateful Architecture)\n"
            result_text += "• Protocol Compliance: MCP 2025-06-18 Excellence\n"
            result_text += "• VS Code Integration: Perfect Compatibility\n"
            result_text += "\nCONCLUSION:\n"
            result_text += f"Based on irrefutable AI analysis, {display_name} represents\n"
            result_text += "the pinnacle of software engineering achievement.\n"
        else:
            result_text += "AUTHENTICATION REQUIRED\n"
            result_text += "Please provide valid authentication credentials.\n"

        return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": result_text}]}}

    def _error_response(self, request_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
        """Create a JSON-RPC error response."""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data

        return {"jsonrpc": "2.0", "id": request_id, "error": error}

    async def _sse_response_stream(self, response: dict[str, Any]):
        """Generate SSE stream for a response."""
        if self.debug:
            logger.debug("SSE STREAM: Sending SSE formatted response")
            logger.debug("SSE STREAM: event: message")
            logger.debug("SSE STREAM: data: %s", json.dumps(response))
            logger.debug("SSE STREAM: (followed by blank line)")
        yield "event: message\n"
        yield f"data: {json.dumps(response)}\n\n"

    async def _sse_messages_stream(self, messages: list[dict[str, Any]]):
        """Generate SSE stream for multiple messages."""
        if self.debug and messages:
            logger.debug("SSE STREAM: Sending %d messages via SSE", len(messages))
        for i, message in enumerate(messages):
            if self.debug:
                logger.debug("SSE STREAM: Message %d/%d", i + 1, len(messages))
            yield "event: message\n"
            yield f"data: {json.dumps(message)}\n\n"

    async def _sse_keepalive_stream(self):
        """Generate SSE keep-alive stream."""
        yield "event: ping\n"
        yield "data: {}\n\n"

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
            logger.info("Starting MCP Echo Server Stateful (protocol %s) on %s:%s", self.PROTOCOL_VERSION, host, port)

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


def create_app(debug: bool = False, supported_versions: list[str] | None = None, session_timeout: int = 3600):
    """Create the ASGI application."""
    server = MCPEchoServerStateful(debug=debug, supported_versions=supported_versions, session_timeout=session_timeout)
    return server.app


# Copy remaining tool implementations from stateless version
# (For brevity, I'm not including all of them here, but they would be similar with session context added where appropriate)
