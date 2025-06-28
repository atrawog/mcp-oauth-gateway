"""Streamable HTTP to stdio proxy for MCP servers with OAuth support."""

import asyncio
import json
import logging
import sys
from typing import Any

import httpx
from httpx import HTTPError

from .config import Settings
from .oauth import OAuthClient


logger = logging.getLogger(__name__)


class StreamableHttpToStdioProxy:
    """Proxy that converts MCP Streamable HTTP transport to stdio for local clients.

    This allows tools like Claude Desktop to connect to remote MCP servers
    that use streamable HTTP transport and require OAuth authentication.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session_id: str | None = None
        self.http_client: httpx.AsyncClient | None = None
        self.oauth_client: OAuthClient | None = None
        self.access_token: str | None = None
        self._running = False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self) -> None:
        """Initialize the proxy and authenticate."""
        logger.info("Starting Streamable HTTP-to-stdio client")

        # Create HTTP client
        self.http_client = httpx.AsyncClient(
            verify=self.settings.verify_ssl,
            timeout=httpx.Timeout(self.settings.request_timeout),
        )

        # Create OAuth client and authenticate
        self.oauth_client = OAuthClient(self.settings)
        async with self.oauth_client as oauth:
            self.access_token = await oauth.ensure_authenticated()

        self._running = True
        logger.info("Client initialized and authenticated")

    async def stop(self) -> None:
        """Clean up resources."""
        self._running = False

        if self.http_client:
            await self.http_client.aclose()

        logger.info("Client stopped")

    async def run(self) -> None:
        """Main proxy loop - read from stdin, forward to HTTP, write to stdout."""
        logger.info("Starting stdio client loop")

        # Set up async stdio
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)

        loop = asyncio.get_event_loop()
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        # Create tasks for reading and writing
        read_task = asyncio.create_task(self._read_loop(reader))

        try:
            await read_task
        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down")
        except Exception as e:
            logger.error(f"Client error: {e}")
            raise
        finally:
            self._running = False

    async def _read_loop(self, reader: asyncio.StreamReader) -> None:
        """Read JSON-RPC messages from stdin and process them."""
        buffer = ""

        while self._running:
            try:
                # Read data from stdin
                data = await reader.read(4096)
                if not data:
                    break

                # Add to buffer and process complete lines
                buffer += data.decode("utf-8")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()

                    if not line:
                        continue

                    # Parse JSON-RPC request
                    try:
                        request = json.loads(line)
                        response = await self._handle_request(request)

                        # Write response to stdout
                        response_line = json.dumps(response) + "\n"
                        sys.stdout.write(response_line)
                        sys.stdout.flush()

                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON received: {e}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "error": {"code": -32700, "message": "Parse error"},
                            "id": None,
                        }
                        sys.stdout.write(json.dumps(error_response) + "\n")
                        sys.stdout.flush()

            except Exception as e:
                logger.error(f"Read loop error: {e}")
                break

    async def _handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle a JSON-RPC request by forwarding to HTTP server."""
        method = request.get("method", "")
        request_id = request.get("id")

        logger.debug(f"Handling request: {method}")

        try:
            # Special handling for initialize
            if method == "initialize":
                # Don't include session ID in initialize request
                self.session_id = None
                logger.info("Initializing new session...")

            # Check if we need to refresh token
            if not self.settings.has_valid_credentials():
                logger.info("Token expired, refreshing...")
                async with self.oauth_client as oauth:
                    await oauth.refresh_token()
                    self.access_token = self.settings.oauth_access_token

            # Forward request to HTTP server
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": "2025-06-18",
            }

            logger.debug(f"Request headers: {headers}")

            if self.session_id:
                headers["Mcp-Session-Id"] = self.session_id

            logger.info(f"Sending request to {self.settings.mcp_server_url}")
            logger.info(f"Headers: {headers}")
            logger.info(f"Request: {request}")

            response = await self.http_client.post(self.settings.mcp_server_url, json=request, headers=headers)

            # Handle authentication errors
            if response.status_code == 401:
                logger.warning("Authentication failed, re-authenticating...")
                async with self.oauth_client as oauth:
                    self.access_token = await oauth.ensure_authenticated()

                # Retry request with new token
                headers["Authorization"] = f"Bearer {self.access_token}"
                response = await self.http_client.post(self.settings.mcp_server_url, json=request, headers=headers)

            response.raise_for_status()

            # Update session ID if returned
            if "Mcp-Session-Id" in response.headers:
                self.session_id = response.headers["Mcp-Session-Id"]
                logger.info(f"Got session ID: {self.session_id}")

            # Parse response based on content type
            content_type = response.headers.get("content-type", "").lower()

            if "text/event-stream" in content_type:
                # Parse SSE response
                for line in response.text.strip().split("\n"):
                    if line.startswith("data: "):
                        result = json.loads(line[6:])
                        break
                else:
                    # If no data found, return empty response
                    result = {"jsonrpc": "2.0", "id": request_id, "result": None}
            else:
                # Standard JSON response
                result = response.json()

            # Send initialized notification after successful initialize
            if method == "initialize" and "result" in result and not result.get("error"):
                logger.info("Sending notifications/initialized")
                notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
                # Update headers to include session ID if we have one
                notif_headers = headers.copy()
                if self.session_id:
                    notif_headers["Mcp-Session-Id"] = self.session_id
                # Send notification without waiting for response
                try:
                    notif_resp = await self.http_client.post(
                        self.settings.mcp_server_url,
                        json=notification,
                        headers=notif_headers,
                    )
                    logger.info(f"Initialized notification response: {notif_resp.status_code}")
                    if notif_resp.status_code not in (200, 202, 204):
                        logger.warning(
                            f"Unexpected notification response: {notif_resp.status_code} - {notif_resp.text}",  # TODO: Break long line
                        )
                except Exception as e:
                    logger.warning(f"Failed to send initialized notification: {e}")

            return result

        except HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"HTTP error: {e!s}"},
            }
        except Exception as e:
            logger.error(f"Request handling error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"Internal error: {e!s}"},
            }

    async def handle_notifications(self) -> None:
        """Handle server-initiated notifications if supported."""
        # This could be extended to support server-sent events or websockets
        # For now, we only support request-response pattern
