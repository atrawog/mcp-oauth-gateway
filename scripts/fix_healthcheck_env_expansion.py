#!/usr/bin/env python3
"""Fix healthcheck commands to properly expand environment variables."""

import os
import re
from pathlib import Path


def fix_healthcheck_env_expansion(service_dir):
    """Fix healthcheck to properly expand environment variables."""
    compose_path = service_dir / "docker-compose.yml"
    
    if not compose_path.exists():
        return False
    
    print(f"Processing {compose_path}...")
    
    with open(compose_path, 'r') as f:
        content = f.read()
    
    # Find healthcheck test lines and fix environment variable expansion
    # Change ${MCP_PROTOCOL_VERSION} to $MCP_PROTOCOL_VERSION (without braces)
    # This allows shell expansion inside the container
    original_content = content
    
    # Fix in the JSON request
    content = re.sub(
        r'\\"protocolVersion\\":\\"\$\{MCP_PROTOCOL_VERSION\}\\"',
        r'\\"protocolVersion\\":\\"$MCP_PROTOCOL_VERSION\\"',
        content
    )
    
    # Fix in the grep pattern
    content = re.sub(
        r"grep -q '\\\"protocolVersion\\\":\\\"\$\{MCP_PROTOCOL_VERSION\}\\\"'",
        r"grep -q '\"protocolVersion\":\"'\"$MCP_PROTOCOL_VERSION\"'\"'",
        content
    )
    
    if content != original_content:
        print(f"  Fixed environment variable expansion in healthcheck")
        with open(compose_path, 'w') as f:
            f.write(content)
        return True
    
    return False


def main():
    # Find all MCP service directories
    base_dir = Path("/home/atrawog/AI/atrawog/mcp-oauth-gateway")
    service_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("mcp-")]
    
    fixed_count = 0
    for service_dir in sorted(service_dirs):
        if fix_healthcheck_env_expansion(service_dir):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} services with environment variable expansion issues")


if __name__ == "__main__":
    main()