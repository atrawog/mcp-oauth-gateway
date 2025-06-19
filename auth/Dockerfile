FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the mcp-oauth-dynamicclient package source
COPY ../mcp-oauth-dynamicclient /tmp/mcp-oauth-dynamicclient

# Install the mcp-oauth-dynamicclient package from source
RUN pip install --no-cache-dir /tmp/mcp-oauth-dynamicclient

# Clean up the temporary copy
RUN rm -rf /tmp/mcp-oauth-dynamicclient

# Copy the main application file
COPY main.py .

# Create non-root user
RUN useradd -m -u 1000 authuser && chown -R authuser:authuser /app
USER authuser

# The sacred OAuth service port
EXPOSE 8000

# Use uvicorn for production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]