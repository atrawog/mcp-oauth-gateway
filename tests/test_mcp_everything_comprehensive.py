"""Comprehensive test of mcp-everything service features using mcp-streamablehttp-client."""

import subprocess
import os
import pytest
import json

from tests.conftest import ensure_services_ready
from tests.test_constants import BASE_DOMAIN, MCP_CLIENT_ACCESS_TOKEN, MCP_EVERYTHING_TESTS_ENABLED, MCP_EVERYTHING_URLS


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


class TestMCPEverythingComprehensive:
    """Comprehensive test of mcp-everything features."""
    
    def run_client_command(self, url: str, token: str, command: str) -> tuple[int, str, str]:
        """Run mcp-streamablehttp-client with a command and return result."""
        # Set environment variables
        env = os.environ.copy()
        env["MCP_SERVER_URL"] = url
        env["MCP_CLIENT_ACCESS_TOKEN"] = token
        
        # Build the command
        cmd = [
            "pixi", "run", "mcp-streamablehttp-client",
            "--server-url", url,
            "--command", command
        ]
        
        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        
        return result.returncode, result.stdout, result.stderr
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_echo_tool(self, everything_url, client_token, wait_for_services):
        """Test the echo tool with a message."""
        returncode, stdout, stderr = self.run_client_command(
            url=everything_url,
            token=client_token,
            command='echo "Hello from comprehensive test!"'
        )
        
        print(f"Return code: {returncode}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")
        
        assert returncode == 0
        assert "Hello from comprehensive test!" in stdout
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_add_tool(self, everything_url, client_token, wait_for_services):
        """Test the add tool with two numbers."""
        # Test with JSON format
        returncode, stdout, stderr = self.run_client_command(
            url=everything_url,
            token=client_token,
            command='add {"a": 5, "b": 3}'
        )
        
        print(f"Return code: {returncode}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")
        
        assert returncode == 0
        assert "8" in stdout or "5 + 3 = 8" in stdout
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_add_tool_key_value(self, everything_url, client_token, wait_for_services):
        """Test the add tool with key=value format."""
        returncode, stdout, stderr = self.run_client_command(
            url=everything_url,
            token=client_token,
            command="add a=10 b=15"
        )
        
        print(f"Return code: {returncode}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")
        
        assert returncode == 0
        assert "25" in stdout or "10 + 15 = 25" in stdout
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_printenv_tool(self, everything_url, client_token, wait_for_services):
        """Test the printEnv tool."""
        returncode, stdout, stderr = self.run_client_command(
            url=everything_url,
            token=client_token,
            command="printEnv"
        )
        
        print(f"Return code: {returncode}")
        print(f"Stdout (first 500 chars): {stdout[:500]}...")
        print(f"Stderr: {stderr}")
        
        assert returncode == 0
        # Should show environment variables
        assert "Environment Variables" in stdout or "PATH" in stdout or "=" in stdout
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_annotated_message_tool(self, everything_url, client_token, wait_for_services):
        """Test the annotatedMessage tool with different message types."""
        # Test error message
        returncode, stdout, stderr = self.run_client_command(
            url=everything_url,
            token=client_token,
            command='annotatedMessage {"messageType": "error"}'
        )
        
        print(f"\n=== Error Message Test ===")
        print(f"Return code: {returncode}")
        print(f"Stdout: {stdout}")
        
        assert returncode == 0
        assert "error" in stdout.lower() or "Error" in stdout
        
        # Test success message
        returncode, stdout, stderr = self.run_client_command(
            url=everything_url,
            token=client_token,
            command='annotatedMessage {"messageType": "success"}'
        )
        
        print(f"\n=== Success Message Test ===")
        print(f"Return code: {returncode}")
        print(f"Stdout: {stdout}")
        
        assert returncode == 0
        assert "success" in stdout.lower() or "Success" in stdout
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_get_resource_reference(self, everything_url, client_token, wait_for_services):
        """Test the getResourceReference tool."""
        returncode, stdout, stderr = self.run_client_command(
            url=everything_url,
            token=client_token,
            command='getResourceReference {"resourceId": 42}'
        )
        
        print(f"Return code: {returncode}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")
        
        assert returncode == 0
        # Should return a resource reference
        assert "resource" in stdout.lower() or "42" in stdout
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_invalid_tool_parameters(self, everything_url, client_token, wait_for_services):
        """Test error handling for invalid tool parameters."""
        # Try echo without required message
        returncode, stdout, stderr = self.run_client_command(
            url=everything_url,
            token=client_token,
            command="echo"
        )
        
        print(f"Return code: {returncode}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")
        
        # Should fail with parameter validation error
        assert returncode == 1
        assert "error" in stdout.lower() or "failed" in stdout.lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_multiple_tools_sequence(self, everything_url, client_token, wait_for_services):
        """Test running multiple tools in sequence."""
        print("\n=== Testing Multiple Tools in Sequence ===")
        
        # Tool 1: Echo
        returncode, stdout, stderr = self.run_client_command(
            url=everything_url,
            token=client_token,
            command='echo "Starting sequence test"'
        )
        assert returncode == 0
        print("✓ Echo completed")
        
        # Tool 2: Add
        returncode, stdout, stderr = self.run_client_command(
            url=everything_url,
            token=client_token,
            command='add {"a": 100, "b": 200}'
        )
        assert returncode == 0
        assert "300" in stdout
        print("✓ Add completed")
        
        # Tool 3: Get resource
        returncode, stdout, stderr = self.run_client_command(
            url=everything_url,
            token=client_token,
            command='getResourceReference {"resourceId": 1}'
        )
        assert returncode == 0
        print("✓ GetResourceReference completed")
        
        print("\n✅ All tools executed successfully in sequence!")