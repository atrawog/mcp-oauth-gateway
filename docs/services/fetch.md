# Fetch Service

The MCP Fetch service provides secure web content retrieval capabilities, allowing Claude to access and process web resources through the OAuth-protected gateway.

## Overview

The Fetch service enables:
- HTTP/HTTPS content retrieval
- HTML to markdown conversion
- Content extraction and parsing
- Header and metadata access
- Configurable timeouts and limits

## Configuration

### Environment Variables

```bash
# Service-specific settings
MCP_FETCH_TIMEOUT=30              # Request timeout in seconds
MCP_FETCH_MAX_SIZE=5242880        # Max response size (5MB)
MCP_FETCH_USER_AGENT="MCP-Gateway/1.0"
MCP_FETCH_FOLLOW_REDIRECTS=true
MCP_FETCH_MAX_REDIRECTS=5
```

### Docker Compose

The service runs as `mcp-fetch` in the compose stack:

```yaml
mcp-fetch:
  image: mcp-oauth-gateway/mcp-fetch:latest
  environment:
    - MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION}
    - FETCH_TIMEOUT=${MCP_FETCH_TIMEOUT}
```

## Usage

### Starting the Service

```bash
# Start fetch service only
just up mcp-fetch

# View logs
just logs mcp-fetch

# Rebuild after changes
just rebuild mcp-fetch
```

### API Endpoints

The fetch service exposes the standard MCP endpoint:

```
POST https://mcp-fetch.gateway.yourdomain.com/mcp
Authorization: Bearer <token>
Content-Type: application/json
```

### Available Methods

#### fetch

Retrieve content from a URL:

```json
{
  "jsonrpc": "2.0",
  "method": "fetch",
  "params": {
    "url": "https://example.com",
    "headers": {
      "Accept": "text/html"
    }
  },
  "id": "1"
}
```

#### fetchWithOptions

Advanced fetch with options:

```json
{
  "jsonrpc": "2.0",
  "method": "fetchWithOptions",
  "params": {
    "url": "https://api.example.com/data",
    "options": {
      "method": "POST",
      "headers": {
        "Content-Type": "application/json"
      },
      "body": "{\"key\": \"value\"}"
    }
  },
  "id": "2"
}
```

## Features

### Content Processing

- **HTML Conversion** - Automatic HTML to Markdown
- **Text Extraction** - Clean text from web pages
- **JSON Parsing** - Structured data handling
- **Binary Detection** - Prevents binary file issues

### Security Features

- **URL Validation** - Prevents SSRF attacks
- **Size Limits** - Prevents memory exhaustion
- **Timeout Protection** - Prevents hanging requests
- **Header Filtering** - Removes sensitive headers

### Rate Limiting

Per-client rate limits:
- 100 requests per minute
- 1000 requests per hour
- Configurable via environment

## Examples

### Basic Web Page Fetch

```python
# Example using mcp-streamablehttp-client
import mcp_streamablehttp_client as mcp

client = mcp.Client(
    "https://mcp-fetch.gateway.yourdomain.com",
    token=access_token
)

result = await client.request("fetch", {
    "url": "https://example.com"
})
```

### API Request with Headers

```python
result = await client.request("fetchWithOptions", {
    "url": "https://api.github.com/user",
    "options": {
        "headers": {
            "Authorization": "token github_pat_..."
        }
    }
})
```

## Limitations

1. **Size Limits** - Default 5MB per response
2. **Timeout** - 30 seconds default
3. **Protocols** - HTTP/HTTPS only
4. **Redirects** - Maximum 5 redirects
5. **Binary Files** - Not supported

## Troubleshooting

### Common Issues

#### Timeout Errors

```json
{
  "error": {
    "code": -32603,
    "message": "Request timeout after 30 seconds"
  }
}
```

**Solution**: Increase `MCP_FETCH_TIMEOUT` or optimize target server

#### Size Limit Exceeded

```json
{
  "error": {
    "code": -32603,
    "message": "Response size exceeds limit"
  }
}
```

**Solution**: Increase `MCP_FETCH_MAX_SIZE` or request smaller resources

#### SSL Certificate Errors

**Solution**: 
- Verify target server certificates
- Check `FETCH_VERIFY_SSL` setting
- Update CA certificates in container

### Debug Mode

Enable detailed logging:

```bash
# In mcp-fetch/.env
DEBUG=true
LOG_LEVEL=DEBUG
```

## Best Practices

1. **Set Appropriate Timeouts** - Balance between reliability and performance
2. **Use Headers Wisely** - Only send necessary headers
3. **Handle Errors Gracefully** - Implement retry logic in clients
4. **Monitor Usage** - Track rate limits and quotas
5. **Cache When Possible** - Reduce redundant fetches

## Security Considerations

- Never fetch internal network resources
- Validate and sanitize URLs
- Be cautious with authentication headers
- Monitor for abuse patterns
- Implement content filtering if needed

## Related Services

- [Filesystem Service](filesystem.md) - For local file operations
- [Memory Service](memory.md) - For caching fetched content