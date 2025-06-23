# 🔥 CLAUDE.md - The MCP-Filesystem Service Divine Scripture! ⚡

**📁 Behold! The Sacred MCP Filesystem Server - File System Oracle of Divine Access! 📁**

**⚡ This is MCP-Filesystem - The Holy Bridge Between File Systems and MCP Protocol! ⚡**

## 🔱 The Sacred Purpose of MCP-Filesystem - Divine File System Power!

**The MCP-Filesystem Service channels the blessed filesystem capabilities through MCP protocol!**

This sacred service manifests these divine powers:
- **File System Access** - Read, write, and manage files with divine authority!
- **Directory Navigation** - Traverse the file system hierarchy with blessed permission!
- **MCP Protocol Bridge** - Wraps filesystem server in streamablehttp glory!
- **OAuth Protected** - Bearer token authentication enforced by Traefik!
- **Sandboxed Operation** - Restricted to /workspace for divine security!
- **Production Ready** - Battle-tested with health monitoring!

**⚡ MCP-Filesystem knows nothing of OAuth - pure protocol innocence maintained! ⚡**

## 🏗️ The Sacred Architecture - stdio-to-HTTP Transcendence!

```
MCP-Filesystem Service (Port 3000)
├── mcp-streamablehttp-proxy (The Divine Bridge!)
│   ├── Spawns official @modelcontextprotocol/server-filesystem
│   ├── Bridges stdio ↔ HTTP with blessed translation
│   └── Manages subprocess lifecycle with divine care
├── HTTP Endpoints (Blessed by the proxy!)
│   ├── /mcp - Primary MCP protocol endpoint
│   └── Health monitoring via MCP protocol
└── MCP Server Process (The stdio servant!)
    └── Official filesystem server speaking JSON-RPC
```

**⚡ We wrap official servers - never reinvent the blessed wheel! ⚡**

## 🐳 The Docker Manifestation - Container of Protocol Purity!

### The Sacred Dockerfile Pattern
```dockerfile
FROM python:3.11-slim  # The blessed Python vessel!

# Install official MCP server
RUN pip install mcp-server-filesystem

# Install mcp-streamablehttp-proxy
# The divine bridge between stdio and HTTP!

EXPOSE 3000  # The blessed MCP port!
HEALTHCHECK  # Prove thy readiness to serve!

# Launch proxy wrapping the official server
CMD ["mcp-streamablehttp-proxy", "python", "-m", "mcp_server_filesystem", "/workspace"]
```

**⚡ Official server + proxy wrapper = Production MCP glory! ⚡**

## 🔧 The Sacred Configuration - Environment Variables of Service!

**MCP Protocol Settings:**
- `MCP_PROTOCOL_VERSION=2025-03-26` - Divine protocol covenant! (hardcoded - the filesystem server only supports this version)
- `MCP_SESSION_TIMEOUT` - Session lifetime in seconds!
- `MCP_MAX_PARALLEL_REQUESTS` - Concurrent request blessing!

**Proxy Configuration:**
- `PROXY_HOST=0.0.0.0` - Listen on all interfaces!
- `PROXY_PORT=3000` - The blessed MCP port!
- Health checks use MCP protocol initialization!

**Service Discovery:**
- `BASE_DOMAIN` - For Traefik routing labels!
- `SERVICE_NAME=mcp-filesystem` - Divine service identifier!

**Filesystem Configuration:**
- Volume mount: `./workspace:/workspace:rw` - The blessed workspace!
- Working directory: `/workspace` - Root of filesystem access!

**⚡ Configuration flows through docker-compose environment! ⚡**

## 🚀 The Sacred Endpoints - MCP Protocol Altars!

### /mcp - The Primary Protocol Gateway!

**POST /mcp - JSON-RPC Request Processing!**
```json
{
  "jsonrpc": "2.0",
  "method": "filesystem/read",
  "params": {
    "path": "/workspace/example.txt"
  },
  "id": "divine-request-001"
}
```

**Response Pattern:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": "File contents here...",
    "mimeType": "text/plain",
    "size": 1024
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

**The MCP-Filesystem service itself knows NO authentication!**

Security is enforced by the sacred trinity:
1. **Traefik** - Enforces Bearer token authentication!
2. **Auth Service** - Validates tokens via ForwardAuth!
3. **MCP-Filesystem** - Receives only pre-authenticated requests!

**Additional Security Measures:**
- **Sandboxed to /workspace** - No access outside blessed directory!
- **Volume-mounted directory** - Controlled via Docker!
- **Read-write permissions** - Configurable per deployment!

**⚡ This is the way of the trinity - separation brings security! ⚡**

## 📡 The MCP Protocol Implementation - 2025-03-26 Compliance!

### Supported MCP Methods (Blessed Filesystem Capabilities!)

**filesystem/read - Divine File Retrieval!**
- Reads file contents with blessed access!
- Returns MIME type and metadata!
- Handles binary and text files!

**filesystem/write - Sacred Content Creation!**
- Writes data to files with divine authority!
- Creates directories as needed!
- Preserves file permissions!

**filesystem/list - Directory Enumeration!**
- Lists directory contents!
- Returns file metadata!
- Supports recursive traversal!

**filesystem/move - File Relocation!**
- Moves files and directories!
- Atomic operations when possible!
- Preserves attributes!

**filesystem/delete - Sacred Removal!**
- Deletes files and directories!
- Recursive deletion support!
- Safety confirmations!

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
  - "traefik.http.routers.mcp-filesystem.rule=Host(`mcp-filesystem.${BASE_DOMAIN}`)"
  - "traefik.http.routers.mcp-filesystem.priority=2"
  
  # ForwardAuth middleware - divine authentication
  - "traefik.http.routers.mcp-filesystem.middlewares=mcp-auth@docker"
  
  # Service definition
  - "traefik.http.services.mcp-filesystem.loadbalancer.server.port=3000"
  
  # OAuth discovery routing - priority 10
  - "traefik.http.routers.mcp-filesystem-oauth-discovery.rule=..."
  - "traefik.http.routers.mcp-filesystem-oauth-discovery.priority=10"
```

**⚡ Priorities prevent the catch-all from devouring sacred paths! ⚡**

## 🧪 Testing the MCP-Filesystem Service - Divine Verification!

```bash
# Basic health verification via MCP protocol
curl -X POST http://localhost:3000/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"'"$MCP_PROTOCOL_VERSION"'","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'

# Test file read operation
curl -X POST https://mcp-filesystem.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "filesystem/read",
    "params": {"path": "/workspace/test.txt"},
    "id": 1
  }'

# Test directory listing
curl -X POST https://mcp-filesystem.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "filesystem/list",
    "params": {"path": "/workspace"},
    "id": 2
  }'
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

### "Permission Denied" - Filesystem Access Issues!
- Check volume mount permissions!
- Verify /workspace directory exists!
- Review container user permissions!

### "Path Not Found" - Invalid File Path!
- Ensure path starts with /workspace!
- Check file actually exists!
- Verify no symlink escapes!

## 📜 The Integration Flow - How Requests Reach Filesystem!

1. **Client Request** → `https://mcp-filesystem.domain.com/mcp`
2. **Traefik Routes** → Checks authentication via ForwardAuth
3. **Auth Validates** → Token verification at /verify endpoint
4. **Request Forwarded** → Reaches MCP-Filesystem on port 3000
5. **Proxy Translates** → HTTP → stdio → filesystem server
6. **Filesystem Executes** → Performs file operation
7. **Response Returns** → stdio → HTTP → client

**⚡ Each layer has its purpose in the divine flow! ⚡**

## 🎯 The Divine Mission - MCP-Filesystem Responsibilities!

**What MCP-Filesystem MUST Do:**
- Wrap official @modelcontextprotocol/server-filesystem!
- Provide HTTP endpoints via proxy!
- Handle MCP protocol correctly!
- Access files within /workspace sandbox!
- Maintain stateless operation per request!

**What MCP-Filesystem MUST NOT Do:**
- Implement authentication logic!
- Know about OAuth flows!
- Access files outside /workspace!
- Route to other services!
- Modify the official server behavior!

**⚡ Purity of purpose brings reliability! ⚡**

## 🛠️ Debugging Commands - Divine Troubleshooting!

```bash
# View service logs
docker logs mcp-filesystem -f

# Check proxy process
docker exec mcp-filesystem ps aux

# Verify workspace mount
docker exec mcp-filesystem ls -la /workspace

# Test direct MCP call
curl -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"filesystem/list","params":{"path":"/workspace"},"id":1}' \
     https://mcp-filesystem.domain.com/mcp

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

## 📂 Workspace Directory Structure - The Sacred File Hierarchy!

```
/workspace/                  # Root of filesystem access
├── projects/               # User project files
├── data/                   # Data storage
├── temp/                   # Temporary files
└── shared/                 # Shared resources
```

**The workspace directory is:**
- Volume-mounted from host
- Persistent across container restarts
- Isolated from system files
- Configurable permissions

---

**🔥 May your files be accessible, your operations atomic, and your protocols forever compliant! ⚡**