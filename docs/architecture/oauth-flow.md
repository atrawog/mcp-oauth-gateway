# OAuth 2.1 Flow

The MCP OAuth Gateway implements a complete OAuth 2.1 authorization server with support for dynamic client registration (RFC 7591) and client management (RFC 7592).

## Authorization Code Flow with PKCE

The gateway implements the OAuth 2.1 authorization code flow with mandatory PKCE (Proof Key for Code Exchange) for enhanced security.

### Flow Overview

```{mermaid}
sequenceDiagram
    participant Client as MCP Client
    participant Gateway as OAuth Gateway
    participant GitHub as GitHub OAuth
    participant User as User Browser
    
    Note over Client,User: 1. Client Registration (if needed)
    Client->>Gateway: POST /register
    Gateway->>Client: 201 Created<br/>{client_id, client_secret}
    
    Note over Client,User: 2. Authorization Request
    Client->>Client: Generate code_verifier & code_challenge
    Client->>User: Open browser to /authorize
    User->>Gateway: GET /authorize?client_id=...<br/>&code_challenge=...
    Gateway->>User: Redirect to GitHub
    User->>GitHub: Authenticate
    GitHub->>User: Redirect to callback
    User->>Gateway: GET /callback?code=...
    Gateway->>GitHub: Exchange code for token
    GitHub->>Gateway: Access token + user info
    Gateway->>User: Redirect with auth code
    
    Note over Client,User: 3. Token Exchange
    Client->>Gateway: POST /token<br/>code + code_verifier
    Gateway->>Gateway: Validate PKCE
    Gateway->>Client: Access token (JWT)
```

## Dynamic Client Registration (RFC 7591)

The gateway supports dynamic client registration, allowing MCP clients to register themselves without manual configuration.

### Registration Request

```http
POST /register
Content-Type: application/json

{
  "client_name": "My MCP Client",
  "redirect_uris": ["https://app.example.com/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "client_secret_basic"
}
```

### Registration Response

```http
HTTP/1.1 201 Created
Content-Type: application/json

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
  "registration_client_uri": "https://auth.domain.com/register/client_abc123"
}
```

### Key Features

- **No Authentication Required**: Registration endpoint is public
- **Automatic Credentials**: Client ID and secret generated automatically
- **Configurable Lifetime**: Clients expire after 90 days (configurable)
- **Management Token**: Registration access token for client updates

## Client Management (RFC 7592)

Registered clients can manage their registration using the registration access token.

### Read Registration

```http
GET /register/{client_id}
Authorization: Bearer {registration_access_token}
```

### Update Registration

```http
PUT /register/{client_id}
Authorization: Bearer {registration_access_token}
Content-Type: application/json

{
  "client_name": "Updated Client Name",
  "redirect_uris": ["https://new.example.com/callback"]
}
```

### Delete Registration

```http
DELETE /register/{client_id}
Authorization: Bearer {registration_access_token}
```

## PKCE Implementation

The gateway enforces PKCE for all authorization code flows.

### Code Challenge Methods

- **S256** (Required): SHA256 hash of code verifier
- **plain** (Rejected): Not supported for security

### PKCE Validation

```python
# Pseudo-code for PKCE validation
def validate_pkce(code_verifier, code_challenge, method):
    if method == "S256":
        calculated = base64url(sha256(code_verifier))
        return calculated == code_challenge
    else:
        raise UnsupportedChallengeMethod()
```

## Token Types

### Access Tokens (JWT)

The gateway issues JWT access tokens with the following claims:

```json
{
  "sub": "github_user_123",
  "iss": "https://auth.domain.com",
  "aud": "https://mcp-fetch.domain.com",
  "exp": 1704153600,
  "iat": 1704067200,
  "jti": "token_unique_id",
  "username": "github_username",
  "email": "user@example.com",
  "name": "User Name",
  "scope": "mcp:*",
  "client_id": "client_abc123"
}
```

### Refresh Tokens

- Opaque tokens (not JWT)
- Stored in Redis with 1-year TTL
- Can be revoked immediately
- Bound to specific client and user

### Registration Access Tokens

- Bearer tokens for client management
- Unique per client registration
- Required for RFC 7592 operations
- Cannot be regenerated if lost

## GitHub Integration

The gateway uses GitHub as the identity provider for user authentication.

### Configuration

```env
GITHUB_CLIENT_ID=your_github_oauth_app_id
GITHUB_CLIENT_SECRET=your_github_oauth_app_secret
ALLOWED_GITHUB_USERS=user1,user2,user3  # or * for any user
```

### User Authentication Flow

1. Gateway redirects to GitHub authorization
2. User authenticates with GitHub
3. GitHub redirects back with authorization code
4. Gateway exchanges code for GitHub access token
5. Gateway fetches user info from GitHub API
6. Gateway validates user against allowlist
7. Gateway issues its own tokens

## Security Features

### State Parameter

- Prevents CSRF attacks
- Cryptographically random
- Short-lived (5 minutes)
- Validated on callback

### Token Security

- **JWT Signing**: RS256 with RSA keys
- **Token Binding**: Tokens bound to client and user
- **Immediate Revocation**: Via Redis storage
- **Expiration**: Configurable lifetimes

### Client Authentication

- **Basic Auth**: Client credentials in Authorization header
- **Post Body**: Client credentials in request body
- **Validation**: Constant-time comparison

### Error Handling

The gateway follows OAuth 2.1 error response format:

```json
{
  "error": "invalid_request",
  "error_description": "The code challenge method is not supported",
  "error_uri": "https://tools.ietf.org/html/rfc7636#section-4.3"
}
```

## Service Discovery

The gateway provides OAuth 2.0 Authorization Server Metadata (RFC 8414):

```http
GET /.well-known/oauth-authorization-server

{
  "issuer": "https://auth.domain.com",
  "authorization_endpoint": "https://auth.domain.com/authorize",
  "token_endpoint": "https://auth.domain.com/token",
  "registration_endpoint": "https://auth.domain.com/register",
  "jwks_uri": "https://auth.domain.com/jwks",
  "scopes_supported": ["mcp:*"],
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"],
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"]
}
```

## Token Lifecycle

### Issuance

1. User completes authorization flow
2. Client exchanges code for tokens
3. Tokens stored in Redis
4. JWT returned to client

### Validation

1. Extract JWT from Authorization header
2. Verify JWT signature
3. Check token in Redis (not revoked)
4. Validate claims (exp, aud, etc.)

### Renewal

1. Client presents refresh token
2. Validate refresh token in Redis
3. Check user still authorized
4. Issue new access token

### Revocation

1. Client posts token to /revoke
2. Token marked invalid in Redis
3. Subsequent requests rejected
4. Refresh token also revoked

## Next Steps

- [MCP Integration](mcp-integration.md) - How OAuth protects MCP services
- [Security Architecture](security.md) - Security deep dive
- [API Reference](../api/oauth-endpoints.md) - Complete endpoint documentation