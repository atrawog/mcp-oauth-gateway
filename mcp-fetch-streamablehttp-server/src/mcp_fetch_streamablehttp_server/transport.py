"""Native Streamable HTTP transport implementation for MCP."""

import json
import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import anyio
from anyio.streams.memory import MemoryObjectReceiveStream
from anyio.streams.memory import MemoryObjectSendStream
from mcp.shared.session import BaseSession
from mcp.shared.session import SessionMessage
from mcp.types import JSONRPCNotification
from mcp.types import JSONRPCRequest


logger = logging.getLogger(__name__)


class StreamableHTTPTransport:
    """Native implementation of MCP Streamable HTTP transport."""

    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.sessions: dict[str, BaseSession] = {}
        self._running = False

    async def handle_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        body: bytes | None,
    ) -> tuple[int, dict[str, str], bytes]:
        """Handle HTTP request and return status, headers, body."""
        # Handle CORS preflight
        if method == "OPTIONS":
            return (
                200,
                {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": ("Content-Type, Mcp-Session-Id, MCP-Protocol-Version"),
                    "Access-Control-Max-Age": "86400",
                },
                b"",
            )

        # Extract session ID from headers
        request_session_id = headers.get("mcp-session-id", headers.get("Mcp-Session-Id"))

        if method == "POST" and path == "/mcp":
            return await self._handle_post_request(headers, body, request_session_id)
        if method == "GET" and path == "/mcp":
            return await self._handle_get_request(headers, request_session_id)
        if method == "DELETE" and path == "/mcp":
            return await self._handle_delete_request(request_session_id)
        return 404, {}, json.dumps({"error": "Not found"}).encode()

    async def _handle_post_request(
        self,
        headers: dict[str, str],
        body: bytes,
        session_id: str | None,
    ) -> tuple[int, dict[str, str], bytes]:
        """Handle POST /mcp request."""
        # Validate content type
        content_type = headers.get("content-type", "").lower()
        if not content_type.startswith("application/json"):
            return (
                400,
                {},
                json.dumps(
                    {
                        "error": "Invalid content type",
                        "message": "Content-Type must be application/json",
                    },
                ).encode(),
            )

        # Parse JSON-RPC request
        try:
            data = json.loads(body)

            # Validate JSON-RPC structure
            if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
                return (
                    400,
                    {},
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32600,
                                "message": "Invalid Request",
                                "data": "Missing or invalid jsonrpc version",
                            },
                            "id": data.get("id"),
                        },
                    ).encode(),
                )

            # Convert to JSONRPCMessage
            if "method" in data:
                message = JSONRPCRequest(**data) if "id" in data else JSONRPCNotification(**data)
            else:
                return (
                    400,
                    {},
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32600,
                                "message": "Invalid Request",
                                "data": "Missing method field",
                            },
                            "id": data.get("id"),
                        },
                    ).encode(),
                )

        except json.JSONDecodeError as e:
            return (
                400,
                {},
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error",
                            "data": str(e),
                        },
                        "id": None,
                    },
                ).encode(),
            )
        except Exception as e:
            return (
                400,
                {},
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600,
                            "message": "Invalid Request",
                            "data": str(e),
                        },
                        "id": data.get("id") if "data" in locals() else None,
                    },
                ).encode(),
            )

        # Get or create session
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
        else:
            # For stateless operation, we'll handle this in the server
            return (
                200,
                {
                    "Content-Type": "application/json",
                    "Mcp-Session-Id": self.session_id,
                },
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "result": None,
                        "id": message.id if hasattr(message, "id") else None,
                    },
                ).encode(),
            )
        return None

    async def _handle_get_request(
        self,
        headers: dict[str, str],
        session_id: str | None,
    ) -> tuple[int, dict[str, str], bytes]:
        """Handle GET /mcp request for SSE."""
        # For now, return 501 Not Implemented
        # Full SSE implementation would require async streaming
        return (
            501,
            {},
            json.dumps(
                {
                    "error": "SSE not implemented",
                    "message": ("This transport currently only supports stateless POST requests"),
                },
            ).encode(),
        )

    async def _handle_delete_request(self, session_id: str | None) -> tuple[int, dict[str, str], bytes]:
        """Handle DELETE /mcp request."""
        if not session_id:
            return (
                400,
                {},
                json.dumps(
                    {
                        "error": "Missing session ID",
                        "message": "Mcp-Session-Id header is required",
                    },
                ).encode(),
            )

        if session_id in self.sessions:
            # Close session
            self.sessions.pop(session_id)
            # Cleanup would happen here
            return 200, {}, b""
        return (
            404,
            {},
            json.dumps(
                {
                    "error": "Session not found",
                    "message": f"Session {session_id} does not exist",
                },
            ).encode(),
        )

    @asynccontextmanager
    async def connect(
        self,
    ) -> AsyncGenerator[
        tuple[
            MemoryObjectReceiveStream[SessionMessage | Exception],
            MemoryObjectSendStream[SessionMessage],
        ],
        None,
    ]:
        """Create memory streams for MCP server communication."""
        # Create bidirectional memory streams
        read_stream_writer, read_stream = anyio.create_memory_object_stream[SessionMessage | Exception](0)
        write_stream, write_stream_reader = anyio.create_memory_object_stream[SessionMessage](0)

        try:
            self._running = True
            yield read_stream, write_stream
        finally:
            self._running = False
            read_stream_writer.close()
            write_stream_reader.close()
