# mcp-fetch-streamablehttp-server

A native StreamableHTTP implementation providing secure web content fetching with built-in SSRF protection, content processing, and direct MCP protocol support.

## Quick Start

**Key Features:**
- Direct HTTP implementation without stdio subprocess overhead
- Advanced SSRF protection with configurable security policies
- HTML to Markdown conversion and content extraction
- Robot.txt compliance and request validation
- Native async support with efficient streaming

**Installation:**
```bash
pip install mcp-fetch-streamablehttp-server
# or
pixi add --pypi mcp-fetch-streamablehttp-server
```

**Basic Usage:**
```bash
# Start the server
python -m mcp_fetch_streamablehttp_server

# Test fetch functionality
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"fetch","arguments":{"url":"https://example.com"}},"id":1}'
```

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [API Reference](#api-reference)
6. [Fetch Tool Details](#fetch-tool-details)
7. [Security Features](#security-features)
8. [Content Processing](#content-processing)
9. [Usage Examples](#usage-examples)
10. [Docker Deployment](#docker-deployment)
11. [Performance Optimization](#performance-optimization)
12. [Monitoring & Debugging](#monitoring--debugging)
13. [Troubleshooting](#troubleshooting)
14. [Best Practices](#best-practices)

## Overview

`mcp-fetch-streamablehttp-server` is a native Python implementation of an MCP server that provides secure URL fetching capabilities through the StreamableHTTP transport. Unlike proxy-based solutions, this server implements the MCP protocol directly, offering:

- Better performance through native implementation
- Tighter integration with HTTP transport layer
- Advanced security features including SSRF protection
- Content processing and format conversion
- Stateless operation for easy scaling

## Architecture

### Native Implementation Benefits

```
┌──────────────┐    Direct HTTP    ┌─────────────────────┐
│  MCP Client  │ ←──────────────→  │  Fetch Server       │
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
├── content.py           # Content processing
└── config.py            # Configuration management
```

## Installation

### Using pip
```bash
pip install mcp-fetch-streamablehttp-server
```

### Using pixi
```bash
pixi add --pypi mcp-fetch-streamablehttp-server
```

### Docker Installation
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install package
RUN pip install mcp-fetch-streamablehttp-server

# Configure
ENV MCP_SERVER_NAME=mcp-fetch
ENV MCP_SERVER_VERSION=1.0.0
ENV MCP_PROTOCOL_VERSION=2025-06-18
ENV HOST=0.0.0.0
ENV PORT=3000

EXPOSE 3000

CMD ["python", "-m", "mcp_fetch_streamablehttp_server"]

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
```

## Configuration

### Environment Variables

```bash
# Required MCP Configuration
MCP_SERVER_NAME=mcp-fetch
MCP_SERVER_VERSION=1.0.0
MCP_PROTOCOL_VERSION=2025-06-18

# Server Configuration
HOST=0.0.0.0               # Bind address
PORT=3000                  # Server port

# Security Settings
FETCH_MAX_SIZE=10485760    # 10MB default
FETCH_TIMEOUT=30           # Request timeout in seconds
FETCH_USER_AGENT="MCP-Fetch-Server/1.0"
FETCH_ALLOW_PRIVATE_IPS=false  # Block private networks

# SSRF Protection
FETCH_ALLOWED_DOMAINS=example.com,api.example.com  # Comma-separated
FETCH_BLOCKED_DOMAINS=internal.local,admin.local   # Comma-separated
MCP_FETCH_ALLOWED_SCHEMES=["http","https"]
MCP_FETCH_BLOCK_PRIVATE_IPS=true

# Content Processing
FETCH_ENABLE_JAVASCRIPT=false   # JavaScript rendering (requires Playwright)
FETCH_EXTRACT_METADATA=true     # Extract page metadata
FETCH_FOLLOW_REDIRECTS=true     # Follow HTTP redirects
FETCH_MAX_REDIRECTS=5          # Maximum redirect hops
MCP_FETCH_ROBOTS_TXT_CACHE_SIZE=1000

# Optional Features
MCP_FETCH_ENABLE_COOKIES=false
MCP_FETCH_VERIFY_SSL=true
```

## API Reference

### StreamableHTTP Endpoints

#### POST /mcp
Main endpoint for JSON-RPC requests.

**Request Headers:**
- `Content-Type: application/json`
- `Accept: application/json, text/event-stream`
- `Mcp-Session-Id: <uuid>` (optional)

**Response Types:**
- JSON for single responses
- Server-Sent Events for streaming

#### GET /mcp
SSE endpoint for pending messages (infrastructure ready).

#### DELETE /mcp
Session termination endpoint (infrastructure ready).

### MCP Protocol Methods

#### initialize
Establishes protocol version and capabilities.

**Request:**
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

**Response:**
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

**Response:**
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

**Request:**
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

### Tool Parameters

The `fetch` tool accepts the following parameters:

- `url` (string, required): The URL to fetch
- `method` (string, optional): HTTP method - "GET" or "POST" (default: "GET")
- `headers` (object, optional): Additional HTTP headers
- `body` (string, optional): Request body for POST requests
- `max_length` (integer, optional): Maximum content size (default: 100000)
- `follow_redirects` (boolean, optional): Follow HTTP redirects
- `max_redirects` (integer, optional): Maximum redirect count

### Response Format

**Text/HTML Content:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "# Page Title\n\nContent in markdown format..."
    }
  ],
  "metadata": {
    "status_code": 200,
    "content_type": "text/html",
    "encoding": "utf-8",
    "final_url": "https://example.com/page",
    "title": "Page Title"
  }
}
```

**JSON Content:**
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

**Image Content:**
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

**Error Response:**
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

## Security Features

### SSRF Protection Layers

1. **URL Validation**
   - Blocked IP ranges:
     - Private networks: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
     - Loopback: 127.0.0.0/8, ::1
     - Link-local: 169.254.0.0/16
     - Cloud metadata: 169.254.169.254

2. **DNS Resolution Check**
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

3. **Domain Filtering**
   - Allow/block list enforcement
   - Configurable via environment variables
   - Prevents access to internal services

### Request Security

- **Timeout enforcement**: Prevents hanging requests
- **Size limits**: Prevents memory exhaustion
- **Content type validation**: Only safe content types
- **Header filtering**: Removes dangerous headers
- **SSL verification**: Enabled by default

### Cloud Metadata Protection

Blocks access to cloud provider metadata endpoints:
- AWS: 169.254.169.254
- GCP: metadata.google.internal
- Azure: 169.254.169.254
- DigitalOcean: 169.254.169.254

## Content Processing

### HTML to Markdown Pipeline

1. **Parse HTML**
   ```python
   soup = BeautifulSoup(html, 'html.parser')
   # Remove script and style tags
   for tag in soup(['script', 'style']):
       tag.decompose()
   # Clean up attributes
   # Preserve semantic structure
   ```

2. **Convert to Markdown**
   - Headers → # Markdown headers
   - Links → [text](url)
   - Images → ![alt](src)
   - Lists → Markdown lists
   - Code → ``` blocks
   - Tables → Markdown tables

3. **Extract Metadata**
   ```python
   metadata = {
       "title": soup.find('title').text,
       "description": meta_description,
       "keywords": meta_keywords,
       "author": meta_author,
       "encoding": detected_encoding
   }
   ```

### Content Type Detection

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

### Robots.txt Compliance

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

## Usage Examples

### Basic Fetch

```bash
# Using curl
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "fetch",
      "arguments": {
        "url": "https://example.com"
      }
    },
    "id": 1
  }'
```

### Fetch with Authentication

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

### Custom Headers and Size Limit

```python
response = await client.post("/mcp", json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "fetch",
        "arguments": {
            "url": "https://api.example.com/large-data",
            "headers": {
                "Accept": "application/json",
                "X-API-Key": "secret"
            },
            "max_length": 1048576  # 1MB limit
        }
    },
    "id": 1
})
```

## Docker Deployment

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
      - FETCH_ALLOWED_DOMAINS=${ALLOWED_DOMAINS}
      - FETCH_MAX_SIZE=10485760
      - FETCH_TIMEOUT=60
      - FETCH_ENABLE_JAVASCRIPT=false
      - MCP_FETCH_BLOCK_PRIVATE_IPS=true
    networks:
      - internal
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/mcp",
             "-X", "POST", "-H", "Content-Type: application/json",
             "-d", '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}']
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 40s
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mcp-fetchs.rule=Host(`mcp-fetchs.${BASE_DOMAIN}`)"
      - "traefik.http.routers.mcp-fetchs.priority=2"
      - "traefik.http.routers.mcp-fetchs.middlewares=mcp-auth"
      - "traefik.http.services.mcp-fetchs.loadbalancer.server.port=3000"
```

### Production Dockerfile

```dockerfile
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -s /bin/bash mcp
USER mcp

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Security headers
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Configure for production
ENV MCP_SERVER_NAME=mcp-fetch
ENV MCP_SERVER_VERSION=1.0.0
ENV MCP_PROTOCOL_VERSION=2025-06-18
ENV HOST=0.0.0.0
ENV PORT=3000

CMD ["python", "-m", "mcp_fetch_streamablehttp_server"]

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
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

- **Robots.txt caching**: LRU cache with configurable size
- **DNS caching**: System-level DNS cache
- **No content caching**: Maintains stateless operation
- **Connection reuse**: HTTP keep-alive enabled

### Streaming Large Content

```python
# Stream processing for large files
async for chunk in response.aiter_bytes():
    process_chunk(chunk)
    if total_size > max_size:
        break
```

### JavaScript Rendering

When `FETCH_ENABLE_JAVASCRIPT=true`:

```python
# Uses Playwright for rendering
browser = await playwright.chromium.launch()
page = await browser.new_page()
await page.goto(url)
await page.wait_for_load_state('networkidle')
content = await page.content()
```

## Monitoring & Debugging

### Health Endpoint

```http
GET /health

{
  "status": "healthy",
  "version": "0.1.4",
  "requests_total": 1234,
  "requests_failed": 12,
  "average_response_time": 1.23,
  "ssrf_blocks": 5,
  "active_connections": 3
}
```

### Metrics to Track

- Request count by URL domain
- Response time percentiles
- Error rates by type
- Size limit violations
- SSRF blocks by reason
- Content type distribution
- Cache hit rates

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

# Log errors
logger.error(
    "fetch_failed",
    url=url,
    error=str(e),
    status_code=response.status_code
)
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export MCP_FETCH_DEBUG=true
python -m mcp_fetch_streamablehttp_server
```

## Troubleshooting

### Common Issues

#### "URL points to private IP"
- **Cause**: Target URL resolves to private IP address
- **Solution**:
  - Verify URL is publicly accessible
  - Check for DNS rebinding
  - Use public URLs only

#### "Response size exceeds limit"
- **Cause**: Content larger than configured limit
- **Solution**:
  - Increase `MCP_FETCH_MAX_SIZE`
  - Consider pagination if API supports it
  - Use HEAD request first to check size

#### "Connection timeout"
- **Cause**: Request took longer than timeout
- **Solution**:
  - Increase `MCP_FETCH_TIMEOUT`
  - Check target server responsiveness
  - Verify network connectivity

#### "Unsupported URL scheme"
- **Cause**: URL uses scheme other than http/https
- **Solution**:
  - Use http or https URLs only
  - Check `MCP_FETCH_ALLOWED_SCHEMES` config

### Error Response Examples

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

## Best Practices

### Security
1. **Always enable SSRF protection** in production
2. **Configure domain allowlists** for sensitive environments
3. **Set appropriate size limits** based on use case
4. **Monitor blocked requests** for security insights
5. **Regularly update security rules** based on threats
6. **Use HTTPS only** in production environments

### Performance
1. **Enable connection pooling** for better performance
2. **Set reasonable timeouts** to prevent hanging
3. **Use appropriate size limits** to prevent OOM
4. **Monitor resource usage** and scale accordingly
5. **Consider caching** for frequently accessed content

### Operations
1. **Use health checks** for container orchestration
2. **Enable structured logging** for better debugging
3. **Monitor error rates** and response times
4. **Document API limitations** clearly
5. **Test SSRF protection** regularly
6. **Keep dependencies updated** for security

### Error Handling
1. **Provide clear error messages** to users
2. **Don't leak internal details** in errors
3. **Log errors with context** for debugging
4. **Handle edge cases** gracefully
5. **Test error scenarios** thoroughly

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

    # Should block cloud metadata
    with pytest.raises(ValueError):
        validate_url("http://169.254.169.254/")

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

### Security Tests
```python
async def test_security_blocks():
    """Test security blocking."""
    # Test private IP blocking
    response = await client.post("/mcp", json={
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "fetch",
            "arguments": {"url": "http://192.168.1.1/"}
        },
        "id": 1
    })

    assert "error" in response.json()
    assert "private IP" in response.json()["error"]["message"]
```

## Limitations

1. **No JavaScript Execution**: By default, can't fetch SPA content (enable with `FETCH_ENABLE_JAVASCRIPT`)
2. **No Authentication Storage**: Stateless operation means no credential persistence
3. **Size Limits**: Large files need appropriate configuration
4. **No Built-in Caching**: Each request fetches fresh content
5. **Limited Content Types**: Primarily text, JSON, and images
6. **No WebSocket Support**: HTTP/HTTPS only
7. **Single Request Model**: No batch fetching
