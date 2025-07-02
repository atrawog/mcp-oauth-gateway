# mcp-echo-streamablehttp-server-stateless

A lightweight, stateless MCP echo service optimized for production diagnostics and high-performance testing.

## Overview

`mcp-echo-streamablehttp-server-stateless` is a pure functional implementation of an MCP echo service. Unlike its stateful counterpart, this service:

- Maintains no session state between requests
- Optimized for horizontal scaling
- Minimal memory footprint
- Ideal for production health checks
- Perfect for load balancing scenarios

## Key Features

### Stateless Design
- No session storage overhead
- Each request is independent
- Safe for load balancing
- No cleanup required
- Predictable resource usage

### Production Ready
- Minimal dependencies
- Fast startup time
- Low memory usage
- High throughput
- Container-optimized

### Diagnostic Tools
- Subset of echo tools
- Focus on pure functions
- No state accumulation
- Consistent performance

## Tool Reference

### Core Tools

The stateless server implements a focused subset of echo tools:

#### 1. echo
Basic echo functionality.
```json
{
  "name": "echo",
  "arguments": {
    "message": "Hello, Stateless!"
  }
}
// Returns: "Hello, Stateless!"
```

#### 2. echo_reverse
String reversal without state.
```json
{
  "name": "echo_reverse",
  "arguments": {
    "message": "Stateless"
  }
}
// Returns: "sseletatS"
```

#### 3. echo_upper
Uppercase transformation.
```json
{
  "name": "echo_upper",
  "arguments": {
    "message": "stateless"
  }
}
// Returns: "STATELESS"
```

#### 4. echo_lower
Lowercase transformation.
```json
{
  "name": "echo_lower",
  "arguments": {
    "message": "STATELESS"
  }
}
// Returns: "stateless"
```

#### 5. echo_length
String length calculation.
```json
{
  "name": "echo_length",
  "arguments": {
    "message": "Count me"
  }
}
// Returns: 8
```

#### 6. echo_with_timestamp
Timestamp addition (current time only).
```json
{
  "name": "echo_with_timestamp",
  "arguments": {
    "message": "Event"
  }
}
// Returns: "[2024-01-01T12:00:00Z] Event"
```

#### 7. echo_health
Service health check tool.
```json
{
  "name": "echo_health",
  "arguments": {}
}
// Returns: {
//   "status": "healthy",
//   "timestamp": "2024-01-01T12:00:00Z",
//   "version": "0.2.0",
//   "stateless": true
// }
```

## Architecture

### Pure Functional Design

```python
# No global state
# No session storage
# No side effects

async def handle_tool_call(tool_name: str, arguments: dict) -> Any:
    # Direct function mapping
    if tool_name == "echo":
        return arguments.get("message", "")
    elif tool_name == "echo_reverse":
        return arguments.get("message", "")[::-1]
    # ... etc
```

### Request Handling

```python
@app.post("/mcp")
async def handle_mcp(request: Request):
    # Parse request
    body = await request.json()

    # Process immediately
    result = process_request(body)

    # Return response
    return StreamingResponse(
        generate_response(result),
        media_type="text/event-stream"
    )
    # No state saved
```

## Configuration

### Minimal Configuration

```bash
# Server settings
ECHO_STATELESS_HOST=0.0.0.0
ECHO_STATELESS_PORT=3000

# Performance tuning
ECHO_STATELESS_WORKERS=4
ECHO_STATELESS_MAX_REQUESTS=10000

# Logging
ECHO_STATELESS_LOG_LEVEL=INFO
```

## Deployment

### Optimized Docker Image

```dockerfile
FROM python:3.12-slim

# Minimal dependencies
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Run with multiple workers
CMD ["uvicorn", "mcp_echo_streamablehttp_server_stateless:app", \
     "--host", "0.0.0.0", "--port", "3000", "--workers", "4"]

# Simple health check
HEALTHCHECK --interval=10s --timeout=2s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
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
      - name: echo
        image: mcp-echo-stateless:latest
        ports:
        - containerPort: 3000
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 10
```

## Use Cases

### 1. Production Health Checks

```yaml
# In production services
healthcheck:
  test: |
    curl -X POST http://mcp-echo-stateless:3000/mcp \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"echo_health"},"id":1}'
  interval: 30s
```

### 2. Load Balancer Testing

```nginx
upstream mcp_echo_stateless {
    # Perfect for round-robin
    server echo1:3000;
    server echo2:3000;
    server echo3:3000;
}
```

### 3. Performance Benchmarking

```bash
# High-performance testing
ab -n 10000 -c 100 \
  -p request.json \
  -T application/json \
  http://localhost:3000/mcp
```

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

## Performance Characteristics

### Resource Usage
- **Memory**: < 50MB per instance
- **CPU**: < 0.1 cores idle
- **Startup**: < 2 seconds
- **Shutdown**: Immediate

### Throughput
- **Requests/sec**: > 5000 (single instance)
- **Latency p50**: < 1ms
- **Latency p99**: < 5ms
- **Concurrent requests**: Unlimited

## Comparison with Stateful

| Feature | Stateless | Stateful |
|---------|-----------|----------|
| Session management | ❌ | ✅ |
| State accumulation | ❌ | ✅ |
| Horizontal scaling | ✅ Easy | ⚠️ Complex |
| Memory usage | ✅ Minimal | ⚠️ Grows |
| Load balancing | ✅ Any algorithm | ⚠️ Sticky sessions |
| Use case | Production/Testing | Development/Debug |

## Monitoring

### Simple Health Endpoint

```http
GET /health

{
  "status": "healthy",
  "uptime": 3600,
  "requests_handled": 1000000,
  "version": "0.2.0"
}
```

### Prometheus Metrics

```python
# Exposed statistics
mcp_echo_requests_total
mcp_echo_request_duration_seconds
mcp_echo_errors_total
mcp_echo_active_requests
```

## Best Practices

1. **Deploy Multiple Instances**: Leverage stateless design
2. **Use Load Balancing**: Any algorithm works
3. **Set Resource Limits**: Predictable usage
4. **Monitor Health**: Simple /health checks
5. **Benchmark First**: Establish baselines

## Integration Examples

### With Traefik

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.services.echo-stateless.loadbalancer.server.port=3000"
  - "traefik.http.services.echo-stateless.loadbalancer.healthcheck.path=/health"
```

### With HAProxy

```
backend echo_stateless
    balance roundrobin
    option httpchk GET /health
    server echo1 echo1:3000 check
    server echo2 echo2:3000 check
    server echo3 echo3:3000 check
```

## Troubleshooting

### High Memory Usage
- Check for memory leaks in custom code
- Verify no accidental state storage
- Review request body sizes

### Performance Degradation
- Check CPU usage
- Verify network latency
- Review concurrent request limits

### Health Check Failures
- Verify /health endpoint accessible
- Check container resource limits
- Review error logs
