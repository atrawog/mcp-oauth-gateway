# OAuth 2.1 Flow

The MCP OAuth Gateway implements a **sophisticated OAuth 2.1 system** that combines client credential authentication with GitHub user authentication. This dual-authentication approach ensures both the OAuth client (e.g., Claude.ai) and the human user are properly verified.

## OAuth Architecture: Client Credentials + User Authentication

```{mermaid}
graph TB
    subgraph "OAuth Client Registration"
        CR[POST /register<br/>No auth required]
        CR --> CC[client_id + client_secret<br/>OAuth credentials]
        CR --> RT[registration_access_token<br/>Client management only]
    end
    
    subgraph "User Authentication"
        UA[GET /authorize<br/>Requires client_id]
        UA --> GH[GitHub OAuth<br/>User authenticates]
        GH --> CB[Callback with<br/>GitHub user info]
        CB --> AC[Authorization code<br/>Binds client + user]
    end
    
    subgraph "Token Exchange"
        TE[POST /token<br/>client_id + client_secret<br/>+ auth code + PKCE]
        TE --> JWT[JWT access_token<br/>Contains both identities]
    end
    
    CC --> UA
    AC --> TE
    
    classDef registration fill:#9cf,stroke:#333,stroke-width:2px
    classDef auth fill:#fc9,stroke:#333,stroke-width:2px
    classDef token fill:#9fc,stroke:#333,stroke-width:2px
    
    class CR,CC,RT registration
    class UA,GH,CB,AC auth
    class TE,JWT token
```

## Complete Authorization Flow

```{mermaid}
sequenceDiagram
    participant Client as OAuth Client<br/>(e.g., Claude.ai)
    participant User as Human User
    participant Gateway as MCP OAuth Gateway
    participant GitHub as GitHub OAuth
    participant Redis as Redis Store
    
    Note over Client,Redis: Step 1: Client Registration (One-time)
    Client->>Gateway: POST /register<br/>{redirect_uris, client_name}
    Gateway->>Redis: Store client registration
    Gateway->>Client: 201 Created<br/>client_id: abc123<br/>client_secret: xyz789<br/>registration_access_token: reg_tok
    
    Note over Client,Redis: Step 2: User Authorization
    User->>Client: Initiate connection
    Client->>Client: Generate PKCE<br/>code_verifier & code_challenge
    Client->>User: Open browser
    User->>Gateway: GET /authorize<br/>?client_id=abc123<br/>&code_challenge=...
    Gateway->>Redis: Validate client_id
    Gateway->>User: 302 Redirect to GitHub
    User->>GitHub: Login & Authorize
    GitHub->>Gateway: GET /callback<br/>?code=gh_code
    Gateway->>GitHub: Exchange for user info
    GitHub->>Gateway: User: johndoe<br/>Email: john@example.com
    Gateway->>Gateway: Check ALLOWED_GITHUB_USERS
    Gateway->>Redis: Store auth code with<br/>client_id + user info
    Gateway->>User: 302 Redirect<br/>?code=auth_code
    User->>Client: Auth code received
    
    Note over Client,Redis: Step 3: Token Exchange
    Client->>Gateway: POST /token<br/>client_id=abc123<br/>client_secret=xyz789<br/>code=auth_code<br/>code_verifier=...
    Gateway->>Redis: Validate client credentials
    Gateway->>Redis: Get auth code data
    Gateway->>Gateway: Validate PKCE<br/>Verify client matches
    Gateway->>Gateway: Generate JWT with:<br/>- sub: github_user_id<br/>- username: johndoe<br/>- client_id: abc123
    Gateway->>Redis: Store tokens
    Gateway->>Client: 200 OK<br/>access_token: JWT<br/>refresh_token: opaque
    
    Note over Client,Redis: Step 4: Access Resources
    Client->>Gateway: GET /mcp<br/>Authorization: Bearer JWT
    Gateway->>Gateway: Validate JWT<br/>Extract identities
    Gateway->>Client: MCP Response<br/>X-User-Name: johndoe
```

### Key Points

- **client_id + client_secret** authenticate the OAuth CLIENT (e.g., Claude.ai)
- **GitHub OAuth** authenticates the human USER
- The final **access_token** contains BOTH: which client AND which user
- **registration_access_token** is ONLY for client management, NOT resource access

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