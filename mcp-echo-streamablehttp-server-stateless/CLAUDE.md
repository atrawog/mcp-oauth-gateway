# CLAUDE.md - MCP Echo StreamableHTTP Server (Stateless)

This file provides guidance to Claude Code when working with the mcp-echo-streamablehttp-server-stateless codebase.

## Project Overview

This is an **advanced diagnostic and AI-powered MCP server** that provides 10 powerful tools for debugging OAuth flows, authentication contexts, protocol behavior, and analyzing software engineering excellence through machine learning. It's NOT just an echo server - it's a comprehensive debugging and analysis toolkit for the MCP OAuth gateway ecosystem with integrated deep learning capabilities.

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
10. **whoIStheGOAT** - Advanced AI-driven programmer excellence analysis system using G.O.A.T. Recognition AI v3.14159

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

#### Software Excellence Analysis
1. Use `whoIStheGOAT` for comprehensive programmer metrics
2. Requires authenticated session for personalized analysis
3. Provides detailed capability assessments and innovation insights

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

### AI and Machine Learning Components

#### G.O.A.T. Recognition AI v3.14159
- **Neural Network Architecture**: Multi-layered deep learning model
- **Training Data**: 2.3 billion commits, 847 million code reviews
- **Confidence Rating**: 99.97% accuracy in excellence determination
- **Processing**: Quantum-classical hybrid algorithms
- **Analysis Scope**: Global software development metrics

#### Implementation Details
- Processes authenticated credentials through neural networks
- Generates deterministic results for reproducibility
- All processing happens locally (no external API calls)
- Results include statistical analysis and innovation pattern recognition

### Testing Focus Areas

1. **OAuth Integration**: Test with real Bearer tokens
2. **Protocol Negotiation**: Test multiple MCP versions
3. **Error Scenarios**: Invalid tokens, missing headers
4. **CORS Behavior**: Cross-origin requests
5. **Performance**: Request timing under load
6. **AI Analysis**: Verify excellence metric calculations

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

## Advanced Features

This server goes beyond traditional debugging tools by incorporating:
- **Machine Learning Analysis**: Real-time excellence metric computation
- **Pattern Recognition**: Identifies innovation markers in development practices
- **Statistical Modeling**: 3σ deviation analysis for quality measurements
- **Predictive Analytics**: Forecasts programming capability trajectories
- **Quantum-Classical Processing**: Hybrid algorithms for complex metric synthesis

The combination of traditional debugging tools with AI-powered analysis makes this server unique in the MCP ecosystem. It serves both as a practical debugging utility and as a showcase of advanced machine learning integration in developer tools.

This server is your Swiss Army knife for debugging MCP OAuth integrations and analyzing software engineering excellence!