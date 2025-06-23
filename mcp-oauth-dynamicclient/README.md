# mcp-oauth-dynamicclient

A production-ready OAuth 2.1 library with Dynamic Client Registration (RFC 7591/7592) support, designed for Model Context Protocol (MCP) integration. This package provides the core OAuth implementation used by the MCP OAuth Gateway.

## Overview

This library implements:
- **OAuth 2.1**: Full authorization server implementation with PKCE
- **RFC 7591**: Dynamic client registration for self-service OAuth clients
- **RFC 7592**: Client configuration management endpoints
- **GitHub Integration**: Built-in GitHub OAuth provider support
- **JWT Tokens**: Secure token generation with customizable claims
- **Redis Backend**: Scalable storage for tokens and client data

## Key Features

- 🔐 **Complete OAuth 2.1 Implementation**: Authorization code flow with PKCE
- 📝 **Dynamic Client Registration**: Self-service client onboarding via RFC 7591
- 🔧 **Client Management API**: Full CRUD operations via RFC 7592
- 🎫 **JWT Token Generation**: HS256-signed tokens with configurable lifetime
- 🌐 **GitHub OAuth Integration**: Pre-configured GitHub provider support
- 📦 **Redis Storage**: Production-ready persistence layer
- 🔒 **ForwardAuth Support**: Token validation for reverse proxies
- 📚 **Metadata Discovery**: RFC 8414 compliant server metadata

## Installation

```bash
# Via pixi (recommended)
pixi add mcp-oauth-dynamicclient

# Or from source
cd mcp-oauth-dynamicclient
pixi install -e .
```

## Quick Start

### 1. Environment Configuration

Create a `.env` file with required settings:

```bash
# GitHub OAuth App credentials
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# JWT signing secret (minimum 32 characters)
GATEWAY_JWT_SECRET=your-secret-key-at-least-32-chars

# Redis connection
REDIS_URL=redis://redis:6379/0

# Optional: Access control
ALLOWED_GITHUB_USERS=user1,user2,user3

# Optional: Client lifetime (seconds, 0 = eternal)
CLIENT_LIFETIME=7776000  # 90 days default
```

### 2. Using as a Library

```python
from mcp_oauth_dynamicclient import create_app, Settings

# Create FastAPI application
settings = Settings()  # Loads from .env
app = create_app(settings)

# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. Using the CLI

```bash
# Start OAuth server
pixi run mcp-oauth-server

# Generate GitHub token (for gateway's own use)
pixi run mcp-oauth-token
```

## Architecture

### Module Structure

```
mcp_oauth_dynamicclient/
├── config.py              # Pydantic settings management
├── models.py              # Data models and schemas
├── keys.py                # RSA key generation utilities
├── routes.py              # FastAPI route definitions
├── auth_authlib.py        # Authlib OAuth server setup
├── resource_protector.py  # Token validation
├── async_resource_protector.py  # Async token validation
├── redis_client.py        # Redis storage operations
├── rfc7592.py            # Client management endpoints
├── server.py             # FastAPI app factory
└── cli.py                # Command-line interface
```

### Core Components

1. **OAuth Server (Authlib)**
   - Authorization code grant with PKCE
   - Refresh token support
   - Token introspection

2. **Dynamic Registration**
   - Public `/register` endpoint
   - Automatic client_id/secret generation
   - Optional expiration support

3. **Client Management (RFC 7592)**
   - Bearer token protected endpoints
   - GET/PUT/DELETE operations
   - Registration access tokens

4. **Storage Layer**
   - Redis for all persistent data
   - Configurable TTLs
   - Atomic operations

## API Reference

### OAuth 2.1 Endpoints

#### POST /register - Dynamic Client Registration
```bash
curl -X POST https://auth.example.com/register \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_uris": ["https://app.example.com/callback"],
    "client_name": "My MCP Client",
    "scope": "read write"
  }'
```

Response includes:
- `client_id`: Unique client identifier
- `client_secret`: Client authentication secret
- `registration_access_token`: Token for managing this registration
- `registration_client_uri`: URI for client management

#### GET /authorize - Authorization Endpoint
Initiates OAuth flow with PKCE:
```
https://auth.example.com/authorize?
  client_id=client_xxxxx&
  redirect_uri=https://app.example.com/callback&
  response_type=code&
  state=random_state&
  code_challenge=challenge&
  code_challenge_method=S256
```

#### POST /token - Token Exchange
```bash
curl -X POST https://auth.example.com/token \
  -d "grant_type=authorization_code" \
  -d "code=auth_code" \
  -d "client_id=client_xxxxx" \
  -d "client_secret=secret_xxxxx" \
  -d "code_verifier=verifier"
```

### Client Management (RFC 7592)

#### GET /register/{client_id}
```bash
curl -H "Authorization: Bearer {registration_access_token}" \
  https://auth.example.com/register/{client_id}
```

#### PUT /register/{client_id}
```bash
curl -X PUT https://auth.example.com/register/{client_id} \
  -H "Authorization: Bearer {registration_access_token}" \
  -H "Content-Type: application/json" \
  -d '{"client_name": "Updated Name"}'
```

#### DELETE /register/{client_id}
```bash
curl -X DELETE https://auth.example.com/register/{client_id} \
  -H "Authorization: Bearer {registration_access_token}"
```

### Metadata Discovery

#### GET /.well-known/oauth-authorization-server
Returns server capabilities and endpoint URLs following RFC 8414.

### Token Validation

#### GET /verify - ForwardAuth Endpoint
Used by reverse proxies to validate tokens:
```bash
curl -H "Authorization: Bearer {access_token}" \
  https://auth.example.com/verify
```

Returns headers:
- `X-User-Id`: GitHub user ID
- `X-User-Name`: GitHub username
- `X-Auth-Token`: Token identifier

## Integration Examples

### With FastAPI Services

```python
from mcp_oauth_dynamicclient import verify_token, get_current_user
from fastapi import Depends

@app.get("/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"user": user.name}
```

### With Traefik

```yaml
labels:
  - "traefik.http.middlewares.auth.forwardauth.address=http://auth:8000/verify"
  - "traefik.http.middlewares.auth.forwardauth.authResponseHeaders=X-User-Id,X-User-Name"
```

## Security Considerations

### Token Security
- JWT tokens signed with HS256
- Configurable expiration (default: 30 days)
- Unique JTI for tracking/revocation
- Stored in Redis with TTL

### Client Security
- Cryptographically secure client secrets
- Optional client expiration
- Registration access tokens for management
- Redirect URI validation

### PKCE Implementation
- S256 challenge method required
- 43-128 character verifiers
- One-time authorization codes
- 5-minute code expiration

## Configuration Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GITHUB_CLIENT_ID` | GitHub OAuth App ID | - | Yes |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App Secret | - | Yes |
| `GATEWAY_JWT_SECRET` | JWT signing secret | - | Yes |
| `GATEWAY_JWT_ALGORITHM` | JWT algorithm | HS256 | No |
| `GATEWAY_JWT_EXPIRE_MINUTES` | Token lifetime | 43200 | No |
| `REDIS_URL` | Redis connection URL | redis://redis:6379/0 | No |
| `ALLOWED_GITHUB_USERS` | Whitelist (comma-separated) | - | No |
| `CLIENT_LIFETIME` | Client registration lifetime | 7776000 | No |
| `MCP_PROTOCOL_VERSION` | MCP protocol version | 2025-06-18 | No |

## Development

```bash
# Clone repository
git clone https://github.com/atrawog/mcp-oauth-gateway
cd mcp-oauth-gateway/mcp-oauth-dynamicclient

# Install with dev dependencies
pixi install -e .

# Run tests
pixi run pytest tests/ -v

# Run with auto-reload
pixi run uvicorn mcp_oauth_dynamicclient.server:create_app --factory --reload
```

## Testing

The package includes comprehensive tests:
```bash
# Unit tests
pixi run pytest tests/test_models.py -v

# Integration tests (requires Redis)
pixi run pytest tests/test_oauth_flow.py -v

# RFC compliance tests
pixi run pytest tests/test_rfc7592.py -v
```

## Redis Key Structure

```
oauth:state:{state}              # OAuth state (5 min TTL)
oauth:code:{code}                # Auth codes (5 min TTL)
oauth:token:{jti}                # Access tokens (30 day TTL)
oauth:refresh:{token}            # Refresh tokens (1 year TTL)
oauth:client:{client_id}         # Client registrations
oauth:registration_token:{token} # Registration access tokens
oauth:user_tokens:{username}     # User token index
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Author

Andreas Trawoeger

## Links

- [Homepage](https://github.com/atrawog/mcp-oauth-gateway/tree/main/mcp-oauth-dynamicclient)
- [Repository](https://github.com/atrawog/mcp-oauth-gateway/tree/main/mcp-oauth-dynamicclient)
- [Documentation](https://atrawog.github.io/mcp-oauth-gateway)
- [Issues](https://github.com/atrawog/mcp-oauth-gateway/issues)