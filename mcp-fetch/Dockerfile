FROM python:3.11-slim

WORKDIR /app

# Install mcp AND mcp-proxy!
RUN pip install mcp mcp-proxy

# The MCP service port
EXPOSE 3000

# Run mcp-proxy to bridge HTTP to stdio for mcp-server-fetch
# This service knows NOTHING about OAuth!
CMD ["mcp-proxy", "--transport", "streamablehttp", "--port", "3000", "--host", "0.0.0.0", "--", "mcp-server-fetch"]