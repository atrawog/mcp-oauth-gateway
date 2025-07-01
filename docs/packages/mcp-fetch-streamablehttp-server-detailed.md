# mcp-fetch-streamablehttp-server

## Overview

The `mcp-fetch-streamablehttp-server` is a native Python implementation of an MCP server that provides secure URL fetching capabilities through the StreamableHTTP transport. Unlike proxy-based solutions, this server implements the MCP protocol directly, offering better performance and tighter integration with the HTTP transport layer.

## Architecture

### Native Implementation Benefits

```
┌──────────────┐    Direct HTTP    ┌─────────────────────┐
│  MCP Client  │ ←──────────────→ │  Fetch Server       │
│  (HTTP)      │    No bridging    │  (Native HTTP)      │
└──────────────┘                   └─────────────────────┘
```

Key advantages over proxy pattern:
- No subprocess overhead
- Direct HTTP implementation
- Better performance
- Simpler deployment
- Native async support

### Core Components

```
mcp_fetch_streamablehttp_server/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point
├── server.py            # FastAPI application
├── transport.py         # StreamableHTTP implementation
├── fetch_handler.py     # Fetch tool implementation
├── security.py          # Security validations
└── config.py            # Configuration management
```

## Key Features

### Secure Fetching
- **SSRF Protection**: Blocks internal networks and cloud metadata
- **Size Limits**: Configurable response size limits
- **Scheme Restrictions**: Only http/https by default
- **Robots.txt Compliance**: Respects site crawling rules
- **Timeout Controls**: Prevents hanging requests

### Native StreamableHTTP
- Direct protocol implementation
- No stdio translation needed
- Full async/await support
- Efficient streaming responses
- SSE support ready

### Stateless Operation
- No session persistence
- Horizontal scaling ready
- Container-friendly
- Easy load balancing

## Installation

### Using pip
```bash
pip install mcp-fetch-streamablehttp-server
```

### Using pixi
```bash
pixi add --pypi mcp-fetch-streamablehttp-server
```

### Docker
```dockerfile
FROM python:3.11-slim

RUN pip install mcp-fetch-streamablehttp-server

ENV MCP_SERVER_NAME=mcp-fetch
ENV MCP_SERVER_VERSION=1.0.0
ENV MCP_PROTOCOL_VERSION=2025-06-18
ENV HOST=0.0.0.0
ENV PORT=3000

EXPOSE 3000

CMD ["python", "-m", "mcp_fetch_streamablehttp_server"]
```

## Configuration

### Environment Variables

```bash
# Required
MCP_SERVER_NAME=mcp-fetch
MCP_SERVER_VERSION=1.0.0
MCP_PROTOCOL_VERSION=2025-06-18

# Server Configuration
HOST=0.0.0.0               # Bind address
PORT=3000                  # Server port

# Fetch Configuration
MCP_FETCH_ALLOWED_SCHEMES=["http","https"]
MCP_FETCH_MAX_SIZE=100000  # 100KB default
MCP_FETCH_TIMEOUT=30       # 30 seconds
MCP_FETCH_MAX_REDIRECTS=5
MCP_FETCH_DEFAULT_USER_AGENT=ModelContextProtocol/1.0
MCP_FETCH_BLOCK_PRIVATE_IPS=true
MCP_FETCH_ROBOTS_TXT_CACHE_SIZE=1000

# Optional Features
MCP_FETCH_ENABLE_COOKIES=false
MCP_FETCH_VERIFY_SSL=true
```

### Docker Compose Configuration

```yaml
services:
  mcp-fetchs:
    build: ./mcp-fetch-streamablehttp-server
    environment:
      - MCP_SERVER_NAME=mcp-fetch
      - MCP_SERVER_VERSION=1.0.0
      - MCP_PROTOCOL_VERSION=2025-06-18
      - HOST=0.0.0.0
      - PORT=3000
      - MCP_FETCH_MAX_SIZE=200000
      - MCP_FETCH_TIMEOUT=60
    networks:
      - internal
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/mcp",
             "-X", "POST", "-H", "Content-Type: application/json",
             "-d", '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}']
      interval: 30s
      timeout: 5s
      retries: 3
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mcp-fetchs.rule=Host(`mcp-fetchs.${BASE_DOMAIN}`)"
      - "traefik.http.routers.mcp-fetchs.priority=2"
      - "traefik.http.routers.mcp-fetchs.middlewares=mcp-auth"
      - "traefik.http.services.mcp-fetchs.loadbalancer.server.port=3000"
```

## API Reference

### StreamableHTTP Endpoints

#### POST /mcp
Main endpoint for JSON-RPC requests.

**Request Headers**:
- `Content-Type: application/json`
- `Accept: application/json, text/event-stream`
- `Mcp-Session-Id: <uuid>` (optional)

**Response Types**:
- JSON for single responses
- Server-Sent Events for streaming

#### GET /mcp
SSE endpoint for pending messages (infrastructure ready).

#### DELETE /mcp
Session termination endpoint (infrastructure ready).

### MCP Protocol Methods

#### initialize
Establishes protocol version and capabilities.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {
      "name": "example-client",
      "version": "1.0"
    }
  },
  "id": 1
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2025-06-18",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "mcp-fetch",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

#### tools/list
Returns available tools.

**Response**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "fetch",
        "description": "Fetches content from a URL",
        "inputSchema": {
          "type": "object",
          "properties": {
            "url": {
              "type": "string",
              "description": "URL to fetch"
            },
            "method": {
              "type": "string",
              "enum": ["GET", "POST"],
              "default": "GET"
            },
            "headers": {
              "type": "object",
              "description": "HTTP headers"
            },
            "body": {
              "type": "string",
              "description": "Request body for POST"
            },
            "max_length": {
              "type": "integer",
              "description": "Maximum response length",
              "default": 100000
            }
          },
          "required": ["url"]
        }
      }
    ]
  },
  "id": 2
}
```

#### tools/call
Executes the fetch tool.

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://api.example.com/data",
      "method": "GET",
      "headers": {
        "Accept": "application/json",
        "User-Agent": "MCP-Client/1.0"
      },
      "max_length": 50000
    }
  },
  "id": 3
}
```

## Fetch Tool Details

### Security Features

#### SSRF Protection
Blocks requests to:
- Localhost (127.0.0.1, ::1)
- Private networks (10.x, 172.16-31.x, 192.168.x)
- Link-local (169.254.x)
- Cloud metadata services:
  - AWS: 169.254.169.254
  - GCP: metadata.google.internal
  - Azure: 169.254.169.254
  - DigitalOcean: 169.254.169.254

#### Request Validation
```python
def validate_url(url: str) -> bool:
    """Comprehensive URL validation."""
    # Check scheme
    if urlparse(url).scheme not in allowed_schemes:
        raise ValueError("Unsupported URL scheme")

    # Resolve hostname
    hostname = urlparse(url).hostname
    ip = socket.gethostbyname(hostname)

    # Check if private IP
    if is_private_ip(ip):
        raise ValueError("Access to private IPs blocked")

    # Check against blocklist
    if hostname in blocked_hosts:
        raise ValueError("Host is blocked")

    return True
```

### Response Handling

#### Content Types

**Text Content**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "<html>...</html>"
    }
  ]
}
```

**JSON Content**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"data\": \"value\"}"
    }
  ]
}
```

**Image Content**:
```json
{
  "content": [
    {
      "type": "image",
      "data": "base64-encoded-image-data",
      "mimeType": "image/png"
    }
  ]
}
```

**Error Response**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "Error: Connection timeout after 30 seconds"
    }
  ],
  "isError": true
}
```

### Advanced Features

#### Robots.txt Compliance
```python
async def check_robots_txt(url: str, user_agent: str) -> bool:
    """Check if URL is allowed by robots.txt."""
    # Cache robots.txt content
    robots_url = get_robots_url(url)

    if robots_url in robots_cache:
        parser = robots_cache[robots_url]
    else:
        # Fetch and parse robots.txt
        parser = await fetch_and_parse_robots(robots_url)
        robots_cache[robots_url] = parser

    return parser.can_fetch(user_agent, url)
```

#### Smart Content Detection
```python
def detect_content_type(response: httpx.Response) -> str:
    """Intelligently detect content type."""
    # Check Content-Type header
    content_type = response.headers.get('content-type', '')

    # Parse media type
    media_type = content_type.split(';')[0].strip()

    # Map to MCP content types
    if media_type.startswith('image/'):
        return 'image'
    elif media_type == 'application/json':
        return 'json'
    else:
        return 'text'
```

## Usage Examples

### Basic Fetch

```bash
# Using curl
curl -X POST https://mcp-fetchs.yourdomain.com/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "fetch",
      "arguments": {
        "url": "https://api.github.com/repos/modelcontextprotocol/servers"
      }
    },
    "id": 1
  }'
```

### Fetch with Headers

```python
import httpx
import asyncio

async def fetch_with_auth():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://mcp-fetchs.yourdomain.com/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "fetch",
                    "arguments": {
                        "url": "https://api.example.com/protected",
                        "headers": {
                            "Authorization": "Bearer API_TOKEN",
                            "Accept": "application/json"
                        }
                    }
                },
                "id": 1
            },
            headers={
                "Authorization": "Bearer MCP_TOKEN"
            }
        )
        return response.json()

asyncio.run(fetch_with_auth())
```

### POST Request

```javascript
const response = await fetch('https://mcp-fetchs.yourdomain.com/mcp', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/call',
    params: {
      name: 'fetch',
      arguments: {
        url: 'https://httpbin.org/post',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ data: 'test' })
      }
    },
    id: 1
  })
});
```

## Error Handling

### Common Errors

#### SSRF Blocked
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "error": "URL points to private IP address"
    }
  },
  "id": 1
}
```

#### Size Limit Exceeded
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [{
      "type": "text",
      "text": "Error: Response size (150000) exceeds limit (100000)"
    }],
    "isError": true
  },
  "id": 1
}
```

#### Timeout
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [{
      "type": "text",
      "text": "Error: Request timeout after 30 seconds"
    }],
    "isError": true
  },
  "id": 1
}
```

## Performance Optimization

### Connection Pooling
```python
# HTTP client with connection pooling
http_client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100,
        keepalive_expiry=30.0
    ),
    timeout=httpx.Timeout(
        connect=5.0,
        read=30.0,
        write=10.0,
        pool=5.0
    )
)
```

### Caching Strategy
- Robots.txt cached with LRU eviction
- DNS results cached by system
- No content caching (stateless)

### Resource Limits
- Max response size prevents memory exhaustion
- Timeout prevents hanging connections
- Connection limits prevent resource starvation

## Security Best Practices

### Input Validation
1. **URL Validation**: Comprehensive checks before fetching
2. **Header Filtering**: Remove dangerous headers
3. **Body Size Limits**: Prevent large POST bodies
4. **Content Type Validation**: Verify response types

### Network Security
1. **SSRF Protection**: Block internal networks
2. **DNS Rebinding**: Resolve and validate IPs
3. **Redirect Following**: Limited and validated
4. **SSL Verification**: Enabled by default

### Response Sanitization
1. **Size Enforcement**: Truncate large responses
2. **Content Filtering**: Remove scripts from HTML
3. **Header Stripping**: Remove sensitive headers
4. **Error Sanitization**: Don't leak internal details

## Deployment Considerations

### Container Security
```dockerfile
# Run as non-root user
FROM python:3.11-slim
RUN useradd -m -s /bin/bash mcp
USER mcp

# Security headers
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
```

### Resource Requirements
- **Memory**: 128MB minimum, 256MB recommended
- **CPU**: 0.1 vCPU minimum, 0.5 vCPU recommended
- **Network**: Outbound HTTPS required
- **Storage**: Minimal (no persistence)

### Scaling Strategy
```yaml
services:
  mcp-fetchs:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 256M
          cpus: '0.5'
        reservations:
          memory: 128M
          cpus: '0.1'
```

## Monitoring and Debugging

### Health Checks
```python
@app.get("/health")
async def health_check():
    """Comprehensive health check."""
    try:
        # Check HTTP client
        await http_client.get("https://httpbin.org/status/200")

        # Check configuration
        assert settings.mcp_server_name
        assert settings.mcp_protocol_version

        return {"status": "healthy"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )
```

### Logging
```python
import structlog

logger = structlog.get_logger()

# Log fetch requests
logger.info(
    "fetch_request",
    url=url,
    method=method,
    size_limit=max_length,
    user_agent=user_agent
)

# Log security events
logger.warning(
    "ssrf_blocked",
    url=url,
    resolved_ip=ip,
    reason="private_ip"
)
```

### Metrics to Track
- Request count by URL domain
- Response times percentiles
- Error rates by type
- Size limit violations
- SSRF blocks

## Testing

### Unit Tests
```python
import pytest
from mcp_fetch_streamablehttp_server import validate_url

def test_ssrf_protection():
    """Test SSRF protection."""
    # Should block localhost
    with pytest.raises(ValueError):
        validate_url("http://localhost/admin")

    # Should block private IPs
    with pytest.raises(ValueError):
        validate_url("http://192.168.1.1/")

    # Should allow public URLs
    assert validate_url("https://example.com/")
```

### Integration Tests
```python
async def test_fetch_tool():
    """Test fetch tool end-to-end."""
    async with AsyncClient(app=app) as client:
        # Initialize
        init_response = await client.post("/mcp", json={
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            },
            "id": 1
        })

        # Fetch content
        fetch_response = await client.post("/mcp", json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "fetch",
                "arguments": {
                    "url": "https://httpbin.org/json"
                }
            },
            "id": 2
        })

        assert fetch_response.status_code == 200
        result = fetch_response.json()
        assert "error" not in result
```

## Troubleshooting

### Common Issues

#### "URL points to private IP"
- Check if target URL resolves to private IP
- May be DNS rebinding attempt
- Verify URL is publicly accessible

#### "Response size exceeds limit"
- Increase MCP_FETCH_MAX_SIZE
- Consider pagination if API supports it
- Use HEAD request first to check size

#### "Connection timeout"
- Increase MCP_FETCH_TIMEOUT
- Check if target server is responsive
- May be network connectivity issue

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export MCP_FETCH_DEBUG=true
python -m mcp_fetch_streamablehttp_server
```

## Best Practices

1. **Set Appropriate Limits**: Balance functionality and security
2. **Monitor Usage**: Track which URLs are fetched
3. **Update Regularly**: Keep security rules current
4. **Test Security**: Regularly test SSRF protection
5. **Document APIs**: Help users understand limitations
6. **Handle Errors Gracefully**: Provide helpful error messages

## Limitations

1. **No JavaScript Execution**: Can't fetch SPA content
2. **No Authentication Storage**: Stateless operation
3. **Size Limits**: Large files need different approach
4. **No Caching**: Each request fetches fresh
5. **Limited Content Types**: Mainly text/JSON/images

## Future Enhancements

- [ ] Playwright integration for JavaScript sites
- [ ] Streaming response support
- [ ] Content caching layer
- [ ] Request queuing and rate limiting
- [ ] Custom security rule configuration
- [ ] Webhook support for async fetching
- [ ] Content extraction tools
