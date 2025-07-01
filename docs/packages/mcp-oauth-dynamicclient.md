# mcp-oauth-dynamicclient

The divine OAuth 2.1 server implementation with full RFC 7591/7592 compliance for dynamic client registration and management.

## Overview

`mcp-oauth-dynamicclient` is the OAuth oracle of the gateway, handling all authentication and authorization flows. It provides:

- OAuth 2.1 compliant authorization server
- Dynamic client registration (RFC 7591)
- Client configuration management (RFC 7592)
- GitHub OAuth integration for user authentication
- JWT token generation with RS256 signing
- Redis-backed storage for tokens and client data

## Key Features

### RFC Compliance
- **OAuth 2.1** - Latest OAuth specification
- **RFC 7591** - Dynamic Client Registration
- **RFC 7592** - OAuth 2.0 Dynamic Client Registration Management
- **RFC 7636** - PKCE (Proof Key for Code Exchange)
- **RFC 8414** - OAuth 2.0 Authorization Server Metadata

### Security Features
- JWT tokens with RS256 signing
- PKCE mandatory for all flows
- Secure session management
- CSRF protection via state parameter
- Origin header validation
- Token expiration and refresh

## Architecture

```python
# Main components
OAuthServer          # Core OAuth server implementation
DynamicClientEndpoint # RFC 7591 registration endpoint
DynamicClientConfigurationEndpoint # RFC 7592 management
JWTService          # Token generation and validation
RedisStorage        # Persistent storage backend
```

## API Endpoints

### OAuth 2.0 Core Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/authorize` | GET | Authorization endpoint |
| `/token` | POST | Token exchange endpoint |
| `/callback` | GET | OAuth callback handler |
| `/revoke` | POST | Token revocation |
| `/introspect` | POST | Token introspection |

### RFC 7591 Registration

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/register` | POST | Register new client | None (public) |

### RFC 7592 Management

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/register/{client_id}` | GET | Read client config | Bearer (registration token) |
| `/register/{client_id}` | PUT | Update client config | Bearer (registration token) |
| `/register/{client_id}` | DELETE | Delete client | Bearer (registration token) |

### Discovery

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/.well-known/oauth-authorization-server` | GET | Server metadata |

## Configuration

### Environment Variables

```bash
# GitHub OAuth (required)
GITHUB_CLIENT_ID=xxx
GITHUB_CLIENT_SECRET=xxx

# JWT Configuration
GATEWAY_JWT_SECRET=xxx  # or RSA keys
GATEWAY_RSA_PRIVATE_KEY=xxx
GATEWAY_RSA_PUBLIC_KEY=xxx

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=xxx

# Token Lifetimes
ACCESS_TOKEN_LIFETIME=2592000  # 30 days
REFRESH_TOKEN_LIFETIME=31536000  # 1 year
CLIENT_LIFETIME=7776000  # 90 days (0 for eternal)

# Access Control
ALLOWED_GITHUB_USERS=user1,user2,user3
```

## Client Registration Flow

### 1. Dynamic Registration (RFC 7591)

```bash
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

Response (201 Created):
{
  "client_id": "client_abc123",
  "client_secret": "secret_xyz789",
  "registration_access_token": "reg-token123",
  "registration_client_uri": "https://auth.example.com/register/client_abc123",
  "client_name": "My MCP Client",
  "redirect_uris": ["http://localhost:8080/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "client_secret_expires_at": 1234567890
}
```

### 2. Client Management (RFC 7592)

```bash
# Read client configuration
GET /register/client_abc123
Authorization: Bearer reg-token123

# Update client configuration
PUT /register/client_abc123
Authorization: Bearer reg-token123
Content-Type: application/json

{
  "client_name": "Updated Client Name",
  "redirect_uris": ["http://localhost:9090/callback"]
}

# Delete client
DELETE /register/client_abc123
Authorization: Bearer reg-token123
```

## OAuth Flow with PKCE

### 1. Generate PKCE Challenge

```python
import secrets
import hashlib
import base64

# Generate code verifier
code_verifier = base64.urlsafe_b64encode(
    secrets.token_bytes(32)
).decode('utf-8').rstrip('=')

# Generate code challenge
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode('utf-8').rstrip('=')
```

### 2. Authorization Request

```
GET /authorize?
  client_id=client_abc123&
  redirect_uri=http://localhost:8080/callback&
  response_type=code&
  scope=mcp:*&
  state=random_state&
  code_challenge=challenge_value&
  code_challenge_method=S256
```

### 3. Token Exchange

```bash
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
client_id=client_abc123&
code=auth_code_value&
redirect_uri=http://localhost:8080/callback&
code_verifier=verifier_value
```

## JWT Token Structure

```json
{
  "iss": "https://auth.example.com",
  "sub": "github|username",
  "aud": "client_abc123",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "unique_token_id",
  "scope": "mcp:*",
  "github_username": "username"
}
```

## Redis Storage Schema

```
oauth:state:{state}          # CSRF state (5 min TTL)
oauth:code:{code}            # Authorization codes (1 year TTL)
oauth:token:{jti}            # Access tokens (30 days TTL)
oauth:refresh:{token}        # Refresh tokens (1 year TTL)
oauth:client:{client_id}     # Client data (includes registration_access_token)
oauth:user_tokens:{username} # User token index (no expiry)
```

## Integration with Gateway

### As Standalone Service

```yaml
# auth/docker-compose.yml
services:
  auth:
    build: .
    environment:
      - GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
      - GATEWAY_JWT_SECRET=${GATEWAY_JWT_SECRET}
    depends_on:
      - redis
    labels:
      - "traefik.http.routers.auth.rule=Host(`auth.${BASE_DOMAIN}`)"
      - "traefik.http.routers.auth.priority=4"
```

### ForwardAuth Integration

```yaml
# Traefik middleware configuration
- "traefik.http.middlewares.mcp-auth.forwardauth.address=http://auth:8000/verify"
- "traefik.http.middlewares.mcp-auth.forwardauth.authResponseHeaders=X-User-Id,X-User-Name"
```

## Security Considerations

1. **Token Storage**: All tokens stored in Redis with appropriate TTLs
2. **PKCE Required**: Prevents authorization code interception
3. **State Validation**: CSRF protection on authorization flow
4. **Origin Checking**: Validates request origins
5. **User Allowlist**: GitHub users must be in ALLOWED_GITHUB_USERS

## Testing

```bash
# Run package tests
just pypi-test mcp-oauth-dynamicclient

# Integration tests
just test tests/test_oauth_flow.py -v
```

## Troubleshooting

### Client Registration Fails
- Check Redis connectivity
- Verify redirect_uris format
- Ensure unique client_name

### Token Validation Fails
- Check JWT secret/keys match
- Verify token not expired
- Ensure Redis has token data

### GitHub OAuth Issues
- Verify GitHub app credentials
- Check callback URL configuration
- Ensure user in allowlist

## CLI Tools

The package includes management scripts:

```bash
# Generate JWT secret
pixi run python -m mcp_oauth_dynamicclient.generate_jwt_secret

# Manage OAuth data
pixi run python -m mcp_oauth_dynamicclient.manage_oauth_data

# Token validation
pixi run python -m mcp_oauth_dynamicclient.validate_tokens
```
