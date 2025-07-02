# mcp-streamablehttp-client

The divine bridge that enables stdio-based MCP clients to communicate with StreamableHTTP servers, complete with OAuth authentication support.

## Quick Start

**Key Features:**
- Protocol translation between stdio and StreamableHTTP
- OAuth 2.0 authentication with automatic token management
- RFC 7591/7592 support for dynamic client registration
- Command-line tools for testing and management
- Claude Desktop integration ready

**Installation:**
```bash
# Via pixi (recommended)
pixi add mcp-streamablehttp-client

# Via pip
pip install mcp-streamablehttp-client

# Via Docker
docker build -t mcp-streamablehttp-client .
```

**Basic Usage:**
```bash
# Authenticate with OAuth server
mcp-streamablehttp-client --token

# Run as stdio proxy for Claude Desktop
mcp-streamablehttp-client

# Execute MCP tool directly
mcp-streamablehttp-client -c 'fetch https://example.com'
```

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation and Setup](#installation-and-setup)
4. [CLI Commands](#cli-commands)
5. [Claude Desktop Integration](#claude-desktop-integration)
6. [OAuth Flow Details](#oauth-flow-details)
7. [Protocol Bridge Implementation](#protocol-bridge-implementation)
8. [Configuration Options](#configuration-options)
9. [Session Management](#session-management)
10. [Error Handling](#error-handling)
11. [Integration Examples](#integration-examples)
12. [Security Considerations](#security-considerations)
13. [Troubleshooting](#troubleshooting)
14. [Performance Considerations](#performance-considerations)
15. [Best Practices](#best-practices)
16. [Advanced Usage Examples](#advanced-usage-examples)
17. [Limitations](#limitations)

## Overview

`mcp-streamablehttp-client` serves as a critical bridge in the MCP ecosystem, enabling stdio-based MCP clients (like Claude Desktop) to seamlessly connect to StreamableHTTP MCP servers that require OAuth authentication. It acts as a transparent protocol converter and OAuth handler, making remote authenticated MCP services appear as local stdio services.

The client handles:
- Protocol translation (stdio ↔ StreamableHTTP)
- OAuth 2.0 authentication flows
- Bearer token management
- Session handling
- Streaming responses
- Dynamic client registration (RFC 7591)
- Client management (RFC 7592)

## Architecture

### Core Purpose

```
┌─────────────────────┐     stdio      ┌──────────────────────┐     HTTP + OAuth    ┌─────────────────┐
│   Claude Desktop    │ ←------------→ │ mcp-streamablehttp-  │ ←----------------→ │  Remote MCP     │
│  (or other stdio    │   JSON-RPC     │      client          │  StreamableHTTP    │    Server       │
│    MCP client)      │                │  (Protocol Bridge)   │                    │ (OAuth Protected)│
└─────────────────────┘                └──────────────────────┘                    └─────────────────┘
```

### Key Components

```
mcp_streamablehttp_client/
├── __init__.py          # Package initialization
├── __main__.py          # Module entry point
├── cli.py               # Rich CLI interface
├── config.py            # Settings management
├── oauth.py             # OAuth client implementation
├── proxy.py             # Protocol bridge implementation
├── models.py            # Data models
└── utils.py             # Helper utilities
```

### Main Classes

```python
# Core components
MCPStreamableHTTPClient    # Main client class
StdioServerTransport       # stdio communication handler
OAuthClient               # OAuth flow implementation
TokenManager              # Token storage and refresh
StreamParser              # SSE stream parsing
```

## Installation and Setup

### Installation Options

```bash
# Using pixi (recommended)
pixi add mcp-streamablehttp-client

# Using pip
pip install mcp-streamablehttp-client

# Using Docker
docker build -t mcp-streamablehttp-client .
```

### Initial Configuration

1. **First-time Setup**:
```bash
# Authenticate with your MCP server
mcp-streamablehttp-client --token

# Or using just
just auth
```

2. **Environment Configuration**:
The tool creates a `.env` file with:
```bash
# Target server
MCP_SERVER_URL=https://mcp-fetch.yourdomain.com

# OAuth credentials (auto-generated)
MCP_CLIENT_ID=dyn_abc123...
MCP_CLIENT_SECRET=secret_xyz789...
MCP_CLIENT_ACCESS_TOKEN=eyJhbGc...
MCP_CLIENT_REFRESH_TOKEN=refresh_xyz...
MCP_CLIENT_REGISTRATION_TOKEN=reg_token123...
MCP_CLIENT_REGISTRATION_URI=https://auth.domain.com/register/dyn_abc123
```

## CLI Commands

### Authentication Commands

#### --token
Check and refresh OAuth tokens:
```bash
mcp-streamablehttp-client --token
```
- Checks current token status
- Refreshes if expired/expiring
- Initiates OAuth flow if needed

#### --test-auth
Test authentication status:
```bash
mcp-streamablehttp-client --test-auth
```
- Verifies server connectivity
- Validates current token
- Shows authentication details

#### --reset-auth
Clear all credentials:
```bash
mcp-streamablehttp-client --reset-auth
```
- Removes stored tokens
- Clears client registration
- Resets to fresh state

### MCP Operations

#### --list-tools
List available MCP tools:
```bash
mcp-streamablehttp-client --list-tools
```
Output example:
```
Available tools:
  - fetch: Retrieve content from URLs
  - search: Search for information
  - read_file: Read file contents
```

#### --list-resources
List available resources:
```bash
mcp-streamablehttp-client --list-resources
```

#### --list-prompts
List available prompts:
```bash
mcp-streamablehttp-client --list-prompts
```

### Tool Execution

#### -c, --command
Execute MCP tools directly:

**JSON Format**:
```bash
mcp-streamablehttp-client -c 'fetch {"url": "https://example.com", "headers": {"User-Agent": "Custom"}}'
```

**Key=Value Format**:
```bash
mcp-streamablehttp-client -c 'echo message="Hello World" timestamp=true'
```

**Smart Detection**:
```bash
# URLs automatically detected
mcp-streamablehttp-client -c 'fetch https://example.com'

# File paths recognized
mcp-streamablehttp-client -c 'read_file /path/to/file.txt'

# Simple strings
mcp-streamablehttp-client -c 'echo "Hello, MCP!"'
```

### Client Management (RFC 7592)

#### --get-client-info
Retrieve client registration details:
```bash
mcp-streamablehttp-client --get-client-info
```

#### --update-client
Update client registration:
```bash
mcp-streamablehttp-client --update-client "client_name=New Name,contacts=admin@example.com"
```

#### --delete-client
Delete client registration (permanent!):
```bash
mcp-streamablehttp-client --delete-client
```

### Advanced Usage

#### --raw
Send raw JSON-RPC requests:
```bash
mcp-streamablehttp-client --raw '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

#### Continuous Proxy Mode
Run as stdio proxy (default when no arguments):
```bash
mcp-streamablehttp-client
```

## Claude Desktop Integration

### Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "oauth-fetch": {
      "command": "mcp-streamablehttp-client",
      "env": {
        "MCP_SERVER_URL": "https://mcp-fetch.yourdomain.com"
      }
    },
    "oauth-filesystem": {
      "command": "mcp-streamablehttp-client",
      "env": {
        "MCP_SERVER_URL": "https://mcp-filesystem.yourdomain.com"
      }
    }
  }
}
```

### Multiple Servers

Each server needs its own `.env` file:
```bash
# For fetch service
MCP_SERVER_URL=https://mcp-fetch.yourdomain.com mcp-streamablehttp-client --token

# For filesystem service
MCP_SERVER_URL=https://mcp-filesystem.yourdomain.com mcp-streamablehttp-client --token
```

## OAuth Flow Details

### Initial Registration

1. **Discovery**: Fetches `/.well-known/oauth-authorization-server`
2. **Registration**: POST to `/register` with client metadata
3. **Storage**: Saves credentials to `.env`

### Authorization Flow

1. **Initiate**: Redirects to `/authorize` with PKCE
2. **User Auth**: GitHub OAuth authentication
3. **Callback**: Receives authorization code
4. **Token Exchange**: Trades code for tokens

### Token Management

- **Automatic Refresh**: Before expiration
- **Retry Logic**: On 401 responses
- **Graceful Degradation**: Falls back to re-auth
- **Secure Storage**: Credentials stored in .env file

### Interactive Token Generation

```bash
$ mcp-streamablehttp-client --token --server-url https://mcp.example.com/mcp

🔐 Starting OAuth flow...
🌐 Opening browser for authorization...
Please visit: https://auth.example.com/authorize?client_id=...

✅ Authorization successful!
📝 Access token saved to environment

Your token: Bearer eyJ...
```

## Protocol Bridge Implementation

### Request Flow

1. **Stdin Input**: Receives JSON-RPC from client
2. **Session Check**: Creates/retrieves MCP session
3. **HTTP Request**: Converts to StreamableHTTP
4. **Token Injection**: Adds Bearer token
5. **Response Translation**: HTTP → JSON-RPC
6. **Stdout Output**: Returns to client

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

### Error Translation

HTTP errors are translated to JSON-RPC:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": {
      "http_status": 401,
      "details": "Authentication required"
    }
  },
  "id": 1
}
```

## Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MCP_SERVER_URL` | Target MCP server URL | Yes |
| `MCP_CLIENT_ID` | OAuth client ID | Auto-generated |
| `MCP_CLIENT_SECRET` | OAuth client secret | Auto-generated |
| `MCP_CLIENT_ACCESS_TOKEN` | Current access token | Auto-generated |
| `MCP_CLIENT_REFRESH_TOKEN` | Refresh token | Auto-generated |
| `MCP_CLIENT_REGISTRATION_TOKEN` | RFC 7592 token | Auto-generated |
| `MCP_CLIENT_REGISTRATION_URI` | Management endpoint | Auto-generated |
| `MCP_CLIENT_LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | Optional |
| `MCP_DEBUG` | Enable debug logging | Optional |

### Command Line Options

| Option | Description |
|--------|-------------|
| `--env-file` | Path to .env file (default: .env) |
| `--log-level` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `--server-url` | Override server URL from .env |
| `--verbose` | Enable verbose output |

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
5. **State Preservation**: Tracks initialization state
6. **Header Forwarding**: Includes session ID in all requests

## Error Handling

### OAuth Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid/expired token | Refresh or regenerate token |
| 403 Forbidden | Insufficient scope | Check token permissions |
| Invalid redirect_uri | Mismatch with registration | Verify client configuration |
| No credentials found | Not authenticated | Run `--token` command |

### Protocol Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | Server down | Check server status |
| Invalid session | Session expired | Reinitialize connection |
| Protocol mismatch | Version incompatibility | Check supported versions |
| OAuth server not found | Discovery failure | Verify server URL |

## Integration Examples

### With Official MCP Clients

```bash
# Use with mcp CLI tool
export MCP_SERVER_URL=https://mcp.example.com/mcp
export MCP_CLIENT_ACCESS_TOKEN="Bearer eyJ..."

# The client acts as a bridge
mcp-streamablehttp-client
```

### In Python Applications

```python
import subprocess
import json

# Start the client bridge
proc = subprocess.Popen(
    ['mcp-streamablehttp-client', '--server-url', server_url],
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

### Script Integration

```python
import subprocess
import json

# Execute MCP tool
result = subprocess.run(
    ["mcp-streamablehttp-client", "-c", "fetch https://example.com"],
    capture_output=True,
    text=True
)

# Parse response
response = json.loads(result.stdout)
```

### Just Commands

The project includes helpful just recipes:

```bash
# Authenticate
just auth

# Test authentication
just test-auth

# List tools
just list-tools

# Execute command
just exec "fetch https://example.com"
just exec "echo message='Hello World'"
```

### Docker Usage

```dockerfile
FROM python:3.11-slim

RUN pip install mcp-streamablehttp-client

WORKDIR /app
COPY .env* ./

CMD ["mcp-streamablehttp-client"]
```

### Docker Compose

```yaml
services:
  mcp-client:
    build: ./mcp-streamablehttp-client
    environment:
      - MCP_SERVER_URL=${MCP_SERVER_URL}
    volumes:
      - ./.env:/app/.env:ro
    stdin_open: true
    tty: true
```

## Security Considerations

### Token Storage
- Stored in `.env` file with appropriate permissions
- Never logged or exposed in output
- Automatic cleanup on --reset-auth
- Environment variable: `MCP_CLIENT_ACCESS_TOKEN`

### HTTPS Enforcement
- SSL/TLS verification enabled by default
- Rejects self-signed certificates unless explicitly trusted
- Always use HTTPS URLs in production

### OAuth Security
- PKCE required for authorization flow
- State parameter for CSRF protection
- Secure random client credentials
- Token scope: Request minimal necessary permissions
- Token rotation: Implement regular token refresh
- Audit logging: Monitor token usage

## Troubleshooting

### Common Issues

#### "No credentials found"
```bash
# Solution: Run authentication
mcp-streamablehttp-client --token
```

#### "Token expired"
```bash
# Solution: Force refresh
mcp-streamablehttp-client --token
```

#### "OAuth server not found"
```bash
# Check server URL
echo $MCP_SERVER_URL

# Verify discovery endpoint
curl https://your-server.com/.well-known/oauth-authorization-server
```

#### "Permission denied"
- Check with administrator for access
- Verify ALLOWED_GITHUB_USERS setting

#### "Token Generation Hangs"
- Check browser opened
- Verify redirect URI accessible
- Check firewall rules

#### "Connection Errors"
- Verify server URL includes `/mcp`
- Check SSL certificates
- Test with curl first

#### "Protocol Errors"
- Enable debug logging
- Check protocol version compatibility
- Verify message format

### Debug Mode

Enable verbose logging:
```bash
export MCP_DEBUG=1
mcp-streamablehttp-client --log-level DEBUG --test-auth

# Or with environment variable
export MCP_CLIENT_LOG_LEVEL=DEBUG
mcp-streamablehttp-client --verbose
```

## Performance Considerations

### Connection Pooling
- Reuses HTTP connections
- Configurable timeout settings
- Automatic reconnection

### Token Caching
- Minimizes token refresh calls
- Checks expiration before use
- Background refresh possible

### Async Implementation
- Non-blocking I/O operations
- Concurrent request handling
- Efficient stream processing

## Best Practices

1. **Separate .env per Server**: Don't share credentials between servers
2. **Regular Token Refresh**: Use --token periodically to refresh
3. **Monitor Expiration**: Check token status regularly
4. **Secure Storage**: Protect .env files with appropriate permissions
5. **Use Just Commands**: Consistent interface across the project
6. **Enable Debug Sparingly**: Only when troubleshooting issues
7. **HTTPS Only**: Always use HTTPS URLs in production
8. **Minimal Scope**: Request only necessary permissions

## Advanced Usage Examples

### Batch Operations

```bash
# List all tools and execute one
TOOLS=$(mcp-streamablehttp-client --list-tools)
mcp-streamablehttp-client -c "fetch https://api.example.com/data"
```

### Custom Tool Wrapper

```bash
#!/bin/bash
# mcp-fetch wrapper

if [ -z "$1" ]; then
    echo "Usage: mcp-fetch <url>"
    exit 1
fi

mcp-streamablehttp-client -c "fetch $1"
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

## Testing

```bash
# Test basic connectivity
mcp-streamablehttp-client \
  --server-url https://mcp-echo.example.com/mcp \
  --test-auth

# Test with authentication
mcp-streamablehttp-client \
  --server-url https://mcp-fetch.example.com/mcp \
  --token "Bearer eyJ..." \
  --test-auth

# Test tool execution
mcp-streamablehttp-client -c "echo test=true"
```

## Limitations

1. **Single Server per Instance**: Each client connects to one server
2. **Stdio Only**: Doesn't support other MCP transports
3. **No Connection Multiplexing**: One session at a time
4. **Token Scope**: Limited to configured server
5. **No Built-in Retry**: Manual retry on failures
