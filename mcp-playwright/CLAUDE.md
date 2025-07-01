# MCP Playwright Service - The Divine Browser Automation Scripture

**🎭 Behold! The sacred MCP Playwright service - browser automation blessed by the divine proxy pattern! ⚡**

## Divine Service Architecture

**🔥 This service channels the official @playwright/mcp server through mcp-streamablehttp-proxy glory! ⚡**

### The Sacred Implementation Pattern

**📜 Pattern Classification: The Blessed Proxy Pattern**
- Wraps the official `@playwright/mcp@latest` from npm registry!
- Uses `mcp-streamablehttp-proxy` to bridge stdio → StreamableHTTP!
- Subprocess management with divine process isolation!
- Full MCP protocol compliance through proxy transcendence!

### The Holy Service Components

**🏗️ Divine Dockerfile Architecture:**
```dockerfile
FROM python:3.12-alpine          # The blessed Alpine foundation!
RUN npm install -g @playwright/mcp@latest  # Official server installation!
RUN pip install /tmp/mcp-streamablehttp-proxy  # Sacred proxy blessing!
CMD ["/app/start.sh"]           # Proxy wraps the official server!
```

**⚡ The Sacred Proxy Invocation:**
```bash
mcp-streamablehttp-proxy npx @playwright/mcp@latest --headless --browser=chromium
```

### The Divine Service Configuration

**🚀 Environment Variables:**
- `MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION:-2025-06-18}` - Protocol covenant version!
- `PLAYWRIGHT_BROWSERS_PATH=/ms-playwright` - Sacred browser installation path!
- `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` - Prevent redundant downloads!
- `LOG_FILE=/logs/server.log` - Divine logging destination!
- `MCP_CORS_ORIGINS=*` - CORS blessing for all origins!

**📊 Health Check Implementation:**
```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"'$$MCP_PROTOCOL_VERSION'\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
    | grep -q '\"protocolVersion\":\"'$$MCP_PROTOCOL_VERSION'\"'"]
```

**⚡ This performs a blessed MCP initialization handshake to verify protocol readiness! ⚡**

### The Sacred Traefik Routing Configuration

**🚦 Divine routing priorities enforced with holy fury:**
- **Priority 10** - OAuth discovery route (highest sanctity!)
- **Priority 4** - CORS preflight OPTIONS (divine browser protection!)
- **Priority 2** - Main MCP route with authentication blessing!
- **Priority 1** - Catch-all route (lowest priority guardian!)

**🔐 Authentication Flow:**
- All requests to `/mcp` require Bearer token authentication!
- OAuth discovery at `/.well-known/oauth-authorization-server` remains public!
- ForwardAuth middleware validates tokens through auth service blessing!

### The Divine Browser Capabilities

**🌐 Browsers blessed by this service:**
- **Chromium** - The primary blessed browser (--browser=chromium)!
- **Firefox** - Installed and ready for divine automation!
- **Headless mode** - Default blessed configuration (--headless)!

**📦 System dependencies for browser glory:**
- `chromium` and `chromium-chromedriver` - For Chromium automation!
- `firefox` - For Firefox automation capability!
- `ttf-liberation` and `font-noto-emoji` - Sacred fonts for rendering!

### The Sacred Service Access Pattern

**🔗 Endpoint Structure:**
- **Base URL**: `https://playwright.${BASE_DOMAIN}`
- **MCP Endpoint**: `https://playwright.${BASE_DOMAIN}/mcp`
- **OAuth Discovery**: `https://playwright.${BASE_DOMAIN}/.well-known/oauth-authorization-server`

**🎯 Service Integration:**
```bash
# Enable via environment variable
MCP_PLAYWRIGHT_ENABLED=true

# Access URL automatically constructed
playwright.${BASE_DOMAIN}
```

### The Divine Logging Configuration

**📜 Logs flow to the sacred directory:**
- `../logs/mcp-playwright/server.log` - All service logs centralized!
- Structured logging through mcp-streamablehttp-proxy wrapper!
- Subprocess stdio captured and blessed with context!

### The Sacred Network Architecture

**🌐 Network topology:**
- Connected to `public` network (external: true)!
- Exposed on port 3000 internally to the Docker network!
- Accessed externally only through Traefik's divine routing!

## The Divine Playwright MCP Protocol Features

**⚡ This service inherits all capabilities from the official @playwright/mcp server! ⚡**

The proxy pattern ensures:
- ✅ Full protocol compliance through official implementation!
- ✅ All Playwright browser automation features preserved!
- ✅ Session management through mcp-streamablehttp-proxy!
- ✅ Error handling and graceful degradation!

**🔥 Remember: This service follows the sacred proxy pattern - we wrap but never modify the official server! ⚡**

## Integration with the Sacred Gateway

**☯️ This service integrates with the MCP OAuth Gateway through:**
1. **Divine Traefik routing** - All requests flow through the sacred proxy!
2. **OAuth bearer tokens** - Authentication handled by ForwardAuth middleware!
3. **Health checks** - Protocol-compliant initialization verifies readiness!
4. **Centralized logging** - All logs flow to ./logs/mcp-playwright/!

**⚡ The service knows nothing of OAuth - that's Traefik's divine responsibility per the Trinity separation! ⚡**
