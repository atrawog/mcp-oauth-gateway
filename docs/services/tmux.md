# Tmux Service

The MCP Tmux service provides terminal session management capabilities through the OAuth-protected gateway. It wraps the official `@modelcontextprotocol/server-tmux` using `mcp-streamablehttp-proxy`.

## Overview

The Tmux service is a proxy wrapper around the official MCP tmux server that enables:
- Terminal session creation and management
- Window and pane control
- Command execution in sessions
- OAuth-protected access via Traefik ForwardAuth

## Architecture

The service uses:
- **Official Server**: `@modelcontextprotocol/server-tmux` from the MCP project
- **Proxy Wrapper**: `mcp-streamablehttp-proxy` to bridge stdio to HTTP
- **Port**: Exposes port 3000 for HTTP access
- **Tmux**: Includes tmux for terminal multiplexing

## Configuration

### Environment Variables

```bash
# Core settings (from main .env)
MCP_PROTOCOL_VERSION=2025-06-18   # Tmux server supports this version
MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
BASE_DOMAIN=${BASE_DOMAIN}
```

### Docker Compose

The service runs as `mcp-tmux` in the compose stack:

```yaml
mcp-tmux:
  build:
    context: ../
    dockerfile: mcp-tmux/Dockerfile
  environment:
    - MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
    - MCP_PROTOCOL_VERSION=2025-06-18
```

## Usage

### Starting the Service

```bash
# Start tmux service only
just up mcp-tmux

# View logs
just logs mcp-tmux

# Rebuild after changes
just rebuild mcp-tmux
```

### API Endpoints

The tmux service exposes the standard MCP endpoint:

```
POST https://tmux.gateway.yourdomain.com/mcp
Authorization: Bearer <token>
Content-Type: application/json
```

### MCP Protocol

The service implements the standard MCP protocol. The specific methods available depend on the official `@modelcontextprotocol/server-tmux` implementation.

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

The features provided are those of the official MCP tmux server:
- Create and manage tmux sessions
- Window and pane management
- Execute commands in sessions
- Session persistence and attachment
- Standard MCP error handling

## Security

Security is enforced at the gateway level:
- **Authentication**: Bearer token required, validated by Traefik ForwardAuth
- **Authorization**: Token must be valid and user must be in allowed list
- **No internal security**: The service itself has no authentication logic

**Note**: This service has elevated capabilities and should be used carefully. Consider disabling it if not needed:
```bash
MCP_TMUX_ENABLED=false
```

## Examples

### Using mcp-streamablehttp-client

```python
# Install: pixi add mcp-streamablehttp-client
from mcp_streamablehttp_client import Client

# Initialize client with bearer token
client = Client(
    "https://tmux.gateway.yourdomain.com/mcp",
    headers={"Authorization": f"Bearer {access_token}"}
)

# Initialize the session
await client.initialize()

# Use the tmux server methods as provided by the official server
# (Refer to @modelcontextprotocol/server-tmux documentation for available methods)
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
- Check service status: `just logs mcp-tmux`
- Verify health: `just check-health`
- Restart service: `just rebuild mcp-tmux`

#### Session Creation Failures

**Cause**: Tmux configuration or resource issues

**Solution**:
- Check tmux is properly installed in container
- Verify resource limits
- Review detailed error logs

### Debugging

View service logs:

```bash
# View logs
just logs mcp-tmux

# Follow logs
just logs -f mcp-tmux
```

## Architecture Notes

- The service wraps the official `@modelcontextprotocol/server-tmux`
- Uses `mcp-streamablehttp-proxy` to bridge stdio to HTTP
- Runs on port 3000 internally
- Includes tmux for terminal multiplexing
- Sessions persist within container lifetime
- Authentication handled by Traefik/Auth service, not MCP service

## Security Considerations

This service provides terminal access capabilities:
- Can execute arbitrary commands in sessions
- Has access to container filesystem
- Should be restricted to trusted users

Consider disabling if not actively used:
```bash
MCP_TMUX_ENABLED=false
```

## Related Services

- [Playwright Service](playwright.md) - For browser automation
- [Filesystem Service](filesystem.md) - For direct file operations