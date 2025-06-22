#!/usr/bin/env python3
"""Update MCP service health checks to use correct protocol versions."""

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

def update_healthcheck(service_name, protocol_version):
    """Update healthcheck in docker-compose.yml to use specific protocol version."""
    compose_file = Path(f'/home/atrawog/AI/atrawog/mcp-oauth-gateway/{service_name}/docker-compose.yml')
    
    if not compose_file.exists():
        print(f"❌ {compose_file} not found")
        return False
    
    with open(compose_file, 'r') as f:
        content = f.read()
    
    # Replace the protocol version in the healthcheck curl command
    # Match the pattern: \"protocolVersion\":\"${MCP_PROTOCOL_VERSION:-2025-06-18}\"
    pattern = r'(\\"protocolVersion\\":\\\\")(\$\{MCP_PROTOCOL_VERSION:-[^}]+\})(\\\\")'
    replacement = f'\\1{protocol_version}\\3'
    content = re.sub(pattern, replacement, content)
    
    # Also update the grep check to match the specific version
    # Match the pattern: grep -q \"protocolVersion\":\"${MCP_PROTOCOL_VERSION:-2025-06-18}\"
    pattern = r'(grep -q \\\\"\\\\"protocolVersion\\\\":\\\\")(\$\{MCP_PROTOCOL_VERSION:-[^}]+\})(\\\\")'
    replacement = f'\\1{protocol_version}\\3'
    content = re.sub(pattern, replacement, content)
    
    with open(compose_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {service_name} healthcheck to use protocol version {protocol_version}")
    return True

def main():
    """Update all MCP service healthchecks."""
    print("Updating MCP service healthchecks with correct protocol versions...\n")
    
    updated = 0
    for service, version in SERVICE_PROTOCOL_VERSIONS.items():
        if update_healthcheck(service, version):
            updated += 1
    
    print(f"\n✅ Updated {updated}/{len(SERVICE_PROTOCOL_VERSIONS)} services")
    print("\n🚀 Next steps:")
    print("1. Run 'just down' to stop all services")
    print("2. Run 'just rebuild-all' to rebuild with updated healthchecks")
    print("3. Run 'just up' to start services")

if __name__ == '__main__':
    main()