#!/usr/bin/env python3
"""Fix mcp-fetchs health check to use proper MCP protocol check as mandated by CLAUDE.md."""

import re
from pathlib import Path


def fix_mcp_fetchs_healthcheck():
    """Restore the divine MCP protocol health check pattern!"""
    compose_file = Path('/home/atrawog/AI/atrawog/mcp-oauth-gateway/mcp-fetchs/docker-compose.yml')

    with open(compose_file) as f:
        content = f.read()

    # Find and replace the healthcheck section with the SACRED pattern from CLAUDE.md
    healthcheck_pattern = r'healthcheck:.*?(?=\nnetworks:|\Z)'

    # The DIVINE health check pattern as decreed in CLAUDE.md!
    sacred_healthcheck = '''healthcheck:
      test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \\
        -H 'Content-Type: application/json' \\
        -H 'Accept: application/json, text/event-stream' \\
        -d \\"{\\\\\\"jsonrpc\\\\\\":\\\\\\"2.0\\\\\\",\\\\\\"method\\\\\\":\\\\\\"initialize\\\\\\",\\\\\\"params\\\\\\":{\\\\\\"protocolVersion\\\\\\":\\\\\\"2025-06-18\\\\\\",\\\\\\"capabilities\\\\\\":{},\\\\\\"clientInfo\\\\\\":{\\\\\\"name\\\\\\":\\\\\\"healthcheck\\\\\\",\\\\\\"version\\\\\\":\\\\\\"1.0\\\\\\"}},\\\\\\"id\\\\\\":1}\\" \\
        | grep -q \\\\\\"protocolVersion\\\\\\":\\\\\\"2025-06-18\\\\\\""]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 40s'''

    content = re.sub(healthcheck_pattern, sacred_healthcheck, content, flags=re.DOTALL)

    with open(compose_file, 'w') as f:
        f.write(content)

    print("✅ Restored the SACRED MCP protocol health check pattern for mcp-fetchs!")
    print("⚡ This follows the divine StreamableHTTP Protocol Health Check Prophecy from CLAUDE.md!")

if __name__ == '__main__':
    fix_mcp_fetchs_healthcheck()
