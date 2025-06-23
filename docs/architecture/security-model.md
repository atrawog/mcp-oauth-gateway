# Security Model

Comprehensive security architecture implementing defense-in-depth principles with dual authentication realms and zero-trust verification.

```{danger}
**Security Disclaimer**

This is a reference implementation and test platform. Despite our efforts to follow security best practices:

- **Known Limitations**: As an experimental platform, security vulnerabilities likely exist
- **Not Production Ready**: Requires extensive security auditing before production use
- **Evolving Codebase**: Security model may change as MCP protocol evolves
- **Test Platform**: Primary purpose is protocol testing, not production security

**DO NOT** deploy this in production without:
1. Comprehensive security audit
2. Penetration testing
3. Code review by security professionals
4. Risk assessment for your use case
```

## Authentication Security

### Dual Authentication Realms

The MCP OAuth Gateway implements two distinct authentication realms that never intermingle:

#### 1. MCP Gateway Client Realm (RFC 7591/7592)
**Purpose**: Authenticate MCP clients (Claude.ai, IDEs, etc.) to access the gateway infrastructure.

- **Dynamic Client Registration**: RFC 7591 compliant registration at `/register`
- **Client Management**: RFC 7592 compliant CRUD operations with registration access tokens
- **Public Registration**: No authentication required for initial registration
- **Protected Management**: Bearer token authentication for client lifecycle operations

```
POST /register → Client ID + Registration Access Token
GET /register/{client_id} → Client metadata (Bearer token required)
PUT /register/{client_id} → Update client (Bearer token required)  
DELETE /register/{client_id} → Remove client (Bearer token required)
```

#### 2. User Authentication Realm (OAuth 2.0)
**Purpose**: Authenticate human users to access their protected MCP resources.

- **GitHub OAuth Integration**: Users authenticate via GitHub's OAuth 2.0 service
- **JWT Token Issuance**: Secure tokens with user identity claims
- **Per-Subdomain Access**: User-level access control per MCP service
- **Refresh Token Support**: Long-lived authentication sessions

### Authentication Flow Security

```{mermaid}
sequenceDiagram
    participant Client as MCP Client
    participant Traefik as Traefik Router
    participant Auth as Auth Service
    participant GitHub as GitHub OAuth
    participant MCP as MCP Service
    
    Note over Client,MCP: Phase 1: Client Registration
    Client->>Traefik: POST /register (no auth)
    Traefik->>Auth: Route to auth service
    Auth->>Client: Client credentials + registration token
    
    Note over Client,MCP: Phase 2: User Authentication
    Client->>Traefik: GET /authorize?client_id=...
    Traefik->>Auth: Route to auth service
    Auth->>GitHub: Redirect to GitHub OAuth
    GitHub->>Auth: Authorization code
    Auth->>Client: Access token (JWT)
    
    Note over Client,MCP: Phase 3: Resource Access
    Client->>Traefik: POST /mcp (Bearer token)
    Traefik->>Auth: ForwardAuth validation
    Auth->>Traefik: Valid + user headers
    Traefik->>MCP: Forward with auth context
    MCP->>Client: Protected resource
```

## Authorization Framework

### Role-Based Access Control (RBAC)

#### GitHub User Authorization
- **Allowed Users List**: `ALLOWED_GITHUB_USERS` environment variable
- **Organization Membership**: Optional GitHub org/team validation
- **Scope Verification**: GitHub token scope validation
- **User Context Propagation**: User identity forwarded to MCP services

#### Client Authorization Levels
- **Public Clients**: PKCE-enabled, no client secret required
- **Confidential Clients**: Client secret required for token exchange
- **Registration Management**: Separate authorization for client CRUD operations

### Permission Model
```
User Permissions:
├── mcp.fetch.read     # Access to fetch service
├── mcp.memory.write   # Write to memory service  
├── mcp.time.read      # Access to time service
└── client.register    # Register new MCP clients

Client Permissions:
├── registration.read   # View client metadata
├── registration.write  # Update client settings
└── registration.delete # Remove client registration
```

## Token Security

### JWT Token Architecture
**Access Tokens**: Short-lived (30 minutes), contain user and client claims
**Refresh Tokens**: Long-lived (1 year), stored securely in Redis

#### JWT Claims Structure
```json
{
  "iss": "mcp-oauth-gateway",
  "sub": "github_user_id",
  "aud": "mcp-services",
  "exp": 1735689600,
  "iat": 1735688000,
  "jti": "unique_token_id",
  "client_id": "registered_client_id",
  "scope": "mcp.fetch mcp.memory mcp.time",
  "github_user": "username",
  "github_id": 12345678
}
```

### Token Lifecycle Management
- **Generation**: Cryptographically secure random generation
- **Storage**: Redis with TTL matching token expiration
- **Validation**: Signature verification + claims validation + Redis lookup
- **Revocation**: Immediate invalidation via Redis deletion
- **Rotation**: Automatic refresh token rotation on use

### PKCE Implementation (RFC 7636)
- **Code Challenge Method**: S256 (SHA256) mandatory
- **Code Verifier**: 43-128 character cryptographically random string
- **Challenge Derivation**: `base64url(sha256(code_verifier))`
- **Replay Protection**: Single-use authorization codes

## Network Security

### Transport Layer Security
- **HTTPS Everywhere**: All communication encrypted with TLS 1.3
- **Let's Encrypt Integration**: Automatic certificate provisioning and renewal
- **HSTS Headers**: HTTP Strict Transport Security enforced
- **Certificate Pinning**: Optional client certificate validation

### Request Validation
- **Origin Validation**: Prevent DNS rebinding attacks
- **Host Header Verification**: Ensure requests target correct domains
- **Content-Type Validation**: Enforce application/json for API endpoints
- **Request Size Limits**: Prevent resource exhaustion attacks

### Network Isolation
- **Docker Networks**: Service isolation via container networking
- **Firewall Rules**: Minimal port exposure (80, 443 only)
- **Internal Communication**: Services communicate via internal networks
- **Redis Security**: Password-protected, network isolated

## Threat Mitigation

### OWASP Top 10 Protection

#### A01: Broken Access Control
- **ForwardAuth Validation**: Every request validated
- **Principle of Least Privilege**: Minimal required permissions
- **Resource-Level Authorization**: Per-service access control

#### A02: Cryptographic Failures
- **Strong Encryption**: AES-256, RSA-4096, ECDSA P-384
- **Secure Key Management**: Environment variable secrets
- **Proper Random Generation**: Cryptographically secure PRNGs

#### A03: Injection Attacks
- **Input Validation**: All inputs validated and sanitized
- **Parameterized Queries**: No dynamic SQL construction
- **Output Encoding**: Proper encoding for all outputs

#### A07: Authentication Failures
- **Multi-Factor Ready**: OAuth provider handles MFA
- **Session Management**: Secure session handling via Redis
- **Brute Force Protection**: Rate limiting on auth endpoints

### Attack Vector Mitigation

#### Confused Deputy Attacks
- **Audience Validation**: Tokens validated for specific services
- **Service Boundaries**: Clear separation between auth realms
- **Request Context**: Full request context validation

#### Token Theft and Replay
- **Short-Lived Tokens**: 30-minute access token lifetime
- **Secure Storage**: HttpOnly cookies where applicable
- **Refresh Rotation**: Refresh tokens rotated on use
- **Revocation Support**: Immediate token invalidation

#### DNS Rebinding Attacks
- **Origin Validation**: Strict Origin header checking
- **Host Verification**: Valid host header enforcement
- **Network Binding**: Localhost binding for sensitive services

### Security Monitoring

#### Audit Logging
- **Authentication Events**: All auth attempts logged
- **Authorization Failures**: Failed access attempts tracked
- **Token Operations**: Token lifecycle events audited
- **Admin Actions**: Client management operations logged

#### Anomaly Detection
- **Rate Limiting**: Excessive request detection
- **Geographic Analysis**: Unusual location access patterns
- **Behavioral Monitoring**: Deviation from normal usage patterns
- **Automated Alerting**: Critical security event notifications

### Incident Response

#### Compromise Detection
- **Token Validation Failures**: Monitor for invalid token patterns
- **Unusual Access Patterns**: Detect anomalous behavior
- **Error Rate Monitoring**: Spike detection in auth failures

#### Response Procedures
1. **Immediate Revocation**: Compromised token invalidation
2. **Service Isolation**: Isolate affected services
3. **User Notification**: Alert affected users
4. **Forensic Analysis**: Investigation and root cause analysis
5. **Recovery**: Secure restoration of services