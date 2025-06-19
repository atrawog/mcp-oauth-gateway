# mcp-streamablehttp-server

A generic stdio-to-streamable-HTTP server for MCP (Model Context Protocol) servers. This package allows you to expose any MCP server that uses stdio communication as streamable HTTP endpoints compatible with the MCP 2025-06-18 transport specification.

## Features

- 🔄 **Universal Compatibility**: Works with any MCP server that communicates over stdio
- 🌐 **Streamable HTTP Transport**: Exposes MCP servers via streamable HTTP endpoints following the 2025-06-18 specification
- 🔐 **Session Management**: Supports multiple concurrent sessions with automatic cleanup
- 🚀 **Easy Integration**: Simple command-line interface and Python API
- 📊 **Health Checks**: Built-in health check endpoint for monitoring
- 🔧 **Configurable**: Customizable timeouts, ports, and logging

## Installation

```bash
pip install mcp-streamablehttp-server
```

## Quick Start

### Command Line Usage

The simplest way to use the server is via the command line:

```bash
# Expose an MCP server module via streamable HTTP
mcp-streamablehttp-server python -m mcp_server_fetch

# Expose a custom MCP server command via streamable HTTP
mcp-streamablehttp-server /path/to/your/mcp-server --server-arg1 --server-arg2

# Run on a different port
mcp-streamablehttp-server --port 8080 python -m mcp_server_fetch

# Increase session timeout to 10 minutes
mcp-streamablehttp-server --timeout 600 python -m mcp_server_fetch
```

### Python API Usage

```python
from mcp_streamablehttp_server import run_server

# Run the streamable HTTP server
run_server(
    server_command=["python", "-m", "mcp_server_fetch"],
    host="0.0.0.0",
    port=3000,
    session_timeout=300,
    log_level="info"
)
```

### Docker Usage

Create a Dockerfile for your MCP server:

```dockerfile
FROM python:3.11-slim

# Install your MCP server (example: fetch server)
RUN pip install "mcp-server-fetch @ git+https://github.com/modelcontextprotocol/servers.git#subdirectory=src/fetch"

# Install the streamable HTTP server
RUN pip install mcp-streamablehttp-server

# Expose the HTTP port
EXPOSE 3000

# Run the streamable HTTP server wrapping your MCP server
CMD ["mcp-streamablehttp-server", "python", "-m", "mcp_server_fetch"]
```

## How It Works

The server acts as a bridge between streamable HTTP clients and stdio-based MCP servers:

1. **HTTP Request**: Client sends HTTP POST to `/mcp` endpoint
2. **Session Management**: Server creates or reuses a session for the client
3. **Stdio Communication**: Server forwards the request to the MCP server via stdin
4. **Response Handling**: Server reads the response from stdout and returns it via streamable HTTP

## Endpoints

### `/mcp` (POST)
Main MCP endpoint for all protocol communication.

**Headers:**
- `Content-Type: application/json` (required)
- `Mcp-Session-Id: <session-id>` (optional, returned by server after first request)

**Request Body:**
JSON-RPC 2.0 formatted MCP request

**Response:**
JSON-RPC 2.0 formatted MCP response with `Mcp-Session-Id` header

### `/health` (GET)
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "active_sessions": 2,
  "server_command": "python -m mcp_server_fetch"
}
```

## Session Management

The server manages multiple concurrent sessions:

- Each client gets its own MCP server subprocess
- Sessions are identified by `Mcp-Session-Id` header
- Sessions timeout after inactivity (default: 5 minutes)
- Expired sessions are automatically cleaned up

## Configuration

### Command Line Options

- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 3000)
- `--timeout`: Session timeout in seconds (default: 300)
- `--log-level`: Logging level: debug, info, warning, error (default: info)

### Environment Variables

You can also configure the server using environment variables:

```bash
export MCP_PROXY_HOST=0.0.0.0
export MCP_PROXY_PORT=3000
export MCP_PROXY_TIMEOUT=300
export MCP_PROXY_LOG_LEVEL=info
```

## Advanced Usage

### Custom FastAPI Integration

You can integrate the server into your existing FastAPI application:

```python
from fastapi import FastAPI
from mcp_streamablehttp_server import create_app

# Create your main app
main_app = FastAPI()

# Create MCP streamable HTTP server app
mcp_app = create_app(
    server_command=["python", "-m", "mcp_server_fetch"],
    session_timeout=300
)

# Mount the MCP app
main_app.mount("/mcp-server", mcp_app)
```

### Monitoring and Logging

The server provides detailed logging for debugging:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Run with debug logging
from mcp_streamablehttp_server import run_server

run_server(
    server_command=["python", "-m", "mcp_server_fetch"],
    log_level="debug"
)
```

## Error Handling

The server handles various error scenarios:

- **Server startup failures**: Returns 503 Service Unavailable
- **Invalid requests**: Returns 400 Bad Request
- **Session timeouts**: Returns 408 Request Timeout
- **Server crashes**: Automatically cleans up and returns 500 Internal Server Error

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-streamablehttp-server.git
cd mcp-streamablehttp-server

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
black .
mypy .
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built for the [Model Context Protocol](https://modelcontextprotocol.io/)
- Inspired by the need for HTTP transport compatibility
- Thanks to the MCP community for feedback and contributions