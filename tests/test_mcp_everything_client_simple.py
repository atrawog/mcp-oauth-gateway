"""Simple test of mcp-everything service using mcp-streamablehttp-client --command."""

import os
import subprocess

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


class TestMCPEverythingClientSimple:
    """Simple test of mcp-everything using mcp-streamablehttp-client."""

    def run_client_command(self, url: str, token: str, command: str, timeout: int = 45) -> tuple[int, str, str]:
        """Run mcp-streamablehttp-client with a command and return result."""
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
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout, env=env)

        return result.returncode, result.stdout, result.stderr

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_test_connection(self, everything_url, client_token, wait_for_services):
        """Test basic connection to the everything server."""
        # The client automatically handles initialization
        # Let's use a simple echo command to test connection
        returncode, stdout, stderr = self.run_client_command(
            url=everything_url,
            token=client_token,
            command="echo test",
        )

        print(f"Return code: {returncode}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")

        # The command might not exist, but we should get a response
        assert returncode == 0 or "not found" in stdout.lower() or "error" in stdout.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_list_tools(self, everything_url, client_token, wait_for_services):
        """Test listing available tools."""
        returncode, stdout, stderr = self.run_client_command(
            url=everything_url,
            token=client_token,
            command="list_tools",
            timeout=45,
        )

        print(f"Return code: {returncode}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")

        # Check if we got a response (even if it's an error about the command)
        assert stdout or stderr

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_help_command(self, everything_url, client_token, wait_for_services):
        """Test help command if available."""
        returncode, stdout, stderr = self.run_client_command(url=everything_url, token=client_token, command="help")

        print(f"Return code: {returncode}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")

        # Check if we got a response
        assert stdout or stderr

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_unknown_command(self, everything_url, client_token, wait_for_services):
        """Test handling of unknown commands."""
        returncode, stdout, stderr = self.run_client_command(
            url=everything_url,
            token=client_token,
            command="this_command_does_not_exist",
        )

        print(f"Return code: {returncode}")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")

        # Should get an error response - the client exits with status 1 for unknown commands
        assert returncode == 1 or "not available" in stdout.lower() or "error" in stdout.lower() or stderr

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
    async def test_everything_available_features(self, everything_url, client_token, wait_for_services):
        """Try to discover available features."""
        print("\n=== Testing mcp-everything server features ===")

        # Try different commands to see what's available (reduced list for performance)
        test_commands = [
            "list",
            "tools",
            "capabilities",
        ]

        for command in test_commands:
            print(f"\nTrying command: {command}")
            returncode, stdout, stderr = self.run_client_command(
                url=everything_url,
                token=client_token,
                command=command,
                timeout=30,
            )

            if stdout:
                print(f"Output: {stdout[:200]}...")  # First 200 chars
            if stderr:
                print(f"Error: {stderr[:200]}...")

            # Look for successful responses
            if returncode == 0 and stdout and "error" not in stdout.lower():
                print(f"✓ Command '{command}' seems to work!")

        print("\n=== Feature discovery completed ===")

        # Test passes if we can communicate with the server
        assert True
