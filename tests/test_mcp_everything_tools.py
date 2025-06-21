"""Test available tools in mcp-everything server."""

import subprocess
import os
import sys

from tests.test_constants import BASE_DOMAIN, MCP_CLIENT_ACCESS_TOKEN


def test_echo_tool():
    """Test the echo tool directly."""
    url = f"https://mcp-everything.{BASE_DOMAIN}/mcp"
    
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
        capture_output=True,
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