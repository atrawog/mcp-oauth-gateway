FROM python:3.12-alpine

WORKDIR /app

# Install necessary packages for Playwright and Node.js
RUN apk add --no-cache \
    bash \
    curl \
    nodejs \
    npm \
    # Dependencies for Playwright browsers
    chromium \
    chromium-chromedriver \
    firefox \
    # Additional dependencies for browser automation
    ttf-liberation \
    font-noto-emoji \
    # System utilities
    ca-certificates \
    tzdata

# Install playwright-mcp via npm
RUN npm install -g @playwright/mcp@latest

# Set up Playwright browsers after installing the package
RUN npx @playwright/mcp --version 2>/dev/null || npx playwright install chromium

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
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Health check to verify the server is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Create a startup script for playwright-mcp
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'exec mcp-streamablehttp-proxy npx @playwright/mcp@latest --headless --browser=chromium' >> /app/start.sh && \
    chmod +x /app/start.sh

# Use mcp-streamablehttp-proxy to wrap the playwright-mcp server
CMD ["/app/start.sh"]