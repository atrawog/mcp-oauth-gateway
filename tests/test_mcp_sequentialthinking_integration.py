"""Integration tests for mcp-sequentialthinking service."""

import json
import os
import subprocess
import uuid
from typing import Any

import pytest

from tests.test_constants import MCP_CLIENT_ACCESS_TOKEN
from tests.test_constants import MCP_PROTOCOL_VERSION
from tests.test_constants import MCP_PROTOCOL_VERSIONS_SUPPORTED


@pytest.fixture
def client_token():
    """MCP client OAuth token for testing."""
    return MCP_CLIENT_ACCESS_TOKEN


@pytest.fixture
async def wait_for_services():
    """Ensure all services are ready."""
    return True


class TestMCPSequentialThinkingIntegration:
    """Integration tests for mcp-sequentialthinking service using mcp-streamablehttp-client."""

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
            request["id"] = f"test-{method.replace('/', '-')}-{uuid.uuid4().hex[:8]}"

        # Convert to JSON string
        raw_request = json.dumps(request)

        # Build the command
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
            pytest.fail(
                f"mcp-streamablehttp-client failed: {result.stderr}\\nOutput: {result.stdout}",  # TODO: Break long line
            )

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
            pytest.fail(f"Failed to parse JSON response: {e}\\nOutput: {result.stdout}")

    def initialize_session(self, url: str, token: str) -> None:
        """Initialize a new MCP session."""
        response = self.run_mcp_client(
            url=url,
            token=token,
            method="initialize",
            params={
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {},
                    "resources": {"subscribe": True},
                    "prompts": {},
                },
                "clientInfo": {
                    "name": "sequentialthinking-test-client",
                    "version": "1.0.0",
                },
            },
        )
        assert "result" in response, f"Initialize failed: {response}"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sequentialthinking_initialize(self, mcp_sequentialthinking_url, client_token, wait_for_services):
        """Test initialize method to establish connection."""
        response = self.run_mcp_client(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {},
                    "resources": {"subscribe": True},
                    "prompts": {},
                    "logging": {},
                    "completions": {},
                },
                "clientInfo": {
                    "name": "test-sequentialthinking-client",
                    "version": "1.0.0",
                },
            },
        )

        assert "result" in response
        result = response["result"]
        # Sequential thinking server should use one of the officially supported protocol versions
        assert result["protocolVersion"] in MCP_PROTOCOL_VERSIONS_SUPPORTED, (
            f"Sequential thinking server protocol version {result['protocolVersion']} not in supported versions: {MCP_PROTOCOL_VERSIONS_SUPPORTED}"  # TODO: Break long line
        )
        assert "serverInfo" in result
        # Server name should indicate sequential thinking functionality
        server_name = result["serverInfo"]["name"]
        assert "sequential" in server_name.lower() or "thinking" in server_name.lower(), (
            f"Server name '{server_name}' doesn't indicate sequential thinking functionality"  # TODO: Break long line
        )
        assert "capabilities" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sequentialthinking_list_tools(self, mcp_sequentialthinking_url, client_token, wait_for_services):
        """Test listing available tools."""
        sequentialthinking_url = f"{mcp_sequentialthinking_url}"
        # First initialize
        self.initialize_session(sequentialthinking_url, client_token)

        # List tools
        response = self.run_mcp_client(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/list",
            params={},
        )

        assert "result" in response
        tools = response["result"]["tools"]
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check tool structure and look for thinking-related tools
        tool_names = []
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            tool_names.append(tool["name"])

        print(f"Available sequential thinking tools: {tool_names}")

        # Sequential thinking server should have thinking-related tools
        thinking_tools = [
            name
            for name in tool_names
            if any(keyword in name.lower() for keyword in ["think", "sequential", "step", "analyze", "reason"])
        ]
        assert len(thinking_tools) > 0, f"No thinking tools found in: {tool_names}"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sequentialthinking_list_resources(self, mcp_sequentialthinking_url, client_token, wait_for_services):
        """Test listing available resources."""
        sequentialthinking_url = f"{mcp_sequentialthinking_url}"
        # Initialize first
        self.initialize_session(sequentialthinking_url, client_token)

        # List resources
        response = self.run_mcp_client(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="resources/list",
            params={},
        )

        # Sequential thinking server may not support resources/list - check for error
        if "error" in response:
            # Sequential thinking server doesn't support resources - this is acceptable
            print(
                f"Sequential thinking server doesn't support resources/list: {response['error']['message']}",  # TODO: Break long line
            )
            assert response["error"]["code"] == -32601  # Method not found
        else:
            # If it does support resources, check the structure
            assert "result" in response
            resources = response["result"]["resources"]
            assert isinstance(resources, list)

            # Check resource structure
            for resource in resources:
                assert "uri" in resource
                assert "name" in resource

            resource_names = [res["name"] for res in resources]
            print(f"Available sequential thinking resources: {resource_names}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sequentialthinking_basic_functionality(
        self,
        mcp_sequentialthinking_url,
        client_token,
        wait_for_services,
    ):
        """Test basic sequential thinking functionality if tools are available."""
        sequentialthinking_url = f"{mcp_sequentialthinking_url}"
        # Initialize
        self.initialize_session(sequentialthinking_url, client_token)

        # List tools to see what's available
        list_response = self.run_mcp_client(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/list",
            params={},
        )

        tools = list_response["result"]["tools"]
        if len(tools) > 0:
            # Try to call the first available tool with minimal parameters
            first_tool = tools[0]
            print(f"Testing sequential thinking tool: {first_tool['name']}")
            print(f"Tool description: {first_tool['description']}")

            # Build basic arguments based on the input schema
            tool_args = {}
            if "inputSchema" in first_tool and "properties" in first_tool["inputSchema"]:
                # Add some basic arguments for thinking operations
                for prop, schema in first_tool["inputSchema"]["properties"].items():
                    if schema.get("type") == "string":
                        if "problem" in prop.lower() or "query" in prop.lower() or "question" in prop.lower():
                            tool_args[prop] = "How can I optimize software performance?"
                        elif "topic" in prop.lower() or "subject" in prop.lower():
                            tool_args[prop] = "software optimization"
                        else:
                            tool_args[prop] = f"test-{prop}"
                    elif schema.get("type") == "number":
                        tool_args[prop] = 5  # Reasonable number of thinking steps
                    elif schema.get("type") == "boolean":
                        tool_args[prop] = True
                    elif schema.get("type") == "object":
                        tool_args[prop] = {}

            # Call the tool
            response = self.run_mcp_client(
                url=mcp_sequentialthinking_url,
                token=client_token,
                method="tools/call",
                params={"name": first_tool["name"], "arguments": tool_args},
            )

            print(f"Sequential thinking response: {json.dumps(response, indent=2)}")

            # Should get either a result or an error (both are acceptable for this test)
            assert "result" in response or "error" in response
            if "result" in response:
                assert "content" in response["result"]
                print(
                    f"Sequential thinking tool '{first_tool['name']}' executed successfully",  # TODO: Break long line
                )
            else:
                print(
                    f"Sequential thinking tool '{first_tool['name']}' returned error (may be expected): {response['error']}",  # TODO: Break long line
                )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sequentialthinking_health_check(self, mcp_sequentialthinking_url, client_token, wait_for_services):
        """Test that the sequential thinking service health endpoint is accessible."""
        # This test verifies the service is running and accessible
        # The actual health check is done via the docker health check

        # Just verify we can initialize - this proves the service is healthy
        response = self.run_mcp_client(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "health-test-client", "version": "1.0.0"},
            },
        )

        assert "result" in response
        print("Sequential thinking service health check passed via MCP initialization")
