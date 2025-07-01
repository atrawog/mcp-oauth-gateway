# mcp-echo-streamablehttp-server-stateful

A comprehensive diagnostic MCP service with session state management, providing 11 specialized echo tools for testing and debugging.

## Overview

`mcp-echo-streamablehttp-server-stateful` is a native StreamableHTTP implementation designed for testing MCP integrations. It maintains session state and provides a rich set of diagnostic tools:

- Session-aware echo operations
- State accumulation and history
- Error simulation capabilities
- Performance testing tools
- Protocol compliance validation
- Binary data handling

## Key Features

### Stateful Operations
- Session state persistence
- Message history tracking
- State accumulation patterns
- Cross-request state access
- Session statistics

### Diagnostic Tools
- 11 specialized echo variants
- Error simulation
- Latency injection
- Data transformation
- Protocol testing

### Native Implementation
- Pure Python/FastAPI
- In-memory session storage
- Async request handling
- StreamableHTTP native

## Tool Reference

### 1. echo
Basic echo that returns the input unchanged.

```json
{
  "name": "echo",
  "arguments": {
    "message": "Hello, World!"
  }
}
// Returns: "Hello, World!"
```

### 2. echo_reverse
Reverses the input string.

```json
{
  "name": "echo_reverse",
  "arguments": {
    "message": "Hello"
  }
}
// Returns: "olleH"
```

### 3. echo_upper
Converts input to uppercase.

```json
{
  "name": "echo_upper",
  "arguments": {
    "message": "hello"
  }
}
// Returns: "HELLO"
```

### 4. echo_lower
Converts input to lowercase.

```json
{
  "name": "echo_lower",
  "arguments": {
    "message": "HELLO"
  }
}
// Returns: "hello"
```

### 5. echo_length
Returns the length of the input.

```json
{
  "name": "echo_length",
  "arguments": {
    "message": "Hello"
  }
}
// Returns: 5
```

### 6. echo_repeat
Repeats the message n times.

```json
{
  "name": "echo_repeat",
  "arguments": {
    "message": "Hi",
    "times": 3
  }
}
// Returns: "HiHiHi"
```

### 7. echo_with_timestamp
Adds current timestamp to the message.

```json
{
  "name": "echo_with_timestamp",
  "arguments": {
    "message": "Event"
  }
}
// Returns: "[2024-01-01T12:00:00Z] Event"
```

### 8. echo_with_delay
Echoes after a specified delay (for timeout testing).

```json
{
  "name": "echo_with_delay",
  "arguments": {
    "message": "Delayed",
    "delay_seconds": 2
  }
}
// Returns: "Delayed" (after 2 seconds)
```

### 9. echo_error
Simulates an error condition.

```json
{
  "name": "echo_error",
  "arguments": {
    "message": "Simulated error",
    "error_code": -32603
  }
}
// Returns: JSON-RPC error with specified code
```

### 10. echo_accumulate
Accumulates messages in session state.

```json
// First call
{
  "name": "echo_accumulate",
  "arguments": {
    "message": "First"
  }
}
// Returns: "Accumulated (1): First"

// Second call
{
  "name": "echo_accumulate",
  "arguments": {
    "message": "Second"
  }
}
// Returns: "Accumulated (2): First, Second"
```

### 11. echo_state
Shows current session state.

```json
{
  "name": "echo_state",
  "arguments": {}
}
// Returns: {
//   "session_id": "abc123",
//   "created_at": "2024-01-01T12:00:00Z",
//   "message_count": 5,
//   "accumulated_messages": ["First", "Second"],
//   "last_activity": "2024-01-01T12:05:00Z"
// }
```

## Session Management

### Session Creation

Sessions are created automatically on first request:

```python
session_id = request.headers.get("Mcp-Session-Id") or generate_id()
sessions[session_id] = {
    "created_at": datetime.utcnow(),
    "messages": [],
    "accumulated": [],
    "request_count": 0
}
```

### Session State Structure

```python
{
    "session_id": "uuid-here",
    "created_at": "2024-01-01T00:00:00Z",
    "last_activity": "2024-01-01T00:05:00Z",
    "request_count": 42,
    "messages": [
        {"timestamp": "...", "tool": "echo", "input": "...", "output": "..."}
    ],
    "accumulated": ["msg1", "msg2", "msg3"],
    "custom_data": {}
}
```

### Session Cleanup

```python
# Configurable session timeout
SESSION_TIMEOUT = 3600  # 1 hour

# Periodic cleanup
async def cleanup_sessions():
    cutoff = datetime.utcnow() - timedelta(seconds=SESSION_TIMEOUT)
    expired = [sid for sid, data in sessions.items()
               if data["last_activity"] < cutoff]
    for sid in expired:
        del sessions[sid]
```

## Configuration

### Environment Variables

```bash
# Server settings
ECHO_HOST=0.0.0.0
ECHO_PORT=3000

# Session management
ECHO_SESSION_TIMEOUT=3600
ECHO_MAX_SESSIONS=1000
ECHO_CLEANUP_INTERVAL=300

# Feature flags
ECHO_ENABLE_BINARY=true
ECHO_ENABLE_COMPRESSION=false
ECHO_MAX_MESSAGE_SIZE=1048576

# Logging
ECHO_LOG_LEVEL=INFO
```

## Advanced Usage

### Testing Error Conditions

```python
# Test timeout handling
response = await call_tool("echo_with_delay", {
    "message": "Test timeout",
    "delay_seconds": 35  # Longer than typical timeout
})

# Test error responses
response = await call_tool("echo_error", {
    "message": "Database connection failed",
    "error_code": -32603  # Internal error
})
```

### Load Testing

```python
# Accumulate many messages
for i in range(1000):
    await call_tool("echo_accumulate", {
        "message": f"Message {i}"
    })

# Check performance
state = await call_tool("echo_state", {})
print(f"Processed {state['request_count']} requests")
```

### Session Testing

```python
# Create multiple sessions
sessions = []
for i in range(10):
    session_id = f"test-session-{i}"
    # Make requests with different session IDs
    await make_request(session_id, "echo", {"message": f"Session {i}"})
    sessions.append(session_id)

# Verify session isolation
for session_id in sessions:
    state = await get_session_state(session_id)
    assert len(state["messages"]) == 1
```

## Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install the package
COPY pyproject.toml .
RUN pip install .

# Configure for production
ENV ECHO_SESSION_TIMEOUT=3600
ENV ECHO_MAX_SESSIONS=1000

# Run the server
CMD ["python", "-m", "mcp_echo_streamablehttp_server_stateful"]

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
```

## Testing Patterns

### Protocol Compliance

```bash
# Test initialization
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {}
    },
    "id": 1
  }'
```

### State Persistence

```bash
# First request - create session
SESSION_ID=$(uuidgen)
curl -X POST http://localhost:3000/mcp \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", ...}'

# Later request - same session
curl -X POST http://localhost:3000/mcp \
  -H "Mcp-Session-Id: $SESSION_ID" \
  ...
```

### Error Simulation

```python
# Test client error handling
try:
    result = await client.call_tool("echo_error", {
        "message": "Simulated failure",
        "error_code": -32600  # Invalid request
    })
except MCPError as e:
    assert e.code == -32600
    print(f"Handled error: {e.message}")
```

## Performance Characteristics

- **Latency**: < 5ms for basic echo operations
- **Throughput**: > 1000 requests/second
- **Memory**: ~1KB per session + message history
- **Concurrency**: Fully async, handles parallel requests

## Monitoring

### Health Endpoint

```http
GET /health

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

### Metrics

- Active session count
- Request rate by tool
- Average response time
- Error rate by type
- Session duration distribution

## Use Cases

1. **Integration Testing**: Validate MCP client implementations
2. **Protocol Development**: Test new protocol features
3. **Performance Testing**: Benchmark client performance
4. **Error Handling**: Verify error condition handling
5. **Session Management**: Test stateful interactions
6. **Load Testing**: Stress test infrastructure
