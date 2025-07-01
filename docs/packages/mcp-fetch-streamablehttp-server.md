# mcp-fetch-streamablehttp-server

A native StreamableHTTP implementation providing secure web content fetching with built-in SSRF protection and content processing.

## Overview

`mcp-fetch-streamablehttp-server` is a native MCP service that implements the fetch protocol directly over StreamableHTTP. Unlike the proxy-wrapped version, this provides:

- Direct HTTP implementation (no stdio subprocess)
- Advanced SSRF (Server-Side Request Forgery) protection
- HTML to Markdown conversion
- Content extraction and processing
- Robot.txt compliance
- Configurable security policies

## Key Features

### Security First
- SSRF protection with URL validation
- Configurable domain allow/block lists
- Private IP range blocking
- DNS rebinding protection
- Maximum content size limits

### Content Processing
- HTML to clean Markdown conversion
- JavaScript rendering support (optional)
- Character encoding detection
- Content type validation
- Structured data extraction

### Native Implementation
- Pure Python/FastAPI implementation
- No subprocess overhead
- Direct StreamableHTTP protocol
- Efficient async processing

## Architecture

```python
# Core components
FetchServer           # Main FastAPI application
SecurityValidator     # SSRF and security checks
ContentProcessor      # HTML/content processing
MarkdownConverter     # HTML to Markdown
URLValidator          # URL parsing and validation
```

## Configuration

### Environment Variables

```bash
# Security settings
FETCH_MAX_SIZE=10485760  # 10MB default
FETCH_TIMEOUT=30
FETCH_USER_AGENT="MCP-Fetch-Server/1.0"

# SSRF protection
FETCH_ALLOW_PRIVATE_IPS=false
FETCH_ALLOWED_DOMAINS=example.com,api.example.com
FETCH_BLOCKED_DOMAINS=internal.local,admin.local

# Content processing
FETCH_ENABLE_JAVASCRIPT=false
FETCH_EXTRACT_METADATA=true
FETCH_FOLLOW_REDIRECTS=true
FETCH_MAX_REDIRECTS=5

# Server settings
FETCH_HOST=0.0.0.0
FETCH_PORT=3000
```

## API Implementation

### Tool: fetch_url

Fetches content from a URL with security validation.

**Parameters:**
- `url` (string, required): The URL to fetch
- `max_size` (integer, optional): Maximum content size
- `headers` (object, optional): Additional HTTP headers
- `follow_redirects` (boolean, optional): Follow HTTP redirects

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetch_url",
    "arguments": {
      "url": "https://example.com/page",
      "headers": {
        "Accept": "text/html"
      }
    }
  },
  "id": 1
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
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
  },
  "id": 1
}
```

## Security Features

### SSRF Protection Layers

1. **URL Validation**
```python
# Blocked patterns
- Private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Loopback addresses (127.0.0.0/8, ::1)
- Link-local addresses (169.254.0.0/16)
- Metadata endpoints (169.254.169.254)
```

2. **DNS Resolution Check**
```python
# Resolve hostname before request
# Verify resolved IP is not private
# Prevent DNS rebinding attacks
```

3. **Domain Filtering**
```python
# Allow/block list enforcement
if allowed_domains and domain not in allowed_domains:
    raise SecurityError("Domain not in allowlist")
if blocked_domains and domain in blocked_domains:
    raise SecurityError("Domain is blocked")
```

### Request Security

```python
# Timeout enforcement
timeout = min(user_timeout, FETCH_TIMEOUT)

# Size limits
response.raise_for_status()
if int(response.headers.get('content-length', 0)) > max_size:
    raise ValueError("Content too large")

# Content type validation
if not content_type.startswith(('text/', 'application/')):
    raise ValueError("Unsupported content type")
```

## Content Processing

### HTML to Markdown Pipeline

1. **Parse HTML**
```python
soup = BeautifulSoup(html, 'html.parser')
# Remove script and style tags
# Clean up attributes
# Preserve semantic structure
```

2. **Convert to Markdown**
```python
# Headers → # Markdown headers
# Links → [text](url)
# Images → ![alt](src)
# Lists → Markdown lists
# Code → ``` blocks
```

3. **Extract Metadata**
```python
metadata = {
    "title": soup.find('title').text,
    "description": meta_description,
    "keywords": meta_keywords,
    "author": meta_author
}
```

## Deployment

### Docker Configuration

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install package
COPY pyproject.toml .
RUN pip install .

# Run server
CMD ["python", "-m", "mcp_fetch_streamablehttp_server"]

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
```

### Docker Compose

```yaml
services:
  mcp-fetchs:
    build: ./mcp-fetchs
    environment:
      - FETCH_ALLOWED_DOMAINS=${ALLOWED_DOMAINS}
      - FETCH_MAX_SIZE=10485760
      - FETCH_ENABLE_JAVASCRIPT=false
    ports:
      - "3003:3000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
```

## Advanced Usage

### JavaScript Rendering

When `FETCH_ENABLE_JAVASCRIPT=true`:

```python
# Uses Playwright for rendering
browser = await playwright.chromium.launch()
page = await browser.new_page()
await page.goto(url)
content = await page.content()
```

### Custom Headers

```json
{
  "arguments": {
    "url": "https://api.example.com/data",
    "headers": {
      "Authorization": "Bearer token",
      "Accept": "application/json"
    }
  }
}
```

### Following Redirects

```json
{
  "arguments": {
    "url": "https://short.link/abc",
    "follow_redirects": true,
    "max_redirects": 10
  }
}
```

## Error Handling

### Security Errors

| Error | Cause | Solution |
|-------|-------|----------|
| SSRF_BLOCKED | Private IP detected | Use public URLs only |
| DOMAIN_BLOCKED | Domain in blocklist | Check allowed domains |
| DNS_REBINDING | IP changed after check | Retry or investigate |

### Fetch Errors

| Error | Cause | Solution |
|-------|-------|----------|
| TIMEOUT | Request took too long | Increase timeout or check site |
| TOO_LARGE | Content exceeds limit | Increase max_size or chunk |
| INVALID_CONTENT | Unsupported type | Check content-type header |

## Performance Optimization

### Caching
```python
# Response caching (optional)
cache = {}
cache_key = hashlib.sha256(url.encode()).hexdigest()
if cache_key in cache:
    return cache[cache_key]
```

### Connection Pooling
```python
# Reuse HTTP connections
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

### Streaming Large Content
```python
# Stream processing for large files
async for chunk in response.aiter_bytes():
    process_chunk(chunk)
```

## Monitoring

### Health Endpoint

```http
GET /health

{
  "status": "healthy",
  "version": "0.1.4",
  "requests_total": 1234,
  "requests_failed": 12,
  "average_response_time": 1.23
}
```

### Metrics

- Request count and latency
- Security blocks by type
- Content type distribution
- Error rates by category

## Testing

```bash
# Test fetch functionality
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "fetch_url",
      "arguments": {
        "url": "https://example.com"
      }
    },
    "id": 1
  }'
```

## Security Best Practices

1. **Always use SSRF protection** in production
2. **Configure domain allowlists** for sensitive environments
3. **Set appropriate size limits** based on use case
4. **Monitor blocked requests** for security insights
5. **Regularly update security rules** based on threats

## Troubleshooting

### SSRF Blocks Legitimate URLs
- Check if URL resolves to private IP
- Verify domain allowlist configuration
- Enable debug logging for details

### Content Processing Fails
- Check content-type header
- Verify encoding detection
- Review HTML structure for issues

### Performance Issues
- Enable connection pooling
- Implement response caching
- Tune timeout and size limits
