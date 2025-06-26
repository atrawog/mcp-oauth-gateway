# 🔥 CLAUDE.md - The MCP-Fetch Service Divine Scripture! ⚡

**🌐 Behold! The Sacred MCP Fetch Server - Web Content Oracle of Divine Retrieval! 🌐**

**⚡ This is MCP-Fetch - The Holy Bridge Between Web Content and MCP Protocol! ⚡**

## 🔱 The Sacred Purpose of MCP-Fetch - Divine Web Fetching Power!

**The MCP-Fetch Service channels the blessed fetch capabilities through MCP protocol!**

This sacred service manifests these divine powers:
- **Web Content Retrieval** - Fetches URLs with divine HTTP mastery!
- **MCP Protocol Bridge** - Wraps fetch server in streamablehttp glory!
- **OAuth Protected** - Bearer token authentication enforced by Traefik!
- **Stateless Operation** - Pure functional fetching with no memory!
- **Production Ready** - Battle-tested with health monitoring!

**⚡ MCP-Fetch knows nothing of OAuth - pure protocol innocence maintained! ⚡**

## 🏗️ The Sacred Architecture - stdio-to-HTTP Transcendence!

```
MCP-Fetch Service (Port 3000)
├── mcp-streamablehttp-proxy (The Divine Bridge!)
│   ├── Spawns official @modelcontextprotocol/server-fetch
│   ├── Bridges stdio ↔ HTTP with blessed translation
│   └── Manages subprocess lifecycle with divine care
├── HTTP Endpoints (Blessed by the proxy!)
│   ├── /mcp - Primary MCP protocol endpoint
│   └── Health monitoring via MCP protocol
└── MCP Server Process (The stdio servant!)
    └── Official fetch server speaking JSON-RPC
```

**⚡ We wrap official servers - never reinvent the blessed wheel! ⚡**

## 🐳 The Docker Manifestation - Container of Protocol Purity!

### The Sacred Dockerfile Pattern
```dockerfile
FROM node:20-slim  # The blessed Node.js vessel!

# Install official MCP server
RUN npm install -g @modelcontextprotocol/server-fetch

# Install mcp-streamablehttp-proxy via pixi
# The divine bridge between stdio and HTTP!

EXPOSE 3000  # The blessed MCP port!
HEALTHCHECK  # Prove thy readiness to serve!

# Launch proxy wrapping the official server
CMD ["pixi", "run", "mcp-streamablehttp-proxy", "--stdio-command", "..."]
```

**⚡ Official server + proxy wrapper = Production MCP glory! ⚡**

## 🔧 The Sacred Configuration - Environment Variables of Service!

**MCP Protocol Settings:**
- `MCP_PROTOCOL_VERSION=2025-03-26` - Divine protocol covenant! (hardcoded - the fetch server only supports this version)
- `MCP_SESSION_TIMEOUT` - Session lifetime in seconds!
- `MCP_MAX_PARALLEL_REQUESTS` - Concurrent request blessing!

**Proxy Configuration:**
- `PROXY_HOST=0.0.0.0` - Listen on all interfaces!
- `PROXY_PORT=3000` - The blessed MCP port!
- Health checks use MCP protocol initialization!

**Service Discovery:**
- `BASE_DOMAIN` - For Traefik routing labels!
- `SERVICE_NAME=mcp-fetch` - Divine service identifier!

**⚡ Configuration flows through docker-compose environment! ⚡**

## 🚀 The Sacred Endpoints - MCP Protocol Altars!

### /mcp - The Primary Protocol Gateway!

**POST /mcp - JSON-RPC Request Processing!**
```json
{
  "jsonrpc": "2.0",
  "method": "fetch/get",
  "params": {
    "url": "https://example.com"
  },
  "id": "divine-request-001"
}
```

**Response Pattern:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": "<!DOCTYPE html>...",
    "headers": {},
    "status": 200
  },
  "id": "divine-request-001"
}
```

### Health Verification - Divine Liveness Through Protocol!

**MCP Protocol Health Check**
- Uses `initialize` method for health verification!
- Validates protocol version compliance!
- Ensures subprocess responds correctly!
- Docker healthcheck via MCP protocol!

## 🔐 The Security Architecture - Divine Protection Through Layers!

**The MCP-Fetch service itself knows NO authentication!**

Security is enforced by the sacred trinity:
1. **Traefik** - Enforces Bearer token authentication!
2. **Auth Service** - Validates tokens via ForwardAuth!
3. **MCP-Fetch** - Receives only pre-authenticated requests!

**⚡ This is the way of the trinity - separation brings security! ⚡**

## 📡 The MCP Protocol Implementation - 2025-03-26 Compliance!

### Supported MCP Methods (Blessed Fetch Capabilities!)

**fetch/get - Divine URL Retrieval!**
- Fetches web content with HTTP glory!
- Converts HTML to readable format!
- Returns headers and status codes!

**fetch/post - Sacred Data Submission!**
- Posts data to web endpoints!
- Supports JSON and form data!
- Handles authentication headers!

### The Session Management Dance

1. **Client sends `initialize`** - The sacred handshake!
2. **Server responds with capabilities** - Declaring its powers!
3. **Session ID assigned** - Via `Mcp-Session-Id` header!
4. **All requests include session** - Maintaining state continuity!
5. **Clean shutdown on disconnect** - Peaceful process death!

## 🔄 The Traefik Integration - Divine Routing Configuration!

```yaml
labels:
  # Basic routing - priority 2
  - "traefik.http.routers.mcp-fetch.rule=Host(`mcp-fetch.${BASE_DOMAIN}`)"
  - "traefik.http.routers.mcp-fetch.priority=2"

  # ForwardAuth middleware - divine authentication
  - "traefik.http.routers.mcp-fetch.middlewares=mcp-auth@docker"

  # Service definition
  - "traefik.http.services.mcp-fetch.loadbalancer.server.port=3000"

  # OAuth discovery routing - priority 10
  - "traefik.http.routers.mcp-fetch-oauth-discovery.rule=..."
  - "traefik.http.routers.mcp-fetch-oauth-discovery.priority=10"
```

**⚡ Priorities prevent the catch-all from devouring sacred paths! ⚡**

## 🧪 Testing the MCP-Fetch Service - Divine Verification!

```bash
# Basic health verification
just test-mcp-fetch-health

# Full MCP protocol test
just test-mcp-fetch-protocol

# Fetch functionality test
just test-mcp-fetch-content

# Integration with auth
just test-mcp-fetch-auth
```

**⚡ Real services, real tests - no mocking in this realm! ⚡**

## 🔥 Common Issues and Divine Solutions!

### "Connection Refused" - Service Not Ready!
- Check Docker health status!
- Verify proxy is running!
- Ensure port 3000 is exposed!

### "401 Unauthorized" - Token Rejection!
- Verify Bearer token in Authorization header!
- Check token hasn't expired!
- Ensure ForwardAuth middleware active!

### "MCP Protocol Error" - Protocol Violation!
- Include MCP-Protocol-Version header!
- Send proper JSON-RPC format!
- Check session ID consistency!

### "Fetch Failed" - External URL Issues!
- Verify target URL is accessible!
- Check for CORS or blocking!
- Review fetch server logs!

## 📜 The Integration Flow - How Requests Reach Fetch!

1. **Client Request** → `https://fetch.domain.com/mcp`
2. **Traefik Routes** → Checks authentication via ForwardAuth
3. **Auth Validates** → Token verification at /verify endpoint
4. **Request Forwarded** → Reaches MCP-Fetch on port 3000
5. **Proxy Translates** → HTTP → stdio → fetch server
6. **Fetch Executes** → Retrieves web content
7. **Response Returns** → stdio → HTTP → client

**⚡ Each layer has its purpose in the divine flow! ⚡**

## 🎯 The Divine Mission - MCP-Fetch Responsibilities!

**What MCP-Fetch MUST Do:**
- Wrap official @modelcontextprotocol/server-fetch!
- Provide HTTP endpoints via proxy!
- Handle MCP protocol correctly!
- Fetch web content reliably!
- Maintain stateless operation!

**What MCP-Fetch MUST NOT Do:**
- Implement authentication logic!
- Know about OAuth flows!
- Store user state!
- Route to other services!
- Modify the official server behavior!

**⚡ Purity of purpose brings reliability! ⚡**

## 🛠️ Debugging Commands - Divine Troubleshooting!

```bash
# View service logs
just logs mcp-fetch

# Check proxy process
docker exec mcp-fetch ps aux

# Test direct MCP call
curl -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"fetch/get","params":{"url":"https://example.com"},"id":1}' \
     https://mcp-fetch.domain.com/mcp

# Monitor health endpoint
# Monitor service via MCP protocol
curl -X POST http://localhost:3000/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"'"$MCP_PROTOCOL_VERSION"'","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'
```

## 🔱 The Sacred Truth of MCP Services!

**All MCP services in this gateway follow the same blessed pattern:**
1. **Official MCP server** - From @modelcontextprotocol/servers!
2. **mcp-streamablehttp-proxy** - The stdio-to-HTTP bridge!
3. **Docker container** - Isolated and manageable!
4. **Traefik routing** - With ForwardAuth protection!
5. **No auth knowledge** - Pure protocol implementation!

**⚡ This pattern scales to ANY MCP server! ⚡**

---

**🔥 May your fetches be swift, your content accessible, and your protocols forever compliant! ⚡**
