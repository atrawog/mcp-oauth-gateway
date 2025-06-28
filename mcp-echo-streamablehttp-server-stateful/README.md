# MCP Echo StreamableHTTP Server - Stateful

A **stateful** MCP Echo Server implementing MCP 2025-06-18 StreamableHTTP transport specification with session management for VS Code compatibility.

## Features

- **Session Management**: Creates and maintains sessions with unique IDs
- **Message Queuing**: Stores messages for retrieval via GET requests
- **VS Code Compatible**: Works with VS Code MCP extension
- **Dual Response Modes**: Supports both JSON and SSE responses based on Accept header
- **Session Cleanup**: Automatic cleanup of expired sessions
- **Comprehensive Tools**: 11 diagnostic and analysis tools including AI-powered excellence analysis
- **Protocol Compliance**: Full MCP 2025-06-18 specification compliance

## Architecture

Unlike the stateless version, this server maintains:

- **Session State**: Each client gets a unique session ID
- **Message Queues**: Messages are queued per session for polling
- **Session Lifecycle**: Proper initialization, activity tracking, and cleanup
- **Background Tasks**: Automatic session cleanup and maintenance

## Key Differences from Stateless Version

| Feature | Stateless | Stateful |
|---------|-----------|----------|
| Session Management | ❌ None | ✅ Full session lifecycle |
| Message Queuing | ❌ Direct response | ✅ Queued for polling |
| GET Request Handling | ❌ Simple keep-alive | ✅ Message retrieval |
| Session Cleanup | ❌ N/A | ✅ Automatic background cleanup |
| Memory Usage | ✅ Minimal | ⚠️  Grows with sessions |

## Installation

```bash
# Install the package
pip install -e .

# Or run directly
python -m mcp_echo_streamablehttp_server_stateful
```

## Usage

### Command Line

```bash
# Basic usage
mcp-echo-stateful

# With custom settings
mcp-echo-stateful --host 0.0.0.0 --port 3000 --debug --session-timeout 7200

# Environment variables
export MCP_ECHO_HOST=0.0.0.0
export MCP_ECHO_PORT=3000
export MCP_ECHO_DEBUG=true
export MCP_SESSION_TIMEOUT=3600
mcp-echo-stateful
```

### Docker

```bash
# Build the image
docker build -t mcp-echo-stateful .

# Run with environment variables
docker run -p 3000:3000 \
  -e MCP_ECHO_DEBUG=true \
  -e MCP_SESSION_TIMEOUT=3600 \
  mcp-echo-stateful
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `MCP_ECHO_HOST` | `0.0.0.0` | Host to bind to |
| `MCP_ECHO_PORT` | `3000` | Port to bind to |
| `MCP_ECHO_DEBUG` | `false` | Enable debug logging |
| `MCP_SESSION_TIMEOUT` | `3600` | Session timeout in seconds |
| `MCP_PROTOCOL_VERSIONS_SUPPORTED` | `2025-06-18,2025-03-26,2024-11-05` | Supported protocol versions |

## Session Management

### Session Lifecycle

1. **Creation**: Session created on first `initialize` request
2. **Initialization**: Client sends `initialize` with protocol negotiation
3. **Active**: Session receives requests and queues responses
4. **Polling**: Client polls with GET requests to retrieve messages
5. **Cleanup**: Session automatically expires after timeout

### Session Headers

- **Request**: `Mcp-Session-Id: <session-id>` (optional for initialize)
- **Response**: `Mcp-Session-Id: <session-id>` (provided by server)

### Message Flow

```
POST /mcp (initialize) → Server creates session → Returns session ID
POST /mcp (tools/list) → Server queues response → Returns via SSE or JSON
GET /mcp (with session ID) → Server returns queued messages → Client receives
```

## Tools Available

1. **echo** - Echo back messages with session context
2. **printHeader** - Display HTTP headers and session info
3. **bearerDecode** - JWT token analysis
4. **authContext** - Complete authentication context
5. **requestTiming** - Performance metrics
6. **protocolNegotiation** - Protocol version analysis
7. **corsAnalysis** - CORS configuration analysis
8. **environmentDump** - Sanitized environment display
9. **healthProbe** - Deep health check with session stats
10. **sessionInfo** - ⭐ **NEW**: Session management statistics
11. **whoIStheGOAT** - AI-powered programmer excellence analysis

## VS Code Integration

This stateful server is specifically designed to work with VS Code MCP extension:

```json
{
  "mcpServers": {
    "echo-stateful": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "https://echo-stateful.yourdomain.com/mcp",
        "-H", "Content-Type: application/json",
        "-H", "Accept: application/json, text/event-stream",
        "-H", "Authorization: Bearer YOUR_TOKEN"
      ],
      "transport": "http"
    }
  }
}
```

## API Examples

### Initialize Session

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {},
      "clientInfo": {"name": "test-client", "version": "1.0"}
    },
    "id": 1
  }'
```

### Poll for Messages

```bash
curl -X GET http://localhost:3000/mcp \
  -H "Mcp-Session-Id: YOUR_SESSION_ID" \
  -H "Accept: text/event-stream"
```

### Session Information

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: YOUR_SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "sessionInfo",
      "arguments": {}
    },
    "id": 2
  }'
```

## Monitoring

### Session Statistics

- **Total Active Sessions**: Current number of active sessions
- **Session Age**: How long each session has been active
- **Message Queues**: Number of queued messages per session
- **Memory Usage**: Session storage memory consumption

### Health Checks

The server provides comprehensive health checking via the `healthProbe` tool:

- System resource usage
- Session management statistics
- Protocol compliance verification
- Performance metrics

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Test with VS Code simulation
python tests/test_vscode_integration.py
```

### Architecture Notes

- **Session Storage**: In-memory dictionary (consider Redis for production)
- **Message Queues**: Per-session deques with size limits
- **Background Tasks**: Asyncio tasks for cleanup
- **Thread Safety**: Single-threaded asyncio design

## Production Considerations

- **Memory Usage**: Sessions accumulate in memory
- **Session Limits**: Consider implementing maximum session limits
- **Persistence**: Consider Redis or database for session storage
- **Monitoring**: Implement session metrics and alerting
- **Security**: Validate session IDs and implement rate limiting

## License

Apache License 2.0 - see LICENSE file for details.
