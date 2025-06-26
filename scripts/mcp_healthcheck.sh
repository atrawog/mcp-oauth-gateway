#!/bin/bash
# Standardized MCP Health Check Script
# This script performs a divine MCP protocol health check for any MCP service

# Configuration from environment
MCP_HOST="${MCP_HOST:-localhost}"
MCP_PORT="${MCP_PORT:-3000}"

# MCP_PROTOCOL_VERSION MUST be set by the calling service
if [ -z "$MCP_PROTOCOL_VERSION" ]; then
  echo "ERROR: MCP_PROTOCOL_VERSION environment variable is not set!"
  echo "Each service must define its own protocol version in docker-compose.yml"
  exit 1
fi

# Build the initialization request payload
REQUEST_PAYLOAD=$(cat <<EOF
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "${MCP_PROTOCOL_VERSION}",
    "capabilities": {},
    "clientInfo": {
      "name": "healthcheck",
      "version": "1.0"
    }
  },
  "id": 1
}
EOF
)

# Perform the health check
response=$(curl -s -X POST "http://${MCP_HOST}:${MCP_PORT}/mcp" \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d "${REQUEST_PAYLOAD}" \
  --max-time 5)

# Check if the response contains the expected protocol version
if echo "$response" | grep -q "\"protocolVersion\":\s*\"${MCP_PROTOCOL_VERSION}\""; then
  echo "Health check passed: MCP service is responding with protocol version ${MCP_PROTOCOL_VERSION}"
  exit 0
else
  echo "Health check failed: MCP service did not respond with expected protocol version"
  echo "Response: $response"
  exit 1
fi
