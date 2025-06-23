# Security Architecture

The MCP OAuth Gateway implements multiple layers of security to protect both the authentication flow and MCP service access.

## Security Layers

### 1. Transport Security

- **HTTPS Everywhere** - All traffic encrypted via TLS 1.3
- **Let's Encrypt Integration** - Automatic certificate renewal
- **HSTS Headers** - Enforce HTTPS connections
- **Certificate Pinning** - Optional for high-security deployments

### 2. Authentication Security

#### OAuth 2.1 Compliance

- **PKCE Required** - S256 challenge method mandatory
- **State Parameter** - CSRF protection on all flows
- **Short-lived Codes** - 1-minute authorization code lifetime
- **No Implicit Flow** - Removed as per OAuth 2.1

#### Token Security

- **JWT with RS256** - Asymmetric signing
- **Short Expiry** - 30-day access tokens
- **Secure Storage** - Redis with encryption at rest
- **Token Binding** - Optional RFC 8705 support

### 3. Authorization Security

#### Dual Realm Architecture

1. **Client Authentication Realm**
   - Dynamic client registration (RFC 7591)
   - Client credentials for MCP access
   - Per-client rate limiting

2. **User Authentication Realm**
   - GitHub OAuth integration
   - User-level access control
   - Allowed users whitelist

#### Access Control

- **Per-Service Authorization** - Granular service access
- **Scope Validation** - Required scopes enforced
- **Resource Isolation** - Service boundaries maintained

### 4. Infrastructure Security

#### Container Security

- **Non-root Containers** - Minimal privileges
- **Read-only Filesystems** - Where applicable
- **Network Segmentation** - Internal service network
- **Secret Management** - Environment variable injection

#### Data Security

- **Redis Encryption** - Data encrypted at rest
- **No Persistent Secrets** - Tokens expire
- **Audit Logging** - All auth events logged
- **GDPR Compliance** - Minimal data retention

## Security Best Practices

### Development

1. **No Hardcoded Secrets** - Use .env files
2. **Input Validation** - All inputs sanitized
3. **Dependency Scanning** - Regular updates
4. **Security Testing** - Part of CI/CD

### Operations

1. **Regular Rotation** - JWT secrets and tokens
2. **Monitoring** - Failed auth attempts
3. **Incident Response** - Clear procedures
4. **Backup Encryption** - Secure backups

## Common Attack Vectors

### Prevented Attacks

- **CSRF** - State parameter validation
- **Token Replay** - JTI tracking
- **Authorization Code Injection** - PKCE validation
- **DNS Rebinding** - Origin header checks

### Mitigation Strategies

1. **Rate Limiting** - Per endpoint and client
2. **Anomaly Detection** - Unusual patterns flagged
3. **Fail Securely** - Deny by default
4. **Defense in Depth** - Multiple security layers

## Security Headers

Required headers on all responses:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

## Compliance

The gateway meets requirements for:

- OAuth 2.1 (draft-ietf-oauth-v2-1)
- RFC 7591 (Dynamic Client Registration)
- RFC 7636 (PKCE)
- RFC 8414 (Authorization Server Metadata)
- OWASP Security Guidelines