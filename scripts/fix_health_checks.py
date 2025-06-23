#!/usr/bin/env python3
"""Fix MCP service health checks to accept any supported protocol version."""

import re
from pathlib import Path


def fix_health_check(compose_file):
    """Update health check to accept any protocol version in response."""
    with open(compose_file) as f:
        content = f.read()

    # Find the healthcheck section
    if "healthcheck:" not in content:
        print(f"No healthcheck in {compose_file}")
        return False

    # Updated health check that accepts any protocol version
    new_healthcheck = """healthcheck:
      test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \\
        -H 'Content-Type: application/json' \\
        -H 'Accept: application/json, text/event-stream' \\
        -d '{\\"jsonrpc\\":\\"2.0\\",\\"method\\":\\"initialize\\",\\"params\\":{\\"protocolVersion\\":\\"${MCP_PROTOCOL_VERSION:-2025-06-18}\\",\\"capabilities\\":{},\\"clientInfo\\":{\\"name\\":\\"healthcheck\\",\\"version\\":\\"1.0\\"}},\\"id\\":1}' \\
        | grep -q '\\"protocolVersion\\":'"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 40s"""

    # Replace the healthcheck section
    pattern = r"healthcheck:.*?(?=\n\w|\nnetworks:|\Z)"
    content = re.sub(pattern, new_healthcheck, content, flags=re.DOTALL)

    with open(compose_file, "w") as f:
        f.write(content)

    print(f"Updated {compose_file}")
    return True


def main():
    """Fix all MCP service health checks."""
    base_dir = Path("/home/atrawog/AI/atrawog/mcp-oauth-gateway")

    # Find all MCP service docker-compose files
    mcp_services = [
        "mcp-fetch",
        "mcp-fetchs",
        "mcp-filesystem",
        "mcp-memory",
        "mcp-playwright",
        "mcp-sequentialthinking",
        "mcp-time",
        "mcp-tmux",
        "mcp-everything",
    ]

    updated = 0
    for service in mcp_services:
        compose_file = base_dir / service / "docker-compose.yml"
        if compose_file.exists() and fix_health_check(compose_file):
            updated += 1

    print(f"\nUpdated {updated} docker-compose files")
    print("\nRun 'just rebuild-all' to apply the changes")


if __name__ == "__main__":
    main()
