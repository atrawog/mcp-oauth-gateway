# mcp-streamablehttp-client

A client-side bridge that enables stdio-based MCP clients (like Claude Desktop) to connect to streamable HTTP-based MCP servers with OAuth authentication. This tool handles the complete OAuth flow and provides comprehensive testing and debugging capabilities.

## Overview

This client bridges the gap between:
- **Stdio-based MCP clients**: Applications expecting stdio transport (Claude Desktop, IDEs)
- **HTTP-based MCP servers**: Servers using streamable HTTP transport with OAuth protection

## Key Features

- 🔐 **Automatic OAuth Authentication**: Complete OAuth device flow with token refresh
- 🔄 **Bidirectional Bridge**: Seamless stdio ↔ streamable HTTP translation
- 🧪 **Raw Protocol Mode**: Send raw JSON-RPC requests for testing
- 📋 **Discovery Commands**: List tools, resources, and prompts
- 🎯 **Tool Execution**: Execute MCP tools directly from CLI
- 📝 **RFC 7592 Support**: Full client registration management
- 🔑 **Smart Token Management**: Automatic refresh and credential storage
- 🎨 **Multiple Argument Formats**: JSON, key=value, and smart parsing

## Installation

```bash
# Via pixi (recommended)
pixi add mcp-streamablehttp-client

# Or from source
cd mcp-streamablehttp-client
pixi install -e .
```

## Quick Start

### 1. Initial Setup

Create a `.env` file:

```bash
# Required: MCP server endpoint
MCP_SERVER_URL=https://mcp-fetch.example.com/mcp

# OAuth tokens (auto-populated after first auth)
MCP_CLIENT_ACCESS_TOKEN=
MCP_CLIENT_REFRESH_TOKEN=
MCP_CLIENT_ID=
MCP_CLIENT_SECRET=
```

### 2. First Run - Authentication

```bash
# Run the client - it will guide you through OAuth
mcp-streamablehttp-client

# The tool will:
# 1. Discover OAuth endpoints
# 2. Register as a client (if needed)
# 3. Display device authorization URL
# 4. Save credentials to .env
```

### 3. Subsequent Usage

After authentication, the client runs automatically:

```bash
# Interactive stdio mode (for Claude Desktop)
mcp-streamablehttp-client

# Or use with specific commands
mcp-streamablehttp-client --list-tools
mcp-streamablehttp-client --command "fetch https://example.com"
```

## Command Line Interface

### Basic Options

```bash
mcp-streamablehttp-client [OPTIONS]

Options:
  --env-file PATH         Path to .env file
  --log-level LEVEL       Logging level (DEBUG, INFO, WARNING, ERROR)
  --server-url URL        Override MCP server URL
  --reset-auth            Clear credentials and re-authenticate
  --test-auth             Test authentication and exit
  -t, --token             Check/refresh OAuth tokens
  --help                  Show help and exit
```

### Tool Execution

Execute MCP tools directly:

```bash
# Simple format
mcp-streamablehttp-client -c "echo Hello World"

# With parameters
mcp-streamablehttp-client -c "fetch https://httpbin.org/json"

# Key=value format
mcp-streamablehttp-client -c "search query='machine learning' limit=10"

# JSON format
mcp-streamablehttp-client -c 'mytool {"param": "value", "count": 42}'
```

### Discovery Commands

List server capabilities:

```bash
# List all available tools with schemas
mcp-streamablehttp-client --list-tools

# List all resources
mcp-streamablehttp-client --list-resources

# List all prompts with arguments
mcp-streamablehttp-client --list-prompts
```

### Raw Protocol Mode

Send raw JSON-RPC requests for testing:

```bash
# List tools using raw protocol
mcp-streamablehttp-client --raw '{"method": "tools/list", "params": {}}'

# Call a tool directly
mcp-streamablehttp-client --raw '{
  "method": "tools/call",
  "params": {
    "name": "echo",
    "arguments": {"message": "Hello"}
  }
}'

# Test initialization
mcp-streamablehttp-client --raw '{
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {"name": "test", "version": "1.0"}
  }
}'
```

### Client Management (RFC 7592)

Manage your OAuth client registration:

```bash
# View current registration
mcp-streamablehttp-client --get-client-info

# Update client metadata
mcp-streamablehttp-client --update-client "client_name=Production Client"

# Update multiple fields
mcp-streamablehttp-client --update-client "client_name=My App,scope=read write"

# Update redirect URIs (semicolon-separated)
mcp-streamablehttp-client --update-client "redirect_uris=https://app1.com/cb;https://app2.com/cb"

# Delete registration (PERMANENT!)
mcp-streamablehttp-client --delete-client
```

## Claude Desktop Integration

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "remote-fetch": {
      "command": "mcp-streamablehttp-client",
      "args": ["--env-file", "/path/to/.env"]
    },
    "another-server": {
      "command": "mcp-streamablehttp-client",
      "env": {
        "MCP_SERVER_URL": "https://another.example.com/mcp",
        "MCP_CLIENT_ACCESS_TOKEN": "existing_token"
      }
    }
  }
}
```

## Architecture

### Core Components

1. **cli.py** - Command-line interface and argument parsing
   - Main entry point with all CLI options
   - Smart argument parsing for tool execution
   - Protocol testing capabilities

2. **proxy.py** - Stdio ↔ HTTP bridge
   - Handles MCP protocol translation
   - Session management with `Mcp-Session-Id`
   - Automatic initialization handling
   - SSE and JSON response parsing

3. **oauth.py** - OAuth authentication
   - Device flow implementation
   - Token refresh logic
   - Dynamic client registration (RFC 7591)
   - Client management (RFC 7592)

4. **config.py** - Configuration management
   - Pydantic settings validation
   - Environment variable handling
   - Credential persistence

### Request Flow

```
Claude Desktop → stdio → Client Proxy → HTTP → OAuth Gateway → MCP Server
       ↑                                                              ↓
       ←─────────── stdio ←───────── HTTP Response ←─────────────────┘
```

## Token Management

### Automatic Token Handling

The client automatically manages tokens:
- Checks expiration before each request
- Refreshes tokens when needed
- Updates .env with new tokens
- Falls back to re-authentication if refresh fails

### Manual Token Management

```bash
# Check token status and refresh if needed
mcp-streamablehttp-client --token

# Force re-authentication
mcp-streamablehttp-client --reset-auth

# Test authentication without running
mcp-streamablehttp-client --test-auth
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_URL` | MCP server endpoint | Required |
| `MCP_CLIENT_ACCESS_TOKEN` | OAuth access token | Auto-generated |
| `MCP_CLIENT_REFRESH_TOKEN` | OAuth refresh token | Auto-generated |
| `MCP_CLIENT_ID` | OAuth client ID | Auto-generated |
| `MCP_CLIENT_SECRET` | OAuth client secret | Auto-generated |
| `MCP_CLIENT_REGISTRATION_TOKEN` | RFC 7592 management token | Auto-generated |
| `MCP_CLIENT_REGISTRATION_URI` | Client management URI | Auto-generated |
| `OAUTH_*` | Override OAuth endpoints | Auto-discovered |
| `SESSION_TIMEOUT` | Session timeout (seconds) | 300 |
| `REQUEST_TIMEOUT` | Request timeout (seconds) | 30 |
| `LOG_LEVEL` | Logging level | INFO |
| `VERIFY_SSL` | Verify SSL certificates | true |

## Testing and Debugging

### Protocol Compliance Testing

Use raw mode to test MCP protocol compliance:

```bash
# Test server capabilities
mcp-streamablehttp-client --raw '{"method": "capabilities/list", "params": {}}'

# Test error handling
mcp-streamablehttp-client --raw '{"method": "invalid/method", "params": {}}'
```

### Integration Testing

The client is extensively tested with various MCP servers:
- `test_mcp_everything_client_full.py` - Raw protocol tests
- `test_mcp_everything_comprehensive.py` - Tool execution tests
- `test_mcp_everything_client_simple.py` - Basic connectivity

### Debugging Tips

1. **Enable debug logging**: `--log-level DEBUG`
2. **Check token status**: `--token`
3. **Test authentication**: `--test-auth`
4. **Use raw mode**: `--raw` for protocol-level debugging
5. **Check server discovery**: Look for OAuth metadata endpoint

## Common Issues

### Authentication Failures

1. Check token status: `mcp-streamablehttp-client --token`
2. Verify server URL is correct
3. Try resetting auth: `--reset-auth`
4. Check OAuth endpoint discovery
5. Verify network connectivity

### Session Issues

- Session IDs are extracted from response headers, not body
- Don't include session ID in initialization requests
- Sessions timeout after inactivity

### Response Parsing

- Supports both JSON and SSE (text/event-stream) formats
- Multiple JSON objects may be present in output
- Parser looks for last valid JSON-RPC response

## Development

```bash
# Clone repository
git clone https://github.com/atrawog/mcp-oauth-gateway
cd mcp-oauth-gateway/mcp-streamablehttp-client

# Install in development mode
pixi install -e .

# Run tests
pixi run pytest tests/ -v

# Test with local server
MCP_SERVER_URL=http://localhost:3000/mcp pixi run mcp-streamablehttp-client --list-tools
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Author

Andreas Trawoeger

## Links

- [Homepage](https://github.com/atrawog/mcp-oauth-gateway/tree/main/mcp-streamablehttp-client)
- [Repository](https://github.com/atrawog/mcp-oauth-gateway/tree/main/mcp-streamablehttp-client)
- [Documentation](https://atrawog.github.io/mcp-oauth-gateway)
- [Issues](https://github.com/atrawog/mcp-oauth-gateway/issues)