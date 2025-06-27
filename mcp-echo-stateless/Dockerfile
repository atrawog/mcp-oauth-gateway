FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package files from parent directory
COPY mcp-echo-streamablehttp-server-stateless/pyproject.toml ./
COPY mcp-echo-streamablehttp-server-stateless/src/ ./src/
COPY mcp-echo-streamablehttp-server-stateless/README.md ./

# Install the package
RUN pip install --no-cache-dir -e .

# Expose the default port
EXPOSE 3000

# Set default environment variables with debug enabled
ENV MCP_ECHO_HOST=0.0.0.0
ENV MCP_ECHO_PORT=3000
ENV MCP_ECHO_DEBUG=true
ENV MCP_PROTOCOL_VERSIONS_SUPPORTED=2025-06-18,2025-03-26,2024-11-05

# Run the server
CMD ["mcp-echo-streamablehttp-server-stateless"]
