#!/usr/bin/env python3
"""Fix all healthchecks to use the correct pattern that actually works."""

from pathlib import Path


def fix_healthcheck_correct(service_dir):
    """Fix healthcheck to use the working pattern."""
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
            # Use the pattern that actually works - with double dollar signs
            # This prevents Docker Compose from substituting at compose time
            # and allows the shell to expand the variable at runtime
            new_healthcheck = '      test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp -H \'Content-Type: application/json\' -H \'Accept: application/json, text/event-stream\' -d \'{\\"jsonrpc\\":\\"2.0\\",\\"method\\":\\"initialize\\",\\"params\\":{\\"protocolVersion\\":\\"\'$$MCP_PROTOCOL_VERSION\'\\",\\"capabilities\\":{},\\"clientInfo\\":{\\"name\\":\\"healthcheck\\",\\"version\\":\\"1.0\\"}},\\"id\\":1}\' | grep -q \'\\"protocolVersion\\":\\"\'$$MCP_PROTOCOL_VERSION\'\\"\'"]'

            if line.strip() != new_healthcheck.strip():
                lines[i] = new_healthcheck + "\n"
                modified = True
                print("  Fixed healthcheck")

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
        if fix_healthcheck_correct(service_dir):
            fixed_count += 1

    print(f"\nFixed {fixed_count} services")


if __name__ == "__main__":
    main()
