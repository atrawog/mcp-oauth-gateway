# OAuth Endpoints

This document provides a complete reference for all OAuth 2.1 endpoints implemented by the MCP OAuth Gateway.

## Authorization Endpoint

### `GET /authorize`

Initiates the OAuth authorization flow. This endpoint redirects users to GitHub for authentication.

**Request Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `client_id` | Yes | The client identifier |
| `redirect_uri` | Yes | Where to redirect after authorization |
| `response_type` | Yes | Must be `code` |
| `state` | Yes | CSRF protection token |
| `code_challenge` | Yes | PKCE challenge (S256 only) |
| `code_challenge_method` | Yes | Must be `S256` |
| `scope` | No | Requested scopes (defaults to `mcp:*`) |

**Example Request:**
```http
GET /authorize?client_id=client_abc123&redirect_uri=https://app.example.com/callback&response_type=code&state=xyz789&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256
```

**Success Response:**
- HTTP 302 redirect to GitHub OAuth

**Error Response:**
```json
{
  "error": "invalid_request",
  "error_description": "Missing required parameter: code_challenge"
}
```

## Token Endpoint

### `POST /token`

Exchanges authorization codes for access tokens or refreshes existing tokens.

**Request Headers:**
```http
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(client_id:client_secret)}
```

**Request Body (Authorization Code):**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `grant_type` | Yes | `authorization_code` |
| `code` | Yes | Authorization code from callback |
| `redirect_uri` | Yes | Must match original request |
| `code_verifier` | Yes | PKCE verifier |

**Request Body (Refresh Token):**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `grant_type` | Yes | `refresh_token` |
| `refresh_token` | Yes | The refresh token |

**Example Request:**
```http
POST /token
Authorization: Basic Y2xpZW50X2FiYzEyMzpzZWNyZXRfeHl6Nzg5
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=auth_code_123&redirect_uri=https://app.example.com/callback&code_verifier=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
```

**Success Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 2592000,
  "refresh_token": "refresh_token_xyz789",
  "scope": "mcp:*"
}
```

**Error Response:**
```json
{
  "error": "invalid_grant",
  "error_description": "Invalid authorization code"
}
```

## Callback Endpoint

### `GET /callback`

Handles OAuth callbacks from GitHub. This endpoint is not called directly by clients.

**Request Parameters:**
| Parameter | Description |
|-----------|-------------|
| `code` | GitHub authorization code |
| `state` | State parameter for CSRF protection |

**Success Response:**
- HTTP 302 redirect to original redirect_uri with authorization code

**Error Response:**
- HTTP 302 redirect to original redirect_uri with error parameters

## Registration Endpoint (RFC 7591)

### `POST /register`

Dynamically registers a new OAuth client. This endpoint is public and requires no authentication.

**Request Headers:**
```http
Content-Type: application/json
```

**Request Body:**
```json
{
  "client_name": "My MCP Client",
  "redirect_uris": ["https://app.example.com/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "client_secret_basic"
}
```

**Success Response (201 Created):**
```json
{
  "client_id": "client_abc123",
  "client_secret": "secret_xyz789",
  "client_name": "My MCP Client",
  "redirect_uris": ["https://app.example.com/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "client_secret_basic",
  "client_id_issued_at": 1704067200,
  "client_secret_expires_at": 1711929600,
  "registration_access_token": "rat_token123",
  "registration_client_uri": "https://auth.example.com/register/client_abc123"
}
```

## Client Management Endpoints (RFC 7592)

### `GET /register/{client_id}`

Retrieves client registration information.

**Request Headers:**
```http
Authorization: Bearer {registration_access_token}
```

**Success Response:**
```json
{
  "client_id": "client_abc123",
  "client_name": "My MCP Client",
  "redirect_uris": ["https://app.example.com/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "client_secret_basic",
  "client_id_issued_at": 1704067200,
  "client_secret_expires_at": 1711929600
}
```

### `PUT /register/{client_id}`

Updates client registration.

**Request Headers:**
```http
Authorization: Bearer {registration_access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "client_name": "Updated Client Name",
  "redirect_uris": ["https://new.example.com/callback"]
}
```

**Success Response:**
```json
{
  "client_id": "client_abc123",
  "client_name": "Updated Client Name",
  "redirect_uris": ["https://new.example.com/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "client_secret_basic"
}
```

### `DELETE /register/{client_id}`

Deletes a client registration.

**Request Headers:**
```http
Authorization: Bearer {registration_access_token}
```

**Success Response:**
- HTTP 204 No Content

## Token Management Endpoints

### `POST /revoke`

Revokes an access or refresh token (RFC 7009).

**Request Headers:**
```http
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(client_id:client_secret)}
```

**Request Body:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `token` | Yes | Token to revoke |
| `token_type_hint` | No | `access_token` or `refresh_token` |

**Success Response:**
- HTTP 200 OK (even if token was already revoked)

### `POST /introspect`

Introspects a token to determine its validity (RFC 7662).

**Request Headers:**
```http
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(client_id:client_secret)}
```

**Request Body:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `token` | Yes | Token to introspect |
| `token_type_hint` | No | `access_token` or `refresh_token` |

**Success Response:**
```json
{
  "active": true,
  "scope": "mcp:*",
  "client_id": "client_abc123",
  "username": "github_user",
  "exp": 1706659200,
  "iat": 1704067200,
  "sub": "github_user_123",
  "aud": "https://mcp-fetch.example.com",
  "iss": "https://auth.example.com",
  "jti": "token_unique_id"
}
```

## Discovery Endpoints

### `GET /.well-known/oauth-authorization-server`

Returns OAuth 2.0 Authorization Server Metadata (RFC 8414).

**Success Response:**
```json
{
  "issuer": "https://auth.example.com",
  "authorization_endpoint": "https://auth.example.com/authorize",
  "token_endpoint": "https://auth.example.com/token",
  "registration_endpoint": "https://auth.example.com/register",
  "jwks_uri": "https://auth.example.com/jwks",
  "revocation_endpoint": "https://auth.example.com/revoke",
  "introspection_endpoint": "https://auth.example.com/introspect",
  "scopes_supported": ["mcp:*"],
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"],
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
  "service_documentation": "https://github.com/atrawog/mcp-oauth-gateway"
}
```

### `GET /jwks`

Returns the JSON Web Key Set for token verification.

**Success Response:**
```json
{
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "key_id_123",
      "alg": "RS256",
      "n": "modulus...",
      "e": "AQAB"
    }
  ]
}
```

## Internal Endpoints

### `GET /verify`

Used by Traefik ForwardAuth to validate tokens. Not intended for direct client use.

**Request Headers:**
```http
Authorization: Bearer {access_token}
```

**Success Response:**
```http
HTTP/1.1 200 OK
X-User-Id: github_user_123
X-User-Name: github_username
X-Auth-Token: {original_token}
```

**Error Response:**
```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="invalid_token"
```

### `GET /health`

Health check endpoint for monitoring.

**Success Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Error Handling

All OAuth endpoints follow RFC 6749 error response format:

```json
{
  "error": "error_code",
  "error_description": "Human-readable description",
  "error_uri": "https://tools.ietf.org/html/rfc6749#section-4.1.2.1"
}
```

Common error codes:
- `invalid_request` - Missing or invalid parameters
- `invalid_client` - Client authentication failed
- `invalid_grant` - Invalid authorization code or refresh token
- `unauthorized_client` - Client not authorized
- `unsupported_grant_type` - Grant type not supported
- `invalid_scope` - Invalid scope requested

## CORS Support

All endpoints support CORS with configurable allowed origins:

```http
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Max-Age: 86400
```

## Rate Limiting

The gateway implements rate limiting:
- Registration: 10 requests per hour per IP
- Token endpoint: 100 requests per minute per client
- Authorization: 20 requests per minute per IP

## Next Steps

- [MCP Endpoints](mcp-endpoints.md) - MCP protocol endpoints
- [Client Registration](client-registration.md) - Dynamic registration details
- [Error Codes](error-codes.md) - Complete error reference