# Memory Service

The MCP Memory service provides a persistent knowledge graph database through the OAuth-protected gateway. It wraps the official `@modelcontextprotocol/server-memory` using `mcp-streamablehttp-proxy`.

## Overview

The Memory service is a proxy wrapper around the official MCP memory server that enables:
- Entity and relation management in a knowledge graph
- Persistent storage of structured data
- Query capabilities for stored knowledge
- OAuth-protected access via Traefik ForwardAuth

## Architecture

The service uses:
- **Official Server**: `@modelcontextprotocol/server-memory` from the MCP project
- **Proxy Wrapper**: `mcp-streamablehttp-proxy` to bridge stdio to HTTP
- **Port**: Exposes port 3000 for HTTP access
- **Storage**: Persistent volume for knowledge graph data

## Configuration

### Environment Variables

```bash
# Core settings (from main .env)
MCP_PROTOCOL_VERSION=2024-11-05   # Memory server supports this version
MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
BASE_DOMAIN=${BASE_DOMAIN}
```

### Docker Compose

The service runs as `mcp-memory` in the compose stack with persistent storage:

```yaml
mcp-memory:
  build:
    context: ../
    dockerfile: mcp-memory/Dockerfile
  environment:
    - MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
    - MCP_PROTOCOL_VERSION=2024-11-05
  volumes:
    - mcp-memory-data:/workspace
```

## Usage

### Starting the Service

```bash
# Start memory service only
just up mcp-memory

# View logs
just logs mcp-memory

# Rebuild after changes
just rebuild mcp-memory
```

### API Endpoints

The memory service exposes the standard MCP endpoint:

```
POST https://memory.gateway.yourdomain.com/mcp
Authorization: Bearer <token>
Content-Type: application/json
```

### MCP Protocol

The service implements the standard MCP protocol. The specific methods available depend on the official `@modelcontextprotocol/server-memory` implementation.

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

The features provided are those of the official MCP memory server:
- Knowledge graph entity management
- Relation creation and querying
- Persistent storage across sessions
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
    "https://memory.gateway.yourdomain.com/mcp",
    headers={"Authorization": f"Bearer {access_token}"}
)

# Initialize the session
await client.initialize()

# Use the memory server methods as provided by the official server
# (Refer to @modelcontextprotocol/server-memory documentation for available methods)
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
- Check service status: `just logs mcp-memory`
- Verify health: `just check-health`
- Restart service: `just rebuild mcp-memory`

### Debugging

View service logs:

```bash
# View logs
just logs mcp-memory

# Follow logs
just logs -f mcp-memory
```

## Architecture Notes

- The service wraps the official `@modelcontextprotocol/server-memory`
- Uses `mcp-streamablehttp-proxy` to bridge stdio to HTTP
- Runs on port 3000 internally
- Data persists in the `mcp-memory-data` Docker volume
- Authentication handled by Traefik/Auth service, not MCP service

## Related Services

- [Fetch Service](fetch.md) - For retrieving data to store
- [Filesystem Service](filesystem.md) - For file-based data management
