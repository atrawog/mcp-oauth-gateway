#!/usr/bin/env python3
"""
Base class for MCP Echo Server implementations (stateful and stateless).

This module provides the MCPEchoServerBase abstract class that contains
common functionality shared between stateful and stateless MCP echo servers.
"""

import json
import logging
import sys
import time
from abc import ABC, abstractmethod
from contextvars import ContextVar
from pathlib import Path
from typing import Any

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Route

logger = logging.getLogger(__name__)
logging.getLogger(__name__).addHandler(logging.NullHandler())

_request_context_var: ContextVar[dict | None] = ContextVar("request_context", default=None)
_request_timing_var: ContextVar[dict | None] = ContextVar("request_timing", default=None)


class MCPEchoServerBase(ABC):
    """
    Abstract base class for MCP Echo Servers.

    Provides common functionality for both stateful and stateless
    MCP echo server implementations per the 2025-06-18 MCP specification.

    Subclasses must implement:
    - get_server_type(): Return "stateless" or "stateful"
    - get_supported_versions(): Return list of supported protocol versions
    - get_additional_headers(): Return dict of additional headers to track
    - get_additional_request_data(): Return dict of additional request data fields
    - handle_initialize(): Handle the initialize request
    """

    def __init__(self, debug: bool = False, supported_versions: list[str] | None = None):
        """
        Initialize MCP Echo Server base.

        Args:
            debug: Enable debug logging
            supported_versions: List of supported MCP protocol versions
        """
        self.debug = debug
        self.supported_versions = supported_versions or self.get_supported_versions()

        # Create Starlette application
        self.app = Starlette(
            debug=debug,
            routes=[
                Route("/", self.handle_mcp_request, methods=["GET", "POST", "OPTIONS"]),
                Route("/mcp", self.handle_mcp_request, methods=["GET", "POST", "OPTIONS"]),
            ],
        )

    # ============================================================================
    # ABSTRACT METHODS - Must be implemented by subclasses
    # ============================================================================

    @abstractmethod
    def get_server_type(self) -> str:
        """Return server type identifier ('stateless' or 'stateful')."""
        pass

    @abstractmethod
    def get_supported_versions(self) -> list[str]:
        """Return list of supported MCP protocol versions."""
        pass

    @abstractmethod
    def get_additional_headers(self) -> dict[str, str]:
        """Return additional headers to track (beyond common ones)."""
        pass

    @abstractmethod
    def get_additional_request_data(self, traefik_headers: dict[str, Any]) -> dict[str, Any]:
        """Return additional request data fields."""
        pass

    @abstractmethod
    async def handle_initialize(self, arguments: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Handle initialize request. Must be implemented by subclasses."""
        pass

    # ============================================================================
    # CONCRETE METHODS - 100% identical across implementations
    # ============================================================================

    async def _handle_post_request(self, request: Request) -> Response:
        """Handle POST requests with validation and processing."""
        # Validate headers
        validation_error = self._validate_post_headers(request)
        if validation_error:
            return validation_error

        # Store request context — ContextVar is scoped per async call-chain,
        # so no manual cleanup or id() key needed.
        _request_context_var.set({
            "headers": dict(request.headers),
            "start_time": time.time(),
            "method": request.method,
            "url": str(request.url),
        })

        return await self._process_json_rpc_request(request)

    def _validate_post_headers(self, request: Request) -> JSONResponse | None:
        """Validate required headers for POST requests."""
        content_type = request.headers.get("content-type", "")
        accept = request.headers.get("accept", "")

        # Content-Type validation
        if not content_type.startswith("application/json"):
            return JSONResponse(
                status_code=415,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Unsupported Media Type",
                        "data": {
                            "detail": "Content-Type must be application/json",
                            "received": content_type,
                        },
                    },
                    "id": None,
                },
            )

        # Accept header validation
        if accept and not (
            "application/json" in accept
            or "text/event-stream" in accept
            or "*/*" in accept
            or "application/*" in accept
        ):
            return JSONResponse(
                status_code=406,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Not Acceptable",
                        "data": {
                            "detail": "Accept must include application/json or text/event-stream",
                            "received": accept,
                        },
                    },
                    "id": None,
                },
            )

        return None

    def _error_response(self, request_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
        """Create a JSON-RPC error response."""
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {"jsonrpc": "2.0", "error": error, "id": request_id}

    async def _sse_response_stream(self, response: dict[str, Any]):
        """Generate SSE stream for a single response."""
        # Send the response as a single SSE event
        data = json.dumps(response)
        yield f"data: {data}\n\n"

    async def _sse_error_stream(self, code: int, message: str):
        """Generate SSE stream for an error."""
        error = self._error_response(None, code, message)
        data = json.dumps(error)
        yield f"data: {data}\n\n"

    def run(self, host: str = "127.0.0.1", port: int = 3000, log_file: str | None = None):
        """
        Run the MCP Echo Server.

        Args:
            host: Host to bind to
            port: Port to bind to
            log_file: Optional path to log file
        """
        # Configure logging here (run() is the application entry point, not library __init__)
        log_level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

        if log_file:
            log_file_path = Path(log_file)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(logging.DEBUG if self.debug else logging.INFO)
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )

            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)

            logger.info(f"Logging to file: {log_file_path}")

        server_type = self.get_server_type()
        logger.info(f"Starting MCP Echo Server ({server_type}) on {host}:{port}")
        logger.info(f"Supported protocol versions: {', '.join(self.supported_versions)}")
        logger.info(f"Debug mode: {'enabled' if self.debug else 'disabled'}")

        # Add startup message for SSE endpoints
        logger.info("SSE streaming endpoints:")
        logger.info("  - GET  /     -> SSE stream (OPTIONS + streaming responses)")
        logger.info("  - GET  /mcp  -> SSE stream (OPTIONS + streaming responses)")
        logger.info("JSON-RPC endpoints:")
        logger.info("  - POST /     -> Single JSON-RPC request/response")
        logger.info("  - POST /mcp  -> Single JSON-RPC request/response")

        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="debug" if self.debug else "info",
            access_log=self.debug,
        )

    # ============================================================================
    # TEMPLATE METHODS - Common structure with customizable parts
    # ============================================================================

    def _get_common_headers(self, request: Request) -> dict[str, Any]:
        """Get common Traefik headers tracked by all server types."""
        common = {
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

        # Add subclass-specific headers
        additional = self.get_additional_headers()
        for key in additional:
            common[key] = request.headers.get(key)

        return common

    def _get_base_request_data(self, request: Request, traefik_headers: dict[str, Any], start_time: float) -> dict[str, Any]:
        """Get base request data common to all server types."""
        server_type = self.get_server_type()
        data = {
            "type": f"mcp_echo_{server_type}_request",
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

        # Add subclass-specific data
        additional_data = self.get_additional_request_data(traefik_headers)
        data.update(additional_data)

        return data

    async def handle_mcp_request(self, request: Request):
        """Handle MCP requests with template method pattern."""
        # Log Traefik forwarded headers for debugging when debug mode is enabled
        if self.debug:
            start_time = time.time()

            # Get all headers (common + subclass-specific)
            traefik_headers = self._get_common_headers(request)

            # Filter out None values
            traefik_headers = {k: v for k, v in traefik_headers.items() if v is not None}

            # Create request data (base + subclass-specific)
            request_data = self._get_base_request_data(request, traefik_headers, start_time)

            # Store timing info for response logging
            _request_timing_var.set({
                "start_time": start_time,
                "request_data": request_data,
                "traefik_headers": traefik_headers,
            })

            # Log request using subclass-specific format
            self._log_request(request, traefik_headers)

        # Handle different HTTP methods
        if request.method == "OPTIONS":
            return self._handle_options_request(request)
        elif request.method == "POST":
            return await self._handle_post_request(request)
        elif request.method == "GET":
            return await self._handle_get_request(request)
        else:
            return JSONResponse(
                status_code=405,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Method Not Allowed",
                        "data": {"detail": f"Method {request.method} not supported"},
                    },
                    "id": None,
                },
            )

    @abstractmethod
    def _log_request(self, request: Request, traefik_headers: dict[str, Any]):
        """Log incoming request. Format differs by server type."""
        pass

    def _handle_options_request(self, request: Request) -> Response:
        """Handle OPTIONS request (returns capabilities)."""
        server_type = self.get_server_type()
        capabilities = {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": self.supported_versions[0] if self.supported_versions else "2025-06-18",
                "capabilities": {
                    "tools": {"listChanged": False},
                    "prompts": {"listChanged": False},
                    "resources": {"listChanged": False if server_type == "stateless" else True},
                },
                "serverInfo": {
                    "name": f"mcp-echo-{server_type}",
                    "version": "1.0.0",
                },
            },
            "id": 1,
        }

        return JSONResponse(content=capabilities, status_code=200)

    async def _handle_get_request(self, request: Request) -> Response:
        """Handle GET request (SSE streaming)."""
        # Return SSE stream with OPTIONS response
        async def stream_options():
            # Send capabilities as first event
            capabilities = {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": self.supported_versions[0] if self.supported_versions else "2025-06-18",
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "prompts": {"listChanged": False},
                        "resources": {
                            "listChanged": False if self.get_server_type() == "stateless" else True
                        },
                    },
                    "serverInfo": {
                        "name": f"mcp-echo-{self.get_server_type()}",
                        "version": "1.0.0",
                    },
                },
                "id": None,
            }

            data = json.dumps(capabilities)
            yield f"data: {data}\n\n"

        return StreamingResponse(
            stream_options(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
        )

    async def _process_json_rpc_request(self, request: Request) -> Response:
        """Process JSON-RPC request (common logic)."""
        # This method is partially shared but needs access to abstract methods
        # Implementation will continue in subclasses or be further abstracted
        pass

    async def _handle_jsonrpc_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle JSON-RPC request dispatch (template method)."""
        # This would dispatch to handle_initialize and other methods
        # Subclasses provide specific implementations
        pass
