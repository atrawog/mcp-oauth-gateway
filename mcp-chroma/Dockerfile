FROM python:3.12-slim

WORKDIR /app

# Install necessary packages for building Python dependencies
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    git \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

# Clone the chroma MCP server repository
RUN git clone https://github.com/privetin/chroma.git /tmp/chroma-mcp

# Install the chroma MCP server dependencies
WORKDIR /tmp/chroma-mcp
RUN uv venv && \
    uv sync --dev

# Copy the mcp-streamablehttp-proxy package source
COPY mcp-streamablehttp-proxy /tmp/mcp-streamablehttp-proxy

# Install the mcp-streamablehttp-proxy package from source
RUN pip install /tmp/mcp-streamablehttp-proxy

# Clean up the temporary proxy copy
RUN rm -rf /tmp/mcp-streamablehttp-proxy

# Create data directory for chroma
RUN mkdir -p /app/data

# Move chroma source to app directory
RUN mv /tmp/chroma-mcp /app/chroma-mcp

# Set working directory back to app
WORKDIR /app

# Expose the standard MCP port
EXPOSE 3000

# Set environment variables
ENV PORT=3000
ENV CHROMA_DATA_PATH=/app/data

# Health check to verify the server is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Create a startup script for chroma MCP server
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'cd /app/chroma-mcp' >> /app/start.sh && \
    echo 'exec mcp-streamablehttp-proxy uv run chroma' >> /app/start.sh && \
    chmod +x /app/start.sh

# Use mcp-streamablehttp-proxy to wrap the chroma MCP server
CMD ["/app/start.sh"]