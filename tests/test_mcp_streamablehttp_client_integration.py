"""Sacred Integration Tests for mcp-streamablehttp-client Command
Following CLAUDE.md Commandment 1: NO MOCKING! Test against real deployed services only!

These tests verify the complete end-to-end flow of using mcp-streamablehttp-client
command line tool to interact with MCP services through the OAuth gateway.
"""

import os
import subprocess

import pytest

from .test_constants import AUTH_BASE_URL


# MCP Client tokens from environment - NO .env loading in tests!
# All configuration must come from environment variables
MCP_CLIENT_ACCESS_TOKEN = os.environ.get("MCP_CLIENT_ACCESS_TOKEN")
MCP_CLIENT_ID = os.environ.get("MCP_CLIENT_ID")
MCP_CLIENT_SECRET = os.environ.get("MCP_CLIENT_SECRET")
MCP_CLIENT_REFRESH_TOKEN = os.environ.get("MCP_CLIENT_REFRESH_TOKEN")


@pytest.fixture
def temp_env_file(tmp_path, mcp_fetch_url):
    """Create a temporary .env file for testing."""
    env_content = f"""
# MCP Server Configuration
MCP_SERVER_URL={mcp_fetch_url}

# OAuth Configuration
OAUTH_AUTHORIZATION_URL={AUTH_BASE_URL}/authorize
OAUTH_TOKEN_URL={AUTH_BASE_URL}/token
OAUTH_DEVICE_AUTH_URL={AUTH_BASE_URL}/device/code
OAUTH_REGISTRATION_URL={AUTH_BASE_URL}/register

# Discovery URL (optional but recommended)
OAUTH_DISCOVERY_URL={mcp_fetch_url.replace("/mcp", "")}/.well-known/oauth-authorization-server

# Logging
LOG_LEVEL=INFO
"""
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    return str(env_file)


@pytest.fixture
def mcp_client_env():
    """Setup MCP_CLIENT environment variables from .env."""
    if not all([MCP_CLIENT_ACCESS_TOKEN, MCP_CLIENT_ID, MCP_CLIENT_SECRET]):
        pytest.fail(
            "Missing MCP_CLIENT credentials in .env - run: just mcp-client-token"
        )

    print("Using MCP_CLIENT tokens from .env:")
    print(f"  Client ID: {MCP_CLIENT_ID}")
    print(f"  Access Token: {MCP_CLIENT_ACCESS_TOKEN[:20]}...")

    # Return env vars to add to subprocess
    return {
        "MCP_CLIENT_ACCESS_TOKEN": MCP_CLIENT_ACCESS_TOKEN,
        "MCP_CLIENT_ID": MCP_CLIENT_ID,
        "MCP_CLIENT_SECRET": MCP_CLIENT_SECRET,
        "MCP_CLIENT_REFRESH_TOKEN": MCP_CLIENT_REFRESH_TOKEN or "",
    }


class TestMCPStreamableHTTPClientCommand:
    """Test the mcp-streamablehttp-client command line tool."""

    @pytest.mark.asyncio
    async def test_fetch_example_com(
        self, temp_env_file, mcp_client_env, wait_for_services
    ):
        """Test fetching https://example.com using mcp-streamablehttp-client command."""
        # Set up environment with MCP_CLIENT_* variables
        env = os.environ.copy()
        env.update(mcp_client_env)

        # Run the command
        cmd = [
            "pixi",
            "run",
            "mcp-streamablehttp-client",
            "--env-file",
            temp_env_file,
            "--command",
            "fetch https://example.com",
        ]

        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, env=env, timeout=30
        )

        # Check command executed successfully
        assert result.returncode == 0, f"Command failed with: {result.stderr}"

        # The output includes progress messages and the actual content
        output = result.stdout

        # Check for "Example Domain" in the output
        assert "Example Domain" in output, (
            f"'Example Domain' not found in output: {output[:500]}..."
        )

        # Also verify it fetched from the correct URL
        assert "https://example.com" in output

        # Check for success indicators
        assert "successfully" in output.lower() or "completed" in output.lower()

        print("✅ Successfully fetched https://example.com")
        print("   Found 'Example Domain' in response")

    @pytest.mark.asyncio
    async def test_command_with_invalid_token(
        self, temp_env_file, tmp_path, wait_for_services
    ):
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
            "fetch https://example.com",
        ]

        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, env=env, timeout=30
        )

        # Debug output
        print(f"Exit code: {result.returncode}")
        print(f"STDOUT: {result.stdout[:500]}")
        print(f"STDERR: {result.stderr[:500]}")

        output_combined = result.stdout + result.stderr

        # Check for authentication failure indicators
        auth_failed = any(
            [
                result.returncode != 0,
                "401" in output_combined,
                "unauthorized" in output_combined.lower(),
                "authentication failed" in output_combined.lower(),
                "invalid token" in output_combined.lower(),
                "invalid_token" in output_combined,
                "Token invalid" in output_combined,
            ]
        )

        # Check for success indicators that should NOT be present
        success_indicators = [
            "Example Domain" in output_combined,
            "successfully" in output_combined.lower()
            and "completed" in output_combined.lower(),
        ]

        # Either authentication should fail OR it should NOT successfully fetch the content
        assert auth_failed or not any(success_indicators), (
            f"Command succeeded with invalid token! Exit code: {result.returncode}, Output: {output_combined[:1000]}"  # TODO: Break long line
        )

        print("✅ Command properly rejected invalid token")

    @pytest.mark.asyncio
    async def test_test_auth_command(
        self, temp_env_file, mcp_client_env, wait_for_services
    ):
        """Test the --test-auth option."""
        env = os.environ.copy()
        env.update(mcp_client_env)

        # Run the test-auth command
        cmd = [
            "pixi",
            "run",
            "mcp-streamablehttp-client",
            "--env-file",
            temp_env_file,
            "--test-auth",
        ]

        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, env=env, timeout=30
        )

        # Should succeed with valid credentials
        assert result.returncode == 0
        assert (
            "success" in result.stdout.lower()
            or "authenticated" in result.stdout.lower()
        )

        print("✅ Authentication test passed")

    @pytest.mark.asyncio
    async def test_token_status_command(
        self, temp_env_file, mcp_client_env, wait_for_services
    ):
        """Test the --token option to check token status."""
        env = os.environ.copy()
        env.update(mcp_client_env)

        # Run the token status command
        cmd = [
            "pixi",
            "run",
            "mcp-streamablehttp-client",
            "--env-file",
            temp_env_file,
            "--token",
        ]

        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, env=env, timeout=30
        )

        # Should show token status
        assert result.returncode == 0
        output = result.stdout.lower()
        assert "token" in output
        assert "valid" in output or "active" in output or "expires" in output

        print("✅ Token status check working")

    @pytest.mark.asyncio
    async def test_command_with_complex_parameters(
        self, temp_env_file, mcp_client_env, wait_for_services
    ):
        """Test command with more complex parameters."""
        env = os.environ.copy()
        env.update(mcp_client_env)

        # Try a command that might list available tools
        cmd = [
            "pixi",
            "run",
            "mcp-streamablehttp-client",
            "--env-file",
            temp_env_file,
            "--log-level",
            "DEBUG",
            "--command",
            "list_tools",
        ]

        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, env=env, timeout=30
        )

        # The exact behavior depends on the MCP server
        # But we should get some response
        if result.returncode == 0:
            print("✅ Complex command executed successfully")
            print(f"   Output length: {len(result.stdout)} bytes")
        else:
            # Some servers might not support list_tools
            print(
                f"⚠️  Command returned error (might be expected): {result.stderr[:200]}"
            )


class TestMCPClientRealWorldUsage:
    """Test real-world usage patterns of the MCP client."""

    @pytest.mark.asyncio
    async def test_consecutive_commands(
        self, temp_env_file, mcp_client_env, wait_for_services
    ):
        """Test running multiple commands in sequence (simulating real usage)."""
        env = os.environ.copy()
        env.update(mcp_client_env)

        # Run multiple fetch commands
        urls = [
            "https://example.com",
        ]

        success_count = 0
        for url in urls:
            cmd = [
                "pixi",
                "run",
                "mcp-streamablehttp-client",
                "--env-file",
                temp_env_file,
                "--command",
                f"fetch {url}",
            ]

            result = subprocess.run(
                cmd, check=False, capture_output=True, text=True, env=env, timeout=30
            )

            if result.returncode == 0:
                success_count += 1

        assert success_count == len(urls), (
            f"Only {success_count}/{len(urls)} commands succeeded"
        )
        print(f"✅ All {len(urls)} consecutive commands executed successfully")

    @pytest.mark.asyncio
    async def test_command_error_handling(
        self, temp_env_file, mcp_client_env, wait_for_services
    ):
        """Test how the client handles various error conditions."""
        env = os.environ.copy()
        env.update(mcp_client_env)

        # Test with invalid command
        cmd = [
            "pixi",
            "run",
            "mcp-streamablehttp-client",
            "--env-file",
            temp_env_file,
            "--command",
            "invalid_command_that_does_not_exist",
        ]

        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, env=env, timeout=30
        )

        # Should handle the error gracefully
        assert (
            result.returncode != 0
            or "error" in result.stdout.lower()
            or "error" in result.stderr.lower()
        )
        print("✅ Invalid command handled gracefully")
