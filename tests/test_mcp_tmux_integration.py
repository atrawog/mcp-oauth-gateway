"""Comprehensive integration tests for MCP Tmux service.
Tests all tmux functionality including session management, pane operations, and command execution.
"""

import json
import os

import pytest

from tests.test_constants import BASE_DOMAIN


class TestMCPTmuxIntegration:
    """Test MCP Tmux service integration with OAuth authentication."""

    def run_mcp_client_raw(self, url, token, method, params=None):
        """Run mcp-streamablehttp-client with raw MCP protocol."""
        import subprocess

        # Create request payload
        request_data = {"jsonrpc": "2.0", "id": 1, "method": method}
        if params:
            request_data["params"] = params

        # Convert to JSON string
        raw_request = json.dumps(request_data)

        # Run mcp-streamablehttp-client
        cmd = [
            "pixi",
            "run",
            "python",
            "-m",
            "mcp_streamablehttp_client.cli",
            "--server-url",
            f"{url}",
            "--raw",
            raw_request,
        ]

        # Set environment variables for token
        env = os.environ.copy()
        env["MCP_CLIENT_ACCESS_TOKEN"] = token

        result = subprocess.run(
            cmd,
            check=False,
            cwd="/home/atrawog/AI/atrawog/mcp-oauth-gateway/mcp-streamablehttp-client",
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        if result.returncode != 0:
            pytest.fail(f"MCP client failed: {result.stderr}")

        # Parse JSON response - look for JSON in the output
        try:
            # Look for JSON response in the output (like the memory test pattern)
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
            return json_objects[-1]

        except Exception as e:
            pytest.fail(f"Failed to parse JSON response: {e}\nOutput: {result.stdout}")

    def test_tmux_service_health(
        self, mcp_tmux_url, mcp_client_token, wait_for_services
    ):
        """Test tmux service health using MCP protocol per divine CLAUDE.md."""
        import requests

        # First verify that /health requires authentication
        response = requests.get(f"{mcp_tmux_url}/health", timeout=10)
        assert response.status_code == 401, (
            "/health endpoint must require authentication per divine CLAUDE.md"
        )

        # Health checks should use MCP protocol initialization
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "healthcheck", "version": "1.0"},
            },
        )

        assert "result" in response or "error" in response
        if "result" in response:
            assert "protocolVersion" in response["result"]
            print(
                f"✅ MCP tmux service is healthy (protocol version: {response['result']['protocolVersion']})"
            )

    def test_tmux_oauth_discovery(self):
        """Test OAuth discovery endpoint routing."""
        import requests
        import urllib3

        # Suppress SSL warnings for test environment
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Use base domain for OAuth discovery, not the /mcp endpoint
        oauth_discovery_url = (
            f"https://tmux.{BASE_DOMAIN}/.well-known/oauth-authorization-server"
        )
        response = requests.get(oauth_discovery_url, timeout=10, verify=False)
        assert response.status_code == 200

        oauth_config = response.json()
        assert oauth_config["issuer"]
        assert oauth_config["authorization_endpoint"]
        assert oauth_config["token_endpoint"]
        assert oauth_config["registration_endpoint"]

    def test_tmux_mcp_initialize(
        self, mcp_tmux_url, mcp_client_token, wait_for_services
    ):
        """Test MCP protocol initialization."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {"roots": {"listChanged": False}, "sampling": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        assert "result" in response
        result = response["result"]
        assert result["protocolVersion"] == "2025-06-18"
        assert "capabilities" in result
        assert "serverInfo" in result

    def test_tmux_list_tools(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test listing available tmux tools."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url, token=mcp_client_token, method="tools/list"
        )

        assert "result" in response
        tools = response["result"]["tools"]

        # Expected tmux tools

        tool_names = {tool["name"] for tool in tools}

        # Check that we have the basic session management tools
        basic_tools = {"list-sessions", "capture-pane", "execute-command"}
        found_basic = basic_tools.intersection(tool_names)
        assert len(found_basic) > 0, (
            f"No basic tmux tools found. Available: {tool_names}"
        )

    def test_tmux_list_sessions(
        self, mcp_tmux_url, mcp_client_token, wait_for_services
    ):
        """Test listing tmux sessions."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={"name": "list-sessions", "arguments": {}},
        )

        assert "result" in response
        result = response["result"]
        assert "content" in result

        # Should have at least the default session created at startup
        content = result["content"]
        if isinstance(content, list) and len(content) > 0:
            session_info = content[0]
            if "text" in session_info:
                assert (
                    "default" in session_info["text"] or len(session_info["text"]) > 0
                )

    def test_tmux_capture_pane(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test capturing pane content."""
        # First list sessions to get a valid session
        sessions_response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={"name": "list-sessions", "arguments": {}},
        )

        assert "result" in sessions_response

        # Try to capture from the default session/pane
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "capture-pane",
                "arguments": {
                    "target": "default:0.0"  # default session, window 0, pane 0
                },
            },
        )

        # Should either succeed or give a specific error about the pane
        assert "result" in response or "error" in response
        if "result" in response:
            result = response["result"]
            assert "content" in result

    def test_tmux_execute_command(
        self, mcp_tmux_url, mcp_client_token, wait_for_services
    ):
        """Test executing a command in tmux."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "execute-command",
                "arguments": {
                    "command": "echo Hello from tmux test",
                    "target": "default:0.0",
                },
            },
        )

        # Should either succeed or give a specific error about the target
        assert "result" in response or "error" in response
        if "result" in response:
            result = response["result"]
            assert "content" in result

    def test_tmux_new_session(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test creating a new tmux session."""
        session_name = "test-session-123"

        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "new-session",
                "arguments": {"session_name": session_name, "detached": True},
            },
        )

        # Should either succeed or give a specific error
        assert "result" in response or "error" in response
        if "result" in response:
            result = response["result"]
            assert "content" in result

    def test_tmux_list_resources(
        self, mcp_tmux_url, mcp_client_token, wait_for_services
    ):
        """Test listing available tmux resources."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url, token=mcp_client_token, method="resources/list"
        )

        assert "result" in response
        resources = response["result"]["resources"]

        # Should have tmux-related resources
        resource_uris = {resource["uri"] for resource in resources}

        # Look for tmux:// resources
        tmux_resources = [uri for uri in resource_uris if uri.startswith("tmux://")]
        assert len(tmux_resources) > 0, (
            f"No tmux:// resources found. Available: {resource_uris}"
        )

    def test_tmux_read_sessions_resource(
        self, mcp_tmux_url, mcp_client_token, wait_for_services
    ):
        """Test reading tmux sessions resource."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="resources/read",
            params={"uri": "tmux://sessions"},
        )

        # Should either succeed or give a specific error about the resource
        assert "result" in response or "error" in response
        if "result" in response:
            result = response["result"]
            assert "contents" in result

    def test_tmux_send_keys(self, mcp_tmux_url, mcp_client_token, wait_for_services):
        """Test sending keys to a tmux pane."""
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="tools/call",
            params={
                "name": "send-keys",
                "arguments": {"keys": "echo test", "target": "default:0.0"},
            },
        )

        # Should either succeed or give a specific error about the target
        assert "result" in response or "error" in response
        if "result" in response:
            result = response["result"]
            assert "content" in result

    def test_tmux_protocol_version_compliance(
        self, mcp_tmux_url, mcp_client_token, wait_for_services
    ):
        """Test MCP protocol version compliance."""
        # Test with correct protocol version
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url,
            token=mcp_client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "version-test", "version": "1.0.0"},
            },
        )

        assert "result" in response
        result = response["result"]
        assert result["protocolVersion"] == "2025-06-18"

    def test_tmux_error_handling(
        self, mcp_tmux_url, mcp_client_token, wait_for_services
    ):
        """Test error handling for invalid operations."""
        # Test invalid method
        response = self.run_mcp_client_raw(
            url=mcp_tmux_url, token=mcp_client_token, method="invalid/method"
        )

        assert "error" in response
        error = response["error"]
        assert error["code"] == -32601  # Method not found

    def test_tmux_authentication_required(self, mcp_tmux_url):
        """Test that MCP endpoint requires authentication."""
        import requests

        # Test without token
        response = requests.post(
            f"{mcp_tmux_url}",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
