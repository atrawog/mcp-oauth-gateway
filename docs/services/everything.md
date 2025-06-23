# Everything Service

The MCP Everything service is a test and demonstration server providing various utility functions through the OAuth-protected gateway. This is a native streamable HTTP implementation designed for testing and development.

## Overview

The Everything service is a native HTTP implementation that provides:
- Echo functionality for testing
- Math operations
- Environment information
- Test tools and utilities
- OAuth-protected access via Traefik ForwardAuth

## Architecture

The service uses:
- **Implementation**: Native streamable HTTP server
- **Protocol**: Direct HTTP without stdio bridging
- **Port**: Exposes port 3000 for HTTP access
- **Purpose**: Testing and development

## Configuration

### Environment Variables

```bash
# Core settings (from main .env)
MCP_PROTOCOL_VERSION=2025-06-18   # Everything server supports this version
MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
BASE_DOMAIN=${BASE_DOMAIN}
```

### Docker Compose

The service runs as `mcp-everything` in the compose stack:

```yaml
mcp-everything:
  build:
    context: ../
    dockerfile: mcp-everything/Dockerfile
  environment:
    - MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}
    - MCP_PROTOCOL_VERSION=2025-06-18
```

## Usage

### Starting the Service

```bash
# Start everything service only
just up mcp-everything

# View logs
just logs mcp-everything

# Rebuild after changes
just rebuild mcp-everything
```

### API Endpoints

The everything service exposes the standard MCP endpoint:

```
POST https://everything.gateway.yourdomain.com/mcp
Authorization: Bearer <token>
Content-Type: application/json
```

### MCP Protocol

The service implements the standard MCP protocol with test utilities.

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

The everything service provides test utilities:
- **Echo Service** - Returns input for testing
- **Math Operations** - Basic calculations
- **Environment Info** - System information
- **Test Tools** - Various testing utilities
- **Protocol Validation** - MCP compliance testing

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
    "https://everything.gateway.yourdomain.com/mcp",
    headers={"Authorization": f"Bearer {access_token}"}
)

# Initialize the session
await client.initialize()

# Use the everything server test methods
# Common test operations include echo, math, and environment queries
```

### Testing with cURL

```bash
# Test echo functionality
curl -X POST https://everything.gateway.yourdomain.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "echo",
    "params": {"message": "Hello, MCP!"},
    "id": 1
  }'
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
- Check service status: `just logs mcp-everything`
- Verify health: `just check-health`
- Restart service: `just rebuild mcp-everything`

### Debugging

View service logs:

```bash
# View logs
just logs mcp-everything

# Follow logs
just logs -f mcp-everything
```

## Architecture Notes

- Native HTTP implementation for testing
- Runs on port 3000 internally
- Designed for protocol testing and development
- Stateless operation
- Authentication handled by Traefik/Auth service, not MCP service

## Use Cases

1. **Protocol Testing** - Validate MCP client implementations
2. **Integration Testing** - Test gateway authentication flow
3. **Development** - Quick testing of MCP concepts
4. **Debugging** - Echo and environment information

## Testing Features

The service is particularly useful for:
- Verifying OAuth token flow
- Testing MCP protocol compliance
- Debugging client implementations
- Performance benchmarking

## Related Services

- [Fetch Service](fetch.md) - For production web content retrieval
- [Fetchs Service](fetchs.md) - Native fetch implementation