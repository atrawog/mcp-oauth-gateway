#!/bin/bash
# Simple wrapper to run MCP OAuth flow with proper terminal handling

export MCP_SERVER_URL="https://mcp-fetch.${BASE_DOMAIN}/mcp"

# Run the command with full terminal access
pixi run python -m mcp_streamablehttp_client.cli --token --server-url "$MCP_SERVER_URL" | tee /tmp/mcp_oauth_output.txt

# Extract and save tokens
pixi run python scripts/extract_tokens.py /tmp/mcp_oauth_output.txt
