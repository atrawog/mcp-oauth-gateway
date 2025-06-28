FROM python:3.13-slim

WORKDIR /app

# Install required system packages including curl for healthchecks and git for cloning
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

# Clone and install mcp-redis from the official repository
RUN git clone https://github.com/redis/mcp-redis.git /tmp/mcp-redis && \
    cd /tmp/mcp-redis && \
    pip install uv && \
    uv pip install --system --no-cache -r pyproject.toml && \
    cp -r src/* /app/ && \
    rm -rf /tmp/mcp-redis

# Install mcp-streamablehttp-proxy to wrap the stdio server
COPY ../mcp-streamablehttp-proxy /tmp/mcp-streamablehttp-proxy
RUN pip install /tmp/mcp-streamablehttp-proxy && \
    rm -rf /tmp/mcp-streamablehttp-proxy

# Expose the StreamableHTTP port
EXPOSE 3000

# Set the transport mode to streamable-http via environment variable
ENV MCP_TRANSPORT=streamable-http

# Run the MCP Redis server through the StreamableHTTP proxy
CMD ["mcp-streamablehttp-proxy", "python", "/app/main.py"]
