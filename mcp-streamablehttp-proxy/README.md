# mcp-streamablehttp-proxy

A generic stdio-to-streamable-HTTP proxy for MCP (Model Context Protocol) servers. This package enables any stdio-based MCP server to be exposed via HTTP endpoints, implementing the MCP 2025-06-18 Streamable HTTP transport specification.

## Overview

This proxy acts as a bridge between:
- **Input**: HTTP requests following the MCP Streamable HTTP specification
- **Output**: stdio communication with any MCP server implementation
- **Purpose**: Enable web-based access to MCP servers that only support stdio transport

## Key Features

- 🔄 **Universal MCP Server Compatibility**: Works with any stdio-based MCP server
- 🌐 **Streamable HTTP Transport**: Full implementation of MCP 2025-06-18 specification
- 📊 **Session Management**: Maintains MCP session state across HTTP requests
- 🚀 **Production Ready**: Health checks via MCP protocol initialization
- 🐳 **Docker Native**: Designed for containerized deployments
- ⚡ **Subprocess Isolation**: Each session runs in its own process space
- 🔧 **Zero Configuration**: Works out-of-the-box with sensible defaults

## Installation

```bash
# Via pixi (recommended)
pixi add mcp-streamablehttp-proxy

# Or from source
cd mcp-streamablehttp-proxy
pixi install -e .
```

## Quick Start

### Command Line Usage

```bash
# Wrap any stdio MCP server
mcp-streamablehttp-proxy serve -- mcp-server-fetch

# With custom port
mcp-streamablehttp-proxy serve --port 8080 -- mcp-server-fetch --config config.json

# With Node.js MCP servers
mcp-streamablehttp-proxy serve -- npx @modelcontextprotocol/server-fetch
```

### Docker Integration

```dockerfile
FROM node:20-slim

# Install MCP server
RUN npm install -g @modelcontextprotocol/server-fetch

# Install proxy
COPY --from=ghcr.io/prefix-dev/pixi:latest /pixi /usr/local/bin/pixi
RUN pixi add mcp-streamablehttp-proxy

EXPOSE 3000

# Health check via MCP protocol
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s \
    CMD curl -s -X POST http://localhost:3000/mcp \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}' \
        | grep -q '"protocolVersion"'

CMD ["pixi", "run", "mcp-streamablehttp-proxy", "serve", "--", "mcp-server-fetch"]
```

## Architecture

The proxy implements a three-layer architecture:

1. **HTTP Layer**: FastAPI server handling `/mcp` endpoint
2. **Bridge Layer**: Translates between HTTP and stdio protocols
3. **Process Layer**: Manages MCP server subprocess lifecycle

### Request Flow

```
HTTP Client → POST /mcp → Session Manager → stdio → MCP Server
    ↑                                                    ↓
    ← HTTP Response ← Response Handler ← stdout ←────────┘
```

## API Reference

### POST /mcp

Main MCP protocol endpoint.

**Request Headers:**
- `Content-Type: application/json` (required)
- `Accept: application/json, text/event-stream` (required)
- `Mcp-Session-Id: <session-id>` (optional, returned after initialization)
- `MCP-Protocol-Version: 2025-06-18` (recommended)

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {
      "name": "my-client",
      "version": "1.0"
    }
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "serverInfo": {
      "name": "mcp-server-fetch",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

## Session Management

- Sessions are created on first request
- Session ID returned in `Mcp-Session-Id` response header
- Sessions timeout after inactivity (default: 5 minutes)
- Each session maintains its own MCP server subprocess
- Automatic cleanup on session expiration or server crash

## Configuration

### Environment Variables

```bash
# Proxy configuration
PROXY_MAX_SESSIONS=1000          # Maximum concurrent sessions
PROXY_SESSION_TIMEOUT=300        # Session timeout in seconds
PROXY_REQUEST_TIMEOUT=30         # Individual request timeout
PROXY_BUFFER_SIZE=65536         # stdio buffer size

# Process management
PROXY_RESTART_ON_ERROR=true     # Auto-restart failed processes
PROXY_RESTART_DELAY=5           # Restart delay in seconds
PROXY_MAX_RESTARTS=3           # Maximum restart attempts
```

### Command Line Options

```bash
mcp-streamablehttp-proxy serve [OPTIONS] -- <mcp-server-command>

Options:
  --host TEXT     Host to bind to [default: 0.0.0.0]
  --port INTEGER  Port to bind to [default: 3000]
  --help          Show this message and exit
```

## Integration with MCP OAuth Gateway

This proxy is designed to work seamlessly with the MCP OAuth Gateway:

```yaml
# Docker Compose example
services:
  mcp-fetch:
    build: ./mcp-fetch
    command: >
      pixi run mcp-streamablehttp-proxy serve --
      npx @modelcontextprotocol/server-fetch
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mcp-fetch.rule=Host(`mcp-fetch.${BASE_DOMAIN}`)"
      - "traefik.http.routers.mcp-fetch.middlewares=mcp-auth@docker"
      - "traefik.http.services.mcp-fetch.loadbalancer.server.port=3000"
```

## Error Handling

The proxy provides detailed error responses:

- **400 Bad Request**: Invalid JSON-RPC format
- **404 Not Found**: Session not found
- **408 Request Timeout**: Request processing timeout
- **500 Internal Server Error**: MCP server crash or error
- **503 Service Unavailable**: Unable to start MCP server

## Performance Considerations

- Each session spawns a separate process
- Buffer sizes affect memory usage and latency
- Session timeout balances resource usage vs user experience
- Consider connection pooling for high-traffic scenarios

## Development

```bash
# Clone repository
git clone https://github.com/atrawog/mcp-oauth-gateway
cd mcp-oauth-gateway/mcp-streamablehttp-proxy

# Install dependencies
pixi install -e .

# Run tests
pixi run pytest tests/ -v

# Run with debug logging
LOG_LEVEL=DEBUG pixi run mcp-streamablehttp-proxy serve -- mcp-test-server
```

## Troubleshooting

### "Subprocess Failed to Start"
- Verify MCP server command is correct
- Check server is installed in container
- Review subprocess error logs
- Ensure executable permissions

### "Session Lost"
- Check session timeout configuration
- Monitor subprocess memory usage
- Review concurrent request handling
- Verify session ID in headers

### Performance Issues
- Monitor subprocess CPU usage
- Check stdio buffer sizes
- Review request queuing
- Consider process pooling

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Author

Andreas Trawoeger

## Links

- [Homepage](https://github.com/atrawog/mcp-oauth-gateway/tree/main/mcp-streamablehttp-proxy)
- [Repository](https://github.com/atrawog/mcp-oauth-gateway/tree/main/mcp-streamablehttp-proxy)
- [Documentation](https://atrawog.github.io/mcp-oauth-gateway)
- [Issues](https://github.com/atrawog/mcp-oauth-gateway/issues)