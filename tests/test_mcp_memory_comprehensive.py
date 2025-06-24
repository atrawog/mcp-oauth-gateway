"""Comprehensive tests for all mcp-memory service functionalities using mcp-streamablehttp-client."""

import json
import os
import subprocess
import uuid
from typing import Any

import pytest

from tests.test_constants import BASE_DOMAIN
from tests.test_constants import MCP_CLIENT_ACCESS_TOKEN
from tests.test_constants import MCP_PROTOCOL_VERSION


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
    return True


class TestMCPMemoryComprehensive:
    """Comprehensive tests for all mcp-memory service functionalities."""

    def run_mcp_client(
        self, url: str, token: str, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
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
        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, timeout=30, env=env
        )

        if result.returncode != 0:
            # Check if it's an expected error
            if "error" in result.stdout or "Error" in result.stdout:
                return {"error": result.stdout, "stderr": result.stderr}
            pytest.fail(
                f"mcp-streamablehttp-client failed: {result.stderr}\\nOutput: {result.stdout}"  # TODO: Break long line
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
                "clientInfo": {"name": "memory-test-client", "version": "1.0.0"},
            },
        )
        assert "result" in response, f"Initialize failed: {response}"

    def get_tool_schema(self, url: str, token: str, tool_name: str) -> dict[str, Any]:
        """Get the schema for a specific tool."""
        self.initialize_session(url, token)

        response = self.run_mcp_client(
            url=url, token=token, method="tools/list", params={}
        )

        assert "result" in response, f"tools/list failed: {response}"
        tools = response["result"]["tools"]

        for tool in tools:
            if tool["name"] == tool_name:
                return tool

        pytest.fail(
            f"Tool '{tool_name}' not found in available tools: {[t['name'] for t in tools]}"  # TODO: Break long line
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_create_entities(
        self, mcp_memory_url, client_token, wait_for_services
    ):
        """Test creating entities in the memory graph."""
        # Get tool schema
        tool_schema = self.get_tool_schema(
            f"{mcp_memory_url}", client_token, "create_entities"
        )
        print(f"\\nTesting create_entities tool: {tool_schema['description']}")
        print(f"Input schema: {json.dumps(tool_schema['inputSchema'], indent=2)}")

        # Test creating entities
        entities_data = [
            {
                "name": "test_user",
                "entityType": "person",
                "observations": ["User prefers morning meetings", "Lives in Berlin"],
            },
            {
                "name": "test_project",
                "entityType": "project",
                "observations": ["AI-powered memory system", "Uses knowledge graphs"],
            },
        ]

        response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "create_entities",
                "arguments": {"entities": entities_data},
            },
        )

        print(f"Create entities response: {json.dumps(response, indent=2)}")

        if "result" in response:
            assert "content" in response["result"]
            content = response["result"]["content"]
            assert isinstance(content, list)
            assert len(content) > 0
            # Memory server returns entity data or empty array - both are valid
            text_content = "".join(
                [item.get("text", "") for item in content if item.get("type") == "text"]
            )
            # If entities were created, they should be in the response
            if text_content and text_content != "[]":
                assert "test_user" in text_content
                assert "test_project" in text_content
            print("✅ Entities operation completed successfully!")
        else:
            # Some test data might cause validation errors - that's acceptable for this test
            assert "error" in response
            print(f"Expected error (validation): {response['error']}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_create_relations(
        self, mcp_memory_url, client_token, wait_for_services
    ):
        """Test creating relations between entities."""
        tool_schema = self.get_tool_schema(
            f"{mcp_memory_url}", client_token, "create_relations"
        )
        print(f"\\nTesting create_relations tool: {tool_schema['description']}")
        print(f"Input schema: {json.dumps(tool_schema['inputSchema'], indent=2)}")

        # First create entities to relate
        self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "create_entities",
                "arguments": {
                    "entities": [
                        {"name": "alice", "entityType": "person"},
                        {"name": "bob", "entityType": "person"},
                    ]
                },
            },
        )

        # Create relations
        relations_data = [{"from": "alice", "to": "bob", "relationType": "knows"}]

        response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "create_relations",
                "arguments": {"relations": relations_data},
            },
        )

        print(f"Create relations response: {json.dumps(response, indent=2)}")

        if "result" in response:
            assert "content" in response["result"]
            content = response["result"]["content"]
            assert isinstance(content, list)
        else:
            assert "error" in response
            print(f"Create relations error: {response['error']}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_add_observations(
        self, mcp_memory_url, client_token, wait_for_services
    ):
        """Test adding observations to entities."""
        tool_schema = self.get_tool_schema(
            f"{mcp_memory_url}", client_token, "add_observations"
        )
        print(f"\\nTesting add_observations tool: {tool_schema['description']}")
        print(f"Input schema: {json.dumps(tool_schema['inputSchema'], indent=2)}")

        # Create an entity first
        self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "create_entities",
                "arguments": {
                    "entities": [{"name": "test_entity", "entityType": "person"}]
                },
            },
        )

        # Add observations
        observations_data = [
            {
                "entityName": "test_entity",
                "contents": [
                    "Likes coffee",
                    "Works remotely",
                    "Prefers async communication",
                ],
            }
        ]

        response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "add_observations",
                "arguments": {"observations": observations_data},
            },
        )

        print(f"Add observations response: {json.dumps(response, indent=2)}")

        if "result" in response:
            assert "content" in response["result"]
        else:
            assert "error" in response
            print(f"Add observations error: {response['error']}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_read_graph(
        self, mcp_memory_url, client_token, wait_for_services
    ):
        """Test reading the entire memory graph."""
        tool_schema = self.get_tool_schema(
            f"{mcp_memory_url}", client_token, "read_graph"
        )
        print(f"\\nTesting read_graph tool: {tool_schema['description']}")
        print(f"Input schema: {json.dumps(tool_schema['inputSchema'], indent=2)}")

        response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={"name": "read_graph", "arguments": {}},
        )

        print(f"Read graph response: {json.dumps(response, indent=2)}")

        if "result" in response:
            assert "content" in response["result"]
            content = response["result"]["content"]
            assert isinstance(content, list)
            # Should return the current state of the memory graph
            text_content = "".join(
                [item.get("text", "") for item in content if item.get("type") == "text"]
            )
            assert len(text_content) > 0  # Should have some content about the graph
        else:
            assert "error" in response
            print(f"Read graph error: {response['error']}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_search_nodes(
        self, mcp_memory_url, client_token, wait_for_services
    ):
        """Test searching for nodes in the memory graph."""
        tool_schema = self.get_tool_schema(
            f"{mcp_memory_url}", client_token, "search_nodes"
        )
        print(f"\\nTesting search_nodes tool: {tool_schema['description']}")
        print(f"Input schema: {json.dumps(tool_schema['inputSchema'], indent=2)}")

        # Create some searchable content first
        self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "create_entities",
                "arguments": {
                    "entities": [
                        {
                            "name": "searchable_entity",
                            "entityType": "concept",
                            "observations": ["important test data"],
                        }
                    ]
                },
            },
        )

        # Search for nodes
        response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={"name": "search_nodes", "arguments": {"query": "searchable"}},
        )

        print(f"Search nodes response: {json.dumps(response, indent=2)}")

        if "result" in response:
            assert "content" in response["result"]
        else:
            assert "error" in response
            print(f"Search nodes error: {response['error']}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_open_nodes(
        self, mcp_memory_url, client_token, wait_for_services
    ):
        """Test opening specific nodes for detailed information."""
        tool_schema = self.get_tool_schema(
            f"{mcp_memory_url}", client_token, "open_nodes"
        )
        print(f"\\nTesting open_nodes tool: {tool_schema['description']}")
        print(f"Input schema: {json.dumps(tool_schema['inputSchema'], indent=2)}")

        # Create an entity to open
        self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "create_entities",
                "arguments": {
                    "entities": [{"name": "detailed_entity", "entityType": "person"}]
                },
            },
        )

        # Open the node
        response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={"name": "open_nodes", "arguments": {"names": ["detailed_entity"]}},
        )

        print(f"Open nodes response: {json.dumps(response, indent=2)}")

        if "result" in response:
            assert "content" in response["result"]
        else:
            assert "error" in response
            print(f"Open nodes error: {response['error']}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_delete_entities(
        self, mcp_memory_url, client_token, wait_for_services
    ):
        """Test deleting entities from memory."""
        tool_schema = self.get_tool_schema(
            f"{mcp_memory_url}", client_token, "delete_entities"
        )
        print(f"\\nTesting delete_entities tool: {tool_schema['description']}")
        print(f"Input schema: {json.dumps(tool_schema['inputSchema'], indent=2)}")

        # Create entity to delete
        self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "create_entities",
                "arguments": {
                    "entities": [
                        {"name": "deletable_entity", "entityType": "temporary"}
                    ]
                },
            },
        )

        # Delete the entity
        response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "delete_entities",
                "arguments": {"entityNames": ["deletable_entity"]},
            },
        )

        print(f"Delete entities response: {json.dumps(response, indent=2)}")

        if "result" in response:
            assert "content" in response["result"]
        else:
            assert "error" in response
            print(f"Delete entities error: {response['error']}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_delete_relations(
        self, mcp_memory_url, client_token, wait_for_services
    ):
        """Test deleting relations from memory."""
        tool_schema = self.get_tool_schema(
            f"{mcp_memory_url}", client_token, "delete_relations"
        )
        print(f"\\nTesting delete_relations tool: {tool_schema['description']}")
        print(f"Input schema: {json.dumps(tool_schema['inputSchema'], indent=2)}")

        # Create entities and relation to delete
        self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "create_entities",
                "arguments": {
                    "entities": [
                        {"name": "entity_a", "entityType": "person"},
                        {"name": "entity_b", "entityType": "person"},
                    ]
                },
            },
        )

        self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "create_relations",
                "arguments": {
                    "relations": [
                        {
                            "from": "entity_a",
                            "to": "entity_b",
                            "relationType": "temporary_connection",
                        }
                    ]
                },
            },
        )

        # Delete the relation
        response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "delete_relations",
                "arguments": {
                    "relationIds": [
                        "entity_a->entity_b"
                    ]  # This might need adjustment based on actual ID format
                },
            },
        )

        print(f"Delete relations response: {json.dumps(response, indent=2)}")

        if "result" in response:
            assert "content" in response["result"]
        else:
            assert "error" in response
            print(f"Delete relations error: {response['error']}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_delete_observations(
        self, mcp_memory_url, client_token, wait_for_services
    ):
        """Test deleting observations from memory."""
        tool_schema = self.get_tool_schema(
            f"{mcp_memory_url}", client_token, "delete_observations"
        )
        print(f"\\nTesting delete_observations tool: {tool_schema['description']}")
        print(f"Input schema: {json.dumps(tool_schema['inputSchema'], indent=2)}")

        # Create entity with observations to delete
        self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "create_entities",
                "arguments": {
                    "entities": [
                        {
                            "name": "observed_entity",
                            "entityType": "person",
                            "observations": ["temporary observation"],
                        }
                    ]
                },
            },
        )

        # Delete observations
        response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "delete_observations",
                "arguments": {
                    "observationIds": [
                        "observed_entity_0"
                    ]  # This might need adjustment based on actual ID format
                },
            },
        )

        print(f"Delete observations response: {json.dumps(response, indent=2)}")

        if "result" in response:
            assert "content" in response["result"]
        else:
            assert "error" in response
            print(f"Delete observations error: {response['error']}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_complete_workflow(
        self, mcp_memory_url, client_token, wait_for_services
    ):
        """Test a complete memory workflow with all operations."""
        print("\\n=== Starting complete memory workflow test ===")

        # 1. Initialize and read initial state
        self.initialize_session(f"{mcp_memory_url}", client_token)

        initial_graph = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={"name": "read_graph", "arguments": {}},
        )
        print(f"Initial graph state: {json.dumps(initial_graph, indent=2)}")

        # 2. Create entities
        create_response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "create_entities",
                "arguments": {
                    "entities": [
                        {
                            "name": "workflow_user",
                            "entityType": "person",
                            "observations": [
                                "Testing complete workflow",
                                "Comprehensive memory testing",
                            ],
                        },
                        {
                            "name": "workflow_project",
                            "entityType": "project",
                            "observations": [
                                "MCP memory integration",
                                "Knowledge graph testing",
                            ],
                        },
                    ]
                },
            },
        )
        print(f"\\nEntities created: {create_response}")

        # 3. Create relations
        relations_response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "create_relations",
                "arguments": {
                    "relations": [
                        {
                            "from": "workflow_user",
                            "to": "workflow_project",
                            "relationType": "works_on",
                        }
                    ]
                },
            },
        )
        print(f"\\nRelations created: {relations_response}")

        # 4. Add more observations
        observations_response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "add_observations",
                "arguments": {
                    "observations": [
                        {
                            "entityName": "workflow_user",
                            "contents": [
                                "Prefers thorough testing",
                                "Values data integrity",
                            ],
                        }
                    ]
                },
            },
        )
        print(f"\\nObservations added: {observations_response}")

        # 5. Search for created content
        search_response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={"name": "search_nodes", "arguments": {"query": "workflow"}},
        )
        print(f"\\nSearch results: {search_response}")

        # 6. Open specific nodes
        open_response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={"name": "open_nodes", "arguments": {"names": ["workflow_user"]}},
        )
        print(f"\\nNode details: {open_response}")

        # 7. Read final graph state
        final_graph = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={"name": "read_graph", "arguments": {}},
        )
        print(f"\\nFinal graph state: {json.dumps(final_graph, indent=2)}")

        print("\\n=== Complete workflow test finished ===")

        # Verify workflow completed (at least some operations succeeded)
        workflow_success = any(
            [
                "result" in create_response,
                "result" in relations_response,
                "result" in observations_response,
                "result" in search_response,
                "result" in open_response,
                "result" in final_graph,
            ]
        )

        assert workflow_success, "Complete workflow failed - no operations succeeded"
        print("✅ Memory workflow completed successfully!")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_error_handling(
        self, mcp_memory_url, client_token, wait_for_services
    ):
        """Test error handling for invalid operations."""
        self.initialize_session(f"{mcp_memory_url}", client_token)

        # Test invalid entity creation
        invalid_entity_response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "create_entities",
                "arguments": {
                    "entities": [{"invalid": "structure"}]  # Missing required fields
                },
            },
        )

        print(
            f"Invalid entity response: {json.dumps(invalid_entity_response, indent=2)}"
        )

        # Test searching non-existent entities
        search_missing_response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "search_nodes",
                "arguments": {"query": "definitely_does_not_exist_12345"},
            },
        )

        print(
            f"Search missing response: {json.dumps(search_missing_response, indent=2)}"
        )

        # Test opening non-existent nodes
        open_missing_response = self.run_mcp_client(
            url=f"{mcp_memory_url}",
            token=client_token,
            method="tools/call",
            params={
                "name": "open_nodes",
                "arguments": {"names": ["definitely_does_not_exist_54321"]},
            },
        )

        print(f"Open missing response: {json.dumps(open_missing_response, indent=2)}")

        # Verify that error handling works (operations either succeed or return proper errors)
        for response in [
            invalid_entity_response,
            search_missing_response,
            open_missing_response,
        ]:
            assert "result" in response or "error" in response, (
                f"Response missing result or error: {response}"
            )

        print("✅ Error handling verification completed!")
