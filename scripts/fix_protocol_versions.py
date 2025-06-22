#!/usr/bin/env python3
"""Fix MCP service docker-compose files to use correct protocol versions."""

import re
from pathlib import Path

# Actual protocol versions supported by each service
SERVICE_PROTOCOL_VERSIONS = {
    'mcp-fetch': '2025-03-26',
    'mcp-fetchs': '2025-06-18',
    'mcp-filesystem': '2025-03-26',
    'mcp-memory': '2024-11-05',
    'mcp-playwright': '2025-06-18',
    'mcp-sequentialthinking': '2024-11-05',
    'mcp-time': '2025-03-26',
    'mcp-tmux': '2025-06-18',
    'mcp-everything': '2025-06-18'
}

def fix_corrupted_line(service_name, protocol_version):
    """Fix the corrupted MCP_PROTOCOL_VERSION line."""
    compose_file = Path(f'/home/atrawog/AI/atrawog/mcp-oauth-gateway/{service_name}/docker-compose.yml')
    
    if not compose_file.exists():
        print(f"❌ {compose_file} not found")
        return False
    
    with open(compose_file, 'r') as f:
        lines = f.readlines()
    
    # Fix corrupted lines
    fixed_lines = []
    for line in lines:
        if line.strip().startswith('P25-'):
            # This is a corrupted line, replace it
            fixed_lines.append(f'      - MCP_PROTOCOL_VERSION={protocol_version}\n')
        else:
            fixed_lines.append(line)
    
    with open(compose_file, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"✅ Fixed {service_name} to use protocol version {protocol_version}")
    return True

def update_healthcheck(service_name, protocol_version):
    """Update healthcheck to use correct protocol version."""
    compose_file = Path(f'/home/atrawog/AI/atrawog/mcp-oauth-gateway/{service_name}/docker-compose.yml')
    
    if not compose_file.exists():
        return False
    
    with open(compose_file, 'r') as f:
        content = f.read()
    
    # Update healthcheck protocol version in the request
    pattern = r'(\\"protocolVersion\\":\\\\")[^"\\]+(\\\\")'
    replacement = f'\\1{protocol_version}\\2'
    content = re.sub(pattern, replacement, content)
    
    # Update healthcheck protocol version in the grep
    pattern = r'(grep -q \\\\"\\\\"protocolVersion\\\\":\\\\")[^"\\]+(\\\\")'
    replacement = f'\\1{protocol_version}\\2'
    content = re.sub(pattern, replacement, content)
    
    with open(compose_file, 'w') as f:
        f.write(content)
    
    return True

def main():
    """Fix all MCP services with correct protocol versions."""
    print("Fixing MCP services with correct protocol versions...\n")
    
    # First fix the corrupted lines
    for service, version in SERVICE_PROTOCOL_VERSIONS.items():
        fix_corrupted_line(service, version)
    
    print("\nUpdating healthchecks...")
    
    # Then update healthchecks
    for service, version in SERVICE_PROTOCOL_VERSIONS.items():
        update_healthcheck(service, version)
    
    print(f"\n✅ Fixed all services")
    print("\n🚀 Next steps:")
    print("1. Run 'just down' to stop all services")
    print("2. Run 'just rebuild-all' to rebuild with new configs")
    print("3. Run 'just up' to start services with correct protocol versions")

if __name__ == '__main__':
    main()