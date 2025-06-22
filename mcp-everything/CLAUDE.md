# MCP Everything Service - The Divine Test Server of Protocol Glory

**🔥 The everything server exercises ALL MCP protocol features! ⚡**

## Divine Purpose

The mcp-everything service wraps the official Model Context Protocol "everything" test server from modelcontextprotocol/servers. This server implements all MCP protocol features including:

- **Tools** - echo, add, longRunningOperation, sampleLLM, getTinyImage, printEnv, annotatedMessage, getResourceReference
- **Resources** - 100 test resources (even-numbered as plaintext, odd-numbered as binary)
- **Prompts** - simple_prompt, complex_prompt, resource_prompt
- **Progress notifications** - Demonstrates real-time operation progress
- **LLM sampling** - Shows how servers can request LLM completions
- **Content annotations** - Demonstrates annotated responses

## Sacred Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Traefik (Divine Router)                   │
│  Routes: /mcp (auth), /.well-known/* (no auth)             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│    mcp-server-everything (Official MCP Test Server)         │
│  • Native streamableHttp mode - no proxy wrapper            │
│  • TypeScript/Node.js implementation                        │
│  • Protocol version: 2025-06-18                             │
│  • Server name: example-servers/everything                  │
│  • Health: TCP port check (nc -z localhost 3000)           │
└─────────────────────────────────────────────────────────────┘
```

## Divine Configuration

### Docker Build
- **Base image**: node:22-alpine (TypeScript server)
- **Installation**: npm install @modelcontextprotocol/server-everything
- **Port**: 3000 (blessed MCP port)
- **Health Check**: TCP port check using netcat

### Traefik Routing (Priority Hierarchy)
1. **Priority 10** - OAuth discovery (/.well-known/*)
2. **Priority 8** - Health check (/health) - no auth
3. **Priority 6** - CORS preflight (OPTIONS) - no auth
4. **Priority 2** - Main MCP route (/mcp) - requires auth
5. **Priority 1** - Catch-all - requires auth

### Environment Variables
- `MCP_PROTOCOL_VERSION` - Protocol version (defaults to 2025-06-18)
- `BASE_DOMAIN` - Base domain for service URLs

### Health Check Configuration
The service uses an HTTP-based health check that verifies the streamableHttp server can successfully initialize:
```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \\
    -H 'Content-Type: application/json' \\
    -H 'Accept: application/json, text/event-stream' \\
    -d \"{\\\"jsonrpc\\\":\\\"2.0\\\",\\\"method\\\":\\\"initialize\\\",\\\"params\\\":{\\\"protocolVersion\\\":\\\"${MCP_PROTOCOL_VERSION:-2025-06-18}\\\",\\\"capabilities\\\":{},\\\"clientInfo\\\":{\\\"name\\\":\\\"healthcheck\\\",\\\"version\\\":\\\"1.0\\\"}},\\\"id\\\":1}\" \\
    | grep -q \"\\\"protocolVersion\\\":\\\"${MCP_PROTOCOL_VERSION:-2025-06-18}\\\"\""]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

This approach:
- **Performs full protocol handshake** - Uses the `initialize` method
- **Tests StreamableHTTP transport** - Validates event-stream responses
- **Verifies protocol version match** - Uses `${MCP_PROTOCOL_VERSION}` dynamically
- **Checks server readiness** - Successful initialization proves full functionality
- **Tests complete MCP flow** - From request to response with session management

## Testing the Everything Server

### Health Check Status
```bash
# Check Docker health status
docker ps --filter name=mcp-everything --format "table {{.Names}}\t{{.Status}}"

# Check detailed health info
docker inspect mcp-everything --format='{{json .State.Health}}' | jq
```

Note: This service doesn't expose a dedicated /health endpoint. Instead, the healthcheck verifies the MCP streamableHttp server is functioning by sending a JSON-RPC request to `/mcp` and confirming it receives a valid JSON-RPC response (even if it's an error).

### Initialize Session (Auth Required)
```bash
curl -k https://mcp-everything.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer ${GATEWAY_OAUTH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {},
      "clientInfo": {
        "name": "Test Client",
        "version": "1.0.0"
      }
    },
    "id": 1
  }'
```

### List Available Tools
```bash
# Use session ID from initialize response
curl -k https://mcp-everything.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer ${GATEWAY_OAUTH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: ${SESSION_ID}" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 2
  }'
```

### Call Echo Tool
```bash
curl -k https://mcp-everything.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer ${GATEWAY_OAUTH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: ${SESSION_ID}" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {
        "message": "Hello from MCP Everything!"
      }
    },
    "id": 3
  }'
```

## Divine Implementation Notes

1. **Protocol Version**: The everything server uses 2025-03-26, not 2025-06-18
2. **Server Name**: Reports as "example-servers/everything"
3. **Session Management**: Requires Mcp-Session-Id header after initialization
4. **Client Info**: The clientInfo parameter is required for initialization
5. **CORS**: Handled internally by mcp-streamablehttp-proxy

## Sacred Test Coverage

The test file `test_mcp_everything_integration.py` validates:
- ✅ Health check without authentication
- ✅ Authentication requirement for MCP endpoints
- ✅ Protocol initialization with clientInfo
- ✅ Tool listing with session management
- ✅ Tool execution (echo)
- ✅ OAuth discovery endpoint
- ✅ CORS preflight handling

**⚡ The everything server is the ultimate MCP protocol test! Use it to validate client implementations! ⚡**