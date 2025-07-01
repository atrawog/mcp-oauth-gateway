# MCP OAuth Dynamic Client

A production-ready OAuth 2.1 authorization server with RFC 7591 dynamic client registration support, designed specifically for the MCP OAuth Gateway.

## Features

- **OAuth 2.1 Compliant** - Modern OAuth implementation with mandatory PKCE
- **Dynamic Client Registration** - RFC 7591 compliant automatic client setup
- **Client Management Protocol** - RFC 7592 compliant CRUD operations
- **GitHub OAuth Integration** - User authentication via GitHub
- **JWT Token Management** - RS256 (recommended) and HS256 support
- **ForwardAuth Compatible** - Works seamlessly with Traefik
- **Redis State Storage** - Scalable token and client storage
- **Token Introspection** - RFC 7662 compliant token validation
- **Token Revocation** - RFC 7009 compliant token lifecycle

## Installation

### Using pip

```bash
pip install mcp-oauth-dynamicclient
```

### Using pixi

```bash
pixi add --pypi mcp-oauth-dynamicclient
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install the package
RUN pip install mcp-oauth-dynamicclient

# Set environment variables (configure via .env or docker-compose)
ENV HOST=0.0.0.0
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Run the server
CMD ["mcp-oauth-server", "--host", "0.0.0.0", "--port", "8000"]
```

## Quick Start

### 1. Set up environment variables

Create a `.env` file with required configuration:

```bash
# GitHub OAuth App credentials
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# JWT Configuration
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=RS256  # or HS256
JWT_PRIVATE_KEY_B64=your_base64_encoded_rsa_key  # For RS256

# Domain configuration
BASE_DOMAIN=yourdomain.com

# Redis configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password  # Optional

# Token lifetimes (in seconds)
ACCESS_TOKEN_LIFETIME=1800      # 30 minutes
REFRESH_TOKEN_LIFETIME=31536000 # 1 year
SESSION_TIMEOUT=300             # 5 minutes
CLIENT_LIFETIME=7776000         # 90 days (0 = never expires)

# Access control
ALLOWED_GITHUB_USERS=user1,user2,user3  # or '*' for any GitHub user

# MCP Protocol version
MCP_PROTOCOL_VERSION=2025-06-18
```

### 2. Run the server

Using the CLI:

```bash
mcp-oauth-server --host 0.0.0.0 --port 8000
```

Using Python:

```python
from mcp_oauth_dynamicclient import create_app, Settings
import uvicorn

settings = Settings()  # Loads from .env
app = create_app(settings)

uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. Register a client

```python
import httpx
import asyncio

async def register_client():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://auth.yourdomain.com/register",
            json={
                "redirect_uris": ["https://myapp.com/callback"],
                "client_name": "My Application",
                "scope": "openid profile email"
            }
        )

        if response.status_code == 201:
            result = response.json()
            print(f"Client ID: {result['client_id']}")
            print(f"Client Secret: {result['client_secret']}")
            print(f"Registration Token: {result['registration_access_token']}")
            # Save these credentials securely!

asyncio.run(register_client())
```

## API Endpoints

### Public Endpoints

- `POST /register` - Register a new OAuth client (RFC 7591)
- `GET /.well-known/oauth-authorization-server` - Server metadata
- `GET /jwks` - JSON Web Key Set for token verification

### OAuth Flow Endpoints

- `GET /authorize` - Start authorization flow
- `POST /token` - Exchange authorization code for tokens
- `GET /callback` - GitHub OAuth callback handler

### Protected Endpoints (Require Bearer Token)

- `GET /verify` - Verify token for ForwardAuth
- `POST /revoke` - Revoke a token
- `POST /introspect` - Introspect token details

### Client Management (Require Registration Access Token)

- `GET /register/{client_id}` - Get client configuration
- `PUT /register/{client_id}` - Update client configuration
- `DELETE /register/{client_id}` - Delete client registration

## OAuth Flow

1. **Client Registration**
   - Client POSTs to `/register` with metadata
   - Receives `client_id`, `client_secret`, and `registration_access_token`

2. **Authorization**
   - Client redirects user to `/authorize` with PKCE challenge
   - User authenticates via GitHub
   - Server redirects back with authorization code

3. **Token Exchange**
   - Client POSTs code to `/token` with PKCE verifier
   - Receives JWT access token and refresh token

4. **Token Usage**
   - Client includes token in `Authorization: Bearer <token>` header
   - Server validates token on each request

## Security Features

- **PKCE Required** - Only S256 code challenge method supported
- **JWT Tokens** - Cryptographically signed with RS256 or HS256
- **Token Expiration** - Configurable lifetimes with automatic cleanup
- **GitHub User Validation** - Restrict access to specific GitHub users
- **Redis Token Storage** - Tokens can be revoked immediately
- **Registration Access Tokens** - Secure client management

## Docker Deployment

The service is designed to run in Docker with the MCP OAuth Gateway:

```yaml
services:
  auth:
    image: mcp-oauth-dynamicclient:latest
    environment:
      - GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
      - GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET}
      - JWT_SECRET=${JWT_SECRET}
      - JWT_ALGORITHM=RS256
      - JWT_PRIVATE_KEY_B64=${JWT_PRIVATE_KEY_B64}
      - BASE_DOMAIN=${BASE_DOMAIN}
      - REDIS_URL=redis://redis:6379/0
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - ACCESS_TOKEN_LIFETIME=1800
      - REFRESH_TOKEN_LIFETIME=31536000
      - SESSION_TIMEOUT=300
      - CLIENT_LIFETIME=7776000
      - ALLOWED_GITHUB_USERS=${ALLOWED_GITHUB_USERS}
      - MCP_PROTOCOL_VERSION=2025-06-18
    depends_on:
      - redis
    networks:
      - internal
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.auth.rule=Host(`auth.${BASE_DOMAIN}`)"
      - "traefik.http.routers.auth.tls=true"
      - "traefik.http.routers.auth.tls.certresolver=letsencrypt"
```

## Traefik Integration

Configure Traefik to use this service for authentication:

```yaml
# ForwardAuth middleware
- "traefik.http.middlewares.auth.forwardauth.address=http://auth:8000/verify"
- "traefik.http.middlewares.auth.forwardauth.authResponseHeaders=X-User-Id,X-User-Name,X-Auth-Token"

# Apply to protected services
- "traefik.http.routers.myservice.middlewares=auth"
```

## Development

### Running tests

```bash
# Start dependencies
docker-compose up -d redis

# Run tests
pytest
```

### Development mode

```bash
# Install in development mode
pip install -e .

# Run with auto-reload
mcp-oauth-server --reload
```

## Configuration Reference

| Environment Variable | Description | Default | Required |
|---------------------|-------------|---------|----------|
| `GITHUB_CLIENT_ID` | GitHub OAuth App Client ID | - | Yes |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App Client Secret | - | Yes |
| `JWT_SECRET` | Secret key for HS256 JWT signing | - | Yes |
| `JWT_ALGORITHM` | JWT signing algorithm (RS256 or HS256) | - | Yes |
| `JWT_PRIVATE_KEY_B64` | Base64 encoded RSA private key (RS256 only) | - | If RS256 |
| `BASE_DOMAIN` | Base domain for OAuth URLs | - | Yes |
| `REDIS_URL` | Redis connection URL | - | Yes |
| `REDIS_PASSWORD` | Redis password | - | No |
| `ACCESS_TOKEN_LIFETIME` | Access token lifetime in seconds | - | Yes |
| `REFRESH_TOKEN_LIFETIME` | Refresh token lifetime in seconds | - | Yes |
| `SESSION_TIMEOUT` | OAuth state timeout in seconds | - | Yes |
| `CLIENT_LIFETIME` | Client registration lifetime (0=never) | - | Yes |
| `ALLOWED_GITHUB_USERS` | Comma-separated GitHub usernames or '*' | - | Yes |
| `MCP_PROTOCOL_VERSION` | MCP protocol version | - | Yes |

## License

Apache-2.0 License

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass with real Redis (no mocks!)
2. Code follows the established patterns
3. New endpoints are RFC compliant
4. Documentation is updated

See [CLAUDE.md](./CLAUDE.md) for detailed development guidelines.
