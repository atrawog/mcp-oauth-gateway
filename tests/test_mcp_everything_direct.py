"""Direct test of mcp-everything service capabilities."""

import asyncio
import json
from typing import Any

import httpx
import pytest

from tests.test_constants import BASE_DOMAIN
from tests.test_constants import MCP_CLIENT_ACCESS_TOKEN
from tests.test_constants import MCP_EVERYTHING_TESTS_ENABLED
from tests.test_constants import MCP_EVERYTHING_URLS


@pytest.fixture()
def base_domain():
    """Base domain for tests."""
    return BASE_DOMAIN


@pytest.fixture()
def everything_url():
    """Full URL for everything service."""
    if not MCP_EVERYTHING_TESTS_ENABLED:
        pytest.skip("MCP Everything tests are disabled. Set MCP_EVERYTHING_TESTS_ENABLED=true to enable.")
    if not MCP_EVERYTHING_URLS:
        pytest.skip("MCP_EVERYTHING_URLS environment variable not set")
    return MCP_EVERYTHING_URLS[0]


@pytest.fixture()
def client_token():
    """MCP client OAuth token for testing."""
    return MCP_CLIENT_ACCESS_TOKEN


class TestMCPEverythingDirect:
    """Direct test of mcp-everything using HTTP client."""

    async def send_mcp_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        params: dict[str, Any] | None = None,
        request_id: int = 1,
    ) -> tuple[dict[str, Any], httpx.Response]:
        """Send a JSON-RPC request to the MCP server."""
        request = {"jsonrpc": "2.0", "method": method, "id": request_id}
        if params is not None:
            request["params"] = params

        response = await client.post("", json=request)

        # Handle SSE response format
        if response.headers.get("content-type", "").startswith("text/event-stream"):
            # Parse SSE
            for line in response.text.strip().split("\n"):
                if line.startswith("data: "):
                    return json.loads(line[6:]), response

        return response.json(), response

    @pytest.mark.integration()
    @pytest.mark.asyncio()
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_server_capabilities(self, everything_url, client_token):
        """Test the everything server's capabilities directly."""
        headers = {
            "Authorization": f"Bearer {client_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": "2025-06-18",
        }

        async with httpx.AsyncClient(base_url=everything_url, headers=headers, timeout=30.0) as client:
            # 1. Initialize connection
            print("\n=== Testing mcp-everything server ===")
            print("1. Initializing connection...")

            init_data, init_response = await self.send_mcp_request(
                client,
                "initialize",
                {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "tools": {},
                        "resources": {"subscribe": True},
                        "prompts": {},
                        "logging": {},
                        "completions": {},
                    },
                    "clientInfo": {"name": "test-direct-client", "version": "1.0.0"},
                },
            )

            assert "result" in init_data
            result = init_data["result"]
            assert result["protocolVersion"] == "2025-06-18"
            assert "serverInfo" in result
            print(
                f"Server: {result['serverInfo']['name']} v{result['serverInfo']['version']}"  # TODO: Break long line
            )
            print(f"Capabilities: {list(result.get('capabilities', {}).keys())}")

            # Get session ID from response headers
            session_id = None
            for header in init_response.headers.get("mcp-session-id", "").split(","):
                if header.strip():
                    session_id = header.strip()
                    break

            if session_id:
                print(f"Got session ID from headers: {session_id}")
                # Add session header for subsequent requests
                client.headers["Mcp-Session-Id"] = session_id
            else:
                print("No session ID in headers!")

            # 2. Send initialized notification (as a notification, not a request)
            print("\n2. Sending initialized notification...")
            print(f"Current headers: {dict(client.headers)}")
            notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            # Send notification without expecting a response
            init_notif_response = await client.post("", json=notification)
            print(f"Notification response status: {init_notif_response.status_code}")
            if init_notif_response.status_code != 200:
                print(f"Notification response: {init_notif_response.text}")

            # Give server a moment to process the notification
            await asyncio.sleep(0.1)

            # 3. List available tools
            print("\n2. Listing available tools...")
            tools_data, _ = await self.send_mcp_request(client, "tools/list", {}, request_id=2)

            if "result" in tools_data:
                tools = tools_data["result"]["tools"]
                print(f"Found {len(tools)} tools:")
                for tool in tools[:5]:  # Show first 5
                    print(f"  - {tool['name']}: {tool['description'][:60]}...")

                # Store tool names for later use
                tool_names = [t["name"] for t in tools]
            else:
                print(f"Error listing tools: {tools_data}")
                tool_names = []

            # 4. List available resources
            print("\n3. Listing available resources...")
            resources_data, _ = await self.send_mcp_request(client, "resources/list", {}, request_id=3)

            if "result" in resources_data:
                resources = resources_data["result"]["resources"]
                print(f"Found {len(resources)} resources:")
                for resource in resources[:5]:  # Show first 5
                    print(f"  - {resource['uri']}: {resource['name']}")
            else:
                print(f"Error listing resources: {resources_data}")

            # 5. List available prompts
            print("\n4. Listing available prompts...")
            prompts_data, _ = await self.send_mcp_request(client, "prompts/list", {}, request_id=4)

            if "result" in prompts_data:
                prompts = prompts_data["result"]["prompts"]
                print(f"Found {len(prompts)} prompts:")
                for prompt in prompts[:5]:  # Show first 5
                    print(f"  - {prompt['name']}: {prompt['description'][:60]}...")
            else:
                print(f"Error listing prompts: {prompts_data}")

            # 6. Try calling a simple tool if available
            if "echo" in tool_names:
                print("\n5. Testing echo tool...")
                echo_data, _ = await self.send_mcp_request(
                    client,
                    "tools/call",
                    {"name": "echo", "arguments": {"message": "Hello from test!"}},
                    request_id=5,
                )

                if "result" in echo_data:
                    print(f"Echo response: {echo_data['result']}")
                else:
                    print(f"Echo error: {echo_data}")

            # 7. Test error handling
            print("\n6. Testing error handling...")
            error_data, _ = await self.send_mcp_request(
                client,
                "tools/call",
                {"name": "nonexistent_tool", "arguments": {}},
                request_id=6,
            )

            if "error" in error_data:
                print(f"Expected error: {error_data['error']['message']}")
            else:
                print(f"Unexpected response: {error_data}")

            print("\n=== Test completed successfully ===")

            # Verify we got meaningful responses
            assert len(tool_names) > 0, "Should have discovered some tools"
