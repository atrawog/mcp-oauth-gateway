# mcp-everything Service

A comprehensive multi-tool service that wraps `mcp-server-everything` using the proxy pattern, with special streaming support.

## Overview

The `mcp-everything` service provides a collection of various tools through the MCP protocol. It uses `mcp-streamablehttp-proxy` to wrap the stdio-based everything server, making it accessible via HTTP with OAuth authentication. This service includes special middleware for Server-Sent Events (SSE) and streaming support.

## Architecture

```
┌─────────────────────────────────────────┐
│       mcp-everything Container          │
├─────────────────────────────────────────┤
│   mcp-streamablehttp-proxy (Port 3000)  │
│              ↓ spawns ↓                 │
│       mcp-server-everything             │
│         (stdio subprocess)              │
└─────────────────────────────────────────┘
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_FILE` | Log file path | `/logs/server.log` |
| `MCP_CORS_ORIGINS` | Allowed CORS origins | `*` |
| `MCP_PROTOCOL_VERSION` | MCP protocol version | `2025-06-18` (configurable) |

### Special Middleware Configuration

The service includes special headers for streaming support:

```yaml
# Disable buffering for SSE
- "traefik.http.middlewares.mcp-everything-streaming.headers.customresponseheaders.X-Accel-Buffering=no"
# Prevent caching of event streams
- "traefik.http.middlewares.mcp-everything-streaming.headers.customresponseheaders.Cache-Control=no-cache"
# Keep connection alive
- "traefik.http.middlewares.mcp-everything-streaming.headers.customresponseheaders.Connection=keep-alive"
```

## Available Tools

The mcp-everything service provides a comprehensive collection of tools. The exact tools depend on the version of mcp-server-everything installed, but typically include:

### System Tools
- File operations
- Process management
- System information
- Network utilities

### Data Tools
- JSON manipulation
- Text processing
- Data transformation
- Encoding/decoding

### Utility Tools
- Random generation
- Hash functions
- Time operations
- Math calculations

### Integration Tools
- HTTP requests
- API interactions
- Database queries
- Message queuing

## Streaming Support

This service is specifically configured for streaming responses, making it ideal for:

### Real-time Data Streams

```bash
# Stream data with SSE support
curl -N -X POST https://mcp-everything.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "stream_data",
      "arguments": {
        "source": "realtime_feed"
      }
    },
    "id": 1
  }'
```

### Long-running Operations

```bash
# Execute long-running task with progress updates
curl -N -X POST https://mcp-everything.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "process_large_dataset",
      "arguments": {
        "dataset": "analytics_2024",
        "stream_progress": true
      }
    },
    "id": 2
  }'
```

## Usage Examples

### Tool Discovery

First, discover available tools:

```bash
curl -X POST https://mcp-everything.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 1
  }'
```

### Example Tool Calls

```bash
# Example: Generate random data
curl -X POST https://mcp-everything.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "generate_random",
      "arguments": {
        "type": "uuid",
        "count": 5
      }
    },
    "id": 2
  }'

# Example: Process JSON data
curl -X POST https://mcp-everything.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "json_transform",
      "arguments": {
        "data": {"name": "test", "value": 123},
        "transform": "flatten"
      }
    },
    "id": 3
  }'
```

## Health Monitoring

### Health Check

The service uses StreamableHTTP protocol initialization for health checks:

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"${MCP_PROTOCOL_VERSION:-2025-06-18}\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
    | grep -q '\"protocolVersion\":\"'"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

### Monitoring

```bash
# View logs
just logs mcp-everything

# Follow logs with streaming events
just logs -f mcp-everything | grep -E "(stream|SSE|event)"

# Monitor active connections
docker exec mcp-everything netstat -an | grep :3000
```

## Streaming Client Examples

### JavaScript/TypeScript EventSource

```javascript
const evtSource = new EventSource(
  'https://mcp-everything.example.com/mcp',
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);

evtSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

evtSource.onerror = (error) => {
  console.error('Stream error:', error);
};

// Send streaming request
fetch('https://mcp-everything.example.com/mcp', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream'
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/call',
    params: {
      name: 'stream_tool',
      arguments: { stream: true }
    },
    id: 1
  })
});
```

### Python Streaming Client

```python
import httpx
import json

async def stream_mcp_data(url, token, tool_name, arguments):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 1
    }

    async with httpx.AsyncClient() as client:
        async with client.stream(
            'POST',
            f"{url}/mcp",
            headers=headers,
            json=payload,
            timeout=None
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    yield data

# Usage
async for event in stream_mcp_data(
    "https://mcp-everything.example.com",
    "your_token",
    "monitor_system",
    {"metrics": ["cpu", "memory", "disk"]}
):
    print(f"Metric update: {event}")
```

## Performance Tuning

### Streaming Optimization

1. **Connection Pooling**
   ```yaml
   deploy:
     replicas: 3  # Scale for concurrent streams
   ```

2. **Buffer Settings**
   - X-Accel-Buffering: no (already configured)
   - Ensures real-time delivery

3. **Timeout Configuration**
   - No timeout for streaming connections
   - Client-side handling recommended

## Troubleshooting

### Streaming Not Working

1. Check middleware is applied:
   ```bash
   docker compose logs traefik | grep mcp-everything-streaming
   ```

2. Verify headers:
   ```bash
   curl -I https://mcp-everything.example.com/mcp \
     -H "Authorization: Bearer $TOKEN"
   # Should show: X-Accel-Buffering: no
   ```

### Connection Drops

1. Check keep-alive settings:
   ```bash
   # Verify Connection: keep-alive header
   curl -v https://mcp-everything.example.com/mcp \
     -H "Authorization: Bearer $TOKEN" \
     2>&1 | grep Connection
   ```

2. Monitor proxy stability:
   ```bash
   just logs mcp-everything | grep -i "connection\|timeout"
   ```

### Tool Discovery Issues

1. List available tools:
   ```bash
   docker exec mcp-everything mcp-server-everything --list-tools
   ```

2. Check server version:
   ```bash
   docker exec mcp-everything pip show mcp-server-everything
   ```

## Best Practices

### Streaming Usage

1. **Use streaming for**:
   - Real-time monitoring
   - Progress updates
   - Large data transfers
   - Live log tailing

2. **Avoid streaming for**:
   - Simple request/response
   - Small data payloads
   - Infrequent updates

### Resource Management

1. **Connection limits**: Set reasonable client connection limits
2. **Timeout handling**: Implement client-side timeout logic
3. **Error recovery**: Automatic reconnection for streams
4. **Backpressure**: Handle slow clients appropriately

## Integration

### With Claude Desktop

Configure in Claude Desktop settings:

```json
{
  "mcpServers": {
    "everything": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--server-url", "https://mcp-everything.example.com/mcp",
        "--token", "Bearer YOUR_TOKEN_HERE"
      ]
    }
  }
}
```

### With Streaming Applications

```python
import asyncio
import httpx
import json

class MCPEverythingStream:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    async def stream_tool(self, tool_name, arguments, callback):
        """Execute a tool and stream results"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                'POST',
                f"{self.base_url}/mcp",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    },
                    "id": 1
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            await callback(data)
                        except json.JSONDecodeError:
                            continue

# Usage
stream = MCPEverythingStream("https://mcp-everything.example.com", "token")

async def handle_event(data):
    print(f"Received: {data}")

await stream.stream_tool(
    "monitor_logs",
    {"service": "web-app", "follow": True},
    handle_event
)
```
