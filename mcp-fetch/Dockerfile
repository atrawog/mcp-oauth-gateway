FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks and git for pip install
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

# Install the OFFICIAL MCP fetch server from modelcontextprotocol/servers
RUN pip install "mcp-server-fetch @ git+https://github.com/modelcontextprotocol/servers.git#subdirectory=src/fetch"

# Copy the mcp-streamablehttp-server package source
COPY ../mcp-streamablehttp-server /tmp/mcp-streamablehttp-server

# Install the mcp-streamablehttp-server package from source
RUN pip install /tmp/mcp-streamablehttp-server

# Clean up the temporary copy
RUN rm -rf /tmp/mcp-streamablehttp-server

# Expose the divine port
EXPOSE 3000

# Run using the installed mcp-streamablehttp-server command
# Using shell form to handle the command properly
CMD mcp-streamablehttp-server python -m mcp_server_fetch