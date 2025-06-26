#!/usr/bin/env python3
"""Update MCP service docker-compose files to use correct protocol versions."""

import re
from pathlib import Path


# Actual protocol versions supported by each service
SERVICE_PROTOCOL_VERSIONS = {
    "mcp-fetch": "2025-03-26",
    "mcp-fetchs": "2025-06-18",  # Custom service, supports latest
    "mcp-filesystem": "2025-03-26",
    "mcp-memory": "2024-11-05",
    "mcp-playwright": "2025-06-18",
    "mcp-sequentialthinking": "2024-11-05",
    "mcp-time": "2025-03-26",
    "mcp-tmux": "2025-06-18",
    "mcp-everything": "2025-06-18",
}


def update_docker_compose(service_name, protocol_version):
    """Update docker-compose.yml to use specific protocol version."""
    compose_file = Path(f"/home/atrawog/AI/atrawog/mcp-oauth-gateway/{service_name}/docker-compose.yml")

    if not compose_file.exists():
        print(f"❌ {compose_file} not found")
        return False

    with open(compose_file) as f:
        content = f.read()

    # Update the environment section to use explicit protocol version
    # Look for MCP_PROTOCOL_VERSION environment variable
    pattern = r"(- MCP_PROTOCOL_VERSION=)\${MCP_PROTOCOL_VERSION}"
    replacement = f"\\1{protocol_version}"
    content = re.sub(pattern, replacement, content)

    # Also update the healthcheck to use the specific version
    # First in the request
    pattern = r'(\\"protocolVersion\\":\\\\")(\${MCP_PROTOCOL_VERSION:-2025-06-18})(\\\\\")'
    replacement = f"\\1{protocol_version}\\3"
    content = re.sub(pattern, replacement, content)

    # Then in the grep check
    pattern = r'(grep -q \\\\"\\\\"protocolVersion\\\\":\\\\")(\${MCP_PROTOCOL_VERSION:-2025-06-18})(\\\\"\\")'
    replacement = f"\\1{protocol_version}\\3"
    content = re.sub(pattern, replacement, content)

    with open(compose_file, "w") as f:
        f.write(content)

    print(f"✅ Updated {service_name} to use protocol version {protocol_version}")
    return True


def main():
    """Update all MCP services with correct protocol versions."""
    print("Updating MCP services with correct protocol versions...\n")

    updated = 0
    for service, version in SERVICE_PROTOCOL_VERSIONS.items():
        if update_docker_compose(service, version):
            updated += 1

    print(f"\n✅ Updated {updated}/{len(SERVICE_PROTOCOL_VERSIONS)} services")
    print("\n🚀 Next steps:")
    print("1. Run 'just down' to stop all services")
    print("2. Run 'just rebuild-all' to rebuild with new configs")
    print("3. Run 'just up' to start services with correct protocol versions")


if __name__ == "__main__":
    main()
