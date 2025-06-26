# 🔥 CLAUDE.md - The mcp-streamablehttp-proxy Package Divine Scripture! ⚡

**🌉 Behold! The Sacred Bridge - stdio to HTTP Protocol Transcendence! 🌉**

**⚡ This is mcp-streamablehttp-proxy - The Holy Translator of MCP Protocols! ⚡**

## 🔱 The Sacred Purpose - Divine Protocol Bridge Implementation!

**mcp-streamablehttp-proxy is the blessed Python package that bridges stdio MCP servers to HTTP!**

This sacred package manifests these divine powers:
- **stdio to HTTP Bridge** - Translates between transport protocols with divine precision!
- **Subprocess Management** - Spawns and controls MCP server processes with holy care!
- **Session State Handling** - Maintains MCP session continuity across requests!
- **Streamable HTTP Transport** - Implements MCP 2025-06-18 transport specification!
- **Health Monitoring** - Provides HTTP health endpoints for container orchestration!
- **Error Translation** - Converts process errors to proper HTTP responses!

**⚡ This package makes ANY stdio MCP server HTTP-accessible! ⚡**

## 🏗️ The Sacred Architecture - Bridge Component Structure!

```
mcp_streamablehttp_proxy/
├── Core Modules (The Sacred Foundations!)
│   ├── __init__.py - Package exports and initialization!
│   ├── proxy.py - The stdio-HTTP bridge engine!
│   ├── server.py - FastAPI server implementation!
│   └── cli.py - Command-line interface blessed!
└── Type Definitions (The Contract Declarations!)
    └── py.typed - Type checking enablement marker!
```

**⚡ Minimal surface area for maximum divine reliability! ⚡**

## 📖 The Sacred Modules - Divine Component Details!

### proxy.py - The Bridge Engine Core!
```python
class MCPProxy:
    """The divine translator between stdio and HTTP!"""

    def __init__(self, stdio_command: List[str]):
        """Initialize with MCP server command!"""
        self.process = None  # The subprocess vessel
        self.sessions = {}   # Active session tracking

    async def start(self):
        """Spawn the MCP server subprocess!"""

    async def handle_request(self, request: dict) -> dict:
        """Translate HTTP request to stdio and back!"""

    async def stop(self):
        """Gracefully terminate the subprocess!"""
```

**The Sacred Bridge Responsibilities:**
1. **Process Lifecycle** - Start, monitor, and stop MCP servers!
2. **Protocol Translation** - HTTP JSON ↔ stdio JSON-RPC!
3. **Session Management** - Track Mcp-Session-Id headers!
4. **Error Handling** - Graceful degradation on failures!

### server.py - The FastAPI Divine Wrapper!
```python
from fastapi import FastAPI, Request, Response

app = FastAPI(title="MCP Streamable HTTP Proxy")

@app.post("/mcp")
async def handle_mcp_request(request: Request) -> Response:
    """Primary MCP endpoint - the sacred gateway!"""
    # Extract session ID from headers
    # Translate request to stdio format
    # Send to subprocess and await response
    # Return formatted HTTP response

# Health checks now done via MCP protocol initialization
```

**⚡ Simple HTTP API wrapping complex stdio interactions! ⚡**

### cli.py - The Command Interface Scripture!
```python
import typer
from typing import List

app = typer.Typer()

@app.command()
def serve(
    stdio_command: List[str],
    host: str = "0.0.0.0",
    port: int = 3000
):
    """
    Start the divine proxy server!

    Example:
        mcp-streamablehttp-proxy serve -- mcp-server-fetch --arg1 --arg2
    """
    # Initialize proxy with command
    # Start FastAPI server
    # Monitor subprocess health
```

**⚡ CLI provides the divine invocation interface! ⚡**

## 🔧 Installation and Sacred Setup!

### Package Installation
```bash
# Via pixi (the blessed way)
pixi add mcp-streamablehttp-proxy

# Or from source with divine intent
cd mcp-streamablehttp-proxy
pixi install -e .
```

### Basic Usage Pattern
```bash
# Wrap any stdio MCP server
mcp-streamablehttp-proxy serve \
    --host 0.0.0.0 \
    --port 3000 \
    -- mcp-server-fetch --config /path/to/config
```

## 🐳 Docker Integration - Container Divine Patterns!

### The Blessed Dockerfile Pattern
```dockerfile
FROM node:20-slim

# Install MCP server
RUN npm install -g @modelcontextprotocol/server-fetch

# Install proxy via pixi
COPY --from=pixi /pixi /usr/local/bin/pixi
RUN pixi add mcp-streamablehttp-proxy

# Expose the blessed port
EXPOSE 3000

# Health check via MCP protocol
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s \
    CMD curl -s -X POST http://localhost:3000/mcp \
        -H 'Content-Type: application/json' \
        -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}' \
        | grep -q '"protocolVersion"'

# Launch proxy wrapping MCP server
CMD ["pixi", "run", "mcp-streamablehttp-proxy", "serve", \
     "--", "mcp-server-fetch"]
```

**⚡ This pattern works for ANY stdio MCP server! ⚡**

## 🚀 The Sacred Usage Patterns!

### Wrapping Official MCP Servers
```python
# In your service startup
proxy = MCPProxy([
    "npx",
    "@modelcontextprotocol/server-fetch",
    "--config", "/app/config.json"
])

await proxy.start()
```

### Custom MCP Server Integration
```python
# Wrap any stdio-based MCP implementation
proxy = MCPProxy([
    "python", "-m", "my_custom_mcp_server",
    "--port", "stdio"
])
```

### Session Management Pattern
```python
# Sessions tracked automatically via headers
headers = {
    "Mcp-Session-Id": "divine-session-123",
    "MCP-Protocol-Version": "2025-06-18"
}

response = await client.post("/mcp", json=request, headers=headers)
```

## 🔐 The Security Considerations - Divine Protection Notes!

### Process Isolation
- Each proxy instance spawns isolated subprocess!
- No shared memory between sessions!
- Process crashes don't affect proxy!
- Automatic restart on subprocess death!

### Input Validation
- JSON-RPC format enforced strictly!
- Method names validated against whitelist!
- Parameter types checked before forwarding!
- Response size limits prevent DoS!

### Error Handling
- Subprocess errors become HTTP 500!
- Malformed requests return HTTP 400!
- Session not found returns HTTP 404!
- All errors include helpful messages!

**⚡ Security through simplicity and isolation! ⚡**

## 📡 The MCP Protocol Implementation - Transport Divine Details!

### Request Flow (HTTP → stdio)
1. **HTTP POST** arrives at `/mcp` endpoint
2. **Extract headers** - Session ID, protocol version
3. **Parse JSON body** - Validate JSON-RPC format
4. **Write to stdin** - Send to subprocess
5. **Read from stdout** - Await response
6. **Return HTTP response** - With appropriate status

### Response Handling
```python
# Success response
{
    "jsonrpc": "2.0",
    "result": {...},
    "id": "request-123"
}

# Error response
{
    "jsonrpc": "2.0",
    "error": {
        "code": -32600,
        "message": "Invalid Request"
    },
    "id": "request-123"
}
```

### Session Lifecycle
1. **First request** - No session ID provided
2. **Initialize response** - Server assigns session
3. **Client includes** - Session ID in all requests
4. **Session timeout** - Cleaned up after inactivity
5. **Graceful shutdown** - Sessions notified of close

## 🧪 Testing the Package - Divine Verification!

```bash
# Run package tests
pixi run pytest tests/ -v

# Test with real MCP server
pixi run pytest tests/test_integration.py -v

# Coverage measurement
pixi run pytest --cov=mcp_streamablehttp_proxy
```

### Testing Patterns
```python
# Test subprocess management
async def test_proxy_lifecycle():
    proxy = MCPProxy(["echo", "test"])
    await proxy.start()
    assert proxy.is_alive()
    await proxy.stop()

# Test request handling
async def test_request_translation():
    proxy = MCPProxy(["mcp-test-server"])
    response = await proxy.handle_request({
        "jsonrpc": "2.0",
        "method": "test",
        "id": 1
    })
    assert response["id"] == 1
```

## 🔥 Common Issues and Divine Solutions!

### "Subprocess Failed to Start" - Command Error!
- Verify MCP server command is correct!
- Check server is installed in container!
- Review subprocess error output!
- Ensure executable permissions!

### "Session Lost" - State Management Issue!
- Check session timeout configuration!
- Verify session ID in headers!
- Monitor subprocess memory usage!
- Review concurrent request handling!

### "Slow Response" - Performance Problems!
- Check subprocess CPU usage!
- Monitor stdio buffer sizes!
- Review request queuing!
- Consider process pooling!

### "Memory Leak" - Resource Management!
- Ensure sessions cleaned up!
- Check subprocess memory!
- Monitor connection pooling!
- Review error accumulation!

## 📚 Advanced Configuration - Divine Tuning Options!

### Environment Variables
```bash
# Proxy configuration
PROXY_MAX_SESSIONS=1000          # Maximum concurrent sessions
PROXY_SESSION_TIMEOUT=3600       # Session timeout in seconds
PROXY_REQUEST_TIMEOUT=30         # Individual request timeout
PROXY_BUFFER_SIZE=65536         # stdio buffer size

# Process management
PROXY_RESTART_ON_ERROR=true     # Auto-restart failed processes
PROXY_RESTART_DELAY=5           # Restart delay in seconds
PROXY_MAX_RESTARTS=3           # Maximum restart attempts
```

### Performance Tuning
```python
# Configure for high throughput
proxy = MCPProxy(
    command=["mcp-server"],
    buffer_size=131072,      # Larger buffers
    max_concurrent=50,       # Request concurrency
    session_timeout=7200     # Longer sessions
)
```

## 🎯 The Divine Mission - Package Responsibilities!

**What mcp-streamablehttp-proxy MUST Do:**
- Bridge stdio MCP servers to HTTP perfectly!
- Manage subprocess lifecycle reliably!
- Handle session state correctly!
- Translate errors appropriately!
- Provide health monitoring endpoints!

**What mcp-streamablehttp-proxy MUST NOT Do:**
- Implement MCP protocol logic!
- Modify message contents!
- Handle authentication/authorization!
- Make routing decisions!
- Store persistent state!

**⚡ Pure transport bridge - no business logic! ⚡**

## 🔱 The Sacred Truth - Why This Package Exists!

**The Divine Problem:**
- Official MCP servers use stdio transport
- Production systems need HTTP endpoints
- Claude.ai requires streamable HTTP
- Docker needs health checks

**The Blessed Solution:**
- Wrap ANY stdio server automatically
- Provide consistent HTTP interface
- Handle all transport complexities
- Enable production deployment

**⚡ One package to bridge them all! ⚡**

## 🛠️ Debugging Commands - Divine Troubleshooting!

```bash
# Test proxy directly
echo '{"jsonrpc":"2.0","method":"initialize","id":1}' | \
    mcp-streamablehttp-proxy debug -- mcp-server

# Monitor subprocess
mcp-streamablehttp-proxy serve -- mcp-server --verbose

# Check health via MCP protocol
curl -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'

# Send test request
curl -X POST http://localhost:3000/mcp \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"test","id":1}'
```

---

**🔥 May your bridges be stable, your processes managed, and your protocols forever translated! ⚡**
