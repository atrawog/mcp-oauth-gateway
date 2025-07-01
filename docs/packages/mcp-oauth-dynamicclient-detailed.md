# mcp-oauth-dynamicclient

## Overview

The `mcp-oauth-dynamicclient` package is the cornerstone of the MCP OAuth Gateway, providing a production-ready OAuth 2.1 authorization server with full support for RFC 7591 (Dynamic Client Registration) and RFC 7592 (Client Management Protocol). This package handles all OAuth authentication flows, client registration, and token management for the gateway.

## Key Features

### OAuth 2.1 Compliance
- Implements the latest OAuth 2.1 specification
- Mandatory PKCE (Proof Key for Code Exchange) with S256 method only
- No implicit grant support (as per OAuth 2.1)
- Secure by default configuration

### Dynamic Client Registration (RFC 7591)
- Public `/register` endpoint for automatic client setup
- No pre-registration required
- Returns client credentials and registration access token
- Supports all standard client metadata fields

### Client Management Protocol (RFC 7592)
- GET/PUT/DELETE operations on `/register/{client_id}`
- Protected by registration access tokens
- Client configuration updates
- Self-service client lifecycle management

### GitHub OAuth Integration
- User authentication via GitHub OAuth
- Configurable user access control
- JWT tokens include GitHub user information
- Support for organization-based access

### Token Management
- JWT tokens with RS256 (recommended) or HS256 signing
- Configurable token lifetimes
- Refresh token support
- Redis-based token storage for instant revocation

## Architecture

### Core Components

```
mcp_oauth_dynamicclient/
├── __init__.py              # Package initialization
├── __main__.py              # Module entry point
├── cli.py                   # CLI interface
├── server.py                # FastAPI app factory
├── routes.py                # OAuth endpoint routes
├── rfc7592.py              # Client management endpoints
├── auth_authlib.py         # Authlib OAuth server setup
├── async_resource_protector.py  # Async token validation
├── resource_protector.py   # Sync token validation
├── models.py               # Pydantic data models
├── config.py               # Settings management
├── keys.py                 # JWT key handling
└── redis_client.py         # Redis connection management
```

### Key Classes and Functions

#### Settings (config.py)
```python
class Settings(BaseSettings):
    # GitHub OAuth
    github_client_id: str
    github_client_secret: str

    # JWT Configuration
    jwt_secret: str
    jwt_algorithm: str = "RS256"
    jwt_private_key_b64: Optional[str] = None

    # Domain Configuration
    base_domain: str

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None

    # Token Lifetimes
    access_token_lifetime: int = 1800  # 30 minutes
    refresh_token_lifetime: int = 31536000  # 1 year
    session_timeout: int = 300  # 5 minutes
    client_lifetime: int = 7776000  # 90 days
```

#### OAuth Server Setup (auth_authlib.py)
- Configures Authlib's AuthorizationServer
- Implements client authentication methods
- Handles token generation and validation
- Integrates with Redis for state management

#### Dynamic Registration (routes.py)
- POST /register endpoint implementation
- Validates client metadata
- Generates client credentials
- Issues registration access token

#### Client Management (rfc7592.py)
- Implements RFC 7592 endpoints
- Bearer token authentication
- Client configuration CRUD operations
- Secure token validation

## API Endpoints

### Public Endpoints

#### POST /register
Dynamic client registration endpoint.

**Request:**
```json
{
  "redirect_uris": ["https://app.example.com/callback"],
  "client_name": "My Application",
  "client_uri": "https://app.example.com",
  "logo_uri": "https://app.example.com/logo.png",
  "scope": "openid profile email",
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"]
}
```

**Response (201 Created):**
```json
{
  "client_id": "dyn_abc123...",
  "client_secret": "secret_xyz789...",
  "client_id_issued_at": 1735680912,
  "client_secret_expires_at": 0,
  "registration_access_token": "reg_token123...",
  "registration_client_uri": "https://auth.domain.com/register/dyn_abc123..."
}
```

#### GET /.well-known/oauth-authorization-server
Server metadata discovery endpoint.

### OAuth Flow Endpoints

#### GET /authorize
Initiates authorization flow with PKCE.

**Parameters:**
- `client_id` - Registered client ID
- `redirect_uri` - Callback URL
- `response_type=code` - Must be "code"
- `state` - CSRF protection
- `code_challenge` - PKCE challenge
- `code_challenge_method=S256` - Must be S256
- `scope` - Requested permissions

#### POST /token
Exchanges authorization code for tokens.

**Request:**
```json
{
  "grant_type": "authorization_code",
  "code": "auth_code_here",
  "redirect_uri": "https://app.example.com/callback",
  "client_id": "dyn_abc123",
  "client_secret": "secret_xyz789",
  "code_verifier": "pkce_verifier_here"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "refresh_token": "refresh_xyz...",
  "scope": "openid profile email"
}
```

### Protected Endpoints

#### GET /verify
ForwardAuth endpoint for Traefik.

**Headers:**
- `Authorization: Bearer <token>`

**Response Headers:**
- `X-User-Id` - GitHub user ID
- `X-User-Name` - GitHub username
- `X-Auth-Token` - Access token

#### POST /revoke
Token revocation endpoint (RFC 7009).

#### POST /introspect
Token introspection endpoint (RFC 7662).

### Client Management Endpoints (RFC 7592)

#### GET /register/{client_id}
Retrieve client configuration.

**Headers:**
- `Authorization: Bearer <registration_access_token>`

#### PUT /register/{client_id}
Update client configuration.

#### DELETE /register/{client_id}
Delete client registration.

## Configuration

### Environment Variables

```bash
# Required
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY_B64=base64_encoded_rsa_private_key
BASE_DOMAIN=yourdomain.com
REDIS_URL=redis://redis:6379/0

# Optional
REDIS_PASSWORD=redis_password
ACCESS_TOKEN_LIFETIME=1800      # 30 minutes
REFRESH_TOKEN_LIFETIME=31536000 # 1 year
SESSION_TIMEOUT=300             # 5 minutes
CLIENT_LIFETIME=7776000         # 90 days (0 = never)
ALLOWED_GITHUB_USERS=user1,user2,user3  # or '*'
MCP_PROTOCOL_VERSION=2025-06-18
```

### JWT Configuration

#### RS256 (Recommended)
Generate RSA key pair:
```bash
# Generate private key
openssl genrsa -out private_key.pem 2048

# Extract public key
openssl rsa -in private_key.pem -pubout -out public_key.pem

# Base64 encode for .env
cat private_key.pem | base64 -w 0 > private_key_b64.txt
```

#### HS256 (Simpler but less secure)
Just set `JWT_SECRET` to a strong random string.

## Redis Storage Schema

### Key Patterns
```
oauth:state:{state}          # OAuth state (5 min TTL)
oauth:code:{code}            # Auth codes (1 year TTL)
oauth:token:{jti}            # Access tokens (30 days TTL)
oauth:refresh:{token}        # Refresh tokens (1 year TTL)
oauth:client:{client_id}     # Client data (client lifetime)
oauth:user_tokens:{username} # User token index (no expiry)
```

### Client Data Structure
```json
{
  "client_id": "dyn_abc123",
  "client_secret": "secret_xyz789",
  "client_id_issued_at": 1735680912,
  "client_secret_expires_at": 0,
  "registration_access_token": "reg_token123",
  "redirect_uris": ["https://app.example.com/callback"],
  "client_name": "My Application",
  "scope": "openid profile email",
  "grant_types": ["authorization_code", "refresh_token"]
}
```

## Security Considerations

### PKCE Enforcement
- Only S256 code challenge method allowed
- Verifier must be 43-128 characters
- Prevents authorization code interception

### Token Security
- JWT tokens signed with RS256 or HS256
- Short-lived access tokens (30 min default)
- Long-lived refresh tokens (1 year default)
- Instant revocation via Redis

### Client Authentication
- Dynamic clients receive strong random credentials
- Registration access tokens for management
- Client secrets never logged or exposed

### User Access Control
- GitHub user allowlist via ALLOWED_GITHUB_USERS
- Set to '*' to allow any GitHub user
- JWT includes GitHub user information

## Integration Examples

### Traefik ForwardAuth
```yaml
labels:
  - "traefik.http.middlewares.auth.forwardauth.address=http://auth:8000/verify"
  - "traefik.http.middlewares.auth.forwardauth.authResponseHeaders=X-User-Id,X-User-Name,X-Auth-Token"
```

### Docker Deployment
```yaml
services:
  auth:
    build: ./mcp-oauth-dynamicclient
    environment:
      - GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
      - GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET}
      - JWT_SECRET=${JWT_SECRET}
      - JWT_ALGORITHM=RS256
      - JWT_PRIVATE_KEY_B64=${JWT_PRIVATE_KEY_B64}
      - BASE_DOMAIN=${BASE_DOMAIN}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    networks:
      - internal
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.auth.rule=Host(`auth.${BASE_DOMAIN}`)"
```

## Error Handling

### OAuth Errors
The service returns RFC 6749 compliant error responses:
- `invalid_request` - Malformed request
- `invalid_client` - Client authentication failed
- `invalid_grant` - Invalid authorization code
- `unauthorized_client` - Client not authorized
- `unsupported_grant_type` - Grant type not supported

### HTTP Status Codes
- 200 OK - Successful token request
- 201 Created - Client registration successful
- 302 Found - Authorization redirects
- 400 Bad Request - Invalid request
- 401 Unauthorized - Authentication required
- 403 Forbidden - Access denied
- 404 Not Found - Resource not found

## Performance Considerations

### Redis Connection Pooling
- Async Redis client with connection pooling
- Configurable pool size via connection URL
- Automatic reconnection on failure

### Token Caching
- JWT validation results cached
- Reduces cryptographic overhead
- TTL matches token lifetime

### Async Implementation
- Full async/await support
- Non-blocking I/O operations
- High concurrency capability

## Monitoring and Logging

### Health Check
```bash
curl http://localhost:8000/health
```

### Metrics
- Token issuance rate
- Failed authentication attempts
- Client registration count
- Active session count

### Logging
- Structured JSON logging available
- Log level configurable
- Sensitive data never logged

## Common Issues and Solutions

### Issue: "No module named 'authlib'"
**Solution**: Install with pip or pixi:
```bash
pip install mcp-oauth-dynamicclient
# or
pixi add --pypi mcp-oauth-dynamicclient
```

### Issue: JWT signature verification failed
**Solution**: Ensure JWT_PRIVATE_KEY_B64 is properly base64 encoded and matches the algorithm.

### Issue: Redis connection refused
**Solution**: Check REDIS_URL and ensure Redis is running.

### Issue: GitHub OAuth callback fails
**Solution**: Verify GitHub OAuth app settings match your domain configuration.

## Best Practices

1. **Use RS256 for JWT signing** - More secure than HS256
2. **Set appropriate token lifetimes** - Balance security and UX
3. **Implement token rotation** - Use refresh tokens properly
4. **Monitor failed attempts** - Detect potential attacks
5. **Regular security audits** - Review client registrations
6. **Backup Redis data** - Prevent data loss
7. **Use HTTPS everywhere** - Never expose tokens over HTTP

## Future Enhancements

- [ ] Support for additional OAuth flows
- [ ] Multi-tenant capabilities
- [ ] Enhanced token introspection
- [ ] Metrics dashboard
- [ ] Automated key rotation
- [ ] WebAuthn support
