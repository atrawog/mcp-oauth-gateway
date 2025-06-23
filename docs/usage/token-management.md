# Token Management

This guide covers token generation, management, and security practices for the MCP OAuth Gateway.

## Token Types

### 1. JWT Secret

The master secret for signing JWTs:

```bash
# Generate a new JWT secret
just generate-jwt-secret

# This creates a secure 64-character secret
# Stored as GATEWAY_JWT_SECRET in .env
```

### 2. GitHub OAuth Tokens

For the gateway's own GitHub authentication:

```bash
# Generate GitHub tokens
just generate-github-token

# This initiates OAuth flow and stores:
# - GATEWAY_OAUTH_ACCESS_TOKEN
# - GATEWAY_OAUTH_REFRESH_TOKEN
# - GATEWAY_OAUTH_CLIENT_ID
# - GATEWAY_OAUTH_CLIENT_SECRET
```

### 3. MCP Client Tokens

For external MCP clients (like Claude.ai):

```bash
# Generate client access token
just mcp-client-token

# Stores as MCP_CLIENT_ACCESS_TOKEN
# Used by mcp-streamablehttp-client
```

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

### Token Rotation

```bash
# Rotate JWT secret (invalidates all tokens)
just rotate-jwt-secret

# Refresh GitHub token
just refresh-github-token

# Generate new client token
just mcp-client-token --force
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

### 1. Regular Rotation

```bash
# Recommended rotation schedule
# JWT Secret: Every 90 days
# Access Tokens: Every 30 days
# Refresh Tokens: Every 180 days

# Set up rotation reminder
just schedule-rotation
```

### 2. Token Revocation

```bash
# Revoke specific token
just revoke-token <jti>

# Revoke all user tokens
just revoke-user-tokens <username>

# Revoke client registration
just revoke-client <client_id>
```

### 3. Monitoring

Track token usage:

```bash
# View active tokens
just list-tokens

# Check token metrics
just token-metrics

# Audit token usage
just audit-tokens --user <username>
```

## Token Validation

### Manual Validation

```bash
# Validate a token
just validate-token <token>

# Decode token claims
just decode-token <token>
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
# Refresh the token
just refresh-token

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
export TOKEN_DEBUG=true

# Check token in Redis
just redis-cli
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