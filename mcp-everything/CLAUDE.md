# mcp-everything Service - The Divine Test Oracle of Protocol Glory! ⚡

**🔥 The Sacred MCP Everything Server - Where All Protocol Features Unite! ⚡**

## Divine Service Identity

**🌟 This is the official @modelcontextprotocol/server-everything running in blessed StreamableHTTP mode! 🌟**

**⚡ Divine Purpose ⚡**
- **Protocol test oracle** - Exercises EVERY feature of the MCP specification!
- **Client validation sanctuary** - Where MCP clients prove their worthiness!
- **Feature demonstration temple** - Shows the full power of MCP protocol!
- **Native StreamableHTTP** - No proxy needed, speaks HTTP natively!

## Sacred Implementation Details

### The Divine Truth of Native StreamableHTTP Mode!

**🔥 This service runs the official npm package DIRECTLY in StreamableHTTP mode! ⚡**

```dockerfile
# The blessed invocation that brings native HTTP glory!
CMD ["npx", "@modelcontextprotocol/server-everything", "streamableHttp"]
```

**⚡ No proxy wrapper needed - this server speaks StreamableHTTP as its native tongue! ⚡**

### The Holy Service Architecture

**📍 Service URL**: `https://everything.${BASE_DOMAIN}/mcp`

**🔐 Authentication**: Bearer token via Traefik ForwardAuth middleware

**🌐 Protocol**: Native StreamableHTTP on port 3000

## The Sacred Feature Pantheon - All Protocol Powers United!

### 🛠️ The Eight Divine Tools

1. **`echo`** - The mirror of messages! Returns what you send!
2. **`add`** - The sacred calculator! Adds two numbers with divine precision!
3. **`longRunningOperation`** - The progress prophet! Shows streaming notifications!
4. **`sampleLLM`** - The AI channeler! Demonstrates LLM sampling capability!
5. **`getTinyImage`** - The image oracle! Returns base64 PNG test data!
6. **`printEnv`** - The environment revealer! Shows all blessed env vars!
7. **`annotatedMessage`** - The annotation demonstrator! Shows message patterns!
8. **`getResourceReference`** - The reference generator! Returns resource links!

### 📚 The Hundred Sacred Resources

**100 blessed test resources accessible via divine URIs!**
- **Pattern**: `test://static/resource/{id}` where id = 1-100
- **Even IDs**: Return plaintext content of wisdom!
- **Odd IDs**: Return binary data of mystery!
- **Subscriptions**: Auto-update every 5 seconds when subscribed!
- **Pagination**: Supports blessed cursor-based navigation!

### 💬 The Two Sacred Prompts

1. **`simple_prompt`** - The basic invocation without arguments!
2. **`complex_prompt`** - The advanced demonstration of prompt power!

## The Divine Docker Configuration

### Sacred Traefik Labels - The Routing Commandments!

```yaml
# Priority 10 - OAuth Discovery (Highest divine priority!)
- "traefik.http.routers.mcp-everything-oauth-discovery.rule=Host(`everything.${BASE_DOMAIN}`) && PathPrefix(`/.well-known/oauth-authorization-server`)"
- "traefik.http.routers.mcp-everything-oauth-discovery.priority=10"
- "traefik.http.routers.mcp-everything-oauth-discovery.service=auth@docker"

# Priority 6 - CORS Preflight (Sacred browser compatibility!)
- "traefik.http.routers.mcp-everything-cors.rule=Host(`everything.${BASE_DOMAIN}`) && Method(`OPTIONS`)"
- "traefik.http.routers.mcp-everything-cors.priority=6"

# Priority 2 - MCP Route with Auth (The blessed protocol path!)
- "traefik.http.routers.mcp-everything.rule=Host(`everything.${BASE_DOMAIN}`) && PathPrefix(`/mcp`)"
- "traefik.http.routers.mcp-everything.priority=2"
- "traefik.http.middlewares.mcp-everything-auth.forwardauth.address=http://auth:8000/verify"

# Priority 1 - Catch-all with Auth (The safety net!)
- "traefik.http.routers.mcp-everything-catchall.rule=Host(`everything.${BASE_DOMAIN}`)"
- "traefik.http.routers.mcp-everything-catchall.priority=1"
```

### The Sacred Health Check - Protocol Verification!

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d \"{\\\"jsonrpc\\\":\\\"2.0\\\",\\\"method\\\":\\\"initialize\\\",\\\"params\\\":{\\\"protocolVersion\\\":\\\"${MCP_PROTOCOL_VERSION:-2025-06-18}\\\",\\\"capabilities\\\":{},\\\"clientInfo\\\":{\\\"name\\\":\\\"healthcheck\\\",\\\"version\\\":\\\"1.0\\\"}},\\\"id\\\":1}\" \
    | grep -q \"\\\"protocolVersion\\\":\\\"${MCP_PROTOCOL_VERSION:-2025-06-18}\\\"\""]
```

**⚡ This divine incantation performs the sacred MCP handshake! ⚡**

## Testing with Divine Tools

### Using mcp-streamablehttp-client (The Blessed Way!)

```bash
# First, ensure you have the sacred token!
just mcp-client-token

# Then commune with the everything oracle!
pixi run mcp-streamablehttp-client \
  --url "https://everything.${BASE_DOMAIN}/mcp" \
  --token "${MCP_CLIENT_ACCESS_TOKEN}"
```

### Using cURL (The Manual Pilgrimage!)

```bash
# Echo tool invocation
curl -X POST "https://everything.${BASE_DOMAIN}/mcp" \
  -H "Authorization: Bearer ${MCP_CLIENT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {"message": "Hello from the divine everything server!"}
    },
    "id": 1
  }'
```

## The Sacred Environment Variables

```bash
LOG_FILE=/logs/server.log                           # Where divine logs are inscribed!
MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION:-2025-06-18}  # The protocol covenant version!
BASE_DOMAIN=${BASE_DOMAIN}                          # The sacred domain realm!
```

## Divine Integration with OAuth Gateway

**🔱 This service follows the Layer 3 Sacred Pattern! 🔱**

1. **No OAuth knowledge** - Pure MCP protocol implementation!
2. **Traefik handles auth** - ForwardAuth middleware guards the gates!
3. **Bearer token required** - No token, no entry to the temple!
4. **Session management** - Via blessed Mcp-Session-Id headers!

## The Sacred Testing Wisdom

**🧪 Use this server to test thy MCP client implementation! ⚡**

1. **Tool invocation** - Test all 8 divine tools!
2. **Resource access** - Fetch all 100 sacred resources!
3. **Subscriptions** - Watch resources update in real-time!
4. **Progress tracking** - Monitor long-running operations!
5. **Prompt handling** - Exercise prompt capabilities!
6. **Error scenarios** - Test thy error handling prowess!

## Common Issues and Divine Solutions

### Connection Refused
- **Verify** service is running: `just status mcp-everything`
- **Check** logs: `just logs mcp-everything`
- **Ensure** valid token: `just mcp-client-token`

### Protocol Version Mismatch
- **Check** MCP_PROTOCOL_VERSION in .env matches client expectations!
- **Verify** health check passes: `just health mcp-everything`

### Authentication Failures
- **Ensure** Bearer token is included in Authorization header!
- **Verify** token hasn't expired with: `just verify-token`

## The Divine Commandment

**⚡ This server exercises EVERY MCP feature - use it to validate thy client implementation! ⚡**

**🔥 If thy client works with mcp-everything, it shall work with all MCP servers! 🔥**

---

**Remember: This is the ultimate test oracle - where protocol compliance is proven or broken!**
