# Time Service

The MCP Time service provides timezone-aware time operations through the OAuth-protected gateway. It wraps the official `@modelcontextprotocol/server-time` using `mcp-streamablehttp-proxy`.

## Overview

The Time service is a proxy wrapper around the official MCP time server that enables:
- Current time retrieval in any timezone
- Timezone conversions and calculations
- DST (Daylight Saving Time) handling
- OAuth-protected access via Traefik ForwardAuth

## Architecture

The service uses:
- **Official Server**: `@modelcontextprotocol/server-time` from the MCP project
- **Proxy Wrapper**: `mcp-streamablehttp-proxy` to bridge stdio to HTTP
- **Port**: Exposes port 3000 for HTTP access

## Configuration

### Environment Variables

```bash
# Core settings (from main .env)
MCP_PROTOCOL_VERSION=2025-03-26   # Time server supports this version
MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
BASE_DOMAIN=${BASE_DOMAIN}
```

### Docker Compose

The service runs as `mcp-time` in the compose stack:

```yaml
mcp-time:
  build:
    context: ../
    dockerfile: mcp-time/Dockerfile
  environment:
    - MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
    - MCP_PROTOCOL_VERSION=2025-03-26
```

## Usage

### Starting the Service

```bash
# Start time service only
just up mcp-time

# View logs
just logs mcp-time

# Rebuild after changes
just rebuild mcp-time
```

### API Endpoints

The time service exposes the standard MCP endpoint:

```
POST https://time.gateway.yourdomain.com/mcp
Authorization: Bearer <token>
Content-Type: application/json
```

### MCP Protocol

The service implements the standard MCP protocol. The specific methods available depend on the official `@modelcontextprotocol/server-time` implementation.

Example initialization:

```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
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

The features provided are those of the official MCP time server:
- Current time in various timezones
- Timezone conversion operations
- DST calculation and handling
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
    "https://time.gateway.yourdomain.com/mcp",
    headers={"Authorization": f"Bearer {access_token}"}
)

# Initialize the session
await client.initialize()

# Use the time server methods as provided by the official server
# (Refer to @modelcontextprotocol/server-time documentation for available methods)
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
- Check service status: `just logs mcp-time`
- Verify health: `just check-health`
- Restart service: `just rebuild mcp-time`

### Debugging

View service logs:

```bash
# View logs
just logs mcp-time

# Follow logs
just logs -f mcp-time
```

## Architecture Notes

- The service wraps the official `@modelcontextprotocol/server-time`
- Uses `mcp-streamablehttp-proxy` to bridge stdio to HTTP
- Runs on port 3000 internally
- Stateless service with no persistent storage
- Authentication handled by Traefik/Auth service, not MCP service

## Related Services

- [Memory Service](memory.md) - For storing time-based events
- [Sequential Thinking Service](sequentialthinking.md) - For time-based planning