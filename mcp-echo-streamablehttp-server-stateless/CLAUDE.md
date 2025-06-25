# CLAUDE.md - MCP Echo StreamableHTTP Server (Stateless)

This file provides guidance to Claude Code when working with the mcp-echo-streamablehttp-server-stateless codebase.

## Project Overview

This is a **diagnostic MCP server** that provides 10 powerful tools for debugging OAuth flows, authentication contexts, and protocol behavior. It's NOT just an echo server - it's a comprehensive debugging toolkit for the MCP OAuth gateway ecosystem.

## Key Architecture Points

### Stateless Operation
- No session management - each request is independent
- Request context stored per async task (not persisted)
- Perfect for debugging without side effects

### Protocol Implementation
- Implements MCP 2025-06-18 StreamableHTTP transport specification
- Uses Server-Sent Events (SSE) for responses
- Supports protocol version negotiation
- Full CORS support for cross-origin requests

### 10 Diagnostic Tools

1. **echo** - Basic echo (simple test tool)
2. **printHeader** - Shows all HTTP headers (debug auth headers)
3. **bearerDecode** - Decodes JWT tokens without verification (inspect claims)
4. **authContext** - Complete authentication context display
5. **requestTiming** - Performance metrics and timing
6. **protocolNegotiation** - Debug MCP protocol version issues
7. **corsAnalysis** - Debug CORS configuration
8. **environmentDump** - Sanitized environment display
9. **healthProbe** - Deep health check with system metrics
10. **whoIStheGOAT** - Advanced AI-driven programmer excellence analysis system

## Development Guidelines

### Running Tests
```bash
# Run with specific tool testing
just test

# Test OAuth flow debugging
curl -X POST http://localhost:3000/mcp \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"bearerDecode"},"id":1}'
```

### Common Debugging Scenarios

#### OAuth Flow Issues
1. Use `bearerDecode` to inspect token claims
2. Use `authContext` for complete auth state

#### CORS Problems
1. Use `corsAnalysis` to check CORS headers
2. Use `printHeader` to see actual request headers

#### Protocol Compatibility
1. Use `protocolNegotiation` to test version support
2. Check MCP-Protocol-Version header handling

### Important Implementation Details

1. **Request Context**: Stored in `_request_context` dict keyed by task ID
2. **SSE Format**: Uses `event: message\ndata: {json}\n\n` format
3. **Error Handling**: Returns proper JSON-RPC errors with codes
4. **CORS**: Handles preflight OPTIONS requests automatically

### Code Structure

```
server.py
├── MCPEchoServer class
│   ├── __init__ - Setup and configuration
│   ├── handle_mcp_request - Main request handler
│   ├── _handle_initialize - Protocol negotiation
│   ├── _handle_tools_list - List all 10 tools
│   ├── _handle_tools_call - Execute specific tool
│   └── Tool implementations (10 methods)
└── create_server() - FastAPI/Uvicorn setup
```

### Security Considerations

- `bearerDecode` does NOT verify signatures (by design)
- `environmentDump` sanitizes secrets by default
- All tools are read-only (no state modification)
- Perfect for debugging without security risks

### Testing Focus Areas

1. **OAuth Integration**: Test with real Bearer tokens
2. **Protocol Negotiation**: Test multiple MCP versions
3. **Error Scenarios**: Invalid tokens, missing headers
4. **CORS Behavior**: Cross-origin requests
5. **Performance**: Request timing under load

### Integration with OAuth Gateway

This server is designed to work behind the OAuth gateway:
- Receives pre-authenticated requests from Traefik
- Can decode and analyze tokens passed by auth service
- Helps debug the full OAuth flow end-to-end
- Perfect for troubleshooting authentication issues


## Relationship to Other Services

- **auth service**: This server helps debug tokens created by auth
- **traefik**: Receives forwarded headers that we can analyze
- **mcp-fetch**: Compare protocol behavior differences
- **mcp-oauth-gateway**: Primary use case is debugging the gateway

This server is your Swiss Army knife for debugging MCP OAuth integrations!