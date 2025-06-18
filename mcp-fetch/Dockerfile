FROM node:20-slim

WORKDIR /app

# Install system dependencies including curl for healthchecks and python for healthcheck
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Install MCP tools
RUN npm install -g @modelcontextprotocol/server-fetch mcp-proxy

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# The MCP service port
EXPOSE 3000

# Run mcp-proxy to bridge HTTP to stdio for mcp-server-fetch
# This service knows NOTHING about OAuth!
CMD ["mcp-proxy", "--transport", "streamablehttp", "--port", "3000", "--host", "0.0.0.0", "--", "mcp-server-fetch"]