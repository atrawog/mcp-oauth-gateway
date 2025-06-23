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
        content = f.read()

    # Find healthcheck test pattern with hardcoded protocol version in the request
    # Match patterns like: \"protocolVersion\":\"2025-06-18\" in the request JSON
    pattern = r"(healthcheck:.*?test:.*?\"protocolVersion\":\")(\d{4}-\d{2}-\d{2})(\".*?)(\n\s+interval:)"

    def replace_hardcoded_version(match):
        # Replace hardcoded version with ${MCP_PROTOCOL_VERSION}
        return (
            match.group(1) + "${MCP_PROTOCOL_VERSION}" + match.group(3) + match.group(4)
        )

    # Apply the fix
    fixed_content = re.sub(pattern, replace_hardcoded_version, content, flags=re.DOTALL)

    if fixed_content != content:
        print(f"  Fixed hardcoded protocol version in {compose_path}")
        with open(compose_path, "w") as f:
            f.write(fixed_content)
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
