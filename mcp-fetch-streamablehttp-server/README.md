# MCP Fetch StreamableHTTP Server

A native Python implementation of an MCP (Model Context Protocol) server that provides secure URL fetching capabilities through the StreamableHTTP transport.

## Overview

This server implements the MCP protocol with a native StreamableHTTP transport, providing a `fetch` tool that allows AI assistants to retrieve content from URLs with built-in security protections.

### Key Features

- **Native MCP Implementation**: Direct protocol implementation without stdio bridging
- **StreamableHTTP Transport**: HTTP-based transport for web-native deployments
- **Secure Fetching**: SSRF protection, size limits, and robots.txt compliance
- **Stateless Operation**: Each request is independent, enabling horizontal scaling
- **Production Ready**: Includes health checks, proper error handling, and security measures

## Architecture

This service operates as part of the MCP OAuth Gateway's three-layer architecture:

1. **Traefik** (Layer 1): Handles routing and authentication
2. **Auth Service** (Layer 2): Manages OAuth flows and token validation
3. **MCP Services** (Layer 3): This service - pure protocol implementation

The service has no authentication code - all auth is handled by Traefik's ForwardAuth middleware.

## Installation

### Using pip

```bash
pip install mcp-fetch-streamablehttp-server
```

### Using pixi

```bash
pixi add --pypi mcp-fetch-streamablehttp-server
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install the package
RUN pip install mcp-fetch-streamablehttp-server

# Set environment variables
ENV MCP_SERVER_NAME=mcp-fetch
ENV MCP_SERVER_VERSION=1.0.0
ENV MCP_PROTOCOL_VERSION=2025-06-18
ENV HOST=0.0.0.0
ENV PORT=3000

# Expose the port
EXPOSE 3000

# Run the server
CMD ["python", "-m", "mcp_fetch_streamablehttp_server"]
```

## Quick Start

### Environment Variables

Create a `.env` file with required configuration:

```bash
# Required
MCP_SERVER_NAME=mcp-fetch
MCP_SERVER_VERSION=1.0.0
MCP_PROTOCOL_VERSION=2025-06-18

# Optional
MCP_FETCH_ALLOWED_SCHEMES=["http","https"]
MCP_FETCH_MAX_REDIRECTS=5
MCP_FETCH_DEFAULT_USER_AGENT=ModelContextProtocol/1.0 (Fetch Server)
HOST=0.0.0.0
PORT=3000
```

### Running with Docker Compose

```yaml
services:
  mcp-fetch:
    build: ./mcp-fetch-streamablehttp-server
    env_file: .env
    ports:
      - "3000:3000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/mcp", "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}']
      interval: 30s
      timeout: 5s
      retries: 3
```

### Running Locally

```bash
# Using pip/pixi installation
mcp-fetch-server

# Or using Python module
python -m mcp_fetch_streamablehttp_server

# Using just and pixi (recommended for development)
just run mcp-fetch

# Or directly with pixi
pixi run -e mcp-fetch python -m mcp_fetch_streamablehttp_server
```

## API Reference

### StreamableHTTP Endpoints

- **POST /mcp**: Handles JSON-RPC requests
- **GET /mcp**: SSE endpoint (infrastructure ready, not yet implemented)
- **DELETE /mcp**: Session termination (infrastructure ready)

### MCP Methods

#### initialize
Protocol handshake and capability negotiation.

```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {
      "name": "example-client",
      "version": "1.0"
    }
  },
  "id": 1
}
```

#### tools/list
Returns available tools (currently just `fetch`).

```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {},
  "id": 2
}
```

#### tools/call
Executes the fetch tool.

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://example.com",
      "method": "GET",
      "headers": {
        "User-Agent": "Custom-Agent/1.0"
      }
    }
  },
  "id": 3
}
```

### Fetch Tool

The `fetch` tool retrieves content from URLs with these parameters:

- **url** (required): The URL to fetch
- **method**: HTTP method (GET or POST, default: GET)
- **headers**: Optional HTTP headers object
- **body**: Optional request body for POST requests
- **max_length**: Maximum response length in bytes (default: 100000)
- **user_agent**: User agent string to use (default: "ModelContextProtocol/1.0")

#### Security Features

- **SSRF Protection**: Blocks requests to localhost, private networks, and cloud metadata services
- **Size Limits**: Responses limited to 100KB by default
- **Scheme Restrictions**: Only http/https allowed by default
- **Redirect Limits**: Maximum 5 redirects by default

#### Response Format

Text content:
```json
{
  "content": [
    {
      "type": "text",
      "text": "Response content here"
    }
  ]
}
```

Image content:
```json
{
  "content": [
    {
      "type": "image",
      "data": "<base64-encoded-image>",
      "mimeType": "image/png"
    }
  ]
}
```

Error response:
```json
{
  "content": [
    {
      "type": "text",
      "text": "Error: Connection timeout"
    }
  ],
  "isError": true
}
```

## Testing

Run tests using the project's testing infrastructure:

```bash
# Run all tests
just test

# Run specific tests
just test test_mcp_fetch

# Run with coverage
just test-sidecar-coverage
```

Tests should verify real protocol interactions without mocks:
- Protocol handshake via initialize
- Tool listing and execution
- Security boundary validation
- Error handling scenarios

## Deployment

### Production Configuration

1. Deploy behind Traefik with appropriate routing labels
2. Configure ForwardAuth middleware for authentication
3. Set all environment variables via .env file
4. Enable health checks for monitoring
5. Use docker-compose for orchestration

### Health Monitoring

The service can be monitored by sending an initialize request:

```bash
curl -X POST http://localhost:3000/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"monitoring","version":"1.0"}},"id":1}'
```

A successful response with matching protocol version indicates health.

## Development

### Project Structure

```
mcp-fetch-streamablehttp-server/
├── src/
│   └── mcp_fetch_streamablehttp_server/
│       ├── __init__.py          # Package initialization
│       ├── __main__.py          # Entry point
│       ├── server.py            # FastAPI application
│       ├── transport.py         # StreamableHTTP transport
│       └── fetch_handler.py     # Fetch tool implementation
├── pyproject.toml               # Package configuration
├── CLAUDE.md                    # Divine implementation guide
└── README.md                    # This file
```

### Adding Features

When extending this service:
1. Maintain stateless operation
2. Add new tools via the MCP tools interface
3. Configure via environment variables
4. Include security validations
5. Follow existing error handling patterns

## Security Considerations

- Never add authentication code (handled by Traefik)
- Validate all URLs against SSRF patterns
- Limit response sizes to prevent DoS
- Use timeout controls for all HTTP operations
- Follow the principle of least privilege

## License

Part of the MCP OAuth Gateway project.
