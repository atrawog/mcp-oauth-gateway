# Security Architecture

Comprehensive security architecture of the MCP OAuth Gateway, implementing defense-in-depth principles and zero-trust security model.

## Security Model Overview

```{mermaid}
graph TB
    subgraph "External Threats"
        ATTACKER[Attackers]
        MITM[MITM Attacks]
        CSRF[CSRF Attacks]
        INJECT[Injection Attacks]
    end

    subgraph "Security Layers"
        subgraph "Layer 1: Network Security"
            HTTPS[HTTPS Only]
            CERT[Let's Encrypt]
            HSTS[HSTS Headers]
        end

        subgraph "Layer 2: Authentication"
            OAUTH[OAuth 2.1]
            PKCE[PKCE Mandatory]
            JWT[JWT RS256]
        end

        subgraph "Layer 3: Authorization"
            FORWARD[ForwardAuth]
            SCOPE[Scope Validation]
            ALLOW[User Allowlist]
        end

        subgraph "Layer 4: Application"
            VALID[Input Validation]
            SSRF[SSRF Protection]
            RATE[Rate Limiting]
        end
    end

    ATTACKER -.->|Blocked| HTTPS
    MITM -.->|Blocked| CERT
    CSRF -.->|Blocked| PKCE
    INJECT -.->|Blocked| VALID
```

## Network Security

### HTTPS Enforcement

All external traffic must use HTTPS:

```yaml
# Traefik configuration
entrypoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true
  websecure:
    address: ":443"
```

### SSL/TLS Configuration

```yaml
# Let's Encrypt automatic certificates
certificatesResolvers:
  letsencrypt:
    acme:
      email: ${ACME_EMAIL}
      storage: /certificates/acme.json
      httpChallenge:
        entryPoint: web
      # Production CA
      caServer: https://acme-v02.api.letsencrypt.org/directory
```

### Security Headers

```yaml
# Traefik security headers middleware
headers:
  stsSeconds: 31536000
  stsIncludeSubdomains: true
  stsPreload: true
  forceSTSHeader: true
  contentTypeNosniff: true
  browserXssFilter: true
  referrerPolicy: "same-origin"
  contentSecurityPolicy: "default-src 'self'"
  customFrameOptionsValue: "DENY"
```

## Authentication Security

### OAuth 2.1 Implementation

Key security features:

1. **PKCE Mandatory**
   ```python
   # Enforce PKCE on all flows
   if not code_challenge:
       raise InvalidRequest("PKCE required")
   if code_challenge_method != "S256":
       raise InvalidRequest("Only S256 supported")
   ```

2. **State Parameter**
   ```python
   # CSRF protection
   state = secrets.token_urlsafe(32)
   redis.setex(f"oauth:state:{state}", 300, client_data)
   ```

3. **Short-lived Tokens**
   ```python
   ACCESS_TOKEN_LIFETIME = 2592000  # 30 days
   STATE_LIFETIME = 300  # 5 minutes
   CODE_LIFETIME = 600  # 10 minutes
   ```

### JWT Security

RS256 signing with key rotation support:

```python
# Key generation
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

# Token signing
token = jwt.encode(
    payload,
    private_key,
    algorithm="RS256",
    headers={"kid": "key-1"}
)
```

### GitHub OAuth Integration

User authentication security:

```python
# User allowlist enforcement
ALLOWED_GITHUB_USERS = os.getenv("ALLOWED_GITHUB_USERS", "").split(",")

if github_username not in ALLOWED_GITHUB_USERS:
    raise Forbidden("User not authorized")
```

## Authorization Security

### ForwardAuth Middleware

Every MCP request validated:

```python
@app.get("/verify")
async def verify_token(request: Request):
    # Extract token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response(status_code=401)

    token = auth_header[7:]

    try:
        # Verify JWT
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"]
        )

        # Check revocation
        if await is_token_revoked(payload["jti"]):
            return Response(status_code=401)

        # Return user info
        return Response(
            status_code=200,
            headers={
                "X-User-Id": payload["sub"],
                "X-User-Name": payload.get("github_username", ""),
                "X-Auth-Token": token
            }
        )
    except JWTError:
        return Response(status_code=401)
```

### Scope Validation

Fine-grained permissions:

```python
# Scope definitions
SCOPES = {
    "mcp:read": "Read access to MCP services",
    "mcp:write": "Write access to MCP services",
    "mcp:*": "Full access to MCP services"
}

# Validation
def validate_scope(required: str, granted: str) -> bool:
    if granted == "mcp:*":
        return True
    return required in granted.split()
```

## Application Security

### Input Validation

All inputs validated and sanitized:

```python
# Client registration validation
class ClientRegistration(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=100)
    redirect_uris: List[HttpUrl]
    grant_types: List[Literal["authorization_code", "refresh_token"]]

    @validator("redirect_uris")
    def validate_redirect_uris(cls, v):
        for uri in v:
            if uri.scheme not in ["http", "https"]:
                raise ValueError("Invalid URI scheme")
        return v
```

### SSRF Protection

In fetch services:

```python
# Block private IPs
PRIVATE_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
]

def is_private_ip(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    return any(addr in network for network in PRIVATE_IP_RANGES)

# DNS resolution check
def validate_url(url: str):
    parsed = urlparse(url)
    # Resolve hostname
    ip = socket.gethostbyname(parsed.hostname)
    if is_private_ip(ip):
        raise SecurityError("Private IP not allowed")
```

### Rate Limiting

Protection against abuse:

```yaml
# Traefik rate limit middleware
rateLimit:
  average: 100  # requests per second
  burst: 200    # burst capacity
  period: 1s

# Per-IP limiting
ipWhiteList:
  sourceRange:
    - "10.0.0.0/8"  # Internal only
```

## Data Security

### Storage Security

Redis security configuration:

```yaml
# Password protection
command: redis-server --requirepass ${REDIS_PASSWORD}

# Network isolation
ports:
  - "127.0.0.1:6379:6379"  # Local only

# Persistence
save: "900 1 300 10 60 10000"
```

### Token Storage

Secure token handling:

```python
# Token storage with TTL
def store_token(token_data: dict):
    jti = token_data["jti"]
    ttl = token_data["exp"] - int(time.time())

    # Store with automatic expiration
    redis.setex(
        f"oauth:token:{jti}",
        ttl,
        json.dumps(token_data)
    )

    # Add to user index
    redis.sadd(
        f"oauth:user_tokens:{token_data['sub']}",
        jti
    )
```

### Secret Management

Environment-based secrets:

```bash
# Generate secure secrets
GATEWAY_JWT_SECRET=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# Never commit secrets
# .gitignore includes:
.env
*.key
*.pem
```

## Audit and Logging

### Security Logging

Comprehensive audit trail:

```python
# Log security events
logger.info("auth_success", extra={
    "user_id": user_id,
    "client_id": client_id,
    "ip": request.client.host,
    "user_agent": request.headers.get("User-Agent")
})

logger.warning("auth_failure", extra={
    "reason": "invalid_token",
    "ip": request.client.host,
    "token_jti": token_jti
})
```

### Log Security

```yaml
# Centralized secure logging
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    labels: "service,security"
```

## Incident Response

### Token Revocation

Immediate token invalidation:

```python
@app.post("/revoke")
async def revoke_token(
    token: str = Form(...),
    token_type_hint: str = Form(None)
):
    # Decode token
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        jti = payload["jti"]

        # Mark as revoked
        redis.setex(
            f"oauth:revoked:{jti}",
            86400,  # 24 hours
            "revoked"
        )

        # Remove from active tokens
        redis.delete(f"oauth:token:{jti}")

        return {"status": "revoked"}
    except Exception:
        # Still return success (RFC 7009)
        return {"status": "revoked"}
```

### Client Compromise

Emergency client deletion:

```bash
# Delete compromised client
just oauth-delete-client-complete client_abc123

# Revoke all client tokens
just run revoke_client_tokens client_abc123
```

## Security Best Practices

### Development Security

1. **No Hardcoded Secrets**
   ```python
   # Bad
   SECRET_KEY = "hardcoded-secret"

   # Good
   SECRET_KEY = os.environ["SECRET_KEY"]
   ```

2. **Secure Defaults**
   ```python
   # Secure by default
   ENABLE_DEBUG = os.getenv("ENABLE_DEBUG", "false").lower() == "true"
   ```

3. **Dependency Scanning**
   ```bash
   # Regular updates
   pip-audit
   safety check
   ```

### Operational Security

1. **Regular Backups**
   ```bash
   just oauth-backup
   ```

2. **Secret Rotation**
   ```bash
   # Rotate JWT signing key
   just generate-rsa-keys
   ```

3. **Security Monitoring**
   - Failed authentication attempts
   - Unusual token usage patterns
   - Service availability

## Compliance Considerations

### OAuth 2.1 Compliance

- ✅ PKCE mandatory
- ✅ Redirect URI validation
- ✅ No implicit flow
- ✅ Secure token storage

### Security Standards

- ✅ OWASP Top 10 addressed
- ✅ No SQL injection (no SQL)
- ✅ XSS protection via CSP
- ✅ CSRF protection via state/PKCE

### Privacy

- Minimal data collection
- No PII in logs
- Token-based identity
- GitHub data not stored

## Security Checklist

Before deployment:

- [ ] HTTPS enabled with valid certificates
- [ ] Strong passwords for Redis
- [ ] JWT secrets generated and secured
- [ ] GitHub OAuth app configured correctly
- [ ] User allowlist populated
- [ ] Rate limiting configured
- [ ] Logging enabled
- [ ] Backup strategy in place
- [ ] Incident response plan ready
- [ ] Security headers configured
