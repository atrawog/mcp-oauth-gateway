"""Test SSE (Server-Sent Events) support for mcp-everything service.
Verifies that SSE responses flow through properly for claude.ai compatibility.
"""

import json
import re
import time
from urllib.parse import urljoin

import pytest
import requests

from tests.test_constants import BASE_DOMAIN
from tests.test_constants import GATEWAY_OAUTH_ACCESS_TOKEN
from tests.test_constants import MCP_EVERYTHING_TESTS_ENABLED


@pytest.fixture
def base_url():
    """Base URL for tests."""
    if not MCP_EVERYTHING_TESTS_ENABLED:
        pytest.skip("MCP Everything tests are disabled. Set MCP_EVERYTHING_TESTS_ENABLED=true to enable.")
    # Use HTTPS for all tests
    return f"https://everything.{BASE_DOMAIN}/"


@pytest.fixture
def auth_headers():
    """Auth headers for requests."""
    return {"Authorization": f"Bearer {GATEWAY_OAUTH_ACCESS_TOKEN}"}


class TestMCPEverythingSSE:
    """Test SSE response handling for mcp-everything echo tool."""

    def test_sse_headers_present(self, base_url, auth_headers):
        """Test that SSE middleware adds required headers."""
        # Initialize session first
        init_response = requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "sse-test-client", "version": "1.0.0"},
                },
                "id": 1,
            },
            verify=True,
        )

        # Check SSE headers are present
        assert init_response.headers.get("X-Accel-Buffering") == "no", (
            "X-Accel-Buffering header should be 'no' for SSE support"
        )
        assert init_response.headers.get("Cache-Control") == "no-cache", "Cache-Control should be 'no-cache' for SSE"
        assert init_response.headers.get("Connection") == "keep-alive", "Connection should be 'keep-alive' for SSE"

    def test_initialize_returns_sse_format(self, base_url, auth_headers):
        """Test that initialize returns proper SSE format response."""
        response = requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "sse-format-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            verify=True,
            stream=True,  # Important for SSE
        )

        assert response.status_code == 200

        # Read the SSE response
        content = response.text

        # SSE format should have event: and data: lines
        assert "event: message" in content, "Response should contain 'event: message'"
        assert "data: " in content, "Response should contain 'data: ' line"

        # Parse the SSE data
        data_match = re.search(r"data: (.+)", content)
        assert data_match, "Should find data line in SSE response"

        # Parse the JSON data
        data_json = json.loads(data_match.group(1))
        assert data_json.get("jsonrpc") == "2.0"
        assert "result" in data_json
        assert data_json["result"]["protocolVersion"] == "2025-06-18"

        # Extract session ID from the id line
        id_match = re.search(r"id: (.+)", content)
        assert id_match, "Should find id line in SSE response"
        session_id = id_match.group(1)

        return session_id

    def test_echo_tool_with_sse_response(self, base_url, auth_headers):
        """Test that echo tool returns SSE format response with echo content."""
        # Step 1: Initialize the server
        init_response = requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "sse-echo-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            verify=True,
            stream=True,
        )

        assert init_response.status_code == 200, f"Initialize failed: {init_response.text}"

        # Extract session ID from response headers
        session_id = init_response.headers.get("Mcp-Session-Id")

        # Step 2: Send initialized notification (required!)
        requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Mcp-Session-Id": session_id or "",
            },
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
                # Note: No "id" field for notifications
            },
            verify=True,
        )

        # Now test echo tool
        echo_message = "Hello from SSE test!"
        echo_response = requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Mcp-Session-Id": session_id or "",
            },
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "echo", "arguments": {"message": echo_message}},
                "id": 1,
            },
            verify=True,
            stream=True,
        )

        if echo_response.status_code != 200:
            print(f"Echo response status: {echo_response.status_code}")
            print(f"Echo response text: {echo_response.text}")
        assert echo_response.status_code == 200

        # Check SSE format
        echo_content = echo_response.text
        assert "event: message" in echo_content, "Echo response should be in SSE format"
        assert "data: " in echo_content, "Echo response should have data line"

        # Parse and verify echo response
        data_match = re.search(r"data: (.+)", echo_content)
        assert data_match, "Should find data in echo response"

        echo_data = json.loads(data_match.group(1))
        assert echo_data.get("jsonrpc") == "2.0"
        assert "result" in echo_data

        # Verify echo content
        result = echo_data["result"]
        assert "content" in result
        assert len(result["content"]) > 0

        # The echo tool should return our message
        echo_text = result["content"][0]["text"]
        assert echo_message in echo_text, f"Echo should contain our message, got: {echo_text}"

    def test_sse_streaming_not_buffered(self, base_url, auth_headers):
        """Test that SSE responses are not buffered (stream immediately)."""
        start_time = time.time()

        response = requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "stream-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            verify=True,
            stream=True,
        )

        # Read first chunk immediately
        first_chunk = None
        for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
            first_chunk = chunk
            break

        elapsed = time.time() - start_time

        # Should receive first chunk quickly (not buffered)
        assert elapsed < 2.0, f"First chunk should arrive quickly, took {elapsed}s"
        assert first_chunk is not None, "Should receive data immediately"
        assert "event: message" in first_chunk, "First chunk should contain SSE event"

    def test_multiple_tools_list_sse(self, base_url, auth_headers):
        """Test listing tools returns SSE format."""
        # Step 1: Initialize the server
        init_response = requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "sse-tools-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            verify=True,
            stream=True,
        )

        assert init_response.status_code == 200, f"Initialize failed: {init_response.text}"

        # Extract session ID from response headers
        session_id = init_response.headers.get("Mcp-Session-Id")

        # Step 2: Send initialized notification (required!)
        requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Mcp-Session-Id": session_id or "",
            },
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
                # Note: No "id" field for notifications
            },
            verify=True,
        )

        # Now list tools
        tools_response = requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Mcp-Session-Id": session_id or "",
            },
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
            verify=True,
        )

        assert tools_response.status_code == 200

        # Parse SSE response
        data_match = re.search(r"data: (.+)", tools_response.text)
        tools_data = json.loads(data_match.group(1))

        # Verify tools list contains echo
        assert "result" in tools_data
        tools = tools_data["result"]["tools"]
        assert any(tool["name"] == "echo" for tool in tools), "Tools list should contain echo tool"

    def test_error_response_in_sse_format(self, base_url, auth_headers):
        """Test that error responses also come in SSE format."""
        # Step 1: Initialize the server
        init_response = requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "sse-error-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            verify=True,
            stream=True,
        )

        assert init_response.status_code == 200, f"Initialize failed: {init_response.text}"

        # Extract session ID from response headers
        session_id = init_response.headers.get("Mcp-Session-Id")

        # Step 2: Send initialized notification (required!)
        requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Mcp-Session-Id": session_id or "",
            },
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
                # Note: No "id" field for notifications
            },
            verify=True,
        )

        # Now try to call a non-existent tool (should error)
        response = requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Mcp-Session-Id": session_id or "",
            },
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "nonexistent-tool", "arguments": {"message": "test"}},
                "id": 1,
            },
            verify=True,
        )

        # Should return 200 with SSE-formatted error
        assert response.status_code == 200

        content = response.text
        # Should be in SSE format even for errors
        assert "event: message" in content or "data: " in content, "Error response should be in SSE format"

        # Parse the error
        data_match = re.search(r"data: (.+)", content)
        if data_match:
            error_data = json.loads(data_match.group(1))
            assert "error" in error_data, "Should contain error in response"
