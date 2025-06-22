# MCP Fetch Service

The MCP Fetch service provides comprehensive web content retrieval capabilities, enabling AI systems and applications to access and process web content through a secure, authenticated interface.

```{image} https://img.shields.io/badge/Status-Production%20Ready-green
:alt: Production Ready
```
```{image} https://img.shields.io/badge/Protocol-MCP-blue
:alt: MCP Protocol
```
```{image} https://img.shields.io/badge/Version-Dynamic-green
:alt: Protocol Version
```

## Overview

MCP Fetch bridges the gap between AI systems and web content, providing secure, rate-limited, and authenticated access to web resources. It supports various content types, handles redirects, and provides robust error handling for production use.

## 🚀 Capabilities

### Web Content Retrieval
- **HTTP/HTTPS Requests** - GET, POST, PUT, DELETE support
- **Content Types** - HTML, JSON, XML, plain text, binary data
- **Header Management** - Custom headers, user agents, authentication
- **Redirect Handling** - Automatic redirect following with limits

### Security Features
- **URL Validation** - Prevents SSRF and malicious requests
- **Rate Limiting** - Configurable request rate limits
- **Timeout Control** - Request timeout management
- **Content Size Limits** - Prevents excessive memory usage

### Content Processing
- **Encoding Detection** - Automatic charset detection
- **HTML Parsing** - Extract text, links, metadata
- **JSON Processing** - Parse and validate JSON responses
- **Error Handling** - Graceful handling of network errors

## 🛠️ Tools

The MCP Fetch service provides a comprehensive `fetch` tool:

### fetch Tool

Retrieve content from web URLs with comprehensive options.

**Parameters:**
- `url` (string, required) - The URL to fetch
- `method` (string, optional) - HTTP method (default: GET)
- `headers` (object, optional) - Custom HTTP headers
- `body` (string, optional) - Request body for POST/PUT
- `timeout` (number, optional) - Request timeout in seconds
- `follow_redirects` (boolean, optional) - Follow redirects (default: true)
- `max_redirects` (number, optional) - Maximum redirect count

**Response Format:**
```json
{
  "url": "https://example.com",
  "status_code": 200,
  "headers": {
    "content-type": "text/html; charset=utf-8",
    "content-length": "1234"
  },
  "content": "<html>...</html>",
  "encoding": "utf-8",
  "final_url": "https://example.com",
  "redirect_count": 0
}
```

## 📝 Usage Examples

### Basic Web Content Retrieval

```bash
# Using mcp-streamablehttp-client
mcp-streamablehttp-client \\
  --server-url https://mcp-fetch.yourdomain.com/mcp \\
  --command "fetch url='https://httpbin.org/json'"
```

```json
{
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://httpbin.org/json"
    }
  }
}
```

### Advanced Request with Headers

```json
{
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://api.example.com/data",
      "method": "GET",
      "headers": {
        "User-Agent": "MCP-Fetch/1.0",
        "Accept": "application/json"
      },
      "timeout": 30
    }
  }
}
```

### POST Request with Body

```json
{
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://httpbin.org/post",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json"
      },
      "body": "{\"key\": \"value\"}"
    }
  }
}
```

## 🏗️ Architecture

### Service Components

```{mermaid}
graph TB
    subgraph "MCP Fetch Container"
        A[mcp-fetch-streamablehttp-server] --> B[HTTP Client]
        B --> C[Content Processor]
        C --> D[Response Formatter]
    end
    
    subgraph "Infrastructure"
        E[Traefik Router] --> F[OAuth Middleware]
        F --> A
        G[Health Checks] --> A
    end
    
    subgraph "External Web"
        H[Web Servers] 
        I[APIs]
        J[Content Sources]
    end
    
    B --> H
    B --> I
    B --> J
```

### Security Architecture

The fetch service implements multiple security layers:

1. **OAuth Authentication** - All requests require valid Bearer tokens
2. **URL Validation** - Prevents SSRF attacks and localhost access
3. **Rate Limiting** - Configurable request limits per client
4. **Content Limits** - Maximum response size enforcement
5. **Timeout Controls** - Prevents hanging requests

## ⚙️ Configuration

### Environment Variables

```bash
# Protocol configuration
MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION:-2025-06-18}
MCP_CORS_ORIGINS=*
PORT=3000

# Request limits
MAX_CONTENT_SIZE=10485760  # 10MB
REQUEST_TIMEOUT=30         # 30 seconds
MAX_REDIRECTS=5           # Maximum redirects

# Rate limiting
RATE_LIMIT_REQUESTS=100   # Requests per minute
RATE_LIMIT_WINDOW=60      # Window in seconds
```

### Docker Configuration

```yaml
services:
  mcp-fetch:
    build:
      context: ../
      dockerfile: mcp-fetch/Dockerfile
    environment:
      - MCP_CORS_ORIGINS=*
      - MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION:-2025-06-18}
      - MAX_CONTENT_SIZE=10485760
    labels:
      # Traefik routing configuration
      - "traefik.http.routers.mcp-fetch.rule=Host(`mcp-fetch.${BASE_DOMAIN}`)"
      - "traefik.http.routers.mcp-fetch.middlewares=mcp-auth"
```

## 🧪 Testing

The MCP Fetch service includes comprehensive testing:

### Test Categories

1. **Protocol Compliance** - MCP protocol validation
2. **Authentication** - OAuth token validation
3. **Fetch Operations** - HTTP request functionality
4. **Error Handling** - Network and protocol errors
5. **Security** - URL validation and limits
6. **Performance** - Load and stress testing

### Running Tests

```bash
# All fetch tests
just test-file tests/test_mcp_fetch_*

# Integration tests
pytest tests/test_mcp_fetch_integration.py -v

# Comprehensive functionality tests  
pytest tests/test_mcp_fetch_complete.py -v

# Real content tests
pytest tests/test_mcp_fetch_real_content.py -v
```

### Test Results

✅ **Protocol Compliance** - MCP protocol verified  
✅ **Authentication** - OAuth 2.1 integration working  
✅ **HTTP Operations** - All methods (GET, POST, PUT, DELETE) tested  
✅ **Content Types** - HTML, JSON, XML, binary content supported  
✅ **Error Handling** - Network errors handled gracefully  
✅ **Security** - URL validation and limits enforced  

## 🔍 Monitoring

### Health Checks

```bash
# Protocol health check via MCP initialization
curl -X POST https://mcp-fetch.yourdomain.com/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"'"${MCP_PROTOCOL_VERSION:-2025-06-18}"'","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'
```

### Metrics

The service provides metrics for:
- **Request Count** - Total HTTP requests processed
- **Response Times** - Average and percentile response times  
- **Error Rates** - HTTP and network error percentages
- **Content Sizes** - Average and maximum content sizes

### Logging

Logs are structured JSON format:

```json
{
  "timestamp": "2025-06-21T23:38:12Z",
  "level": "INFO",
  "service": "mcp-fetch",
  "request_id": "req-123",
  "url": "https://example.com",
  "method": "GET",
  "status_code": 200,
  "response_time_ms": 150,
  "content_size": 1234
}
```

## 🚨 Error Handling

### Common Error Responses

```json
{
  "error": {
    "code": -32602,
    "message": "Invalid URL format",
    "data": {
      "url": "invalid-url",
      "validation_error": "Missing scheme"
    }
  }
}
```

### Error Categories

1. **URL Validation Errors**
   - Invalid URL format
   - Prohibited schemes (file://, localhost)
   - Malformed URLs

2. **Network Errors**
   - Connection timeouts
   - DNS resolution failures
   - SSL certificate errors

3. **HTTP Errors**
   - 4xx client errors
   - 5xx server errors
   - Redirect loops

4. **Content Errors**
   - Content too large
   - Encoding issues
   - Parsing failures

## 🎯 Use Cases

### Web Scraping
- **Content Analysis** - Extract text and metadata from web pages
- **Data Collection** - Gather structured data from APIs
- **Monitoring** - Check website status and changes

### API Integration
- **REST APIs** - Interact with RESTful web services
- **Webhooks** - Receive and process webhook notifications
- **Data Synchronization** - Sync data between systems

### Content Processing
- **Document Retrieval** - Fetch documents for processing
- **Image Analysis** - Retrieve images for AI analysis
- **Feed Processing** - Process RSS/Atom feeds

## 🔧 Troubleshooting

### Common Issues

1. **Connection Timeouts**
   ```bash
   # Check network connectivity
   curl -I https://target-url.com
   
   # Increase timeout
   # Set REQUEST_TIMEOUT environment variable
   ```

2. **URL Validation Failures**
   ```bash
   # Ensure URL is properly formatted
   # Check for prohibited schemes or hosts
   ```

3. **Content Size Limits**
   ```bash
   # Check content size
   curl -I https://target-url.com | grep content-length
   
   # Adjust MAX_CONTENT_SIZE if needed
   ```

### Debug Commands

```bash
# Service logs
docker logs mcp-fetch

# Test fetch functionality
mcp-streamablehttp-client \\
  --server-url https://mcp-fetch.yourdomain.com/mcp \\
  --command "fetch url='https://httpbin.org/status/200'"

# Protocol health check
curl -X POST https://mcp-fetch.yourdomain.com/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"'"${MCP_PROTOCOL_VERSION:-2025-06-18}"'","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'
```

## 🔗 Integration

### Claude.ai Integration

Configure Claude.ai to use the fetch service:

```json
{
  "mcpServers": {
    "fetch": {
      "command": "mcp-streamablehttp-client",
      "args": ["--server-url", "https://mcp-fetch.yourdomain.com/mcp"]
    }
  }
}
```

### Custom Clients

Integrate with custom MCP clients:

```python
import mcp

# Initialize client
client = mcp.Client()

# Configure server
await client.add_server(
    "fetch",
    "https://mcp-fetch.yourdomain.com/mcp",
    headers={"Authorization": "Bearer <token>"}
)

# Use fetch tool
result = await client.call_tool("fetch", {
    "url": "https://api.example.com/data"
})
```

## 📊 Performance

### Benchmarks

- **Response Time** - < 100ms overhead (excluding network)
- **Throughput** - 1000+ requests/minute
- **Memory Usage** - ~50MB baseline + content size
- **Concurrent Requests** - 100+ concurrent connections

### Optimization Tips

1. **Use HTTP/2** - Enable for better performance
2. **Cache Control** - Respect cache headers
3. **Connection Pooling** - Reuse connections
4. **Content Compression** - Support gzip/deflate

---

**Next Steps:**
- Explore {doc}`mcp-memory` for knowledge graph storage
- Check {doc}`../integration/claude-ai` for AI integration
- Review {doc}`../api/mcp-endpoints` for protocol details