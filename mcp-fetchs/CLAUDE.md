# 🔥 CLAUDE.md - The MCP Fetchs Service Divine Scripture! ⚡

**🌐 Behold! The Native StreamableHTTP Fetch Service - Pure Protocol Implementation Glory! 🌐**

**⚡ This is mcp-fetchs - The Native StreamableHTTP Fetch Implementation of Divine Purity! ⚡**

## 🔱 The Sacred Purpose - Native StreamableHTTP Implementation!

**mcp-fetchs is the blessed MCP service that provides HTTP fetch capabilities through native StreamableHTTP transport!**

This divine service manifests these powers:
- **Native StreamableHTTP** - Direct protocol implementation without stdio bridging!
- **Pure Python Implementation** - FastAPI + Uvicorn with uvloop for divine async performance!
- **OAuth Protection** - Bearer token authentication via Traefik ForwardAuth!
- **Protocol Compliant** - Full MCP 2025-06-18 specification implementation!
- **Stateless Operation** - Each request stands alone in holy isolation!

**⚡ This service demonstrates native StreamableHTTP implementation patterns! ⚡**

## 🏗️ The Sacred Architecture - Service Component Structure!

```
mcp-fetchs/
├── Dockerfile          # Container incantation for divine isolation!
└── docker-compose.yml  # Service orchestration scripture!

Source (from mcp-fetch-streamablehttp-server/):
├── server.py           # FastAPI application divine core!
├── transport.py        # StreamableHTTP transport implementation!
├── fetch_handler.py    # Fetch tool logic with security!
└── __main__.py         # Entry point blessing!
```

**⚡ Native implementation = Direct HTTP handling = Maximum control! ⚡**

## 🐳 The Divine Dockerfile - Container Implementation!

**The blessed container construction follows these sacred steps:**

1. **Base Image** - `python:3.12-slim` for modern Python glory!
2. **System Dependencies** - `build-essential`, `curl`, `git` for compilation needs!
3. **Source Copy** - Copies `mcp-fetch-streamablehttp-server` package source!
4. **Dependency Installation** - Installs all Python packages via pip!
5. **Non-root User** - Runs as `mcpuser` (uid 1000) for security!
6. **Port Exposure** - Port 3000 for StreamableHTTP communication!
7. **Entrypoint** - Direct module execution: `python -m mcp_fetch_streamablehttp_server`

**⚡ Note: Dockerfile includes `/health` endpoint check but it's not implemented in code! ⚡**

## 📡 The Service Configuration - Docker Compose Divine Details!

### The Sacred Routing Configuration - Traefik Label Glory!

**Priority 10 - OAuth Discovery Route (HIGHEST DIVINE PRIORITY!):**
```yaml
- "traefik.http.routers.mcp-fetchs-oauth-discovery.rule=Host(`fetchs.${BASE_DOMAIN}`) && PathPrefix(`/.well-known/oauth-authorization-server`)"
- "traefik.http.routers.mcp-fetchs-oauth-discovery.priority=10"
- "traefik.http.routers.mcp-fetchs-oauth-discovery.service=auth@docker"
# NO AUTH MIDDLEWARE - Discovery must be publicly accessible!
```

**Priority 3 - CORS Preflight Route (OPTIONS Sacred Handling!):**
```yaml
- "traefik.http.routers.mcp-fetchs-options.rule=Host(`fetchs.${BASE_DOMAIN}`) && PathPrefix(`/mcp`) && Method(`OPTIONS`)"
- "traefik.http.routers.mcp-fetchs-options.priority=3"
- "traefik.http.routers.mcp-fetchs-options.middlewares=mcp-cors@file"
# NO AUTH for preflight - CORS must check first!
```

**Priority 2 - MCP Route with Authentication (Protected Divine Access!):**
```yaml
- "traefik.http.routers.mcp-fetchs.rule=Host(`fetchs.${BASE_DOMAIN}`) && PathPrefix(`/mcp`)"
- "traefik.http.routers.mcp-fetchs.priority=2"
- "traefik.http.routers.mcp-fetchs.middlewares=mcp-cors@file,mcp-auth@file"
```

**Priority 1 - Catch-all Route (Lowest Priority Safety Net!):**
```yaml
- "traefik.http.routers.mcp-fetchs-catchall.rule=Host(`fetchs.${BASE_DOMAIN}`)"
- "traefik.http.routers.mcp-fetchs-catchall.priority=1"
- "traefik.http.routers.mcp-fetchs-catchall.middlewares=mcp-cors@file,mcp-auth@file"
```

### The Divine Health Check - Protocol-Based Verification!

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"'$$MCP_PROTOCOL_VERSION'\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
    | grep -q '\"protocolVersion\":\"'$$MCP_PROTOCOL_VERSION'\"'"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

**⚡ This performs a REAL MCP initialization handshake! Protocol compliance verified! ⚡**

### The Sacred Environment Variables

```yaml
environment:
  - LOG_FILE=/logs/server.log                         # Centralized logging path
  - HOST=0.0.0.0                                      # Binding address
  - PORT=3000                                         # Sacred port 3000
  - MCP_SERVER_NAME=mcp-fetch-streamablehttp         # Server identity
  - MCP_SERVER_VERSION=0.1.0                         # Version declaration
  - MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION:-2025-06-18}  # Protocol version
  - MCP_FETCH_DEFAULT_USER_AGENT=ModelContextProtocol/1.0 (Fetch Server)
```

## 🌊 The Native StreamableHTTP Implementation - Direct Protocol Glory!

### Sacred Protocol Implementation Details

**The service implements these MCP methods:**

1. **`initialize`** - Protocol handshake and capability negotiation
   - Validates protocol version match
   - Returns server capabilities and info
   - Declares support for tools only (no prompts, resources, or logging)

2. **`tools/list`** - Returns available tools
   - Currently returns only the `fetch` tool
   - Supports pagination parameters (not implemented yet)

3. **`tools/call`** - Executes tool operations
   - Handles `fetch` tool with comprehensive parameter validation
   - Returns proper tool execution results or errors

### The Sacred Fetch Tool Implementation

**Tool Definition:**
```json
{
  "name": "fetch",
  "description": "Fetch a URL and return its contents",
  "inputSchema": {
    "type": "object",
    "properties": {
      "url": { "type": "string", "description": "URL to fetch" },
      "method": { "type": "string", "enum": ["GET", "POST"], "default": "GET" },
      "headers": { "type": "object", "additionalProperties": { "type": "string" } },
      "body": { "type": "string", "description": "Request body for POST" },
      "max_length": { "type": "integer", "default": 100000 },
      "user_agent": { "type": "string", "default": "ModelContextProtocol/1.0" }
    },
    "required": ["url"]
  }
}
```

### Divine Security Protections - SSRF Prevention!

**⚡ The fetch handler implements these security measures: ⚡**

1. **URL Scheme Validation**
   - Only allows configured schemes (default: http, https)
   - Rejects file://, ftp://, and other protocols

2. **Host Blocking (SSRF Protection)**
   - Blocks localhost, 127.0.0.1, 0.0.0.0, ::1
   - Blocks AWS metadata service (169.254.169.254)
   - Blocks private IP ranges (10.*, 172.*, 192.168.*)
   - Uses simple prefix matching for efficiency

3. **Content Security**
   - Response size limited by max_length parameter (default 100KB)
   - Automatic content-type detection
   - Images converted to base64 with MIME type
   - HTML title extraction for text/html responses

4. **Robots.txt Compliance**
   - Checks robots.txt before fetching (when robotspy is available)
   - Caches robots.txt per host to avoid repeated fetches
   - Allows access if robots.txt fetch fails

### Response Processing Patterns

**Text Content:**
- Attempts UTF-8 decoding, falls back to repr() for binary
- Truncates at max_length with "... (truncated)" suffix
- Extracts HTML title when content-type is text/html

**Image Content:**
- Converts to base64 encoding
- Includes MIME type from Content-Type header
- Enforces max_length limit

## 🔐 The OAuth Integration - Bearer Token Authentication Flow!

**⚡ DIVINE DECREE: NO AUTHENTICATION CODE IN SERVICE! ⚡**

The service maintains "pure protocol innocence" as mandated by CLAUDE.md:
- **No auth logic** - Comments explicitly state this in server.py
- **No CORS handling** - Traefik middleware handles all CORS
- **Bearer tokens** - Validated entirely by Traefik ForwardAuth
- **Clean separation** - Service only knows MCP protocol

## 🚦 Transport Implementation Status

### Currently Implemented
- **POST /mcp** - Full JSON-RPC request processing
- **Stateless operation** - No session management implemented
- **Protocol validation** - Proper JSON-RPC 2.0 compliance
- **Error handling** - Standard JSON-RPC error codes

### Not Yet Implemented
- **GET /mcp** - Returns 501 Not Implemented (SSE planned)
- **DELETE /mcp** - Infrastructure present but no session management
- **Session management** - Transport has placeholders but not used
- **SSE streaming** - Configuration flag exists but not implemented

## 🛠️ Configuration Through Environment Variables

**All configuration flows through blessed environment variables:**

```bash
# Required Settings (via pydantic-settings)
MCP_SERVER_NAME=mcp-fetch-streamablehttp      # Server identity
MCP_SERVER_VERSION=0.1.0                       # Version declaration
MCP_PROTOCOL_VERSION=2025-06-18               # Protocol version

# Optional Fetch Settings
MCP_FETCH_ALLOWED_SCHEMES=["http","https"]    # Allowed URL schemes
MCP_FETCH_MAX_REDIRECTS=5                     # Redirect limit
MCP_FETCH_DEFAULT_USER_AGENT=ModelContextProtocol/1.0 (Fetch Server)
MCP_FETCH_ENABLE_SSE=false                    # Future SSE flag

# Server Settings
HOST=0.0.0.0                                   # Binding address
PORT=3000                                      # Service port
```

## 📊 Error Handling Patterns

### JSON-RPC Protocol Errors
- `-32700` - Parse error (invalid JSON)
- `-32600` - Invalid request structure
- `-32601` - Method not found
- `-32602` - Invalid parameters
- `-32603` - Internal server error

### Tool Execution Errors
Tool errors return with `isError: true` flag:
```json
{
  "content": [{
    "type": "text",
    "text": "Tool execution failed: <error message>"
  }],
  "isError": true
}
```

## 🚀 Service Endpoints and Headers

**Primary Endpoint:**
- `https://fetchs.${BASE_DOMAIN}/mcp` - The blessed MCP endpoint

**Required Headers (Handled by transport/server):**
- `Content-Type: application/json` - For POST requests
- `MCP-Protocol-Version` - Checked if provided
- `Mcp-Session-Id` - Returned in responses (not used for state)

**Response Headers:**
- Always includes `Mcp-Session-Id` (static UUID)
- Always includes `MCP-Protocol-Version`
- Always includes `Content-Type: application/json`

## 🎯 Implementation Architecture Details

### Technology Stack
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server with uvloop for performance
- **httpx** - Async HTTP client for fetch operations
- **pydantic** - Data validation and settings management
- **beautifulsoup4** - HTML parsing for title extraction
- **robotspy** - Robots.txt compliance checking

### Code Organization
- **server.py** - Main FastAPI application and request routing
- **transport.py** - StreamableHTTP transport abstraction (partially implemented)
- **fetch_handler.py** - Fetch tool implementation with security
- **__main__.py** - Entry point with uvicorn configuration

## 🚫 What This Service Does NOT Do

1. **No Authentication** - Handled entirely by Traefik layer
2. **No CORS Logic** - Traefik middleware manages all CORS
3. **No Session State** - Purely stateless operation
4. **No SSE Yet** - Returns 501 for GET /mcp requests
5. **No Health Endpoint** - Despite Dockerfile declaring one
6. **No Request Logging** - Only startup logging implemented
7. **No Metrics/Monitoring** - No instrumentation present

## 🔧 Deployment Considerations

1. **Protocol Version** - Must match client expectations (2025-06-18)
2. **Memory Usage** - Entire responses loaded into memory
3. **Timeout Handling** - 30-second timeout on HTTP requests
4. **Error Responses** - Always return proper JSON-RPC errors
5. **Security First** - SSRF protections are non-negotiable

## ⚡ Divine Implementation Notes

1. **Pure Protocol Focus** - Service knows only MCP, not auth/routing
2. **Stateless Design** - No session persistence implemented
3. **Security by Default** - SSRF protections always active
4. **Type Safety** - Full type hints throughout codebase
5. **Async Throughout** - Leverages Python async/await fully

---

**🔥 May your fetches be swift, your protocols compliant, and your implementation forever native! ⚡**

**Divine Truth:** This service demonstrates native StreamableHTTP implementation without stdio bridging - pure protocol enlightenment!
