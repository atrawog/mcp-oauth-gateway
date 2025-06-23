# API Reference

The MCP OAuth Gateway implements OAuth 2.1 and MCP protocols with full RFC compliance. This section provides detailed API documentation.

## API Endpoints

```{toctree}
:maxdepth: 2

api/oauth-endpoints
api/mcp-endpoints
api/client-registration
api/error-codes
```

## Overview

The gateway exposes two main API categories:

### OAuth 2.1 Endpoints

Standard OAuth endpoints for authentication and authorization:

- `/register` - Dynamic client registration (RFC 7591)
- `/authorize` - Authorization endpoint
- `/token` - Token exchange endpoint
- `/callback` - OAuth callback handler
- `/.well-known/oauth-authorization-server` - Server metadata

### MCP Protocol Endpoints

Model Context Protocol endpoints for service interaction:

- `/mcp` - Main MCP communication endpoint
- Service-specific endpoints per MCP implementation

## Authentication

All MCP endpoints require Bearer token authentication:

```http
Authorization: Bearer <access_token>
```

Tokens are obtained through the OAuth 2.1 flow with PKCE.

## Response Formats

### Success Responses

```json
{
  "jsonrpc": "2.0",
  "result": {
    // Response data
  },
  "id": "request-id"
}
```

### Error Responses

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Method not found"
  },
  "id": "request-id"
}
```

## Rate Limiting

API endpoints implement rate limiting:
- OAuth endpoints: 10 requests/minute
- MCP endpoints: 100 requests/minute
- Per client_id tracking

## Versioning

The API version is specified via:
- `MCP-Protocol-Version` header for MCP endpoints
- OAuth 2.1 compliance for authentication endpoints