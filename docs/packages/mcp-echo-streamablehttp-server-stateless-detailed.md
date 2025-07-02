# mcp-echo-streamablehttp-server-stateless

## Overview

The `mcp-echo-streamablehttp-server-stateless` is a lightweight diagnostic MCP server designed for protocol debugging, authentication testing, and system diagnostics. Unlike its stateful counterpart, this server maintains no session state between requests, making it ideal for production diagnostics, load testing, and scenarios where horizontal scaling is required.

## Architecture

### Stateless Design Philosophy

```
┌──────────────┐    HTTP Request     ┌─────────────────────┐
│  MCP Client  │ ──────────────────→ │  Stateless Echo     │
│              │                      │  Server             │
│              │ ←────────────────── │  (No persistence)   │
└──────────────┘    HTTP Response    └─────────────────────┘

Each request is completely independent - no shared state
```

### Core Components

```
mcp_echo_streamablehttp_server_stateless/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point
├── server.py            # FastAPI application
├── tools.py             # 9 diagnostic tools
├── models.py            # Data models
└── utils.py             # Helper utilities
```

## Key Features

### Stateless Operation
- **No Session Persistence**: Each request is isolated
- **Thread-Safe**: Uses contextvars for request isolation
- **Horizontal Scaling**: Can run multiple instances
- **No Memory Growth**: No state accumulation
- **Cloud-Native**: Perfect for containerized deployments

### 9 Diagnostic Tools

1. **echo** - Simple message echo for connectivity testing
2. **printHeader** - Displays all HTTP headers organized by category
3. **bearerDecode** - Decodes JWT Bearer tokens (no verification)
4. **authContext** - Complete authentication context analysis
5. **requestTiming** - Request performance timing and system stats
6. **corsAnalysis** - Analyzes CORS configuration and headers
7. **environmentDump** - Displays sanitized environment configuration
8. **healthProbe** - Deep health check with system resource monitoring
9. **whoIStheGOAT** - Easter egg revealing programming wisdom

### Protocol Support
- MCP Protocol 2025-06-18 (configurable)
- StreamableHTTP transport
- JSON-RPC 2.0 compliant
- SSE response support
- Session ID tracking (without state)

## Installation

### Using pip
```bash
pip install mcp-echo-streamablehttp-server-stateless
```

### Using pixi
```bash
pixi add --pypi mcp-echo-streamablehttp-server-stateless
```

### Docker
```dockerfile
FROM python:3.11-slim

RUN pip install mcp-echo-streamablehttp-server-stateless

ENV MCP_ECHO_HOST=0.0.0.0
ENV MCP_ECHO_PORT=3000
ENV MCP_ECHO_DEBUG=false

EXPOSE 3000

CMD ["python", "-m", "mcp_echo_streamablehttp_server_stateless"]
```

## Configuration

### Environment Variables

```bash
# Server Configuration
MCP_ECHO_HOST=127.0.0.1        # Bind address (default: 127.0.0.1)
MCP_ECHO_PORT=3000             # Server port (default: 3000)
MCP_ECHO_DEBUG=false           # Debug logging (default: false)

# Protocol Configuration
MCP_PROTOCOL_VERSION=2025-06-18
MCP_PROTOCOL_VERSIONS_SUPPORTED=2025-06-18,2024-11-05

# Logging
LOG_FILE=/logs/mcp-echo-stateless.log
LOG_LEVEL=INFO

# Performance
WORKERS=1                       # Number of worker processes
WORKER_CONNECTIONS=1000         # Max connections per worker
```

## API Reference

### POST /mcp
Main endpoint for JSON-RPC requests.

**Headers**:
- `Content-Type: application/json`
- `Accept: application/json, text/event-stream`
- `Mcp-Session-Id: <uuid>` (optional, passed through)
- `Authorization: Bearer <token>` (optional, analyzed by tools)

**Initialize Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {
      "name": "test-client",
      "version": "1.0"
    }
  },
  "id": 1
}
```

## Diagnostic Tools in Detail

### 1. echo
Basic connectivity and echo testing.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "echo",
    "arguments": {
      "message": "Hello, MCP!",
      "uppercase": false,
      "reverse": true
    }
  },
  "id": 2
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [{
      "type": "text",
      "text": "!PCM ,olleH"
    }]
  },
  "id": 2
}
```

### 2. printHeader
Comprehensive header analysis.

**Response Example**:
```json
{
  "content": [{
    "type": "text",
    "text": "📋 HTTP Headers Analysis (18 total headers)\n\n🔐 Authentication Headers:\n  authorization: Bearer eyJhbGc...\n  x-user-id: 12345\n  x-user-name: johndoe\n  x-auth-token: token_abc123\n\n🌐 Standard HTTP Headers:\n  host: mcp-echo.example.com\n  user-agent: MCP-Client/1.0\n  content-type: application/json\n  accept: application/json, text/event-stream\n\n🔧 MCP Protocol Headers:\n  mcp-session-id: 550e8400-e29b-41d4-a716-446655440000\n  mcp-protocol-version: 2025-06-18\n\n🚀 Traefik Headers:\n  x-forwarded-for: 192.168.1.100\n  x-forwarded-proto: https\n  x-real-ip: 192.168.1.100\n\n📦 Custom Headers:\n  x-request-id: req_xyz789\n  x-correlation-id: corr_123"
  }]
}
```

### 3. bearerDecode
JWT token analysis without verification.

**Request**:
```json
{
  "name": "bearerDecode",
  "arguments": {
    "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.NHVaYe26MbtOYhSKkoKYdFVomg4i8ZJd8_-RU8VNbftc4TSMb4bXP3l3YlNWACwyXPGffz5aXHc6lty1Y2t4SWRqGteragsVdZufDn5BlnJl9pdR_kdVFUsra2rWKEofkZeIC4yWytE58sMIihvo9H1ScmmVwBcQP6XETqYd0aSHp1gOa9RdUPDvoXQ5oqygTqVtxaDr6wUFKrKItgBMzWIdNZ6y7O9E0DhEPTbE9rfBo6KTFsHAZnMg4k68CDp2woYIaXbmYTWcvbzIuHO7_37GT79XdIwkm95QJ7hYC9RiwrV7mesbY4PAahERJawntho0my942XheVLmGwLMBkQ"
  }
}
```

**Response**:
```json
{
  "content": [{
    "type": "text",
    "text": "🔍 JWT Token Analysis (Unverified)\n\n📄 Header:\n{\n  \"alg\": \"RS256\",\n  \"typ\": \"JWT\"\n}\n\n📦 Payload:\n{\n  \"sub\": \"1234567890\",\n  \"name\": \"John Doe\",\n  \"admin\": true,\n  \"iat\": 1516239022\n}\n\n⏱️ Token Timeline:\n  Issued At: 2018-01-18 01:30:22 UTC (1516239022)\n  Age: 6 years, 11 months\n\n⚠️ Security Notice:\n  This analysis does NOT verify the token signature.\n  Token may be forged or tampered with.\n  Use only for debugging purposes."
  }]
}
```

### 4. authContext
Complete authentication context analysis.

**Response Structure**:
```json
{
  "content": [{
    "type": "text",
    "text": "🔐 Authentication Context Analysis\n\n👤 User Information:\n  User ID: 12345\n  Username: johndoe\n  Email: john@example.com\n  Roles: [\"user\", \"developer\"]\n\n🎫 Token Analysis:\n  Type: Bearer\n  Length: 847 characters\n  Algorithm: RS256 (from header)\n  Issuer: https://auth.example.com\n  Audience: https://api.example.com\n\n🔑 Session Information:\n  Session ID: 550e8400-e29b-41d4-a716-446655440000\n  Client: test-client v1.0\n  Protocol: 2025-06-18\n\n🌐 Request Context:\n  Origin: https://app.example.com\n  IP Address: 192.168.1.100\n  User Agent: MCP-Client/1.0\n\n✅ Authentication Status: AUTHENTICATED"
  }]
}
```

### 5. requestTiming
Performance timing and system analysis.

**Response**:
```json
{
  "content": [{
    "type": "text",
    "text": "⏱️ Request Timing Analysis\n\n📊 Performance Metrics:\n  Request Started: 2024-01-01 12:00:00.123456 UTC\n  Current Time: 2024-01-01 12:00:00.145678 UTC\n  Processing Duration: 22.22ms\n  Performance Rating: 🟢 Excellent (<50ms)\n\n💻 System Resources:\n  CPU Usage: 12.5% (2 cores)\n  Memory: 256MB / 1024MB (25.0%)\n  Python Version: 3.11.0\n  Platform: Linux-5.15.0-x86_64\n\n🌡️ Process Stats:\n  Process ID: 1234\n  Thread Count: 4\n  Open Files: 42\n  Uptime: 1h 23m 45s\n\n📈 Load Average:\n  1 min: 0.15\n  5 min: 0.20\n  15 min: 0.18"
  }]
}
```

### 6. corsAnalysis
CORS configuration analysis.

**Response**:
```json
{
  "content": [{
    "type": "text",
    "text": "🌐 CORS Analysis\n\n📥 Request Headers:\n  Origin: https://app.example.com\n  Access-Control-Request-Method: POST\n  Access-Control-Request-Headers: authorization, content-type\n\n📤 Response Headers (Expected):\n  Access-Control-Allow-Origin: https://app.example.com\n  Access-Control-Allow-Methods: GET, POST, OPTIONS\n  Access-Control-Allow-Headers: authorization, content-type\n  Access-Control-Allow-Credentials: true\n  Access-Control-Max-Age: 86400\n\n🔍 CORS Status:\n  ✅ Origin allowed\n  ✅ Method allowed\n  ✅ Headers allowed\n  ✅ Credentials allowed\n\n💡 Recommendations:\n  - CORS headers should be set by Traefik\n  - This service should not set CORS headers\n  - Use specific origins, not wildcards"
  }]
}
```

### 7. environmentDump
Sanitized environment display.

**Response**:
```json
{
  "content": [{
    "type": "text",
    "text": "🔧 Environment Configuration (Sanitized)\n\n🌟 MCP Configuration:\n  MCP_ECHO_HOST: 0.0.0.0\n  MCP_ECHO_PORT: 3000\n  MCP_ECHO_DEBUG: false\n  MCP_PROTOCOL_VERSION: 2025-06-18\n  MCP_PROTOCOL_VERSIONS_SUPPORTED: 2025-06-18,2024-11-05\n\n🔐 Sensitive Values (Hidden):\n  JWT_SECRET: ******* (hidden)\n  DATABASE_PASSWORD: ******* (hidden)\n  API_KEY: ******* (hidden)\n\n📊 Runtime Environment:\n  NODE_ENV: production\n  LOG_LEVEL: INFO\n  TZ: UTC\n\n🐳 Container Detection:\n  Running in Docker: ✅ Yes\n  Container ID: abc123def456\n  Kubernetes: ❌ No"
  }]
}
```

### 8. healthProbe
Comprehensive health check.

**Response**:
```json
{
  "content": [{
    "type": "text",
    "text": "🏥 System Health Report\n\n✅ Overall Status: HEALTHY\n\n🔋 Resource Usage:\n  CPU: 12.5% (healthy)\n  Memory: 256MB / 1024MB (healthy)\n  Disk: 45% used (healthy)\n  Network: Active connections: 23\n\n🌡️ Service Health:\n  HTTP Server: ✅ Running\n  Event Loop: ✅ Responsive\n  Database: ⚠️ Not configured\n  Redis: ⚠️ Not configured\n\n📊 Performance Metrics:\n  Average Response Time: 18.5ms\n  Request Rate: 120 req/min\n  Error Rate: 0.1%\n  Uptime: 99.99%\n\n🔍 Diagnostic Summary:\n  All systems operational\n  No critical issues detected\n  Performance within normal parameters"
  }]
}
```

### 9. whoIStheGOAT
Programming wisdom easter egg.

**Response varies**, example:
```json
{
  "content": [{
    "type": "text",
    "text": "🐐 Excellence Analysis: Dennis Ritchie\n\n🌟 Why Dennis Ritchie is the GOAT:\n\nDennis Ritchie created the C programming language and co-developed Unix, forming the foundation of modern computing. His work influences virtually every device and system today.\n\n💡 Key Contributions:\n• Created C (1972) - the language that built the world\n• Co-created Unix with Ken Thompson\n• Influenced all modern programming languages\n• Enabled portable system software\n\n📖 Wisdom: \"The only way to learn a new programming language is by writing programs in it.\"\n\n🎯 Legacy Impact: Every time you use a computer, phone, or any digital device, you're using technology built on Ritchie's foundations.\n\nHumble, brilliant, and transformative - a true GOAT! 🙌"
  }]
}
```

## Usage Examples

### Basic Testing

```bash
# Initialize and test echo
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {"message": "Hello, World!"}
    },
    "id": 1
  }'
```

### Authentication Debugging

```python
import httpx
import asyncio

async def debug_auth():
    async with httpx.AsyncClient() as client:
        # Test with Bearer token
        response = await client.post(
            "http://localhost:3000/mcp",
            headers={
                "Authorization": "Bearer eyJhbGc..."
            },
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "authContext",
                    "arguments": {}
                },
                "id": 1
            }
        )

        result = response.json()
        print(result["result"]["content"][0]["text"])

asyncio.run(debug_auth())
```

### Performance Testing

```javascript
// Concurrent performance testing
async function performanceTest() {
  const promises = [];

  for (let i = 0; i < 100; i++) {
    promises.push(
      fetch('http://localhost:3000/mcp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'tools/call',
          params: {
            name: 'requestTiming',
            arguments: {}
          },
          id: i
        })
      })
    );
  }

  const results = await Promise.all(promises);
  console.log(`Completed ${results.length} requests`);
}
```

## Docker Compose Integration

```yaml
services:
  mcp-echo-stateless:
    build: ./mcp-echo-streamablehttp-server-stateless
    environment:
      - MCP_ECHO_HOST=0.0.0.0
      - MCP_ECHO_PORT=3000
      - MCP_ECHO_DEBUG=false
      - MCP_PROTOCOL_VERSION=2025-06-18
    deploy:
      replicas: 3  # Can scale horizontally
      resources:
        limits:
          memory: 256M
          cpus: '0.5'
    networks:
      - internal
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/mcp",
             "-X", "POST", "-H", "Content-Type: application/json",
             "-d", '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"healthProbe","arguments":{}},"id":1}']
      interval: 30s
      timeout: 5s
      retries: 3
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mcp-echo-stateless.rule=Host(`mcp-echo.${BASE_DOMAIN}`)"
      - "traefik.http.routers.mcp-echo-stateless.priority=2"
      - "traefik.http.routers.mcp-echo-stateless.middlewares=mcp-auth"
      - "traefik.http.services.mcp-echo-stateless.loadbalancer.server.port=3000"
```

## Performance Characteristics

### Resource Usage
- **Memory**: ~50MB base
- **CPU**: Minimal (I/O bound)
- **Startup Time**: <1 second
- **Request Overhead**: <1ms

### Scaling
- **Horizontal**: Unlimited instances
- **Vertical**: Single-threaded per worker
- **Load Balancing**: Round-robin ready
- **State**: None - perfect for scaling

### Benchmarks
```bash
# Using wrk for load testing
wrk -t12 -c400 -d30s --script=mcp_echo.lua http://localhost:3000/mcp

# Results (example)
Requests/sec: 15,234.56
Latency:      25.43ms avg
Throughput:   45.2MB/s
```

## Use Cases

### 1. Protocol Debugging
- Verify MCP protocol implementation
- Test client/server handshake
- Debug message formatting

### 2. Authentication Testing
- Decode JWT tokens
- Verify auth headers
- Test ForwardAuth integration

### 3. Performance Analysis
- Measure request latency
- Monitor resource usage
- Load testing baseline

### 4. Integration Testing
- Validate OAuth flows
- Test Traefik routing
- Verify header forwarding

### 5. Production Diagnostics
- Health monitoring
- Environment verification
- CORS troubleshooting

## Comparison with Stateful Version

| Aspect | Stateless | Stateful |
|--------|-----------|----------|
| State Persistence | ❌ None | ✅ Session-based |
| Horizontal Scaling | ✅ Excellent | ❌ Limited |
| Resource Usage | ✅ Low | ⚠️ Higher |
| Use Case | Production | Development |
| Message Queuing | ❌ No | ✅ Yes |
| Replay Capability | ❌ No | ✅ Yes |
| Session Tracking | ⚠️ ID only | ✅ Full state |

## Security Considerations

### Important Warnings

1. **No Token Verification**: `bearerDecode` does NOT verify signatures
2. **No Authentication**: Service has no built-in auth
3. **Information Disclosure**: Tools reveal system information
4. **Debug Only**: Not for production secrets

### Best Practices

1. **Always use behind Traefik**: Never expose directly
2. **Limit access**: Use IP allowlists in production
3. **Sanitize logs**: Don't log sensitive data
4. **Monitor usage**: Track who uses debug tools
5. **Rotate tokens**: Debug tokens should be short-lived

## Troubleshooting

### Common Issues

#### "Method not found"
Ensure you're calling the correct method:
- `initialize` first
- Then `tools/list` or `tools/call`

#### Empty responses
Check Accept header includes `application/json`

#### Performance degradation
- Check CPU/memory limits
- Verify no blocking I/O
- Monitor concurrent connections

### Debug Mode

```bash
# Maximum verbosity
export MCP_ECHO_DEBUG=true
export LOG_LEVEL=DEBUG
export PYTHONDEBUG=1

python -m mcp_echo_streamablehttp_server_stateless
```

## Development Tips

### Testing Tools
```python
# Quick test script
import requests

def test_tool(tool_name, arguments={}):
    response = requests.post(
        "http://localhost:3000/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1
        }
    )
    return response.json()

# Test all tools
tools = ["echo", "printHeader", "bearerDecode",
         "authContext", "requestTiming", "corsAnalysis",
         "environmentDump", "healthProbe", "whoIStheGOAT"]

for tool in tools:
    print(f"\n=== Testing {tool} ===")
    result = test_tool(tool)
    print(result)
```

### Custom Deployment

```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-echo-stateless
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-echo-stateless
  template:
    metadata:
      labels:
        app: mcp-echo-stateless
    spec:
      containers:
      - name: echo-server
        image: mcp-echo-stateless:latest
        ports:
        - containerPort: 3000
        env:
        - name: MCP_ECHO_HOST
          value: "0.0.0.0"
        - name: MCP_ECHO_DEBUG
          value: "false"
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /mcp
            port: 3000
            httpHeaders:
            - name: Content-Type
              value: application/json
          initialDelaySeconds: 5
          periodSeconds: 10
```

## Best Practices

1. **Use for debugging only**: Not for production logic
2. **Combine with monitoring**: Use alongside proper APM
3. **Automate testing**: Include in CI/CD pipelines
4. **Document findings**: Save debug outputs
5. **Version control**: Track which version was used
6. **Security audit**: Review what's exposed

## Future Enhancements

- [ ] Performance statistics endpoint
- [ ] OpenTelemetry tracing
- [ ] WebSocket support
- [ ] GraphQL introspection tool
- [ ] Request replay tool
- [ ] Latency injection for testing
- [ ] Customizable response delays
