"""
Simple SSE tests focusing on verifying the headers fix for claude.ai.
Tests that SSE responses can flow through without buffering.
"""

import json
import pytest
import requests
import time
from urllib.parse import urljoin
import re

from tests.test_constants import BASE_DOMAIN
from tests.test_constants import GATEWAY_OAUTH_ACCESS_TOKEN
from tests.test_constants import MCP_EVERYTHING_TESTS_ENABLED


@pytest.fixture
def base_url():
    """Base URL for tests."""
    if not MCP_EVERYTHING_TESTS_ENABLED:
        pytest.skip(
            "MCP Everything tests are disabled. Set MCP_EVERYTHING_TESTS_ENABLED=true to enable."
        )
    return f"https://everything.{BASE_DOMAIN}/"


@pytest.fixture
def auth_headers():
    """Auth headers for requests."""
    return {"Authorization": f"Bearer {GATEWAY_OAUTH_ACCESS_TOKEN}"}


class TestMCPEverythingSSESimple:
    """Simple tests to verify SSE support is working."""

    def test_sse_headers_on_initialize(self, base_url, auth_headers):
        """Test that SSE middleware headers are present on initialize."""
        response = requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "header-test",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            },
            verify=True
        )
        
        # These headers should be added by our middleware
        assert response.headers.get("X-Accel-Buffering") == "no", \
            "X-Accel-Buffering header should be 'no'"
        assert response.headers.get("Cache-Control") == "no-cache", \
            "Cache-Control should be 'no-cache'"
        assert response.headers.get("Connection") == "keep-alive", \
            "Connection should be 'keep-alive'"
        
        # Response should be successful
        assert response.status_code == 200
        assert "event: message" in response.text
        assert "data: " in response.text

    def test_sse_format_preserved(self, base_url, auth_headers):
        """Test that SSE format is preserved through the gateway."""
        response = requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "format-test",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            },
            verify=True
        )
        
        # Verify SSE format
        lines = response.text.strip().split('\n')
        assert any(line.startswith("event: ") for line in lines), \
            "Should have event: line"
        assert any(line.startswith("id: ") for line in lines), \
            "Should have id: line"
        assert any(line.startswith("data: ") for line in lines), \
            "Should have data: line"
        
        # Parse the JSON from data line
        for line in lines:
            if line.startswith("data: "):
                data = json.loads(line[6:])
                assert data["jsonrpc"] == "2.0"
                assert "result" in data
                break

    def test_no_buffering_delay(self, base_url, auth_headers):
        """Test that responses are not buffered (arrive quickly)."""
        start_time = time.time()
        
        response = requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "speed-test",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            },
            verify=True,
            stream=True  # Stream the response
        )
        
        # Read first chunk
        first_chunk = None
        for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
            first_chunk = chunk
            break
        
        elapsed = time.time() - start_time
        
        # Should receive data quickly (not buffered)
        assert elapsed < 2.0, f"Response took {elapsed}s, might be buffered"
        assert first_chunk is not None
        assert "event: message" in first_chunk

    def test_json_error_handling(self, base_url, auth_headers):
        """Test that JSON errors are handled properly."""
        # Send invalid request
        response = requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            json={
                "jsonrpc": "2.0",
                "method": "invalid-method",
                "params": {},
                "id": 1
            },
            verify=True
        )
        
        # Native streamableHttp might return JSON errors
        if response.status_code == 400:
            # JSON error response
            error_data = response.json()
            assert "error" in error_data
            assert error_data["jsonrpc"] == "2.0"
        else:
            # SSE error response
            assert "event: message" in response.text
            data_match = re.search(r'data: (.+)', response.text)
            if data_match:
                data = json.loads(data_match.group(1))
                assert "error" in data

    def test_cors_headers_present(self, base_url, auth_headers):
        """Test that CORS headers are properly set for claude.ai."""
        response = requests.post(
            urljoin(base_url, "mcp"),
            headers={
                **auth_headers,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Origin": "https://claude.ai"
            },
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "cors-test",
                        "version": "1.0.0"
                    }
                },
                "id": 1
            },
            verify=True
        )
        
        # Check CORS headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Credentials" in response.headers