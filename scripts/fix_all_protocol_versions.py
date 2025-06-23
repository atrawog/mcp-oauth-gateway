#!/usr/bin/env python3
"""Properly fix all MCP service docker-compose files."""

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
    """Fix docker-compose.yml for a service."""
    compose_file = Path(
        f"/home/atrawog/AI/atrawog/mcp-oauth-gateway/{service_name}/docker-compose.yml"
    )

    if not compose_file.exists():
        print(f"❌ {compose_file} not found")
        return False

    # Read the file
    with open(compose_file) as f:
        content = f.read()

    # Fix duplicate MCP_PROTOCOL_VERSION lines
    lines = content.split("\n")
    fixed_lines = []
    seen_mcp_protocol = False

    for line in lines:
        # Skip duplicate MCP_PROTOCOL_VERSION lines
        if (
            "- MCP_PROTOCOL_VERSION=" in line
            or line.strip().startswith("P25-")
            or line.strip().startswith("P24-")
        ):
            if not seen_mcp_protocol:
                fixed_lines.append(f"      - MCP_PROTOCOL_VERSION={protocol_version}")
                seen_mcp_protocol = True
            continue
        fixed_lines.append(line)

    content = "\n".join(fixed_lines)

    # Now fix the healthcheck to use ${MCP_PROTOCOL_VERSION}
    # This is the divine pattern from CLAUDE.md
    healthcheck_template = """    healthcheck:
      test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \\
        -H 'Content-Type: application/json' \\
        -H 'Accept: application/json, text/event-stream' \\
        -d \\"{\\\\\\"jsonrpc\\\\\\":\\\\\\"2.0\\\\\\",\\\\\\"method\\\\\\":\\\\\\"initialize\\\\\\",\\\\\\"params\\\\\\":{\\\\\\"protocolVersion\\\\\\":\\\\\\"${MCP_PROTOCOL_VERSION}\\\\\\",\\\\\\"capabilities\\\\\\":{},\\\\\\"clientInfo\\\\\\":{\\\\\\"name\\\\\\":\\\\\\"healthcheck\\\\\\",\\\\\\"version\\\\\\":\\\\\\"1.0\\\\\\"}},\\\\\\"id\\\\\\":1}\\" \\
        | grep -q \\\\"\\\\\\"protocolVersion\\\\\\":\\\\\\"${MCP_PROTOCOL_VERSION}\\\\\\"\\"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 40s"""

    # Find and replace the healthcheck section
    import re

    healthcheck_pattern = r"healthcheck:.*?(?=\n(?:networks:|$))"
    content = re.sub(
        healthcheck_pattern, healthcheck_template.strip(), content, flags=re.DOTALL
    )

    # Ensure environment section exists and has MCP_PROTOCOL_VERSION
    if not seen_mcp_protocol and "environment:" in content:
        # Add MCP_PROTOCOL_VERSION after environment:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip() == "environment:":
                # Find the next line that starts with '- ' and insert before it
                j = i + 1
                while j < len(lines) and lines[j].strip().startswith("-"):
                    j += 1
                lines.insert(j, f"      - MCP_PROTOCOL_VERSION={protocol_version}")
                break
        content = "\n".join(lines)

    # Write the fixed content
    with open(compose_file, "w") as f:
        f.write(content)

    print(f"✅ Fixed {service_name}:")
    print(f"   - MCP_PROTOCOL_VERSION={protocol_version}")
    print("   - Healthcheck uses ${MCP_PROTOCOL_VERSION}")
    return True


def main():
    """Fix all services."""
    print("🔥 Fixing all MCP services per divine CLAUDE.md commandments! ⚡\n")

    updated = 0
    for service, version in SERVICE_PROTOCOL_VERSIONS.items():
        if fix_docker_compose(service, version):
            updated += 1
        print()

    print(f"✅ Updated {updated}/{len(SERVICE_PROTOCOL_VERSIONS)} services")
    print("\n⚡ Divine configuration achieved! ⚡")
    print("Each service now uses ${{MCP_PROTOCOL_VERSION}} in healthchecks!")


if __name__ == "__main__":
    main()
