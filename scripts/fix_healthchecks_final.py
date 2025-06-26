#!/usr/bin/env python3
"""Fix MCP service health checks to use correct protocol versions."""

import re
from pathlib import Path


# Actual protocol versions supported by each service
SERVICE_PROTOCOL_VERSIONS = {
    "mcp-fetch": "2025-03-26",
    "mcp-fetchs": "2025-06-18",
    "mcp-filesystem": "2025-03-26",
    "mcp-memory": "2024-11-05",
    "mcp-playwright": "2025-06-18",
    "mcp-sequentialthinking": "2024-11-05",
    "mcp-time": "2025-03-26",
    "mcp-tmux": "2025-06-18",
    "mcp-everything": "2025-06-18",
}


def update_healthcheck(service_name, protocol_version):
    """Update healthcheck to use the correct hardcoded protocol version."""
    compose_file = Path(f"/home/atrawog/AI/atrawog/mcp-oauth-gateway/{service_name}/docker-compose.yml")

    if not compose_file.exists():
        print(f"❌ {compose_file} not found")
        return False

    with open(compose_file) as f:
        content = f.read()

    # Replace ${MCP_PROTOCOL_VERSION:-2025-06-18} with the actual version in the curl command
    pattern = r"\$\{MCP_PROTOCOL_VERSION:-[\d-]+\}"
    content = re.sub(pattern, protocol_version, content)

    with open(compose_file, "w") as f:
        f.write(content)

    print(f"✅ Updated {service_name} healthcheck to use protocol version {protocol_version}")
    return True


def main():
    """Update all MCP service healthchecks."""
    print("Fixing MCP service healthchecks with correct protocol versions...\n")

    updated = 0
    for service, version in SERVICE_PROTOCOL_VERSIONS.items():
        if update_healthcheck(service, version):
            updated += 1

    print(f"\n✅ Updated {updated}/{len(SERVICE_PROTOCOL_VERSIONS)} services")
    print("\n🚀 Services need to be rebuilt for healthcheck changes to take effect:")
    print("1. Run 'just down' to stop all services")
    print("2. Run 'just rebuild-all' to rebuild with updated healthchecks")
    print("3. Run 'just up' to start services")


if __name__ == "__main__":
    main()
