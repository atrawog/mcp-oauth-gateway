# MCP Filesystem Service - The Divine File System Oracle

**🗄️ Behold! The sacred gateway to the file system realm! ⚡**

## Service Overview - The Divine Purpose

**🔥 This service grants blessed MCP clients access to file system operations! ⚡**

The mcp-filesystem service channels the divine powers of the official `mcp-server-filesystem` from modelcontextprotocol/servers, wrapping it in the blessed StreamableHTTP proxy pattern for OAuth-protected web access!

## Sacred Implementation Pattern - The Proxy Architecture

**⚡ Pattern 1: The Sacred Proxy Pattern - As decreed by the gateway commandments! ⚡**

This service follows the blessed proxy pattern:
- **Official MCP Server**: Uses `mcp-server-filesystem` from GitHub's divine repository!
- **Divine Bridge**: `mcp-streamablehttp-proxy` transforms stdio ↔ HTTP with sacred transcendence!
- **Protocol Version**: Blessed with `2025-03-26` - The covenant of file system communion!

## The Divine Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   mcp-filesystem Service                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │        mcp-streamablehttp-proxy (Port 3000)         │    │
│  │  • Receives HTTP requests on /mcp endpoint          │    │
│  │  • Manages subprocess lifecycle                     │    │
│  │  • Bridges HTTP ↔ stdio with divine translation     │    │
│  └─────────────────────────────────────────────────────┘    │
│                            ↓                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │          mcp-server-filesystem (stdio)              │    │
│  │  • Official MCP filesystem implementation           │    │
│  │  • Serves /workspace directory with sacred access   │    │
│  │  • Pure stdio JSON-RPC communication                │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Sacred Configuration

### Environment Variables - The Divine Settings

```bash
LOG_FILE=/logs/server.log         # Sacred log destination
MCP_CORS_ORIGINS=${MCP_CORS_ORIGINS}  # Blessed CORS origins
MCP_PROTOCOL_VERSION=2025-03-26   # The covenant version
```

### Volume Mounts - The Sacred Storage Paths

```yaml
./workspace:/workspace:rw    # The blessed directory for file operations
../logs/mcp-filesystem:/logs # The divine log sanctuary
```

**⚡ The /workspace directory is the sacred realm where all file operations occur! ⚡**

## Traefik Routing Configuration - The Divine Traffic Laws

**🚦 The sacred routing hierarchy with blessed priorities! 🚦**

### Priority 10 - OAuth Discovery (Highest Divine Priority!)
```yaml
/.well-known/oauth-authorization-server → auth service
# No authentication - Public salvation for all who seek!
```

### Priority 4 - CORS Preflight
```yaml
OPTIONS requests → Direct to service
# No authentication - CORS must fly freely!
```

### Priority 2 - MCP Endpoint
```yaml
/mcp → mcp-filesystem service
# Protected by mcp-auth middleware - Bearer token required!
```

### Priority 1 - Catch-all
```yaml
All other paths → mcp-filesystem service
# Protected by mcp-auth middleware - Bearer token required!
```

## Health Check Implementation - The Divine Vitality Test

**🏥 The sacred MCP protocol initialization handshake! ⚡**

```bash
curl -s -X POST http://localhost:3000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{
    "jsonrpc":"2.0",
    "method":"initialize",
    "params":{
      "protocolVersion":"2025-03-26",
      "capabilities":{},
      "clientInfo":{
        "name":"healthcheck",
        "version":"1.0"
      }
    },
    "id":1
  }'
```

**⚡ Success confirmed by protocol version in response - divine handshake complete! ⚡**

## Service Endpoint - The Sacred Access Portal

**🌐 The blessed URL structure for divine file system access! ⚡**

```
https://filesystem.${BASE_DOMAIN}/mcp
```

**Required Headers for Divine Communication:**
- `Authorization: Bearer <token>` - The blessed OAuth token!
- `Content-Type: application/json` - The sacred content type!
- `Accept: application/json, text/event-stream` - For blessed streaming!

## Docker Implementation - The Container Incantation

**🐳 The divine container configuration! ⚡**

1. **Base Image**: `node:20-slim` - The blessed Node.js foundation!
2. **Official Server**: Cloned from `modelcontextprotocol/servers` GitHub temple!
3. **Proxy Installation**: `mcp-streamablehttp-proxy` via pip3!
4. **Execution**: `mcp-streamablehttp-proxy mcp-server-filesystem /workspace`

## The Sacred Filesystem Capabilities

**📁 What this divine service provides through the official MCP server! ⚡**

The wrapped `mcp-server-filesystem` provides blessed file operations within `/workspace`:
- **Read Operations** - View the sacred texts!
- **Write Operations** - Inscribe new wisdom!
- **Directory Operations** - Navigate the holy file tree!
- **File Metadata** - Divine attributes revealed!

**⚡ All operations are confined to /workspace - the sacred sandbox! ⚡**

## Integration with Gateway - The Divine Unity

**🔐 How this service achieves OAuth-protected glory! ⚡**

1. **Traefik Routes** - Divine traffic control with sacred priorities!
2. **ForwardAuth Middleware** - Bearer token validation through auth service!
3. **CORS Support** - Cross-origin blessings for web clients!
4. **Session Management** - Via Mcp-Session-Id headers if needed!

## Security Boundaries - The Sacred Limits

**🛡️ Divine protections enforced by design! ⚡**

- **Workspace Isolation** - Only `/workspace` is accessible, no escape!
- **OAuth Protection** - All endpoints require blessed bearer tokens!
- **No Direct Access** - Must flow through Traefik's divine judgment!
- **Process Isolation** - Container + subprocess = double divine isolation!

**⚡ Violate these boundaries and face filesystem chaos! ⚡**

## The Sacred Commandments for Maintenance

**🔧 When working with this divine service! ⚡**

1. **Never modify the proxy** - It channels divine stdio transformation!
2. **Update via official repo** - Pull latest `mcp-server-filesystem` from GitHub!
3. **Respect the workspace** - All operations stay within `/workspace` sanctuary!
4. **Monitor the logs** - Divine wisdom flows to `/logs/server.log`!
5. **Test with real clients** - No mocks, only blessed integration tests!

**⚡ Follow these commandments or face production filesystem disasters! ⚡**
