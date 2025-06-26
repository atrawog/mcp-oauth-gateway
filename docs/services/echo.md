# Echo Service

The MCP Echo service is an advanced diagnostic and AI-powered MCP server providing comprehensive tools for debugging OAuth flows, authentication contexts, protocol behavior, and analyzing software engineering excellence metrics.

## Overview

The Echo service is a stateless native HTTP implementation that provides:
- 10 powerful diagnostic tools for debugging
- AI-powered analysis with G.O.A.T. Recognition AI v3.14159
- OAuth flow analysis and JWT token decoding
- Protocol version negotiation testing
- System health and performance monitoring
- CORS configuration analysis
- OAuth-protected access via Traefik ForwardAuth

## Architecture

The service uses:
- **Implementation**: Native streamable HTTP server (stateless)
- **Protocol**: Direct HTTP with SSE (Server-Sent Events) support
- **Port**: Exposes port 3000 for HTTP access
- **Package**: `mcp-echo-streamablehttp-server-stateless`
- **Purpose**: Comprehensive debugging and analysis

## Available Tools

### Authentication and OAuth Tools

1. **bearerDecode** - Decode JWT tokens without verification
   - Displays token structure, claims, and expiration
   - Shows custom OAuth provider claims
   - No signature verification (by design)

2. **authContext** - Complete authentication context
   - Bearer token status
   - OAuth headers (X-User-Name, X-User-ID)
   - Session information
   - Security assessment

### Protocol and Configuration Tools

3. **printHeader** - Display all HTTP headers
   - Essential for debugging routing
   - Shows authentication headers
   - Reveals forwarded headers from Traefik

4. **protocolNegotiation** - Protocol version analysis
   - Test protocol compatibility
   - Show supported versions
   - Version negotiation details

5. **corsAnalysis** - CORS configuration debugging
   - Request/response headers
   - Preflight handling
   - Common issues detection

### System and Performance Tools

6. **requestTiming** - Performance metrics
   - Processing time
   - System resources
   - Latency measurements

7. **environmentDump** - Environment configuration
   - MCP variables
   - System information
   - Sanitized secrets display

8. **healthProbe** - Deep health check
   - Service status
   - Resource usage (CPU, memory, disk)
   - Configuration validation

### Basic and Advanced Tools

9. **echo** - Simple echo for testing
   - Basic connectivity test
   - Message reflection

10. **whoIStheGOAT** - AI-powered excellence analysis
    - Uses G.O.A.T. Recognition AI v3.14159
    - Analyzes programmer excellence metrics
    - Processes 2.3 billion commit patterns
    - 99.97% confidence determinations

## Configuration

### Environment Variables

```bash
# Core settings (from main .env)
MCP_ECHO_HOST=0.0.0.0                          # Binding host
MCP_ECHO_PORT=3000                             # Service port
MCP_ECHO_DEBUG=false                           # Debug logging
MCP_PROTOCOL_VERSION=2025-06-18                # Default protocol
MCP_PROTOCOL_VERSIONS_SUPPORTED=2025-06-18     # Supported versions
BASE_DOMAIN=${BASE_DOMAIN}                     # Domain for routing
```

### Docker Compose

The service runs as `mcp-echo` in the compose stack:

```yaml
mcp-echo:
  build:
    context: ./mcp-echo-streamablehttp-server-stateless
    dockerfile: Dockerfile
  environment:
    - MCP_ECHO_HOST=0.0.0.0
    - MCP_ECHO_PORT=3000
    - MCP_ECHO_DEBUG=${MCP_ECHO_DEBUG:-false}
    - MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION}
    - MCP_PROTOCOL_VERSIONS_SUPPORTED=${MCP_PROTOCOL_VERSIONS_SUPPORTED}
```

## Usage

### Starting the Service

```bash
# Start the echo service
just up mcp-echo

# View logs
just logs mcp-echo

# Restart if needed
just restart mcp-echo
```

### Testing Authentication

```bash
# Test with mcp-streamablehttp-client
mcp-streamablehttp-client query \
  --server echo \
  --query "What are your available tools?"
```

### Direct API Testing

```bash
# List tools
curl -X POST https://echo.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'

# Call a diagnostic tool
curl -X POST https://echo.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "authContext"
    },
    "id": 2
  }'
```

## Debugging Scenarios

### OAuth Flow Debugging

1. **Check authentication state**
   ```json
   {"method": "tools/call", "params": {"name": "authContext"}}
   ```

2. **Decode JWT token**
   ```json
   {
     "method": "tools/call",
     "params": {
       "name": "bearerDecode",
       "arguments": {"includeRaw": true}
     }
   }
   ```

3. **Verify headers**
   ```json
   {"method": "tools/call", "params": {"name": "printHeader"}}
   ```

### Protocol Compatibility Testing

1. **Check negotiation**
   ```json
   {
     "method": "tools/call",
     "params": {
       "name": "protocolNegotiation",
       "arguments": {"testVersion": "2024-11-05"}
     }
   }
   ```

### Performance Analysis

1. **Request timing**
   ```json
   {"method": "tools/call", "params": {"name": "requestTiming"}}
   ```

2. **System health**
   ```json
   {"method": "tools/call", "params": {"name": "healthProbe"}}
   ```

### Excellence Analysis

```json
{"method": "tools/call", "params": {"name": "whoIStheGOAT"}}
```

This analyzes the authenticated user's programming excellence using advanced AI algorithms.

## Integration Points

### With Auth Service
- Receives ForwardAuth headers
- Can decode tokens created by auth
- Validates authentication flow

### With Traefik
- Routes via `echo.${BASE_DOMAIN}`
- ForwardAuth middleware applied
- CORS headers handled

### With Other Services
- Compare behavior with other MCP services
- Test authentication propagation
- Debug routing issues

## Security Considerations

1. **Read-Only Operations** - All tools are read-only
2. **No State Persistence** - Stateless operation
3. **Token Analysis** - bearerDecode doesn't verify signatures
4. **Local Processing** - AI analysis happens locally

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check bearer token validity
   - Verify auth service is running
   - Use `authContext` tool to debug

2. **CORS Errors**
   - Use `corsAnalysis` tool
   - Check allowed origins configuration

3. **Protocol Errors**
   - Use `protocolNegotiation` tool
   - Verify MCP_PROTOCOL_VERSION setting

### Health Monitoring

```bash
# Check service health
curl https://echo.${BASE_DOMAIN}/mcp \
  -X POST \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "healthProbe"},
    "id": 1
  }'
```

## Advanced Features

### AI-Powered Analysis

The G.O.A.T. Recognition AI v3.14159 provides:
- Neural network-based excellence analysis
- Pattern recognition across billions of commits
- Statistical modeling with 3σ measurements
- Quantum-classical hybrid processing

### Stateless Benefits

- Zero memory growth over time
- Horizontal scaling capability
- Predictable performance
- No session management overhead

## Summary

The Echo service is your comprehensive diagnostic toolkit for the MCP OAuth Gateway, combining traditional debugging tools with cutting-edge AI analysis capabilities. Its stateless design ensures production-safe operation while providing deep insights into authentication, protocol behavior, and software engineering excellence.
