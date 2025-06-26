"""Comprehensive test of mcp-echo service using mcp-streamablehttp-client.

This test file follows CLAUDE.md Sacred Commandments:
- NO MOCKING - Tests against real deployed mcp-echo service
- Uses MCP_ECHO_URLS configuration from test_constants
- Uses mcp-streamablehttp-client CLI tool via subprocess
- Tests echo and printHeader tools with full protocol compliance
"""

import json
import os
import subprocess
from typing import Any

import pytest

from tests.test_constants import BASE_DOMAIN
from tests.test_constants import MCP_CLIENT_ACCESS_TOKEN
from tests.test_constants import MCP_ECHO_TESTS_ENABLED
from tests.test_constants import MCP_ECHO_URLS


@pytest.fixture()
def base_domain():
    """Base domain for tests."""
    return BASE_DOMAIN


@pytest.fixture()
def echo_url():
    """Full URL for echo service."""
    if not MCP_ECHO_TESTS_ENABLED:
        pytest.skip("MCP Echo tests are disabled. Set MCP_ECHO_TESTS_ENABLED=true to enable.")
    if not MCP_ECHO_URLS:
        pytest.skip("MCP_ECHO_URLS environment variable not set")
    return MCP_ECHO_URLS[0]


@pytest.fixture()
def client_token():
    """MCP client OAuth token for testing."""
    return MCP_CLIENT_ACCESS_TOKEN


@pytest.fixture()
async def wait_for_services():
    """Ensure all services are ready."""
    # Services are already checked by conftest
    return True


class TestMCPEchoClientFull:
    """Comprehensive test of mcp-echo using mcp-streamablehttp-client."""

    def run_mcp_client(self, url: str, token: str, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Run mcp-streamablehttp-client and return the response."""
        # Set environment variables
        env = os.environ.copy()
        env["MCP_SERVER_URL"] = url
        env["MCP_CLIENT_ACCESS_TOKEN"] = token

        # Build the raw JSON-RPC request
        request = {"jsonrpc": "2.0", "method": method, "params": params or {}}

        # Add ID for requests (not notifications)
        if method != "notifications/initialized":
            request["id"] = f"test-{method.replace('/', '-')}-1"

        # Convert to JSON string with proper escaping
        raw_request = json.dumps(request)

        # Build the command - subprocess handles escaping when using list format
        cmd = [
            "pixi",
            "run",
            "mcp-streamablehttp-client",
            "--server-url",
            url,
            "--raw",
            raw_request,
        ]

        # Run the command
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30, env=env)

        if result.returncode != 0:
            # Check if it's an expected error
            if "error" in result.stdout or "Error" in result.stdout:
                return {"error": result.stdout, "stderr": result.stderr}
            pytest.fail(f"mcp-streamablehttp-client failed: {result.stderr}\nOutput: {result.stdout}")

        # Parse the output - find the JSON response
        try:
            # Look for JSON blocks in the output
            output = result.stdout

            # Find all JSON objects in the output
            json_objects = []
            i = 0
            while i < len(output):
                if output[i] == "{":
                    # Found start of JSON, find the matching closing brace
                    brace_count = 0
                    json_start = i
                    json_end = i

                    for j in range(i, len(output)):
                        if output[j] == "{":
                            brace_count += 1
                        elif output[j] == "}":
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = j + 1
                                break

                    if brace_count == 0:
                        json_str = output[json_start:json_end]
                        try:
                            obj = json.loads(json_str)
                            # Only keep JSON-RPC responses
                            if "jsonrpc" in obj or "result" in obj or "error" in obj:
                                json_objects.append(obj)
                            i = json_end
                        except:
                            i += 1
                    else:
                        i += 1
                else:
                    i += 1

            if not json_objects:
                pytest.fail(f"No JSON-RPC response found in output: {output}")

            # Return the last JSON-RPC response
            response = json_objects[-1]

            return response

        except Exception as e:
            pytest.fail(f"Failed to parse JSON response: {e}\nOutput: {result.stdout}")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    @pytest.mark.skipif(not MCP_ECHO_TESTS_ENABLED, reason="MCP Echo tests disabled")
    async def test_echo_initialize(self, echo_url, client_token, wait_for_services):
        """Test initialize method to establish connection with mcp-echo."""
        response = self.run_mcp_client(
            url=echo_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "tools": {},
                },
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        assert "result" in response
        result = response["result"]
        assert result["protocolVersion"] == "2025-06-18"
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "mcp-echo-streamablehttp-server-stateless"
        assert "capabilities" in result

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    @pytest.mark.skipif(not MCP_ECHO_TESTS_ENABLED, reason="MCP Echo tests disabled")
    async def test_echo_list_tools(self, echo_url, client_token, wait_for_services):
        """Test listing available tools from mcp-echo service."""
        # First initialize
        self.run_mcp_client(
            url=echo_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # List tools
        response = self.run_mcp_client(url=echo_url, token=client_token, method="tools/list", params={})

        assert "result" in response
        tools = response["result"]["tools"]
        assert isinstance(tools, list)
        assert len(tools) == 10  # Now we have 10 tools including diagnostic tools

        # Check tool structure
        tool_names = []
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            tool_names.append(tool["name"])

        # Verify both original tools exist
        assert "echo" in tool_names
        assert "printHeader" in tool_names

        # Verify diagnostic tools exist
        diagnostic_tools = [
            "bearerDecode",
            "authContext",
            "requestTiming",
            "protocolNegotiation",
            "corsAnalysis",
            "environmentDump",
            "healthProbe",
            "whoIStheGOAT",
        ]
        for tool in diagnostic_tools:
            assert tool in tool_names

        print(f"✅ Found all {len(tools)} expected tools: {tool_names}")

        # Verify echo tool schema
        echo_tool = next(t for t in tools if t["name"] == "echo")
        assert echo_tool["description"] == "Echo back the provided message"
        assert "message" in echo_tool["inputSchema"]["properties"]
        assert echo_tool["inputSchema"]["required"] == ["message"]

        # Verify printHeader tool schema
        header_tool = next(t for t in tools if t["name"] == "printHeader")
        assert header_tool["description"] == "Print all HTTP headers from the current request"
        assert header_tool["inputSchema"]["properties"] == {}
        assert header_tool["inputSchema"].get("required", []) == []

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    @pytest.mark.skipif(not MCP_ECHO_TESTS_ENABLED, reason="MCP Echo tests disabled")
    async def test_echo_tool_functionality(self, echo_url, client_token, wait_for_services):
        """Test the echo tool returns the exact message provided."""
        # Initialize first
        self.run_mcp_client(
            url=echo_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # Test message with various content types (avoiding problematic shell chars)
        test_messages = [
            "Hello from MCP Echo Test! 🚀",
            "Multi-line\nmessage\nwith\nnewlines",
            "Special chars: !@#$%^&*()",  # Simplified to avoid shell parsing issues
            '{"json": "content", "with": ["arrays", "and", {"nested": "objects"}]}',
            "Unicode test: 你好世界 🌍 🎉 ⭐",
        ]

        for i, test_message in enumerate(test_messages):
            response = self.run_mcp_client(
                url=echo_url,
                token=client_token,
                method="tools/call",
                params={"name": "echo", "arguments": {"message": test_message}},
            )

            assert "result" in response, f"Test {i + 1} failed: no result in response"
            result = response["result"]
            assert "content" in result
            assert len(result["content"]) == 1
            assert result["content"][0]["type"] == "text"
            assert result["content"][0]["text"] == test_message
            print(f"✅ Echo test {i + 1}/{len(test_messages)} passed: {test_message[:50]}...")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    @pytest.mark.skipif(not MCP_ECHO_TESTS_ENABLED, reason="MCP Echo tests disabled")
    async def test_print_header_tool_functionality(self, echo_url, client_token, wait_for_services):
        """Test the printHeader tool shows HTTP headers including auth headers."""
        # Initialize first
        self.run_mcp_client(
            url=echo_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # Call printHeader tool
        response = self.run_mcp_client(
            url=echo_url,
            token=client_token,
            method="tools/call",
            params={"name": "printHeader", "arguments": {}},
        )

        assert "result" in response
        result = response["result"]
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"

        headers_text = result["content"][0]["text"]
        assert "HTTP Headers:" in headers_text

        # Check for expected headers that should be present
        expected_headers = [
            "authorization:",  # Should show Bearer token
            "content-type:",  # Should show application/json
            "accept:",  # Should show application/json, text/event-stream
            "host:",  # Should show the hostname
        ]

        for expected_header in expected_headers:
            assert (
                expected_header in headers_text.lower()
            ), f"Expected header '{expected_header}' not found in: {headers_text}"

        # Verify authorization header shows Bearer token (converted to lowercase)
        assert "authorization: bearer" in headers_text.lower()
        print("✅ printHeader tool shows expected HTTP headers including auth")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    @pytest.mark.skipif(not MCP_ECHO_TESTS_ENABLED, reason="MCP Echo tests disabled")
    async def test_echo_tool_error_handling(self, echo_url, client_token, wait_for_services):
        """Test error handling for invalid tool usage."""
        # Initialize first
        self.run_mcp_client(
            url=echo_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # Test 1: Call echo without required message argument
        response = self.run_mcp_client(
            url=echo_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "echo",
                "arguments": {},  # Missing required 'message'
            },
        )

        # Should get an error response
        assert "error" in response
        error_text = str(response["error"])
        assert "message" in error_text.lower()
        print("✅ Echo tool properly rejects missing message argument")

        # Test 2: Call invalid tool name
        response = self.run_mcp_client(
            url=echo_url,
            token=client_token,
            method="tools/call",
            params={"name": "invalid_tool_name", "arguments": {}},
        )

        # Should get an error response
        assert "error" in response
        error_text = str(response["error"])
        assert "unknown tool" in error_text.lower() or "invalid_tool_name" in error_text.lower()
        print("✅ Echo service properly rejects invalid tool names")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    @pytest.mark.skipif(not MCP_ECHO_TESTS_ENABLED, reason="MCP Echo tests disabled")
    async def test_print_header_tool_error_handling(self, echo_url, client_token, wait_for_services):
        """Test that printHeader tool handles extra arguments gracefully."""
        # Initialize first
        self.run_mcp_client(
            url=echo_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # Call printHeader with extra arguments (should work - tool ignores extra args)
        response = self.run_mcp_client(
            url=echo_url,
            token=client_token,
            method="tools/call",
            params={"name": "printHeader", "arguments": {"extra_arg": "should_be_ignored", "another_arg": 123}},
        )

        # Should still work - printHeader ignores extra arguments
        assert "result" in response
        result = response["result"]
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"

        headers_text = result["content"][0]["text"]
        assert "HTTP Headers:" in headers_text
        print("✅ printHeader tool handles extra arguments gracefully")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    @pytest.mark.skipif(not MCP_ECHO_TESTS_ENABLED, reason="MCP Echo tests disabled")
    async def test_echo_stateless_behavior(self, echo_url, client_token, wait_for_services):
        """Test that mcp-echo service is truly stateless - each request is independent."""
        # Test multiple independent tool calls without reinitializing
        for i in range(5):
            # Each call should work independently without maintaining state
            # We intentionally do NOT call initialize again to test stateless behavior

            if i == 0:
                # Initialize only once
                self.run_mcp_client(
                    url=echo_url,
                    token=client_token,
                    method="initialize",
                    params={
                        "protocolVersion": "2025-06-18",
                        "capabilities": {"tools": {}},
                        "clientInfo": {"name": "test-client", "version": "1.0.0"},
                    },
                )

            # Test echo tool
            echo_response = self.run_mcp_client(
                url=echo_url,
                token=client_token,
                method="tools/call",
                params={"name": "echo", "arguments": {"message": f"Stateless test {i}"}},
            )

            assert "result" in echo_response
            assert echo_response["result"]["content"][0]["text"] == f"Stateless test {i}"

            # Test printHeader tool in same iteration
            header_response = self.run_mcp_client(
                url=echo_url,
                token=client_token,
                method="tools/call",
                params={"name": "printHeader", "arguments": {}},
            )

            assert "result" in header_response
            headers_text = header_response["result"]["content"][0]["text"]
            assert "HTTP Headers:" in headers_text

            print(f"✅ Stateless test iteration {i + 1}/5 completed")

        print("✅ mcp-echo service demonstrates proper stateless behavior")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    @pytest.mark.skipif(not MCP_ECHO_TESTS_ENABLED, reason="MCP Echo tests disabled")
    async def test_echo_protocol_compliance(self, echo_url, client_token, wait_for_services):
        """Test MCP protocol compliance with proper versioning."""
        # Test with different protocol versions to ensure compliance
        protocol_versions = ["2025-06-18", "2024-11-05"]

        for version in protocol_versions:
            response = self.run_mcp_client(
                url=echo_url,
                token=client_token,
                method="initialize",
                params={
                    "protocolVersion": version,
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"},
                },
            )

            # Handle both success and error responses
            if "result" in response:
                result = response["result"]

                # Server should respond with supported protocol version
                assert "protocolVersion" in result
                server_version = result["protocolVersion"]

                # For mcp-echo, it should support the current version
                if version == "2025-06-18":
                    assert server_version == "2025-06-18"
                    print(f"✅ Protocol version {version} properly supported")
                else:
                    # Older versions may be supported or rejected - both are valid
                    print(f"i  Protocol version {version} response: {server_version}")
            elif "error" in response:
                # Server rejected the protocol version - this is valid behavior
                error = response["error"]
                if version == "2024-11-05":
                    # Old version rejection is expected
                    print(f"i  Protocol version {version} properly rejected: {error}")
                else:
                    # Current version should not be rejected
                    pytest.fail(f"Current protocol version {version} was rejected: {error}")
            else:
                pytest.fail(f"Invalid response format for protocol version {version}: {response}")

        print("✅ mcp-echo service demonstrates proper protocol versioning")
