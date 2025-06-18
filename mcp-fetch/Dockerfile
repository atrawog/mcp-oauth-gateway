FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks and other utilities
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Install the OFFICIAL MCP fetch server
RUN pip install mcp-server-fetch

# Install FastMCP for streamable HTTP transport
# Force compatible httpx version for mcp-server-fetch
RUN pip install "httpx<0.28" fastmcp

# Copy our generic stdio-to-HTTP proxy
COPY mcp_stdio_http_proxy.py /app/

# The MCP service port
EXPOSE 3000

# Run the generic proxy with the official mcp-server-fetch
CMD ["python", "mcp_stdio_http_proxy.py", "python", "-m", "mcp_server_fetch"]