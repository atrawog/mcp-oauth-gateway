# mcp-echo-streamablehttp-server-stateless

A lightweight, stateless MCP echo service optimized for production diagnostics, authentication testing, and high-performance scenarios with no session state persistence.

## Quick Start

**Key Features:**
- No session state between requests - perfect for horizontal scaling
- 9 diagnostic tools for OAuth/auth testing and system analysis
- Minimal memory footprint and fast startup
- Thread-safe with contextvars for request isolation
- Cloud-native and container-optimized

**Installation:**
```bash
pip install mcp-echo-streamablehttp-server-stateless
# or
pixi add --pypi mcp-echo-streamablehttp-server-stateless
```

**Basic Usage:**
```bash
# Start the server
python -m mcp_echo_streamablehttp_server_stateless

# Test echo functionality
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"echo","arguments":{"message":"Hello!"}},"id":1}'
```

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Diagnostic Tools Reference](#diagnostic-tools-reference)
6. [API Reference](#api-reference)
7. [Usage Examples](#usage-examples)
8. [Docker Deployment](#docker-deployment)
9. [Performance & Scaling](#performance--scaling)
10. [Use Cases](#use-cases)
11. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
12. [Security Considerations](#security-considerations)
13. [Comparison with Stateful Version](#comparison-with-stateful-version)

## Overview

The `mcp-echo-streamablehttp-server-stateless` is designed for scenarios where state persistence is not needed, making it ideal for:

- Production health checks and diagnostics
- Load balancing across multiple instances
- OAuth and authentication debugging
- Performance benchmarking
- Gateway integration testing

Unlike its stateful counterpart, each request is completely independent with no shared state, enabling unlimited horizontal scaling.

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
├── server.py            # FastAPI application with tools
├── models.py            # Data models
└── utils.py             # Helper utilities
```

### Pure Functional Design

- No global state or session storage
- Thread-safe using contextvars
- Each request handler is a pure function
- No side effects or state accumulation
- Immutable request handling

## Installation

### Using pip
```bash
pip install mcp-echo-streamablehttp-server-stateless
```

### Using pixi
```bash
pixi add --pypi mcp-echo-streamablehttp-server-stateless
```

### Docker Installation
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Minimal dependencies
RUN pip install --no-cache-dir mcp-echo-streamablehttp-server-stateless

# Run with multiple workers for production
CMD ["uvicorn", "mcp_echo_streamablehttp_server_stateless:app", \
     "--host", "0.0.0.0", "--port", "3000", "--workers", "4"]

# Simple health check
HEALTHCHECK --interval=10s --timeout=2s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
```

## Configuration

### Environment Variables

```bash
# Server Configuration
MCP_ECHO_HOST=0.0.0.0          # Bind address (default: 127.0.0.1)
MCP_ECHO_PORT=3000             # Server port (default: 3000)
MCP_ECHO_DEBUG=false           # Debug logging (default: false)

# Protocol Configuration
MCP_PROTOCOL_VERSION=2025-06-18
MCP_PROTOCOL_VERSIONS_SUPPORTED=2025-06-18,2024-11-05

# Performance Tuning
ECHO_STATELESS_WORKERS=4        # Number of worker processes
ECHO_STATELESS_MAX_REQUESTS=10000  # Max requests per worker
WORKER_CONNECTIONS=1000         # Max connections per worker

# Logging
ECHO_STATELESS_LOG_LEVEL=INFO
LOG_FILE=/logs/mcp-echo-stateless.log
LOG_LEVEL=INFO
```

## Diagnostic Tools Reference

### 1. echo
Simple message echo for connectivity testing with optional transformations.

**Arguments:**
- `message` (string, required): Message to echo
- `uppercase` (boolean, optional): Convert to uppercase
- `reverse` (boolean, optional): Reverse the message

**Example:**
```json
{
  "name": "echo",
  "arguments": {
    "message": "Hello, MCP!",
    "uppercase": false,
    "reverse": true
  }
}
```

**Response:**
```
!PCM ,olleH
```

### 2. printHeader
Displays all HTTP headers organized by category for debugging.

**Arguments:** None

**Response:**
```
📋 HTTP Headers Analysis (18 total headers)

🔐 Authentication Headers:
  authorization: Bearer eyJhbGc...
  x-user-id: 12345
  x-user-name: johndoe
  x-auth-token: token_abc123

🌐 Standard HTTP Headers:
  host: mcp-echo.example.com
  user-agent: MCP-Client/1.0
  content-type: application/json
  accept: application/json, text/event-stream

🔧 MCP Protocol Headers:
  mcp-session-id: 550e8400-e29b-41d4-a716-446655440000
  mcp-protocol-version: 2025-06-18

🚀 Traefik Headers:
  x-forwarded-for: 192.168.1.100
  x-forwarded-proto: https
  x-real-ip: 192.168.1.100

📦 Custom Headers:
  x-request-id: req_xyz789
  x-correlation-id: corr_123
```

### 3. bearerDecode
Decodes JWT Bearer tokens without verification (debugging only).

**Arguments:**
- `token` (string, optional): JWT token to decode (uses Authorization header if not provided)

**Response:**
```
🔍 JWT Token Analysis (Unverified)

📄 Header:
{
  "alg": "RS256",
  "typ": "JWT"
}

📦 Payload:
{
  "sub": "1234567890",
  "name": "John Doe",
  "admin": true,
  "iat": 1516239022
}

⏱️ Token Timeline:
  Issued At: 2018-01-18 01:30:22 UTC (1516239022)
  Age: 6 years, 11 months

⚠️ Security Notice:
  This analysis does NOT verify the token signature.
  Token may be forged or tampered with.
  Use only for debugging purposes.
```

### 4. authContext
Complete authentication context analysis from request headers.

**Response:**
```
🔐 Authentication Context Analysis

👤 User Information:
  User ID: 12345
  Username: johndoe
  Email: john@example.com
  Roles: ["user", "developer"]

🎫 Token Analysis:
  Type: Bearer
  Length: 847 characters
  Algorithm: RS256 (from header)
  Issuer: https://auth.example.com
  Audience: https://api.example.com

🔑 Session Information:
  Session ID: 550e8400-e29b-41d4-a716-446655440000
  Client: test-client v1.0
  Protocol: 2025-06-18

🌐 Request Context:
  Origin: https://app.example.com
  IP Address: 192.168.1.100
  User Agent: MCP-Client/1.0

✅ Authentication Status: AUTHENTICATED
```

### 5. requestTiming
Performance timing and system resource analysis.

**Response:**
```
⏱️ Request Timing Analysis

📊 Performance Metrics:
  Request Started: 2024-01-01 12:00:00.123456 UTC
  Current Time: 2024-01-01 12:00:00.145678 UTC
  Processing Duration: 22.22ms
  Performance Rating: 🟢 Excellent (<50ms)

💻 System Resources:
  CPU Usage: 12.5% (2 cores)
  Memory: 256MB / 1024MB (25.0%)
  Python Version: 3.11.0
  Platform: Linux-5.15.0-x86_64

🌡️ Process Stats:
  Process ID: 1234
  Thread Count: 4
  Open Files: 42
  Uptime: 1h 23m 45s

📈 Load Average:
  1 min: 0.15
  5 min: 0.20
  15 min: 0.18
```

### 6. corsAnalysis
Analyzes CORS configuration and headers.

**Response:**
```
🌐 CORS Analysis

📥 Request Headers:
  Origin: https://app.example.com
  Access-Control-Request-Method: POST
  Access-Control-Request-Headers: authorization, content-type

📤 Response Headers (Expected):
  Access-Control-Allow-Origin: https://app.example.com
  Access-Control-Allow-Methods: GET, POST, OPTIONS
  Access-Control-Allow-Headers: authorization, content-type
  Access-Control-Allow-Credentials: true
  Access-Control-Max-Age: 86400

🔍 CORS Status:
  ✅ Origin allowed
  ✅ Method allowed
  ✅ Headers allowed
  ✅ Credentials allowed

💡 Recommendations:
  - CORS headers should be set by Traefik
  - This service should not set CORS headers
  - Use specific origins, not wildcards
```

### 7. environmentDump
Displays sanitized environment configuration.

**Response:**
```
🔧 Environment Configuration (Sanitized)

🌟 MCP Configuration:
  MCP_ECHO_HOST: 0.0.0.0
  MCP_ECHO_PORT: 3000
  MCP_ECHO_DEBUG: false
  MCP_PROTOCOL_VERSION: 2025-06-18
  MCP_PROTOCOL_VERSIONS_SUPPORTED: 2025-06-18,2024-11-05

🔐 Sensitive Values (Hidden):
  JWT_SECRET: ******* (hidden)
  DATABASE_PASSWORD: ******* (hidden)
  API_KEY: ******* (hidden)

📊 Runtime Environment:
  NODE_ENV: production
  LOG_LEVEL: INFO
  TZ: UTC

🐳 Container Detection:
  Running in Docker: ✅ Yes
  Container ID: abc123def456
  Kubernetes: ❌ No
```

### 8. healthProbe
Comprehensive health check with system monitoring.

**Response:**
```
🏥 System Health Report

✅ Overall Status: HEALTHY

🔋 Resource Usage:
  CPU: 12.5% (healthy)
  Memory: 256MB / 1024MB (healthy)
  Disk: 45% used (healthy)
  Network: Active connections: 23

🌡️ Service Health:
  HTTP Server: ✅ Running
  Event Loop: ✅ Responsive
  Database: ⚠️ Not configured
  Redis: ⚠️ Not configured

📊 Performance Metrics:
  Average Response Time: 18.5ms
  Request Rate: 120 req/min
  Error Rate: 0.1%
  Uptime: 99.99%

🔍 Diagnostic Summary:
  All systems operational
  No critical issues detected
  Performance within normal parameters
```

### 9. whoIStheGOAT
Programming wisdom easter egg revealing tech legends.

**Response varies**, example:
```
🐐 Excellence Analysis: Dennis Ritchie

🌟 Why Dennis Ritchie is the GOAT:

Dennis Ritchie created the C programming language and co-developed Unix, forming the foundation of modern computing. His work influences virtually every device and system today.

💡 Key Contributions:
• Created C (1972) - the language that built the world
• Co-created Unix with Ken Thompson
• Influenced all modern programming languages
• Enabled portable system software

📖 Wisdom: "The only way to learn a new programming language is by writing programs in it."

🎯 Legacy Impact: Every time you use a computer, phone, or any digital device, you're using technology built on Ritchie's foundations.

Humble, brilliant, and transformative - a true GOAT! 🙌
```

## API Reference

### POST /mcp
Main endpoint for JSON-RPC requests.

**Request Headers:**
- `Content-Type: application/json`
- `Accept: application/json, text/event-stream`
- `Mcp-Session-Id: <uuid>` (optional, passed through without state)
- `Authorization: Bearer <token>` (optional, analyzed by tools)

**Initialize Request:**
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

### GET /health
Simple health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "uptime": 3600,
  "requests_handled": 1000000,
  "version": "0.2.0"
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

### Load Balancer Testing

```nginx
upstream mcp_echo_stateless {
    # Perfect for round-robin
    server echo1:3000;
    server echo2:3000;
    server echo3:3000;
}

server {
    location /mcp {
        proxy_pass http://mcp_echo_stateless;
    }
}
```

## Docker Deployment

### Docker Compose Configuration

```yaml
services:
  mcp-echo-stateless:
    build: ./mcp-echo-streamablehttp-server-stateless
    environment:
      - MCP_ECHO_HOST=0.0.0.0
      - MCP_ECHO_PORT=3000
      - MCP_ECHO_DEBUG=false
      - MCP_PROTOCOL_VERSION=2025-06-18
      - ECHO_STATELESS_WORKERS=4
      - ECHO_STATELESS_LOG_LEVEL=INFO
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
      - "traefik.http.services.mcp-echo-stateless.loadbalancer.healthcheck.path=/health"
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-echo-stateless
spec:
  replicas: 3  # Easy horizontal scaling
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
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 2
          periodSeconds: 5
```

## Performance & Scaling

### Performance Characteristics

- **Memory**: < 50MB base per instance
- **CPU**: < 0.1 cores idle, I/O bound under load
- **Startup**: < 2 seconds
- **Shutdown**: Immediate
- **Request Overhead**: < 1ms
- **Latency p50**: < 1ms
- **Latency p99**: < 5ms
- **Throughput**: > 5000 requests/sec (single instance)

### Resource Usage

- **Memory**: Constant ~50MB (no growth)
- **CPU**: Scales linearly with requests
- **Network**: Efficient async I/O
- **Disk**: Minimal (logs only)

### Scaling Capabilities

- **Horizontal**: Unlimited instances
- **Vertical**: Single-threaded per worker
- **Load Balancing**: Any algorithm works
- **State**: None - perfect for auto-scaling
- **Concurrent Requests**: Limited only by resources

### Benchmarks

```bash
# Using wrk for load testing
wrk -t12 -c400 -d30s --script=mcp_echo.lua http://localhost:3000/mcp

# Results (example)
Requests/sec: 15,234.56
Latency:      25.43ms avg
Throughput:   45.2MB/s

# Using Apache Bench
ab -n 10000 -c 100 \
  -p request.json \
  -T application/json \
  http://localhost:3000/mcp
```

## Use Cases

### 1. Production Health Checks

```yaml
# In production services
healthcheck:
  test: |
    curl -X POST http://mcp-echo-stateless:3000/mcp \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"healthProbe"},"id":1}'
  interval: 30s
```

### 2. Protocol Debugging
- Verify MCP protocol implementation
- Test client/server handshake
- Debug message formatting
- Validate protocol versions

### 3. Authentication Testing
- Decode JWT tokens safely
- Verify auth header propagation
- Test ForwardAuth integration
- Debug OAuth flows

### 4. Gateway Integration Testing

```python
# Test gateway without state concerns
async def test_gateway_auth():
    # Any instance will do
    response = await client.post(
        "https://echo.example.com/mcp",
        headers={"Authorization": f"Bearer {token}"},
        json=echo_request
    )
    assert response.status_code == 200
```

### 5. Performance Benchmarking
- Establish baseline performance
- Test infrastructure limits
- Measure gateway overhead
- Validate scaling strategies

### 6. CORS Troubleshooting
- Analyze CORS requirements
- Debug preflight requests
- Verify header propagation

## Monitoring & Troubleshooting

### Monitoring Endpoints

```python
# Prometheus metrics exposed
mcp_echo_requests_total
mcp_echo_request_duration_seconds
mcp_echo_errors_total
mcp_echo_active_requests
```

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
- Review resource allocation

#### Health check failures
- Verify /health endpoint accessible
- Check container resource limits
- Review error logs
- Ensure proper startup time

### Debug Mode

```bash
# Maximum verbosity
export MCP_ECHO_DEBUG=true
export LOG_LEVEL=DEBUG
export PYTHONDEBUG=1

python -m mcp_echo_streamablehttp_server_stateless
```

### Troubleshooting Script

```python
# Quick diagnostic script
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

## Security Considerations

### Important Warnings

1. **No Token Verification**: `bearerDecode` does NOT verify JWT signatures
2. **No Built-in Authentication**: Service has no auth mechanisms
3. **Information Disclosure**: Tools reveal system information
4. **Debug Only**: Not for production secrets handling
5. **Stateless Nature**: Cannot track or limit per-user requests

### Best Practices

1. **Always use behind Traefik**: Never expose directly to internet
2. **Limit access**: Use IP allowlists in production
3. **Sanitize logs**: Don't log sensitive data
4. **Monitor usage**: Track who uses debug tools
5. **Rotate tokens**: Debug tokens should be short-lived
6. **Network isolation**: Run in isolated network segments
7. **Resource limits**: Prevent DoS with proper limits

### Security Hardening

```yaml
# Example security configuration
services:
  mcp-echo-stateless:
    # ... other config ...
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

## Comparison with Stateful Version

| Feature | Stateless | Stateful |
|---------|-----------|----------|
| Session persistence | ❌ None | ✅ Session-based |
| Message queuing | ❌ No | ✅ Yes |
| State accumulation | ❌ No | ✅ Yes |
| Replay capability | ❌ No | ✅ Yes (replayLastEcho) |
| Session tracking | ⚠️ ID only | ✅ Full state |
| Horizontal scaling | ✅ Excellent | ❌ Limited |
| Load balancing | ✅ Any algorithm | ⚠️ Sticky sessions |
| Resource usage | ✅ Low (~50MB) | ⚠️ Higher (grows) |
| Memory growth | ✅ None | ⚠️ With sessions |
| Use case | Production/Testing | Development/Debug |
| Complexity | ✅ Simple | ⚠️ Higher |

### When to Use Stateless

- Production diagnostics and health checks
- High-scale deployments
- Load balanced environments
- Minimal resource footprint required
- Gateway integration testing
- Performance benchmarking

### When to Use Stateful

- Development and debugging
- Testing OAuth flows with continuity
- Complex multi-request scenarios
- Session-based testing
- State accumulation needed
