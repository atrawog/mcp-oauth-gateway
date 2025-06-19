FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash mcpuser

# Set working directory
WORKDIR /app

# Copy package files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir -e .

# Create credentials directory
RUN mkdir -p /home/mcpuser/.mcp && \
    chown -R mcpuser:mcpuser /home/mcpuser/.mcp

# Switch to non-root user
USER mcpuser

# Set home directory for credential storage
ENV HOME=/home/mcpuser

# Default command
ENTRYPOINT ["mcp-http-stdio"]