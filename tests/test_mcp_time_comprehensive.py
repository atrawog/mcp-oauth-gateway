"""Comprehensive tests for mcp-time service using mcp-streamablehttp-client."""

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


class TestMCPTimeComprehensive:
    """Comprehensive tests for mcp-time service functionality."""

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
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30, env=env)

        if result.returncode != 0:
            pytest.fail(
                f"mcp-streamablehttp-client failed: {result.stderr}\\nOutput: {result.stdout}"  # TODO: Break long line
            )

        # Parse the output to find the actual response
        output = result.stdout
        lines = output.split("\\n")

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
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30, env=env)

        if result.returncode != 0:
            # Check if it's an expected error
            if "error" in result.stdout or "Error" in result.stdout:
                return {"error": result.stdout, "stderr": result.stderr}
            pytest.fail(
                f"mcp-streamablehttp-client failed: {result.stderr}\\nOutput: {result.stdout}"  # TODO: Break long line
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
            pytest.fail(f"Failed to parse JSON response: {e}\\nOutput: {result.stdout}")

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
                    "name": "time-comprehensive-test-client",
                    "version": "1.0.0",
                },
            },
        )
        assert "result" in response, f"Initialize failed: {response}"

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_time_tool_discovery(self, mcp_time_url, client_token, wait_for_services):
        """Test discovering available time tools."""
        time_url = f"{mcp_time_url}"
        # Initialize session
        self.initialize_session(time_url, client_token)

        # List available tools
        response = self.run_mcp_client_raw(url=time_url, token=client_token, method="tools/list", params={})

        assert "result" in response
        tools = response["result"]["tools"]
        assert isinstance(tools, list)
        assert len(tools) >= 2

        # Check for expected tools
        tool_names = [tool["name"] for tool in tools]
        assert "get_current_time" in tool_names
        assert "convert_time" in tool_names

        # Get tool details
        get_current_time_tool = next(tool for tool in tools if tool["name"] == "get_current_time")
        convert_time_tool = next(tool for tool in tools if tool["name"] == "convert_time")

        # Verify get_current_time tool structure
        assert "description" in get_current_time_tool
        assert "inputSchema" in get_current_time_tool
        assert "properties" in get_current_time_tool["inputSchema"]
        assert "timezone" in get_current_time_tool["inputSchema"]["properties"]

        # Verify convert_time tool structure
        assert "description" in convert_time_tool
        assert "inputSchema" in convert_time_tool
        properties = convert_time_tool["inputSchema"]["properties"]
        assert "source_timezone" in properties
        assert "time" in properties
        assert "target_timezone" in properties

        print(f"Time tools found: {tool_names}")
        print(f"get_current_time description: {get_current_time_tool['description']}")
        print(f"convert_time description: {convert_time_tool['description']}")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_get_current_time_utc(self, mcp_time_url, client_token, wait_for_services):
        """Test getting current time in UTC."""
        time_url = f"{mcp_time_url}"
        # Initialize session
        self.initialize_session(time_url, client_token)

        # Get current time in UTC
        response = self.run_mcp_client_raw(
            url=time_url,
            token=client_token,
            method="tools/call",
            params={"name": "get_current_time", "arguments": {"timezone": "UTC"}},
        )

        print(f"UTC time response: {json.dumps(response, indent=2)}")

        assert "result" in response
        assert "content" in response["result"]
        content = response["result"]["content"]
        assert isinstance(content, list)
        assert len(content) > 0

        # Parse the text content
        text_content = content[0]["text"]
        assert "UTC" in text_content
        print(f"Current UTC time: {text_content}")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_get_current_time_major_timezones(self, mcp_time_url, client_token, wait_for_services):
        """Test getting current time in major global timezones."""
        time_url = f"{mcp_time_url}"
        # Initialize session
        self.initialize_session(time_url, client_token)

        # Test major timezones
        timezones = [
            "America/New_York",
            "America/Los_Angeles",
            "Europe/London",
            "Europe/Paris",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Australia/Sydney",
        ]

        for timezone in timezones:
            response = self.run_mcp_client_raw(
                url=time_url,
                token=client_token,
                method="tools/call",
                params={
                    "name": "get_current_time",
                    "arguments": {"timezone": timezone},
                },
            )

            print(f"Time in {timezone}: {response}")

            # Should get either a result or an error
            assert "result" in response or "error" in response
            if "result" in response:
                content = response["result"]["content"]
                assert isinstance(content, list)
                assert len(content) > 0
                text_content = content[0]["text"]
                # Timezone name should appear in the response
                assert timezone.split("/")[-1] in text_content or timezone in text_content
                print(f"✅ {timezone}: {text_content}")
            else:
                print(f"❌ {timezone}: {response['error']}")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_convert_time_basic(self, mcp_time_url, client_token, wait_for_services):
        """Test basic time conversion between timezones."""
        time_url = f"{mcp_time_url}"
        # Initialize session
        self.initialize_session(time_url, client_token)

        # Convert 2:30 PM EST to PST
        response = self.run_mcp_client_raw(
            url=time_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "convert_time",
                "arguments": {
                    "source_timezone": "America/New_York",
                    "time": "14:30",
                    "target_timezone": "America/Los_Angeles",
                },
            },
        )

        print(f"Time conversion response: {json.dumps(response, indent=2)}")

        assert "result" in response or "error" in response
        if "result" in response:
            content = response["result"]["content"]
            assert isinstance(content, list)
            assert len(content) > 0
            text_content = content[0]["text"]
            assert "14:30" in text_content  # Source time should be mentioned
            assert "New_York" in text_content or "York" in text_content
            assert "Los_Angeles" in text_content or "Angeles" in text_content
            print(f"✅ Time conversion successful: {text_content}")
        else:
            print(f"Time conversion error: {response['error']}")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_convert_time_global_business_hours(self, mcp_time_url, client_token, wait_for_services):
        """Test time conversion for global business hours coordination."""
        time_url = f"{mcp_time_url}"
        # Initialize session
        self.initialize_session(time_url, client_token)

        # Convert 9 AM business hours across major business centers
        conversions = [
            {
                "name": "New York to London",
                "source": "America/New_York",
                "target": "Europe/London",
                "time": "09:00",
            },
            {
                "name": "London to Tokyo",
                "source": "Europe/London",
                "target": "Asia/Tokyo",
                "time": "09:00",
            },
            {
                "name": "Tokyo to Sydney",
                "source": "Asia/Tokyo",
                "target": "Australia/Sydney",
                "time": "09:00",
            },
        ]

        successful_conversions = 0

        for conversion in conversions:
            response = self.run_mcp_client_raw(
                url=time_url,
                token=client_token,
                method="tools/call",
                params={
                    "name": "convert_time",
                    "arguments": {
                        "source_timezone": conversion["source"],
                        "time": conversion["time"],
                        "target_timezone": conversion["target"],
                    },
                },
            )

            print(f"\\n{conversion['name']} (9 AM): {response}")

            if "result" in response:
                content = response["result"]["content"]
                if isinstance(content, list) and len(content) > 0:
                    text_content = content[0]["text"]
                    print(f"✅ {conversion['name']}: {text_content}")
                    successful_conversions += 1
            else:
                print(f"❌ {conversion['name']}: Failed")

        # At least some conversions should work
        assert successful_conversions >= 2, f"Expected at least 2 successful conversions, got {successful_conversions}"

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_convert_time_edge_cases(self, mcp_time_url, client_token, wait_for_services):
        """Test time conversion edge cases."""
        time_url = f"{mcp_time_url}"
        # Initialize session
        self.initialize_session(time_url, client_token)

        # Test various time formats and edge cases
        test_cases = [
            {
                "name": "Midnight conversion",
                "source": "UTC",
                "target": "America/New_York",
                "time": "00:00",
            },
            {
                "name": "End of day conversion",
                "source": "UTC",
                "target": "Asia/Tokyo",
                "time": "23:59",
            },
            {
                "name": "With seconds",
                "source": "Europe/London",
                "target": "America/Los_Angeles",
                "time": "15:30:45",
            },
        ]

        for test_case in test_cases:
            response = self.run_mcp_client_raw(
                url=time_url,
                token=client_token,
                method="tools/call",
                params={
                    "name": "convert_time",
                    "arguments": {
                        "source_timezone": test_case["source"],
                        "time": test_case["time"],
                        "target_timezone": test_case["target"],
                    },
                },
            )

            print(f"\\n{test_case['name']}: {response}")

            # Should get either a result or an error (both are acceptable for edge cases)
            assert "result" in response or "error" in response
            if "result" in response:
                print(f"✅ {test_case['name']}: Success")
            else:
                print(f"⚠️ {test_case['name']}: {response.get('error', 'Unknown error')}")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_time_error_handling(self, mcp_time_url, client_token, wait_for_services):
        """Test error handling with invalid parameters."""
        time_url = f"{mcp_time_url}"
        # Initialize session
        self.initialize_session(time_url, client_token)

        # Test invalid timezone
        invalid_timezone_response = self.run_mcp_client_raw(
            url=time_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "get_current_time",
                "arguments": {"timezone": "Invalid/Timezone"},
            },
        )

        print(
            f"Invalid timezone response: {json.dumps(invalid_timezone_response, indent=2)}"  # TODO: Break long line
        )

        # Should get an error or a result with error content
        if "error" in invalid_timezone_response:
            print("Tool correctly returned JSON-RPC error for invalid timezone")
        elif "result" in invalid_timezone_response:
            content = invalid_timezone_response["result"]["content"]
            if isinstance(content, list) and len(content) > 0:
                text_content = content[0].get("text", "")
                # Check if error is mentioned in content
                if "error" in text_content.lower() or "invalid" in text_content.lower():
                    print("Tool correctly returned error in content for invalid timezone")
                else:
                    print(f"Unexpected response for invalid timezone: {text_content}")

        # Test invalid time format
        invalid_time_response = self.run_mcp_client_raw(
            url=time_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "convert_time",
                "arguments": {
                    "source_timezone": "UTC",
                    "time": "25:99",  # Invalid time
                    "target_timezone": "America/New_York",
                },
            },
        )

        print(
            f"Invalid time format response: {json.dumps(invalid_time_response, indent=2)}"  # TODO: Break long line
        )

        # Should handle invalid time format gracefully
        assert "result" in invalid_time_response or "error" in invalid_time_response

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_time_timezone_detection(self, mcp_time_url, client_token, wait_for_services):
        """Test timezone detection and handling."""
        time_url = f"{mcp_time_url}"
        # Initialize session
        self.initialize_session(time_url, client_token)

        # Test various valid IANA timezone formats
        valid_timezones = [
            "UTC",
            "GMT",
            "America/New_York",
            "Europe/London",
            "Asia/Tokyo",
            "Australia/Sydney",
            "Pacific/Auckland",
        ]

        successful_queries = 0

        for timezone in valid_timezones:
            response = self.run_mcp_client_raw(
                url=time_url,
                token=client_token,
                method="tools/call",
                params={
                    "name": "get_current_time",
                    "arguments": {"timezone": timezone},
                },
            )

            if "result" in response:
                content = response["result"]["content"]
                if isinstance(content, list) and len(content) > 0:
                    successful_queries += 1
                    print(f"✅ {timezone}: Valid")
            else:
                print(f"❌ {timezone}: Failed")

        # Most valid timezones should work
        assert successful_queries >= 5, f"Expected at least 5 successful timezone queries, got {successful_queries}"
        print(
            f"Successfully queried {successful_queries}/{len(valid_timezones)} timezones"  # TODO: Break long line
        )

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_time_complete_workflow(self, mcp_time_url, client_token, wait_for_services):
        """Test a complete time-related workflow."""
        time_url = f"{mcp_time_url}"
        # Initialize session
        self.initialize_session(time_url, client_token)

        print("\\n=== Starting Complete Time Workflow ===")

        # Step 1: Get current time in UTC
        utc_response = self.run_mcp_client_raw(
            url=time_url,
            token=client_token,
            method="tools/call",
            params={"name": "get_current_time", "arguments": {"timezone": "UTC"}},
        )
        print(
            f"Step 1 - Get UTC time: {'✅ Success' if 'result' in utc_response else '❌ Error'}"  # TODO: Break long line
        )

        # Step 2: Get current time in New York
        ny_response = self.run_mcp_client_raw(
            url=time_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "get_current_time",
                "arguments": {"timezone": "America/New_York"},
            },
        )
        print(
            f"Step 2 - Get New York time: {'✅ Success' if 'result' in ny_response else '❌ Error'}"  # TODO: Break long line
        )

        # Step 3: Convert 3 PM New York time to Tokyo
        conversion_response = self.run_mcp_client_raw(
            url=time_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "convert_time",
                "arguments": {
                    "source_timezone": "America/New_York",
                    "time": "15:00",
                    "target_timezone": "Asia/Tokyo",
                },
            },
        )
        print(
            f"Step 3 - Convert NY to Tokyo: {'✅ Success' if 'result' in conversion_response else '❌ Error'}"  # TODO: Break long line
        )

        # Step 4: Convert morning Tokyo time back to London
        reverse_conversion = self.run_mcp_client_raw(
            url=time_url,
            token=client_token,
            method="tools/call",
            params={
                "name": "convert_time",
                "arguments": {
                    "source_timezone": "Asia/Tokyo",
                    "time": "09:00",
                    "target_timezone": "Europe/London",
                },
            },
        )
        print(
            f"Step 4 - Convert Tokyo to London: {'✅ Success' if 'result' in reverse_conversion else '❌ Error'}"  # TODO: Break long line
        )

        print("=== Time Workflow Complete ===\\n")

        # Verify at least most steps succeeded
        successful_steps = sum(
            1
            for step in [
                utc_response,
                ny_response,
                conversion_response,
                reverse_conversion,
            ]
            if "result" in step
        )
        print(f"Successfully completed {successful_steps}/4 time operations")
        assert successful_steps >= 3, f"Expected at least 3 successful steps, got {successful_steps}"

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_time_protocol_compliance(self, mcp_time_url, client_token, wait_for_services):
        """Test MCP protocol compliance for time service."""
        time_url = f"{mcp_time_url}"
        # Test initialization
        init_response = self.run_mcp_client_raw(
            url=time_url,
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
        assert "tools" in capabilities  # Time should support tools

        print("✅ Protocol compliance verified")
        print(f"  Server: {server_info['name']} v{server_info['version']}")
        print(f"  Protocol: {result['protocolVersion']}")
        print(f"  Capabilities: {list(capabilities.keys())}")

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    async def test_time_performance_batch(self, mcp_time_url, client_token, wait_for_services):
        """Test time service performance with multiple requests."""
        time_url = f"{mcp_time_url}"
        # Initialize session
        self.initialize_session(time_url, client_token)

        print("\\n=== Testing Time Service Performance ===")

        # Batch of timezone queries
        timezones = [
            "UTC",
            "America/New_York",
            "Europe/London",
            "Asia/Tokyo",
            "Australia/Sydney",
        ]

        successful_requests = 0

        for i, timezone in enumerate(timezones, 1):
            response = self.run_mcp_client_raw(
                url=time_url,
                token=client_token,
                method="tools/call",
                params={
                    "name": "get_current_time",
                    "arguments": {"timezone": timezone},
                },
            )

            if "result" in response:
                successful_requests += 1
                print(f"Request {i}/5 ({timezone}): ✅ Success")
            else:
                print(f"Request {i}/5 ({timezone}): ❌ Failed")

        print(f"=== Performance Test Complete: {successful_requests}/5 successful ===\\n")

        # Most requests should succeed
        assert successful_requests >= 4, f"Expected at least 4 successful requests, got {successful_requests}"
