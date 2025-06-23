#!/usr/bin/env python3
"""Fix all hardcoded protocol versions in healthchecks to use ${MCP_PROTOCOL_VERSION}."""

import re
from pathlib import Path


def fix_healthcheck_protocol_version(service_dir):
    """Fix protocol version in healthcheck for a service."""
    compose_path = service_dir / "docker-compose.yml"

    if not compose_path.exists():
        return False

    print(f"Processing {compose_path}...")

    with open(compose_path) as f:
        lines = f.readlines()

    modified = False
    for i, line in enumerate(lines):
        # Look for healthcheck test lines with hardcoded protocol version
        if "test:" in line and "protocolVersion" in line:
            # Replace hardcoded version in the request JSON with ${MCP_PROTOCOL_VERSION}
            # Match pattern: \"protocolVersion\":\"2025-06-18\" (or any date)
            original_line = line
            line = re.sub(
                r"\\\"protocolVersion\\\":\\\"(\d{4}-\d{2}-\d{2})\\\"",
                r'\\"protocolVersion\\":\\"${MCP_PROTOCOL_VERSION}\\"',
                line,
                count=1,  # Only replace the first occurrence (the request)
            )

            if line != original_line:
                lines[i] = line
                modified = True
                print("  Fixed hardcoded protocol version in healthcheck")

    if modified:
        with open(compose_path, "w") as f:
            f.writelines(lines)
        return True

    return False


def main():
    # Find all MCP service directories
    base_dir = Path("/home/atrawog/AI/atrawog/mcp-oauth-gateway")
    service_dirs = [
        d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("mcp-")
    ]

    fixed_count = 0
    for service_dir in sorted(service_dirs):
        if fix_healthcheck_protocol_version(service_dir):
            fixed_count += 1

    print(
        f"\nFixed {fixed_count} services with hardcoded protocol versions in healthchecks"
    )


if __name__ == "__main__":
    main()
