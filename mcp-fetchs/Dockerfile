FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files from the Python package directory
COPY mcp-fetch-streamablehttp-server/pyproject.toml ./
COPY mcp-fetch-streamablehttp-server/src/ ./src/

# Upgrade pip and install wheel
RUN pip install --upgrade pip wheel

# Install the package and dependencies with verbose output
RUN pip install --no-cache-dir -v -e . || (echo "Installation failed, trying individual packages" && \
    pip install --no-cache-dir mcp httpx pydantic pydantic-settings python-dotenv beautifulsoup4 aiofiles uvloop uvicorn fastapi && \
    pip install --no-cache-dir robotspy || echo "Warning: robotspy installation failed")

# Add non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=3000
ENV MCP_FETCH_PROTOCOL_VERSION=2025-06-18

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Run the server
CMD ["python", "-m", "mcp_fetch_streamablehttp_server"]
