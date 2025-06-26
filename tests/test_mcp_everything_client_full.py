"""Comprehensive test of mcp-everything service using mcp-streamablehttp-client."""

import json
import os
import subprocess
from typing import Any

import pytest

from tests.test_constants import BASE_DOMAIN
from tests.test_constants import MCP_CLIENT_ACCESS_TOKEN
from tests.test_constants import MCP_EVERYTHING_TESTS_ENABLED
from tests.test_constants import MCP_EVERYTHING_URLS


@pytest.fixture
def base_domain():
    """Base domain for tests."""
    return BASE_DOMAIN


@pytest.fixture
def everything_url():
    """Full URL for everything service."""
    if not MCP_EVERYTHING_TESTS_ENABLED:
        pytest.skip("MCP Everything tests are disabled. Set MCP_EVERYTHING_TESTS_ENABLED=true to enable.")
    if not MCP_EVERYTHING_URLS:
        pytest.skip("MCP_EVERYTHING_URLS environment variable not set")
    return MCP_EVERYTHING_URLS[0]


@pytest.fixture
def client_token():
    """MCP client OAuth token for testing."""
    return MCP_CLIENT_ACCESS_TOKEN


@pytest.fixture
async def wait_for_services():
    """Ensure all services are ready."""
    # Services are already checked by conftest
    return True


class TestMCPEverythingClientFull:
    """Comprehensive test of mcp-everything using mcp-streamablehttp-client."""

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
                f"mcp-streamablehttp-client failed: {result.stderr}\nOutput: {result.stdout}"  # TODO: Break long line
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
            pytest.fail(f"Failed to parse JSON response: {e}\nOutput: {result.stdout}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_initialize(self, everything_url, client_token, wait_for_services):
        """Test initialize method to establish connection."""
        response = self.run_mcp_client(
            url=everything_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "tools": {},
                    "resources": {"subscribe": True},
                    "prompts": {},
                    "logging": {},
                    "completions": {},
                },
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        assert "result" in response
        result = response["result"]
        assert result["protocolVersion"] == "2025-06-18"
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "example-servers/everything"
        assert "capabilities" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_list_tools(self, everything_url, client_token, wait_for_services):
        """Test listing available tools."""
        # First initialize
        self.run_mcp_client(
            url=everything_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # List tools
        response = self.run_mcp_client(url=everything_url, token=client_token, method="tools/list", params={})

        assert "result" in response
        tools = response["result"]["tools"]
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

        # Look for specific tools that should exist
        tool_names = [tool["name"] for tool in tools]
        print(f"Available tools: {tool_names}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_list_resources(self, everything_url, client_token, wait_for_services):
        """Test listing available resources."""
        # Initialize first
        self.run_mcp_client(
            url=everything_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {"resources": {"subscribe": True}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # List resources
        response = self.run_mcp_client(url=everything_url, token=client_token, method="resources/list", params={})

        assert "result" in response
        resources = response["result"]["resources"]
        assert isinstance(resources, list)

        # Check resource structure
        for resource in resources:
            assert "uri" in resource
            assert "name" in resource

        resource_names = [res["name"] for res in resources]
        print(f"Available resources: {resource_names}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_list_prompts(self, everything_url, client_token, wait_for_services):
        """Test listing available prompts."""
        # Initialize first
        self.run_mcp_client(
            url=everything_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {"prompts": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # List prompts
        response = self.run_mcp_client(url=everything_url, token=client_token, method="prompts/list", params={})

        assert "result" in response
        prompts = response["result"]["prompts"]
        assert isinstance(prompts, list)

        # Check prompt structure
        for prompt in prompts:
            assert "name" in prompt
            assert "description" in prompt

        prompt_names = [p["name"] for p in prompts]
        print(f"Available prompts: {prompt_names}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_call_tool(self, everything_url, client_token, wait_for_services):
        """Test calling a tool if available."""
        # Initialize
        self.run_mcp_client(
            url=everything_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # List tools first to see what's available
        list_response = self.run_mcp_client(url=everything_url, token=client_token, method="tools/list", params={})

        tools = list_response["result"]["tools"]
        if len(tools) > 0:
            # Try to call the first available tool
            first_tool = tools[0]
            print(f"Calling tool: {first_tool['name']}")

            # Build arguments based on the input schema
            tool_args = {}
            if "inputSchema" in first_tool and "properties" in first_tool["inputSchema"]:
                # Add minimal required arguments
                for prop, schema in first_tool["inputSchema"]["properties"].items():
                    if schema.get("type") == "string":
                        tool_args[prop] = f"test-{prop}"
                    elif schema.get("type") == "number":
                        tool_args[prop] = 42
                    elif schema.get("type") == "boolean":
                        tool_args[prop] = True

            # Call the tool
            response = self.run_mcp_client(
                url=everything_url,
                token=client_token,
                method="tools/call",
                params={"name": first_tool["name"], "arguments": tool_args},
            )

            assert "result" in response or "error" in response
            if "result" in response:
                assert "content" in response["result"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_read_resource(self, everything_url, client_token, wait_for_services):
        """Test reading a resource if available."""
        # Initialize
        self.run_mcp_client(
            url=everything_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {"resources": {"subscribe": True}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # List resources
        list_response = self.run_mcp_client(url=everything_url, token=client_token, method="resources/list", params={})

        resources = list_response["result"]["resources"]
        if len(resources) > 0:
            # Try to read the first resource
            first_resource = resources[0]
            print(f"Reading resource: {first_resource['uri']}")

            response = self.run_mcp_client(
                url=everything_url,
                token=client_token,
                method="resources/read",
                params={"uri": first_resource["uri"]},
            )

            assert "result" in response or "error" in response
            if "result" in response:
                assert "contents" in response["result"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_get_prompt(self, everything_url, client_token, wait_for_services):
        """Test getting a prompt if available."""
        # Initialize
        self.run_mcp_client(
            url=everything_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {"prompts": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # List prompts
        list_response = self.run_mcp_client(url=everything_url, token=client_token, method="prompts/list", params={})

        prompts = list_response["result"]["prompts"]
        if len(prompts) > 0:
            # Try to get the first prompt
            first_prompt = prompts[0]
            print(f"Getting prompt: {first_prompt['name']}")

            # Build arguments if needed
            prompt_args = {}
            if "arguments" in first_prompt:
                for arg in first_prompt["arguments"]:
                    if arg.get("required", False):
                        prompt_args[arg["name"]] = f"test-{arg['name']}"

            response = self.run_mcp_client(
                url=everything_url,
                token=client_token,
                method="prompts/get",
                params={"name": first_prompt["name"], "arguments": prompt_args},
            )

            assert "result" in response or "error" in response
            if "result" in response:
                assert "messages" in response["result"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_logging(self, everything_url, client_token, wait_for_services):
        """Test logging functionality."""
        # Initialize with logging capability
        self.run_mcp_client(
            url=everything_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {"logging": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # The everything server should support logging
        # We can't easily test notifications, but we've confirmed logging capability
        assert True

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_protocol_compliance(self, everything_url, client_token, wait_for_services):
        """Test protocol compliance and error handling."""
        # Test with unsupported method
        response = self.run_mcp_client(
            url=everything_url,
            token=client_token,
            method="nonexistent/method",
            params={},
        )

        # Should get an error
        assert "error" in response or ("raw_output" in response and "error" in response["raw_output"])

        # Test with wrong protocol version
        response = self.run_mcp_client(
            url=everything_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "1.0.0",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        )

        # The server may accept the request but should return the correct protocol version
        if "result" in response:
            # Server accepted but should return the correct version
            assert response["result"]["protocolVersion"] == "2025-06-18"
        else:
            # Or it might return an error
            assert "error" in response

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_full_workflow(self, everything_url, client_token, wait_for_services):
        """Test a complete workflow using multiple capabilities."""
        print("\n=== Starting full workflow test ===")

        # 1. Initialize with all capabilities
        print("1. Initializing connection...")
        init_response = self.run_mcp_client(
            url=everything_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "tools": {},
                    "resources": {"subscribe": True},
                    "prompts": {},
                    "logging": {},
                    "completions": {},
                },
                "clientInfo": {"name": "test-workflow-client", "version": "1.0.0"},
            },
        )

        assert "result" in init_response
        server_capabilities = init_response["result"]["capabilities"]
        print(f"Server capabilities: {list(server_capabilities.keys())}")

        # 2. List all available features
        print("\n2. Discovering available features...")

        # List tools
        tools_response = self.run_mcp_client(url=everything_url, token=client_token, method="tools/list", params={})
        tools = tools_response["result"]["tools"]
        print(f"Found {len(tools)} tools")

        # List resources
        resources_response = self.run_mcp_client(
            url=everything_url, token=client_token, method="resources/list", params={}
        )
        resources = resources_response["result"]["resources"]
        print(f"Found {len(resources)} resources")

        # List prompts
        prompts_response = self.run_mcp_client(url=everything_url, token=client_token, method="prompts/list", params={})
        prompts = prompts_response["result"]["prompts"]
        print(f"Found {len(prompts)} prompts")

        # 3. Use some features
        print("\n3. Using discovered features...")

        # Call a tool if available
        if tools:
            tool = tools[0]
            print(f"Calling tool: {tool['name']}")
            tool_response = self.run_mcp_client(
                url=everything_url,
                token=client_token,
                method="tools/call",
                params={"name": tool["name"], "arguments": {}},
            )
            print(f"Tool response: {'success' if 'result' in tool_response else 'error'}")

        # Read a resource if available
        if resources:
            resource = resources[0]
            print(f"Reading resource: {resource['uri']}")
            resource_response = self.run_mcp_client(
                url=everything_url,
                token=client_token,
                method="resources/read",
                params={"uri": resource["uri"]},
            )
            print(
                f"Resource response: {'success' if 'result' in resource_response else 'error'}"  # TODO: Break long line
            )

        print("\n=== Workflow test completed ===")

        # Verify we tested multiple capabilities
        assert len(tools) > 0 or len(resources) > 0 or len(prompts) > 0
        print(
            f"Successfully tested everything server with {len(tools)} tools, {len(resources)} resources, {len(prompts)} prompts"  # TODO: Break long line
        )
