# mcp-oauth-dynamicclient

The divine OAuth 2.1 server implementation with full RFC 7591/7592 compliance for dynamic client registration and management.

## Quick Start

**Key Features:**
- OAuth 2.1 compliant authorization server
- Dynamic client registration (RFC 7591) with public endpoint
- Client configuration management (RFC 7592) with protected endpoints
- GitHub OAuth integration for user authentication
- JWT tokens with RS256 (recommended) or HS256 signing
- Redis-backed storage for instant token revocation

**Installation:**
```bash
pip install mcp-oauth-dynamicclient
# or
pixi add --pypi mcp-oauth-dynamicclient
```

**Basic Usage:**
```bash
# Start the OAuth server
python -m mcp_oauth_dynamicclient

# Register a client
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"client_name":"My App","redirect_uris":["http://localhost:8080/callback"]}'
```

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Endpoints](#api-endpoints)
4. [Configuration](#configuration)
5. [Client Registration Flow](#client-registration-flow)
6. [OAuth Flow with PKCE](#oauth-flow-with-pkce)
7. [JWT Token Structure](#jwt-token-structure)
8. [Redis Storage Schema](#redis-storage-schema)
9. [Security Considerations](#security-considerations)
10. [Integration Examples](#integration-examples)
11. [Error Handling](#error-handling)
12. [Performance Considerations](#performance-considerations)
13. [Monitoring and Logging](#monitoring-and-logging)
14. [Troubleshooting](#troubleshooting)
15. [Best Practices](#best-practices)

## Overview

`mcp-oauth-dynamicclient` is the cornerstone of the MCP OAuth Gateway, providing a production-ready OAuth 2.1 authorization server with full support for RFC 7591 (Dynamic Client Registration) and RFC 7592 (Client Management Protocol). This package handles all OAuth authentication flows, client registration, and token management for the gateway.

### Core Capabilities

- **OAuth 2.1 Compliance**: Latest specification with security-first defaults
- **Dynamic Registration**: No pre-registration required for clients
- **Client Management**: Full lifecycle management via RFC 7592
- **GitHub Integration**: User authentication with configurable access control
- **Token Management**: JWT with Redis backing for instant revocation
- **PKCE Mandatory**: S256 code challenge method enforced

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

### Main Classes

```python
# Settings configuration
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

# Main components
OAuthServer          # Core OAuth server implementation
DynamicClientEndpoint # RFC 7591 registration endpoint
DynamicClientConfigurationEndpoint # RFC 7592 management
JWTService          # Token generation and validation
RedisStorage        # Persistent storage backend
```

## API Endpoints

### OAuth 2.0 Core Endpoints

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/authorize` | GET | Authorization endpoint | None |
| `/token` | POST | Token exchange endpoint | Client credentials |
| `/callback` | GET | OAuth callback handler | None |
| `/revoke` | POST | Token revocation | Bearer token |
| `/introspect` | POST | Token introspection | Bearer token |

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

### Discovery & Utility

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/.well-known/oauth-authorization-server` | GET | Server metadata | None |
| `/verify` | GET/POST | ForwardAuth endpoint | Bearer token |
| `/health` | GET | Health check | None |

## Configuration

### Environment Variables

```bash
# Required - GitHub OAuth
GITHUB_CLIENT_ID=xxx
GITHUB_CLIENT_SECRET=xxx

# Required - JWT Configuration
GATEWAY_JWT_SECRET=xxx          # For HS256 or fallback
GATEWAY_RSA_PRIVATE_KEY=xxx     # For RS256 (recommended)
GATEWAY_RSA_PUBLIC_KEY=xxx      # For RS256
# OR use base64 encoded:
JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY_B64=xxx         # Base64 encoded private key

# Required - Domain
BASE_DOMAIN=yourdomain.com

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=xxx
REDIS_URL=redis://redis:6379/0  # Alternative to host/port

# Token Lifetimes
ACCESS_TOKEN_LIFETIME=2592000   # 30 days (default: 30 min)
REFRESH_TOKEN_LIFETIME=31536000 # 1 year
SESSION_TIMEOUT=300             # 5 minutes
CLIENT_LIFETIME=7776000         # 90 days (0 for eternal)

# Access Control
ALLOWED_GITHUB_USERS=user1,user2,user3  # or '*' for any

# Protocol Version
MCP_PROTOCOL_VERSION=2025-06-18
```

### JWT Key Generation

#### RS256 (Recommended)
```bash
# Generate private key
openssl genrsa -out private_key.pem 2048

# Extract public key
openssl rsa -in private_key.pem -pubout -out public_key.pem

# Base64 encode for .env
cat private_key.pem | base64 -w 0 > private_key_b64.txt
```

#### HS256 (Simpler)
```bash
# Generate strong secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Client Registration Flow

### 1. Dynamic Registration (RFC 7591)

**Request:**
```bash
POST /register
Content-Type: application/json

{
  "client_name": "My MCP Client",
  "redirect_uris": ["http://localhost:8080/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "scope": "mcp:*",
  "token_endpoint_auth_method": "none",
  "client_uri": "https://app.example.com",
  "logo_uri": "https://app.example.com/logo.png"
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
  "registration_client_uri": "https://auth.example.com/register/dyn_abc123...",
  "client_name": "My MCP Client",
  "redirect_uris": ["http://localhost:8080/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "scope": "mcp:*",
  "token_endpoint_auth_method": "none"
}
```

### 2. Client Management (RFC 7592)

#### Read Client Configuration
```bash
GET /register/dyn_abc123
Authorization: Bearer reg_token123

# Response: Current client configuration
```

#### Update Client Configuration
```bash
PUT /register/dyn_abc123
Authorization: Bearer reg_token123
Content-Type: application/json

{
  "client_name": "Updated Client Name",
  "redirect_uris": ["http://localhost:9090/callback"],
  "logo_uri": "https://app.example.com/new-logo.png"
}

# Response: Updated configuration
```

#### Delete Client
```bash
DELETE /register/dyn_abc123
Authorization: Bearer reg_token123

# Response: 204 No Content
```

## OAuth Flow with PKCE

### 1. Generate PKCE Challenge

```python
import secrets
import hashlib
import base64

# Generate code verifier (43-128 characters)
code_verifier = base64.urlsafe_b64encode(
    secrets.token_bytes(32)
).decode('utf-8').rstrip('=')

# Generate code challenge (S256 only)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode('utf-8').rstrip('=')
```

### 2. Authorization Request

```
GET /authorize?
  client_id=dyn_abc123&
  redirect_uri=http://localhost:8080/callback&
  response_type=code&
  scope=mcp:*&
  state=random_state_value&
  code_challenge=challenge_value&
  code_challenge_method=S256
```

### 3. Token Exchange

```bash
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
client_id=dyn_abc123&
client_secret=secret_xyz789&  # If confidential client
code=auth_code_value&
redirect_uri=http://localhost:8080/callback&
code_verifier=verifier_value
```

### 4. Token Response

```json
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "refresh_token": "refresh_xyz...",
  "scope": "mcp:*"
}
```

### 5. Refresh Token

```bash
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&
refresh_token=refresh_xyz...&
client_id=dyn_abc123&
client_secret=secret_xyz789
```

## JWT Token Structure

### Header
```json
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "key-id"  // If using key rotation
}
```

### Payload
```json
{
  "iss": "https://auth.example.com",
  "sub": "github|username",
  "aud": "dyn_abc123",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "unique_token_id",
  "scope": "mcp:*",
  "github_username": "username",
  "client_id": "dyn_abc123"
}
```

## Redis Storage Schema

### Key Patterns

```
oauth:state:{state}          # CSRF state (5 min TTL)
oauth:code:{code}            # Authorization codes (1 year TTL)
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
  "client_secret_expires_at": 0,  // 0 = never expires
  "registration_access_token": "reg_token123",
  "redirect_uris": ["https://app.example.com/callback"],
  "client_name": "My Application",
  "scope": "openid profile email",
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "client_secret_basic"
}
```

### Token Storage

```json
{
  "jti": "unique_token_id",
  "user_id": "github|username",
  "client_id": "dyn_abc123",
  "scope": "mcp:*",
  "exp": 1234567890,
  "revoked": false
}
```

## Security Considerations

### PKCE Enforcement
- **Mandatory S256**: Only S256 code challenge method allowed
- **Verifier validation**: Must be 43-128 characters
- **Prevents interception**: Authorization code useless without verifier
- **No downgrade**: Plain method rejected

### Token Security
- **JWT signing**: RS256 (asymmetric) or HS256 (symmetric)
- **Short-lived access**: 30 minutes default
- **Long-lived refresh**: 1 year default with rotation
- **Instant revocation**: Via Redis token storage
- **JTI tracking**: Prevents token replay

### Client Authentication
- **Strong credentials**: Cryptographically random generation
- **Registration tokens**: Separate from OAuth tokens
- **Secret protection**: Never logged or displayed after creation
- **Expiration support**: Configurable client lifetimes

### User Access Control
- **GitHub allowlist**: Via ALLOWED_GITHUB_USERS
- **Wildcard support**: Set to '*' for any GitHub user
- **JWT claims**: Include GitHub user information
- **Organization support**: Future enhancement

### Request Validation
- **Origin checking**: Validates request origins
- **State parameter**: CSRF protection
- **Redirect URI**: Exact match required
- **Scope validation**: Requested vs granted

## Integration Examples

### As Standalone Service

```yaml
# auth/docker-compose.yml
services:
  auth:
    build: ./mcp-oauth-dynamicclient
    environment:
      - GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
      - GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET}
      - GATEWAY_JWT_SECRET=${GATEWAY_JWT_SECRET}
      - JWT_ALGORITHM=RS256
      - JWT_PRIVATE_KEY_B64=${JWT_PRIVATE_KEY_B64}
      - BASE_DOMAIN=${BASE_DOMAIN}
      - REDIS_URL=redis://redis:6379/0
      - ALLOWED_GITHUB_USERS=user1,user2,user3
    depends_on:
      - redis
    networks:
      - internal
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.auth.rule=Host(`auth.${BASE_DOMAIN}`)"
      - "traefik.http.routers.auth.priority=4"
```

### ForwardAuth Integration

```yaml
# Traefik middleware configuration
labels:
  - "traefik.http.middlewares.mcp-auth.forwardauth.address=http://auth:8000/verify"
  - "traefik.http.middlewares.mcp-auth.forwardauth.authResponseHeaders=X-User-Id,X-User-Name,X-Auth-Token"
  - "traefik.http.middlewares.mcp-auth.forwardauth.trustForwardHeader=true"
```

### MCP Service Protection

```yaml
# mcp-service/docker-compose.yml
services:
  mcp-service:
    # ... service config ...
    labels:
      - "traefik.http.routers.mcp-service.middlewares=mcp-auth"
```

## Error Handling

### OAuth Error Responses

The service returns RFC 6749 compliant error responses:

| Error | Description | HTTP Status |
|-------|-------------|-------------|
| `invalid_request` | Malformed request | 400 |
| `invalid_client` | Client authentication failed | 401 |
| `invalid_grant` | Invalid authorization code/refresh token | 400 |
| `unauthorized_client` | Client not authorized for grant type | 400 |
| `unsupported_grant_type` | Grant type not supported | 400 |
| `invalid_scope` | Requested scope invalid | 400 |

### Registration Errors

| Error | Description | HTTP Status |
|-------|-------------|-------------|
| `invalid_redirect_uri` | Invalid URI format | 400 |
| `invalid_client_metadata` | Invalid metadata fields | 400 |

### HTTP Status Codes

- **200 OK**: Successful token request
- **201 Created**: Client registration successful
- **204 No Content**: Successful deletion
- **302 Found**: Authorization redirects
- **400 Bad Request**: Invalid request
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Access denied
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

## Performance Considerations

### Redis Connection Pooling
- Async Redis client with automatic pooling
- Configurable pool size via connection URL
- Connection reuse for efficiency
- Automatic reconnection on failure

### Token Validation Caching
- JWT validation results cached in memory
- Reduces cryptographic operations
- TTL matches token lifetime
- Automatic cache invalidation

### Async Implementation
- Full async/await throughout
- Non-blocking I/O operations
- High concurrency support
- Efficient resource utilization

### Optimization Tips
1. Use Redis connection pooling
2. Enable JWT validation caching
3. Set appropriate token lifetimes
4. Monitor Redis memory usage
5. Use RS256 for better performance at scale

## Monitoring and Logging

### Health Check Endpoint

```bash
GET /health

# Response
{
  "status": "healthy",
  "redis": "connected",
  "version": "1.0.0"
}
```

### Key Metrics to Monitor

- **Token issuance rate**: Track OAuth flow completion
- **Failed authentications**: Detect potential attacks
- **Client registrations**: Monitor adoption
- **Active sessions**: Current user load
- **Redis memory**: Storage utilization
- **Response times**: Performance tracking

### Logging Configuration

```python
# Structured logging
import structlog

logger = structlog.get_logger()

# Log important events
logger.info("client_registered",
    client_id=client_id,
    client_name=client_name)

logger.warning("auth_failed",
    reason="invalid_credentials",
    client_id=client_id)
```

### Security Event Logging

- Failed login attempts
- Invalid token usage
- Client registration/deletion
- Scope escalation attempts
- PKCE validation failures

## Troubleshooting

### Common Issues

#### "No module named 'authlib'"
**Solution**: Install the package properly:
```bash
pip install mcp-oauth-dynamicclient[all]
# or
pixi add --pypi mcp-oauth-dynamicclient
```

#### JWT signature verification failed
**Solution**:
- Ensure JWT_PRIVATE_KEY_B64 is properly base64 encoded
- Verify algorithm matches (RS256 vs HS256)
- Check key format (PEM for RS256)

#### Redis connection refused
**Solution**:
- Check REDIS_URL format: `redis://host:port/db`
- Verify Redis is running: `redis-cli ping`
- Check network connectivity
- Verify password if set

#### GitHub OAuth callback fails
**Solution**:
- Verify GitHub OAuth app settings
- Check callback URL matches exactly
- Ensure HTTPS in production
- Verify client ID/secret

#### Client registration returns 400
**Solution**:
- Check redirect_uris format (must be array)
- Verify URI schemes (http/https)
- Ensure unique client_name
- Valid grant_types for token_endpoint_auth_method

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m mcp_oauth_dynamicclient
```

## Best Practices

### Security
1. **Use RS256 for JWT signing** - More secure than HS256
2. **Set appropriate token lifetimes** - Balance security and UX
3. **Implement token rotation** - Use refresh tokens properly
4. **Monitor failed attempts** - Detect potential attacks
5. **Regular security audits** - Review client registrations
6. **Use HTTPS everywhere** - Never expose tokens over HTTP
7. **Validate redirect URIs** - Prevent open redirects

### Operations
1. **Backup Redis data** - Prevent data loss
2. **Set up monitoring** - Track key metrics
3. **Log security events** - Audit trail
4. **Plan for scaling** - Redis clustering if needed
5. **Automate certificate renewal** - For HTTPS
6. **Document client onboarding** - Clear registration process

### Development
1. **Use environment variables** - Never hardcode secrets
2. **Test with PKCE** - Ensure compliance
3. **Validate token expiration** - Handle gracefully
4. **Implement proper error handling** - User-friendly messages
5. **Follow OAuth 2.1 spec** - Stay compliant
6. **Keep dependencies updated** - Security patches

## CLI Tools

The package includes helpful CLI commands:

```bash
# Generate JWT secret
python -m mcp_oauth_dynamicclient generate-secret

# Create RSA key pair
python -m mcp_oauth_dynamicclient create-keys

# Validate configuration
python -m mcp_oauth_dynamicclient validate-config

# Clean expired tokens
python -m mcp_oauth_dynamicclient cleanup-tokens
```

## Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=mcp_oauth_dynamicclient tests/

# Integration tests
just test tests/test_oauth_flow.py -v

# Test specific endpoint
pytest tests/test_registration.py::test_dynamic_registration
```
