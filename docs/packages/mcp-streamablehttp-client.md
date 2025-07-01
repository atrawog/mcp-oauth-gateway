# mcp-streamablehttp-client

The divine bridge that enables stdio-based MCP clients to communicate with StreamableHTTP servers, complete with OAuth authentication support.

## Overview

`mcp-streamablehttp-client` serves as a protocol translator, allowing traditional stdio-based MCP clients (like Claude Desktop) to connect to HTTP-based MCP servers. It handles:

- Protocol translation (stdio ↔ StreamableHTTP)
- OAuth 2.0 authentication flows
- Bearer token management
- Session handling
- Streaming responses

## Key Features

### Protocol Bridge
- Translates stdio JSON-RPC to HTTP requests
- Maintains session state across requests
- Handles streaming responses properly
- Preserves all MCP protocol semantics

### OAuth Integration
- Built-in OAuth 2.0 client
- PKCE support for secure flows
- Token persistence and refresh
- Interactive authorization flow

### CLI Interface
- Command-line tool for testing
- OAuth token generation utility
- Direct server communication
- Debug and verbose modes

## Architecture

```python
# Core components
MCPStreamableHTTPClient    # Main client class
StdioServerTransport       # stdio communication handler
OAuthClient               # OAuth flow implementation
TokenManager              # Token storage and refresh
StreamParser              # SSE stream parsing
```

## Installation

```bash
# Via pixi (recommended)
pixi install

# Or standalone
pip install mcp-streamablehttp-client
```

## Usage

### As a CLI Tool

```bash
# Basic connection (no auth)
mcp-streamablehttp-client --server-url https://mcp-echo.example.com/mcp

# With OAuth token
mcp-streamablehttp-client \
  --server-url https://mcp-fetch.example.com/mcp \
  --token "Bearer eyJ..."

# Generate OAuth token interactively
mcp-streamablehttp-client \
  --server-url https://mcp-fetch.example.com/mcp \
  --token
```

### In Claude Desktop Configuration

```json
{
  "mcpServers": {
    "mcp-fetch": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--server-url", "https://mcp-fetch.example.com/mcp",
        "--token", "Bearer eyJ..."
      ]
    }
  }
}
```

### Programmatic Usage

```python
from mcp_streamablehttp_client import MCPStreamableHTTPClient

# Create client
client = MCPStreamableHTTPClient(
    server_url="https://mcp-service.example.com/mcp",
    token="Bearer eyJ..."
)

# Run the client (blocks)
client.run()
```

## OAuth Token Flow

### 1. Interactive Token Generation

```bash
$ mcp-streamablehttp-client --token --server-url https://mcp.example.com/mcp

🔐 Starting OAuth flow...
🌐 Opening browser for authorization...
Please visit: https://auth.example.com/authorize?client_id=...

✅ Authorization successful!
📝 Access token saved to environment

Your token: Bearer eyJ...
```

### 2. Token Storage

Tokens can be stored in:
- Environment variable: `MCP_AUTH_TOKEN`
- Config file: `~/.mcp/tokens.json`
- Command line argument

### 3. Token Refresh

The client automatically handles token refresh when:
- Token is near expiration
- Server returns 401 Unauthorized
- Refresh token is available

## Protocol Translation

### stdio to HTTP

```
stdio client → JSON-RPC → client → HTTP POST → server
                                ↓
stdio client ← JSON-RPC ← client ← SSE stream ← server
```

### Message Flow Example

1. **Client sends (stdio)**:
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {}
  },
  "id": 1
}
```

2. **Client translates to HTTP**:
```http
POST /mcp HTTP/1.1
Host: mcp-service.example.com
Authorization: Bearer eyJ...
Content-Type: application/json

{"jsonrpc": "2.0", "method": "initialize", ...}
```

3. **Server responds (SSE)**:
```
event: message
data: {"jsonrpc": "2.0", "result": {...}, "id": 1}
```

4. **Client outputs (stdio)**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2025-06-18",
    "capabilities": {...}
  },
  "id": 1
}
```

## Configuration

### Environment Variables

```bash
# OAuth token
MCP_AUTH_TOKEN=Bearer eyJ...

# Server URL (default for CLI)
MCP_SERVER_URL=https://mcp-service.example.com/mcp

# OAuth endpoints (auto-discovered)
OAUTH_AUTHORIZATION_ENDPOINT=https://auth.example.com/authorize
OAUTH_TOKEN_ENDPOINT=https://auth.example.com/token

# Logging
MCP_CLIENT_LOG_LEVEL=INFO
```

### Configuration File

```json
{
  "servers": {
    "mcp-fetch": {
      "url": "https://mcp-fetch.example.com/mcp",
      "token": "Bearer eyJ..."
    },
    "mcp-memory": {
      "url": "https://mcp-memory.example.com/mcp",
      "token": "Bearer eyJ..."
    }
  }
}
```

## Session Management

The client handles MCP sessions automatically:

1. **Session Creation**: On successful initialization
2. **Session ID Tracking**: Via `Mcp-Session-Id` header
3. **Session Persistence**: Across multiple requests
4. **Session Cleanup**: On shutdown or error

## Error Handling

### OAuth Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid/expired token | Refresh or regenerate token |
| 403 Forbidden | Insufficient scope | Check token permissions |
| Invalid redirect_uri | Mismatch with registration | Verify client configuration |

### Protocol Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | Server down | Check server status |
| Invalid session | Session expired | Reinitialize connection |
| Protocol mismatch | Version incompatibility | Check supported versions |

## Integration Examples

### With Official MCP Clients

```bash
# Use with mcp CLI tool
export MCP_SERVER_URL=https://mcp.example.com/mcp
export MCP_AUTH_TOKEN="Bearer eyJ..."

# The client acts as a bridge
mcp-streamablehttp-client
```

### In Python Applications

```python
import subprocess
import json

# Start the client bridge
proc = subprocess.Popen(
    ['mcp-streamablehttp-client', '--server-url', server_url, '--token', token],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Send MCP messages
message = {"jsonrpc": "2.0", "method": "initialize", "id": 1}
proc.stdin.write(json.dumps(message) + '\n')
proc.stdin.flush()

# Read responses
response = json.loads(proc.stdout.readline())
```

## Debugging

### Enable Debug Logging

```bash
# Verbose output
mcp-streamablehttp-client --verbose

# Debug logging
export MCP_CLIENT_LOG_LEVEL=DEBUG
```

### Common Issues

1. **Token Generation Hangs**
   - Check browser opened
   - Verify redirect URI accessible
   - Check firewall rules

2. **Connection Errors**
   - Verify server URL includes `/mcp`
   - Check SSL certificates
   - Test with curl first

3. **Protocol Errors**
   - Enable debug logging
   - Check protocol version compatibility
   - Verify message format

## Testing

```bash
# Test basic connectivity
mcp-streamablehttp-client \
  --server-url https://mcp-echo.example.com/mcp \
  --test

# Test with authentication
mcp-streamablehttp-client \
  --server-url https://mcp-fetch.example.com/mcp \
  --token "Bearer eyJ..." \
  --test
```

## Security Considerations

1. **Token Storage**: Use secure storage for tokens
2. **HTTPS Only**: Always use HTTPS URLs
3. **Token Scope**: Request minimal necessary permissions
4. **Token Rotation**: Implement regular token refresh
5. **Audit Logging**: Monitor token usage
