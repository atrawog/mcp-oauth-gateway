#!/usr/bin/env python3
"""Generate docker-compose includes based on enabled services."""

import os
from pathlib import Path

import yaml


def main():
    """Generate docker-compose.includes.yml based on enabled services."""
    # Base includes that are always present
    includes = [
        "traefik/docker-compose.yml",
        "auth/docker-compose.yml",
    ]

    # Conditionally add mcp-fetch
    if os.getenv("MCP_FETCH_ENABLED", "false").lower() == "true":
        includes.append("mcp-fetch/docker-compose.yml")

    # Conditionally add mcp-fetchs
    if os.getenv("MCP_FETCHS_ENABLED", "false").lower() == "true":
        includes.append("mcp-fetchs/docker-compose.yml")

    # Conditionally add mcp-filesystem
    if os.getenv("MCP_FILESYSTEM_ENABLED", "false").lower() == "true":
        includes.append("mcp-filesystem/docker-compose.yml")

    # Conditionally add mcp-memory
    if os.getenv("MCP_MEMORY_ENABLED", "false").lower() == "true":
        includes.append("mcp-memory/docker-compose.yml")

    # Conditionally add mcp-playwright
    if os.getenv("MCP_PLAYWRIGHT_ENABLED", "false").lower() == "true":
        includes.append("mcp-playwright/docker-compose.yml")

    # Conditionally add mcp-sequentialthinking
    if os.getenv("MCP_SEQUENTIALTHINKING_ENABLED", "false").lower() == "true":
        includes.append("mcp-sequentialthinking/docker-compose.yml")

    # Conditionally add mcp-time
    if os.getenv("MCP_TIME_ENABLED", "false").lower() == "true":
        includes.append("mcp-time/docker-compose.yml")

    # Conditionally add mcp-tmux
    if os.getenv("MCP_TMUX_ENABLED", "false").lower() == "true":
        includes.append("mcp-tmux/docker-compose.yml")

    # Conditionally add mcp-echo
    if os.getenv("MCP_ECHO_ENABLED", "false").lower() == "true":
        includes.append("mcp-echo/docker-compose.yml")

    # Conditionally add mcp-everything
    if os.getenv("MCP_EVERYTHING_ENABLED", "false").lower() == "true":
        includes.append("mcp-everything/docker-compose.yml")

    # Generate the includes file
    compose_data = {
        "include": includes,
        "networks": {"public": {"external": True}},
        "volumes": {
            "traefik-certificates": {"external": True},
            "redis-data": {"external": True},
            "coverage-data": {"external": True},
            "auth-keys": {"external": True},
            "mcp-memory-data": {"external": True},
        },
    }

    # Write the generated file
    output_path = Path(__file__).parent.parent / "docker-compose.includes.yml"
    with open(output_path, "w") as f:
        yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)

    print(f"Generated {output_path}")
    if os.getenv("MCP_FETCH_ENABLED", "false").lower() == "true":
        print("✅ mcp-fetch is ENABLED")
    else:
        print("❌ mcp-fetch is DISABLED")

    if os.getenv("MCP_FETCHS_ENABLED", "false").lower() == "true":
        print("✅ mcp-fetchs is ENABLED")
    else:
        print("❌ mcp-fetchs is DISABLED")

    if os.getenv("MCP_FILESYSTEM_ENABLED", "false").lower() == "true":
        print("✅ mcp-filesystem is ENABLED")
    else:
        print("❌ mcp-filesystem is DISABLED")

    if os.getenv("MCP_MEMORY_ENABLED", "false").lower() == "true":
        print("✅ mcp-memory is ENABLED")
    else:
        print("❌ mcp-memory is DISABLED")

    if os.getenv("MCP_PLAYWRIGHT_ENABLED", "false").lower() == "true":
        print("✅ mcp-playwright is ENABLED")
    else:
        print("❌ mcp-playwright is DISABLED")

    if os.getenv("MCP_SEQUENTIALTHINKING_ENABLED", "false").lower() == "true":
        print("✅ mcp-sequentialthinking is ENABLED")
    else:
        print("❌ mcp-sequentialthinking is DISABLED")

    if os.getenv("MCP_TIME_ENABLED", "false").lower() == "true":
        print("✅ mcp-time is ENABLED")
    else:
        print("❌ mcp-time is DISABLED")

    if os.getenv("MCP_TMUX_ENABLED", "false").lower() == "true":
        print("✅ mcp-tmux is ENABLED")
    else:
        print("❌ mcp-tmux is DISABLED")

    if os.getenv("MCP_ECHO_ENABLED", "false").lower() == "true":
        print("✅ mcp-echo is ENABLED")
    else:
        print("❌ mcp-echo is DISABLED")

    if os.getenv("MCP_EVERYTHING_ENABLED", "false").lower() == "true":
        print("✅ mcp-everything is ENABLED")
    else:
        print("❌ mcp-everything is DISABLED")


if __name__ == "__main__":
    main()
