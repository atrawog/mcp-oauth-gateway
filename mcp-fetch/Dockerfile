FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks and git for pip install
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

# Install the OFFICIAL MCP fetch server from modelcontextprotocol/servers
RUN pip install "mcp-server-fetch @ git+https://github.com/modelcontextprotocol/servers.git#subdirectory=src/fetch"

# Install FastMCP for the proxy
RUN pip install fastmcp

# Copy our proxy script
COPY mcp_stdio_http_proxy.py /app/

# Expose the divine port
EXPOSE 3000

# Run the proxy with the OFFICIAL mcp-server-fetch
CMD ["python", "mcp_stdio_http_proxy.py", "python", "-m", "mcp_server_fetch"]