FROM python:3.12-alpine

WORKDIR /app

# Install tmux, curl, and Node.js for tmux-mcp
RUN apk add --no-cache tmux bash curl nodejs npm

# Install tmux-mcp via npm
RUN npm install -g tmux-mcp

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
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Create a startup script to ensure tmux session exists
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'tmux list-sessions 2>/dev/null || tmux new-session -d -s default' >> /app/start.sh && \
    echo 'exec mcp-streamablehttp-proxy npx tmux-mcp' >> /app/start.sh && \
    chmod +x /app/start.sh

# Use mcp-streamablehttp-proxy to wrap the tmux-mcp server
CMD ["/app/start.sh"]