#!/usr/bin/env python3
"""Fix MCP service docker-compose files to properly use MCP_PROTOCOL_VERSION."""

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

def fix_docker_compose(service_name, protocol_version):
    """Update docker-compose.yml to properly set and use MCP_PROTOCOL_VERSION."""
    compose_file = Path(f'/home/atrawog/AI/atrawog/mcp-oauth-gateway/{service_name}/docker-compose.yml')
    
    if not compose_file.exists():
        print(f"❌ {compose_file} not found")
        return False
    
    with open(compose_file, 'r') as f:
        lines = f.readlines()
    
    # Fix corrupted lines and ensure MCP_PROTOCOL_VERSION is set correctly
    fixed_lines = []
    in_environment = False
    found_protocol_version = False
    
    for i, line in enumerate(lines):
        # Check if we're in the environment section
        if line.strip() == 'environment:':
            in_environment = True
            fixed_lines.append(line)
            continue
        
        # Check if we're leaving the environment section
        if in_environment and line.strip() and not line.strip().startswith('-'):
            # We're leaving environment section, add MCP_PROTOCOL_VERSION if not found
            if not found_protocol_version:
                fixed_lines.append(f'      - MCP_PROTOCOL_VERSION={protocol_version}\n')
            in_environment = False
        
        # Fix corrupted lines (like "P25-03-26")
        if line.strip().startswith('P25-') or line.strip().startswith('P24-'):
            fixed_lines.append(f'      - MCP_PROTOCOL_VERSION={protocol_version}\n')
            found_protocol_version = True
            continue
        
        # Update existing MCP_PROTOCOL_VERSION line
        if '- MCP_PROTOCOL_VERSION=' in line:
            fixed_lines.append(f'      - MCP_PROTOCOL_VERSION={protocol_version}\n')
            found_protocol_version = True
            continue
        
        fixed_lines.append(line)
    
    # Write the fixed content
    with open(compose_file, 'w') as f:
        f.writelines(fixed_lines)
    
    # Now update healthcheck to use ${MCP_PROTOCOL_VERSION}
    with open(compose_file, 'r') as f:
        content = f.read()
    
    # Replace hardcoded protocol versions in healthcheck with ${MCP_PROTOCOL_VERSION}
    # Match patterns like "2025-06-18", "2025-03-26", "2024-11-05"
    healthcheck_pattern = r'(test:.*?"protocolVersion":")(\d{4}-\d{2}-\d{2})(".*?grep.*?"protocolVersion":")(\d{4}-\d{2}-\d{2})(")'
    
    def update_healthcheck(match):
        return match.group(1) + '${MCP_PROTOCOL_VERSION}' + match.group(3) + '${MCP_PROTOCOL_VERSION}' + match.group(5)
    
    content = re.sub(healthcheck_pattern, update_healthcheck, content, flags=re.DOTALL)
    
    with open(compose_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {service_name}:")
    print(f"   - Set MCP_PROTOCOL_VERSION={protocol_version} in environment")
    print(f"   - Updated healthcheck to use ${{MCP_PROTOCOL_VERSION}}")
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
    print("   - Uses ${{MCP_PROTOCOL_VERSION}} in healthchecks (no hardcoding!)")

if __name__ == '__main__':
    main()