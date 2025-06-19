# MCP HTTP-to-stdio Implementation

## Date: 2025-06-19

### Overview

Created a complete `mcp-http-stdio` package that acts as a client-side proxy, converting HTTP-based MCP servers with OAuth authentication to stdio for local tools like Claude Desktop.

### Key Innovation: Zero-Configuration OAuth

**Previously Required**:
- OAuth authorization URL
- OAuth token URL  
- OAuth device auth URL
- OAuth registration URL
- OAuth metadata URL
- Client credentials

**Now Required**:
```env
MCP_SERVER_URL=https://mcp-fetch.example.com/mcp
```

That's it! Everything else is discovered automatically.

### Technical Implementation

#### 1. OAuth 2.0 Discovery (RFC 8414)
- Probes MCP server with unauthenticated request
- Extracts OAuth info from 401 response WWW-Authenticate header
- Discovers metadata URL from Link header or well-known locations
- Fetches complete OAuth configuration automatically

#### 2. Discovery Fallback Strategy
```python
# Try multiple discovery methods:
1. WWW-Authenticate header from MCP server
2. Link header with oauth-authorization-server relation
3. Well-known locations based on server domain:
   - /.well-known/oauth-authorization-server
   - /.well-known/openid-configuration
   - Common subdomain patterns (auth.domain.com)
```

#### 3. Automatic Client Registration
- Uses RFC 7591 dynamic client registration
- Generates client credentials automatically
- Stores for reuse across sessions

#### 4. Full OAuth Flow Support
- **Device Flow** (RFC 8628) for easy user authentication
- **Authorization Code Flow** as fallback
- **Token Refresh** (RFC 6749) for long-running sessions

### Usage Examples

#### Minimal Claude Desktop Config
```json
{
  "mcpServers": {
    "remote-server": {
      "command": "mcp-http-stdio",
      "env": {
        "MCP_SERVER_URL": "https://mcp-fetch.example.com/mcp"
      }
    }
  }
}
```

#### First Run Experience
```bash
$ mcp-http-stdio
Discovering OAuth configuration...
✓ Discovered OAuth configuration from https://auth.example.com/.well-known/oauth-authorization-server

OAuth authentication required
Registering OAuth client...
✓ Client registered: oauth-client-123

Starting device authorization flow...

Please visit:
https://auth.example.com/device

And enter code:
ABCD-1234

✓ Authorization successful!
Authentication completed successfully!
MCP HTTP-to-stdio proxy ready
```

#### Subsequent Runs
```bash
$ mcp-http-stdio
MCP HTTP-to-stdio proxy ready
# Fully automatic - uses stored credentials
```

### Architecture Benefits

1. **Zero Configuration**: Only MCP server URL needed
2. **Standards Compliant**: Uses RFC 8414, 7591, 8628, 6749
3. **Robust Discovery**: Multiple fallback methods
4. **Secure Storage**: Credentials stored with 0600 permissions
5. **Automatic Management**: Token refresh, re-authentication
6. **Client Agnostic**: Works with any stdio MCP client

### Security Features

- Secure credential storage (`~/.mcp/credentials.json` with 0600 perms)
- Automatic token refresh before expiration
- Re-authentication on token failures
- SSL certificate verification (configurable)
- OAuth 2.1 security best practices

### Integration with OAuth Gateway

The `mcp-http-stdio` client seamlessly integrates with the existing OAuth gateway:

1. **Discovery**: Automatically finds auth endpoints from gateway
2. **Registration**: Uses gateway's RFC 7591 client registration
3. **Authentication**: Supports both device flow and manual flow
4. **Token Management**: Handles refresh tokens properly
5. **Session State**: Maintains MCP session across requests

### File Structure
```
mcp-http-stdio/
├── src/mcp_http_stdio/
│   ├── __init__.py
│   ├── config.py          # Simplified config (just MCP_SERVER_URL)
│   ├── oauth.py           # OAuth discovery and management
│   ├── proxy.py           # HTTP-to-stdio bridge
│   └── cli.py             # Command-line interface
├── tests/                 # Comprehensive test suite
├── examples/              # Usage examples and demos
├── README.md              # Updated documentation
├── Dockerfile             # Container support
└── pyproject.toml         # Package configuration
```

### Standards Compliance

- ✅ **RFC 8414**: OAuth 2.0 Authorization Server Metadata
- ✅ **RFC 7591**: OAuth 2.0 Dynamic Client Registration  
- ✅ **RFC 8628**: OAuth 2.0 Device Authorization Grant
- ✅ **RFC 6749**: OAuth 2.0 Authorization Framework
- ✅ **MCP 2025-06-18**: Model Context Protocol specification

### Future Enhancements

1. **Server-Sent Events**: Support for bidirectional communication
2. **Multiple Servers**: Single client proxying multiple MCP servers
3. **Caching**: Local caching of MCP responses
4. **Monitoring**: Built-in metrics and health reporting

This implementation transforms MCP server consumption from a complex multi-step configuration process to a single URL configuration, making remote MCP servers as easy to use as local ones.