# MCP Echo StreamableHTTP Server - Stateless

A stateless diagnostic MCP (Model Context Protocol) server that implements the StreamableHTTP transport specification. This server provides comprehensive debugging tools for MCP protocol development and OAuth authentication flow analysis.

## Overview

This is a **stateless** implementation of an MCP echo server designed specifically for:
- Protocol debugging and validation
- Authentication flow analysis
- System diagnostics and health monitoring
- MCP client integration testing

Unlike the stateful variant, this server maintains no session state between requests, making each request completely independent.

## Features

### 9 Diagnostic Tools

1. **echo** - Simple message echo for basic connectivity testing
2. **printHeader** - Displays all HTTP headers organized by category
3. **bearerDecode** - Decodes JWT Bearer tokens (without verification) for debugging
4. **authContext** - Provides complete authentication context analysis
5. **requestTiming** - Shows request performance metrics and system stats
6. **corsAnalysis** - Analyzes CORS configuration and headers
7. **environmentDump** - Displays sanitized environment configuration
8. **healthProbe** - Performs deep health check with system resource monitoring
9. **whoIStheGOAT** - Easter egg that reveals programming wisdom

### Protocol Support

- **MCP Protocol Version**: 2025-06-18 (configurable)
- **Transport**: StreamableHTTP with JSON and SSE response formats
- **JSON-RPC**: 2.0 compliant
- **Session Management**: Stateless with session ID tracking via headers

### Authentication Integration

- Designed to work behind Traefik with ForwardAuth middleware
- Reads authentication headers forwarded by Traefik
- Provides JWT token decoding for debugging (no verification)
- Exposes complete authentication context through diagnostic tools

## Installation

### Using pip

```bash
pip install mcp-echo-streamablehttp-server-stateless
```

### Using pixi

```bash
pixi add --pypi mcp-echo-streamablehttp-server-stateless
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install the package
RUN pip install mcp-echo-streamablehttp-server-stateless

# Set environment variables
ENV MCP_ECHO_HOST=0.0.0.0
ENV MCP_ECHO_PORT=3000
ENV MCP_ECHO_DEBUG=false

# Expose the port
EXPOSE 3000

# Run the server
CMD ["python", "-m", "mcp_echo_streamablehttp_server_stateless"]
```

## Configuration

### Environment Variables

```bash
# Server Configuration
MCP_ECHO_HOST=127.0.0.1          # Server bind address (default: 127.0.0.1)
MCP_ECHO_PORT=3000               # Server port (default: 3000)
MCP_ECHO_DEBUG=false             # Enable debug logging (default: false)

# Protocol Configuration
MCP_PROTOCOL_VERSION=2025-06-18  # Default MCP protocol version
MCP_PROTOCOL_VERSIONS_SUPPORTED=2025-06-18,2024-11-05  # Comma-separated supported versions

# Logging
LOG_FILE=/logs/mcp-echo-stateless.log  # Optional log file path
```

### Docker Compose Integration

```yaml
services:
  mcp-echo-stateless:
    image: mcp-echo-stateless:latest
    build:
      context: ./mcp-echo-streamablehttp-server-stateless
    environment:
      - MCP_ECHO_HOST=0.0.0.0
      - MCP_ECHO_PORT=3000
      - MCP_ECHO_DEBUG=false
      - MCP_PROTOCOL_VERSION=2025-06-18
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

The service includes comprehensive Docker configuration with:
- Health checks using MCP protocol initialization
- Traefik routing labels with proper priorities
- Integration with the OAuth gateway architecture

## Quick Start

### Running Locally

```bash
# Using pip/pixi installation
mcp-echo-stateless-server

# Or using Python module
python -m mcp_echo_streamablehttp_server_stateless

# With custom configuration
MCP_ECHO_PORT=8080 MCP_ECHO_DEBUG=true mcp-echo-stateless-server
```

## Usage Examples

### Testing with Just Commands

```bash
# Test basic echo functionality
just test-mcp-tool mcp-echo-stateless echo '{"message": "Hello, World!"}'

# Analyze authentication context
just test-mcp-tool mcp-echo-stateless authContext '{}'

# View all HTTP headers
just test-mcp-tool mcp-echo-stateless printHeader '{}'

# Check system health
just test-mcp-tool mcp-echo-stateless healthProbe '{}'

# Decode a Bearer token
just test-mcp-tool mcp-echo-stateless bearerDecode '{"token": "your-jwt-token-here"}'
```

### Direct API Usage

```bash
# Initialize connection
curl -X POST https://mcp-echo-stateless.yourdomain.com/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0"
      }
    },
    "id": 1
  }'

# Call a tool
curl -X POST https://mcp-echo-stateless.yourdomain.com/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {
        "message": "Hello from MCP!"
      }
    },
    "id": 2
  }'
```

## Architecture

### Stateless Design

- No session persistence between requests
- Request context exists only for the duration of each request
- No Redis or database dependencies
- Thread-safe using Python's contextvars for request isolation

### Integration with OAuth Gateway

The service is designed to work as part of the MCP OAuth Gateway architecture:
1. Traefik routes requests based on domain/path
2. ForwardAuth middleware validates OAuth tokens
3. Authenticated requests are forwarded with user context headers
4. Service processes requests and returns responses

### Health Monitoring

The service includes a comprehensive health check that:
- Validates MCP protocol implementation
- Checks system resources (CPU, memory)
- Verifies service responsiveness
- Uses actual protocol initialization for validation

## Development

### Running Locally

```bash
# Start the service
just up mcp-echo-stateless

# View logs
just logs mcp-echo-stateless

# Run tests
just test mcp-echo-stateless
```

### Debugging

Enable debug mode for verbose logging:
```bash
MCP_ECHO_DEBUG=true just up mcp-echo-stateless
```

## Important Notes

- **Not for Production Authentication**: This service decodes tokens without verification for debugging purposes only
- **Stateless Operation**: No data persists between requests
- **Diagnostic Focus**: Designed for debugging and testing, not production workloads
- **CORS Handling**: CORS headers are managed by Traefik, not the service itself

## Related Services

- **mcp-echo-streamablehttp-server-stateful**: Stateful variant with session persistence
- **auth**: OAuth authentication service that provides token validation
- **traefik**: Reverse proxy handling routing and authentication middleware
