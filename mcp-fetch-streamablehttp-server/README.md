# MCP Fetch Streamable HTTP Server

A native Python implementation of an MCP fetch server with Streamable HTTP transport, implementing the MCP 2025-06-18 protocol specification from scratch.

## Features

- **Native Streamable HTTP Transport**: Implements the transport layer from scratch without using proxy patterns
- **Fetch Tool**: Supports GET and POST requests with robots.txt compliance
- **Stateless Operation**: Each request is handled independently for better scalability
- **OAuth Ready**: Designed to work with Bearer token authentication
- **Production Ready**: Includes health checks, proper error handling, and Docker support

## Architecture

Unlike the proxy-based approach, this implementation:
- Runs as a native Python ASGI application using FastAPI
- Implements the MCP protocol directly without subprocesses
- Provides better performance and error handling
- Integrates seamlessly with the OAuth gateway

## Installation

```bash
pip install -e .
```

## Running

### Direct execution
```bash
python -m mcp_fetch_streamablehttp_server
```

### With Docker
```bash
# Docker configuration is in ../mcp-fetchs/
cd ../mcp-fetchs
docker-compose up -d
```

## Configuration

Environment variables:
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 3000)
- `MCP_FETCH_SERVER_NAME`: Server name (default: mcp-fetch-streamablehttp)
- `MCP_FETCH_PROTOCOL_VERSION`: MCP protocol version (default: 2025-06-18)
- `MCP_FETCH_DEFAULT_USER_AGENT`: Default user agent for fetch requests

## API Endpoints

- `POST /mcp`: Main MCP endpoint for JSON-RPC requests
- `GET /health`: Health check endpoint
- `OPTIONS /mcp`: CORS preflight support

## Supported MCP Methods

- `initialize`: Initialize MCP session
- `tools/list`: List available tools
- `tools/call`: Execute the fetch tool

## Fetch Tool

The fetch tool supports:
- HTTP GET and POST requests
- Custom headers and request bodies
- Robots.txt compliance checking
- Automatic content type detection (text/image)
- Response size limits
- User agent customization