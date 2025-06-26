#!/usr/bin/env python3
"""Fix MCP service docker-compose files to properly use MCP_PROTOCOL_VERSION."""

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


def fix_docker_compose(service_name, protocol_version):
    """Update docker-compose.yml to properly set and use MCP_PROTOCOL_VERSION."""
    compose_file = Path(f"/home/atrawog/AI/atrawog/mcp-oauth-gateway/{service_name}/docker-compose.yml")

    if not compose_file.exists():
        print(f"❌ {compose_file} not found")
        return False

    with open(compose_file) as f:
        content = f.read()

    # First, ensure MCP_PROTOCOL_VERSION is properly set in environment section
    # Look for the environment section and update/add MCP_PROTOCOL_VERSION
    env_pattern = r"(environment:\s*\n(?:[ \t]*-[^\n]+\n)*)"

    def update_environment(match):
        env_section = match.group(1)
        # Check if MCP_PROTOCOL_VERSION already exists
        if "MCP_PROTOCOL_VERSION=" in env_section:
            # Update existing line
            env_section = re.sub(
                r"([ \t]*- MCP_PROTOCOL_VERSION=).*",
                f"\\1{protocol_version}",
                env_section,
            )
        else:
            # Add new line
            env_section = env_section.rstrip("\n") + f"\n      - MCP_PROTOCOL_VERSION={protocol_version}\n"
        return env_section

    content = re.sub(env_pattern, update_environment, content)

    # Now update the healthcheck to use ${MCP_PROTOCOL_VERSION} instead of hardcoded values
    # This regex matches the healthcheck test line and replaces hardcoded protocol versions
    healthcheck_pattern = r'(test: \["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp[^"]*-d \'{[^}]*"protocolVersion":")([^"]+)("[^}]*}\}[^"]*grep[^"]*"protocolVersion":")([^"]+)("[^"]*"\])'

    def update_healthcheck(match):
        return match.group(1) + "${MCP_PROTOCOL_VERSION}" + match.group(3) + "${MCP_PROTOCOL_VERSION}" + match.group(5)

    content = re.sub(healthcheck_pattern, update_healthcheck, content)

    with open(compose_file, "w") as f:
        f.write(content)

    print(f"✅ Updated {service_name}:")
    print(f"   - Set MCP_PROTOCOL_VERSION={protocol_version} in environment")
    print(f"   - Updated healthcheck to use ${MCP_PROTOCOL_VERSION}")
    return True


def main():
    """Update all MCP services with proper protocol version configuration."""
    print("Fixing MCP services to properly use MCP_PROTOCOL_VERSION...\n")

    updated = 0
    for service, version in SERVICE_PROTOCOL_VERSIONS.items():
        if fix_docker_compose(service, version):
            updated += 1
        print()

    print(f"✅ Updated {updated}/{len(SERVICE_PROTOCOL_VERSIONS)} services")
    print("\n🚀 Next steps:")
    print("1. Run 'just down' to stop all services")
    print("2. Run 'just up' to start services with proper configuration")
    print("\n⚡ Each service now:")
    print("   - Has MCP_PROTOCOL_VERSION set to its supported version")
    print("   - Uses ${MCP_PROTOCOL_VERSION} in healthchecks (no hardcoding!)")


if __name__ == "__main__":
    main()
