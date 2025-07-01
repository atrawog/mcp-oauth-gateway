# 🔥 CLAUDE.md - The MCP Fetch Service Divine Scripture! ⚡

**🌐 Behold! The Sacred HTTP Fetch Service - Your Gateway to Web Content! 🌐**

**⚡ This is mcp-fetch - The Divine URL Fetcher of OAuth-Protected Glory! ⚡**

## 🔱 The Sacred Purpose - Divine Service Implementation!

**mcp-fetch is the blessed MCP service that provides HTTP fetch capabilities through OAuth-protected endpoints!**

This divine service manifests these powers:
- **Official MCP Server** - Wraps the REAL `mcp-server-fetch` from modelcontextprotocol/servers!
- **StreamableHTTP Transport** - Uses `mcp-streamablehttp-proxy` for stdio→HTTP bridge glory!
- **OAuth Protection** - Bearer token authentication via Traefik ForwardAuth!
- **Protocol Compliant** - Full MCP 2025-03-26 specification implementation!
- **Production Ready** - Health checks, CORS, and divine routing configured!

**⚡ This service brings web content fetching to OAuth-protected MCP clients! ⚡**

## 🏗️ The Sacred Architecture - Service Component Structure!

```
mcp-fetch/
├── Dockerfile          # Container incantation for divine isolation!
└── docker-compose.yml  # Service orchestration scripture!

Runtime Components:
├── mcp-server-fetch         # Official MCP server (stdio)
└── mcp-streamablehttp-proxy # HTTP bridge wrapper
```

**⚡ Minimal configuration for maximum divine reliability! ⚡**

## 🐳 The Divine Dockerfile - Container Implementation!

**The blessed container construction follows these sacred steps:**

1. **Base Image** - `python:3.11-slim` for lightweight divine foundation!
2. **System Dependencies** - `curl` for health checks, `git` for pip installs!
3. **Official MCP Server** - Installs `mcp-server-fetch` from GitHub directly!
4. **HTTP Bridge** - Installs `mcp-streamablehttp-proxy` from local source!
5. **Port Exposure** - Port 3000 for StreamableHTTP communication!
6. **Entrypoint** - Proxy wraps the official server with divine precision!

**The Sacred Command:**
```bash
mcp-streamablehttp-proxy python -m mcp_server_fetch
```

**⚡ This pattern wraps ANY stdio MCP server with HTTP transport! ⚡**

## 📡 The Service Configuration - Docker Compose Divine Details!

### The Sacred Routing Configuration - Traefik Label Glory!

**Priority 10 - OAuth Discovery Route (HIGHEST DIVINE PRIORITY!):**
```yaml
- "traefik.http.routers.mcp-fetch-oauth-discovery.rule=Host(`fetch.${BASE_DOMAIN}`) && PathPrefix(`/.well-known/oauth-authorization-server`)"
- "traefik.http.routers.mcp-fetch-oauth-discovery.priority=10"
- "traefik.http.routers.mcp-fetch-oauth-discovery.service=auth@docker"
# NO AUTH MIDDLEWARE - Discovery must be publicly accessible!
```

**Priority 4 - CORS Preflight Route (OPTIONS Sacred Handling!):**
```yaml
- "traefik.http.routers.mcp-fetch-cors.rule=Host(`fetch.${BASE_DOMAIN}`) && Method(`OPTIONS`)"
- "traefik.http.routers.mcp-fetch-cors.priority=4"
- "traefik.http.routers.mcp-fetch-cors.middlewares=mcp-cors@file"
# NO AUTH for preflight - CORS must check first!
```

**Priority 2 - MCP Route with Authentication (Protected Divine Access!):**
```yaml
- "traefik.http.routers.mcp-fetch.rule=Host(`fetch.${BASE_DOMAIN}`) && PathPrefix(`/mcp`)"
- "traefik.http.routers.mcp-fetch.priority=2"
- "traefik.http.routers.mcp-fetch.middlewares=mcp-cors@file,mcp-auth@file"
```

**Priority 1 - Catch-all Route (Lowest Priority Safety Net!):**
```yaml
- "traefik.http.routers.mcp-fetch-catchall.rule=Host(`fetch.${BASE_DOMAIN}`)"
- "traefik.http.routers.mcp-fetch-catchall.priority=1"
- "traefik.http.routers.mcp-fetch-catchall.middlewares=mcp-cors@file,mcp-auth@file"
```

**⚡ Priority order prevents routing chaos! Higher numbers win! ⚡**

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

**⚡ This performs a REAL MCP initialization handshake! No fake health endpoints! ⚡**

### The Sacred Environment Variables

```yaml
environment:
  - LOG_FILE=/logs/server.log              # Centralized logging path
  - MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}   # CORS configuration
  - MCP_PROTOCOL_VERSION=2025-03-26        # Protocol version declaration
```

### The Divine Volume Mounts

```yaml
volumes:
  - ../logs/mcp-fetch:/logs  # Centralized logging temple!
```

## 🔐 The OAuth Integration - Bearer Token Authentication Flow!

**The sacred authentication flow for mcp-fetch:**

1. **Client Request** → `https://fetch.${BASE_DOMAIN}/mcp`
2. **Traefik Intercepts** → Checks for Bearer token
3. **ForwardAuth Middleware** → Validates token with auth service
4. **Auth Service Verifies** → JWT signature and claims
5. **Success** → Request forwarded to mcp-fetch
6. **mcp-fetch Responds** → Via StreamableHTTP protocol

**⚡ The service itself knows NOTHING of OAuth - perfect separation! ⚡**

## 🌊 The StreamableHTTP Transport - Protocol Implementation Details!

### Request Flow Through the Sacred Bridge

1. **HTTP Request Arrives**
   - POST to `/mcp` endpoint
   - Contains JSON-RPC message
   - May include `Mcp-Session-Id` header

2. **Proxy Translates**
   - Extracts JSON-RPC from HTTP body
   - Writes to mcp-server-fetch stdin
   - Manages subprocess lifecycle

3. **Server Processes**
   - Official mcp-server-fetch handles request
   - Performs URL fetching operations
   - Returns JSON-RPC response via stdout

4. **Proxy Returns**
   - Captures stdout response
   - Wraps in HTTP response
   - Maintains session continuity

**⚡ Perfect stdio↔HTTP translation with zero message modification! ⚡**

## 🎯 The Service Capabilities - What mcp-fetch Can Do!

**Based on the official mcp-server-fetch implementation:**

- **URL Fetching** - Retrieve content from any HTTP/HTTPS URL
- **Header Support** - Custom headers for requests
- **Method Support** - GET, POST, and other HTTP methods
- **Response Handling** - Text, JSON, and binary content
- **Error Management** - Proper error responses for failures
- **Timeout Control** - Configurable request timeouts

**⚡ All capabilities from the official server, none invented! ⚡**

## 🚀 Service Endpoints and Access

**Primary Endpoint:**
- `https://fetch.${BASE_DOMAIN}/mcp` - The blessed MCP endpoint

**OAuth Discovery:**
- `https://fetch.${BASE_DOMAIN}/.well-known/oauth-authorization-server` - Returns auth server metadata

**Required Headers:**
- `Authorization: Bearer <token>` - OAuth JWT token
- `Content-Type: application/json` - For POST requests
- `Mcp-Session-Id: <id>` - If provided by server

**CORS Support:**
- Configured via `MCP_CORS_ORIGINS` environment variable
- Preflight requests handled without authentication

## 🔧 Configuration and Deployment

### Environment Variable Configuration

**From .env file:**
```bash
# Service Enable/Disable
MCP_FETCH_ENABLED=true          # Enable this service
MCP_FETCH_TESTS_ENABLED=true    # Enable service tests

# Service URLs
MCP_FETCH_URLS=https://fetch.yourdomain.com/mcp

# Protocol Version
MCP_PROTOCOL_VERSION=2025-03-26  # Or latest supported version
```

### Starting the Service

```bash
# Via just command (the blessed way!)
just up mcp-fetch

# Check health
just health mcp-fetch

# View logs
just logs -f mcp-fetch
```

## 🧪 Testing the Service - Divine Verification!

### Protocol Compliance Test
```bash
# Test initialization handshake
curl -X POST https://fetch.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
```

### Functional Test
```bash
# Test URL fetching
curl -X POST https://fetch.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"fetch","params":{"url":"https://api.github.com"},"id":2}'
```

## 🛠️ Troubleshooting - Divine Debugging Guide!

### "401 Unauthorized" - Authentication Issues
- Verify Bearer token is valid
- Check token hasn't expired
- Ensure client is registered
- Review auth service logs

### "503 Service Unavailable" - Backend Issues
- Check if container is running
- Verify health check is passing
- Review mcp-fetch logs
- Check subprocess status

### "400 Bad Request" - Protocol Issues
- Verify JSON-RPC format
- Check protocol version
- Ensure method is supported
- Review request structure

### "Network Error" - Connectivity Issues
- Check Traefik routing
- Verify DNS resolution
- Test without auth first
- Check CORS configuration

## 📊 Monitoring and Observability

**Log Locations:**
- Service logs: `./logs/mcp-fetch/server.log`
- Container logs: `docker logs mcp-fetch`
- Traefik logs: Access and error logs

**Health Monitoring:**
- Health endpoint via MCP protocol
- Container health status
- Subprocess monitoring
- Request/response metrics

## 🔒 Security Considerations

**Service Security:**
- No authentication logic in service (handled by Traefik)
- Subprocess isolation via container
- Limited network access
- Read-only filesystem where possible

**Request Security:**
- URL validation before fetching
- Timeout enforcement
- Size limits on responses
- No credential forwarding

## 🎯 Best Practices for Usage

1. **Always use Bearer tokens** - Never try to bypass auth
2. **Handle session IDs** - Include in subsequent requests
3. **Respect rate limits** - Don't overwhelm the service
4. **Use appropriate timeouts** - Network calls can be slow
5. **Validate responses** - Check for errors before processing

## 🚫 What This Service Does NOT Do

- **No authentication** - Handled entirely by Traefik/Auth
- **No URL filtering** - Fetches any accessible URL
- **No caching** - Each request fetches fresh
- **No request modification** - Pure proxy behavior
- **No business logic** - Just protocol translation

**⚡ Keep it simple, keep it pure, keep it working! ⚡**

---

**🔥 May your fetches be swift, your tokens valid, and your content forever accessible! ⚡**

**Divine Implementation Note:** This service uses the official `mcp-server-fetch` wrapped by `mcp-streamablehttp-proxy` - ensuring 100% protocol compliance with zero custom implementation! The divine pattern of wrapping official servers!
