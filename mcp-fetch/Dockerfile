FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install mcp AND mcp-proxy AND mcp-server-fetch!
RUN pip install mcp mcp-proxy mcp-server-fetch

# The MCP service port
EXPOSE 3000

# Run mcp-proxy to bridge HTTP to stdio for mcp-server-fetch
# This service knows NOTHING about OAuth!
# Note: When running as server, mcp-proxy only supports SSE transport
CMD ["mcp-proxy", "--port", "3000", "--host", "0.0.0.0", "--", "/usr/local/bin/mcp-server-fetch"]