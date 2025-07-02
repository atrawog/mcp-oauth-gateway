# MCP StreamableHTTP Client

A bridge client that enables local MCP (Model Context Protocol) clients like Claude Desktop to connect to remote MCP servers that use StreamableHTTP transport and require OAuth authentication.

## Overview

The `mcp-streamablehttp-client` acts as a protocol bridge, converting between:
- **stdio** (standard input/output) - used by local MCP clients
- **StreamableHTTP** - used by remote MCP servers with OAuth protection

This enables seamless integration of OAuth-protected MCP services with tools that only support stdio-based MCP servers.

## Features

- **OAuth 2.0 Authentication** - Full support for dynamic client registration (RFC 7591) and management (RFC 7592)
- **Automatic Token Management** - Handles token refresh, storage, and expiration
- **Protocol Bridging** - Transparent conversion between stdio and StreamableHTTP
- **Session Management** - Maintains MCP sessions across protocol boundaries
- **Smart Command Parsing** - Flexible argument formats for easy tool usage
- **Claude Desktop Integration** - Direct configuration support

## Installation

### Using pixi (Recommended)

```bash
pixi add --pypi mcp-streamablehttp-client
```

### Using pip

```bash
pip install mcp-streamablehttp-client
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install the package
RUN pip install mcp-streamablehttp-client

# Set working directory
WORKDIR /app

# Copy .env file (if exists)
COPY .env* ./

# Run the client
CMD ["mcp-streamablehttp-client"]
```

### Using Docker Compose

```yaml
services:
  mcp-client:
    image: mcp-streamablehttp-client:latest
    build:
      context: ./mcp-streamablehttp-client
    environment:
      - MCP_SERVER_URL=${MCP_SERVER_URL}
    volumes:
      - ./.env:/app/.env:ro
    stdin_open: true
    tty: true
```

```bash
# Build and run with docker-compose
docker-compose up -d
```

## Quick Start

### 1. Initial Setup

First, authenticate with your MCP server:

```bash
# Using just (recommended)
just auth

# Or directly
mcp-streamablehttp-client --token
```

This will guide you through the OAuth flow and save your credentials to `.env`.

### 2. Test Connection

Verify your authentication:

```bash
just test-auth
```

### 3. Use with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-oauth-server": {
      "command": "mcp-streamablehttp-client",
      "env": {
        "MCP_SERVER_URL": "https://mcp-fetch.yourdomain.com"
      }
    }
  }
}
```

### 4. Execute Commands

Run MCP tool commands:

```bash
# List available tools
just list-tools

# Execute a tool
just exec "fetch https://example.com"
just exec "echo message='Hello World'"
```

## Configuration

All configuration is done through environment variables in `.env`:

| Variable | Description | Required |
|----------|-------------|----------|
| `MCP_SERVER_URL` | Target MCP server URL | Yes |
| `MCP_CLIENT_ID` | OAuth client ID | Auto-generated |
| `MCP_CLIENT_SECRET` | OAuth client secret | Auto-generated |
| `MCP_CLIENT_ACCESS_TOKEN` | Current access token | Auto-generated |
| `MCP_CLIENT_REFRESH_TOKEN` | Refresh token | Auto-generated |
| `MCP_CLIENT_REGISTRATION_TOKEN` | RFC 7592 management token | Auto-generated |
| `MCP_CLIENT_REGISTRATION_URI` | RFC 7592 management endpoint | Auto-generated |

## Usage

### CLI Commands

#### Authentication Commands

```bash
# Setup or refresh OAuth tokens
mcp-streamablehttp-client --token

# Test authentication status
mcp-streamablehttp-client --test-auth

# Clear all credentials
mcp-streamablehttp-client --reset-auth
```

#### MCP Commands

```bash
# List available tools
mcp-streamablehttp-client --list-tools

# List available resources
mcp-streamablehttp-client --list-resources

# List available prompts
mcp-streamablehttp-client --list-prompts

# Execute a tool command
mcp-streamablehttp-client -c "tool_name arguments"
```

#### Client Management (RFC 7592)

```bash
# Get client registration info
mcp-streamablehttp-client --get-client-info

# Update client registration
mcp-streamablehttp-client --update-client "client_name=New Name,contacts=admin@example.com"

# Delete client registration
mcp-streamablehttp-client --delete-client
```

#### Advanced Usage

```bash
# Send raw JSON-RPC request
mcp-streamablehttp-client --raw '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'

# Run as continuous proxy (for Claude Desktop)
mcp-streamablehttp-client
```

### Command Argument Formats

The client supports multiple argument formats for flexibility:

```bash
# JSON format (for complex arguments)
mcp-streamablehttp-client -c 'tool {"key": "value", "nested": {"foo": "bar"}}'

# Key=value format
mcp-streamablehttp-client -c 'tool key1=value1 key2=value2'

# Smart detection (URLs, paths, etc.)
mcp-streamablehttp-client -c 'fetch https://example.com'
mcp-streamablehttp-client -c 'read_file /path/to/file.txt'

# Simple string arguments
mcp-streamablehttp-client -c 'echo "Hello World"'
```

## Architecture

```
┌─────────────────────┐     stdio      ┌──────────────────────┐     HTTP + OAuth    ┌─────────────────┐
│   Claude Desktop    │ ←------------→ │ mcp-streamablehttp-  │ ←----------------→ │  Remote MCP     │
│  (or other stdio    │   JSON-RPC     │      client          │  StreamableHTTP    │    Server       │
│    MCP client)      │                │  (Protocol Bridge)   │                    │ (OAuth Protected)│
└─────────────────────┘                └──────────────────────┘                    └─────────────────┘
```

The client acts as a transparent bridge, handling:
- Protocol conversion (stdio ↔ HTTP)
- OAuth authentication (token injection)
- Session management (state preservation)
- Error translation (HTTP → JSON-RPC)

## Security

- OAuth tokens are stored securely in `.env` file
- Automatic token refresh before expiration
- SSL/TLS verification enabled by default
- Supports PKCE for authorization code flow
- Client credentials never exposed in logs

## Development

### Running Tests

```bash
# Run all tests
just test

# Run specific test
just test-auth
```

### Building

```bash
# Build Docker image
just build

# Rebuild with no cache
just rebuild
```

## Troubleshooting

### Common Issues

1. **"No credentials found"**
   - Run `mcp-streamablehttp-client --token` to authenticate

2. **"Token expired"**
   - The client should auto-refresh, but you can force it with `--token`

3. **"OAuth server not found"**
   - Check `MCP_SERVER_URL` is correct
   - Ensure the server supports OAuth discovery

4. **"Permission denied"**
   - Your OAuth user may not have access to the requested resource
   - Check with your administrator

### Debug Mode

Set environment variable for verbose logging:

```bash
export MCP_DEBUG=1
mcp-streamablehttp-client --test-auth
```

## Examples

See the `examples/` directory for:
- `claude_desktop_config.json` - Claude Desktop configuration
- `command_examples.sh` - Common command patterns
- `demo.py` - Python integration example
- `token_example.md` - OAuth flow walkthrough

## License

[License information here]

## Contributing

[Contribution guidelines here]
