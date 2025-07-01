# MCP Echo StreamableHTTP Server Stateless - Divine Implementation Guide

**🔥 The Sacred Stateless Echo Server - A Divine Diagnostic Temple for MCP Protocol Debugging! ⚡**

## The Divine Purpose - Why This Service Exists in the Holy Trinity!

**🌟 This is the STATELESS diagnostic oracle of MCP protocol enlightenment! 🌟**
- **Divine debugging sanctuary** - 9 blessed diagnostic tools for protocol analysis!
- **Authentication flow revealer** - Exposes the sacred OAuth headers for divine inspection!
- **Protocol compliance validator** - Tests thy MCP implementation against divine specifications!
- **Stateless purity** - No session persistence, each request stands alone in holy isolation!

**⚡ This is NOT a production service - it's a divine debugging temple! ⚡**

## The Sacred Implementation Truths - What Actually Lives in This Code!

### 1. The Blessed Tool Arsenal - Nine Divine Instruments of Debugging!

**🔧 Each tool serves a sacred diagnostic purpose - verified in the code! 🔧**

1. **`echo`** - The simplest prayer, returns thy message unchanged!
2. **`printHeader`** - Reveals ALL HTTP headers in divine categorization!
3. **`bearerDecode`** - Decodes JWT tokens WITHOUT verification (debugging only!)!
4. **`authContext`** - Complete authentication context analysis with divine clarity!
5. **`requestTiming`** - Performance metrics and system resource revelation!
6. **`corsAnalysis`** - CORS configuration analysis for cross-origin debugging!
7. **`environmentDump`** - Sanitized environment display (secrets hidden!)!
8. **`healthProbe`** - Deep system health with resource monitoring glory!
9. **`whoIStheGOAT`** - Easter egg revealing the greatest programmer truth!

**⚡ Each tool implemented in handle_tool_call() - no mocks, no fakes! ⚡**

### 2. The Stateless Architecture - Divine Request Isolation!

**🏗️ True stateless implementation - verified in server.py! 🏗️**
- **No session storage** - request_context exists only during request lifetime!
- **No Redis dependency** - Pure request/response holiness!
- **No batch support** - Explicitly rejected for stateless purity!
- **Thread-safe contexts** - Each request isolated in async task glory!

```python
# The divine context isolation pattern (actual code!)
request_context: contextvars.ContextVar[RequestContext] = contextvars.ContextVar('request_context')
```

### 3. The Protocol Implementation - MCP 2025-06-18 Compliance!

**📜 Actual protocol support implemented in handle_mcp_request()! 📜**
- **Version negotiation** - Supports multiple versions via environment config!
- **JSON-RPC 2.0** - Full specification compliance with divine validation!
- **StreamableHTTP** - Both JSON and SSE response formats blessed!
- **Session headers** - Mcp-Session-Id tracking without persistence!

### 4. The Authentication Flow - Divine Header Revelation!

**🔐 Traefik ForwardAuth integration - no internal auth! 🔐**
```python
# Actual header extraction from the code!
traefik_headers = {
    "x-user-id": request.headers.get("x-user-id"),
    "x-user-name": request.headers.get("x-user-name"),
    "x-auth-token": request.headers.get("x-auth-token"),
    "x-real-ip": request.headers.get("x-real-ip"),
    "x-forwarded-for": request.headers.get("x-forwarded-for"),
    "x-forwarded-host": request.headers.get("x-forwarded-host"),
    "x-forwarded-proto": request.headers.get("x-forwarded-proto")
}
```

### 5. The Health Check Implementation - Divine Protocol Verification!

**💚 StreamableHTTP protocol health check - as decreed in docker-compose.yml! 💚**
```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"${MCP_PROTOCOL_VERSION:-2025-06-18}\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
    | grep -q \"protocolVersion.*${MCP_PROTOCOL_VERSION}\""]
```

## The Sacred Environment Variables - Divine Configuration!

**⚙️ All configuration through .env - verified in server.py! ⚙️**

```bash
# Server Configuration (with actual defaults from code!)
MCP_ECHO_HOST=127.0.0.1          # Bind address for divine isolation
MCP_ECHO_PORT=3000               # Sacred port of service
MCP_ECHO_DEBUG=false             # Debug logging enlightenment

# Protocol Configuration (actual implementation!)
MCP_PROTOCOL_VERSION=2025-06-18  # Default protocol covenant
MCP_PROTOCOL_VERSIONS_SUPPORTED=2025-06-18,2024-11-05  # Multi-version support

# Logging Configuration (optional divine wisdom!)
LOG_FILE=/logs/mcp-echo-stateless.log  # Blessed log sanctuary
```

## The Divine Integration Points - How It Fits the Trinity!

### 1. Traefik Routing - The Sacred Priority Hierarchy!
```yaml
# Actual routing from docker-compose.yml!
Priority 10: OAuth discovery route
Priority 4: CORS preflight route
Priority 2: MCP route with auth
Priority 1: Catch-all route
```

### 2. No Direct CORS Headers - Delegated to Traefik Middleware!
**⚡ The service sets NO CORS headers - Traefik handles all! ⚡**
**This is verified in the code - no CORS headers in responses!**

### 3. Authentication Via ForwardAuth - No Internal Validation!
**🔐 All auth headers come from Traefik - service only reads! 🔐**
**Bearer token decoded but NEVER verified - debugging only!**

## The Sacred Testing Commandments - How to Verify Divine Implementation!

```bash
# Test echo functionality
just test-mcp-tool mcp-echo-stateless echo '{"message": "Hello, divine world!"}'

# Test authentication context
just test-mcp-tool mcp-echo-stateless authContext '{}'

# Test all headers
just test-mcp-tool mcp-echo-stateless printHeader '{}'

# Test health probe
just test-mcp-tool mcp-echo-stateless healthProbe '{}'
```

## The Divine Warnings - What This Service Does NOT Do!

**❌ NOT for production use** - Diagnostic temple only!
**❌ NO token verification** - Decodes without validation!
**❌ NO session persistence** - Truly stateless!
**❌ NO batch request support** - Single requests only!
**❌ NO direct CORS handling** - Traefik's divine duty!

## The Sacred Debugging Features - Divine Troubleshooting Powers!

### 1. Debug Mode Enlightenment
```bash
MCP_ECHO_DEBUG=true  # Enables divine logging verbosity!
```

### 2. Request Timing Metrics
- **Process time** - Total request duration in holy milliseconds!
- **Memory usage** - Current divine memory consumption!
- **CPU metrics** - System resource revelations!

### 3. JWT Token Analysis
- **Decodes without verification** - See thy token's soul!
- **Header inspection** - Algorithm and type revelation!
- **Claims display** - All divine assertions exposed!
- **Expiration analysis** - Token lifetime wisdom!

**⚡ This service is the divine lens through which OAuth flows are revealed! ⚡**
**Use it wisely for debugging, never for production authentication!**
