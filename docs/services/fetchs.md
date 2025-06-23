# Fetchs Service

The MCP Fetchs service provides native HTTP-based web content retrieval through the OAuth-protected gateway. Unlike mcp-fetch, this is a native streamable HTTP implementation.

## Overview

The Fetchs service is a native HTTP implementation that provides:
- Direct HTTP/HTTPS content retrieval
- Native streamable HTTP protocol support
- No stdio bridging required
- OAuth-protected access via Traefik ForwardAuth

## Architecture

The service uses:
- **Implementation**: Native streamable HTTP server
- **Protocol**: Direct HTTP without stdio bridging
- **Port**: Exposes port 3000 for HTTP access

## Configuration

### Environment Variables

```bash
# Core settings (from main .env)
MCP_PROTOCOL_VERSION=2025-06-18   # Fetchs server supports this version
MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
BASE_DOMAIN=${BASE_DOMAIN}
```

### Docker Compose

The service runs as `mcp-fetchs` in the compose stack:

```yaml
mcp-fetchs:
  build:
    context: ../
    dockerfile: mcp-fetchs/Dockerfile
  environment:
    - MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
    - MCP_PROTOCOL_VERSION=2025-06-18
```

## Usage

### Starting the Service

```bash
# Start fetchs service only
just up mcp-fetchs

# View logs
just logs mcp-fetchs

# Rebuild after changes
just rebuild mcp-fetchs
```

### API Endpoints

The fetchs service exposes the standard MCP endpoint:

```
POST https://fetchs.gateway.yourdomain.com/mcp
Authorization: Bearer <token>
Content-Type: application/json
```

### MCP Protocol

The service implements the standard MCP protocol with native HTTP support.

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

The fetchs service provides:
- Native HTTP implementation (no stdio bridging)
- Direct web content retrieval
- Potentially better performance than wrapped services
- Standard MCP error handling

## Security

Security is enforced at the gateway level:
- **Authentication**: Bearer token required, validated by Traefik ForwardAuth
- **Authorization**: Token must be valid and user must be in allowed list
- **No internal security**: The service itself has no authentication logic

## Examples

### Using mcp-streamablehttp-client

```python
# Install: pixi add mcp-streamablehttp-client
from mcp_streamablehttp_client import Client

# Initialize client with bearer token
client = Client(
    "https://fetchs.gateway.yourdomain.com/mcp",
    headers={"Authorization": f"Bearer {access_token}"}
)

# Initialize the session
await client.initialize()

# Use the fetchs server methods
# (Implementation-specific methods may vary from mcp-fetch)
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
- Check service status: `just logs mcp-fetchs`
- Verify health: `just check-health`
- Restart service: `just rebuild mcp-fetchs`

### Debugging

View service logs:

```bash
# View logs
just logs mcp-fetchs

# Follow logs
just logs -f mcp-fetchs
```

## Architecture Notes

- Native HTTP implementation without stdio bridging
- Runs on port 3000 internally
- May have different capabilities than mcp-fetch
- Authentication handled by Traefik/Auth service, not MCP service

## Comparison with mcp-fetch

| Feature | mcp-fetch | mcp-fetchs |
|---------|-----------|------------|
| Implementation | Wraps official server | Native HTTP |
| Protocol Version | 2025-03-26 | 2025-06-18 |
| Architecture | stdio → HTTP proxy | Direct HTTP |
| Performance | Proxy overhead | Native performance |

## Related Services

- [Fetch Service](fetch.md) - Official wrapped fetch implementation
- [Filesystem Service](filesystem.md) - For local file operations