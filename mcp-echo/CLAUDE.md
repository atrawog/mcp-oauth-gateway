# 🔥 CLAUDE.md - The MCP-Echo Service Divine Scripture! ⚡

**🗣️ Behold! The Sacred MCP Echo Server - The Divine Echo Chamber of Testing! 🗣️**

**⚡ This is MCP-Echo - The Holy Testing Ground for MCP Protocol Compliance! ⚡**

## 🔱 The Sacred Purpose of MCP-Echo - Divine Testing Power!

**The MCP-Echo Service channels the blessed testing capabilities through MCP protocol!**

This sacred service manifests these divine powers:
- **Echo Tool** - Returns thy message with perfect fidelity!
- **PrintEnv Tool** - Reveals environment variable secrets!
- **Stateless Operation** - Pure functional echo with no memory!
- **Debug Mode** - Divine message tracing for enlightenment!
- **Production Ready** - Battle-tested with health monitoring!

**⚡ MCP-Echo knows nothing of OAuth - pure protocol innocence maintained! ⚡**

## 🏗️ The Sacred Architecture - Native StreamableHTTP Implementation!

```
MCP-Echo Service (Port 3000)
├── StreamableHTTP Server (The Divine Implementation!)
│   ├── Native Python MCP SDK usage
│   ├── Direct HTTP endpoint at /mcp
│   └── Stateless request handling
├── Tool Implementations (Blessed Functions!)
│   ├── echo - Mirror thy words
│   └── printEnv - Reveal thy environment
└── Debug Logging (Optional Enlightenment!)
    └── Full request/response tracing
```

**⚡ Pure Python implementation - no subprocess complexity! ⚡**

## 🐳 The Docker Manifestation - Container of Testing Purity!

### The Sacred Dockerfile Pattern
```dockerfile
FROM python:3.11-slim  # The blessed Python vessel!

# Install the package from source
COPY mcp-echo-streamablehttp-server-stateless/ ./

# Debug mode enabled by divine decree!
ENV MCP_ECHO_DEBUG=true

EXPOSE 3000  # The blessed MCP port!
HEALTHCHECK  # Prove thy readiness to echo!

# Launch the server directly
CMD ["mcp-echo-streamablehttp-server-stateless"]
```

**⚡ Simple server + debug logging = Testing enlightenment! ⚡**

## 🔧 The Sacred Configuration - Environment Variables of Echo!

**MCP Protocol Settings:**
- `MCP_PROTOCOL_VERSION=2025-03-26` - Divine protocol covenant!
- `MCP_ECHO_DEBUG=true` - Enable divine message tracing!

**Server Configuration:**
- `MCP_ECHO_HOST=0.0.0.0` - Listen on all interfaces!
- `MCP_ECHO_PORT=3000` - The blessed MCP port!
- Health checks use MCP protocol initialization!

**Service Discovery:**
- `BASE_DOMAIN` - For Traefik routing labels!
- `SERVICE_NAME=mcp-echo` - Divine service identifier!

**⚡ Configuration flows through docker-compose environment! ⚡**

## 🚀 The Sacred Endpoints - MCP Protocol Testing Altars!

### /mcp - The Primary Protocol Gateway!

**Initialize Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "capabilities": {},
    "clientInfo": {
      "name": "test-client",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

**Echo Tool Call:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "echo",
    "arguments": {
      "message": "Hello, MCP!"
    }
  },
  "id": 2
}
```

**PrintEnv Tool Call:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "printEnv",
    "arguments": {
      "name": "USER"
    }
  },
  "id": 3
}
```

### Health Verification - Divine Liveness Through Protocol!

**MCP Protocol Health Check**
- Uses `initialize` method for health verification!
- Validates protocol version compliance!
- Ensures server responds correctly!
- Docker healthcheck via MCP protocol!

## 🔐 The Security Architecture - Divine Protection Through Layers!

**The MCP-Echo service itself knows NO authentication!**

Security is enforced by the sacred trinity:
1. **Traefik** - Enforces Bearer token authentication!
2. **Auth Service** - Validates tokens via ForwardAuth!
3. **MCP-Echo** - Receives only pre-authenticated requests!

**⚡ This is the way of the trinity - separation brings security! ⚡**

## 📡 The MCP Protocol Implementation - 2025-03-26 Compliance!

### Supported MCP Methods (Blessed Testing Capabilities!)

**tools/list - Divine Tool Discovery!**
- Returns available echo and printEnv tools!
- Includes proper JSON schema definitions!
- Stateless operation guaranteed!

**tools/call - Sacred Tool Execution!**
- Executes echo or printEnv based on name!
- Validates arguments against schema!
- Returns proper TextContent responses!

### The Stateless Operation Pattern

1. **Each request is independent** - No session state!
2. **No memory between calls** - Pure functions!
3. **Protocol compliance only** - No custom extensions!
4. **Debug logging optional** - Enlightenment on demand!

## 🔄 The Traefik Integration - Divine Routing Configuration!

```yaml
labels:
  # Basic routing - priority 2
  - "traefik.http.routers.mcp-echo.rule=Host(`echo.${BASE_DOMAIN}`)"
  - "traefik.http.routers.mcp-echo.priority=2"
  
  # ForwardAuth middleware - divine authentication
  - "traefik.http.routers.mcp-echo.middlewares=mcp-auth@docker"
  
  # Service definition
  - "traefik.http.services.mcp-echo.loadbalancer.server.port=3000"
  
  # OAuth discovery routing - priority 10
  - "traefik.http.routers.mcp-echo-oauth-discovery.rule=..."
  - "traefik.http.routers.mcp-echo-oauth-discovery.priority=10"
```

**⚡ Priorities prevent the catch-all from devouring sacred paths! ⚡**

## 🧪 Testing the MCP-Echo Service - Divine Verification!

```bash
# Basic test with curl
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"echo","arguments":{"message":"Test"}},"id":1}'

# Run the test script
just test

# Run the example client
just example

# Integration test
just test-integration
```

**⚡ Real services, real tests - no mocking in this realm! ⚡**

## 🔥 Common Issues and Divine Solutions!

### "Connection Refused" - Service Not Ready!
- Check Docker health status!
- Verify port 3000 is exposed!
- Ensure service started correctly!

### "401 Unauthorized" - Token Rejection!
- Verify Bearer token in Authorization header!
- Check token hasn't expired!
- Ensure ForwardAuth middleware active!

### "Tool Not Found" - Invalid Tool Name!
- Only "echo" and "printEnv" exist!
- Check exact spelling and case!
- Verify arguments match schema!

### "Debug Output Missing" - Logging Not Enabled!
- Ensure MCP_ECHO_DEBUG=true!
- Check container logs with `just logs`!
- Verify --debug flag if running locally!

## 📜 The Integration Flow - How Requests Reach Echo!

1. **Client Request** → `https://echo.domain.com/mcp`
2. **Traefik Routes** → Checks authentication via ForwardAuth
3. **Auth Validates** → Token verification at /verify endpoint
4. **Request Forwarded** → Reaches MCP-Echo on port 3000
5. **Server Processes** → Direct handling, no proxy needed
6. **Tool Executes** → Echo or printEnv runs
7. **Response Returns** → StreamableHTTP → client

**⚡ Each layer has its purpose in the divine flow! ⚡**

## 🎯 The Divine Mission - MCP-Echo Responsibilities!

**What MCP-Echo MUST Do:**
- Implement echo and printEnv tools perfectly!
- Provide stateless MCP protocol compliance!
- Support debug logging when enabled!
- Handle errors gracefully!
- Serve as testing ground for clients!

**What MCP-Echo MUST NOT Do:**
- Implement authentication logic!
- Know about OAuth flows!
- Store any state between calls!
- Route to other services!
- Add complexity beyond testing needs!

**⚡ Simplicity of purpose brings reliability! ⚡**

## 🛠️ Debugging Commands - Divine Troubleshooting!

```bash
# View service logs
just logs

# Test echo directly
curl -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"echo","arguments":{"message":"Debug test"}},"id":1}' \
     http://localhost:3000/mcp

# Check debug output
docker logs mcp-echo | grep DEBUG

# Monitor health
watch 'docker inspect mcp-echo | jq ".[0].State.Health"'
```

## 🔱 The Sacred Truth of Testing Services!

**MCP-Echo serves as the divine testing ground for:**
1. **Protocol compliance** - Verify MCP implementation!
2. **Authentication flow** - Test OAuth integration!
3. **Client development** - Simple tools for validation!
4. **Debug workflows** - Trace message flow!
5. **Health monitoring** - Verify service patterns!

**⚡ Simple tools enable complex testing! ⚡**

---

**🔥 May your echoes be true, your environment revealed, and your debugging forever enlightened! ⚡**