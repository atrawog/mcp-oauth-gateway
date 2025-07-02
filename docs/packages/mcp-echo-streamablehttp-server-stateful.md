# mcp-echo-streamablehttp-server-stateful

A comprehensive diagnostic MCP server that maintains session state across requests, providing 11 specialized debugging tools for testing OAuth flows, session management, and MCP protocol compliance.

## Quick Start

**Key Features:**
- Session-aware echo operations with UUID-based tracking
- Message history and state persistence across requests
- 11 diagnostic tools for OAuth and protocol testing
- Native StreamableHTTP implementation
- Automatic session cleanup and management

**Installation:**
```bash
pip install mcp-echo-streamablehttp-server-stateful
# or
pixi add --pypi mcp-echo-streamablehttp-server-stateful
```

**Basic Usage:**
```bash
# Start the server
python -m mcp_echo_streamablehttp_server_stateful

# Initialize a session
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18"},"id":1}'
```

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Diagnostic Tools Reference](#diagnostic-tools-reference)
6. [Session Management](#session-management)
7. [API Endpoints](#api-endpoints)
8. [Usage Examples](#usage-examples)
9. [Docker Deployment](#docker-deployment)
10. [Performance & Scaling](#performance--scaling)
11. [Monitoring & Debugging](#monitoring--debugging)
12. [Testing Strategies](#testing-strategies)
13. [Security Considerations](#security-considerations)
14. [Comparison with Stateless Version](#comparison-with-stateless-version)

## Overview

The `mcp-echo-streamablehttp-server-stateful` is a diagnostic MCP server specifically designed for testing scenarios that require persistent state between requests. It's essential for validating OAuth flows, session management, and complex MCP protocol interactions in the gateway environment.

### Core Capabilities

- **Session Management**: UUID-based sessions with automatic cleanup
- **State Persistence**: Maintains data across multiple requests
- **Message Queuing**: FIFO queues per session (max 100 messages)
- **Protocol Testing**: Full MCP 2025-06-18 compliance validation
- **OAuth Debugging**: JWT decoding, auth context analysis, CORS testing
- **Performance Analysis**: Request timing, resource monitoring, health probes

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

### Native Implementation Benefits

- Pure Python/FastAPI implementation
- In-memory session storage for speed
- Async request handling throughout
- Direct StreamableHTTP protocol support
- No subprocess overhead

## Installation

### Using pip
```bash
pip install mcp-echo-streamablehttp-server-stateful
```

### Using pixi
```bash
pixi add --pypi mcp-echo-streamablehttp-server-stateful
```

### Docker Installation
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install the package
RUN pip install mcp-echo-streamablehttp-server-stateful

# Configure for production
ENV MCP_ECHO_HOST=0.0.0.0
ENV MCP_ECHO_PORT=3000
ENV MCP_ECHO_DEBUG=true
ENV MCP_SESSION_TIMEOUT=3600

EXPOSE 3000

CMD ["python", "-m", "mcp_echo_streamablehttp_server_stateful"]

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
```

## Configuration

### Environment Variables

```bash
# Server Configuration
MCP_ECHO_HOST=0.0.0.0          # Bind address (default: 0.0.0.0)
MCP_ECHO_PORT=3000             # Server port (default: 3000)
MCP_ECHO_DEBUG=true            # Enable debug logging

# Session Management
MCP_SESSION_TIMEOUT=3600       # Session timeout in seconds (default: 1 hour)
MCP_SESSION_CLEANUP_INTERVAL=60 # Cleanup interval in seconds
MCP_MAX_SESSIONS=1000          # Maximum concurrent sessions
ECHO_CLEANUP_INTERVAL=300      # Legacy: cleanup interval

# Protocol Configuration
MCP_PROTOCOL_VERSION=2025-06-18
MCP_PROTOCOL_VERSIONS_SUPPORTED=2025-06-18,2024-11-05

# Feature Flags
ECHO_ENABLE_BINARY=true        # Enable binary data handling
ECHO_ENABLE_COMPRESSION=false  # Enable response compression
ECHO_MAX_MESSAGE_SIZE=1048576  # Max message size (1MB)

# Logging
ECHO_LOG_LEVEL=INFO
LOG_FILE=/logs/mcp-echo-stateful.log
```

## Diagnostic Tools Reference

### 1. echo
Echo messages with session context tracking.

**Arguments:**
- `message` (string, required): Message to echo
- `uppercase` (boolean, optional): Convert to uppercase

**Example:**
```json
{
  "name": "echo",
  "arguments": {
    "message": "Hello, stateful world!",
    "uppercase": true
  }
}
```

**Response:**
```
HELLO, STATEFUL WORLD!

Session: 550e8400-e29b-41d4-a716-446655440000
Echo count in session: 1
```

### 2. replayLastEcho
Demonstrates stateful behavior by replaying the last echoed message.

**Arguments:** None

**Response:**
```
🔄 Replaying last echo:
HELLO, STATEFUL WORLD!

Original echo count: 1
This session has replayed 1 messages
```

### 3. printHeader
Display all HTTP headers categorized by type.

**Arguments:**
- `category` (string, optional): Filter by category (auth, standard, mcp, custom)

**Response:**
```
📋 HTTP Headers Analysis

🔐 Authentication Headers:
  Authorization: Bearer eyJhbGc...
  X-User-Id: 12345
  X-User-Name: johndoe

🌐 Standard Headers:
  Host: mcp-echo.example.com
  User-Agent: MCP-Client/1.0

🔄 MCP Headers:
  Mcp-Session-Id: 550e8400...

📊 Header Statistics:
  Total headers: 15
  Auth headers: 3
  Custom headers: 2
```

### 4. bearerDecode
Decode JWT tokens without verification (debugging only).

**Arguments:**
- `token` (string, optional): JWT token to decode (uses Authorization header if not provided)

**Response:**
```
🔍 JWT Token Analysis

Header:
{
  "alg": "RS256",
  "typ": "JWT"
}

Payload:
{
  "sub": "user123",
  "name": "John Doe",
  "iat": 1516239022,
  "exp": 1516242622
}

⏱️ Token Status:
- Issued: 2018-01-18 01:30:22 UTC
- Expires: 2018-01-18 02:30:22 UTC
- Status: EXPIRED
```

### 5. authContext
Complete authentication context analysis.

**Response:**
```
🔐 Authentication Context

👤 User Information:
- User ID: 12345
- Username: johndoe
- GitHub User: johndoe

🎫 Token Details:
- Token Type: Bearer
- Token Length: 847 characters
- Token Preview: eyJhbG...AbC123

🔑 Derived Information:
- Authentication: ✅ Authenticated
- Session: 550e8400-e29b-41d4-a716-446655440000
- Request ID: req_abc123
```

### 6. requestTiming
Display request performance statistics with session context.

**Response:**
```
⏱️ Request Timing Analysis

📊 Performance Metrics:
- Request Start: 2024-01-01 12:00:00.123 UTC
- Processing Time: 23.45ms
- Performance: 🟢 Excellent

🖥️ System Resources:
- CPU Usage: 15.2%
- Memory Usage: 256MB / 1024MB (25%)
- Active Sessions: 5
- Message Queue Size: 12

📈 Session Statistics:
- Session Age: 5m 30s
- Requests in Session: 42
- Average Response Time: 18.7ms
```

### 7. corsAnalysis
Analyze CORS configuration and headers.

**Response:**
```
🌐 CORS Analysis

Allowed Origins: *
Allowed Methods: GET, POST, OPTIONS
Allowed Headers: Content-Type, Authorization, Mcp-Session-Id
Exposed Headers: Mcp-Session-Id
Max Age: 86400
Credentials: true

Status: ✅ Permissive CORS configuration
```

### 8. environmentDump
Show sanitized environment configuration.

**Response:**
```
🔧 Environment Configuration

MCP Settings:
- MCP_ECHO_HOST: 0.0.0.0
- MCP_ECHO_PORT: 3000
- MCP_SESSION_TIMEOUT: 3600

Feature Flags:
- Debug Mode: ✅ Enabled
- Binary Support: ✅ Enabled
- Compression: ❌ Disabled
```

### 9. healthProbe
Deep health check with session statistics.

**Response:**
```
🏥 System Health Report

✅ Overall Status: HEALTHY

📊 Session Statistics:
- Active Sessions: 5
- Total Sessions Created: 127
- Sessions Expired: 122
- Cleanup Run Count: 61
- Last Cleanup: 45s ago

💾 Memory Status:
- Process Memory: 256MB
- Session Storage: 12KB
- Message Queues: 8KB

⚡ Performance:
- Average Session Lifetime: 12m 30s
- Session Creation Rate: 0.5/min
- Message Queue Depth: 3.2 avg
```

### 10. sessionInfo
Display current session information.

**Response:**
```
📊 Session Information

🔑 Session Details:
- Session ID: 550e8400-e29b-41d4-a716-446655440000
- Created: 2024-01-01 12:00:00 UTC
- Last Activity: 2024-01-01 12:05:30 UTC
- Age: 5m 30s
- Time Until Expiry: 54m 30s

📈 Session Metrics:
- Total Requests: 42
- Echo Count: 5
- Replay Count: 2
- Message Queue: 3 pending

🧠 Session State:
- Initialized: ✅
- Protocol Version: 2025-06-18
- Client: test-client v1.0
```

### 11. whoIStheGOAT
AI-powered excellence analyzer (fun diagnostic tool).

**Arguments:**
- `subject` (string, optional): Subject to analyze

**Response:**
```
🐐 GOAT Analysis Complete

Subject: MCP Protocol
Excellence Score: 95/100
Greatness Factor: Legendary

Top Qualities:
- Stateful session management
- Protocol compliance
- Developer experience

Verdict: Certified GOAT 🏆
```

## Session Management

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

### Session Creation

Sessions are created automatically on first request:

```python
session_id = request.headers.get("Mcp-Session-Id") or generate_id()
sessions[session_id] = {
    "session_id": session_id,
    "created_at": time.time(),
    "last_activity": time.time(),
    "initialized": False,
    "protocol_version": None,
    "client_info": {},
    "state": {
        "last_echo": None,
        "echo_count": 0,
        "accumulated": [],
        "custom_data": {}
    }
}
```

### Message Queue Implementation

```python
def queue_message(self, session_id: str, message: dict):
    """Queue a message for async delivery."""
    queue = self.message_queues[session_id]

    # Prevent queue overflow
    if len(queue) >= MAX_MESSAGE_QUEUE_SIZE:
        queue.popleft()  # Remove oldest

    queue.append(message)
```

### Session Cleanup

```python
async def cleanup_sessions():
    """Remove expired sessions periodically."""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL)

        current_time = time.time()
        expired = [
            sid for sid, data in sessions.items()
            if current_time - data["last_activity"] > SESSION_TIMEOUT
        ]

        for sid in expired:
            del sessions[sid]
            if sid in message_queues:
                del message_queues[sid]

        logger.info(f"Cleaned up {len(expired)} expired sessions")
```

## API Endpoints

### POST /mcp
Main endpoint for JSON-RPC requests.

**Request Headers:**
- `Content-Type: application/json`
- `Accept: application/json, text/event-stream`
- `Mcp-Session-Id: <uuid>` (optional on first request)

**Initialize Request:**
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

**Response Headers:**
- `Mcp-Session-Id: 550e8400-e29b-41d4-a716-446655440000`

### GET /mcp
Poll for queued messages (requires session).

**Request Headers:**
- `Mcp-Session-Id: <uuid>` (required)
- `Accept: text/event-stream`

**Response:** Server-Sent Events stream
```
event: message
data: {"jsonrpc":"2.0","method":"notification","params":{}}

event: keep-alive
data: {"type":"ping"}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "sessions": {
    "active": 42,
    "total_created": 1337,
    "expired": 1295
  },
  "uptime_seconds": 3600,
  "version": "0.2.0"
}
```

## Usage Examples

### Python Client Example

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

### JavaScript Message Queue Polling

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

### Bash Testing Script

```bash
# Create session and get info
SESSION_ID=$(curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' \
  -i | grep -i mcp-session-id | cut -d' ' -f2 | tr -d '\r')

echo "Session ID: $SESSION_ID"

# Make an echo request
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"echo","arguments":{"message":"Hello from bash!"}},"id":2}'

# Check session info
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"sessionInfo","arguments":{}},"id":3}'
```

### Testing OAuth Context

```python
# Test with OAuth headers
headers = {
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIs...",
    "X-User-Id": "12345",
    "X-User-Name": "johndoe",
    "Mcp-Session-Id": session_id
}

# Check auth context
auth_response = await client.post(
    "http://localhost:3000/mcp",
    headers=headers,
    json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "authContext",
            "arguments": {}
        },
        "id": 4
    }
)
```

## Docker Deployment

### Docker Compose Configuration

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
      - ECHO_ENABLE_BINARY=true
      - ECHO_LOG_LEVEL=INFO
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
      start_period: 40s
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mcp-echo-stateful.rule=Host(`mcp-echo-stateful.${BASE_DOMAIN}`)"
      - "traefik.http.routers.mcp-echo-stateful.priority=2"
      - "traefik.http.routers.mcp-echo-stateful.middlewares=mcp-auth"
      - "traefik.http.services.mcp-echo-stateful.loadbalancer.server.port=3000"
```

### Production Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Create non-root user
RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
USER mcp

# Configure for production
ENV MCP_ECHO_HOST=0.0.0.0
ENV MCP_ECHO_PORT=3000
ENV MCP_SESSION_TIMEOUT=3600
ENV MCP_MAX_SESSIONS=1000

# Run the server
CMD ["python", "-m", "mcp_echo_streamablehttp_server_stateful"]

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
```

## Performance & Scaling

### Performance Characteristics

- **Latency**: < 5ms for basic echo operations
- **Throughput**: > 1000 requests/second per instance
- **Memory**: ~50KB per session + message history
- **Concurrency**: Fully async, handles parallel requests efficiently

### Resource Usage

- **Session Storage**: In-memory storage with O(1) lookup
- **Message Queues**: Bounded deque (max 100 messages per session)
- **Background Tasks**: Cleanup every 60 seconds
- **CPU**: Minimal usage except during cleanup cycles

### Scaling Limitations

- **Single Instance**: In-memory state prevents horizontal scaling
- **No Persistence**: Sessions lost on restart
- **Memory Bound**: Limited by available RAM
- **Session Limit**: Configurable via MCP_MAX_SESSIONS

### Production Considerations

For production use, consider:
- Redis backend for distributed sessions
- Session persistence across restarts
- Load balancing with sticky sessions
- Monitoring memory usage trends

## Monitoring & Debugging

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
- Memory usage by component
- Message queue depths

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
Sessions not being cleaned up properly.
**Solution**: Check cleanup task is running, verify SESSION_TIMEOUT

#### Protocol Version Mismatch
```json
{
  "error": {
    "code": -32602,
    "message": "Unsupported protocol version"
  }
}
```
**Solution**: Use supported version from capabilities

### Logging

The server provides structured logging:

```python
logger.info("Session created", extra={
    "session_id": session_id,
    "client_name": client_info.get("name"),
    "protocol_version": protocol_version
})
```

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

def test_message_queue_overflow():
    """Test queue bounds."""
    manager = SessionManager()
    session_id = manager.create_session()

    # Fill queue beyond limit
    for i in range(150):
        manager.queue_message(session_id, {"msg": i})

    # Should only have 100 messages
    queue = manager.get_message_queue(session_id)
    assert len(queue) == 100
    assert queue[0]["msg"] == 50  # First 50 dropped
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

async def test_session_isolation():
    """Test sessions are isolated."""
    session1 = await initialize_session()
    session2 = await initialize_session()

    # Echo in session 1
    await echo_message(session1, "Session 1 message")

    # Session 2 should not see it
    info2 = await get_session_info(session2)
    assert info2["echo_count"] == 0
```

### Load Testing

```python
async def load_test():
    """Test with many concurrent sessions."""
    sessions = []

    # Create 100 sessions
    for i in range(100):
        session_id = await initialize_session()
        sessions.append(session_id)

    # Make requests concurrently
    tasks = []
    for session_id in sessions:
        task = echo_message(session_id, f"Load test {session_id}")
        tasks.append(task)

    await asyncio.gather(*tasks)

    # Check health
    health = await check_health()
    assert health["sessions"]["active"] == 100
```

## Security Considerations

### No Built-in Authentication
- This server has NO authentication mechanisms
- Relies entirely on Traefik ForwardAuth middleware
- Never expose directly to the internet

### Token Handling
- `bearerDecode` does NOT verify JWT signatures
- Used for debugging only, not security
- Never trust decoded values for authorization

### Session Security
- Sessions are not encrypted in memory
- No built-in session hijacking protection
- Session IDs should be treated as sensitive
- Use HTTPS in production environments

### Input Validation
- All tool inputs are validated
- Message size limits enforced
- No code execution capabilities

## Comparison with Stateless Version

| Feature | Stateful | Stateless |
|---------|----------|-----------|
| Session persistence | ✅ Yes | ❌ No |
| Message queuing | ✅ Yes | ❌ No |
| State-dependent tools | ✅ Yes (replayLastEcho, sessionInfo) | ❌ No |
| Resource usage | Higher (~50KB/session) | Lower (minimal) |
| Horizontal scaling | ❌ Limited | ✅ Easy |
| Use case | Testing, debugging, development | Production diagnostics |
| Complexity | Higher | Lower |
| Protocol compliance testing | ✅ Full | ✅ Full |

### When to Use Stateful

- Testing OAuth flows with session continuity
- Debugging complex multi-request scenarios
- Validating session management implementation
- Load testing with realistic session behavior
- Development and integration testing

### When to Use Stateless

- Production diagnostic endpoints
- High-scale deployments
- Simple echo/diagnostic needs
- Minimal resource footprint required
- Horizontal scaling needed
