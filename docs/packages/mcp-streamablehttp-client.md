# mcp-streamablehttp-client

## Overview

The `mcp-streamablehttp-client` package is a sophisticated bridge that enables stdio-based MCP clients (like Claude Desktop) to connect to HTTP-based MCP servers with OAuth authentication. It provides comprehensive features for authentication, testing, and debugging MCP integrations.

```{admonition} Key Features
:class: info

- 🔐 **OAuth Device Flow**: Automatic authentication with token refresh
- 🔄 **Protocol Bridge**: Seamless stdio ↔ HTTP translation
- 🧪 **Testing Tools**: Raw protocol mode and discovery commands
- 🎯 **Direct Execution**: Run MCP tools from command line
- 📝 **RFC 7592 Support**: Complete client registration management
- 🔑 **Smart Credentials**: Automatic token storage and refresh
```

## Architecture

### System Position

```{mermaid}
graph LR
    subgraph "MCP Client Application"
        CD[Claude Desktop<br/>or IDE]
    end
    
    subgraph "mcp-streamablehttp-client"
        CLI[CLI Interface]
        P[Proxy Core]
        O[OAuth Manager]
        C[Config Manager]
    end
    
    subgraph "Remote Infrastructure"
        GW[OAuth Gateway]
        MS[MCP Servers]
    end
    
    CD -->|stdio| CLI
    CLI --> P
    P --> O
    O --> C
    P -->|HTTP + OAuth| GW
    GW --> MS
    
    classDef client fill:#9cf,stroke:#333,stroke-width:2px
    classDef bridge fill:#fc9,stroke:#333,stroke-width:2px
    classDef remote fill:#9fc,stroke:#333,stroke-width:2px
    
    class CD client
    class CLI,P,O,C bridge
    class GW,MS remote
```

### Package Structure

```
mcp_streamablehttp_client/
├── __init__.py      # Package initialization
├── cli.py           # Command-line interface
├── proxy.py         # stdio ↔ HTTP bridge
├── oauth.py         # OAuth authentication
├── config.py        # Configuration management
└── py.typed         # Type checking marker
```

### Core Components

#### cli.py - Command Interface

Provides extensive CLI options:
- Interactive stdio mode for Claude Desktop
- Tool execution with `--command`
- Raw protocol testing with `--raw`
- Discovery commands (`--list-tools`, etc.)
- OAuth management (`--token`, `--reset-auth`)
- RFC 7592 client management

#### proxy.py - Protocol Bridge

Handles bidirectional translation:
- JSON-RPC over stdio (client side)
- JSON-RPC over HTTP (server side)
- Session management with `Mcp-Session-Id`
- Automatic initialization handling
- SSE and JSON response parsing

#### oauth.py - Authentication Manager

Implements complete OAuth flow:
- Device authorization flow
- Dynamic client registration (RFC 7591)
- Token refresh logic
- Credential persistence
- Client management (RFC 7592)

## Installation

### Using pixi (Recommended)

```bash
pixi add mcp-streamablehttp-client
```

### From Source

```bash
cd mcp-streamablehttp-client
pixi install -e .
```

## Quick Start

### 1. Initial Configuration

Create a `.env` file:

```bash
# Required: MCP server endpoint
MCP_SERVER_URL=https://mcp-fetch.example.com/mcp

# OAuth configuration (optional, auto-discovered)
OAUTH_AUTHORIZATION_URL=https://auth.example.com/authorize
OAUTH_TOKEN_URL=https://auth.example.com/token
OAUTH_REGISTRATION_URL=https://auth.example.com/register

# Credentials (auto-populated after first auth)
MCP_CLIENT_ACCESS_TOKEN=
MCP_CLIENT_REFRESH_TOKEN=
MCP_CLIENT_ID=
MCP_CLIENT_SECRET=
```

### 2. First Run - Authentication

```bash
# Run the client - it will guide through OAuth
mcp-streamablehttp-client

# Output:
# 🔐 No valid authentication found. Starting OAuth flow...
# 📝 Registering as OAuth client...
# ✅ Client registered successfully!
# 
# 🌐 Please visit: https://auth.example.com/device
# 📋 Enter code: ABCD-1234
# 
# ⏳ Waiting for authorization...
# ✅ Authentication successful!
# 💾 Credentials saved to .env file
```

### 3. Claude Desktop Integration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "remote-fetch": {
      "command": "mcp-streamablehttp-client",
      "args": ["--env-file", "/path/to/.env"]
    }
  }
}
```

## Command Line Interface

### Basic Usage

```bash
mcp-streamablehttp-client [OPTIONS]

Options:
  --env-file PATH         Path to .env file
  --log-level LEVEL       Logging level (DEBUG, INFO, WARNING, ERROR)
  --server-url URL        Override MCP server URL
  --help                  Show help and exit
```

### Authentication Options

```bash
# Check and refresh tokens
mcp-streamablehttp-client --token

# Reset authentication (clear credentials)
mcp-streamablehttp-client --reset-auth

# Test authentication without running
mcp-streamablehttp-client --test-auth
```

### Tool Execution

Execute MCP tools directly from CLI:

```bash
# Simple execution
mcp-streamablehttp-client -c "echo Hello World"

# With parameters
mcp-streamablehttp-client -c "fetch https://example.com"

# Key=value format
mcp-streamablehttp-client -c "search query='python tutorial' limit=10"

# JSON format
mcp-streamablehttp-client -c 'weather {"location": "San Francisco", "units": "celsius"}'
```

### Discovery Commands

List server capabilities:

```bash
# List all tools with descriptions
mcp-streamablehttp-client --list-tools

# Example output:
# Available tools:
# - fetch: Fetch content from URLs
#   Arguments:
#     - url (string, required): URL to fetch
#     - method (string): HTTP method (default: GET)
#     - headers (object): Custom headers
# 
# - echo: Echo back a message
#   Arguments:
#     - message (string, required): Message to echo

# List resources
mcp-streamablehttp-client --list-resources

# List prompts
mcp-streamablehttp-client --list-prompts
```

### Raw Protocol Mode

Send raw JSON-RPC requests for testing:

```bash
# Direct protocol testing
mcp-streamablehttp-client --raw '{"method": "tools/list", "params": {}}'

# Test specific methods
mcp-streamablehttp-client --raw '{
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {"url": "https://httpbin.org/json"}
  }
}'

# Custom protocol testing
mcp-streamablehttp-client --raw '{
  "method": "resources/read",
  "params": {"uri": "file:///example.txt"}
}'
```

### Client Management (RFC 7592)

Manage OAuth client registration:

```bash
# View current registration
mcp-streamablehttp-client --get-client-info

# Output:
# Client Registration Info:
# - Client ID: client_abc123xyz
# - Client Name: mcp-streamablehttp-client
# - Created: 2024-01-15T10:30:00Z
# - Expires: Never

# Update client metadata
mcp-streamablehttp-client --update-client "client_name=Production MCP Client"

# Update multiple fields
mcp-streamablehttp-client --update-client "client_name=My App,scope=read write admin"

# Update redirect URIs (semicolon-separated)
mcp-streamablehttp-client --update-client "redirect_uris=https://app1.com/cb;https://app2.com/cb"

# Delete registration (PERMANENT!)
mcp-streamablehttp-client --delete-client
```

## Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MCP_SERVER_URL` | MCP server endpoint URL | - | Yes |
| `MCP_CLIENT_ACCESS_TOKEN` | OAuth access token | - | Auto |
| `MCP_CLIENT_REFRESH_TOKEN` | OAuth refresh token | - | Auto |
| `MCP_CLIENT_ID` | OAuth client ID | - | Auto |
| `MCP_CLIENT_SECRET` | OAuth client secret | - | Auto |
| `MCP_CLIENT_REGISTRATION_TOKEN` | RFC 7592 management token | - | Auto |
| `MCP_CLIENT_REGISTRATION_URI` | Client management URI | - | Auto |
| `OAUTH_AUTHORIZATION_URL` | OAuth authorization endpoint | - | Auto-discovered |
| `OAUTH_TOKEN_URL` | OAuth token endpoint | - | Auto-discovered |
| `OAUTH_REGISTRATION_URL` | Client registration endpoint | - | Auto-discovered |
| `OAUTH_DEVICE_AUTH_URL` | Device authorization endpoint | - | Auto-discovered |
| `SESSION_TIMEOUT` | MCP session timeout (seconds) | 300 | No |
| `REQUEST_TIMEOUT` | HTTP request timeout (seconds) | 30 | No |
| `LOG_LEVEL` | Logging verbosity | INFO | No |
| `VERIFY_SSL` | Verify SSL certificates | true | No |

### Configuration Object

The client uses Pydantic for configuration:

```python
from mcp_streamablehttp_client import Settings

settings = Settings(
    mcp_server_url="https://mcp.example.com/mcp",
    log_level="DEBUG",
    session_timeout=600
)
```

## Authentication Flow

### Device Authorization Flow

```{mermaid}
sequenceDiagram
    participant User
    participant Client
    participant AuthServer
    participant GitHub
    
    Client->>AuthServer: POST /register<br/>(Dynamic Registration)
    AuthServer-->>Client: client_id, client_secret
    
    Client->>AuthServer: POST /device/code<br/>(Request device code)
    AuthServer-->>Client: device_code, user_code, verification_uri
    
    Client->>User: Display: "Visit: {uri}<br/>Code: {user_code}"
    
    User->>AuthServer: Visit URL, enter code
    AuthServer->>GitHub: Redirect to GitHub OAuth
    User->>GitHub: Authenticate
    GitHub-->>AuthServer: Authorization code
    
    loop Poll for completion
        Client->>AuthServer: POST /token<br/>(Check device code)
        AuthServer-->>Client: pending / token
    end
    
    AuthServer-->>Client: access_token, refresh_token
    Client->>Client: Save to .env
```

### Token Management

The client automatically handles token lifecycle:

1. **Expiration Check**: Before each request
2. **Automatic Refresh**: When token expires
3. **Credential Update**: Saves new tokens to .env
4. **Fallback**: Re-authentication if refresh fails

## Usage Patterns

### Interactive Mode (Claude Desktop)

When used with Claude Desktop, the client operates in stdio mode:

```python
# Internal flow
while True:
    request = read_from_stdin()
    
    # Check/refresh auth
    ensure_valid_token()
    
    # Forward to HTTP server
    response = forward_to_http(request)
    
    # Return to client
    write_to_stdout(response)
```

### Command Execution Mode

For direct tool execution:

```python
# Parse command
tool_name, arguments = parse_command(command_string)

# Execute via MCP
result = execute_tool(tool_name, arguments)

# Display result
print_formatted_result(result)
```

### Testing Mode

For protocol testing and debugging:

```python
# Send raw request
response = send_raw_request(json_string)

# Parse response
if response.get("result"):
    display_result(response["result"])
elif response.get("error"):
    display_error(response["error"])
```

## Advanced Features

### Smart Argument Parsing

The client supports multiple argument formats:

```bash
# Positional arguments
mcp-streamablehttp-client -c "echo Hello World"
# Parsed as: {"message": "Hello World"}

# Key=value pairs
mcp-streamablehttp-client -c "search query=test limit=5"
# Parsed as: {"query": "test", "limit": 5}

# JSON objects
mcp-streamablehttp-client -c 'tool {"key": "value", "num": 42}'
# Parsed as: {"key": "value", "num": 42}

# Mixed formats
mcp-streamablehttp-client -c "fetch https://example.com method=POST"
# Parsed as: {"url": "https://example.com", "method": "POST"}
```

### Session Management

The client maintains MCP session state:

- Automatic initialization on first request
- Session ID persistence across requests
- Graceful handling of session timeouts
- Automatic re-initialization when needed

### Response Parsing

Handles multiple response formats:

- Standard JSON responses
- Server-Sent Events (SSE) format
- Multi-line JSON objects
- Error responses with proper formatting

## Integration Examples

### With Custom MCP Servers

```json
{
  "mcpServers": {
    "custom-server": {
      "command": "mcp-streamablehttp-client",
      "env": {
        "MCP_SERVER_URL": "https://custom.example.com/mcp",
        "MCP_CLIENT_ACCESS_TOKEN": "existing_token"
      }
    }
  }
}
```

### Multiple Server Configuration

```json
{
  "mcpServers": {
    "fetch-server": {
      "command": "mcp-streamablehttp-client",
      "args": ["--env-file", "/configs/fetch.env"]
    },
    "filesystem-server": {
      "command": "mcp-streamablehttp-client",
      "args": ["--env-file", "/configs/filesystem.env"]
    }
  }
}
```

### Programmatic Usage

```python
from mcp_streamablehttp_client import StreamableHttpToStdioProxy

# Create proxy instance
proxy = StreamableHttpToStdioProxy(
    server_url="https://mcp.example.com/mcp",
    access_token="your_token"
)

# Run in async context
async def main():
    await proxy.run()

asyncio.run(main())
```

## Testing and Debugging

### Protocol Compliance Testing

Test MCP protocol compliance:

```bash
# Test initialization
mcp-streamablehttp-client --raw '{
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {"name": "test", "version": "1.0"}
  }
}'

# Test error handling
mcp-streamablehttp-client --raw '{"method": "invalid/method"}'

# Test tool execution
mcp-streamablehttp-client --raw '{
  "method": "tools/call",
  "params": {"name": "echo", "arguments": {"message": "test"}}
}'
```

### Debug Logging

Enable verbose logging:

```bash
# Via command line
mcp-streamablehttp-client --log-level DEBUG

# Via environment
export LOG_LEVEL=DEBUG
mcp-streamablehttp-client
```

Debug output includes:
- HTTP requests/responses
- OAuth flow details
- Token refresh events
- Session management
- Error details

### Common Testing Scenarios

```bash
# Test authentication
mcp-streamablehttp-client --test-auth

# Check token status
mcp-streamablehttp-client --token

# List server capabilities
mcp-streamablehttp-client --list-tools

# Test specific tool
mcp-streamablehttp-client -c "echo test message"

# Raw protocol test
mcp-streamablehttp-client --raw '{"method": "tools/list", "params": {}}'
```

## Troubleshooting

### Authentication Issues

#### "No valid authentication found"

**Solutions**:
1. Check MCP_SERVER_URL is correct
2. Verify OAuth endpoints are accessible
3. Try `--reset-auth` to start fresh
4. Check network connectivity

#### "Token refresh failed"

**Solutions**:
1. Verify refresh token hasn't expired
2. Check OAuth server is running
3. Try manual re-authentication
4. Review OAuth server logs

### Connection Issues

#### "Failed to connect to server"

**Solutions**:
1. Verify server URL and port
2. Check SSL certificates (`VERIFY_SSL=false` for testing)
3. Test with curl: `curl -I https://server/mcp`
4. Check firewall rules

#### "Session timeout"

**Solutions**:
1. Increase SESSION_TIMEOUT
2. Check for network interruptions
3. Verify server session handling
4. Monitor request frequency

### Protocol Issues

#### "Invalid JSON-RPC response"

**Solutions**:
1. Enable debug logging
2. Test with `--raw` mode
3. Verify server protocol version
4. Check response format

#### "Method not found"

**Solutions**:
1. List available methods: `--list-tools`
2. Check method name spelling
3. Verify server capabilities
4. Update protocol version

## Best Practices

### Security

1. **Credential Storage**: Store .env files securely
2. **Token Rotation**: Implement regular token refresh
3. **SSL Verification**: Always verify in production
4. **Access Control**: Limit token scope appropriately
5. **Audit Logging**: Monitor authentication events

### Performance

1. **Connection Reuse**: Maintain persistent connections
2. **Token Caching**: Minimize refresh requests
3. **Batch Operations**: Group related requests
4. **Timeout Tuning**: Adjust for network conditions
5. **Resource Cleanup**: Handle disconnections gracefully

### Error Handling

1. **Graceful Degradation**: Handle auth failures smoothly
2. **Retry Logic**: Implement exponential backoff
3. **User Feedback**: Provide clear error messages
4. **Logging**: Capture diagnostic information
5. **Recovery**: Automatic re-authentication

## Advanced Topics

### Custom OAuth Providers

Configure alternative OAuth providers:

```python
from mcp_streamablehttp_client import OAuthConfig

custom_oauth = OAuthConfig(
    authorization_url="https://custom.auth/authorize",
    token_url="https://custom.auth/token",
    device_url="https://custom.auth/device",
    client_id="custom_client",
    client_secret="custom_secret"
)
```

### Request Interceptors

Add custom request processing:

```python
async def request_interceptor(request: dict) -> dict:
    # Add custom headers
    request["_headers"] = {
        "X-Custom-Header": "value"
    }
    return request

proxy.add_interceptor(request_interceptor)
```

### Response Transformers

Process responses before returning:

```python
async def response_transformer(response: dict) -> dict:
    # Add metadata
    response["_metadata"] = {
        "timestamp": time.time(),
        "server": "remote"
    }
    return response

proxy.add_transformer(response_transformer)
```

## Development

### Running Tests

```bash
# All tests
pixi run pytest tests/ -v

# Specific test category
pixi run pytest tests/test_oauth.py -v
pixi run pytest tests/test_proxy.py -v
pixi run pytest tests/test_cli.py -v

# With coverage
pixi run pytest --cov=mcp_streamablehttp_client
```

### Test Categories

1. **Unit Tests**: Component isolation
2. **Integration Tests**: OAuth flow testing
3. **Protocol Tests**: MCP compliance
4. **CLI Tests**: Command parsing

### Contributing

See the main project [Development Guidelines](../development/guidelines.md) for contribution standards.

## Migration Guide

### From Direct HTTP Clients

If migrating from direct HTTP MCP clients:

1. Install mcp-streamablehttp-client
2. Configure OAuth credentials
3. Update client configuration
4. Test authentication flow
5. Verify tool execution

### From Other Bridges

Key differences from other stdio-HTTP bridges:

1. **Built-in OAuth**: No separate auth setup
2. **Testing Tools**: Extensive debugging features
3. **Smart Parsing**: Flexible argument formats
4. **Token Management**: Automatic refresh
5. **RFC Compliance**: Full 7591/7592 support

## License

Apache License 2.0 - see project LICENSE file.

## Support

- **Issues**: [GitHub Issues](https://github.com/atrawog/mcp-oauth-gateway/issues)
- **Documentation**: [Full Documentation](https://atrawog.github.io/mcp-oauth-gateway)
- **Source**: [GitHub Repository](https://github.com/atrawog/mcp-oauth-gateway/tree/main/mcp-streamablehttp-client)