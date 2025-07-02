# mcp-echo-stateless Service

A stateless echo service that natively implements the StreamableHTTP protocol without session persistence.

## Overview

The `mcp-echo-stateless` service is a native StreamableHTTP implementation that provides simple echo functionality without maintaining any session state. Each request is handled independently, making it ideal for testing basic MCP connectivity, OAuth authentication flows, and debugging without the complexity of session management.

## Architecture

```
┌─────────────────────────────────────────┐
│    mcp-echo-stateless Container         │
├─────────────────────────────────────────┤
│ mcp-echo-streamablehttp-server-stateless│
│        (Native Python + FastAPI)        │
│            Port 3000                    │
│                                         │
│   ┌─────────────────────────────┐      │
│   │    Stateless Processing     │      │
│   │  - No session storage       │      │
│   │  - Independent requests     │      │
│   │  - Pure functional design   │      │
│   └─────────────────────────────┘      │
└─────────────────────────────────────────┘
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_FILE` | Log file path | `/logs/server.log` |
| `HOST` | Bind address | `0.0.0.0` |
| `PORT` | Service port | `3000` |
| `MCP_SERVER_NAME` | Server identification | `mcp-echo-streamablehttp-stateless` |
| `MCP_SERVER_VERSION` | Server version | `0.1.0` |
| `MCP_PROTOCOL_VERSION` | MCP protocol version | `2025-06-18` |
| `DEBUG` | Enable debug mode | `true` |

### Multi-Subdomain Support

The service supports multiple subdomains for testing different instances:
- `echo-stateless0.example.com` through `echo-stateless9.example.com`
- Each subdomain is completely independent
- No shared state between requests or instances

## Available Tools

### echo

Echo back the input without any state tracking.

**Parameters:**
- `message` (string, required): Message to echo
- `uppercase` (boolean, optional): Convert to uppercase
- `reverse` (boolean, optional): Reverse the message
- `repeat` (number, optional): Number of times to repeat (max: 10)
- `format` (string, optional): Response format ("plain", "json", "xml")

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "echo",
    "arguments": {
      "message": "Hello, stateless world!",
      "uppercase": true,
      "repeat": 3
    }
  },
  "id": 1
}
```

### ping

Simple connectivity test.

**Parameters:** None

**Returns:**
- Timestamp
- Service version
- Protocol version

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "ping",
    "arguments": {}
  },
  "id": 2
}
```

### echo_headers

Echo back request headers for debugging.

**Parameters:**
- `include_auth` (boolean, optional): Include authorization header (redacted)

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "echo_headers",
    "arguments": {
      "include_auth": true
    }
  },
  "id": 3
}
```

### echo_json

Echo back JSON data with optional transformations.

**Parameters:**
- `data` (object, required): JSON data to echo
- `pretty` (boolean, optional): Pretty print the JSON
- `sort_keys` (boolean, optional): Sort object keys

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "echo_json",
    "arguments": {
      "data": {"name": "test", "values": [1, 2, 3]},
      "pretty": true,
      "sort_keys": true
    }
  },
  "id": 4
}
```

## Usage Examples

### Basic Echo Operations

```bash
# Simple echo
curl -X POST https://echo-stateless.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {
        "message": "Test message"
      }
    },
    "id": 1
  }'

# Echo with transformations
curl -X POST https://echo-stateless.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {
        "message": "hello world",
        "uppercase": true,
        "reverse": true,
        "repeat": 2
      }
    },
    "id": 2
  }'
```

### Connectivity Testing

```python
import httpx
import asyncio

class ConnectivityTester:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def test_endpoints(self, endpoints):
        """Test multiple echo endpoints"""
        async with httpx.AsyncClient() as client:
            tasks = []

            for endpoint in endpoints:
                task = client.post(
                    f"{endpoint}/mcp",
                    headers=self.headers,
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "ping",
                            "arguments": {}
                        },
                        "id": 1
                    },
                    timeout=5
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            return [
                {
                    "endpoint": endpoint,
                    "success": not isinstance(result, Exception),
                    "response_time": result.elapsed.total_seconds() if not isinstance(result, Exception) else None,
                    "error": str(result) if isinstance(result, Exception) else None
                }
                for endpoint, result in zip(endpoints, results)
            ]

# Test multiple instances
tester = ConnectivityTester("", token)
endpoints = [f"https://echo-stateless{i}.example.com" for i in range(10)]
results = await tester.test_endpoints(endpoints)
```

### OAuth Flow Testing

```bash
# Test OAuth authentication without session complexity
# 1. Attempt without token (should fail)
curl -X POST https://echo-stateless.example.com/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "ping",
      "arguments": {}
    },
    "id": 1
  }'
# Expected: 401 Unauthorized

# 2. Test with valid token
curl -X POST https://echo-stateless.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "echo_headers",
      "arguments": {"include_auth": true}
    },
    "id": 2
  }'
# Expected: 200 OK with headers
```

### Debug Header Echo

```python
async def debug_request_headers():
    """Debug OAuth and routing headers"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://echo-stateless.example.com/mcp",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Custom-Header": "test-value"
            },
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "echo_headers",
                    "arguments": {"include_auth": true}
                },
                "id": 1
            }
        )

        result = response.json()
        headers = result["result"]["headers"]

        print("Request headers received by service:")
        for key, value in headers.items():
            if key.lower() == "authorization":
                print(f"  {key}: Bearer ***REDACTED***")
            else:
                print(f"  {key}: {value}")
```

## Testing Patterns

### Load Testing

```python
import asyncio
import time

async def load_test(requests_per_second=100, duration_seconds=60):
    """Load test the stateless service"""
    start_time = time.time()
    request_count = 0
    errors = 0

    async def send_request():
        nonlocal request_count, errors
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://echo-stateless.example.com/mcp",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "echo",
                            "arguments": {
                                "message": f"Load test {request_count}"
                            }
                        },
                        "id": request_count
                    },
                    timeout=5
                )
                request_count += 1
        except Exception:
            errors += 1

    # Send requests at specified rate
    while time.time() - start_time < duration_seconds:
        batch_start = time.time()

        # Send batch of requests
        tasks = [send_request() for _ in range(requests_per_second)]
        await asyncio.gather(*tasks)

        # Wait for next second
        elapsed = time.time() - batch_start
        if elapsed < 1:
            await asyncio.sleep(1 - elapsed)

    return {
        "total_requests": request_count,
        "errors": errors,
        "success_rate": (request_count - errors) / request_count * 100,
        "actual_rps": request_count / duration_seconds
    }
```

### Multi-Instance Round-Robin

```bash
#!/bin/bash
# Test round-robin across multiple instances

INSTANCES=10
REQUESTS=100
TOKEN="your_token_here"

for ((i=1; i<=REQUESTS; i++)); do
    INSTANCE=$((i % INSTANCES))

    echo "Request $i to echo-stateless$INSTANCE"

    curl -s -X POST "https://echo-stateless$INSTANCE.example.com/mcp" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"jsonrpc\": \"2.0\",
            \"method\": \"tools/call\",
            \"params\": {
                \"name\": \"echo\",
                \"arguments\": {
                    \"message\": \"Request $i to instance $INSTANCE\"
                }
            },
            \"id\": $i
        }" | jq -r '.result.content'
done
```

## Comparison with Stateful Service

| Feature | echo-stateless | echo-stateful |
|---------|----------------|---------------|
| Session Management | None | Full session support |
| Memory Usage | Minimal | Higher (stores state) |
| Scalability | Excellent | Good (with affinity) |
| Use Case | Testing, debugging | Stateful workflows |
| Request Isolation | Complete | Session-based |
| Performance | Higher | Lower (state overhead) |

## Health Monitoring

### Health Check

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-06-18\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
    | grep -q '\"protocolVersion\":\"2025-06-18\"'"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

### Performance Monitoring

```bash
# Monitor response times
while true; do
    START=$(date +%s%N)

    curl -s -X POST https://echo-stateless.example.com/mcp \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"ping","arguments":{}},"id":1}' \
        > /dev/null

    END=$(date +%s%N)
    DURATION=$((($END - $START) / 1000000))

    echo "Response time: ${DURATION}ms"
    sleep 1
done
```

## Best Practices

### When to Use Stateless

1. **API Testing**: Simple request/response validation
2. **Load Testing**: No session overhead
3. **Debugging**: Isolate authentication issues
4. **Health Checks**: Lightweight connectivity tests
5. **Demos**: Simple functionality demonstration

### Performance Optimization

1. **No State Overhead**: Each request is independent
2. **Horizontal Scaling**: Add instances freely
3. **Caching**: Responses can be cached (identical inputs)
4. **Load Balancing**: No session affinity needed

## Troubleshooting

### No Response

1. Check authentication:
   ```bash
   curl -I https://echo-stateless.example.com/mcp \
     -H "Authorization: Bearer $TOKEN"
   ```

2. Verify service is running:
   ```bash
   curl http://localhost:3000/health
   ```

### Debugging Requests

Enable debug mode for detailed logs:
```bash
# Check debug output
docker logs mcp-echo-stateless | grep DEBUG

# Follow logs during request
just logs -f mcp-echo-stateless
```

## Integration

### With Claude Desktop

```json
{
  "mcpServers": {
    "echo-stateless": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--server-url", "https://echo-stateless.example.com/mcp",
        "--token", "Bearer YOUR_TOKEN_HERE"
      ]
    }
  }
}
```

### Simple Test Client

```python
class EchoStatelessClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def echo(self, message, **options):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                headers=self.headers,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "echo",
                        "arguments": {
                            "message": message,
                            **options
                        }
                    },
                    "id": 1
                }
            )
            return response.json()["result"]["content"]

# Usage
client = EchoStatelessClient("https://echo-stateless.example.com", token)
result = await client.echo("Hello", uppercase=True, repeat=3)
print(result)  # "HELLO HELLO HELLO"
```
