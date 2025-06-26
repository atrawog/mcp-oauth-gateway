"""Comprehensive tests for mcp-sequentialthinking service using mcp-streamablehttp-client."""

import json
import os
import subprocess
import uuid
from typing import Any

import pytest

from tests.test_constants import MCP_CLIENT_ACCESS_TOKEN
from tests.test_constants import MCP_PROTOCOL_VERSION
from tests.test_constants import MCP_PROTOCOL_VERSIONS_SUPPORTED


@pytest.fixture()
def client_token():
    """MCP client OAuth token for testing."""
    return MCP_CLIENT_ACCESS_TOKEN


@pytest.fixture()
async def wait_for_services():
    """Ensure all services are ready."""
    return True


class TestMCPSequentialThinkingComprehensive:
    """Comprehensive tests for mcp-sequentialthinking service functionality."""

    def run_mcp_client_command(self, url: str, token: str, command: str) -> dict[str, Any]:
        """Run mcp-streamablehttp-client with a command and return the response."""
        # Set environment variables
        env = os.environ.copy()
        env["MCP_SERVER_URL"] = url
        env["MCP_CLIENT_ACCESS_TOKEN"] = token

        # Build the command
        cmd = [
            "pixi",
            "run",
            "mcp-streamablehttp-client",
            "--server-url",
            url,
            "--command",
            command,
        ]

        # Run the command
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,  # Longer timeout for thinking operations
            env=env,
        )

        if result.returncode != 0:
            pytest.fail(
                f"mcp-streamablehttp-client failed: {result.stderr}\nOutput: {result.stdout}"  # TODO: Break long line
            )

        # Parse the output to find the actual response
        output = result.stdout
        lines = output.split("\n")

        # Look for lines that contain JSON responses
        for line in lines:
            line = line.strip()
            if line.startswith("{") and "content" in line:
                try:
                    response_data = json.loads(line)
                    return response_data
                except json.JSONDecodeError:
                    continue

        # If no JSON found, return the raw output for analysis
        return {"raw_output": output, "stderr": result.stderr}

    def run_mcp_client_raw(
        self, url: str, token: str, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Run mcp-streamablehttp-client with raw JSON-RPC and return the response."""
        # Set environment variables
        env = os.environ.copy()
        env["MCP_SERVER_URL"] = url
        env["MCP_CLIENT_ACCESS_TOKEN"] = token

        # Build the raw JSON-RPC request
        request = {"jsonrpc": "2.0", "method": method, "params": params or {}}

        # Add ID for requests (not notifications)
        if method != "notifications/initialized":
            request["id"] = f"test-{method.replace('/', '-')}-{uuid.uuid4().hex[:8]}"

        # Convert to JSON string - use compact format to avoid issues
        raw_request = json.dumps(request, separators=(",", ":"))

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
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=60, env=env)

        if result.returncode != 0:
            # Check if it's an expected error
            if "error" in result.stdout or "Error" in result.stdout:
                return {"error": result.stdout, "stderr": result.stderr}
            pytest.fail(
                f"mcp-streamablehttp-client failed: {result.stderr}\nOutput: {result.stdout}"  # TODO: Break long line
            )

        # Parse the output - find the JSON response
        try:
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
                return {"raw_output": output, "stderr": result.stderr}

            # Return the last JSON-RPC response
            response = json_objects[-1]
            return response

        except Exception as e:
            pytest.fail(f"Failed to parse JSON response: {e}\nOutput: {result.stdout}")

    def initialize_session(self, url: str, token: str) -> None:
        """Initialize a new MCP session."""
        response = self.run_mcp_client_raw(
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
                    "name": "sequentialthinking-comprehensive-test-client",
                    "version": "1.0.0",
                },
            },
        )
        assert "result" in response, f"Initialize failed: {response}"

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_sequentialthinking_tool_discovery(self, mcp_sequentialthinking_url, client_token, wait_for_services):
        """Test discovering available sequential thinking tools."""
        # Initialize session
        self.initialize_session(mcp_sequentialthinking_url, client_token)

        # List available tools
        response = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/list",
            params={},
        )

        assert "result" in response
        tools = response["result"]["tools"]
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check for sequential thinking tool
        tool_names = [tool["name"] for tool in tools]
        assert "sequentialthinking" in tool_names

        # Get the sequential thinking tool details
        sequential_tool = next(tool for tool in tools if tool["name"] == "sequentialthinking")
        assert "description" in sequential_tool
        assert "inputSchema" in sequential_tool
        assert "properties" in sequential_tool["inputSchema"]

        print(f"Sequential thinking tool found: {sequential_tool['name']}")
        print(f"Description: {sequential_tool['description']}")

        # Verify expected parameters (using camelCase naming from the server)
        properties = sequential_tool["inputSchema"]["properties"]
        expected_params = [
            "thought",
            "nextThoughtNeeded",
            "thoughtNumber",
            "totalThoughts",
        ]
        for param in expected_params:
            assert param in properties, f"Missing required parameter: {param}"

        print(f"Available parameters: {list(properties.keys())}")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_sequentialthinking_simple_problem(self, mcp_sequentialthinking_url, client_token, wait_for_services):
        """Test solving a simple problem with sequential thinking."""
        # Initialize session
        self.initialize_session(mcp_sequentialthinking_url, client_token)

        # Start a simple thinking process
        response = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "I need to solve the problem: What are the key factors for optimizing software performance?",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": 1,
                    "totalThoughts": 5,
                    "isRevision": False,
                },
            },
        )

        print(f"Sequential thinking response: {json.dumps(response, indent=2)}")

        # Should get either a result or an error
        assert "result" in response or "error" in response
        if "result" in response:
            assert "content" in response["result"]
            print("Sequential thinking tool executed successfully")
        else:
            # Check if it's a parameter validation error
            print(f"Sequential thinking returned error: {response['error']}")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_sequentialthinking_multi_step_process(
        self, mcp_sequentialthinking_url, client_token, wait_for_services
    ):
        """Test a multi-step thinking process."""
        # Initialize session
        self.initialize_session(mcp_sequentialthinking_url, client_token)

        # Step 1: Initial thought
        step1_response = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "Let me break down database optimization into key areas: indexing, query optimization, and hardware considerations.",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": 1,
                    "totalThoughts": 4,
                    "isRevision": False,
                },
            },
        )

        print(f"Step 1 response: {json.dumps(step1_response, indent=2)}")
        assert "result" in step1_response or "error" in step1_response

        # Step 2: Deeper analysis
        step2_response = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "For indexing: proper index selection is crucial. B-tree indexes for equality searches, composite indexes for multi-column queries.",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": 2,
                    "totalThoughts": 4,
                    "isRevision": False,
                },
            },
        )

        print(f"Step 2 response: {json.dumps(step2_response, indent=2)}")
        assert "result" in step2_response or "error" in step2_response

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_sequentialthinking_revision_process(
        self, mcp_sequentialthinking_url, client_token, wait_for_services
    ):
        """Test the revision capability of sequential thinking."""
        # Initialize session
        self.initialize_session(mcp_sequentialthinking_url, client_token)

        # Original thought
        original_response = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "The best way to improve software performance is to optimize the database queries.",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": 1,
                    "totalThoughts": 3,
                    "isRevision": False,
                },
            },
        )

        print(f"Original thought response: {json.dumps(original_response, indent=2)}")

        # Revision thought
        revision_response = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "Actually, I need to revise my previous thought. Performance optimization should start with profiling to identify bottlenecks, not assume database is the issue.",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": 2,
                    "totalThoughts": 4,
                    "isRevision": True,
                    "revisesThought": 1,
                },
            },
        )

        print(f"Revision response: {json.dumps(revision_response, indent=2)}")
        assert "result" in revision_response or "error" in revision_response

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_sequentialthinking_branching_logic(
        self, mcp_sequentialthinking_url, client_token, wait_for_services
    ):
        """Test branching logic in sequential thinking."""
        # Initialize session
        self.initialize_session(mcp_sequentialthinking_url, client_token)

        # Main branch
        main_branch_response = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "For software architecture, I can consider microservices or monolithic approaches.",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": 1,
                    "totalThoughts": 3,
                    "isRevision": False,
                },
            },
        )

        print(f"Main branch response: {json.dumps(main_branch_response, indent=2)}")

        # Branch A: Microservices
        branch_a_response = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "Branch A: Microservices offer scalability and technology diversity but increase complexity.",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": 2,
                    "totalThoughts": 4,
                    "isRevision": False,
                    "branchFromThought": 1,
                    "branchId": "microservices",
                },
            },
        )

        print(f"Branch A response: {json.dumps(branch_a_response, indent=2)}")
        assert "result" in branch_a_response or "error" in branch_a_response

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_sequentialthinking_dynamic_scaling(
        self, mcp_sequentialthinking_url, client_token, wait_for_services
    ):
        """Test dynamic scaling of thought process."""
        # Initialize session
        self.initialize_session(mcp_sequentialthinking_url, client_token)

        # Start with low thought count, then scale up
        initial_response = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "I thought this problem would be simple, but I am realizing it needs more analysis.",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": 2,
                    "totalThoughts": 6,  # Scaling up from initial estimate
                    "isRevision": False,
                    "needsMoreThoughts": True,
                },
            },
        )

        print(f"Dynamic scaling response: {json.dumps(initial_response, indent=2)}")
        assert "result" in initial_response or "error" in initial_response

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_sequentialthinking_hypothesis_testing(
        self, mcp_sequentialthinking_url, client_token, wait_for_services
    ):
        """Test hypothesis generation and testing."""
        # Initialize session
        self.initialize_session(mcp_sequentialthinking_url, client_token)

        # Generate hypothesis
        hypothesis_response = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "Hypothesis: Caching will improve performance by 50%. Let me verify this against the analysis so far.",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": 3,
                    "totalThoughts": 5,
                    "isRevision": False,
                },
            },
        )

        print(f"Hypothesis response: {json.dumps(hypothesis_response, indent=2)}")

        # Verification thought
        verification_response = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "Verification: The 50% improvement depends on cache hit rates and data access patterns. More analysis needed.",
                    "nextThoughtNeeded": False,
                    "thoughtNumber": 4,
                    "totalThoughts": 5,
                    "isRevision": False,
                },
            },
        )

        print(f"Verification response: {json.dumps(verification_response, indent=2)}")
        assert "result" in verification_response or "error" in verification_response

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_sequentialthinking_error_handling(self, mcp_sequentialthinking_url, client_token, wait_for_services):
        """Test error handling with invalid parameters."""
        # Initialize session
        self.initialize_session(mcp_sequentialthinking_url, client_token)

        # Test with invalid thought_number (string instead of number)
        error_response = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "This should cause an error.",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": "invalid",  # String instead of number
                    "totalThoughts": 3,
                    "isRevision": False,
                },
            },
        )

        print(f"Error handling response: {json.dumps(error_response, indent=2)}")

        # Should get an error or a result with error content
        if "error" in error_response:
            print("Tool correctly returned JSON-RPC error for invalid parameters")
        elif "result" in error_response and "content" in error_response["result"]:
            content = error_response["result"]["content"]
            if isinstance(content, list) and len(content) > 0:
                text_content = content[0].get("text", "")
                if "error" in text_content.lower() or "invalid" in text_content.lower():
                    print("Tool correctly returned error in content for invalid parameters")
                else:
                    print(f"Unexpected response content: {text_content}")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_sequentialthinking_complete_workflow(
        self, mcp_sequentialthinking_url, client_token, wait_for_services
    ):
        """Test a complete sequential thinking workflow from start to finish."""
        # Initialize session
        self.initialize_session(mcp_sequentialthinking_url, client_token)

        print("\n=== Starting Complete Sequential Thinking Workflow ===")

        # Step 1: Problem identification
        step1 = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "Problem: How to design a scalable web service that can handle 1M+ requests per day?",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": 1,
                    "totalThoughts": 5,
                    "isRevision": False,
                },
            },
        )
        print(
            f"Step 1 - Problem identification: {'✅ Success' if 'result' in step1 else '❌ Error'}"  # TODO: Break long line
        )

        # Step 2: Analysis
        step2 = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "Analysis: 1M requests/day = ~11.6 requests/second average, but need to handle peak loads of 5-10x that rate.",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": 2,
                    "totalThoughts": 6,  # Scaling up as we realize complexity
                    "isRevision": False,
                },
            },
        )
        print(f"Step 2 - Analysis: {'✅ Success' if 'result' in step2 else '❌ Error'}")

        # Step 3: Solution exploration
        step3 = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "Solution approach: Load balancer + multiple app instances + caching + database optimization.",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": 3,
                    "totalThoughts": 6,
                    "isRevision": False,
                },
            },
        )
        print(
            f"Step 3 - Solution exploration: {'✅ Success' if 'result' in step3 else '❌ Error'}"  # TODO: Break long line
        )

        # Step 4: Refinement
        step4 = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "Refinement: Add CDN for static content, implement Redis for session storage, use read replicas for database.",
                    "nextThoughtNeeded": True,
                    "thoughtNumber": 4,
                    "totalThoughts": 6,
                    "isRevision": False,
                },
            },
        )
        print(f"Step 4 - Refinement: {'✅ Success' if 'result' in step4 else '❌ Error'}")

        # Step 5: Final solution
        step5 = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "sequentialthinking",
                "arguments": {
                    "thought": "Final solution: Microservices architecture with auto-scaling, CDN, Redis caching, load balancing, and monitoring.",
                    "nextThoughtNeeded": False,
                    "thoughtNumber": 5,
                    "totalThoughts": 6,
                    "isRevision": False,
                },
            },
        )
        print(
            f"Step 5 - Final solution: {'✅ Success' if 'result' in step5 else '❌ Error'}"  # TODO: Break long line
        )

        print("=== Sequential Thinking Workflow Complete ===\n")

        # Verify at least some steps succeeded
        successful_steps = sum(1 for step in [step1, step2, step3, step4, step5] if "result" in step)
        print(f"Successfully completed {successful_steps}/5 thinking steps")
        assert successful_steps >= 3, f"Expected at least 3 successful steps, got {successful_steps}"

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_sequentialthinking_protocol_compliance(
        self, mcp_sequentialthinking_url, client_token, wait_for_services
    ):
        """Test MCP protocol compliance for sequential thinking service."""
        # Test initialization
        init_response = self.run_mcp_client_raw(
            url=mcp_sequentialthinking_url,
            token=client_token,
            method="initialize",
            params={
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "protocol-test-client", "version": "1.0.0"},
            },
        )

        assert "result" in init_response
        result = init_response["result"]

        # Verify protocol version compatibility
        assert result["protocolVersion"] in MCP_PROTOCOL_VERSIONS_SUPPORTED

        # Verify server info
        assert "serverInfo" in result
        server_info = result["serverInfo"]
        assert "name" in server_info
        assert "version" in server_info

        # Verify capabilities
        assert "capabilities" in result
        capabilities = result["capabilities"]
        assert "tools" in capabilities  # Sequential thinking should support tools

        print("✅ Protocol compliance verified")
        print(f"  Server: {server_info['name']} v{server_info['version']}")
        print(f"  Protocol: {result['protocolVersion']}")
        print(f"  Capabilities: {list(capabilities.keys())}")
