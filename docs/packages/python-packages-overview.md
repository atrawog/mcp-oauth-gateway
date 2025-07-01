# Python Packages in MCP OAuth Gateway

This document provides a comprehensive overview of all Python packages in the MCP OAuth Gateway, based on actual analysis of their source code, dependencies, and implementation.

## Package Summary Table

| Package | Version | Purpose | Key Dependencies |
|---------|---------|---------|------------------|
| mcp-oauth-dynamicclient | 0.2.0 | OAuth 2.1 server with RFC 7591/7592 compliance | FastAPI, Authlib, Redis |
| mcp-streamablehttp-client | 0.1.0 | Bridge client converting stdio ↔ StreamableHTTP | httpx, mcp, authlib |
| mcp-streamablehttp-proxy | 0.2.0 | Generic stdio-to-HTTP proxy for MCP servers | FastAPI, uvicorn, httpx |
| mcp-fetch-streamablehttp-server | 0.1.0 | Native MCP fetch server with HTTP transport | mcp, FastAPI, httpx |
| mcp-echo-streamablehttp-server-stateful | 0.2.0 | Stateful echo server with session management | mcp, uvicorn, psutil |
| mcp-echo-streamablehttp-server-stateless | 0.2.0 | Stateless echo server for protocol debugging | mcp, uvicorn, psutil |

## Core Infrastructure Packages

### mcp-oauth-dynamicclient

**Purpose**: Production-ready OAuth 2.1 authorization server with dynamic client registration support.

**Key Features**:
- OAuth 2.1 compliant with mandatory PKCE (S256 only)
- RFC 7591 dynamic client registration
- RFC 7592 client management protocol
- GitHub OAuth integration for user authentication
- JWT token management (RS256 and HS256)
- Redis-based token storage
- ForwardAuth compatible for Traefik integration

**Architecture**:
- FastAPI-based async server
- Authlib for OAuth implementation
- Redis for state management
- Modular route structure

**Key Components**:
- `server.py` - FastAPI application factory
- `routes.py` - OAuth endpoint implementations
- `rfc7592.py` - Client management endpoints
- `auth_authlib.py` - OAuth server configuration
- `models.py` - Pydantic models for requests/responses
- `keys.py` - JWT key management

**CLI Entry Point**: `mcp-oauth-server`

### mcp-streamablehttp-proxy

**Purpose**: Universal bridge that converts any stdio-based MCP server to StreamableHTTP endpoints.

**Key Features**:
- Works with any stdio MCP server
- Session management with isolated subprocesses
- Configurable timeouts and ports
- Full MCP protocol lifecycle support
- Async I/O for concurrent requests

**Architecture**:
- Spawns MCP server as subprocess
- Translates between HTTP and stdio protocols
- Session-based isolation
- Background cleanup tasks

**Key Components**:
- `proxy.py` - Main proxy implementation
- `server.py` - Uvicorn server runner
- `cli.py` - Command-line interface

**CLI Usage**:
```bash
mcp-streamablehttp-proxy python -m mcp_server_fetch
mcp-streamablehttp-proxy /usr/local/bin/mcp-server-filesystem --root /data
mcp-streamablehttp-proxy npx @modelcontextprotocol/server-memory
```

### mcp-streamablehttp-client

**Purpose**: Bridge client enabling local MCP clients (like Claude Desktop) to connect to OAuth-protected StreamableHTTP servers.

**Key Features**:
- OAuth 2.0 authentication with automatic token management
- RFC 7591 dynamic registration support
- RFC 7592 client management
- Protocol bridging (stdio ↔ StreamableHTTP)
- Smart command parsing
- Claude Desktop integration

**Architecture**:
- Acts as transparent proxy
- Handles OAuth flows automatically
- Stores credentials in .env
- Async HTTP client for server communication

**Key Components**:
- `proxy.py` - Main proxy implementation
- `oauth.py` - OAuth client implementation
- `config.py` - Settings management
- `cli.py` - Rich CLI with multiple commands

**CLI Features**:
- Token management (`--token`)
- Tool execution (`-c "tool_name args"`)
- Client management (`--get-client-info`, `--update-client`, `--delete-client`)
- MCP operations (`--list-tools`, `--list-resources`, `--list-prompts`)

## MCP Service Packages

### mcp-fetch-streamablehttp-server

**Purpose**: Native Python implementation of MCP fetch server with StreamableHTTP transport.

**Key Features**:
- Direct MCP protocol implementation (no stdio bridging)
- Secure URL fetching with SSRF protection
- Size limits and robots.txt compliance
- Stateless operation for horizontal scaling
- Production-ready with health checks

**Architecture**:
- FastAPI-based server
- Native StreamableHTTP implementation
- Security-first design
- Environment-based configuration

**Fetch Tool Security**:
- Blocks localhost and private networks
- Cloud metadata service protection
- Response size limits (100KB default)
- Scheme restrictions (http/https only)
- Redirect limits (5 max)

### mcp-echo-streamablehttp-server-stateful

**Purpose**: Stateful diagnostic echo server with session management and 11 debug tools.

**Key Features**:
- Persistent session management
- Message queuing per session
- Stateful tools (e.g., replayLastEcho)
- Background session cleanup
- Comprehensive diagnostics

**11 Debug Tools**:
1. `echo` - Echo with session context
2. `replayLastEcho` - Replay last echo (stateful!)
3. `printHeader` - Display HTTP headers
4. `bearerDecode` - Decode JWT tokens
5. `authContext` - OAuth context analysis
6. `requestTiming` - Performance metrics
7. `corsAnalysis` - CORS configuration
8. `environmentDump` - Sanitized env vars
9. `healthProbe` - Deep health check
10. `sessionInfo` - Session statistics
11. `whoIStheGOAT` - AI excellence analyzer

**Session Features**:
- UUID-based tracking
- FIFO message queues (max 100)
- Automatic expiration
- Per-session state storage

### mcp-echo-streamablehttp-server-stateless

**Purpose**: Stateless diagnostic echo server for protocol debugging and authentication testing.

**Key Features**:
- No session persistence
- 9 diagnostic tools
- Thread-safe with contextvars
- Designed for debugging OAuth flows
- Minimal dependencies

**9 Debug Tools**:
1. `echo` - Simple message echo
2. `printHeader` - HTTP header analysis
3. `bearerDecode` - JWT debugging
4. `authContext` - Auth context display
5. `requestTiming` - Request metrics
6. `corsAnalysis` - CORS headers
7. `environmentDump` - Config display
8. `healthProbe` - System health
9. `whoIStheGOAT` - Easter egg

**Use Cases**:
- Protocol validation
- Authentication debugging
- Integration testing
- CORS troubleshooting

## Package Relationships

### Architectural Layers

1. **Authentication Layer**
   - `mcp-oauth-dynamicclient` provides OAuth services
   - All other packages rely on this for authentication

2. **Protocol Bridge Layer**
   - `mcp-streamablehttp-proxy` wraps stdio servers
   - `mcp-streamablehttp-client` bridges for stdio clients

3. **Native Implementation Layer**
   - `mcp-fetch-streamablehttp-server` (native HTTP)
   - `mcp-echo-streamablehttp-server-*` (native HTTP)

### Integration Patterns

1. **Proxy Pattern** (using mcp-streamablehttp-proxy):
   ```
   Official MCP Server → Proxy → HTTP Endpoint → OAuth Gateway → Client
   ```

2. **Native Pattern** (direct implementation):
   ```
   Native HTTP Server → OAuth Gateway → Client
   ```

3. **Client Bridge Pattern** (using mcp-streamablehttp-client):
   ```
   Claude Desktop → Client Bridge → OAuth Gateway → MCP Service
   ```

## Common Implementation Details

### Shared Patterns

1. **Configuration**: All packages use environment variables
2. **Logging**: Consistent logging with optional file output
3. **Health Checks**: Protocol-based validation
4. **Error Handling**: Proper HTTP status codes and JSON-RPC errors
5. **Docker Support**: All packages include Dockerfile examples

### Protocol Compliance

- All packages support MCP protocol versions
- Default to 2025-06-18 with fallback support
- Proper initialize/initialized lifecycle
- JSON-RPC 2.0 message handling

### Security Considerations

- No authentication code in MCP services (handled by Traefik)
- Input validation on all endpoints
- SSRF protection where applicable
- Token validation without storage in services

## Testing Philosophy

All packages follow the "no mocks" testing approach:
- Real service integration tests
- Protocol compliance validation
- End-to-end OAuth flow testing
- Performance and load testing

## Deployment Considerations

1. **Docker-first**: All packages designed for container deployment
2. **Traefik Integration**: Consistent labeling patterns
3. **Health Monitoring**: Built-in health check endpoints
4. **Horizontal Scaling**: Stateless designs where possible
5. **Resource Management**: Proper cleanup and timeout handling
