"""Core proxy functionality for bridging stdio MCP servers to HTTP."""

import asyncio
import json
import logging
import subprocess
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class MCPSession:
    """Individual MCP session with its own subprocess."""

    def __init__(self, session_id: str, server_command: List[str]):
        self.session_id = session_id
        self.server_command = server_command
        self.process: Optional[subprocess.Popen] = None
        self.session_initialized = False
        self.request_id_counter = 0
        self.pending_responses: Dict[int, asyncio.Future] = {}
        self.server_capabilities: Dict[str, Any] = {}
        self.server_info: Dict[str, Any] = {}
        self.available_tools: List[Dict[str, Any]] = []
        self.last_activity = time.time()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._read_task: Optional[asyncio.Task] = None

    async def start_server(self):
        """Start the underlying MCP server process."""
        logger.info(
            f"Starting MCP server for session {self.session_id}: {' '.join(self.server_command)}",  # TODO: Break long line
        )

        self.process = await asyncio.create_subprocess_exec(
            *self.server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Start reading responses from the server
        self._read_task = asyncio.create_task(self._read_responses())

        # Don't auto-initialize - wait for client to send initialize request

    async def _read_responses(self):
        """Read responses from the server stdout."""
        while self.process and self.process.stdout:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    break

                line = line.decode().strip()
                if not line:
                    continue

                try:
                    response = json.loads(line)
                    await self._handle_response(response)
                except json.JSONDecodeError:
                    logger.warning(
                        f"Session {self.session_id}: Invalid JSON from server: {line}",
                    )  # TODO: Break long line
                    continue

            except Exception as e:
                logger.error(
                    f"Session {self.session_id}: Error reading from server: {e}",
                )  # TODO: Break long line
                break

    async def _handle_response(self, response: Dict[str, Any]):
        """Handle a response from the server."""
        request_id = response.get("id")

        if request_id is not None and request_id in self.pending_responses:
            # This is a response to one of our requests
            future = self.pending_responses.pop(request_id)
            if not future.cancelled():
                future.set_result(response)
        else:
            # This might be a notification or unsolicited message
            logger.debug(
                f"Session {self.session_id}: Received unsolicited message: {response}",
            )  # TODO: Break long line

    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the server and wait for response."""
        if not self.process or not self.process.stdin:
            raise RuntimeError(
                f"Session {self.session_id}: Server process not available",
            )  # TODO: Break long line

        # Update activity timestamp
        self.last_activity = time.time()

        request_id = request.get("id")
        if request_id is not None:
            # Create future for response
            future = asyncio.Future()
            self.pending_responses[request_id] = future

        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()

        if request_id is not None:
            # Wait for response
            try:
                response = await asyncio.wait_for(future, timeout=30.0)
                return response
            except asyncio.TimeoutError as e:
                self.pending_responses.pop(request_id, None)
                raise RuntimeError(f"Session {self.session_id}: Request timeout") from e

        return {}

    # _initialize_session method removed - initialization is handled directly in handle_request
    async def _list_tools(self):
        """Get list of available tools from the server."""
        self.request_id_counter += 1

        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": self.request_id_counter,
        }

        response = await self._send_request(request)

        if "error" in response:
            logger.error(
                f"Session {self.session_id}: Failed to list tools: {response['error']}",
            )  # TODO: Break long line
            return

        result = response.get("result", {})
        self.available_tools = result.get("tools", [])
        logger.info(
            f"Session {self.session_id}: Available tools: {[t.get('name') for t in self.available_tools]}",  # TODO: Break long line
        )

    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming MCP request."""
        method = request_data.get("method")
        if method == "initialize":
            if not self.session_initialized:
                # Log the incoming request for debugging
                logger.info(
                    f"Session {self.session_id}: Initialize request: {json.dumps(request_data, indent=2)}",  # TODO: Break long line
                )

                # Forward the initialize request to the underlying server
                response = await self._send_request(request_data)
                logger.info(
                    f"Session {self.session_id}: Initialize response from server: {json.dumps(response, indent=2)}",  # TODO: Break long line
                )

                # If successful, complete the initialization process
                if "result" in response:
                    self.session_initialized = True
                    self.server_capabilities = response["result"].get("capabilities", {})
                    self.server_info = response["result"].get("serverInfo", {})

                    # Send initialized notification
                    initialized_notification = {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized",
                        "params": {},
                    }
                    await self._send_request(initialized_notification)

                    # Get available tools
                    await self._list_tools()

                    logger.info(f"Session {self.session_id} initialized successfully")

                return response
            else:
                # Already initialized
                return {
                    "jsonrpc": "2.0",
                    "id": request_data.get("id"),
                    "error": {"code": -32603, "message": "Session already initialized"},
                }

        # Only check initialization for non-initialize requests
        if method != "initialize" and not self.session_initialized:
            raise RuntimeError(f"Session {self.session_id} not initialized")

        logger.info(
            f"Session {self.session_id}: Handling MCP request: {json.dumps(request_data, indent=2)}",  # TODO: Break long line
        )

        # Update activity timestamp
        self.last_activity = time.time()

        # Forward the request to the server
        if "id" not in request_data:
            self.request_id_counter += 1
            request_data["id"] = self.request_id_counter

        response = await self._send_request(request_data)
        logger.info(
            f"Session {self.session_id}: MCP server response: {json.dumps(response, indent=2)}",  # TODO: Break long line
        )
        return response

    async def close(self):
        """Close the server process."""
        logger.info(f"Closing session {self.session_id}")

        if self._cleanup_task:
            self._cleanup_task.cancel()

        if self._read_task:
            self._read_task.cancel()

        # Cancel all pending responses
        for future in self.pending_responses.values():
            if not future.cancelled():
                future.cancel()
        self.pending_responses.clear()

        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except (ProcessLookupError, OSError):
                # Process already terminated or system error - this is fine
                pass
            self.process = None

        self.session_initialized = False


class MCPSessionManager:
    """Manages multiple MCP sessions."""

    def __init__(self, server_command: List[str], session_timeout: int = 300):
        self.server_command = server_command
        self.sessions: Dict[str, MCPSession] = {}
        self.session_timeout = session_timeout  # Default 5 minutes
        self._cleanup_task: Optional[asyncio.Task] = None
        # Proxy is protocol-agnostic - it forwards whatever the client requests

    async def start(self):
        """Start the session manager."""
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

    async def stop(self):
        """Stop the session manager and clean up all sessions."""
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # Close all sessions
        for session in list(self.sessions.values()):
            await session.close()
        self.sessions.clear()

    async def get_or_create_session(self, session_id: Optional[str] = None) -> MCPSession:
        """Get existing session or create a new one."""
        if session_id is None:
            session_id = str(uuid4())

        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.last_activity = time.time()
            return session

        # Create new session
        session = MCPSession(session_id, self.server_command)
        await session.start_server()
        self.sessions[session_id] = session

        logger.info(
            f"Created new session {session_id}. Total sessions: {len(self.sessions)}",
        )  # TODO: Break long line
        return session

    async def handle_request(
        self,
        request_data: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> tuple[Dict[str, Any], str]:
        """Handle MCP request and return response with session ID."""
        method = request_data.get("method")

        # Handle initialize requests specially - they create new sessions
        if method == "initialize":
            # Log requested version - we'll accept any and forward to underlying server
            requested_version = request_data.get("params", {}).get("protocolVersion")
            if requested_version:
                logger.info(
                    f"Client requested protocol version: {requested_version}, forwarding to underlying MCP server",  # TODO: Break long line
                )

            # Don't allow re-initialization of existing sessions
            if session_id and session_id in self.sessions:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_data.get("id"),
                    "error": {"code": -32603, "message": "Session already initialized"},
                }
                return response, session_id

            # Create new session
            new_session_id = str(uuid4())
            session = MCPSession(new_session_id, self.server_command)

            # Start the subprocess
            await session.start_server()

            # Store the session
            self.sessions[new_session_id] = session
            logger.info(
                f"Created new session {new_session_id}. Total sessions: {len(self.sessions)}",  # TODO: Break long line
            )

            # Let the session handle the initialize request completely
            response = await session.handle_request(request_data)

            return response, new_session_id

        # For other requests, require a valid session ID
        if not session_id:
            # No session ID provided - this is an error for non-initialize requests
            response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32002,
                    "message": "Session ID required. Please include Mcp-Session-Id header from initialize response.",
                },
            }
            return response, ""

        # Check if session exists
        if session_id not in self.sessions:
            response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32002,
                    "message": f"Invalid session ID: {session_id}. Session may have expired or does not exist.",  # TODO: Break long line
                },
            }
            return response, ""

        # Use existing session
        session = self.sessions[session_id]
        session.last_activity = time.time()
        response = await session.handle_request(request_data)
        return response, session.session_id

    async def _cleanup_expired_sessions(self):
        """Periodically clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                current_time = time.time()
                expired_sessions = []

                for session_id, session in self.sessions.items():
                    if current_time - session.last_activity > self.session_timeout:
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    session = self.sessions.pop(session_id, None)
                    if session:
                        await session.close()
                        logger.info(f"Cleaned up expired session {session_id}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")


def create_app(server_command: List[str], session_timeout: int = 300) -> FastAPI:
    """Create FastAPI app with MCP proxy endpoints."""
    app = FastAPI()

    # CORS is handled by Traefik middleware - no need to configure here
    # This ensures CORS headers are set in only one place as required

    # Create session manager
    session_manager = MCPSessionManager(server_command, session_timeout)

    @app.on_event("startup")
    async def startup_event():
        """Initialize the session manager on startup."""
        await session_manager.start()

    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up on shutdown."""
        await session_manager.stop()

    # Health checks now done via MCP protocol initialization

    @app.options("/mcp")
    async def handle_mcp_options():
        """Handle CORS preflight for MCP endpoint."""
        # The CORS middleware will handle the actual response headers
        # We just need to return 200 OK to indicate the endpoint accepts OPTIONS
        return {"status": "ok"}

    @app.post("/mcp")
    async def handle_mcp(request: Request):
        """Handle MCP requests without trailing slash redirect."""
        # CORS is handled by Traefik middleware - no validation needed here

        try:
            request_data = await request.json()
            method = request_data.get("method", "unknown")

            # Extract session ID from headers if present
            session_id = request.headers.get("Mcp-Session-Id")

            # Log session tracking info
            if method == "initialize":
                logger.info("Initialize request received. Creating new session...")
            else:
                logger.info(
                    f"Request for method '{method}' with session ID: {session_id or 'MISSING'}",  # TODO: Break long line
                )

            response, returned_session_id = await session_manager.handle_request(
                request_data,
                session_id,
            )

            # Create response with session ID header
            json_response = JSONResponse(content=response)
            if returned_session_id:
                json_response.headers["Mcp-Session-Id"] = returned_session_id
                logger.info(f"Response includes session ID: {returned_session_id}")

            return json_response

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": str(e)},
                    "id": None,
                },
            )

    @app.post("/mcp/")
    async def handle_mcp_trailing(request: Request):
        """Handle MCP requests with trailing slash."""
        # Origin validation is handled in handle_mcp
        return await handle_mcp(request)

    return app
