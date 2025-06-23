"""Test available tools in mcp-everything server."""

import os
import subprocess

import pytest

from tests.test_constants import MCP_CLIENT_ACCESS_TOKEN
from tests.test_constants import MCP_EVERYTHING_TESTS_ENABLED
from tests.test_constants import MCP_EVERYTHING_URLS


@pytest.mark.skipif(not MCP_EVERYTHING_TESTS_ENABLED, reason="MCP Everything tests disabled")
def test_echo_tool():
    """Test the echo tool directly."""
    if not MCP_EVERYTHING_URLS:
        pytest.skip("MCP_EVERYTHING_URLS environment variable not set")
    url = MCP_EVERYTHING_URLS[0]

    env = os.environ.copy()
    env["MCP_SERVER_URL"] = url
    env["MCP_CLIENT_ACCESS_TOKEN"] = MCP_CLIENT_ACCESS_TOKEN

    # Test echo command
    cmd = [
        "pixi", "run", "mcp-streamablehttp-client",
        "--server-url", url,
        "--command", "echo Hello from mcp-everything test!"
    ]

    result = subprocess.run(
        cmd,
        check=False, capture_output=True,
        text=True,
        env=env,
        timeout=30
    )

    print(f"Return code: {result.returncode}")
    print(f"Output:\n{result.stdout}")
    if result.stderr:
        print(f"Stderr:\n{result.stderr}")

    # Check for success
    assert result.returncode == 0 or "Echo: Hello from mcp-everything test!" in result.stdout


if __name__ == "__main__":
    test_echo_tool()
