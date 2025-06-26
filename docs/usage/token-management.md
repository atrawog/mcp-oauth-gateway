# Token Management

This guide covers token generation, management, and security practices for the MCP OAuth Gateway.

## 🔴 Critical Distinction: Required vs Testing Tokens

### Tokens REQUIRED to Run the Gateway

Only **5 tokens** are required to run the gateway:

1. **`GITHUB_CLIENT_ID`** - From your GitHub OAuth App
2. **`GITHUB_CLIENT_SECRET`** - From your GitHub OAuth App
3. **`GATEWAY_JWT_SECRET`** - Run: `just generate-jwt-secret`
4. **`JWT_PRIVATE_KEY_B64`** - Run: `just generate-rsa-keys`
5. **`REDIS_PASSWORD`** - Set manually

**That's it!** The gateway can run with just these 5 tokens.

### Tokens ONLY for Testing

All other tokens are **optional** and only used for testing:

- **`GITHUB_PAT`** - GitHub Personal Access Token (for test API calls)
- **`GATEWAY_OAUTH_*`** tokens - Generated during test OAuth flows
- **`MCP_CLIENT_*`** tokens - For testing MCP client libraries

```{important}
The gateway itself does NOT consume OAuth tokens. It's an OAuth provider that issues tokens to clients. The only credentials it needs are for the GitHub OAuth App to authenticate users.
```

## Token Types

### 1. JWT Secret

The master secret for signing JWTs:

```bash
# Generate a new JWT secret
just generate-jwt-secret

# This creates a secure 64-character secret
# Stored as GATEWAY_JWT_SECRET in .env
```

### 2. GitHub OAuth Tokens (OPTIONAL - Testing Only)

These tokens are **NOT required** to run the gateway. They're only used for automated testing:

```bash
# Generate GitHub PAT for testing (uses device flow)
just generate-github-token

# This initiates GitHub Device Flow:
# 1. Requests device code from GitHub
# 2. Shows: "Visit https://github.com/login/device"
# 3. Displays code: "XXXX-XXXX" for you to enter
# 4. Polls GitHub until you authorize
# 5. Stores the resulting GitHub PAT as GITHUB_PAT

# Also generates test tokens:
# - GATEWAY_OAUTH_ACCESS_TOKEN (for test authentication)
# - GATEWAY_OAUTH_REFRESH_TOKEN (for test refresh)
# - GATEWAY_OAUTH_CLIENT_ID (test client)
# - GATEWAY_OAUTH_CLIENT_SECRET (test client)
```

**⚠️ Important**: These tokens are only used by the test suite to verify OAuth flows work correctly. The gateway itself doesn't use them.

### 3. MCP Client Tokens (OPTIONAL - Testing Only)

For testing MCP client libraries like `mcp-streamablehttp-client`:

```bash
# Generate test client token (uses device flow)
just mcp-client-token

# This uses Device Flow:
# 1. Attempts to register/authenticate the client
# 2. If browser unavailable, initiates device flow
# 3. Shows verification URL and code
# 4. You manually authorize on GitHub
# 5. Stores as MCP_CLIENT_ACCESS_TOKEN

# These tokens are used for:
# - Testing mcp-streamablehttp-client
# - Integration testing with MCP services
# - Development and debugging
```

**⚠️ Important**: These tokens are for testing MCP client libraries, not for running the gateway.

## Token Lifecycle

### Access Tokens

- **Default Lifetime**: 30 days
- **Format**: JWT with claims
- **Storage**: Redis with TTL
- **Refresh**: Via refresh token

### Refresh Tokens

- **Lifetime**: 1 year
- **Format**: Opaque string
- **Storage**: Redis
- **Usage**: One-time use

### Client Registration

- **Default Lifetime**: 90 days
- **Eternal Mode**: Set `CLIENT_LIFETIME=0`
- **Management**: RFC 7592 endpoints

## Token Generation Commands

### Initial Setup

```bash
# 1. Generate JWT secret (once)
just generate-jwt-secret

# 2. Set up GitHub OAuth
just generate-github-token

# 3. Create MCP client token
just mcp-client-token
```

### Token Refresh

```bash
# Refresh OAuth tokens
just refresh-tokens

# Generate new client token
just mcp-client-token
```

## Token Storage

### Environment Variables

Tokens are stored in `.env`:

```bash
# JWT Configuration
GATEWAY_JWT_SECRET=<64-char-secret>

# Gateway's Own Tokens
GATEWAY_OAUTH_ACCESS_TOKEN=<jwt-token>
GATEWAY_OAUTH_REFRESH_TOKEN=<refresh-token>

# Client Tokens
MCP_CLIENT_ACCESS_TOKEN=<bearer-token>
```

### Redis Storage

Token metadata in Redis:

```
oauth:token:{jti}         # Token validation data
oauth:refresh:{token}     # Refresh token mapping
oauth:user_tokens:{user}  # User's active tokens
```

## Security Best Practices

### 1. Regular Maintenance

```bash
# Check token expiration
just check-token-expiry

# Purge expired tokens
just oauth-purge-expired

# Backup OAuth data
just oauth-backup
```

### 2. Token Management

```bash
# Delete specific token by JTI
just oauth-delete-token <jti>

# Delete client registration
just oauth-delete-registration <client_id>

# Delete client and all associated data
just oauth-delete-client-complete <client_id>
```

### 3. Monitoring

Track token usage:

```bash
# View active tokens
just oauth-list-tokens

# View registrations
just oauth-list-registrations

# Show OAuth statistics
just oauth-stats
```

## Token Validation

### Token Validation Commands

```bash
# Validate all current tokens
just validate-tokens

# Check logs for validation errors
just logs auth | grep "token validation"
```

### Programmatic Validation

```python
# Example token validation
import jwt
from datetime import datetime

def validate_token(token, secret):
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["RS256"]
        )

        # Check expiration
        if payload['exp'] < datetime.utcnow().timestamp():
            return False, "Token expired"

        # Check required claims
        required = ['sub', 'iat', 'exp', 'jti']
        for claim in required:
            if claim not in payload:
                return False, f"Missing claim: {claim}"

        return True, payload

    except jwt.InvalidTokenError as e:
        return False, str(e)
```

## Troubleshooting

### Common Issues

#### Token Expired

**Error**: "Token has expired"

**Solution**:
```bash
# Refresh OAuth tokens
just refresh-tokens

# Or generate new token
just mcp-client-token
```

#### Invalid Signature

**Error**: "Invalid token signature"

**Solution**:
- Verify JWT secret matches
- Check token hasn't been tampered
- Ensure correct algorithm (RS256)

#### Token Not Found

**Error**: "Token not found in Redis"

**Solution**:
- Check Redis connectivity
- Verify token was properly stored
- Token may have been revoked

### Debug Token Issues

```bash
# Enable debug logging
export DEBUG=true

# Check token in Redis
just exec redis redis-cli
> GET oauth:token:<jti>

# View auth service logs
just logs auth -f
```

## Advanced Topics

### Custom Token Claims

Add custom claims in configuration:

```bash
# In auth/.env
TOKEN_CUSTOM_CLAIMS='{"org": "mycompany", "role": "developer"}'
```

### Token Binding

Bind tokens to specific conditions:

```bash
# IP binding
TOKEN_BIND_IP=true

# User agent binding
TOKEN_BIND_UA=true

# Client certificate binding
TOKEN_BIND_CERT=true
```

### Multi-Factor Tokens

Require additional validation:

```bash
# Enable MFA for tokens
TOKEN_MFA_REQUIRED=true
TOKEN_MFA_PROVIDER=totp
```

## Best Practices Summary

1. **Generate Strong Secrets** - Use provided commands
2. **Rotate Regularly** - Set up rotation schedule
3. **Monitor Usage** - Track token metrics
4. **Revoke Compromised** - Act quickly on breaches
5. **Audit Regularly** - Review token usage
6. **Backup Secrets** - Secure offline backup
7. **Use Short Lifetimes** - Minimize exposure window
8. **Implement Alerts** - Notify on suspicious activity

## Related Documentation

- [Security Architecture](../architecture/security.md)
- [Client Registration](../api/client-registration.md)
- [Monitoring](monitoring.md)
