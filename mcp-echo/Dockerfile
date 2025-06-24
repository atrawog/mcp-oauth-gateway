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
EXPOSE 8000

# Set default environment variables with debug enabled
ENV MCP_ECHO_HOST=0.0.0.0
ENV MCP_ECHO_PORT=8000
ENV MCP_ECHO_DEBUG=true

# Run the server
CMD ["mcp-echo-streamablehttp-server-stateless"]