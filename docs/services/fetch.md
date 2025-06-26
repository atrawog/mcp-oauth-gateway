# Fetch Service

The MCP Fetch service provides secure web content retrieval capabilities through the OAuth-protected gateway. It wraps the official `@modelcontextprotocol/server-fetch` using `mcp-streamablehttp-proxy`.

## Overview

The Fetch service is a proxy wrapper around the official MCP fetch server that enables:
- HTTP/HTTPS content retrieval through MCP protocol
- OAuth-protected access via Traefik ForwardAuth
- Standard MCP protocol compliance

## Architecture

The service uses:
- **Official Server**: `@modelcontextprotocol/server-fetch` from the MCP project
- **Proxy Wrapper**: `mcp-streamablehttp-proxy` to bridge stdio to HTTP
- **Port**: Exposes port 3000 for HTTP access

## Configuration

### Environment Variables

```bash
# Core settings (from main .env)
MCP_PROTOCOL_VERSION=2025-03-26   # Hardcoded - fetch server only supports this version
MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
BASE_DOMAIN=${BASE_DOMAIN}
```

### Docker Compose

The service runs as `mcp-fetch` in the compose stack:

```yaml
mcp-fetch:
  build:
    context: ../
    dockerfile: mcp-fetch/Dockerfile
  environment:
    - MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
    - MCP_PROTOCOL_VERSION=2025-03-26
```

## Usage

### Starting the Service

```bash
# Start fetch service only
just up mcp-fetch

# View logs
just logs mcp-fetch

# Rebuild after changes
just rebuild mcp-fetch
```

### API Endpoints

The fetch service exposes the standard MCP endpoint:

```
POST https://mcp-fetch.gateway.yourdomain.com/mcp
Authorization: Bearer <token>
Content-Type: application/json
```

### MCP Protocol

The service implements the standard MCP protocol. The specific methods available depend on the official `@modelcontextprotocol/server-fetch` implementation.

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

The features provided are those of the official MCP fetch server:
- Web content retrieval via MCP protocol
- Standard MCP error handling
- Session management via Mcp-Session-Id headers

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
    "https://fetch.gateway.yourdomain.com/mcp",
    headers={"Authorization": f"Bearer {access_token}"}
)

# Initialize the session
await client.initialize()

# Use the fetch server methods as provided by the official server
# (Refer to @modelcontextprotocol/server-fetch documentation for available methods)
```

### Direct HTTP Request

```bash
# Initialize session
curl -X POST https://fetch.gateway.yourdomain.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {"name": "curl-client", "version": "1.0"}
    },
    "id": 1
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
- Check service status: `just logs mcp-fetch`
- Verify health: `just check-health`
- Restart service: `just rebuild mcp-fetch`

#### MCP Protocol Errors

**Cause**: Invalid JSON-RPC format or unsupported method

**Solution**:
- Ensure proper JSON-RPC 2.0 format
- Check protocol version matches (2025-03-26)
- Refer to official MCP documentation

### Debugging

View service logs:

```bash
# View logs
just logs mcp-fetch

# Follow logs
just logs -f mcp-fetch

# Check service health
just check-health
```

## Best Practices

1. **Use the official client library** - `mcp-streamablehttp-client` for Python
2. **Handle MCP sessions properly** - Initialize before making requests
3. **Include required headers** - Authorization and Content-Type
4. **Follow MCP protocol** - Use correct JSON-RPC format

## Architecture Notes

- The service wraps the official `@modelcontextprotocol/server-fetch`
- Uses `mcp-streamablehttp-proxy` to bridge stdio to HTTP
- Runs on port 3000 internally
- Authentication handled by Traefik/Auth service, not MCP service

## Related Services

- [Filesystem Service](filesystem.md) - For local file operations
- [Memory Service](memory.md) - For caching fetched content
