# mcp-streamablehttp-proxy

A generic stdio-to-StreamableHTTP bridge for MCP (Model Context Protocol) servers. This proxy enables any stdio-based MCP server to be accessed via HTTP endpoints, making them compatible with web-based clients and HTTP infrastructure like API gateways.

## Overview

The `mcp-streamablehttp-proxy` acts as a translation layer between:
- **MCP clients** that speak StreamableHTTP (like Claude.ai, web-based IDEs)
- **MCP servers** that only speak stdio JSON-RPC (like the official MCP servers)

It manages sessions, spawns server subprocesses, and handles the protocol translation transparently.

## Features

- **Universal MCP Server Support** - Works with any stdio-based MCP server
- **Session Management** - Each client gets an isolated server subprocess
- **Full Protocol Support** - Handles the complete MCP lifecycle
- **Configurable** - Flexible timeout, host, and port configuration
- **Production Ready** - Async implementation with proper cleanup
- **Gateway Compatible** - Designed for use with Traefik and OAuth gateways

## Installation

### Via pip
```bash
pip install mcp-streamablehttp-proxy
```

### Via pixi
```bash
pixi add --pypi mcp-streamablehttp-proxy
```

## Usage

### Basic Usage

```bash
# Proxy a Python MCP server module
mcp-streamablehttp-proxy python -m mcp_server_fetch

# Proxy an executable MCP server
mcp-streamablehttp-proxy /usr/local/bin/mcp-server-filesystem --root /data

# Proxy an npm-based MCP server
mcp-streamablehttp-proxy npx @modelcontextprotocol/server-memory
```

### Command Line Options

```
mcp-streamablehttp-proxy [OPTIONS] <server_command> [server_args...]

Options:
  --host TEXT         Host to bind to (default: 127.0.0.1)
  --port INTEGER      Port to bind to (default: 3000)
  --timeout INTEGER   Session timeout in seconds (default: 300)
  --log-level TEXT    Log level: debug/info/warning/error (default: info)
  --help             Show this message and exit
```

### Environment Variables

- `MCP_BIND_HOST` - Override default bind host
- `MCP_PORT` - Override default port
- `LOG_FILE` - Enable file logging to specified path

## How It Works

1. **Client sends HTTP request** to `/mcp` endpoint
2. **Proxy creates session** on first `initialize` request
3. **Proxy spawns subprocess** running the specified MCP server
4. **Proxy translates** between HTTP and stdio protocols
5. **Client includes session ID** in subsequent requests
6. **Sessions timeout** after period of inactivity

## API

### Endpoint

- **POST /mcp** - Single endpoint for all MCP protocol messages

### Headers

- **Mcp-Session-Id** - Required for all requests after initialization
- **Content-Type** - Must be `application/json`

### Request Format

Standard JSON-RPC 2.0 messages:
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "example-client",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

### Response Format

JSON-RPC 2.0 responses with session ID header:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "serverInfo": {
      "name": "example-server",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

Response includes header: `Mcp-Session-Id: <uuid>`

## Examples

### Testing with curl

```bash
# Start the proxy
mcp-streamablehttp-proxy python -m mcp_server_fetch

# Initialize session
SESSION_ID=$(curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05"},"id":1}' \
  -i | grep -i mcp-session-id | cut -d' ' -f2 | tr -d '\r')

# List available tools
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":2}'
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

RUN pip install mcp-streamablehttp-proxy mcp-server-fetch

# Bind to 0.0.0.0 for container networking
CMD ["mcp-streamablehttp-proxy", "--host", "0.0.0.0", "python", "-m", "mcp_server_fetch"]
```

### Docker Compose with Traefik

```yaml
services:
  mcp-fetch:
    build: .
    environment:
      - MCP_BIND_HOST=0.0.0.0
      - MCP_PORT=3000
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mcp-fetch.rule=Host(`mcp-fetch.example.com`)"
      - "traefik.http.services.mcp-fetch.loadbalancer.server.port=3000"
      - "traefik.http.routers.mcp-fetch.middlewares=mcp-auth"
      - "traefik.http.middlewares.mcp-auth.forwardauth.address=http://auth:8000/verify"
```

## Session Management

### Session Lifecycle

1. **Creation** - New session created on `initialize` request
2. **Active** - Session kept alive by requests
3. **Timeout** - Session expires after inactivity (default: 300s)
4. **Cleanup** - Subprocess terminated and resources freed

### Session Limits

- One subprocess per session
- Sessions are isolated from each other
- No built-in session limit (manage via container resources)

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Session not found | Invalid or expired session ID | Initialize new session |
| Request timeout | Server took >30s to respond | Check server health |
| Subprocess died | Server crashed | Check server logs |
| Invalid request | Malformed JSON-RPC | Verify request format |

### Debugging

Enable debug logging:
```bash
mcp-streamablehttp-proxy --log-level debug python -m mcp_server_fetch

# Or with file logging
export LOG_FILE=/tmp/mcp-proxy.log
mcp-streamablehttp-proxy --log-level debug python -m mcp_server_fetch
```

## Performance Considerations

- **One subprocess per session** - Plan resources accordingly
- **30-second request timeout** - Not suitable for very long operations
- **Async I/O** - Handles concurrent requests within sessions
- **No request queuing** - Requests processed in parallel

For high-load scenarios, consider:
- Running multiple proxy instances behind a load balancer
- Adjusting session timeout based on usage patterns
- Monitoring subprocess resource usage

## Security

⚠️ **This proxy provides NO authentication or authorization!**

Always deploy behind an authenticating reverse proxy like Traefik with:
- OAuth2/JWT authentication
- Rate limiting
- Access control
- HTTPS termination

Never expose the proxy directly to the internet!

## Integration with MCP OAuth Gateway

This proxy is designed to work seamlessly with the MCP OAuth Gateway:

1. Proxy exposes MCP servers as HTTP endpoints
2. Traefik provides routing and authentication
3. OAuth gateway handles client registration and tokens
4. Clients access MCP servers with OAuth bearer tokens

## Development

### Running Tests
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=mcp_streamablehttp_proxy tests/
```

### Type Checking
```bash
mypy src/
```

### Linting
```bash
ruff check src/
ruff format src/
```

## Troubleshooting

### Proxy won't start
- Verify the MCP server command is correct
- Check that the server is installed and in PATH
- Ensure port 3000 (or custom port) is available

### Sessions immediately timeout
- Increase timeout with `--timeout` option
- Check if server is responding to initialize
- Verify server stdout is line-buffered JSON

### Requests hang
- Enable debug logging to see communication
- Check if server is actually responding
- Verify JSON-RPC request format

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built for the [Model Context Protocol](https://modelcontextprotocol.io)
- Designed for integration with HTTP infrastructure
- Part of the MCP OAuth Gateway ecosystem
