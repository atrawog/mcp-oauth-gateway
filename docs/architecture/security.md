# Security Architecture

The MCP OAuth Gateway implements multiple layers of security to protect both the authentication flow and MCP service access.

## Security Layers

### 1. Transport Security

- **HTTPS Everywhere** - All traffic encrypted via TLS
- **Let's Encrypt Integration** - Automatic certificate renewal via Traefik
- **SSL/TLS Termination** - Handled by Traefik reverse proxy

### 2. Authentication Security

#### OAuth 2.1 Compliance

- **PKCE Required** - S256 challenge method mandatory
- **State Parameter** - CSRF protection on all flows
- **Authorization Codes** - Stored in Redis with expiration
- **No Implicit Flow** - Only authorization code flow supported

#### Token Security

- **JWT with HS256** - HMAC signing with shared secret
- **Token Expiry** - 30-day access tokens, 1-year refresh tokens
- **Redis Storage** - Tokens stored with TTL matching expiration
- **JTI Tracking** - Unique token identifiers prevent replay

#### Registration Access Token Security (RFC 7592)

**CRITICAL**: Registration access tokens are completely separate from OAuth access tokens.

- **Token Generation**: `reg-{secrets.token_urlsafe(32)}` - 32 bytes of cryptographic randomness
- **Storage**: Part of client data in Redis at `oauth:client:{client_id}`
- **Authentication**: Direct Bearer token comparison using `secrets.compare_digest`
- **Lifetime**: Matches client lifetime (90 days default, eternal if CLIENT_LIFETIME=0)
- **Scope**: ONLY valid for RFC 7592 management endpoints (`/register/{client_id}`)
- **Security Enforcement**: OAuth JWT tokens explicitly rejected with 403 Forbidden
- **Lost Token Impact**: Client becomes permanently unmanageable - no recovery mechanism
- **Implementation**: `DynamicClientConfigurationEndpoint` class handles authentication

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

- **GitHub User Whitelist** - ALLOWED_GITHUB_USERS configuration
- **Bearer Token Validation** - Traefik ForwardAuth middleware
- **Service Isolation** - Each MCP service runs independently

### 4. Infrastructure Security

#### Container Security

- **Docker Compose** - Service orchestration
- **Network Segmentation** - Internal `public` network for services
- **Secret Management** - Environment variables via .env file

#### Data Security

- **Redis Storage** - Token and session data
- **Token Expiration** - Access tokens expire after 30 days
- **Logging** - Standard service logs via Docker

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

1. **Token Validation** - All requests verified
2. **HTTPS Only** - No plaintext communication
3. **Fail Securely** - Invalid tokens denied
4. **Layered Architecture** - Traefik → Auth → MCP separation

## Security Headers

Security headers are handled by Traefik reverse proxy configuration for HTTPS enforcement and basic security.

## Compliance

The gateway meets requirements for:

- OAuth 2.1 (draft-ietf-oauth-v2-1)
- RFC 7591 (Dynamic Client Registration)
- RFC 7636 (PKCE)
- RFC 8414 (Authorization Server Metadata)
- OWASP Security Guidelines