# MCP OAuth Dynamic Client

A production-ready OAuth 2.1 server with Dynamic Client Registration (RFC 7591) support, designed for Model Context Protocol (MCP) integration.

## Features

- **OAuth 2.1 Compliant**: Full implementation of OAuth 2.1 authorization flows
- **RFC 7591 Dynamic Client Registration**: Self-service client registration
- **PKCE Support**: Proof Key for Code Exchange (RFC 7636) with S256 challenge
- **GitHub Integration**: Built-in GitHub OAuth provider support
- **JWT Tokens**: Secure token management with configurable lifetimes
- **Redis Backend**: Scalable session and token storage
- **ForwardAuth Compatible**: Works seamlessly with Traefik and other reverse proxies
- **Production Ready**: Health checks, proper error handling, and comprehensive logging

## Installation

```bash
pip install mcp-oauth-dynamicclient
```

## Quick Start

### 1. Set up environment variables

Create a `.env` file with the required configuration:

```bash
# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# JWT Configuration  
JWT_SECRET=your_jwt_secret_key_at_least_32_chars

# Domain Configuration
BASE_DOMAIN=your-domain.com

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password  # Optional

# Access Control (Optional)
ALLOWED_GITHUB_USERS=user1,user2,user3
```

### 2. Run the server

```bash
# Using the CLI
mcp-oauth-server

# Or with custom options
mcp-oauth-server --host 0.0.0.0 --port 8000

# Development mode with auto-reload
mcp-oauth-server --reload
```

### 3. Using as a library

```python
from mcp_oauth_dynamicclient import create_app, Settings

# Create settings
settings = Settings()

# Create FastAPI app
app = create_app(settings)

# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## API Endpoints

### OAuth 2.1 Endpoints

- `POST /register` - Dynamic client registration (RFC 7591)
- `GET /authorize` - OAuth authorization endpoint
- `GET /callback` - OAuth callback handler
- `POST /token` - Token exchange endpoint
- `POST /revoke` - Token revocation (RFC 7009)
- `POST /introspect` - Token introspection (RFC 7662)

### Metadata & Discovery

- `GET /.well-known/oauth-authorization-server` - Server metadata (RFC 8414)
- `GET /health` - Health check endpoint

### ForwardAuth

- `GET/POST /verify` - Token verification for reverse proxies

## Dynamic Client Registration

Register a new OAuth client:

```bash
curl -X POST https://auth.your-domain.com/register \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_uris": ["https://your-app.com/callback"],
    "client_name": "My Application",
    "scope": "openid profile email"
  }'
```

Response:
```json
{
  "client_id": "client_xxxxxxxxxxxxx",
  "client_secret": "secret_xxxxxxxxxxxxx",
  "client_secret_expires_at": 0,
  "redirect_uris": ["https://your-app.com/callback"],
  "client_name": "My Application",
  "scope": "openid profile email",
  "client_id_issued_at": 1234567890
}
```

## OAuth Flow Example

1. **Initiate authorization**:
```
https://auth.your-domain.com/authorize?
  client_id=client_xxxxxxxxxxxxx&
  redirect_uri=https://your-app.com/callback&
  response_type=code&
  scope=openid%20profile%20email&
  state=random_state_value&
  code_challenge=challenge_value&
  code_challenge_method=S256
```

2. **Exchange code for token**:
```bash
curl -X POST https://auth.your-domain.com/token \
  -d "grant_type=authorization_code" \
  -d "code=auth_code_from_callback" \
  -d "redirect_uri=https://your-app.com/callback" \
  -d "client_id=client_xxxxxxxxxxxxx" \
  -d "client_secret=secret_xxxxxxxxxxxxx" \
  -d "code_verifier=verifier_value"
```

## Integration with Traefik

Example docker-compose configuration:

```yaml
services:
  auth:
    image: mcp-oauth-dynamicclient
    environment:
      - GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
      - GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET}
      - JWT_SECRET=${JWT_SECRET}
      - BASE_DOMAIN=${BASE_DOMAIN}
      - REDIS_URL=redis://redis:6379/0
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.auth.rule=Host(`auth.${BASE_DOMAIN}`)"
      - "traefik.http.routers.auth.tls=true"
      - "traefik.http.services.auth.loadbalancer.server.port=8000"
      - "traefik.http.middlewares.auth-verify.forwardauth.address=http://auth:8000/verify"
      - "traefik.http.middlewares.auth-verify.forwardauth.authResponseHeaders=X-User-Id,X-User-Name"
```

## Development

### Setup development environment

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-oauth-dynamicclient
cd mcp-oauth-dynamicclient

# Install development dependencies
pip install -e ".[dev]"
```

### Run tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_oauth_dynamicclient

# Run specific test
pytest tests/test_oauth_flow.py -v
```

### Code quality

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

## Configuration Reference

| Environment Variable | Description | Default | Required |
|---------------------|-------------|---------|----------|
| `GITHUB_CLIENT_ID` | GitHub OAuth App Client ID | - | Yes |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App Client Secret | - | Yes |
| `JWT_SECRET` | Secret key for JWT signing (min 32 chars) | - | Yes |
| `BASE_DOMAIN` | Base domain for OAuth URLs | - | Yes |
| `REDIS_URL` | Redis connection URL | - | Yes |
| `REDIS_PASSWORD` | Redis password | None | No |
| `ACCESS_TOKEN_LIFETIME` | Access token lifetime in seconds | 86400 | No |
| `REFRESH_TOKEN_LIFETIME` | Refresh token lifetime in seconds | 2592000 | No |
| `SESSION_TIMEOUT` | Session timeout in seconds | 3600 | No |
| `ALLOWED_GITHUB_USERS` | Comma-separated list of allowed users | "" | No |

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/yourusername/mcp-oauth-dynamicclient/issues).