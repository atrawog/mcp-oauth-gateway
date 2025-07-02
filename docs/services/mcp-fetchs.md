# mcp-fetchs Service

A native StreamableHTTP web fetching service that directly implements the MCP protocol without stdio bridging.

## Overview

The `mcp-fetchs` service provides web content fetching capabilities through a native StreamableHTTP implementation. Unlike the proxy-based `mcp-fetch`, this service directly implements the MCP protocol over HTTP, offering better performance and native async support without subprocess overhead.

## Architecture

```
┌─────────────────────────────────────────┐
│        mcp-fetchs Container             │
├─────────────────────────────────────────┤
│   mcp-fetch-streamablehttp-server       │
│        (Native Python + FastAPI)        │
│            Port 3000                    │
│                                         │
│   Direct HTTP/WebSocket Implementation  │
│        No stdio subprocess              │
└─────────────────────────────────────────┘
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_FILE` | Log file path | `/logs/server.log` |
| `HOST` | Bind address | `0.0.0.0` |
| `PORT` | Service port | `3000` |
| `MCP_SERVER_NAME` | Server identification | `mcp-fetch-streamablehttp` |
| `MCP_SERVER_VERSION` | Server version | `0.1.0` |
| `MCP_PROTOCOL_VERSION` | MCP protocol version | `2025-06-18` |
| `MCP_FETCH_DEFAULT_USER_AGENT` | HTTP user agent | `ModelContextProtocol/1.0 (Fetch Server)` |
| `MCP_CORS_ORIGINS` | Allowed CORS origins | `*` |

## Native StreamableHTTP Benefits

### Performance Advantages

1. **No subprocess overhead**: Direct HTTP handling
2. **Native async**: Full async/await support with FastAPI
3. **Connection pooling**: Efficient HTTP client management
4. **WebSocket ready**: Native bidirectional communication

### Implementation Features

- Built with FastAPI and Uvicorn
- Native Python asyncio support
- Direct protocol implementation
- Efficient memory usage
- Better error handling

## Available Tools

The mcp-fetchs service provides these native fetch tools:

### fetch_url

Fetches content from a URL with advanced options.

**Parameters:**
- `url` (string, required): The URL to fetch
- `method` (string, optional): HTTP method (GET, POST, etc.)
- `headers` (object, optional): Custom HTTP headers
- `body` (string, optional): Request body for POST/PUT
- `timeout` (number, optional): Request timeout in seconds
- `follow_redirects` (boolean, optional): Follow HTTP redirects
- `max_redirects` (number, optional): Maximum redirect count

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetch_url",
    "arguments": {
      "url": "https://api.example.com/data",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer token123"
      },
      "body": "{\"query\": \"test\"}",
      "timeout": 30
    }
  },
  "id": 1
}
```

### fetch_binary

Fetches binary content (images, files, etc.).

**Parameters:**
- `url` (string, required): The URL to fetch
- `encoding` (string, optional): Output encoding ("base64", "hex")

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetch_binary",
    "arguments": {
      "url": "https://example.com/image.png",
      "encoding": "base64"
    }
  },
  "id": 2
}
```

### fetch_batch

Fetches multiple URLs concurrently.

**Parameters:**
- `urls` (array, required): Array of URLs to fetch
- `max_concurrent` (number, optional): Maximum concurrent requests

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetch_batch",
    "arguments": {
      "urls": [
        "https://api1.example.com/data",
        "https://api2.example.com/data",
        "https://api3.example.com/data"
      ],
      "max_concurrent": 3
    }
  },
  "id": 3
}
```

## Usage Examples

### Advanced HTTP Requests

```bash
# POST request with custom headers
curl -X POST https://mcp-fetchs.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "fetch_url",
      "arguments": {
        "url": "https://api.example.com/graphql",
        "method": "POST",
        "headers": {
          "Content-Type": "application/json",
          "X-API-Key": "secret123"
        },
        "body": "{\"query\": \"{ users { id name } }\"}"
      }
    },
    "id": 1
  }'
```

### Binary Content Handling

```python
import httpx
import base64
from PIL import Image
from io import BytesIO

async def fetch_and_process_image(mcp_url, token, image_url):
    async with httpx.AsyncClient() as client:
        # Fetch image as base64
        response = await client.post(
            f"{mcp_url}/mcp",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "fetch_binary",
                    "arguments": {
                        "url": image_url,
                        "encoding": "base64"
                    }
                },
                "id": 1
            }
        )

        # Decode and process
        result = response.json()
        image_data = base64.b64decode(result["result"]["content"])
        image = Image.open(BytesIO(image_data))

        return image
```

### Concurrent Fetching

```python
class BatchFetcher:
    def __init__(self, mcp_url, token):
        self.mcp_url = mcp_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def fetch_apis(self, api_endpoints):
        """Fetch multiple API endpoints concurrently"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.mcp_url}/mcp",
                headers=self.headers,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch_batch",
                        "arguments": {
                            "urls": api_endpoints,
                            "max_concurrent": 5
                        }
                    },
                    "id": 1
                }
            )

            results = response.json()["result"]["responses"]

            # Process results
            return {
                url: result["content"] if result["success"] else result["error"]
                for url, result in zip(api_endpoints, results)
            }
```

## Native Features

### Session Management

Native StreamableHTTP supports stateful sessions:

```python
class StatefulFetcher:
    def __init__(self, mcp_url, token):
        self.mcp_url = mcp_url
        self.token = token
        self.session_id = None

    async def initialize_session(self):
        """Initialize MCP session"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.mcp_url}/mcp",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "fetch-client",
                            "version": "1.0"
                        }
                    },
                    "id": 1
                }
            )

            # Extract session ID from headers
            if "Mcp-Session-Id" in response.headers:
                self.session_id = response.headers["Mcp-Session-Id"]

            return response.json()
```

### Error Handling

Native implementation provides detailed error information:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "field": "url",
      "reason": "Invalid URL format",
      "value": "not-a-url"
    }
  },
  "id": 1
}
```

## Performance Optimization

### Connection Pooling

The native implementation maintains HTTP connection pools:

```python
# Server automatically pools connections
# Configure via environment:
HTTPX_MAX_CONNECTIONS=100
HTTPX_MAX_KEEPALIVE_CONNECTIONS=20
```

### Concurrent Request Limits

```python
# Batch fetching with rate limiting
async def rate_limited_fetch(urls, max_per_second=10):
    batch_size = max_per_second
    results = []

    for i in range(0, len(urls), batch_size):
        batch = urls[i:i+batch_size]

        # Fetch batch
        batch_results = await fetch_batch(batch)
        results.extend(batch_results)

        # Rate limit
        if i + batch_size < len(urls):
            await asyncio.sleep(1)

    return results
```

## Health Monitoring

### Health Check

The service uses native StreamableHTTP protocol initialization:

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"${MCP_PROTOCOL_VERSION:-2025-06-18}\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
    | grep -q '\"protocolVersion\":\"${MCP_PROTOCOL_VERSION:-2025-06-18}\"'"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

### Metrics Endpoint

Native implementation may expose metrics:

```bash
# Check service metrics (if available)
curl https://mcp-fetchs.example.com/metrics

# Example metrics:
# - Request count
# - Response times
# - Error rates
# - Active connections
```

## Troubleshooting

### Connection Issues

1. Check service is running:
   ```bash
   curl http://localhost:3000/health
   ```

2. Verify protocol version:
   ```bash
   docker exec mcp-fetchs env | grep MCP_PROTOCOL_VERSION
   ```

### Performance Issues

1. Monitor connection pool:
   ```bash
   docker exec mcp-fetchs netstat -an | grep :3000 | wc -l
   ```

2. Check resource usage:
   ```bash
   docker stats mcp-fetchs
   ```

### Debug Mode

Enable debug logging:

```bash
# Set in docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG
  - UVICORN_LOG_LEVEL=debug
```

## Comparison with Proxy-based mcp-fetch

| Feature | mcp-fetchs (Native) | mcp-fetch (Proxy) |
|---------|-------------------|-------------------|
| Implementation | Direct HTTP | stdio subprocess |
| Performance | Higher | Lower (subprocess overhead) |
| Async Support | Native | Via proxy |
| Memory Usage | Lower | Higher |
| Protocol Version | 2025-06-18 | Configurable |
| Advanced Features | More HTTP options | Basic fetch |
| Debugging | Direct logs | Proxy + subprocess logs |

## Best Practices

### Request Configuration

1. **Set appropriate timeouts** for long-running requests
2. **Use batch fetching** for multiple URLs
3. **Handle redirects explicitly** when needed
4. **Include user agent** for API compatibility

### Error Handling

```python
async def safe_fetch(url, retry_count=3):
    for attempt in range(retry_count):
        try:
            result = await fetch_url(url)
            if result["success"]:
                return result["content"]
        except Exception as e:
            if attempt == retry_count - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Integration

### With Claude Desktop

Configure in Claude Desktop settings:

```json
{
  "mcpServers": {
    "fetchs": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--server-url", "https://mcp-fetchs.example.com/mcp",
        "--token", "Bearer YOUR_TOKEN_HERE"
      ]
    }
  }
}
```

### With Modern Web Frameworks

```typescript
// TypeScript/Next.js integration
class MCPFetchClient {
  private baseUrl: string;
  private token: string;

  constructor(baseUrl: string, token: string) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async fetchWithCache(url: string, cacheTime: number = 3600) {
    const cacheKey = `fetch:${url}`;

    // Check cache first
    const cached = await redis.get(cacheKey);
    if (cached) return JSON.parse(cached);

    // Fetch via MCP
    const response = await fetch(`${this.baseUrl}/mcp`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'tools/call',
        params: {
          name: 'fetch_url',
          arguments: { url }
        },
        id: 1
      })
    });

    const result = await response.json();

    // Cache result
    await redis.setex(cacheKey, cacheTime, JSON.stringify(result));

    return result;
  }
}
```
