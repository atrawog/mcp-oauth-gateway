# OAuth Endpoints

Complete reference for OAuth 2.1 endpoints implemented by the Auth service.

## Endpoint Overview

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/authorize` | GET | Start authorization flow | None |
| `/token` | POST | Exchange code for token | Client credentials |
| `/callback` | GET | OAuth callback handler | None (internal) |
| `/revoke` | POST | Revoke token | Client credentials |
| `/introspect` | POST | Token introspection | Client credentials |
| `/.well-known/oauth-authorization-server` | GET | Server metadata | None |

## Authorization Endpoint

### `GET /authorize`

Initiates the OAuth 2.1 authorization flow with PKCE.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Registered client identifier |
| `redirect_uri` | string | Yes | Callback URL (must match registration) |
| `response_type` | string | Yes | Must be `code` |
| `scope` | string | No | Requested permissions (default: `mcp:*`) |
| `state` | string | Yes | CSRF protection token |
| `code_challenge` | string | Yes | PKCE challenge (base64url) |
| `code_challenge_method` | string | Yes | Must be `S256` |

#### Example Request

```
GET /authorize?
  client_id=client_7d8e9f0a&
  redirect_uri=http://localhost:8080/callback&
  response_type=code&
  scope=mcp:*&
  state=abc123xyz&
  code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&
  code_challenge_method=S256
```

#### Response

Redirects to GitHub OAuth for user authentication, then back to client:

```
HTTP/1.1 302 Found
Location: http://localhost:8080/callback?
  code=auth_9f3c8e2d&
  state=abc123xyz
```

#### Error Response

```
HTTP/1.1 302 Found
Location: http://localhost:8080/callback?
  error=invalid_request&
  error_description=Missing required parameter: code_challenge&
  state=abc123xyz
```

## Token Endpoint

### `POST /token`

Exchanges authorization code for access token.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `grant_type` | string | Yes | `authorization_code` or `refresh_token` |
| `client_id` | string | Yes | Client identifier |
| `client_secret` | string | No | Required for confidential clients |
| `code` | string | Yes* | Authorization code (*for auth code grant) |
| `redirect_uri` | string | Yes* | Must match authorize request |
| `code_verifier` | string | Yes* | PKCE verifier |
| `refresh_token` | string | Yes** | For refresh grant (**) |

#### Example Request (Authorization Code)

```http
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
client_id=client_7d8e9f0a&
code=auth_9f3c8e2d&
redirect_uri=http://localhost:8080/callback&
code_verifier=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
```

#### Example Request (Refresh Token)

```http
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&
client_id=client_7d8e9f0a&
refresh_token=refresh_8d4b2c7e
```

#### Success Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 2592000,
  "refresh_token": "refresh_8d4b2c7e",
  "scope": "mcp:*"
}
```

#### Error Response

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "invalid_grant",
  "error_description": "Authorization code is invalid or expired"
}
```

## Callback Endpoint

### `GET /callback`

Internal endpoint for GitHub OAuth callback processing.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | string | Yes | GitHub authorization code |
| `state` | string | Yes | State from original request |

#### Flow

1. Receives callback from GitHub
2. Validates state parameter
3. Exchanges GitHub code for user info
4. Generates authorization code
5. Redirects to client callback

This endpoint is not called directly by clients.

## Revocation Endpoint

### `POST /revoke`

Revokes an access or refresh token.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Token to revoke |
| `token_type_hint` | string | No | `access_token` or `refresh_token` |
| `client_id` | string | Yes | Client identifier |
| `client_secret` | string | No | For confidential clients |

#### Example Request

```http
POST /revoke
Content-Type: application/x-www-form-urlencoded

token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...&
token_type_hint=access_token&
client_id=client_7d8e9f0a
```

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "revoked"
}
```

Note: Always returns 200 OK per RFC 7009, even if token was already revoked or invalid.

## Introspection Endpoint

### `POST /introspect`

Returns token metadata and validation status.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Token to introspect |
| `token_type_hint` | string | No | `access_token` or `refresh_token` |
| `client_id` | string | Yes | Client identifier |
| `client_secret` | string | No | For confidential clients |

#### Example Request

```http
POST /introspect
Content-Type: application/x-www-form-urlencoded

token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...&
client_id=client_7d8e9f0a
```

#### Active Token Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "active": true,
  "scope": "mcp:*",
  "client_id": "client_7d8e9f0a",
  "username": "github|johndoe",
  "token_type": "Bearer",
  "exp": 1706745600,
  "iat": 1704153600,
  "sub": "github|johndoe",
  "aud": "client_7d8e9f0a",
  "iss": "https://auth.example.com",
  "jti": "token_3f8a9c2d"
}
```

#### Inactive Token Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "active": false
}
```

## Discovery Endpoint

### `GET /.well-known/oauth-authorization-server`

Returns OAuth 2.0 Authorization Server Metadata (RFC 8414).

#### Example Request

```http
GET /.well-known/oauth-authorization-server
```

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "issuer": "https://auth.example.com",
  "authorization_endpoint": "https://auth.example.com/authorize",
  "token_endpoint": "https://auth.example.com/token",
  "registration_endpoint": "https://auth.example.com/register",
  "revocation_endpoint": "https://auth.example.com/revoke",
  "introspection_endpoint": "https://auth.example.com/introspect",
  "jwks_uri": "https://auth.example.com/.well-known/jwks.json",
  "response_types_supported": ["code"],
  "response_modes_supported": ["query"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"],
  "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic", "none"],
  "scopes_supported": ["mcp:*", "mcp:read", "mcp:write"],
  "service_documentation": "https://docs.example.com",
  "ui_locales_supported": ["en-US"]
}
```

## Authentication Methods

### Public Clients

Public clients (mobile apps, SPAs) use:
- No client secret required
- PKCE mandatory
- `token_endpoint_auth_method`: `none`

### Confidential Clients

Confidential clients use:
- Client secret required
- Supported methods:
  - `client_secret_post` - In request body
  - `client_secret_basic` - HTTP Basic auth

## PKCE Implementation

### Code Verifier Generation

```python
import secrets
import base64

# Generate code verifier (43-128 characters)
code_verifier = base64.urlsafe_b64encode(
    secrets.token_bytes(32)
).decode('utf-8').rstrip('=')
```

### Code Challenge Generation

```python
import hashlib

# Generate S256 challenge
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode('utf-8').rstrip('=')
```

## Security Headers

All OAuth endpoints include security headers:

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
```

## Error Handling

OAuth errors follow RFC 6749 format:

| Error Code | Description |
|------------|-------------|
| `invalid_request` | Request missing required parameter |
| `invalid_client` | Client authentication failed |
| `invalid_grant` | Authorization code or refresh token invalid |
| `unauthorized_client` | Client not authorized for grant type |
| `unsupported_grant_type` | Grant type not supported |
| `invalid_scope` | Requested scope invalid or exceeds granted |

## Rate Limiting

OAuth endpoints have specific rate limits:

- `/authorize`: 20 requests/minute per IP
- `/token`: 60 requests/minute per client
- `/revoke`: 30 requests/minute per client
- `/introspect`: 100 requests/minute per client
