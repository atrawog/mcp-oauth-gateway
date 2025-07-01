# mcp-echo-streamablehttp-server-stateful

## Overview

The `mcp-echo-streamablehttp-server-stateful` is a comprehensive diagnostic MCP server that maintains session state across requests. It provides 11 powerful debugging tools specifically designed for testing OAuth flows, session management, and MCP protocol compliance. This stateful variant is essential for testing scenarios that require persistent state between requests.

## Architecture

### Stateful Design

```
┌──────────────┐    HTTP + Session    ┌─────────────────────┐
│  MCP Client  │ ←─────────────────→ │  Stateful Echo      │
│              │    Mcp-Session-Id    │  Server             │
└──────────────┘                      └─────────────────────┘
                                              │
                                              ▼
                                      ┌─────────────────────┐
                                      │  Session Storage    │
                                      │  - UUID tracking    │
                                      │  - Message queues   │
                                      │  - State data       │
                                      └─────────────────────┘
```

### Core Components

```
mcp_echo_streamablehttp_server_stateful/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point
├── server.py            # Main server with SessionManager
├── tools.py             # 11 diagnostic tools
├── models.py            # Data models
├── session.py           # Session management
└── utils.py             # Helper utilities
```

## Key Features

### Session Management
- **UUID-based Sessions**: Unique session IDs via headers
- **Message Queuing**: FIFO queues per session (max 100)
- **State Persistence**: Store data between requests
- **Automatic Cleanup**: Background task removes expired sessions
- **Session Context**: Access session data in tools

### 11 Diagnostic Tools

1. **echo** - Echo messages with session context
2. **replayLastEcho** - Replay the last echoed message (demonstrates state!)
3. **printHeader** - Display all HTTP headers categorized
4. **bearerDecode** - Decode JWT tokens without verification
5. **authContext** - Show complete OAuth authentication context
6. **requestTiming** - Display request performance metrics
7. **corsAnalysis** - Analyze CORS configuration
8. **environmentDump** - Show sanitized environment config
9. **healthProbe** - Deep health check with session statistics
10. **sessionInfo** - Display current session information
11. **whoIStheGOAT** - AI-powered excellence analyzer

### Protocol Features
- Full MCP 2025-06-18 compliance
- Multiple protocol version support
- JSON-RPC 2.0 implementation
- StreamableHTTP with SSE support
- Proper lifecycle management

## Installation

### Using pip
```bash
pip install mcp-echo-streamablehttp-server-stateful
```

### Using pixi
```bash
pixi add --pypi mcp-echo-streamablehttp-server-stateful
```

### Docker
```dockerfile
FROM python:3.11-slim

RUN pip install mcp-echo-streamablehttp-server-stateful

ENV MCP_ECHO_HOST=0.0.0.0
ENV MCP_ECHO_PORT=3000
ENV MCP_ECHO_DEBUG=true
ENV MCP_SESSION_TIMEOUT=3600

EXPOSE 3000

CMD ["python", "-m", "mcp_echo_streamablehttp_server_stateful"]
```

## Configuration

### Environment Variables

```bash
# Server Configuration
MCP_ECHO_HOST=0.0.0.0          # Bind address
MCP_ECHO_PORT=3000             # Server port
MCP_ECHO_DEBUG=true            # Enable debug logging

# Session Configuration
MCP_SESSION_TIMEOUT=3600       # Session timeout in seconds (1 hour)
MCP_SESSION_CLEANUP_INTERVAL=60 # Cleanup interval in seconds

# Protocol Configuration
MCP_PROTOCOL_VERSION=2025-06-18
MCP_PROTOCOL_VERSIONS_SUPPORTED=2025-06-18,2024-11-05

# Logging
LOG_FILE=/logs/mcp-echo-stateful.log
```

## Session Management Details

### SessionManager Class

```python
class SessionManager:
    """Manages MCP sessions with message queuing and cleanup."""

    def __init__(self, session_timeout: int = 3600):
        self.sessions: dict[str, dict[str, Any]] = {}
        self.message_queues: dict[str, deque] = defaultdict(deque)
        self.session_timeout = session_timeout
        self._cleanup_task: asyncio.Task | None = None
```

### Session Data Structure

```python
{
    "session_id": "uuid-v4",
    "created_at": 1234567890.0,  # Unix timestamp
    "last_activity": 1234567890.0,
    "initialized": True,
    "protocol_version": "2025-06-18",
    "client_info": {
        "name": "example-client",
        "version": "1.0"
    },
    "state": {
        "last_echo": "Hello, World!",  # Tool-specific state
        "echo_count": 5,
        "custom_data": {}
    }
}
```

### Message Queue Implementation

```python
# Message queuing per session
def queue_message(self, session_id: str, message: dict):
    """Queue a message for async delivery."""
    queue = self.message_queues[session_id]

    # Prevent queue overflow
    if len(queue) >= MAX_MESSAGE_QUEUE_SIZE:
        queue.popleft()  # Remove oldest

    queue.append(message)
```

## API Endpoints

### POST /mcp
Main endpoint for JSON-RPC requests.

**Request Headers**:
- `Content-Type: application/json`
- `Accept: application/json, text/event-stream`
- `Mcp-Session-Id: <uuid>` (returned after initialize)

**Session Creation**:
```json
{
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
}
```

**Response Headers**:
- `Mcp-Session-Id: 550e8400-e29b-41d4-a716-446655440000`

### GET /mcp
Poll for queued messages (requires session).

**Request Headers**:
- `Mcp-Session-Id: <uuid>` (required)
- `Accept: text/event-stream`

**Response**: Server-Sent Events stream
```
event: message
data: {"jsonrpc":"2.0","method":"notification","params":{}}

event: keep-alive
data: {"type":"ping"}
```

## Diagnostic Tools in Detail

### 1. echo
Simple echo with session tracking.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "echo",
    "arguments": {
      "message": "Hello, stateful world!",
      "uppercase": true
    }
  },
  "id": 2
}
```

**Response**:
```json
{
  "content": [{
    "type": "text",
    "text": "HELLO, STATEFUL WORLD!\n\nSession: 550e8400-e29b-41d4-a716-446655440000\nEcho count in session: 1"
  }]
}
```

### 2. replayLastEcho
Demonstrates stateful behavior.

**Response**:
```json
{
  "content": [{
    "type": "text",
    "text": "🔄 Replaying last echo:\nHELLO, STATEFUL WORLD!\n\nOriginal echo count: 1\nThis session has replayed 1 messages"
  }]
}
```

### 3. printHeader
Categorized header display.

**Response**:
```json
{
  "content": [{
    "type": "text",
    "text": "📋 HTTP Headers Analysis\n\n🔐 Authentication Headers:\n  Authorization: Bearer eyJhbGc...\n  X-User-Id: 12345\n  X-User-Name: johndoe\n\n🌐 Standard Headers:\n  Host: mcp-echo.example.com\n  User-Agent: MCP-Client/1.0\n\n🔄 MCP Headers:\n  Mcp-Session-Id: 550e8400...\n\n📊 Header Statistics:\n  Total headers: 15\n  Auth headers: 3\n  Custom headers: 2"
  }]
}
```

### 4. bearerDecode
JWT debugging without verification.

**Request**:
```json
{
  "name": "bearerDecode",
  "arguments": {
    "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Response**:
```json
{
  "content": [{
    "type": "text",
    "text": "🔍 JWT Token Analysis\n\nHeader:\n{\n  \"alg\": \"RS256\",\n  \"typ\": \"JWT\"\n}\n\nPayload:\n{\n  \"sub\": \"user123\",\n  \"name\": \"John Doe\",\n  \"iat\": 1516239022,\n  \"exp\": 1516242622\n}\n\n⏱️ Token Status:\n- Issued: 2018-01-18 01:30:22 UTC\n- Expires: 2018-01-18 02:30:22 UTC\n- Status: EXPIRED"
  }]
}
```

### 5. authContext
Complete authentication analysis.

**Response**:
```json
{
  "content": [{
    "type": "text",
    "text": "🔐 Authentication Context\n\n👤 User Information:\n- User ID: 12345\n- Username: johndoe\n- GitHub User: johndoe\n\n🎫 Token Details:\n- Token Type: Bearer\n- Token Length: 847 characters\n- Token Preview: eyJhbG...AbC123\n\n🔑 Derived Information:\n- Authentication: ✅ Authenticated\n- Session: 550e8400-e29b-41d4-a716-446655440000\n- Request ID: req_abc123"
  }]
}
```

### 6. requestTiming
Performance metrics with session context.

**Response**:
```json
{
  "content": [{
    "type": "text",
    "text": "⏱️ Request Timing Analysis\n\n📊 Performance Metrics:\n- Request Start: 2024-01-01 12:00:00.123 UTC\n- Processing Time: 23.45ms\n- Performance: 🟢 Excellent\n\n🖥️ System Resources:\n- CPU Usage: 15.2%\n- Memory Usage: 256MB / 1024MB (25%)\n- Active Sessions: 5\n- Message Queue Size: 12\n\n📈 Session Statistics:\n- Session Age: 5m 30s\n- Requests in Session: 42\n- Average Response Time: 18.7ms"
  }]
}
```

### 7. sessionInfo
Current session details.

**Response**:
```json
{
  "content": [{
    "type": "text",
    "text": "📊 Session Information\n\n🔑 Session Details:\n- Session ID: 550e8400-e29b-41d4-a716-446655440000\n- Created: 2024-01-01 12:00:00 UTC\n- Last Activity: 2024-01-01 12:05:30 UTC\n- Age: 5m 30s\n- Time Until Expiry: 54m 30s\n\n📈 Session Metrics:\n- Total Requests: 42\n- Echo Count: 5\n- Replay Count: 2\n- Message Queue: 3 pending\n\n🧠 Session State:\n- Initialized: ✅\n- Protocol Version: 2025-06-18\n- Client: test-client v1.0"
  }]
}
```

### 8. healthProbe
Deep health check with session stats.

**Response**:
```json
{
  "content": [{
    "type": "text",
    "text": "🏥 System Health Report\n\n✅ Overall Status: HEALTHY\n\n📊 Session Statistics:\n- Active Sessions: 5\n- Total Sessions Created: 127\n- Sessions Expired: 122\n- Cleanup Run Count: 61\n- Last Cleanup: 45s ago\n\n💾 Memory Status:\n- Process Memory: 256MB\n- Session Storage: 12KB\n- Message Queues: 8KB\n\n⚡ Performance:\n- Average Session Lifetime: 12m 30s\n- Session Creation Rate: 0.5/min\n- Message Queue Depth: 3.2 avg"
  }]
}
```

## Usage Examples

### Initialize and Use Stateful Tools

```python
import httpx
import asyncio

async def test_stateful_echo():
    async with httpx.AsyncClient() as client:
        # Initialize session
        init_response = await client.post(
            "http://localhost:3000/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"}
                },
                "id": 1
            }
        )

        # Extract session ID
        session_id = init_response.headers.get("Mcp-Session-Id")

        # First echo
        echo1 = await client.post(
            "http://localhost:3000/mcp",
            headers={"Mcp-Session-Id": session_id},
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "echo",
                    "arguments": {"message": "First message"}
                },
                "id": 2
            }
        )

        # Replay last echo (stateful!)
        replay = await client.post(
            "http://localhost:3000/mcp",
            headers={"Mcp-Session-Id": session_id},
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "replayLastEcho",
                    "arguments": {}
                },
                "id": 3
            }
        )

        print(replay.json())

asyncio.run(test_stateful_echo())
```

### Message Queue Polling

```javascript
// Poll for queued messages
const eventSource = new EventSource(
  'http://localhost:3000/mcp',
  {
    headers: {
      'Mcp-Session-Id': sessionId
    }
  }
);

eventSource.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
});

eventSource.addEventListener('keep-alive', (event) => {
  console.log('Keep-alive ping');
});
```

### Session Management

```bash
# Create session and get info
SESSION_ID=$(curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' \
  -i | grep -i mcp-session-id | cut -d' ' -f2 | tr -d '\r')

# Check session info
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"sessionInfo","arguments":{}},"id":2}'
```

## Docker Compose Integration

```yaml
services:
  mcp-echo-stateful:
    build: ./mcp-echo-streamablehttp-server-stateful
    environment:
      - MCP_ECHO_HOST=0.0.0.0
      - MCP_ECHO_PORT=3000
      - MCP_ECHO_DEBUG=true
      - MCP_SESSION_TIMEOUT=3600
      - MCP_PROTOCOL_VERSION=2025-06-18
    networks:
      - internal
    volumes:
      - ./logs:/logs
    healthcheck:
      test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-06-18\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
        | grep -q '\"protocolVersion\":\"2025-06-18\"'"]
      interval: 30s
      timeout: 5s
      retries: 3
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mcp-echo-stateful.rule=Host(`mcp-echo-stateful.${BASE_DOMAIN}`)"
      - "traefik.http.routers.mcp-echo-stateful.priority=2"
      - "traefik.http.routers.mcp-echo-stateful.middlewares=mcp-auth"
      - "traefik.http.services.mcp-echo-stateful.loadbalancer.server.port=3000"
```

## Performance Considerations

### Session Storage
- In-memory storage (no persistence)
- O(1) session lookup
- Automatic expiration
- Bounded message queues

### Resource Usage
- ~50KB per active session
- Background cleanup every 60s
- Non-blocking async I/O
- Efficient deque for messages

### Scaling Limitations
- Single instance only (in-memory state)
- No session replication
- Sessions lost on restart
- Consider Redis for production

## Monitoring and Debugging

### Debug Mode
```bash
# Enable debug logging
export MCP_ECHO_DEBUG=true
export LOG_LEVEL=DEBUG
python -m mcp_echo_streamablehttp_server_stateful
```

### Session Metrics
Monitor via `healthProbe` tool:
- Active session count
- Session creation rate
- Average session lifetime
- Memory usage
- Queue depths

### Common Issues

#### Session Not Found
```json
{
  "error": {
    "code": -32603,
    "message": "Session not found or expired"
  }
}
```
**Solution**: Create new session with initialize

#### Queue Overflow
When queue exceeds 100 messages, oldest are dropped.
**Solution**: Poll more frequently or increase limit

#### Memory Growth
Sessions not being cleaned up.
**Solution**: Check cleanup task is running

## Testing Strategies

### Unit Tests
```python
def test_session_expiration():
    """Test session cleanup."""
    manager = SessionManager(session_timeout=1)
    session_id = manager.create_session()

    # Session should exist
    assert manager.get_session(session_id) is not None

    # Wait for expiration
    time.sleep(2)
    manager.cleanup_expired_sessions()

    # Session should be gone
    assert manager.get_session(session_id) is None
```

### Integration Tests
```python
async def test_stateful_behavior():
    """Test state persistence across requests."""
    # Initialize
    session_id = await initialize_session()

    # Echo something
    await echo_message(session_id, "Test message")

    # Replay should return same message
    replay_response = await replay_last_echo(session_id)
    assert "Test message" in replay_response
```

## Best Practices

1. **Session Hygiene**: Don't create unnecessary sessions
2. **Polling Strategy**: Poll based on expected message rate
3. **Error Handling**: Always check for session expiration
4. **Resource Monitoring**: Watch memory usage in production
5. **Graceful Shutdown**: Allow cleanup task to finish
6. **Testing**: Use for integration tests, not production

## Comparison with Stateless Version

| Feature | Stateful | Stateless |
|---------|----------|-----------|
| Session persistence | ✅ Yes | ❌ No |
| Message queuing | ✅ Yes | ❌ No |
| replayLastEcho tool | ✅ Yes | ❌ No |
| sessionInfo tool | ✅ Yes | ❌ No |
| Resource usage | Higher | Lower |
| Horizontal scaling | ❌ Limited | ✅ Easy |
| Use case | Testing, debugging | Production diagnostics |

## Security Considerations

### No Authentication
- This server has NO built-in authentication
- Relies on Traefik ForwardAuth middleware
- Never expose directly to internet

### Token Decoding
- `bearerDecode` does NOT verify signatures
- For debugging only
- Never trust decoded values

### Session Security
- Sessions are not encrypted
- No session hijacking protection
- Use only in trusted environments

## Future Enhancements

- [ ] Redis backend for distributed sessions
- [ ] WebSocket support for real-time updates
- [ ] Session persistence across restarts
- [ ] Configurable message queue sizes
- [ ] Session analytics and reporting
- [ ] Rate limiting per session
- [ ] Custom state storage plugins
