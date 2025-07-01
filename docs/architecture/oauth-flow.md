# OAuth Flow Architecture

Comprehensive documentation of the OAuth 2.1 flows implemented in the MCP OAuth Gateway, including dynamic client registration and PKCE.

## OAuth 2.1 Implementation

The gateway implements OAuth 2.1 with these key features:

- Authorization Code Flow with PKCE (mandatory)
- Dynamic Client Registration (RFC 7591)
- Client Configuration Management (RFC 7592)
- JWT access tokens with RS256 signing
- GitHub OAuth for user authentication

## Flow Overview

```{mermaid}
sequenceDiagram
    participant C as MCP Client
    participant G as Gateway (Traefik)
    participant A as Auth Service
    participant R as Redis
    participant GH as GitHub OAuth
    participant M as MCP Service

    Note over C,M: 1. Dynamic Client Registration
    C->>G: POST /register
    G->>A: Forward to Auth
    A->>R: Store client data
    A->>C: 201 Created (client credentials)

    Note over C,M: 2. Authorization Flow
    C->>C: Generate PKCE verifier/challenge
    C->>G: GET /authorize
    G->>A: Forward to Auth
    A->>GH: Redirect to GitHub
    GH->>A: Callback with code
    A->>C: Redirect with auth code

    Note over C,M: 3. Token Exchange
    C->>G: POST /token
    G->>A: Forward to Auth
    A->>R: Validate & store token
    A->>C: Access token (JWT)

    Note over C,M: 4. API Access
    C->>G: Request + Bearer token
    G->>A: ForwardAuth /verify
    A->>R: Validate token
    A->>G: 200 OK + headers
    G->>M: Forward request
    M->>C: Response
```

## Dynamic Client Registration (RFC 7591)

### Registration Request

```http
POST /register
Content-Type: application/json

{
  "client_name": "My MCP Client",
  "redirect_uris": ["http://localhost:8080/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "scope": "mcp:*",
  "token_endpoint_auth_method": "none"
}
```

### Registration Response

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "client_id": "client_7a3d5f2e",
  "client_secret": "secret_9b4c6e8d",
  "client_name": "My MCP Client",
  "redirect_uris": ["http://localhost:8080/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "scope": "mcp:*",
  "token_endpoint_auth_method": "none",
  "registration_access_token": "reg-4f7d9c2a",
  "registration_client_uri": "https://auth.example.com/register/client_7a3d5f2e",
  "client_secret_expires_at": 1743638400
}
```

### Registration Storage

```python
# Redis storage structure
oauth:client:client_7a3d5f2e = {
    "client_id": "client_7a3d5f2e",
    "client_secret": "secret_9b4c6e8d",
    "client_name": "My MCP Client",
    "redirect_uris": ["http://localhost:8080/callback"],
    "registration_access_token": "reg-4f7d9c2a",
    "created_at": "2024-01-01T00:00:00Z",
    "expires_at": "2024-04-01T00:00:00Z"
}
```

## Authorization Code Flow with PKCE

### Step 1: PKCE Generation

```python
import secrets
import hashlib
import base64

# Generate code verifier (43-128 characters)
code_verifier = base64.urlsafe_b64encode(
    secrets.token_bytes(32)
).decode('utf-8').rstrip('=')

# Generate code challenge (S256)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode('utf-8').rstrip('=')
```

### Step 2: Authorization Request

```
GET /authorize?
    client_id=client_7a3d5f2e&
    redirect_uri=http://localhost:8080/callback&
    response_type=code&
    scope=mcp:*&
    state=abc123xyz&
    code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&
    code_challenge_method=S256
```

### Step 3: User Authentication

```{mermaid}
sequenceDiagram
    participant U as User
    participant A as Auth Service
    participant G as GitHub

    U->>A: GET /authorize
    A->>A: Validate client_id
    A->>A: Store state + PKCE
    A->>G: Redirect to GitHub OAuth
    U->>G: Login + Authorize
    G->>A: Callback with code
    A->>A: Validate state
    A->>A: Generate auth code
    A->>U: Redirect to client
```

### Step 4: Token Exchange

```http
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
client_id=client_7a3d5f2e&
code=auth_9f3a7b2c&
redirect_uri=http://localhost:8080/callback&
code_verifier=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
```

### Token Response

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 2592000,
  "refresh_token": "refresh_8d4b2c7e",
  "scope": "mcp:*"
}
```

## JWT Token Structure

### Header
```json
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "key-1"
}
```

### Payload
```json
{
  "iss": "https://auth.example.com",
  "sub": "github|username",
  "aud": "client_7a3d5f2e",
  "exp": 1706745600,
  "iat": 1704153600,
  "jti": "token_3f8a9c2d",
  "scope": "mcp:*",
  "github_username": "username",
  "github_id": "12345",
  "github_email": "user@example.com"
}
```

### Signature
Generated using RS256 with the private key.

## Token Validation Flow

### ForwardAuth Middleware

```{mermaid}
sequenceDiagram
    participant C as Client
    participant T as Traefik
    participant A as Auth Service
    participant R as Redis
    participant S as MCP Service

    C->>T: Request + Bearer token
    T->>A: GET /verify
    Note over A: Extract token from header
    A->>A: Verify JWT signature
    A->>R: Check token not revoked
    A->>A: Validate claims
    A->>T: 200 OK + User headers
    T->>S: Forward + headers
    S->>T: Response
    T->>C: Response
```

### Validation Steps

1. **Extract Token**
   ```python
   auth_header = request.headers.get("Authorization")
   token = auth_header.split(" ")[1]  # Bearer TOKEN
   ```

2. **Verify Signature**
   ```python
   payload = jwt.decode(
       token,
       public_key,
       algorithms=["RS256"],
       audience=client_id
   )
   ```

3. **Check Revocation**
   ```python
   jti = payload["jti"]
   if redis.exists(f"oauth:revoked:{jti}"):
       raise TokenRevoked()
   ```

4. **Validate Claims**
   ```python
   if payload["exp"] < time():
       raise TokenExpired()
   if payload["iss"] != expected_issuer:
       raise InvalidIssuer()
   ```

## Client Management (RFC 7592)

### Read Client Configuration

```http
GET /register/client_7a3d5f2e
Authorization: Bearer reg-4f7d9c2a

Response:
{
  "client_id": "client_7a3d5f2e",
  "client_name": "My MCP Client",
  "redirect_uris": ["http://localhost:8080/callback"],
  ...
}
```

### Update Client Configuration

```http
PUT /register/client_7a3d5f2e
Authorization: Bearer reg-4f7d9c2a
Content-Type: application/json

{
  "client_name": "Updated Client Name",
  "redirect_uris": ["http://localhost:9090/callback"]
}
```

### Delete Client

```http
DELETE /register/client_7a3d5f2e
Authorization: Bearer reg-4f7d9c2a

Response: 204 No Content
```

## Security Considerations

### PKCE Protection

- Mandatory for all flows
- Prevents authorization code interception
- S256 challenge method required

### State Parameter

- CSRF protection
- Cryptographically random
- 5-minute expiration

### Token Security

- RS256 signing (asymmetric)
- Short-lived access tokens (30 days)
- Secure token storage in Redis
- Token revocation support

### Client Authentication

- Public clients supported (mobile/SPA)
- Client secret for confidential clients
- Registration access token for management

## Error Handling

### OAuth Errors

| Error | Description | HTTP Code |
|-------|-------------|-----------|
| `invalid_request` | Malformed request | 400 |
| `invalid_client` | Unknown client | 401 |
| `invalid_grant` | Invalid auth code | 400 |
| `unauthorized_client` | Client not authorized | 403 |
| `unsupported_grant_type` | Grant type not supported | 400 |
| `invalid_scope` | Requested scope invalid | 400 |

### Token Errors

| Error | Description | HTTP Code |
|-------|-------------|-----------|
| `invalid_token` | Token validation failed | 401 |
| `insufficient_scope` | Token lacks required scope | 403 |
| `token_expired` | Token past expiration | 401 |
| `token_revoked` | Token has been revoked | 401 |

## Integration Examples

### Python Client

```python
import httpx
from authlib.integrations.httpx_client import OAuth2Session

# Client registration
client = OAuth2Session(
    client_id=None,
    redirect_uri="http://localhost:8080/callback"
)

# Register client
reg_response = await client.post(
    "https://auth.example.com/register",
    json={
        "client_name": "Python MCP Client",
        "redirect_uris": ["http://localhost:8080/callback"]
    }
)
client_info = reg_response.json()

# Authorization flow
auth_url, state = client.create_authorization_url(
    "https://auth.example.com/authorize",
    code_challenge=code_challenge,
    code_challenge_method="S256"
)

# Token exchange
token = await client.fetch_token(
    "https://auth.example.com/token",
    authorization_response=callback_url,
    code_verifier=code_verifier
)
```

### JavaScript Client

```javascript
// Using PKCE
const codeVerifier = generateCodeVerifier();
const codeChallenge = await generateCodeChallenge(codeVerifier);

// Authorization URL
const params = new URLSearchParams({
  client_id: clientId,
  redirect_uri: redirectUri,
  response_type: 'code',
  scope: 'mcp:*',
  state: generateState(),
  code_challenge: codeChallenge,
  code_challenge_method: 'S256'
});

window.location.href = `https://auth.example.com/authorize?${params}`;

// Token exchange
const tokenResponse = await fetch('https://auth.example.com/token', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded'
  },
  body: new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: clientId,
    code: authCode,
    redirect_uri: redirectUri,
    code_verifier: codeVerifier
  })
});
```
