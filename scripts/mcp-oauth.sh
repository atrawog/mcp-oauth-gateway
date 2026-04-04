#!/bin/bash
# Simple script to run MCP OAuth flow with proper terminal handling

echo "🔐 Generating MCP client token using mcp-streamablehttp-client..."

# Load environment
source .env

# Set MCP server URL
export MCP_SERVER_URL="https://mcp-fetch.${BASE_DOMAIN}/mcp"

# Run the OAuth flow
uv run python -m mcp_streamablehttp_client.cli --token --server-url "$MCP_SERVER_URL"
