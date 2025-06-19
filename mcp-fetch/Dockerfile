FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks and git for pip install
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

# Install the OFFICIAL MCP fetch server from modelcontextprotocol/servers
RUN pip install "mcp-server-fetch @ git+https://github.com/modelcontextprotocol/servers.git#subdirectory=src/fetch"

# Copy the mcp-stdio-http package source
COPY ../mcp-stdio-http /tmp/mcp-stdio-http

# Install the mcp-stdio-http package from source
RUN pip install /tmp/mcp-stdio-http

# Clean up the temporary copy
RUN rm -rf /tmp/mcp-stdio-http

# Expose the divine port
EXPOSE 3000

# Run using the installed mcp-stdio-http command
# Using shell form to handle the command properly
CMD mcp-stdio-http python -m mcp_server_fetch