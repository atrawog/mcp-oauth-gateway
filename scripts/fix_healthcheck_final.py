#!/usr/bin/env python3
"""Final fix for healthcheck commands to properly use runtime environment variables."""

import re
from pathlib import Path


def fix_healthcheck_final(service_dir):
    """Fix healthcheck to use runtime environment variables properly."""
    compose_path = service_dir / "docker-compose.yml"

    if not compose_path.exists():
        return False

    print(f"Processing {compose_path}...")

    with open(compose_path) as f:
        content = f.read()

    # Find healthcheck test lines
    original_content = content

    # Replace $MCP_PROTOCOL_VERSION with \$MCP_PROTOCOL_VERSION to prevent compose-time substitution
    # This ensures the variable is evaluated at runtime inside the container
    content = re.sub(
        r"\"protocolVersion\":\"\$MCP_PROTOCOL_VERSION\"",
        r'\\"protocolVersion\\":\\"\\$MCP_PROTOCOL_VERSION\\"',
        content,
    )

    # For the grep part, we need to be more careful with escaping
    # Replace the grep pattern to use proper escaping
    content = re.sub(
        r"grep -q '\"protocolVersion\":\"'\"\$MCP_PROTOCOL_VERSION\"'\"'",
        r'grep -q \\"protocolVersion\\":\\"\\$MCP_PROTOCOL_VERSION\\"',
        content,
    )

    # Alternative pattern that might exist
    content = re.sub(
        r"grep -q \'\"protocolVersion\":\"\$MCP_PROTOCOL_VERSION\"\'",
        r'grep -q \\"protocolVersion\\":\\"\\$MCP_PROTOCOL_VERSION\\"',
        content,
    )

    if content != original_content:
        print("  Fixed runtime environment variable usage")
        with open(compose_path, "w") as f:
            f.write(content)
        return True

    return False


def main():
    # Find all MCP service directories
    base_dir = Path("/home/atrawog/AI/atrawog/mcp-oauth-gateway")
    service_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("mcp-")]

    fixed_count = 0
    for service_dir in sorted(service_dirs):
        if fix_healthcheck_final(service_dir):
            fixed_count += 1

    print(f"\nFixed {fixed_count} services for runtime environment variable usage")


if __name__ == "__main__":
    main()
