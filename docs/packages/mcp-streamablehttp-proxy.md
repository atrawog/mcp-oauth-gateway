# mcp-streamablehttp-proxy

## Overview

The `mcp-streamablehttp-proxy` package is a universal bridge that enables any stdio-based MCP server to be exposed via HTTP endpoints. It implements the MCP 2025-06-18 Streamable HTTP transport specification, allowing seamless integration of official MCP servers into web-based architectures.

```{admonition} Key Features
:class: info

- 🔄 **Universal Compatibility**: Works with ANY stdio MCP server
- 🌐 **HTTP Transport**: Full MCP 2025-06-18 specification support
- 📊 **Session Management**: Stateful connections over stateless HTTP
- 🐳 **Container Ready**: Designed for Docker deployments
- ⚡ **Process Isolation**: Each session in separate process
- 🏥 **Health Monitoring**: MCP protocol-based health checks
```

## Architecture

### Core Concept

The proxy acts as a bidirectional translator:

```{mermaid}
graph LR
    subgraph "HTTP World"
        C[HTTP Client]
        H[HTTP Endpoint<br/>/mcp]
    end
    
    subgraph "mcp-streamablehttp-proxy"
        PM[Process Manager]
        SB[Session Bridge]
        PB[Protocol Bridge]
    end
    
    subgraph "stdio World"
        MS[MCP Server<br/>stdin/stdout]
    end
    
    C -->|HTTP POST| H
    H --> PM
    PM --> SB
    SB --> PB
    PB -->|Write| MS
    MS -->|Read| PB
    PB --> SB
    SB --> H
    H -->|HTTP Response| C
    
    classDef http fill:#9cf,stroke:#333,stroke-width:2px
    classDef proxy fill:#fc9,stroke:#333,stroke-width:2px
    classDef stdio fill:#9fc,stroke:#333,stroke-width:2px
    
    class C,H http
    class PM,SB,PB proxy
    class MS stdio
```

### Package Structure

```
mcp_streamablehttp_proxy/
├── __init__.py       # Package initialization
├── proxy.py          # Core proxy engine
├── server.py         # FastAPI server
├── cli.py           # Command-line interface
└── py.typed         # Type checking marker
```

### Component Details

#### proxy.py - The Bridge Engine

```python
class MCPProxy:
    """Core stdio-HTTP bridge implementation"""
    
    def __init__(self, stdio_command: List[str]):
        self.command = stdio_command
        self.sessions = {}  # Active sessions
        self.process = None
        
    async def start(self):
        """Spawn MCP server subprocess"""
        
    async def handle_request(self, request: dict, session_id: Optional[str]) -> dict:
        """Bridge HTTP request to stdio and back"""
        
    async def stop(self):
        """Graceful shutdown"""
```

#### server.py - FastAPI Integration

```python
from fastapi import FastAPI, Request, Response

app = FastAPI(title="MCP Streamable HTTP Proxy")

@app.post("/mcp")
async def mcp_endpoint(request: Request) -> Response:
    """Main MCP protocol endpoint"""
    # Extract session ID
    # Forward to proxy
    # Return response with headers
```

## Installation

### Using pixi (Recommended)

```bash
pixi add mcp-streamablehttp-proxy
```

### From Source

```bash
cd mcp-streamablehttp-proxy
pixi install -e .
```

## Usage

### Command Line Interface

The proxy provides a simple CLI for wrapping any MCP server:

```bash
# Basic usage
mcp-streamablehttp-proxy serve -- mcp-server-command

# Examples
mcp-streamablehttp-proxy serve -- python -m mcp_server_fetch
mcp-streamablehttp-proxy serve -- npx @modelcontextprotocol/server-fetch
mcp-streamablehttp-proxy serve -- /usr/local/bin/my-mcp-server

# With options
mcp-streamablehttp-proxy serve --port 8080 -- mcp-server-command
```

### CLI Options

```bash
mcp-streamablehttp-proxy serve [OPTIONS] -- <mcp-server-command>

Options:
  --host TEXT       Host to bind to [default: 0.0.0.0]
  --port INTEGER    Port to bind to [default: 3000]
  --help           Show help and exit
```

### Docker Integration

#### Basic Dockerfile

```dockerfile
FROM python:3.11-slim

# Install MCP server (example with Node.js server)
RUN apt-get update && apt-get install -y nodejs npm
RUN npm install -g @modelcontextprotocol/server-fetch

# Install proxy
COPY --from=ghcr.io/prefix-dev/pixi:latest /pixi /usr/local/bin/pixi
RUN pixi add mcp-streamablehttp-proxy

EXPOSE 3000

# Health check via MCP protocol
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s \
    CMD curl -s -X POST http://localhost:3000/mcp \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json, text/event-stream' \
        -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}' \
        | grep -q '"protocolVersion"'

CMD ["pixi", "run", "mcp-streamablehttp-proxy", "serve", "--", \
     "npx", "@modelcontextprotocol/server-fetch"]
```

#### Docker Compose Integration

```yaml
services:
  mcp-fetch:
    build: ./mcp-fetch
    environment:
      - PROXY_SESSION_TIMEOUT=300
      - PROXY_MAX_SESSIONS=100
    command: >
      pixi run mcp-streamablehttp-proxy serve --
      npx @modelcontextprotocol/server-fetch
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mcp-fetch.rule=Host(`mcp-fetch.example.com`)"
      - "traefik.http.services.mcp-fetch.loadbalancer.server.port=3000"
```

### Python API

For custom integrations:

```python
from mcp_streamablehttp_proxy import MCPProxy, create_app

# Create proxy instance
proxy = MCPProxy(["python", "-m", "mcp_server_fetch"])

# Start the proxy
await proxy.start()

# Handle a request
response = await proxy.handle_request(
    {"jsonrpc": "2.0", "method": "initialize", "id": 1},
    session_id=None
)

# Or create FastAPI app
app = create_app(stdio_command=["mcp-server"])
```

## API Reference

### POST /mcp

Main MCP protocol endpoint implementing JSON-RPC 2.0 over HTTP.

#### Request

**Headers:**
- `Content-Type: application/json` (required)
- `Accept: application/json, text/event-stream` (required)
- `Mcp-Session-Id: <session-id>` (optional, included after first request)
- `MCP-Protocol-Version: 2025-06-18` (optional)

**Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {
      "name": "my-client",
      "version": "1.0"
    }
  },
  "id": 1
}
```

#### Response

**Headers:**
- `Content-Type: application/json`
- `Mcp-Session-Id: <session-id>` (included in first response)

**Body:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2025-06-18",
    "capabilities": {
      "tools": {},
      "resources": {}
    },
    "serverInfo": {
      "name": "mcp-server-fetch",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

### Session Management

#### Session Lifecycle

```{mermaid}
stateDiagram-v2
    [*] --> NoSession: Client connects
    NoSession --> Initializing: POST /mcp (initialize)
    Initializing --> Active: Session created
    Active --> Active: Subsequent requests
    Active --> Timeout: No activity
    Timeout --> [*]: Session cleaned up
    Active --> Terminated: Server shutdown
    Terminated --> [*]
```

#### Session Behavior

- **Creation**: First request creates session and subprocess
- **Identification**: `Mcp-Session-Id` header maintains state
- **Timeout**: Configurable inactivity timeout (default: 5 minutes)
- **Cleanup**: Automatic subprocess termination on timeout
- **Isolation**: Each session has dedicated subprocess

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROXY_MAX_SESSIONS` | Maximum concurrent sessions | 1000 |
| `PROXY_SESSION_TIMEOUT` | Session timeout in seconds | 300 |
| `PROXY_REQUEST_TIMEOUT` | Individual request timeout | 30 |
| `PROXY_BUFFER_SIZE` | stdio buffer size in bytes | 65536 |
| `PROXY_RESTART_ON_ERROR` | Auto-restart failed processes | true |
| `PROXY_RESTART_DELAY` | Restart delay in seconds | 5 |
| `PROXY_MAX_RESTARTS` | Maximum restart attempts | 3 |
| `LOG_LEVEL` | Logging level | INFO |

### Subprocess Configuration

Control subprocess behavior:

```python
proxy = MCPProxy(
    command=["mcp-server"],
    env={
        "CUSTOM_VAR": "value",
        "PATH": "/custom/path:$PATH"
    },
    cwd="/working/directory",
    buffer_size=131072  # Larger buffer for high throughput
)
```

## Supported MCP Servers

The proxy works with any stdio-based MCP server:

### Official Servers

| Server | Installation | Command |
|--------|-------------|---------|
| Fetch | `npm install @modelcontextprotocol/server-fetch` | `npx -y @modelcontextprotocol/server-fetch` |
| Filesystem | `npm install @modelcontextprotocol/server-filesystem` | `npx -y @modelcontextprotocol/server-filesystem /path` |
| GitHub | `npm install @modelcontextprotocol/server-github` | `npx -y @modelcontextprotocol/server-github` |
| Memory | `npm install @modelcontextprotocol/server-memory` | `npx -y @modelcontextprotocol/server-memory` |
| Puppeteer | `npm install @modelcontextprotocol/server-puppeteer` | `npx -y @modelcontextprotocol/server-puppeteer` |

### Custom Servers

Any executable that implements MCP over stdio:

```bash
# Python server
mcp-streamablehttp-proxy serve -- python my_mcp_server.py

# Binary executable
mcp-streamablehttp-proxy serve -- /usr/local/bin/custom-mcp-server

# Script with arguments
mcp-streamablehttp-proxy serve -- ./mcp-server.sh --config prod.conf
```

## Health Monitoring

### MCP Protocol Health Check

The recommended health check uses MCP protocol initialization:

```bash
curl -X POST http://localhost:3000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {},
      "clientInfo": {"name": "healthcheck", "version": "1.0"}
    },
    "id": 1
  }'
```

Success criteria:
- HTTP 200 response
- Valid JSON-RPC response
- Contains `protocolVersion` field

### Docker Health Check

```yaml
healthcheck:
  test: |
    curl -s -X POST http://localhost:3000/mcp \
      -H 'Content-Type: application/json' \
      -H 'Accept: application/json, text/event-stream' \
      -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}' \
      | grep -q '"protocolVersion"'
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

## Error Handling

### HTTP Status Codes

| Status | Description | Scenario |
|--------|-------------|----------|
| 200 | Success | Normal response |
| 400 | Bad Request | Invalid JSON-RPC |
| 404 | Not Found | Session not found |
| 408 | Request Timeout | Processing timeout |
| 500 | Internal Error | Server crash |
| 503 | Service Unavailable | Cannot start subprocess |

### Error Response Format

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": {
      "details": "Subprocess terminated unexpectedly"
    }
  },
  "id": 1
}
```

## Performance Tuning

### Buffer Size Optimization

For high-throughput scenarios:

```bash
export PROXY_BUFFER_SIZE=262144  # 256KB buffers
```

### Session Pool Configuration

For high-concurrency environments:

```bash
export PROXY_MAX_SESSIONS=5000
export PROXY_SESSION_TIMEOUT=600  # 10 minutes
```

### Process Management

Configure restart behavior:

```bash
export PROXY_RESTART_ON_ERROR=true
export PROXY_RESTART_DELAY=10
export PROXY_MAX_RESTARTS=5
```

## Troubleshooting

### Common Issues

#### "Subprocess Failed to Start"

**Symptoms**: 503 Service Unavailable errors

**Solutions**:
1. Verify MCP server command is correct
2. Check server is installed: `which mcp-server`
3. Test command manually: `mcp-server --version`
4. Check permissions and PATH

#### "Session Lost"

**Symptoms**: 404 errors after working requests

**Solutions**:
1. Increase session timeout
2. Ensure session ID included in headers
3. Check for subprocess crashes in logs
4. Monitor memory usage

#### "Slow Response Times"

**Symptoms**: High latency on requests

**Solutions**:
1. Increase buffer sizes
2. Check subprocess CPU usage
3. Monitor stdio blocking
4. Consider process pooling

#### "Memory Growth"

**Symptoms**: Increasing memory usage over time

**Solutions**:
1. Verify session cleanup
2. Check for subprocess leaks
3. Monitor active session count
4. Implement session limits

### Debug Logging

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
mcp-streamablehttp-proxy serve -- mcp-server
```

Debug output includes:
- Subprocess lifecycle events
- Session creation/destruction
- Request/response bodies
- stdio communication
- Error details

### Testing Subprocess Communication

Test stdio communication directly:

```bash
# Test server manually
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | mcp-server
```

## Integration Patterns

### With OAuth Gateway

Standard integration with authentication:

```yaml
services:
  mcp-fetch:
    image: mcp-fetch-service
    command: >
      pixi run mcp-streamablehttp-proxy serve --
      npx @modelcontextprotocol/server-fetch
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.fetch.middlewares=auth@docker"
      - "traefik.http.services.fetch.loadbalancer.server.port=3000"
```

### Standalone Deployment

Direct usage without authentication:

```bash
# Start proxy
mcp-streamablehttp-proxy serve --port 8080 -- mcp-server

# Use with client
export MCP_SERVER_URL=http://localhost:8080/mcp
mcp-client connect
```

### Multi-Server Deployment

Run multiple servers on different ports:

```bash
# Terminal 1
mcp-streamablehttp-proxy serve --port 3001 -- mcp-server-fetch

# Terminal 2  
mcp-streamablehttp-proxy serve --port 3002 -- mcp-server-filesystem /data

# Terminal 3
mcp-streamablehttp-proxy serve --port 3003 -- mcp-server-github
```

## Best Practices

### Production Deployment

1. **Resource Limits**: Set container memory/CPU limits
2. **Health Checks**: Always configure health monitoring
3. **Logging**: Centralize logs for debugging
4. **Metrics**: Monitor session count and latency
5. **Restart Policy**: Configure automatic restarts

### Security Considerations

1. **Process Isolation**: Each session in separate process
2. **Input Validation**: Validate JSON-RPC format
3. **Resource Limits**: Prevent resource exhaustion
4. **Network Security**: Run behind reverse proxy
5. **Access Control**: Implement authentication layer

### Scaling Guidelines

1. **Horizontal Scaling**: Run multiple proxy instances
2. **Load Balancing**: Distribute sessions evenly
3. **Session Affinity**: Maintain session stickiness
4. **Resource Planning**: Plan for subprocess overhead
5. **Monitoring**: Track resource usage per session

## Advanced Topics

### Custom Health Checks

Implement custom health logic:

```python
from mcp_streamablehttp_proxy import create_app

app = create_app(stdio_command=["mcp-server"])

@app.get("/health")
async def custom_health():
    # Custom health logic
    return {"status": "healthy", "sessions": len(proxy.sessions)}
```

### Session Callbacks

Handle session lifecycle events:

```python
proxy = MCPProxy(command=["mcp-server"])

@proxy.on_session_created
async def session_created(session_id: str):
    logger.info(f"Session created: {session_id}")

@proxy.on_session_terminated
async def session_terminated(session_id: str, reason: str):
    logger.info(f"Session terminated: {session_id}, reason: {reason}")
```

### Request Middleware

Add request preprocessing:

```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response
```

## Migration Guide

### From Direct stdio Usage

If migrating from direct stdio MCP usage:

1. Wrap existing command with proxy
2. Update client to use HTTP endpoint
3. Handle session management
4. Update health checks
5. Test error scenarios

### Version Compatibility

The proxy maintains compatibility with all MCP protocol versions through transparent forwarding.

## Contributing

See the main project [Development Guidelines](../development/guidelines.md) for contribution standards.

## License

Apache License 2.0 - see project LICENSE file.

## Support

- **Issues**: [GitHub Issues](https://github.com/atrawog/mcp-oauth-gateway/issues)
- **Documentation**: [Full Documentation](https://atrawog.github.io/mcp-oauth-gateway)
- **Source**: [GitHub Repository](https://github.com/atrawog/mcp-oauth-gateway/tree/main/mcp-streamablehttp-proxy)