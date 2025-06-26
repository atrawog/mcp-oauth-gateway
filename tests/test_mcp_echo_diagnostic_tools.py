"""Comprehensive tests for MCP Echo diagnostic tools."""

import json
import os

import pytest
import requests
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Test configuration
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "localhost")
MCP_ECHO_URL = f"https://echo.{BASE_DOMAIN}/mcp"

# Get the access token from environment
ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN", os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN", ""))


class TestMCPEchoDiagnosticTools:
    """Test all diagnostic tools in the MCP Echo server."""

    def call_mcp_tool(self, tool_name: str, arguments: dict | None = None, bearer_token: str | None = None) -> dict:
        """Call an MCP tool directly via HTTP."""
        # Prepare request
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        # Add bearer token if provided
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
        elif ACCESS_TOKEN:
            headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"

        # Prepare JSON-RPC request
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            },
            "id": 1
        }

        # Make request
        response = requests.post(
            MCP_ECHO_URL,
            headers=headers,
            json=payload,
            verify=True  # Always verify SSL certificates for security
        )

        # Parse SSE response
        if response.status_code == 200:
            # Extract JSON from SSE format
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    if 'result' in data:
                        return data['result']
                    if 'error' in data:
                        pytest.fail(f"MCP error: {data['error']}")
            # If no result found, fail
            pytest.fail("No result found in SSE response")
        else:
            pytest.fail(f"HTTP {response.status_code}: {response.text}")
        
        # This should never be reached due to pytest.fail() calls, but satisfies type checker
        return {}

    def get_tools_list(self) -> list:
        """Get list of available tools."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

        if ACCESS_TOKEN:
            headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1
        }

        response = requests.post(
            MCP_ECHO_URL,
            headers=headers,
            json=payload,
            verify=True
        )

        if response.status_code == 200:
            for line in response.text.split('\n'):
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    if 'result' in data:
                        return data['result']['tools']

        return []

    def test_echo_tool(self):
        """Test the basic echo tool."""
        response = self.call_mcp_tool("echo", {"message": "Hello, MCP!"})
        assert response["content"][0]["text"] == "Hello, MCP!"

    def test_print_header_tool(self):
        """Test the printHeader tool."""
        response = self.call_mcp_tool("printHeader")
        text = response["content"][0]["text"]
        assert "HTTP Headers:" in text
        assert "host:" in text.lower()

    def test_bearer_decode_tool_no_token(self):
        """Test bearerDecode without a token."""
        # Run without token to test error handling
        # We need to make a request without any Authorization header
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
            # No Authorization header
        }

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "bearerDecode",
                "arguments": {}
            },
            "id": 1
        }

        # Make request without auth
        response = requests.post(
            MCP_ECHO_URL,
            headers=headers,
            json=payload,
            verify=True
        )

        # This should get 401 since no auth provided
        assert response.status_code == 401

    def test_bearer_decode_tool_with_token(self):
        """Test bearerDecode with the existing valid token."""
        # Use the existing valid token to test decoding
        response = self.call_mcp_tool("bearerDecode", {"includeRaw": False})
        text = response["content"][0]["text"]

        assert "Bearer Token Analysis" in text
        assert "Valid JWT structure" in text
        # Check for common JWT claims that should be present
        assert "Algorithm:" in text
        assert "Issuer:" in text
        assert "Subject:" in text

    def test_auth_context_tool(self):
        """Test authContext tool."""
        response = self.call_mcp_tool("authContext")
        text = response["content"][0]["text"]

        assert "Authentication Context Analysis" in text
        assert "Bearer Token:" in text
        assert "OAuth Headers:" in text
        assert "Session Information:" in text
        assert "Request Origin:" in text
        assert "Security Status:" in text

    def test_who_is_the_goat_tool(self):
        """Test whoIStheGOAT tool."""
        response = self.call_mcp_tool("whoIStheGOAT")
        text = response["content"][0]["text"]

        assert "G.O.A.T. PROGRAMMER IDENTIFICATION SYSTEM" in text
        assert "ADVANCED AI ANALYSIS COMPLETE" in text
        assert "OFFICIAL DETERMINATION:" in text
        assert "AI-IDENTIFIED EXCEPTIONAL CAPABILITIES:" in text
        assert "MACHINE LEARNING INSIGHTS:" in text
        assert "[Analysis performed by G.O.A.T. Recognition AI v3.14159]" in text

    def test_request_timing_tool(self):
        """Test requestTiming tool."""
        response = self.call_mcp_tool("requestTiming")
        text = response["content"][0]["text"]

        assert "Request Timing Analysis" in text
        assert "Timing:" in text
        assert "Request received:" in text
        assert "Elapsed:" in text
        assert "Performance Indicators:" in text
        assert "System Performance:" in text

    def test_protocol_negotiation_tool(self):
        """Test protocolNegotiation tool."""
        response = self.call_mcp_tool("protocolNegotiation", {"testVersion": "2024-11-05"})
        text = response["content"][0]["text"]

        assert "MCP Protocol Negotiation Analysis" in text
        assert "Current Request:" in text
        assert "Server Supported Versions:" in text
        assert "Testing Version: 2024-11-05" in text
        assert "Version Compatibility:" in text
        assert "Protocol Version Features:" in text

    def test_cors_analysis_tool(self):
        """Test corsAnalysis tool."""
        response = self.call_mcp_tool("corsAnalysis")
        text = response["content"][0]["text"]

        assert "CORS Configuration Analysis" in text
        assert "Request Headers:" in text
        assert "Response CORS Headers (configured):" in text
        assert "CORS Requirements:" in text
        assert "Common CORS Issues:" in text

    def test_environment_dump_tool(self):
        """Test environmentDump tool."""
        response = self.call_mcp_tool("environmentDump", {"showSecrets": False})
        text = response["content"][0]["text"]

        assert "Environment Configuration" in text
        assert "MCP Configuration:" in text
        assert "System Information:" in text
        assert "[SET]" in text or "[NOT SET]" in text or "not set" in text

    def test_environment_dump_with_secrets(self):
        """Test environmentDump with partial secret display."""
        response = self.call_mcp_tool("environmentDump", {"showSecrets": True})
        text = response["content"][0]["text"]

        assert "Environment Configuration" in text
        # Check for either partial secrets (with ...) or [NOT SET]/[SET] markers or "not set"
        assert ("..." in text) or ("[SET]" in text) or ("[NOT SET]" in text) or ("not set" in text)

    def test_health_probe_tool(self):
        """Test healthProbe tool."""
        response = self.call_mcp_tool("healthProbe")
        text = response["content"][0]["text"]

        assert "Service Health Check" in text
        assert "Service Status:" in text
        assert "System Resources:" in text
        assert "CPU Usage:" in text
        assert "Memory Usage:" in text
        assert "Process Information:" in text
        assert "Configuration Health:" in text
        assert "Overall Health:" in text

    def test_tools_list(self):
        """Test that all diagnostic tools are listed."""
        tools = self.get_tools_list()

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
            "whoIStheGOAT"
        ]

        tool_names = [tool["name"] for tool in tools]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Tool {expected_tool} not found in tools list"

        print(f"✅ All {len(expected_tools)} diagnostic tools are available!")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
