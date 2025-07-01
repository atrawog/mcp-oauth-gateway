# mcp-streamablehttp-proxy

The divine bridge that wraps stdio-based MCP servers with StreamableHTTP endpoints, enabling web-based access to official MCP servers.

## Overview

`mcp-streamablehttp-proxy` acts as a protocol translator in the opposite direction from the client - it wraps existing stdio MCP servers (like the official ones from modelcontextprotocol/servers) and exposes them via HTTP endpoints. This enables:

- Web access to stdio-only MCP servers
- OAuth authentication integration via gateway
- Session management for stateful servers
- Health monitoring for container orchestration

## Key Features

### Process Management
- Spawns and manages stdio MCP server subprocesses
- Handles process lifecycle (start, stop, restart)
- Monitors subprocess health
- Graceful shutdown on termination

### Protocol Translation
- HTTP POST `/mcp` endpoint for JSON-RPC
- Bidirectional stdio ↔ HTTP translation
- Preserves all protocol semantics
- Handles streaming responses

### Session Management
- Maintains session state per client
- Session ID via `Mcp-Session-Id` header
- Configurable session timeout
- Session cleanup on disconnect

## Architecture

```python
# Core components
StreamableHTTPProxy      # Main FastAPI application
SessionManager          # Client session tracking
ProcessManager          # Subprocess lifecycle
StdioTransport         # stdio communication
MessageRouter          # Request/response routing
```

## Configuration

### Command Line Arguments

```bash
mcp-streamablehttp-proxy \
  --mcp-command "mcp-server-fetch" \
  --mcp-args "--allowed-domains example.com" \
  --port 3000 \
  --host 0.0.0.0
```

### Environment Variables

```bash
# Server configuration
MCP_PROXY_PORT=3000
MCP_PROXY_HOST=0.0.0.0

# Process management
MCP_SUBPROCESS_TIMEOUT=30
MCP_STARTUP_TIMEOUT=10

# Session management
MCP_SESSION_TIMEOUT=3600
MCP_MAX_SESSIONS=100

# Logging
MCP_LOG_LEVEL=INFO
```

## Usage Examples

### Wrapping Official MCP Servers

#### Fetch Server
```dockerfile
FROM python:3.12-slim
RUN pip install mcp-streamablehttp-proxy mcp-server-fetch
CMD ["mcp-streamablehttp-proxy", "--mcp-command", "mcp-server-fetch"]
```

#### Filesystem Server
```dockerfile
FROM python:3.12-slim
RUN pip install mcp-streamablehttp-proxy mcp-server-filesystem
CMD ["mcp-streamablehttp-proxy", "--mcp-command", "mcp-server-filesystem", \
     "--mcp-args", "--root /data --read-only"]
```

#### Time Server
```dockerfile
FROM python:3.12-slim
RUN pip install mcp-streamablehttp-proxy mcp-server-time
CMD ["mcp-streamablehttp-proxy", "--mcp-command", "mcp-server-time"]
```

### Docker Compose Integration

```yaml
services:
  mcp-fetch:
    build:
      context: ./mcp-fetch
    environment:
      - MCP_LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    labels:
      - "traefik.http.routers.mcp-fetch.rule=Host(`mcp-fetch.${BASE_DOMAIN}`)"
      - "traefik.http.middlewares.mcp-fetch.forwardauth.address=http://auth:8000/verify"
```

## API Endpoints

### `/mcp` - Main Protocol Endpoint

**Request:**
```http
POST /mcp HTTP/1.1
Content-Type: application/json
Mcp-Session-Id: session-123 (optional)

{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {}
  },
  "id": 1
}
```

**Response (SSE stream):**
```
event: message
data: {"jsonrpc": "2.0", "result": {"protocolVersion": "2025-06-18", ...}, "id": 1}

event: done
data: {"status": "complete"}
```

### `/health` - Health Check

```http
GET /health HTTP/1.1

Response:
{
  "status": "healthy",
  "subprocess": "running",
  "sessions": 5,
  "uptime": 3600
}
```

## Session Lifecycle

### 1. Session Creation

When a client first connects without a session ID:

```python
# Proxy creates new session
session_id = generate_session_id()
subprocess = spawn_mcp_server()
sessions[session_id] = {
    "process": subprocess,
    "created": time.time(),
    "last_activity": time.time()
}
```

### 2. Session Usage

Subsequent requests include session ID:

```http
POST /mcp
Mcp-Session-Id: session-123
```

### 3. Session Cleanup

Sessions are cleaned up when:
- Client sends explicit shutdown
- Session timeout exceeded
- Subprocess crashes
- Proxy shutdown

## Subprocess Management

### Starting Subprocesses

```python
# Proxy spawns MCP server
process = subprocess.Popen(
    [mcp_command] + mcp_args,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=False  # Binary mode for proper encoding
)
```

### Health Monitoring

The proxy monitors subprocess health:
- Checks process is alive
- Monitors stdio responsiveness
- Restarts on crash (configurable)
- Reports health via `/health`

### Graceful Shutdown

On proxy shutdown:
1. Send shutdown to all subprocesses
2. Wait for graceful termination
3. Force kill if timeout exceeded
4. Clean up resources

## Error Handling

### Subprocess Errors

| Error | Cause | Handling |
|-------|-------|----------|
| Process crash | Server died | Restart or fail session |
| Startup timeout | Server slow/hung | Kill and retry |
| Communication error | Broken pipe | Terminate session |

### Protocol Errors

| Error | Response |
|-------|----------|
| Invalid JSON-RPC | 400 Bad Request |
| Unknown session | 404 Not Found |
| Server error | 500 with error details |

## Performance Tuning

### Connection Pooling

```python
# Reuse sessions where possible
connection_pool = {
    "max_idle": 10,
    "idle_timeout": 300
}
```

### Buffer Sizes

```bash
# Tune for large responses
MCP_READ_BUFFER_SIZE=65536
MCP_WRITE_BUFFER_SIZE=65536
```

### Concurrent Sessions

```bash
# Limit concurrent sessions
MCP_MAX_SESSIONS=100
MCP_SESSION_TIMEOUT=3600
```

## Monitoring

### Metrics Exposed

- Active sessions count
- Subprocess CPU/memory usage
- Request latency
- Error rates
- Session duration

### Logging

```python
# Structured logging
logger.info("session_created", extra={
    "session_id": session_id,
    "client_ip": client_ip,
    "mcp_server": mcp_command
})
```

## Security Considerations

1. **Process Isolation**: Each session gets its own subprocess
2. **Resource Limits**: Configure max sessions and timeouts
3. **Input Validation**: Validate all JSON-RPC messages
4. **Subprocess Sandboxing**: Use containers for isolation
5. **Authentication**: Handled by gateway layer (not proxy)

## Troubleshooting

### Subprocess Won't Start
```bash
# Test command manually
mcp-server-fetch --version

# Check logs
docker logs mcp-fetch

# Verify installation
pip list | grep mcp-server
```

### Session Errors
```bash
# Check active sessions
curl http://localhost:3000/health

# Enable debug logging
export MCP_LOG_LEVEL=DEBUG
```

### Performance Issues
```bash
# Monitor subprocess
docker stats mcp-fetch

# Check session count
curl http://localhost:3000/health | jq .sessions

# Tune parameters
export MCP_MAX_SESSIONS=50
```

## Integration Patterns

### With Traefik
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.service.rule=Host(`service.domain`)"
  - "traefik.http.services.service.loadbalancer.server.port=3000"
```

### With Monitoring
```yaml
# Prometheus metrics
- "prometheus.io/scrape=true"
- "prometheus.io/port=3000"
- "prometheus.io/path=/metrics"
```

### With Logging
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```
