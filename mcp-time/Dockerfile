FROM python:3.12-alpine

WORKDIR /app

# Install basic dependencies for health checks
RUN apk add --no-cache curl netcat-openbsd

# Install the official MCP time server
RUN pip install mcp-server-time

# Copy the mcp-streamablehttp-proxy package source
COPY ../mcp-streamablehttp-proxy /tmp/mcp-streamablehttp-proxy

# Install the mcp-streamablehttp-proxy package from source
RUN pip install /tmp/mcp-streamablehttp-proxy

# Clean up the temporary copy
RUN rm -rf /tmp/mcp-streamablehttp-proxy

# Expose the standard MCP port
EXPOSE 3000

# Set environment variables
ENV PORT=3000

# Health check to verify the server is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Use mcp-streamablehttp-proxy to wrap the time server
# Using shell form to handle the command properly
CMD mcp-streamablehttp-proxy python -m mcp_server_time
