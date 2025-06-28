"""Comprehensive tests for MCP Echo diagnostic tools.

This test file follows CLAUDE.md Sacred Commandments:
- NO MOCKING - Tests against real deployed mcp-echo service
- NO HARDCODED VALUES - All configuration from environment
- Uses mcp_echo_stateless_url fixture for URL configuration
"""

import json

import httpx
import pytest


class TestMCPEchoDiagnosticTools:
    """Test all diagnostic tools in the MCP Echo server."""

    async def call_mcp_tool(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
        gateway_auth_headers: dict,
        tool_name: str,
        arguments: dict | None = None,
        bearer_token: str | None = None,
    ) -> dict:
        """Call an MCP tool directly via HTTP."""
        # Prepare request
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

        # Add bearer token if provided
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
        else:
            headers.update(gateway_auth_headers)

        # Prepare JSON-RPC request
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments or {}},
            "id": 1,
        }

        # Make request
        response = await http_client.post(
            mcp_echo_stateless_url,
            headers=headers,
            json=payload,
        )

        # Parse response (can be either SSE or JSON format)
        if response.status_code == 200:
            # Check if it's SSE format (contains "data: " lines)
            if "data: " in response.text:
                # Extract JSON from SSE format
                for line in response.text.split("\n"):
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if "result" in data:
                            return data["result"]
                        if "error" in data:
                            pytest.fail(f"MCP error: {data['error']}")
                # If no result found in SSE, fail
                pytest.fail("No result found in SSE response")
            else:
                # Try parsing as plain JSON
                try:
                    data = json.loads(response.text)
                    if "result" in data:
                        return data["result"]
                    if "error" in data:
                        pytest.fail(f"MCP error: {data['error']}")
                    # If neither result nor error, fail
                    pytest.fail(f"Invalid JSON response: {response.text}")
                except json.JSONDecodeError:
                    pytest.fail(f"Failed to parse response as JSON: {response.text}")
        else:
            pytest.fail(f"HTTP {response.status_code}: {response.text}")

        # This should never be reached due to pytest.fail() calls, but satisfies type checker
        return {}

    async def get_tools_list(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
        gateway_auth_headers: dict,
    ) -> list:
        """Get list of available tools."""
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        headers.update(gateway_auth_headers)

        payload = {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}

        response = await http_client.post(mcp_echo_stateless_url, headers=headers, json=payload)

        if response.status_code == 200:
            # Check if it's SSE format
            if "data: " in response.text:
                for line in response.text.split("\n"):
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if "result" in data:
                            return data["result"]["tools"]
            else:
                # Try parsing as plain JSON
                try:
                    data = json.loads(response.text)
                    if "result" in data:
                        return data["result"]["tools"]
                except json.JSONDecodeError:
                    pass

        return []

    @pytest.mark.asyncio
    async def test_echo_tool(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
        gateway_auth_headers: dict,
    ):
        """Test the basic echo tool."""
        response = await self.call_mcp_tool(
            http_client,
            mcp_echo_stateless_url,
            gateway_auth_headers,
            "echo",
            {"message": "Hello, MCP!"},
        )
        assert response["content"][0]["text"] == "Hello, MCP!"

    @pytest.mark.asyncio
    async def test_print_header_tool(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
        gateway_auth_headers: dict,
    ):
        """Test the printHeader tool."""
        response = await self.call_mcp_tool(http_client, mcp_echo_stateless_url, gateway_auth_headers, "printHeader")
        text = response["content"][0]["text"]
        assert "HTTP Headers:" in text
        assert "host:" in text.lower()

    @pytest.mark.asyncio
    async def test_bearer_decode_tool_no_token(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
    ):
        """Test bearerDecode without a token."""
        # Run without token to test error handling
        # We need to make a request without any Authorization header
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            # No Authorization header
        }

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "bearerDecode", "arguments": {}},
            "id": 1,
        }

        # Make request without auth
        response = await http_client.post(mcp_echo_stateless_url, headers=headers, json=payload)

        # This should get 401 since no auth provided
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_bearer_decode_tool_with_token(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
        gateway_auth_headers: dict,
    ):
        """Test bearerDecode with the existing valid token."""
        # Use the existing valid token to test decoding
        response = await self.call_mcp_tool(
            http_client,
            mcp_echo_stateless_url,
            gateway_auth_headers,
            "bearerDecode",
            {"includeRaw": False},
        )
        text = response["content"][0]["text"]

        assert "Bearer Token Analysis" in text
        assert "Valid JWT structure" in text
        # Check for common JWT claims that should be present
        assert "Algorithm:" in text
        assert "Issuer:" in text
        assert "Subject:" in text

    @pytest.mark.asyncio
    async def test_auth_context_tool(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
        gateway_auth_headers: dict,
    ):
        """Test authContext tool."""
        response = await self.call_mcp_tool(http_client, mcp_echo_stateless_url, gateway_auth_headers, "authContext")
        text = response["content"][0]["text"]

        assert "Authentication Context Analysis" in text
        assert "Bearer Token:" in text
        assert "OAuth Headers:" in text
        assert "Session Information:" in text
        assert "Request Origin:" in text
        assert "Security Status:" in text

    @pytest.mark.asyncio
    async def test_who_is_the_goat_tool(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
        gateway_auth_headers: dict,
    ):
        """Test whoIStheGOAT tool."""
        response = await self.call_mcp_tool(http_client, mcp_echo_stateless_url, gateway_auth_headers, "whoIStheGOAT")
        text = response["content"][0]["text"]

        assert "G.O.A.T. PROGRAMMER IDENTIFICATION SYSTEM" in text
        assert "ADVANCED AI ANALYSIS COMPLETE" in text
        assert "OFFICIAL DETERMINATION:" in text
        assert "AI-IDENTIFIED EXCEPTIONAL CAPABILITIES:" in text
        assert "MACHINE LEARNING INSIGHTS:" in text
        assert "[Analysis performed by G.O.A.T. Recognition AI v3.14159]" in text

    @pytest.mark.asyncio
    async def test_request_timing_tool(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
        gateway_auth_headers: dict,
    ):
        """Test requestTiming tool."""
        response = await self.call_mcp_tool(http_client, mcp_echo_stateless_url, gateway_auth_headers, "requestTiming")
        text = response["content"][0]["text"]

        assert "Request Timing Analysis" in text
        assert "Timing:" in text
        assert "Request received:" in text
        assert "Elapsed:" in text
        assert "Performance Indicators:" in text
        assert "System Performance:" in text

    @pytest.mark.asyncio
    async def test_protocol_negotiation_tool(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
        gateway_auth_headers: dict,
    ):
        """Test protocolNegotiation tool."""
        response = await self.call_mcp_tool(
            http_client,
            mcp_echo_stateless_url,
            gateway_auth_headers,
            "protocolNegotiation",
            {"testVersion": "2024-11-05"},
        )
        text = response["content"][0]["text"]

        assert "MCP Protocol Negotiation Analysis" in text
        assert "Current Request:" in text
        assert "Server Supported Versions:" in text
        assert "Testing Version: 2024-11-05" in text
        assert "Version Compatibility:" in text
        assert "Protocol Version Features:" in text

    @pytest.mark.asyncio
    async def test_cors_analysis_tool(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
        gateway_auth_headers: dict,
    ):
        """Test corsAnalysis tool."""
        response = await self.call_mcp_tool(http_client, mcp_echo_stateless_url, gateway_auth_headers, "corsAnalysis")
        text = response["content"][0]["text"]

        assert "CORS Configuration Analysis" in text
        assert "Request Headers:" in text
        assert "Response CORS Headers (set by Traefik):" in text
        assert "CORS Requirements:" in text
        assert "Common CORS Issues:" in text

    @pytest.mark.asyncio
    async def test_environment_dump_tool(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
        gateway_auth_headers: dict,
    ):
        """Test environmentDump tool."""
        response = await self.call_mcp_tool(
            http_client,
            mcp_echo_stateless_url,
            gateway_auth_headers,
            "environmentDump",
            {"showSecrets": False},
        )
        text = response["content"][0]["text"]

        assert "Environment Configuration" in text
        assert "MCP Configuration:" in text
        assert "System Information:" in text
        assert "[SET]" in text or "[NOT SET]" in text or "not set" in text

    @pytest.mark.asyncio
    async def test_environment_dump_with_secrets(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
        gateway_auth_headers: dict,
    ):
        """Test environmentDump with partial secret display."""
        response = await self.call_mcp_tool(
            http_client,
            mcp_echo_stateless_url,
            gateway_auth_headers,
            "environmentDump",
            {"showSecrets": True},
        )
        text = response["content"][0]["text"]

        assert "Environment Configuration" in text
        # Check for either partial secrets (with ...) or [NOT SET]/[SET] markers or "not set"
        assert ("..." in text) or ("[SET]" in text) or ("[NOT SET]" in text) or ("not set" in text)

    @pytest.mark.asyncio
    async def test_health_probe_tool(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
        gateway_auth_headers: dict,
    ):
        """Test healthProbe tool."""
        response = await self.call_mcp_tool(http_client, mcp_echo_stateless_url, gateway_auth_headers, "healthProbe")
        text = response["content"][0]["text"]

        assert "Service Health Check" in text
        assert "Service Status:" in text
        assert "System Resources:" in text
        assert "CPU Usage:" in text
        assert "Memory Usage:" in text
        assert "Process Information:" in text
        assert "Configuration Health:" in text
        assert "Overall Health:" in text

    @pytest.mark.asyncio
    async def test_tools_list(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateless_url: str,
        gateway_auth_headers: dict,
    ):
        """Test that all diagnostic tools are listed."""
        tools = await self.get_tools_list(http_client, mcp_echo_stateless_url, gateway_auth_headers)

        # Check all tools are listed
        expected_tools = [
            "echo",
            "printHeader",
            "bearerDecode",
            "authContext",
            "requestTiming",
            "protocolNegotiation",
            "corsAnalysis",
            "environmentDump",
            "healthProbe",
            "whoIStheGOAT",
        ]

        tool_names = [tool["name"] for tool in tools]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Tool {expected_tool} not found in tools list"

        print(f"✅ All {len(expected_tools)} diagnostic tools are available!")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
