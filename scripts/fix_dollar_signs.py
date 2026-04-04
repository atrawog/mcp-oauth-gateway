#!/usr/bin/env python3
"""Fix double dollar signs in healthchecks."""

from pathlib import Path


# Services to fix
SERVICES = [
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


def fix_dollar_signs(service_name):
    """Fix double dollar signs in healthcheck."""
    compose_file = Path(
        f"/home/atrawog/AI/atrawog/mcp-oauth-gateway/{service_name}/docker-compose.yml"
    )

    if not compose_file.exists():
        print(f"❌ {compose_file} not found")
        return False

    with open(compose_file) as f:
        content = f.read()

    # Replace double dollar signs with single
    content = content.replace("$${MCP_PROTOCOL_VERSION}", "${MCP_PROTOCOL_VERSION}")

    with open(compose_file, "w") as f:
        f.write(content)

    print(f"✅ Fixed {service_name}")
    return True


def main():
    """Fix all services."""
    print("Fixing double dollar signs...\n")

    for service in SERVICES:
        fix_dollar_signs(service)

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
