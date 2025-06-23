#!/usr/bin/env python3
"""Make all healthchecks uniform and properly use runtime environment variables."""

from pathlib import Path


def fix_healthcheck_uniform(service_dir):
    """Fix healthcheck to use uniform pattern with runtime environment variables."""
    compose_path = service_dir / "docker-compose.yml"

    if not compose_path.exists():
        return False

    print(f"Processing {compose_path}...")

    with open(compose_path) as f:
        lines = f.readlines()

    modified = False
    for i, line in enumerate(lines):
        # Find healthcheck test lines
        if "test:" in line and "curl" in line and "mcp" in line:
            # Create a uniform healthcheck that properly uses runtime environment variables
            # Using sh -c with proper escaping to ensure the variable is evaluated at runtime
            new_healthcheck = '      test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp -H \'Content-Type: application/json\' -H \'Accept: application/json, text/event-stream\' -d \'{\\"jsonrpc\\":\\"2.0\\",\\"method\\":\\"initialize\\",\\"params\\":{\\"protocolVersion\\":\\"\'\\$MCP_PROTOCOL_VERSION\'\\",\\"capabilities\\":{},\\"clientInfo\\":{\\"name\\":\\"healthcheck\\",\\"version\\":\\"1.0\\"}},\\"id\\":1}\' | grep -q \'\\"protocolVersion\\":\\"\'\\$MCP_PROTOCOL_VERSION\'\\"\'"]'

            if line.strip() != new_healthcheck.strip():
                lines[i] = new_healthcheck + "\n"
                modified = True
                print("  Fixed healthcheck to use uniform pattern")

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
        if fix_healthcheck_uniform(service_dir):
            fixed_count += 1

    print(f"\nFixed {fixed_count} services with uniform healthcheck pattern")


if __name__ == "__main__":
    main()
