# Auth Service

The Auth Service is the OAuth 2.1 authorization server that handles all authentication and authorization for the MCP OAuth Gateway. It integrates with GitHub OAuth for user authentication and implements dynamic client registration per RFC 7591/7592.

## Overview

The Auth service provides:
- OAuth 2.1 authorization server implementation
- GitHub OAuth integration for user authentication
- Dynamic client registration (RFC 7591/7592)
- JWT token generation and validation
- ForwardAuth endpoint for Traefik integration

## Architecture

The service uses:
- **Framework**: FastAPI with mcp-oauth-dynamicclient package
- **Storage**: Redis for state and token management
- **Port**: Exposes port 8000 internally
- **Authentication**: GitHub OAuth as identity provider

## Configuration

### Environment Variables

```bash
# GitHub OAuth App (REQUIRED)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# JWT Configuration (REQUIRED)
GATEWAY_JWT_SECRET=your-generated-jwt-secret-at-least-32-chars
JWT_ALGORITHM=RS256  # or HS256
JWT_PRIVATE_KEY_B64=your-base64-encoded-private-key  # For RS256 only

# Access Control (REQUIRED)
ALLOWED_GITHUB_USERS=user1,user2  # Comma-separated list

# Token Lifetimes (REQUIRED)
ACCESS_TOKEN_LIFETIME=86400      # 24 hours
REFRESH_TOKEN_LIFETIME=2592000   # 30 days
SESSION_TIMEOUT=3600             # 1 hour
CLIENT_LIFETIME=7776000          # 90 days (0 for eternal)

# Redis Connection (REQUIRED)
REDIS_PASSWORD=your-secure-redis-password
REDIS_URL=redis://redis:6379

# Protocol Configuration
MCP_PROTOCOL_VERSION=2025-06-18
MCP_PROTOCOL_VERSIONS_SUPPORTED=2025-06-18,2025-03-26,2024-11-05
```

## OAuth Endpoints

### Public Endpoints

#### POST /register - Dynamic Client Registration
- Implements RFC 7591
- No authentication required
- Returns client credentials and registration token

```bash
curl -X POST https://auth.gateway.yourdomain.com/register \
  -H "Content-Type: application/json" \
  -d '{
    "redirect_uris": ["https://app.example.com/callback"],
    "client_name": "My MCP Client"
  }'
```

#### GET /authorize - OAuth Authorization
- Initiates OAuth flow
- Redirects to GitHub for authentication
- Supports PKCE (required)

```bash
# Browser-based flow
https://auth.gateway.yourdomain.com/authorize?
  client_id=CLIENT_ID&
  redirect_uri=REDIRECT_URI&
  state=STATE&
  code_challenge=CHALLENGE&
  code_challenge_method=S256
```

#### POST /token - Token Exchange
- Exchanges authorization code for tokens
- Validates PKCE verifier
- Returns JWT access token

```bash
curl -X POST https://auth.gateway.yourdomain.com/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&
      code=AUTH_CODE&
      client_id=CLIENT_ID&
      client_secret=CLIENT_SECRET&
      code_verifier=VERIFIER"
```

#### GET /.well-known/oauth-authorization-server - Server Metadata
- Returns OAuth server capabilities
- Required by MCP specification
- No authentication required

### Internal Endpoints

#### GET /verify - ForwardAuth Validation
- Used by Traefik for request validation
- Validates Bearer tokens
- Returns user information in headers

## Security Features

### Authentication Flow
1. Client registration via `/register`
2. User redirected to `/authorize`
3. GitHub OAuth authentication
4. Authorization code returned
5. Code exchanged for JWT token
6. Token used for API access

### Token Security
- JWT tokens signed with HS256 or RS256
- Short-lived access tokens (24 hours default)
- Refresh tokens for renewal (30 days default)
- Tokens bound to GitHub user identity

### Access Control
- GitHub user whitelist (`ALLOWED_GITHUB_USERS`)
- Per-client registration lifetime
- Token validation on every request
- Automatic token cleanup

## Integration with Traefik

The Auth service integrates with Traefik via ForwardAuth:

```yaml
# Traefik middleware configuration
- "traefik.http.middlewares.mcp-auth.forwardauth.address=http://auth:8000/verify"
- "traefik.http.middlewares.mcp-auth.forwardauth.authResponseHeaders=X-User-Id,X-User-Name"
```

Flow:
1. Request arrives at Traefik
2. ForwardAuth middleware calls `/verify`
3. Auth service validates Bearer token
4. User info returned in headers
5. Request forwarded to destination

## Redis Storage Schema

```redis
# OAuth State Management
oauth:state:{state}           # OAuth flow state (5min TTL)
oauth:code:{code}             # Authorization codes (1year TTL)
oauth:pkce:{code_challenge}   # PKCE verifiers

# Client Management  
oauth:client:{client_id}      # Client registration data
oauth:client_index            # Client ID index

# Token Management
oauth:token:{jti}             # Active JWT tokens (30day TTL)
oauth:refresh:{token}         # Refresh tokens (1year TTL)
oauth:user_tokens:{username}  # User's token index
```

## Starting the Service

```bash
# Start auth service only
just up auth

# View logs
just logs auth

# Rebuild after changes
just rebuild auth
```

## Troubleshooting

### Common Issues

#### GitHub OAuth Errors
- Verify `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`
- Check OAuth app callback URL matches
- Ensure user is in `ALLOWED_GITHUB_USERS`

#### JWT Validation Failures
- Verify `GATEWAY_JWT_SECRET` is consistent
- Check token expiration
- Ensure JWT algorithm matches configuration

#### Redis Connection Errors
- Verify Redis is running: `just logs redis`
- Check `REDIS_PASSWORD` and `REDIS_URL`
- Ensure Redis has persistence enabled

### Debugging

```bash
# View auth logs
just logs auth

# Check OAuth registrations
just oauth-list-registrations

# Validate tokens
just validate-tokens

# View OAuth statistics
just oauth-stats
```

## Architecture Notes

- Built with FastAPI and mcp-oauth-dynamicclient
- Stateless design with Redis backend
- No knowledge of MCP protocols
- Pure OAuth implementation
- Runs as single service instance

## Related Documentation

- [OAuth Flow](../architecture/oauth-flow.md) - Detailed flow documentation
- [Components](../architecture/components.md) - System architecture
- [Security](../architecture/security.md) - Security details