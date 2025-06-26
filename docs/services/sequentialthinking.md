# Sequential Thinking Service

The MCP Sequential Thinking service provides structured problem-solving capabilities through the OAuth-protected gateway. It wraps the official `@modelcontextprotocol/server-sequentialthinking` using `mcp-streamablehttp-proxy`.

## Overview

The Sequential Thinking service is a proxy wrapper around the official MCP sequential thinking server that enables:
- Step-by-step problem decomposition
- Revision and branching of thought processes
- State management for complex reasoning
- OAuth-protected access via Traefik ForwardAuth

## Architecture

The service uses:
- **Official Server**: `@modelcontextprotocol/server-sequentialthinking` from the MCP project
- **Proxy Wrapper**: `mcp-streamablehttp-proxy` to bridge stdio to HTTP
- **Port**: Exposes port 3000 for HTTP access

## Configuration

### Environment Variables

```bash
# Core settings (from main .env)
MCP_PROTOCOL_VERSION=2024-11-05   # Sequential thinking server supports this version
MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
BASE_DOMAIN=${BASE_DOMAIN}
```

### Docker Compose

The service runs as `mcp-sequentialthinking` in the compose stack:

```yaml
mcp-sequentialthinking:
  build:
    context: ../
    dockerfile: mcp-sequentialthinking/Dockerfile
  environment:
    - MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
    - MCP_PROTOCOL_VERSION=2024-11-05
```

## Usage

### Starting the Service

```bash
# Start sequential thinking service only
just up mcp-sequentialthinking

# View logs
just logs mcp-sequentialthinking

# Rebuild after changes
just rebuild mcp-sequentialthinking
```

### API Endpoints

The sequential thinking service exposes the standard MCP endpoint:

```
POST https://sequentialthinking.gateway.yourdomain.com/mcp
Authorization: Bearer <token>
Content-Type: application/json
```

### MCP Protocol

The service implements the standard MCP protocol. The specific methods available depend on the official `@modelcontextprotocol/server-sequentialthinking` implementation.

Example initialization:

```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
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

The features provided are those of the official MCP sequential thinking server:
- Break complex problems into manageable steps
- Revise and refine reasoning chains
- Branch thought processes for exploration
- Maintain state across reasoning sessions
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
    "https://sequentialthinking.gateway.yourdomain.com/mcp",
    headers={"Authorization": f"Bearer {access_token}"}
)

# Initialize the session
await client.initialize()

# Use the sequential thinking server methods as provided by the official server
# (Refer to @modelcontextprotocol/server-sequentialthinking documentation for available methods)
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
- Check service status: `just logs mcp-sequentialthinking`
- Verify health: `just check-health`
- Restart service: `just rebuild mcp-sequentialthinking`

### Debugging

View service logs:

```bash
# View logs
just logs mcp-sequentialthinking

# Follow logs
just logs -f mcp-sequentialthinking
```

## Architecture Notes

- The service wraps the official `@modelcontextprotocol/server-sequentialthinking`
- Uses `mcp-streamablehttp-proxy` to bridge stdio to HTTP
- Runs on port 3000 internally
- Maintains session state for reasoning chains
- Authentication handled by Traefik/Auth service, not MCP service

## Related Services

- [Memory Service](memory.md) - For storing reasoning results
- [Time Service](time.md) - For time-based planning
