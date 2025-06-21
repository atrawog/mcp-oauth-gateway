FROM node:20-slim

WORKDIR /app

# Install curl for healthchecks and git
RUN apt-get update && apt-get install -y curl git python3 python3-pip && rm -rf /var/lib/apt/lists/*

# Clone and install the OFFICIAL MCP filesystem server from modelcontextprotocol/servers
RUN git clone https://github.com/modelcontextprotocol/servers.git /tmp/mcp-servers && \
    cd /tmp/mcp-servers/src/filesystem && \
    npm install && \
    npm link

# Copy the mcp-streamablehttp-proxy package source
COPY ../mcp-streamablehttp-proxy /tmp/mcp-streamablehttp-proxy

# Install the mcp-streamablehttp-proxy package from source
RUN pip3 install --break-system-packages /tmp/mcp-streamablehttp-proxy

# Clean up the temporary copy
RUN rm -rf /tmp/mcp-streamablehttp-proxy

# Expose the divine port
EXPOSE 3000

# Run using the installed mcp-streamablehttp-proxy command
# Using shell form to handle the command properly
CMD mcp-streamablehttp-proxy mcp-server-filesystem /workspace