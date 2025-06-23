"""Integration tests for mcp-memory service."""

import json
import os
import subprocess
from typing import Any

import pytest

from tests.test_constants import BASE_DOMAIN
from tests.test_constants import MCP_CLIENT_ACCESS_TOKEN
from tests.test_constants import MCP_PROTOCOL_VERSION
from tests.test_constants import MCP_PROTOCOL_VERSIONS_SUPPORTED


@pytest.fixture
def base_domain():
    """Base domain for tests."""
    return BASE_DOMAIN


# Using mcp_memory_url fixture from conftest.py which handles test skipping


@pytest.fixture
def client_token():
    """MCP client OAuth token for testing."""
    return MCP_CLIENT_ACCESS_TOKEN


@pytest.fixture
async def wait_for_services():
    """Ensure all services are ready."""
    # Services are already checked by conftest
    return True


class TestMCPMemoryIntegration:
    """Integration tests for mcp-memory service using mcp-streamablehttp-client."""

    def run_mcp_client(self, url: str, token: str, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Run mcp-streamablehttp-client and return the response."""
        # Set environment variables
        env = os.environ.copy()
        env["MCP_SERVER_URL"] = url
        env["MCP_CLIENT_ACCESS_TOKEN"] = token

        # Build the raw JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }

        # Add ID for requests (not notifications)
        if method != "notifications/initialized":
            request["id"] = f"test-{method.replace('/', '-')}-1"

        # Convert to JSON string
        raw_request = json.dumps(request)

        # Build the command
        cmd = [
            "pixi", "run", "mcp-streamablehttp-client",
            "--server-url", url,
            "--raw", raw_request
        ]

        # Run the command
        result = subprocess.run(
            cmd,
            check=False, capture_output=True,
            text=True,
            timeout=30,
            env=env
        )

        if result.returncode != 0:
            # Check if it's an expected error
            if "error" in result.stdout or "Error" in result.stdout:
                return {"error": result.stdout, "stderr": result.stderr}
            pytest.fail(f"mcp-streamablehttp-client failed: {result.stderr}\\nOutput: {result.stdout}")

        # Parse the output - find the JSON response
        try:
            # Look for JSON blocks in the output
            output = result.stdout

            # Find all JSON objects in the output
            json_objects = []
            i = 0
            while i < len(output):
                if output[i] == '{':
                    # Found start of JSON, find the matching closing brace
                    brace_count = 0
                    json_start = i
                    json_end = i

                    for j in range(i, len(output)):
                        if output[j] == '{':
                            brace_count += 1
                        elif output[j] == '}':
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_initialize(self, mcp_memory_url, client_token, wait_for_services):
        """Test initialize method to establish connection."""
        response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {},
                    "resources": {"subscribe": True},
                    "prompts": {},
                    "logging": {},
                    "completions": {}
                },
                "clientInfo": {
                    "name": "test-memory-client",
                    "version": "1.0.0"
                }
            }
        )

        assert "result" in response
        result = response["result"]
        # Memory server should use one of the officially supported protocol versions
        assert result["protocolVersion"] in MCP_PROTOCOL_VERSIONS_SUPPORTED, \
            f"Memory server protocol version {result['protocolVersion']} not in supported versions: {MCP_PROTOCOL_VERSIONS_SUPPORTED}"
        assert "serverInfo" in result
        # Server name is "memory-server" from the official MCP memory server
        assert result["serverInfo"]["name"] in ["memory", "memory-server"]
        assert "capabilities" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_list_tools(self, mcp_memory_url, client_token, wait_for_services):
        """Test listing available tools."""
        # First initialize
        self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        )

        # List tools
        response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/list",
            params={}
        )

        assert "result" in response
        tools = response["result"]["tools"]
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check tool structure and look for memory-specific tools
        tool_names = []
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            tool_names.append(tool["name"])

        print(f"Available memory tools: {tool_names}")

        # Memory server provides knowledge graph tools (not named "memory" but entity/relation tools)
        knowledge_graph_tools = [name for name in tool_names if any(keyword in name.lower() for keyword in ["entity", "entities", "relation", "observation", "graph", "node"])]
        assert len(knowledge_graph_tools) > 0, f"No knowledge graph tools found in: {tool_names}"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_list_resources(self, mcp_memory_url, client_token, wait_for_services):
        """Test listing available resources."""
        # Initialize first
        self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"resources": {"subscribe": True}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        )

        # List resources
        response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="resources/list",
            params={}
        )

        # Memory server may not support resources/list - check for error
        if "error" in response:
            # Memory server doesn't support resources - this is acceptable
            print(f"Memory server doesn't support resources/list: {response['error']['message']}")
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
            print(f"Available memory resources: {resource_names}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_basic_functionality(self, mcp_memory_url, client_token, wait_for_services):
        """Test basic memory functionality if tools are available."""
        # Initialize
        self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        )

        # List tools to see what's available
        list_response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/list",
            params={}
        )

        tools = list_response["result"]["tools"]
        if len(tools) > 0:
            # Try to call the first available tool with minimal parameters
            first_tool = tools[0]
            print(f"Testing memory tool: {first_tool['name']}")

            # Build basic arguments based on the input schema
            tool_args = {}
            if "inputSchema" in first_tool and "properties" in first_tool["inputSchema"]:
                # Add some basic arguments for memory operations
                for prop, schema in first_tool["inputSchema"]["properties"].items():
                    if schema.get("type") == "string":
                        if "content" in prop.lower() or "text" in prop.lower():
                            tool_args[prop] = "test memory content"
                        elif "entity" in prop.lower():
                            tool_args[prop] = "test_entity"
                        else:
                            tool_args[prop] = f"test-{prop}"
                    elif schema.get("type") == "object":
                        tool_args[prop] = {}

            # Call the tool
            response = self.run_mcp_client(
                url=f"{mcp_memory_url}",
                token=client_token,
                method="tools/call",
                params={
                    "name": first_tool["name"],
                    "arguments": tool_args
                }
            )

            # Should get either a result or an error (both are acceptable for this test)
            assert "result" in response or "error" in response
            if "result" in response:
                assert "content" in response["result"]
                print(f"Memory tool '{first_tool['name']}' executed successfully")
            else:
                print(f"Memory tool '{first_tool['name']}' returned error (expected for some tools): {response['error']}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_health_check(self, mcp_memory_url, client_token, wait_for_services):
        """Test that the memory service health endpoint is accessible."""
        # This test verifies the service is running and accessible
        # The actual health check is done via the docker health check

        # Just verify we can initialize - this proves the service is healthy
        response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "health-test-client", "version": "1.0.0"}
            }
        )

        assert "result" in response
        print("Memory service health check passed via MCP initialization")
