# MCP Fetchs Service

The MCP Fetchs service provides enhanced web content retrieval and HTTP operations through the Model Context Protocol.

## Overview

MCP Fetchs is an alternative implementation of web fetching capabilities, offering extended features beyond the standard MCP Fetch service. It wraps the official server implementation and exposes it via HTTP endpoints secured with OAuth 2.1 authentication.

## Features

### 🌐 Enhanced HTTP Operations
- **All HTTP Methods** - GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **Custom Headers** - Full header control
- **Request Bodies** - JSON, form data, raw content
- **Response Handling** - Status codes, headers, body parsing

### 🔧 Advanced Features
- **Redirects Control** - Follow or capture redirects
- **Timeout Management** - Configurable request timeouts
- **Proxy Support** - Route through proxy servers
- **Cookie Handling** - Session persistence

### 📊 Content Processing
- **Auto-parsing** - JSON, XML, HTML detection
- **Encoding Detection** - Automatic charset handling
- **Compression** - gzip, deflate support
- **Streaming** - Large file handling

### 🛡️ Security Features
- **SSL Verification** - Certificate validation
- **Authentication** - Basic, Bearer, custom auth
- **Rate Limiting** - Request throttling
- **Domain Filtering** - Allowed/blocked lists

## Authentication

All requests require OAuth 2.1 Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     https://mcp-fetchs.yourdomain.com/mcp
```

## Endpoints

### Primary Endpoints
- **`/mcp`** - Main MCP protocol endpoint
- **`/mcp`** - Main MCP protocol endpoint (health checks via protocol initialization)
- **`/.well-known/oauth-authorization-server`** - OAuth discovery

## Usage Examples

### Basic GET Request

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://api.example.com/data",
      "method": "GET"
    }
  },
  "id": 1
}
```

### POST with Headers and Body

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://api.example.com/users",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer api-token"
      },
      "body": {
        "name": "John Doe",
        "email": "john@example.com"
      }
    }
  },
  "id": 2
}
```

### Advanced Request with Options

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetch_advanced",
    "arguments": {
      "url": "https://api.example.com/data",
      "options": {
        "timeout": 30000,
        "follow_redirects": false,
        "verify_ssl": true,
        "max_retries": 3
      }
    }
  },
  "id": 3
}
```

## Available Tools

### Core Operations
- `fetch` - Perform HTTP request
- `fetch_advanced` - Request with options
- `fetch_batch` - Multiple requests
- `fetch_stream` - Streaming response

### Utility Tools
- `parse_url` - URL parsing
- `encode_url` - URL encoding
- `build_url` - URL construction
- `extract_links` - Link extraction

### Content Tools
- `parse_json` - JSON parsing
- `parse_xml` - XML parsing
- `parse_html` - HTML parsing
- `extract_text` - Text extraction

### Security Tools
- `check_ssl` - SSL verification
- `validate_domain` - Domain checking
- `sanitize_url` - URL sanitization

## Configuration

### Environment Variables

```bash
# From .env file
MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION:-2025-06-18}
BASE_DOMAIN=yourdomain.com

# Fetchs specific
FETCHS_TIMEOUT=30000
FETCHS_MAX_REDIRECTS=5
FETCHS_USER_AGENT="MCP-Fetchs/1.0"
```

### Docker Labels

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.mcp-fetchs.rule=Host(`mcp-fetchs.${BASE_DOMAIN}`)"
  - "traefik.http.routers.mcp-fetchs.middlewares=mcp-auth@docker"
```

## Testing

### Integration Tests
```bash
just test-file tests/test_mcp_fetchs_complete.py
just test-file tests/test_mcp_fetchs_protocol.py
just test-file tests/test_mcp_fetchs_security.py
```

### Manual Testing
```bash
# List available tools
mcp-streamablehttp-client query https://mcp-fetchs.yourdomain.com/mcp \
  --token YOUR_TOKEN \
  '{"method": "tools/list"}'

# Fetch a URL
mcp-streamablehttp-client query https://mcp-fetchs.yourdomain.com/mcp \
  --token YOUR_TOKEN \
  '{"method": "tools/call", "params": {"name": "fetch", "arguments": {"url": "https://example.com"}}}'
```

## Error Handling

### Common Errors

1. **Connection Error**
   ```json
   {
     "error": {
       "code": -32603,
       "message": "Failed to connect to host"
     }
   }
   ```

2. **Timeout Error**
   ```json
   {
     "error": {
       "code": -32603,
       "message": "Request timeout after 30000ms"
     }
   }
   ```

3. **Invalid URL**
   ```json
   {
     "error": {
       "code": -32602,
       "message": "Invalid URL format"
     }
   }
   ```

## Best Practices

### Performance
- Use appropriate timeouts
- Enable compression
- Reuse connections
- Cache responses when possible

### Security
- Always verify SSL certificates
- Validate URLs before fetching
- Use domain allowlists
- Sanitize response data

### Reliability
- Implement retry logic
- Handle timeouts gracefully
- Check response status
- Validate content types

## Advanced Features

### Batch Requests
```json
{
  "method": "tools/call",
  "params": {
    "name": "fetch_batch",
    "arguments": {
      "requests": [
        {"url": "https://api1.example.com/data"},
        {"url": "https://api2.example.com/data"},
        {"url": "https://api3.example.com/data"}
      ],
      "parallel": true
    }
  }
}
```

### Custom Authentication
```json
{
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://api.example.com/protected",
      "auth": {
        "type": "bearer",
        "token": "your-api-token"
      }
    }
  }
}
```

### Response Processing
```json
{
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://api.example.com/data.json",
      "parse": true,
      "encoding": "utf-8"
    }
  }
}
```

## Troubleshooting

### Service Issues
```bash
# Check container status
docker ps | grep mcp-fetchs

# View logs
docker logs mcp-fetchs

# Protocol health check via MCP initialization
curl -X POST https://mcp-fetchs.yourdomain.com/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"'"${MCP_PROTOCOL_VERSION:-2025-06-18}"'","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'
```

### Request Debugging
```bash
# Enable debug logging
docker exec mcp-fetchs sh -c "export DEBUG=* && node server.js"

# Test with curl
curl -X POST https://mcp-fetchs.yourdomain.com/mcp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/call", "params": {"name": "fetch", "arguments": {"url": "https://httpbin.org/get"}}}'
```

## Performance Considerations

- **Connection Pooling** - Reuse HTTP connections
- **Timeouts** - Set appropriate timeouts (30s default)
- **Payload Size** - Limit response size (10MB default)
- **Concurrent Requests** - Limit parallel requests
- **Caching** - Implement response caching

## Related Documentation

- {doc}`mcp-fetch` - Standard fetch service
- {doc}`../integration/index` - Integration guides
- {doc}`../architecture/mcp-protocol` - Protocol details