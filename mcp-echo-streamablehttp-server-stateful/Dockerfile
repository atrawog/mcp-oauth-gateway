# MCP Echo StreamableHTTP Server - Stateful version Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files
COPY pyproject.toml ./
COPY src/ ./src/
COPY README.md ./

# Install the package
RUN pip install --no-cache-dir -e .

# Health check using the built-in health probe
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=40s \
    CMD curl -f -X POST http://localhost:3000/mcp \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"healthProbe","arguments":{}},"id":999}' \
        || exit 1

# Expose port
EXPOSE 3000

# Set default environment variables
ENV MCP_ECHO_HOST=0.0.0.0
ENV MCP_ECHO_PORT=3000
ENV MCP_ECHO_DEBUG=false
ENV MCP_SESSION_TIMEOUT=3600
ENV MCP_PROTOCOL_VERSIONS_SUPPORTED=2025-06-18,2025-03-26,2024-11-05

# Run the server
CMD ["mcp-echo-streamablehttp-server-stateful"]
