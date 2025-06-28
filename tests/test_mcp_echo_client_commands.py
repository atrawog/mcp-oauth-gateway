"""Test mcp-echo service using mcp-streamablehttp-client command interface.

This test file follows CLAUDE.md Sacred Commandments:
- NO MOCKING - Tests against real deployed mcp-echo service
- Uses MCP_ECHO_STATELESS_URLS configuration from test_constants
- Tests using --command and --list-tools interfaces
- Complements test_mcp_echo_client_full.py with command-line testing
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from tests.test_constants import AUTH_BASE_URL
from tests.test_constants import MCP_ECHO_STATELESS_TESTS_ENABLED
from tests.test_constants import MCP_ECHO_STATELESS_URLS


# MCP Client tokens from environment - NO .env loading in tests!
# All configuration must come from environment variables
MCP_CLIENT_ACCESS_TOKEN = os.environ.get("MCP_CLIENT_ACCESS_TOKEN")
MCP_CLIENT_ID = os.environ.get("MCP_CLIENT_ID")
MCP_CLIENT_SECRET = os.environ.get("MCP_CLIENT_SECRET")


@pytest.fixture
def temp_env_file(tmp_path):
    """Create a temporary .env file for mcp-streamablehttp-client."""
    if not MCP_ECHO_STATELESS_URLS:
        pytest.skip("MCP_ECHO_STATELESS_URLS environment variable not set")

    echo_url = MCP_ECHO_STATELESS_URLS[0]

    env_content = f"""
# MCP Server Configuration
MCP_SERVER_URL={echo_url}

# OAuth Configuration
OAUTH_AUTHORIZATION_URL={AUTH_BASE_URL}/authorize
OAUTH_TOKEN_URL={AUTH_BASE_URL}/token
OAUTH_DEVICE_AUTH_URL={AUTH_BASE_URL}/device/code
OAUTH_REGISTRATION_URL={AUTH_BASE_URL}/register

# Discovery URL (optional but recommended)
OAUTH_DISCOVERY_URL={echo_url.replace("/mcp", "")}/.well-known/oauth-authorization-server

# Logging
LOG_LEVEL=INFO
"""
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    return str(env_file)


@pytest.fixture
def mcp_client_env():
    """Setup MCP_CLIENT environment variables from test environment."""
    if not all([MCP_CLIENT_ACCESS_TOKEN, MCP_CLIENT_ID, MCP_CLIENT_SECRET]):
        pytest.fail("Missing MCP_CLIENT credentials in environment - run: just mcp-client-token")

    print("Using MCP_CLIENT tokens from environment:")
    print(f"  Client ID: {MCP_CLIENT_ID}")
    print(f"  Access Token: {MCP_CLIENT_ACCESS_TOKEN[:20]}...")

    # Return env vars to add to subprocess
    return {
        "MCP_CLIENT_ACCESS_TOKEN": MCP_CLIENT_ACCESS_TOKEN,
        "MCP_CLIENT_ID": MCP_CLIENT_ID,
        "MCP_CLIENT_SECRET": MCP_CLIENT_SECRET,
    }


class TestMCPEchoClientCommands:
    """Test mcp-echo service using mcp-streamablehttp-client command interface."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_ECHO_STATELESS_TESTS_ENABLED, reason="MCP Echo stateless tests disabled")
    async def test_echo_list_tools_command(self, temp_env_file, mcp_client_env, _wait_for_services):
        """Test listing tools using --list-tools command."""
        # Set up environment with MCP_CLIENT_* variables
        env = os.environ.copy()
        env.update(mcp_client_env)

        # Run the list-tools command
        cmd = [
            "pixi",
            "run",
            "mcp-streamablehttp-client",
            "--env-file",
            temp_env_file,
            "--list-tools",
        ]

        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )  # Reduced from 30s

        # Check command executed successfully
        assert result.returncode == 0, f"Command failed with: {result.stderr}"

        # The output should contain tool information
        output = result.stdout

        # Check for expected tools
        assert "echo" in output, f"'echo' tool not found in output: {output}"
        assert "printHeader" in output, f"'printHeader' tool not found in output: {output}"

        # Check for tool descriptions
        assert "Echo back the provided message" in output
        assert "Print all HTTP headers" in output

        print("✅ Successfully listed mcp-echo tools")
        print("   Found 'echo' and 'printHeader' tools with descriptions")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_ECHO_STATELESS_TESTS_ENABLED, reason="MCP Echo stateless tests disabled")
    async def test_echo_tool_command_simple(self, temp_env_file, mcp_client_env, _wait_for_services):
        """Test echo tool using --command interface with simple message."""
        # Set up environment with MCP_CLIENT_* variables
        env = os.environ.copy()
        env.update(mcp_client_env)

        test_message = "Hello from mcp-echo command test!"

        # Run the echo command
        cmd = [
            "pixi",
            "run",
            "mcp-streamablehttp-client",
            "--env-file",
            temp_env_file,
            "--command",
            f"echo {test_message}",
        ]

        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )  # Reduced from 30s

        # Check command executed successfully
        assert result.returncode == 0, f"Command failed with: {result.stderr}"

        # The output should contain the echoed message
        output = result.stdout
        assert test_message in output, f"'{test_message}' not found in output: {output[:500]}..."

        print("✅ Successfully echoed message via command interface")
        print(f"   Message: {test_message}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_ECHO_STATELESS_TESTS_ENABLED, reason="MCP Echo stateless tests disabled")
    async def test_echo_tool_command_json_args(self, temp_env_file, mcp_client_env, _wait_for_services):
        """Test echo tool using --command interface with JSON arguments."""
        # Set up environment with MCP_CLIENT_* variables
        env = os.environ.copy()
        env.update(mcp_client_env)

        test_message = "JSON args test with special chars: !@#$%^&()"

        # Run the echo command with JSON arguments
        cmd = [
            "pixi",
            "run",
            "mcp-streamablehttp-client",
            "--env-file",
            temp_env_file,
            "--command",
            f'echo {{"message": "{test_message}"}}',
        ]

        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )  # Reduced from 30s

        # Check command executed successfully
        assert result.returncode == 0, f"Command failed with: {result.stderr}"

        # The output should contain the echoed message
        output = result.stdout
        assert test_message in output, f"'{test_message}' not found in output: {output[:500]}..."

        print("✅ Successfully echoed message via JSON command interface")
        print(f"   Message: {test_message}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_ECHO_STATELESS_TESTS_ENABLED, reason="MCP Echo stateless tests disabled")
    async def test_echo_tool_command_multiline(self, temp_env_file, mcp_client_env, _wait_for_services):
        """Test echo tool with multiline message via command interface."""
        # Set up environment with MCP_CLIENT_* variables
        env = os.environ.copy()
        env.update(mcp_client_env)

        test_message = "Line 1\\nLine 2\\nLine 3 with special chars: 🚀"

        # Run the echo command
        cmd = [
            "pixi",
            "run",
            "mcp-streamablehttp-client",
            "--env-file",
            temp_env_file,
            "--command",
            f'echo {{"message": "{test_message}"}}',
        ]

        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )  # Reduced from 30s

        # Check command executed successfully
        assert result.returncode == 0, f"Command failed with: {result.stderr}"

        # The output should contain the echoed message (with actual newlines)
        output = result.stdout
        # The test_message contains literal \n, so we check for the actual lines
        assert "Line 1" in output and "Line 2" in output and "Line 3" in output

        print("✅ Successfully echoed multiline message via command interface")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_ECHO_STATELESS_TESTS_ENABLED, reason="MCP Echo stateless tests disabled")
    async def test_print_header_tool_command(self, temp_env_file, mcp_client_env, _wait_for_services):
        """Test printHeader tool using --command interface."""
        # Set up environment with MCP_CLIENT_* variables
        env = os.environ.copy()
        env.update(mcp_client_env)

        # Run the printHeader command
        cmd = [
            "pixi",
            "run",
            "mcp-streamablehttp-client",
            "--env-file",
            temp_env_file,
            "--command",
            "printHeader",
        ]

        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )  # Reduced from 30s

        # Check command executed successfully
        assert result.returncode == 0, f"Command failed with: {result.stderr}"

        # The output should contain HTTP headers
        output = result.stdout
        assert "HTTP Headers:" in output, f"'HTTP Headers:' not found in output: {output}"

        # Should show some expected headers
        assert "authorization:" in output.lower() or "bearer" in output.lower()
        # The printHeader tool returns specific headers (Traefik forwarded and auth headers)
        # It doesn't return all request headers like accept, content-type, etc.
        assert any(header in output.lower() for header in ["x-forwarded-", "x-real-ip", "authorization"])

        print("✅ Successfully executed printHeader via command interface")
        print("   Found HTTP headers including auth information")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_ECHO_STATELESS_TESTS_ENABLED, reason="MCP Echo stateless tests disabled")
    async def test_command_with_invalid_token(self, temp_env_file, _wait_for_services):
        """Test that command fails properly with invalid token."""
        env = os.environ.copy()
        # CRITICAL: Clear ALL MCP_CLIENT_* variables that the client reads from environment
        env.pop("MCP_CLIENT_ACCESS_TOKEN", None)
        env.pop("MCP_CLIENT_REFRESH_TOKEN", None)
        env.pop("MCP_CLIENT_ID", None)
        env.pop("MCP_CLIENT_SECRET", None)

        # Now set our invalid credentials
        env["MCP_CLIENT_ACCESS_TOKEN"] = "invalid_token_12345"
        env["MCP_CLIENT_ID"] = "invalid_client"
        env["MCP_CLIENT_SECRET"] = "invalid_secret"

        # Run the command
        cmd = [
            "pixi",
            "run",
            "mcp-streamablehttp-client",
            "--env-file",
            temp_env_file,
            "--command",
            "echo test message",
        ]

        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )  # Reduced from 30s

        # Command should fail due to invalid token
        assert result.returncode != 0, "Command should have failed with invalid token"

        # Check for authentication error indicators
        error_output = result.stderr + result.stdout
        assert any(
            indicator in error_output.lower() for indicator in ["401", "unauthorized", "invalid", "token", "auth"]
        ), f"Expected auth error not found in: {error_output}"

        print("✅ Command properly failed with invalid token")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_ECHO_STATELESS_TESTS_ENABLED, reason="MCP Echo stateless tests disabled")
    async def test_invalid_tool_command(self, temp_env_file, mcp_client_env, _wait_for_services):
        """Test that invalid tool commands fail properly."""
        # Set up environment with MCP_CLIENT_* variables
        env = os.environ.copy()
        env.update(mcp_client_env)

        # Run command with invalid tool name
        cmd = [
            "pixi",
            "run",
            "mcp-streamablehttp-client",
            "--env-file",
            temp_env_file,
            "--command",
            "invalid_tool_name test arguments",
        ]

        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )  # Reduced from 30s

        # Command should fail due to invalid tool name
        assert result.returncode != 0, "Command should have failed with invalid tool name"

        # Check for tool error indicators
        error_output = result.stderr + result.stdout
        assert any(
            indicator in error_output.lower() for indicator in ["unknown tool", "invalid", "not found", "error"]
        ), f"Expected tool error not found in: {error_output}"

        print("✅ Command properly failed with invalid tool name")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_ECHO_STATELESS_TESTS_ENABLED, reason="MCP Echo stateless tests disabled")
    async def test_echo_stress_test_commands(self, temp_env_file, mcp_client_env, _wait_for_services):
        """Stress test echo tool with multiple rapid commands."""
        # Set up environment with MCP_CLIENT_* variables
        env = os.environ.copy()
        env.update(mcp_client_env)

        # Run multiple echo commands rapidly
        for i in range(5):
            test_message = f"Stress test message {i + 1}/5"

            cmd = [
                "pixi",
                "run",
                "mcp-streamablehttp-client",
                "--env-file",
                temp_env_file,
                "--command",
                f"echo {test_message}",
            ]

            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                env=env,
                timeout=10,
            )  # Reduced from 30s

            assert result.returncode == 0, f"Stress test {i + 1} failed: {result.stderr}"
            assert test_message in result.stdout
            print(f"✅ Stress test {i + 1}/5 completed")

        print("✅ mcp-echo service handles rapid command requests properly")

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(not MCP_ECHO_STATELESS_TESTS_ENABLED, reason="MCP Echo stateless tests disabled")
    async def test_echo_multiple_urls(self, mcp_client_env, _wait_for_services):
        """Test echo command on multiple configured URLs."""
        if not MCP_ECHO_STATELESS_URLS:
            pytest.skip("MCP_ECHO_STATELESS_URLS environment variable not set")

        # Test up to 5 URLs to avoid excessive testing time
        urls_to_test = MCP_ECHO_STATELESS_URLS[:5]

        env = os.environ.copy()
        env.update(mcp_client_env)

        results = []
        for url in urls_to_test:
            # Create temp env file for this URL
            with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
                f.write(f"""
# MCP Server Configuration
MCP_SERVER_URL={url}

# OAuth Configuration
OAUTH_AUTHORIZATION_URL={AUTH_BASE_URL}/authorize
OAUTH_TOKEN_URL={AUTH_BASE_URL}/token
OAUTH_DEVICE_AUTH_URL={AUTH_BASE_URL}/device/code
OAUTH_REGISTRATION_URL={AUTH_BASE_URL}/register

# Discovery URL
OAUTH_DISCOVERY_URL={url.replace("/mcp", "")}/.well-known/oauth-authorization-server

# Logging
LOG_LEVEL=INFO
""")
                temp_env_path = f.name

            try:
                # Test echo command on this URL
                test_message = f"Testing {url.split('//')[1].split('/')[0]}"
                cmd = [
                    "pixi",
                    "run",
                    "mcp-streamablehttp-client",
                    "--env-file",
                    temp_env_path,
                    "--command",
                    f'echo {{"message": "{test_message}"}}',
                ]

                result = subprocess.run(
                    cmd,
                    check=False,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=10,
                )  # Reduced from 30s

                if result.returncode == 0 and test_message in result.stdout:
                    results.append((url, "✅ Success"))
                else:
                    results.append((url, f"❌ Failed: {result.stderr[:100]}"))
            finally:
                # Clean up temp file
                Path(temp_env_path).unlink(missing_ok=True)

        # Print results
        print(f"\n{'=' * 60}")
        print("Multiple URL Test Results:")
        print(f"{'=' * 60}")
        for url, status in results:
            hostname = url.split("//")[1].split("/")[0]
            print(f"{hostname}: {status}")
        print(f"{'=' * 60}")

        # All tested URLs should succeed
        failed = [url for url, status in results if "❌" in status]
        assert not failed, f"Failed URLs: {failed}"
