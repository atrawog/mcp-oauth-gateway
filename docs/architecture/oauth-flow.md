# OAuth 2.1 Authentication Flows

This document details the OAuth 2.1 authentication flows implemented in the MCP OAuth Gateway, including dynamic client registration, authorization flows, and token management.

## Overview

The gateway implements a complete OAuth 2.1 authorization server with:
- **RFC 6749** - OAuth 2.0 Core (updated to 2.1 requirements)
- **RFC 7591** - Dynamic Client Registration
- **RFC 7592** - Client Configuration Management
- **RFC 7636** - PKCE (Proof Key for Code Exchange)
- **RFC 8414** - Authorization Server Metadata

## Authentication Flow Diagram

```{mermaid}
sequenceDiagram
    participant Client as MCP Client
    participant Traefik as Traefik Router
    participant Auth as Auth Service
    participant Redis as Redis Store
    participant GitHub as GitHub OAuth
    participant MCP as MCP Service
    
    Client->>Traefik: 1. Request MCP endpoint
    Traefik->>Client: 2. 401 Unauthorized (WWW-Authenticate)
    Client->>Auth: 3. GET /.well-known/oauth-authorization-server
    Auth->>Client: 4. Server metadata
    Client->>Auth: 5. POST /register (dynamic registration)
    Auth->>Redis: 6. Store client
    Auth->>Client: 7. client_id, client_secret
    Client->>Auth: 8. GET /authorize (with PKCE)
    Auth->>GitHub: 9. Redirect to GitHub
    GitHub->>Auth: 10. Callback with code
    Auth->>Client: 11. Redirect with auth code
    Client->>Auth: 12. POST /token (code + verifier)
    Auth->>Redis: 13. Validate & store token
    Auth->>Client: 14. Access token (JWT)
    Client->>Traefik: 15. Request with Bearer token
    Traefik->>Auth: 16. ForwardAuth validation
    Auth->>Traefik: 17. User info headers
    Traefik->>MCP: 18. Proxied request
    MCP->>Client: 19. MCP response
```

## Client Registration Flow (RFC 7591)

### 1. Dynamic Registration

Clients register dynamically without pre-configuration:

```http
POST /register HTTP/1.1
Host: auth.example.com
Content-Type: application/json

{
  "client_name": "My MCP Client",
  "redirect_uris": ["http://localhost:8080/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "client_secret_post"
}
```

Response:
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "client_id": "7f3e2a5b9c1d4e6f",
  "client_secret": "supersecret123",
  "client_name": "My MCP Client",
  "redirect_uris": ["http://localhost:8080/callback"],
  "registration_access_token": "reg-token-abc123",
  "registration_client_uri": "https://auth.example.com/register/7f3e2a5b9c1d4e6f",
  "client_secret_expires_at": 0
}
```

### 2. Client Management (RFC 7592)

Clients can manage their registration:

```http
GET /register/{client_id} HTTP/1.1
Host: auth.example.com
Authorization: Bearer reg-token-abc123
```

## Authorization Code Flow with PKCE

### 1. Generate PKCE Challenge

Client generates cryptographically random verifier:
```python
code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode('utf-8').rstrip('=')
```

### 2. Authorization Request

```http
GET /authorize HTTP/1.1
Host: auth.example.com

Parameters:
  response_type=code
  client_id=7f3e2a5b9c1d4e6f
  redirect_uri=http://localhost:8080/callback
  scope=read write
  state=random-state-value
  code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
  code_challenge_method=S256
```

### 3. User Authentication

The auth service redirects to GitHub OAuth:
```http
HTTP/1.1 302 Found
Location: https://github.com/login/oauth/authorize?client_id=GITHUB_CLIENT_ID&...
```

### 4. Authorization Code Return

After GitHub authentication:
```http
GET /callback?code=auth-code-123&state=random-state-value HTTP/1.1
Host: localhost:8080
```

### 5. Token Exchange

```http
POST /token HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code=auth-code-123
&client_id=7f3e2a5b9c1d4e6f
&client_secret=supersecret123
&redirect_uri=http://localhost:8080/callback
&code_verifier=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
```

Response:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "refresh_token": "refresh-token-xyz789",
  "scope": "read write"
}
```

## Token Structure

### JWT Claims

Access tokens are JWTs with the following claims:

```json
{
  "iss": "https://auth.example.com",
  "sub": "github|123456",
  "aud": ["https://mcp-fetch.example.com"],
  "exp": 1640995200,
  "iat": 1640908800,
  "jti": "unique-token-id",
  "scope": "read write",
  "client_id": "7f3e2a5b9c1d4e6f",
  "username": "johndoe",
  "email": "john@example.com"
}
```

### Token Validation

Services validate tokens by:
1. Verifying JWT signature
2. Checking expiration
3. Validating audience
4. Confirming scope

## Refresh Token Flow

### Token Refresh Request

```http
POST /token HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&refresh_token=refresh-token-xyz789
&client_id=7f3e2a5b9c1d4e6f
&client_secret=supersecret123
```

## Error Handling

### OAuth Error Responses

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "invalid_request",
  "error_description": "The request is missing a required parameter",
  "error_uri": "https://auth.example.com/docs/errors#invalid_request"
}
```

Common error codes:
- `invalid_request` - Malformed request
- `invalid_client` - Client authentication failed
- `invalid_grant` - Invalid authorization code or refresh token
- `unauthorized_client` - Client not authorized for grant type
- `unsupported_grant_type` - Grant type not supported
- `invalid_scope` - Requested scope is invalid

## Security Considerations

### PKCE Requirements
- **Mandatory S256** - Only SHA256 challenge method allowed
- **Verifier length** - 43-128 characters required
- **Single use** - Verifiers cannot be reused

### Token Security
- **Short-lived access tokens** - 24 hour default
- **Rotating refresh tokens** - New token on each refresh
- **Secure storage** - Tokens stored encrypted in Redis
- **Revocation support** - Tokens can be revoked

### Client Security
- **Secret rotation** - Clients can rotate secrets
- **Redirect URI validation** - Strict matching required
- **Rate limiting** - Prevent brute force attacks

## Implementation Details

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/register` | POST | Dynamic client registration |
| `/register/{id}` | GET/PUT/DELETE | Client management |
| `/authorize` | GET | Authorization endpoint |
| `/token` | POST | Token endpoint |
| `/callback` | GET | OAuth callback |
| `/revoke` | POST | Token revocation |
| `/introspect` | POST | Token introspection |
| `/.well-known/oauth-authorization-server` | GET | Server metadata |

### Storage Schema

#### Client Storage
```python
{
    "client_id": "7f3e2a5b9c1d4e6f",
    "client_secret": "hashed-secret",
    "client_name": "My MCP Client",
    "redirect_uris": ["http://localhost:8080/callback"],
    "created_at": "2024-01-01T00:00:00Z",
    "registration_access_token": "reg-token-abc123"
}
```

#### Token Storage
```python
{
    "jti": "unique-token-id",
    "user_id": "github|123456",
    "client_id": "7f3e2a5b9c1d4e6f",
    "scope": "read write",
    "expires_at": "2024-01-02T00:00:00Z"
}
```

## Testing OAuth Flows

### Manual Testing

1. **Registration**
   ```bash
   curl -X POST https://auth.example.com/register \
     -H "Content-Type: application/json" \
     -d '{"client_name": "Test Client", "redirect_uris": ["http://localhost:8080/callback"]}'
   ```

2. **Authorization**
   ```bash
   # Generate PKCE challenge
   just generate-pkce-challenge
   
   # Start authorization flow
   open "https://auth.example.com/authorize?client_id=CLIENT_ID&..."
   ```

3. **Token Exchange**
   ```bash
   curl -X POST https://auth.example.com/token \
     -d "grant_type=authorization_code&code=CODE&..."
   ```

### Automated Testing

```bash
# Run OAuth flow tests
just test-oauth-flow

# Test specific scenarios
just test-file tests/test_full_oauth_flow.py
just test-file tests/test_pkce_validation.py
just test-file tests/test_rfc7591_compliance.py
```

## Troubleshooting

### Common Issues

1. **Invalid Client**
   - Verify client_id exists
   - Check client_secret is correct
   - Ensure redirect_uri matches

2. **PKCE Failures**
   - Verifier must be 43-128 characters
   - Challenge must use S256 method
   - Verifier must match challenge

3. **Token Validation**
   - Check token expiration
   - Verify JWT signature
   - Confirm audience claim

### Debug Tools

```bash
# Decode JWT token
just decode-jwt TOKEN

# Check Redis storage
just redis-cli GET oauth:client:CLIENT_ID

# View auth logs
just logs auth | grep "oauth"
```

## Related Documentation

- {doc}`security-model` - Security architecture
- {doc}`../api/oauth-endpoints` - API reference
- {doc}`../integration/claude-ai` - Claude.ai integration