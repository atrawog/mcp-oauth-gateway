#!/usr/bin/env python3
"""Fix healthcheck syntax in all docker-compose files."""

import re
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


def fix_healthcheck(service_name):
    """Fix healthcheck syntax for a service."""
    compose_file = Path(f"/home/atrawog/AI/atrawog/mcp-oauth-gateway/{service_name}/docker-compose.yml")

    if not compose_file.exists():
        print(f"❌ {compose_file} not found")
        return False

    with open(compose_file) as f:
        content = f.read()

    # The proper healthcheck format - simpler escaping
    healthcheck_template = """    healthcheck:
      test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d '{\\"jsonrpc\\":\\"2.0\\",\\"method\\":\\"initialize\\",\\"params\\":{\\"protocolVersion\\":\\"$${MCP_PROTOCOL_VERSION}\\",\\"capabilities\\":{},\\"clientInfo\\":{\\"name\\":\\"healthcheck\\",\\"version\\":\\"1.0\\"}},\\"id\\":1}' | grep -q '\\"protocolVersion\\":\\"$${MCP_PROTOCOL_VERSION}\\"'"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 40s"""

    # Find and replace the healthcheck section
    healthcheck_pattern = r"healthcheck:.*?(?=\nnetworks:|volumes:|\Z)"
    content = re.sub(
        healthcheck_pattern,
        healthcheck_template.strip() + "\n",
        content,
        flags=re.DOTALL,
    )

    # Write the fixed content
    with open(compose_file, "w") as f:
        f.write(content)

    print(f"✅ Fixed {service_name} healthcheck syntax")
    return True


def main():
    """Fix all services."""
    print("🔧 Fixing healthcheck syntax in all services...\n")

    updated = 0
    for service in SERVICES:
        if fix_healthcheck(service):
            updated += 1

    print(f"\n✅ Fixed {updated}/{len(SERVICES)} services")


if __name__ == "__main__":
    main()
