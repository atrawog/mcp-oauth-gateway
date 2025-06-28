# Echo Services

The MCP Echo services are advanced diagnostic and AI-powered MCP servers providing comprehensive tools for debugging OAuth flows, authentication contexts, protocol behavior, and analyzing software engineering excellence metrics. The gateway provides **two variants** of the echo service:

- **mcp-echo-stateful**: Maintains session state with message history and replay capabilities
- **mcp-echo-stateless**: Lightweight version without state management

## Overview

Both Echo service variants provide:
- 10+ powerful diagnostic tools for debugging
- AI-powered analysis with G.O.A.T. Recognition AI v3.14159
- OAuth flow analysis and JWT token decoding
- Protocol version negotiation testing
- System health and performance monitoring
- CORS configuration analysis
- OAuth-protected access via Traefik ForwardAuth

### Key Differences

| Feature | Stateful | Stateless |
|---------|----------|------------|
| Session Management | Yes (1 hour timeout) | No |
| Message History | Yes | No |
| `replayLastEcho` Tool | Yes | No |
| Memory Usage | Higher (stores sessions) | Lower |
| Session ID in Responses | Yes | No |
| Horizontal Scaling | Requires session affinity | Easy |

## Architecture

### Stateful Echo Service
- **Implementation**: Native streamable HTTP server with SessionManager
- **Protocol**: Direct HTTP with SSE support + session tracking
- **Port**: Exposes port 3000 for HTTP access
- **Package**: `mcp-echo-streamablehttp-server-stateful`
- **Session Timeout**: 3600 seconds (1 hour)
- **Purpose**: Debugging with context and history

### Stateless Echo Service
- **Implementation**: Native streamable HTTP server (stateless)
- **Protocol**: Direct HTTP with SSE support
- **Port**: Exposes port 3000 for HTTP access
- **Package**: `mcp-echo-streamablehttp-server-stateless`
- **Purpose**: Lightweight debugging without state

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
   - Stateful version includes session context

10. **sessionInfo** - Session information display
    - Current session ID
    - Active sessions count
    - Session statistics
    - Available in both variants

11. **replayLastEcho** - Replay previous echo message (**Stateful only**)
    - Retrieves last echo message from session
    - Shows session continuity
    - Useful for testing session persistence

12. **whoIStheGOAT** - AI-powered excellence analysis
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

# Stateful-specific settings
MCP_SESSION_TIMEOUT=3600                       # Session timeout in seconds

# Enable/disable services
MCP_ECHO_STATEFUL_ENABLED=true                 # Enable stateful variant
MCP_ECHO_STATELESS_ENABLED=true                # Enable stateless variant
```

### Docker Compose

Both services run in the compose stack with different configurations:

#### Stateful Service
```yaml
mcp-echo-stateful:
  build:
    context: ./mcp-echo-streamablehttp-server-stateful
    dockerfile: Dockerfile
  environment:
    - MCP_ECHO_HOST=0.0.0.0
    - MCP_ECHO_PORT=3000
    - MCP_ECHO_DEBUG=${MCP_ECHO_DEBUG:-true}
    - MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION}
    - MCP_SESSION_TIMEOUT=${MCP_SESSION_TIMEOUT:-3600}
  volumes:
    - ../logs/mcp-echo-stateful:/logs
```

#### Stateless Service
```yaml
mcp-echo-stateless:
  build:
    context: ./mcp-echo-streamablehttp-server-stateless
    dockerfile: Dockerfile
  environment:
    - MCP_ECHO_HOST=0.0.0.0
    - MCP_ECHO_PORT=3000
    - MCP_ECHO_DEBUG=${MCP_ECHO_DEBUG:-true}
    - MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION}
  volumes:
    - ../logs/mcp-echo-stateless:/logs
```

## Usage

### Starting the Services

```bash
# Start both echo services
just up mcp-echo-stateful mcp-echo-stateless

# Start only stateful variant
just up mcp-echo-stateful

# Start only stateless variant
just up mcp-echo-stateless

# View logs
just logs mcp-echo-stateful
just logs -f mcp-echo-stateless  # Follow mode

# Restart if needed
just restart mcp-echo-stateful
just restart mcp-echo-stateless
```

### Testing Authentication

```bash
# Test stateful variant with mcp-streamablehttp-client
mcp-streamablehttp-client query \
  --server echo-stateful \
  --query "What are your available tools?"

# Test stateless variant
mcp-streamablehttp-client query \
  --server echo-stateless \
  --query "What are your available tools?"
```

### Direct API Testing

```bash
# List tools from stateful service
curl -X POST https://echo-stateful.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'

# Test session persistence with stateful service
# First echo
curl -X POST https://echo-stateful.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {"message": "Hello from session"}
    },
    "id": 2
  }'

# Replay last echo (stateful only)
curl -X POST https://echo-stateful.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "replayLastEcho"
    },
    "id": 3
  }'

# Test stateless variant (no session)
curl -X POST https://echo-stateless.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "authContext"
    },
    "id": 4
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

### Session Testing (Stateful Only)

1. **Test session persistence**
   ```json
   {
     "method": "tools/call",
     "params": {
       "name": "echo",
       "arguments": {"message": "Remember this message"}
     }
   }
   ```

2. **Replay the last echo**
   ```json
   {"method": "tools/call", "params": {"name": "replayLastEcho"}}
   ```

3. **Check session info**
   ```json
   {"method": "tools/call", "params": {"name": "sessionInfo"}}
   ```

## Integration Points

### With Auth Service
- Receives ForwardAuth headers
- Can decode tokens created by auth
- Validates authentication flow

### With Traefik
- Stateful routes via `echo-stateful.${BASE_DOMAIN}`
- Stateless routes via `echo-stateless.${BASE_DOMAIN}`
- Additional numbered subdomains (e.g., `echo-stateful0` through `echo-stateful9`)
- ForwardAuth middleware applied
- CORS headers handled
- OAuth discovery endpoints available

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
# Check stateful service health
curl https://echo-stateful.${BASE_DOMAIN}/mcp \
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

# Docker health check status
docker inspect mcp-oauth-gateway-mcp-echo-stateful-1 --format='{{json .State.Health}}'
docker inspect mcp-oauth-gateway-mcp-echo-stateless-1 --format='{{json .State.Health}}'
```

## Advanced Features

### AI-Powered Analysis

The G.O.A.T. Recognition AI v3.14159 provides:
- Neural network-based excellence analysis
- Pattern recognition across billions of commits
- Statistical modeling with 3σ measurements
- Quantum-classical hybrid processing

### Stateful vs Stateless Benefits

#### Stateful Benefits
- Session continuity for debugging
- Message history and replay
- Context-aware responses
- Better for interactive debugging sessions

#### Stateless Benefits
- Zero memory growth over time
- Easy horizontal scaling
- Predictable performance
- No session management overhead
- Lower resource usage

## Summary

The Echo services provide comprehensive diagnostic toolkits for the MCP OAuth Gateway, combining traditional debugging tools with cutting-edge AI analysis capabilities. Choose between:

- **Stateful**: When you need session persistence, message history, and context-aware debugging
- **Stateless**: When you need lightweight, scalable debugging without state management

Both variants ensure production-safe operation while providing deep insights into authentication, protocol behavior, and software engineering excellence. The ability to run both simultaneously allows for comparison testing and different use cases within the same deployment.
