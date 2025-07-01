# The Divine MCP StreamableHTTP Client Commandments

**🔥 Behold! The Sacred Bridge Between stdio and StreamableHTTP! ⚡**

**⚡ This is the blessed client that connects local MCP tools to OAuth-protected servers! ⚡**

## The Sacred Architecture - The Divine Bridge Pattern!

**🌉 The Holy Trinity of Protocol Bridging! 🌉**

```
┌─────────────────────────────────────────────────────────────┐
│  Local MCP Client (Claude Desktop) - The stdio Supplicant   │
│  • Speaks only stdio JSON-RPC - the ancient tongue!         │
│  • Knows nothing of HTTP or OAuth - blessed ignorance!      │
│  • Expects local process communication - simple and pure!   │
└─────────────────────────────────────────────────────────────┘
                              ↓ stdio
┌─────────────────────────────────────────────────────────────┐
│  mcp-streamablehttp-client - The Divine Protocol Bridge     │
│  • Converts stdio ↔ StreamableHTTP with blessed magic!      │
│  • Handles OAuth authentication transparently!               │
│  • Maintains session state across protocol boundaries!      │
│  • The only component that speaks both tongues!             │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTP + OAuth
┌─────────────────────────────────────────────────────────────┐
│  Remote MCP Server - The StreamableHTTP Oracle              │
│  • Requires OAuth Bearer tokens for divine access!          │
│  • Speaks StreamableHTTP protocol over sacred HTTPS!        │
│  • Protected by authentication middleware glory!            │
└─────────────────────────────────────────────────────────────┘
```

**⚡ Without this bridge, local clients cannot reach OAuth-protected servers! ⚡**

## The Ten Sacred Commandments of MCP Client Implementation

### 1. OAuth 2.0 + RFC 7591/7592 Full Compliance or Authentication Chaos!

**🔐 The client implements the complete OAuth divine trinity! ⚡**

**The Sacred OAuth Features Implemented:**
- **Dynamic Client Registration (RFC 7591)** - Automatic client birth through `/register`!
- **Client Management (RFC 7592)** - Full CRUD operations on thy registration!
- **Multiple Auth Flows** - Device flow (blessed) and Authorization Code (with PKCE)!
- **Token Management** - Automatic refresh before the hour of expiration!
- **Discovery Support** - Finds OAuth endpoints through `.well-known` pilgrimage!

**⚡ No manual client registration needed - the divine automation handles all! ⚡**

### 2. Environment Variables Only - No Config Files Ever!

**⚙️ All configuration flows through .env - this is the eternal law! ⚡**

**The Sacred Environment Variables:**
```bash
MCP_SERVER_URL=https://mcp-fetch.yourdomain.com  # Target server URL
MCP_CLIENT_ID=dyn_xxx...                         # OAuth client ID
MCP_CLIENT_SECRET=xxx...                         # OAuth client secret
MCP_CLIENT_ACCESS_TOKEN=xxx...                   # Current access token
MCP_CLIENT_REFRESH_TOKEN=xxx...                  # Refresh token
MCP_CLIENT_REGISTRATION_TOKEN=reg_xxx...         # RFC 7592 management token
MCP_CLIENT_REGISTRATION_URI=https://...          # RFC 7592 management endpoint
```

**⚡ The `--token` command blesses thy .env with all credentials automatically! ⚡**

### 3. Protocol Bridge Pattern - The Divine Architecture!

**🌉 stdio in, StreamableHTTP out - the eternal transformation! ⚡**

**The Sacred Bridge Responsibilities:**
1. **Protocol Conversion** - JSON-RPC over stdio ↔ JSON-RPC over HTTP!
2. **Authentication Injection** - Bearer tokens added to every request!
3. **Session Management** - Mcp-Session-Id tracked across boundaries!
4. **Error Translation** - HTTP errors become JSON-RPC errors!
5. **SSE Parsing** - Server-Sent Events transformed to stdio responses!

**⚡ The bridge is transparent - clients need not know of its divine work! ⚡**

### 4. Smart Command Parsing - The Divine Intelligence!

**🧠 Multiple input formats supported with blessed flexibility! ⚡**

**The Sacred Parsing Patterns:**
```bash
# JSON format - for complex arguments
mcp-streamablehttp-client -c 'tool {"key": "value", "nested": {"foo": "bar"}}'

# Key=value format - for simple arguments
mcp-streamablehttp-client -c 'tool key1=value1 key2=value2'

# Smart detection - URL for fetch, path for files
mcp-streamablehttp-client -c 'fetch https://example.com'
mcp-streamablehttp-client -c 'read_file /path/to/file.txt'

# Positional arguments - for single-parameter tools
mcp-streamablehttp-client -c 'echo "Hello World"'
```

**⚡ The parser divines thy intent through blessed heuristics! ⚡**

### 5. Token Lifecycle Management - The Sacred Token Dance!

**🔄 Tokens are born, live, and are reborn through divine automation! ⚡**

**The Token Lifecycle Prophecy:**
1. **Birth** - `--token` initiates OAuth flow and receives tokens!
2. **Life** - Tokens used automatically on every request!
3. **Renewal** - Refresh triggered before expiration automatically!
4. **Persistence** - All tokens saved to .env for eternal access!
5. **Death** - `--reset-auth` clears all credentials for rebirth!

**⚡ Never manually manage tokens - the divine automation handles all! ⚡**

### 6. Session State Management - The Divine Continuity!

**🎯 Sessions persist across the stdio boundary! ⚡**

**The Sacred Session Laws:**
- **Automatic Initialization** - First request triggers `initialize` automatically!
- **Session ID Tracking** - `Mcp-Session-Id` preserved across all requests!
- **State Persistence** - Session maintained until explicit termination!
- **Protocol Version Negotiation** - Client and server agree on blessed version!

**⚡ Stateful MCP servers work seamlessly through the bridge! ⚡**

### 7. Error Handling with Divine Grace!

**⚠️ All errors translated to proper JSON-RPC format! ⚡**

**The Sacred Error Translation:**
- **HTTP 401** → JSON-RPC error with OAuth flow trigger!
- **HTTP 403** → JSON-RPC error "Forbidden" message!
- **HTTP 404** → JSON-RPC error "Not Found" message!
- **Network errors** → JSON-RPC error with connection details!
- **OAuth errors** → Clear instructions for authentication!

**⚡ No error shall pass untranslated through the bridge! ⚡**

### 8. CLI Commands - The Divine Interface!

**🖥️ Multiple modes of blessed operation! ⚡**

**The Sacred Command Modes:**
```bash
# Continuous proxy mode (for Claude Desktop)
mcp-streamablehttp-client

# Single command execution
mcp-streamablehttp-client -c "tool_name arguments"

# List available tools/resources/prompts
mcp-streamablehttp-client --list-tools
mcp-streamablehttp-client --list-resources
mcp-streamablehttp-client --list-prompts

# OAuth management
mcp-streamablehttp-client --token      # Setup/refresh tokens
mcp-streamablehttp-client --test-auth  # Verify authentication
mcp-streamablehttp-client --reset-auth # Clear credentials

# RFC 7592 client management
mcp-streamablehttp-client --get-client-info
mcp-streamablehttp-client --update-client "client_name=New Name"
mcp-streamablehttp-client --delete-client

# Raw JSON-RPC (power user mode)
mcp-streamablehttp-client --raw '{"jsonrpc": "2.0", "method": "...", "id": 1}'
```

**⚡ Every mode serves a divine purpose in the bridge ecosystem! ⚡**

### 9. Claude Desktop Integration - The Sacred Configuration!

**🖥️ Direct integration with Claude Desktop through blessed config! ⚡**

**The Sacred claude_desktop_config.json Pattern:**
```json
{
  "mcpServers": {
    "oauth-protected-server": {
      "command": "mcp-streamablehttp-client",
      "env": {
        "MCP_SERVER_URL": "https://mcp-fetch.yourdomain.com"
      }
    }
  }
}
```

**⚡ One bridge process per remote server - divine isolation! ⚡**

### 10. The Divine Just Commands!

**⚡ All operations flow through just - this is the eternal law! ⚡**

```justfile
# Authenticate with OAuth server
auth:
    pixi run mcp-streamablehttp-client --token

# Test authentication
test-auth:
    pixi run mcp-streamablehttp-client --test-auth

# List available tools
list-tools:
    pixi run mcp-streamablehttp-client --list-tools

# Execute a command
exec command:
    pixi run mcp-streamablehttp-client -c "{{command}}"

# Run continuous proxy
proxy:
    pixi run mcp-streamablehttp-client

# Get client info
client-info:
    pixi run mcp-streamablehttp-client --get-client-info

# Run the service container
up:
    docker-compose up -d

# View logs
logs:
    docker-compose logs -f
```

**⚡ Direct command execution is heresy - use just! ⚡**

## The Sacred Implementation Details

### OAuth Discovery Mechanism - The Divine Endpoint Quest!

**🔍 The client seeks OAuth endpoints through multiple blessed paths! ⚡**

**The Discovery Hierarchy:**
1. Try `/.well-known/oauth-authorization-server` on target domain
2. Try `/.well-known/openid-configuration` as fallback
3. Extract auth domain and try well-known paths there
4. Follow the sacred breadcrumbs to enlightenment!

**⚡ No hardcoded endpoints - discovery or death! ⚡**

### Protocol Version Negotiation - The Divine Handshake!

**🤝 Client and server must agree on the blessed protocol version! ⚡**

**The Negotiation Ritual:**
1. Client sends `initialize` with supported versions
2. Server responds with chosen version
3. All subsequent communication uses agreed version
4. Default: 2025-06-18 (the latest blessed version)

**⚡ Version mismatch = communication failure! ⚡**

### Token Security - The Sacred Protection!

**🔒 Tokens are protected with divine security measures! ⚡**

**The Security Commandments:**
- Tokens stored in .env file only (never in code!)
- Access tokens include expiration tracking
- Automatic refresh 5 minutes before expiry
- Registration tokens kept separate (RFC 7592)
- SSL verification enabled by default

**⚡ Compromise a token = immediate `--reset-auth` required! ⚡**

## The Divine Testing Commandments

**🧪 Real servers only - no mocks allowed! ⚡**

**The Testing Requirements:**
- Test against actual OAuth servers
- Test against real MCP endpoints
- Test token expiration scenarios
- Test error conditions with real failures
- Test all CLI commands end-to-end

**⚡ Mock = lies! Real = truth! ⚡**

## The Sacred Error Messages

**📢 Every error guides the user to salvation! ⚡**

**Divine Error Examples:**
- "No credentials found. Run with --token to authenticate"
- "Token expired. Refreshing automatically..."
- "OAuth server not found. Check MCP_SERVER_URL"
- "Authentication failed. Run --reset-auth and try again"

**⚡ Cryptic errors = user suffering! Clear errors = divine guidance! ⚡**

## The Production Deployment Pattern

**🚀 Docker container with blessed isolation! ⚡**

**The Container Prophecy:**
- Runs as non-root user (divine security!)
- Minimal Alpine image (blessed efficiency!)
- Environment variables injected at runtime
- Health checks via authentication test
- Logs to stdout (container best practice!)

**⚡ Deploy with just up - automation is divine! ⚡**

---

**⚡ This is the way of the MCP StreamableHTTP Client! ⚡**
**🔥 Follow these commandments or face protocol chaos! 🔥**
**✨ The bridge brings unity to divided protocols! ✨**
