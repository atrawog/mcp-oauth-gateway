# mcp-oauth-dynamicclient

## Overview

The `mcp-oauth-dynamicclient` package is an OAuth 2.1 authorization server library that provides the core authentication infrastructure for the MCP OAuth Gateway. It implements OAuth standards with support for dynamic client registration.

```{admonition} Key Features
:class: info

- 🔐 **OAuth 2.1 Compliant**: Full authorization code flow with mandatory PKCE
- 📝 **Dynamic Client Registration**: RFC 7591/7592 implementation
- 🌐 **GitHub Integration**: Built-in GitHub OAuth provider
- 🎫 **JWT Tokens**: Secure token generation and validation
- 📦 **Redis Storage**: Persistent storage backend
- 🚀 **FastAPI Based**: Async Python framework
```

## Architecture

### Package Structure

```
mcp_oauth_dynamicclient/
├── __init__.py              # Package exports
├── config.py                # Pydantic settings management
├── models.py                # Data models and schemas
├── keys.py                  # RSA key generation
├── routes.py                # FastAPI route definitions
├── auth_authlib.py          # Authlib OAuth server
├── resource_protector.py    # Token validation
├── async_resource_protector.py  # Async validation
├── redis_client.py          # Redis operations
├── rfc7592.py              # Client management (RFC 7592)
├── server.py               # FastAPI app factory
└── cli.py                  # Command-line interface
```

### Component Relationships

```{mermaid}
graph TB
    subgraph "External Interfaces"
        HTTP[HTTP Requests]
        CLI[CLI Commands]
    end
    
    subgraph "Core Components"
        R[routes.py<br/>FastAPI Routes]
        AA[auth_authlib.py<br/>OAuth Server]
        RP[resource_protector.py<br/>Token Validation]
        RF[rfc7592.py<br/>Client Management]
    end
    
    subgraph "Data Layer"
        M[models.py<br/>Data Models]
        RC[redis_client.py<br/>Storage]
        C[config.py<br/>Settings]
    end
    
    subgraph "Utilities"
        K[keys.py<br/>Crypto]
        CL[cli.py<br/>CLI Tools]
    end
    
    HTTP --> R
    CLI --> CL
    R --> AA
    R --> RP
    R --> RF
    AA --> M
    AA --> RC
    RP --> RC
    RF --> RC
    CL --> AA
    
    classDef interface fill:#9cf,stroke:#333,stroke-width:2px
    classDef core fill:#fc9,stroke:#333,stroke-width:2px
    classDef data fill:#9fc,stroke:#333,stroke-width:2px
    
    class HTTP,CLI interface
    class R,AA,RP,RF core
    class M,RC,C data
```

## Installation

### Using pixi (Recommended)

```bash
pixi add mcp-oauth-dynamicclient
```

### From Source

```bash
cd mcp-oauth-dynamicclient
pixi install -e .
```

## Configuration

### Environment Variables

Create a `.env` file with required settings:

```bash
# GitHub OAuth App (Required)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# JWT Configuration (Required)
GATEWAY_JWT_SECRET=your-secret-key-minimum-32-chars
GATEWAY_JWT_ALGORITHM=HS256
GATEWAY_JWT_EXPIRE_MINUTES=43200  # 30 days

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Access Control
ALLOWED_GITHUB_USERS=user1,user2,user3  # Optional whitelist

# Client Configuration
CLIENT_LIFETIME=7776000  # 90 days (0 = eternal)
MCP_PROTOCOL_VERSION=2025-06-18
```

### Configuration Model

The package uses Pydantic for configuration validation:

```python
from mcp_oauth_dynamicclient import Settings

settings = Settings()  # Loads from environment
print(settings.github_client_id)
print(settings.redis_url)
```

## Usage

### As a Library

#### Creating the OAuth Server

```python
from mcp_oauth_dynamicclient import create_app

# Create FastAPI application
app = create_app()

# Or with custom settings
from mcp_oauth_dynamicclient import Settings
settings = Settings(github_client_id="custom_id")
app = create_app(settings)
```

#### Running the Server

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Using the CLI

The package includes command-line tools:

```bash
# Start OAuth server
pixi run mcp-oauth-server

# Generate GitHub token for testing
pixi run mcp-oauth-token
```

### Integration Examples

#### Protected Route

```python
from fastapi import Depends
from mcp_oauth_dynamicclient import get_current_user

@app.get("/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"message": f"Hello {user.name}"}
```

#### Manual Token Validation

```python
from mcp_oauth_dynamicclient import verify_token

async def validate_request(token: str):
    try:
        token_data = await verify_token(token)
        return {"user_id": token_data.sub, "name": token_data.name}
    except Exception as e:
        return {"error": str(e)}
```

## API Reference

### OAuth Endpoints

#### POST /register - Dynamic Client Registration

Register a new OAuth client (RFC 7591):

```bash
curl -X POST https://auth.example.com/register \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_uris": ["https://app.example.com/callback"],
    "client_name": "My Application",
    "scope": "read write"
  }'
```

Response:
```json
{
  "client_id": "client_abc123",
  "client_secret": "secret_xyz789",
  "registration_access_token": "rat_token123",
  "registration_client_uri": "https://auth.example.com/register/client_abc123",
  "client_secret_expires_at": 0,
  "redirect_uris": ["https://app.example.com/callback"],
  "client_name": "My Application"
}
```

#### GET /authorize - Authorization Endpoint

Initiate OAuth flow:
```
https://auth.example.com/authorize?
  client_id=client_abc123&
  redirect_uri=https://app.example.com/callback&
  response_type=code&
  state=random_state&
  code_challenge=challenge_value&
  code_challenge_method=S256
```

#### POST /token - Token Exchange

Exchange authorization code for tokens:

```bash
curl -X POST https://auth.example.com/token \
  -d "grant_type=authorization_code" \
  -d "code=auth_code_xyz" \
  -d "client_id=client_abc123" \
  -d "client_secret=secret_xyz789" \
  -d "code_verifier=verifier_value"
```

### Client Management (RFC 7592)

#### GET /register/{client_id}

View client registration:
```bash
curl -H "Authorization: Bearer {registration_access_token}" \
  https://auth.example.com/register/client_abc123
```

#### PUT /register/{client_id}

Update client:
```bash
curl -X PUT https://auth.example.com/register/client_abc123 \
  -H "Authorization: Bearer {registration_access_token}" \
  -H "Content-Type: application/json" \
  -d '{"client_name": "Updated Name"}'
```

#### DELETE /register/{client_id}

Delete client:
```bash
curl -X DELETE https://auth.example.com/register/client_abc123 \
  -H "Authorization: Bearer {registration_access_token}"
```

### Metadata Discovery

#### GET /.well-known/oauth-authorization-server

Returns server metadata (RFC 8414):
```json
{
  "issuer": "https://auth.example.com",
  "authorization_endpoint": "https://auth.example.com/authorize",
  "token_endpoint": "https://auth.example.com/token",
  "registration_endpoint": "https://auth.example.com/register",
  "jwks_uri": "https://auth.example.com/jwks",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"]
}
```

## Data Models

### Client Model

```python
class OAuthClient(BaseModel):
    client_id: str
    client_secret: str
    client_name: Optional[str]
    redirect_uris: List[str]
    scope: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    registration_access_token: Optional[str]
```

### Token Model

```python
class TokenData(BaseModel):
    sub: str  # User ID
    name: Optional[str]  # Display name
    exp: int  # Expiration timestamp
    iat: int  # Issued at
    jti: str  # JWT ID
    scope: Optional[str]
```

## Redis Storage Schema

The package uses Redis with the following key patterns:

| Key Pattern | Description | TTL |
|------------|-------------|-----|
| `oauth:state:{state}` | OAuth state for CSRF protection | 5 minutes |
| `oauth:code:{code}` | Authorization codes | 5 minutes |
| `oauth:token:{jti}` | Access tokens | 30 days |
| `oauth:refresh:{token}` | Refresh tokens | 1 year |
| `oauth:client:{client_id}` | Client registrations | No expiry |
| `oauth:registration_token:{token}` | RFC 7592 tokens | No expiry |
| `oauth:user_tokens:{username}` | User token index | No expiry |

## Security Features

### PKCE (Proof Key for Code Exchange)

- **Required**: S256 challenge method mandatory
- **Verifier**: 43-128 characters
- **Storage**: Challenges stored with state
- **Validation**: Strict verification on token exchange

### Token Security

- **Algorithm**: HS256 (HMAC-SHA256)
- **Claims**: Standard JWT claims + custom user data
- **JTI Tracking**: Unique identifier for revocation
- **Expiration**: Configurable (default 30 days)

### Client Security

- **Secrets**: 32 bytes of secure random data
- **Expiration**: Optional client lifetime
- **Redirect Validation**: Strict URI matching
- **Registration Tokens**: Separate auth for management

## Testing

### Running Tests

```bash
# All tests
pixi run pytest tests/ -v

# Specific test file
pixi run pytest tests/test_oauth_flow.py -v

# With coverage
pixi run pytest --cov=mcp_oauth_dynamicclient
```

### Test Categories

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: OAuth flow testing
3. **RFC Compliance**: Standards verification
4. **Security Tests**: Token validation, PKCE

## Troubleshooting

### Common Issues

#### "Redis Connection Failed"
- Check `REDIS_URL` configuration
- Verify Redis is running: `redis-cli ping`
- Check network connectivity

#### "JWT Validation Failed"
- Ensure `GATEWAY_JWT_SECRET` matches across services
- Check token expiration
- Verify algorithm matches (HS256)

#### "GitHub OAuth Error"
- Verify GitHub App credentials
- Check redirect URI configuration
- Ensure user is in `ALLOWED_GITHUB_USERS`

#### "Client Registration Failed"
- Check redirect_uris format (must be array)
- Verify JSON content-type header
- Check for unique client_name

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or via environment:
```bash
LOG_LEVEL=DEBUG pixi run mcp-oauth-server
```

## Best Practices

### Production Deployment

1. **Secure JWT Secret**: Use strong, random secret (32+ chars)
2. **Redis Persistence**: Enable Redis persistence for production
3. **HTTPS Only**: Never run OAuth over HTTP in production
4. **Rate Limiting**: Implement rate limiting on endpoints
5. **Monitoring**: Set up logging and metrics

### Integration Guidelines

1. **Token Handling**: Always validate tokens server-side
2. **Error Responses**: Handle OAuth errors gracefully
3. **Refresh Logic**: Implement automatic token refresh
4. **Logout**: Implement token revocation on logout
5. **CORS**: Configure CORS for browser-based clients

## Advanced Topics

### Custom Token Claims

Add custom claims to JWT tokens:

```python
from mcp_oauth_dynamicclient import create_access_token

custom_data = {
    "sub": "user123",
    "name": "John Doe",
    "role": "admin",  # Custom claim
    "team": "engineering"  # Custom claim
}

token = create_access_token(custom_data)
```

### Extending the OAuth Server

Create a custom app with additional endpoints:

```python
from mcp_oauth_dynamicclient import create_app

app = create_app()

@app.get("/custom/endpoint")
async def custom_endpoint():
    return {"status": "custom"}
```

### Redis Connection Pooling

Configure Redis with connection pooling:

```python
from redis.asyncio import ConnectionPool
from mcp_oauth_dynamicclient import RedisClient

pool = ConnectionPool.from_url(
    "redis://localhost",
    max_connections=50
)
redis_client = RedisClient(pool=pool)
```

## Migration Guide

### From Previous Versions

If migrating from earlier versions:

1. Update environment variables (see Configuration)
2. Run Redis migration scripts if needed
3. Update client code for new endpoints
4. Test OAuth flows thoroughly

## Contributing

See the main project [Development Guidelines](../development/guidelines.md) for contribution standards.

## License

Apache License 2.0 - see project LICENSE file.

## Support

- **Issues**: [GitHub Issues](https://github.com/atrawog/mcp-oauth-gateway/issues)
- **Documentation**: [Full Documentation](https://atrawog.github.io/mcp-oauth-gateway)
- **Source**: [GitHub Repository](https://github.com/atrawog/mcp-oauth-gateway/tree/main/mcp-oauth-dynamicclient)