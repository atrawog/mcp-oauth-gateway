# API Reference

Complete API reference for the MCP OAuth Gateway, covering OAuth 2.1 endpoints, MCP protocol endpoints, and administrative APIs.

## API Categories

The gateway exposes three categories of APIs:

### 1. OAuth 2.1 Endpoints

Authentication and authorization APIs implementing OAuth 2.1 specification:

- **[OAuth Endpoints](oauth-endpoints)** - Core OAuth 2.1 flows
- **[Client Registration](client-registration)** - RFC 7591/7592 dynamic registration

### 2. MCP Protocol Endpoints

Model Context Protocol service endpoints:

- **[MCP Endpoints](mcp-endpoints)** - StreamableHTTP protocol implementation

### 3. Administrative APIs

Internal APIs for health, monitoring, and management.

## Base URLs

APIs are accessible at these base URLs:

```
# OAuth endpoints
https://auth.{BASE_DOMAIN}/*

# MCP service endpoints
https://{service}.{BASE_DOMAIN}/mcp
```

## Authentication

### OAuth Endpoints

Most OAuth endpoints are public or use client credentials:

| Endpoint | Authentication |
|----------|----------------|
| `/register` | None (public) |
| `/authorize` | Client ID validation |
| `/token` | Client credentials |
| `/register/{id}` | Bearer (registration token) |

### MCP Endpoints

All MCP endpoints require Bearer token authentication:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...
```

## Content Types

### Request Content Types

- OAuth endpoints: `application/x-www-form-urlencoded` or `application/json`
- MCP endpoints: `application/json`

### Response Content Types

- OAuth endpoints: `application/json`
- MCP endpoints: `text/event-stream` (Server-Sent Events)

## Common Headers

### Required Headers

```http
# For OAuth endpoints
Content-Type: application/json
Accept: application/json

# For MCP endpoints
Content-Type: application/json
Accept: application/json, text/event-stream
Authorization: Bearer {token}
```

### Optional Headers

```http
# Session management (MCP)
Mcp-Session-Id: {session-id}

# Request tracking
X-Request-ID: {uuid}
```

## Rate Limiting

Rate limiting is not currently implemented but can be added via Traefik middleware if needed.

## Error Responses

### OAuth Error Format

```json
{
  "error": "invalid_client",
  "error_description": "Client authentication failed",
  "error_uri": "https://docs.example.com/errors/invalid_client"
}
```

### MCP Error Format

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": {
      "details": "Missing required parameter"
    }
  },
  "id": null
}
```

### HTTP Status Codes

| Code | Description | Used For |
|------|-------------|----------|
| 200 | OK | Successful requests |
| 201 | Created | Client registration |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Invalid/missing auth |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server errors |

## API Versioning

### OAuth APIs

OAuth 2.1 compliant - version in specification compliance.

### MCP Protocol Versions

Negotiated during initialization:

```json
{
  "params": {
    "protocolVersion": "2025-06-18"
  }
}
```

Supported versions:
- `2025-06-18` (latest)
- `2025-03-26`
- `2024-11-05`

## CORS Configuration

CORS headers for browser-based clients:

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Max-Age: 86400
```

## API Discovery

### OAuth Metadata

```
GET /.well-known/oauth-authorization-server

{
  "issuer": "https://auth.example.com",
  "authorization_endpoint": "https://auth.example.com/authorize",
  "token_endpoint": "https://auth.example.com/token",
  "registration_endpoint": "https://auth.example.com/register",
  "revocation_endpoint": "https://auth.example.com/revoke",
  "introspection_endpoint": "https://auth.example.com/introspect",
  "code_challenge_methods_supported": ["S256"],
  "grant_types_supported": ["authorization_code", "refresh_token"]
}
```

### MCP Service Discovery

Services self-describe capabilities during initialization.

## Security Considerations

1. **Always use HTTPS** - HTTP requests rejected
2. **Token expiration** - Access tokens expire after 30 days
3. **PKCE required** - All OAuth flows must use PKCE
4. **Origin validation** - CORS and origin headers checked
5. **Input validation** - All inputs sanitized and validated

## Client Libraries

### Python
```python
import httpx
from authlib.integrations.httpx_client import OAuth2Session

client = OAuth2Session()
```

### JavaScript
```javascript
const client = new MCPClient({
  serverUrl: 'https://service.example.com/mcp',
  token: 'Bearer ...'
});
```

### Command Line
```bash
# Using mcp-streamablehttp-client
mcp-streamablehttp-client \
  --server-url https://service.example.com/mcp \
  --token "Bearer ..."
```

## API Testing

### OAuth Endpoints
```bash
# Test with curl
curl -X POST https://auth.example.com/register \
  -H "Content-Type: application/json" \
  -d '{"client_name": "Test Client"}'
```

### MCP Endpoints
```bash
# Test with httpie
http POST https://service.example.com/mcp \
  Authorization:"Bearer ..." \
  jsonrpc=2.0 method=initialize id=1
```

## Next Steps

- [OAuth Endpoints](oauth-endpoints) - Detailed OAuth API reference
- [MCP Endpoints](mcp-endpoints) - MCP protocol reference
- [Client Registration](client-registration) - Registration API details
- [Error Codes](error-codes) - Complete error code reference
