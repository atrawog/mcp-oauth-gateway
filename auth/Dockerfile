FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly (no package installation)
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    authlib \
    httpx \
    redis \
    pydantic-settings \
    PyJWT \
    cryptography \
    coverage \
    python-multipart

# Create keys directory for RS256 - THE BLESSED KEY SANCTUARY!
RUN mkdir -p /app/keys

# Create non-root user
RUN useradd -m -u 1000 authuser && chown -R authuser:authuser /app

# Copy the source code directly to /app
COPY mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient /app/mcp_oauth_dynamicclient

USER authuser

# The sacred OAuth service port
EXPOSE 8000

# Run from source with PYTHONPATH
ENV PYTHONPATH=/app:${PYTHONPATH}

# Run the server directly from source using CLI
# Coverage will be enabled via PYTHONPATH=/coverage-spy
CMD ["python", "-m", "mcp_oauth_dynamicclient.cli", "--host", "0.0.0.0", "--port", "8000"]
