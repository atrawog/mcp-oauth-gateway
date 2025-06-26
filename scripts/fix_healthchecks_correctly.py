#!/usr/bin/env python3
"""Fix health checks to expect the correct protocol versions in responses."""

import re
from pathlib import Path


# What each service ACTUALLY returns (not what we request!)
SERVICE_RESPONSE_VERSIONS = {
    "mcp-fetch": "2025-03-26",
    "mcp-fetchs": "2025-06-18",  # Native implementation, supports latest
    "mcp-filesystem": "2025-03-26",
    "mcp-memory": "2024-11-05",
    "mcp-playwright": "2025-06-18",
    "mcp-sequentialthinking": "2024-11-05",
    "mcp-time": "2025-03-26",
    "mcp-tmux": "2025-06-18",
    "mcp-everything": "2025-06-18",
}


def fix_healthcheck(service_name, response_version):
    """Fix healthcheck to expect the correct response version."""
    compose_file = Path(f"/home/atrawog/AI/atrawog/mcp-oauth-gateway/{service_name}/docker-compose.yml")

    if not compose_file.exists():
        print(f"❌ {compose_file} not found")
        return False

    with open(compose_file) as f:
        content = f.read()

    # The healthcheck should:
    # 1. Request with ${MCP_PROTOCOL_VERSION} (whatever the client wants)
    # 2. But expect the actual version the server supports in the response

    # Find the healthcheck section
    healthcheck_pattern = r'(healthcheck:.*?test: \["CMD", "sh", "-c", "curl[^]]+\])'

    def replace_healthcheck(match):
        healthcheck = match.group(1)
        # Replace the grep part to expect the actual response version
        # Look for patterns like: grep -q '"protocolVersion":"${MCP_PROTOCOL_VERSION}"'
        grep_pattern = r'grep -q [\'"]\\?"protocolVersion\\?":\\?"[^"]+\\?"[\'"]'
        new_grep = f'grep -q \'\\"protocolVersion\\":\\"{response_version}\\"\''
        return re.sub(grep_pattern, new_grep, healthcheck)

    content = re.sub(healthcheck_pattern, replace_healthcheck, content, flags=re.DOTALL)

    with open(compose_file, "w") as f:
        f.write(content)

    print(f"✅ Fixed {service_name}:")
    print("   - Requests with ${MCP_PROTOCOL_VERSION} (client's choice)")
    print(f"   - Expects '{response_version}' in response (what server actually supports)")
    return True


def main():
    """Fix all services."""
    print("🔥 Fixing health checks to expect correct response versions! ⚡\n")
    print("The proxy forwards whatever version the client requests,")
    print("but the server responds with the version it actually supports.\n")

    updated = 0
    for service, version in SERVICE_RESPONSE_VERSIONS.items():
        if fix_healthcheck(service, version):
            updated += 1
        print()

    print(f"✅ Fixed {updated}/{len(SERVICE_RESPONSE_VERSIONS)} services")
    print("\n⚡ Health checks now properly handle protocol version negotiation! ⚡")


if __name__ == "__main__":
    main()
