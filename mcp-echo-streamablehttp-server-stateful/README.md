# MCP Echo StreamableHTTP Server - Stateful

A stateful diagnostic MCP echo server with session management, message queuing, and 11 comprehensive debug tools for testing OAuth flows and MCP protocol compliance.

## Features

### Stateful Session Management
- **Persistent Sessions**: UUID-based session tracking across requests
- **Message Queuing**: Per-session message buffers for async clients
- **Automatic Cleanup**: Background task removes expired sessions
- **Session Context**: Store and retrieve state between requests

### MCP Protocol Compliance
- Full MCP 2025-06-18 StreamableHTTP transport implementation
- Supports multiple protocol versions (configurable)
- JSON-RPC 2.0 message handling
- Proper initialize � initialized lifecycle

### 11 Debug Tools

1. **echo** - Echo messages with session context
2. **replayLastEcho** - Replay the last echoed message (stateful feature!)
3. **printHeader** - Display all HTTP headers categorized
4. **bearerDecode** - Decode JWT tokens without verification
5. **authContext** - Show OAuth authentication context
6. **requestTiming** - Display request performance metrics
7. **corsAnalysis** - Analyze CORS configuration
8. **environmentDump** - Show sanitized environment config
9. **healthProbe** - Deep health check with session stats
10. **sessionInfo** - Display session information and statistics
11. **whoIStheGOAT** - AI-powered excellence analyzer

## Endpoints

### POST /mcp
- Accepts JSON-RPC 2.0 requests
- Creates/manages sessions via Mcp-Session-Id header
- Supports both JSON and SSE response formats
- Returns session ID for stateful clients

### GET /mcp
- Polls for queued messages (requires session ID)
- Returns Server-Sent Events (SSE) stream
- Sends keep-alive pings when queue is empty

## Configuration

Environment variables:
- `MCP_ECHO_HOST` - Host to bind (default: 0.0.0.0)
- `MCP_ECHO_PORT` - Port to bind (default: 3000)
- `MCP_ECHO_DEBUG` - Enable debug logging (default: true)
- `MCP_SESSION_TIMEOUT` - Session timeout in seconds (default: 3600)
- `MCP_PROTOCOL_VERSION` - Default protocol version (default: 2025-06-18)
- `MCP_PROTOCOL_VERSIONS_SUPPORTED` - Comma-separated supported versions

## Installation

### Using pip

```bash
pip install mcp-echo-streamablehttp-server-stateful
```

### Using pixi

```bash
pixi add --pypi mcp-echo-streamablehttp-server-stateful
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install the package
RUN pip install mcp-echo-streamablehttp-server-stateful

# Set environment variables
ENV MCP_ECHO_HOST=0.0.0.0
ENV MCP_ECHO_PORT=3000
ENV MCP_ECHO_DEBUG=true

# Expose the port
EXPOSE 3000

# Run the server
CMD ["python", "-m", "mcp_echo_streamablehttp_server_stateful"]
```

The service includes:
- Health check with protocol validation
- Traefik labels for OAuth integration
- Volume mounts for logs
- Automatic HTTPS via Let's Encrypt

## Session Features

### Message Queuing
- FIFO queue per session (max 100 messages)
- Automatic overflow protection
- Complete queue drain on GET requests

### Session Storage
Each session maintains:
- Creation and last activity timestamps
- Protocol version and client info
- Initialization state
- Custom application state (e.g., last echo message)

### Background Cleanup
- Runs every 60 seconds
- Removes sessions older than timeout
- Clears associated message queues

## Quick Start

### Running Locally

```bash
# Using pip/pixi installation
mcp-echo-stateful-server

# Or using Python module
python -m mcp_echo_streamablehttp_server_stateful

# With custom configuration
MCP_ECHO_PORT=8080 MCP_SESSION_TIMEOUT=7200 mcp-echo-stateful-server
```

### Using with Docker Compose

```yaml
services:
  mcp-echo-stateful:
    image: mcp-echo-stateful:latest
    build:
      context: ./mcp-echo-streamablehttp-server-stateful
    environment:
      - MCP_ECHO_HOST=0.0.0.0
      - MCP_ECHO_PORT=3000
      - MCP_ECHO_DEBUG=true
      - MCP_SESSION_TIMEOUT=3600
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

## Example Usage

### Initialize Session
```bash
curl -X POST https://echo-stateful.yourdomain.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","clientInfo":{"name":"test","version":"1.0"}},"id":1}'
```

### Use Stateful Tool
```bash
curl -X POST https://echo-stateful.yourdomain.com/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: <session-id-from-initialize>" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"replayLastEcho","arguments":{}},"id":2}'
```

## Differences from Stateless Version

This stateful version adds:
- Session management with UUID tracking
- Message queuing for async delivery
- Stateful tools (replayLastEcho)
- GET endpoint for message polling
- Background cleanup tasks
- Session statistics and monitoring

## License

Apache 2.0 - See LICENSE file for details.
