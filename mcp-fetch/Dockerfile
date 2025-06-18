FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Install the BLESSED FastMCP framework!
RUN pip install fastmcp httpx

# Copy our MCP server implementation
COPY mcp_fetch_server.py /app/

# The MCP service port
EXPOSE 3000

# Run the native streamable HTTP server - NO PROXIES!
# This service knows NOTHING about OAuth!
CMD ["python", "mcp_fetch_server.py"]