# Playwright Service

The MCP Playwright service provides browser automation capabilities through the OAuth-protected gateway. It wraps the official `@modelcontextprotocol/server-playwright` using `mcp-streamablehttp-proxy`.

## Overview

The Playwright service is a proxy wrapper around the official MCP playwright server that enables:
- Browser automation and control
- Web page screenshot capture
- JavaScript execution in browser context
- OAuth-protected access via Traefik ForwardAuth

## Architecture

The service uses:
- **Official Server**: `@modelcontextprotocol/server-playwright` from the MCP project
- **Proxy Wrapper**: `mcp-streamablehttp-proxy` to bridge stdio to HTTP
- **Port**: Exposes port 3000 for HTTP access
- **Browser**: Includes Chromium browser for automation

## Configuration

### Environment Variables

```bash
# Core settings (from main .env)
MCP_PROTOCOL_VERSION=2025-06-18   # Playwright server supports this version
MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
BASE_DOMAIN=${BASE_DOMAIN}
```

### Docker Compose

The service runs as `mcp-playwright` in the compose stack:

```yaml
mcp-playwright:
  build:
    context: ../
    dockerfile: mcp-playwright/Dockerfile
  environment:
    - MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
    - MCP_PROTOCOL_VERSION=2025-06-18
```

## Usage

### Starting the Service

```bash
# Start playwright service only
just up mcp-playwright

# View logs
just logs mcp-playwright

# Rebuild after changes
just rebuild mcp-playwright
```

### API Endpoints

The playwright service exposes the standard MCP endpoint:

```
POST https://playwright.gateway.yourdomain.com/mcp
Authorization: Bearer <token>
Content-Type: application/json
```

### MCP Protocol

The service implements the standard MCP protocol. The specific methods available depend on the official `@modelcontextprotocol/server-playwright` implementation.

Example initialization:

```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {
      "name": "your-client",
      "version": "1.0"
    }
  },
  "id": 1
}
```

## Features

The features provided are those of the official MCP playwright server:
- Browser automation and control
- Screenshot capture of web pages
- JavaScript execution in page context
- Web testing and validation
- Standard MCP error handling

## Security

Security is enforced at the gateway level:
- **Authentication**: Bearer token required, validated by Traefik ForwardAuth
- **Authorization**: Token must be valid and user must be in allowed list
- **No internal security**: The service itself has no authentication logic

**Note**: This service has elevated capabilities and should be used carefully. Consider disabling it if not needed:
```bash
MCP_PLAYWRIGHT_ENABLED=false
```

## Examples

### Using mcp-streamablehttp-client

```python
# Install: pixi add mcp-streamablehttp-client
from mcp_streamablehttp_client import Client

# Initialize client with bearer token
client = Client(
    "https://playwright.gateway.yourdomain.com/mcp",
    headers={"Authorization": f"Bearer {access_token}"}
)

# Initialize the session
await client.initialize()

# Use the playwright server methods as provided by the official server
# (Refer to @modelcontextprotocol/server-playwright documentation for available methods)
```

## Troubleshooting

### Common Issues

#### 401 Unauthorized

**Cause**: Invalid or expired bearer token

**Solution**: 
- Verify token with `just validate-tokens`
- Generate new token with `just generate-github-token`

#### Connection Refused

**Cause**: Service not running or unhealthy

**Solution**:
- Check service status: `just logs mcp-playwright`
- Verify health: `just check-health`
- Restart service: `just rebuild mcp-playwright`

#### Browser Launch Failures

**Cause**: Resource constraints or missing dependencies

**Solution**:
- Ensure adequate memory (requires more resources than other services)
- Check Docker resource limits
- View detailed error logs

### Debugging

View service logs:

```bash
# View logs
just logs mcp-playwright

# Follow logs
just logs -f mcp-playwright
```

## Architecture Notes

- The service wraps the official `@modelcontextprotocol/server-playwright`
- Uses `mcp-streamablehttp-proxy` to bridge stdio to HTTP
- Runs on port 3000 internally
- Includes Chromium browser for automation
- Resource-intensive - consider disabling if not needed
- Authentication handled by Traefik/Auth service, not MCP service

## Resource Considerations

This service is resource-intensive due to browser automation:
- Higher memory usage (browser processes)
- Higher CPU usage (rendering)
- Slower startup time (browser initialization)

Consider disabling if not actively used:
```bash
MCP_PLAYWRIGHT_ENABLED=false
```

## Related Services

- [Fetch Service](fetch.md) - For simpler HTTP requests without browser
- [Tmux Service](tmux.md) - For terminal automation