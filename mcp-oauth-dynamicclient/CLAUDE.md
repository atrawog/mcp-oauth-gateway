# CLAUDE.md - Divine Development Guidance for MCP OAuth Dynamic Client

**🔥 This is the sacred CLAUDE.md for mcp-oauth-dynamicclient! ⚡**

## Divine Service Architecture

**🌟 mcp-oauth-dynamicclient: The OAuth 2.1 and RFC 7591/7592 Compliant Auth Service! 🌟**

This blessed service implements:
- **OAuth 2.1** - Modern authentication with PKCE (S256 only!)
- **RFC 7591** - Dynamic Client Registration Protocol
- **RFC 7592** - Dynamic Client Configuration Management Protocol
- **RFC 8414** - OAuth 2.0 Authorization Server Metadata
- **RFC 6749** - The OAuth 2.0 Authorization Framework
- **RFC 7009** - OAuth 2.0 Token Revocation
- **RFC 7662** - OAuth 2.0 Token Introspection
- **RFC 7636** - Proof Key for Code Exchange (PKCE)

## Sacred Implementation Details

### The Divine Separation of Authentication Realms

**⚡ Two authentication realms exist - never confuse them! ⚡**

1. **MCP Gateway Client Realm** - Dynamic client registration via RFC 7591/7592
   - Public `/register` endpoint for client birth
   - Bearer `registration_access_token` for client management
   - Client credentials for OAuth token issuance

2. **User Authentication Realm** - GitHub OAuth for human users
   - GitHub OAuth flow for user authentication
   - JWT tokens with user claims
   - Access control via ALLOWED_GITHUB_USERS

### The Sacred Endpoints

**🚀 OAuth 2.1 Core Endpoints:**
- `/authorize` - Authorization endpoint (initiates GitHub OAuth)
- `/token` - Token endpoint (exchanges codes for JWTs)
- `/callback` - GitHub OAuth callback
- `/verify` - ForwardAuth verification for Traefik

**📜 RFC 7591 Dynamic Registration:**
- `POST /register` - PUBLIC endpoint for client registration

**🔐 RFC 7592 Client Management (Bearer Auth Required):**
- `GET /register/{client_id}` - View client configuration
- `PUT /register/{client_id}` - Update client configuration
- `DELETE /register/{client_id}` - Delete client registration

**✨ Extension Endpoints:**
- `/.well-known/oauth-authorization-server` - Server metadata (RFC 8414)
- `/jwks` - JSON Web Key Set for RS256 public keys
- `/revoke` - Token revocation (RFC 7009)
- `/introspect` - Token introspection (RFC 7662)

### The Divine JWT Implementation

**🔥 RS256 is the blessed algorithm! HS256 exists only for transition! ⚡**

```python
# The blessed RS256 implementation in auth_authlib.py
if self.settings.jwt_algorithm == "RS256":
    # Use RSA public key for RS256 - divine cryptographic validation!
    token = self.jwt.encode(header, payload, self.key_manager.private_key)
else:
    # HS256 is HERESY but supported for backwards compatibility
    token = self.jwt.encode(header, payload, self.settings.jwt_secret)
```

### The Sacred Redis Storage Patterns

```
oauth:state:{state}          # 5 minute TTL - CSRF protection
oauth:code:{code}            # 1 year TTL - Authorization codes
oauth:token:{jti}            # 30 days TTL - JWT access tokens
oauth:refresh:{token}        # 1 year TTL - Refresh tokens
oauth:client:{client_id}     # Client lifetime - Includes registration_access_token!
oauth:user_tokens:{username} # No expiry - Index of user's tokens
```

### The Divine Client Lifecycle

1. **Birth** - POST /register creates client with credentials
2. **Blessing** - Receive `registration_access_token` for management
3. **Life** - 90 days default or eternal if CLIENT_LIFETIME=0
4. **Management** - Use Bearer token for GET/PUT/DELETE operations
5. **Death** - Natural expiration or explicit DELETE

### The Sacred Configuration (NO DEFAULTS!)

```python
class Settings(BaseSettings):
    """Sacred Configuration following the divine laws"""

    # GitHub OAuth
    github_client_id: str
    github_client_secret: str

    # JWT Configuration
    jwt_secret: str
    jwt_algorithm: str  # NO DEFAULTS!
    jwt_private_key_b64: Optional[str] = None  # Base64 encoded RSA key

    # Domain Configuration
    base_domain: str

    # Redis Configuration
    redis_url: str
    redis_password: Optional[str]  # NO DEFAULTS!

    # Token Lifetimes - NO DEFAULTS!
    access_token_lifetime: int
    refresh_token_lifetime: int
    session_timeout: int
    client_lifetime: int  # 0 = never expires

    # Access Control
    allowed_github_users: str  # NO DEFAULTS! Comma-separated or '*'

    # MCP Protocol Version
    mcp_protocol_version: str  # NO DEFAULTS!
```

### The Divine Security Architecture

**🔐 Authlib-based implementation - NO AD-HOC SECURITY CODE! ⚡**

The implementation uses:
- `authlib.oauth2` for OAuth 2.0 compliance
- `authlib.jose` for JWT handling
- `authlib.integrations.httpx_client` for GitHub OAuth
- Custom `ResourceProtector` wrapper for async FastAPI compatibility

**⚡ NEVER implement security primitives yourself! Use Authlib! ⚡**

### The Sacred PKCE Implementation

```python
def verify_pkce_challenge(self, verifier: str, challenge: str, method: str = "S256") -> bool:
    """Verify PKCE code challenge - S256 only as per CLAUDE.md sacred laws"""
    if method == "plain":
        # REJECTED: Plain method is deprecated per CLAUDE.md commandments!
        return False

    if method != "S256":
        # Only S256 is blessed by the sacred laws
        return False

    # Proper S256 verification: SHA256 hash + base64url encode
    digest = hashlib.sha256(verifier.encode()).digest()
    computed = base64.urlsafe_b64encode(digest).decode().rstrip("=")

    return computed == challenge
```

### The Divine Bearer Token Architecture

**🌟 Three types of Bearer tokens exist in the sacred realm! 🌟**

1. **OAuth Access Tokens** - JWT tokens for resource access
2. **Registration Access Tokens** - `reg-{token}` for client management
3. **GitHub Access Tokens** - External tokens from GitHub OAuth

**⚡ Each serves its divine purpose - never confuse them! ⚡**

## Development Commandments

### The Sacred Testing Approach

**🧪 Real Redis required - NO MOCKS! ⚡**

```python
# Tests must use real Redis via docker-compose
async def test_client_registration():
    # Real HTTP client
    async with httpx.AsyncClient() as client:
        # Real Redis connection
        redis_client = redis.from_url(settings.redis_url)

        # Real registration request
        response = await client.post("/register", json={...})

        # Verify in real Redis
        client_data = await redis_client.get(f"oauth:client:{client_id}")
```

### The Divine Error Handling

**⚡ RFC-compliant error responses or damnation! ⚡**

```python
# Always return proper OAuth error format
{
    "error": "invalid_client",
    "error_description": "Client authentication failed",
    "error_uri": "https://tools.ietf.org/html/rfc6749#section-5.2"
}

# Always include WWW-Authenticate header on 401
headers={"WWW-Authenticate": "Bearer"}
```

### The Sacred Logging Pattern

```python
# Structured logging for divine observability
logger.info(
    "AUTH REQUEST - Method: %s | Path: %s | Real-IP: %s | JSON: %s",
    request.method,
    request.url.path,
    traefik_headers.get("x-real-ip", "unknown"),
    json.dumps(request_data),
)
```

## Integration with the Gateway

### The Divine Traefik Labels

```yaml
# Auth service gets priority 4 (highest!)
- "traefik.http.routers.auth-oauth.priority=4"
- "traefik.http.routers.auth-oauth.rule=PathPrefix(`/register`) || PathPrefix(`/authorize`) || PathPrefix(`/token`) || PathPrefix(`/callback`) || PathPrefix(`/.well-known`)"

# ForwardAuth middleware configuration
- "traefik.http.middlewares.mcp-auth.forwardauth.address=http://auth:8000/verify"
- "traefik.http.middlewares.mcp-auth.forwardauth.authResponseHeaders=X-User-Id,X-User-Name,X-Auth-Token"
```

### The Sacred Environment Variables

```bash
# GitHub OAuth (from GitHub App)
GITHUB_CLIENT_ID=Ov23li...
GITHUB_CLIENT_SECRET=xxx...

# JWT Configuration
JWT_SECRET=xxx...  # For HS256 (deprecated)
JWT_ALGORITHM=RS256  # The blessed algorithm!
JWT_PRIVATE_KEY_B64=xxx...  # Base64 encoded RSA key

# Domain
BASE_DOMAIN=yourdomain.com

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=xxx...

# Token Lifetimes (seconds)
ACCESS_TOKEN_LIFETIME=1800  # 30 minutes
REFRESH_TOKEN_LIFETIME=31536000  # 1 year
SESSION_TIMEOUT=300  # 5 minutes
CLIENT_LIFETIME=7776000  # 90 days (0 for eternal)

# Access Control
ALLOWED_GITHUB_USERS=user1,user2  # or '*' for any GitHub user

# MCP Protocol
MCP_PROTOCOL_VERSION=2025-06-18
```

## The Divine Package Usage

### Installation

```bash
# Via pixi (blessed!)
pixi add mcp-oauth-dynamicclient

# Via pip (if you must)
pip install mcp-oauth-dynamicclient
```

### Running the Server

```bash
# Via CLI (production)
mcp-oauth-server --host 0.0.0.0 --port 8000

# Via Python
from mcp_oauth_dynamicclient import create_app, Settings

settings = Settings()  # Loads from .env
app = create_app(settings)

# Run with uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Client Registration Example

```python
import httpx
import json

async def register_client():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://auth.yourdomain.com/register",
            json={
                "redirect_uris": ["https://app.com/callback"],
                "client_name": "My Application",
                "scope": "openid profile email"
            }
        )

        if response.status_code == 201:
            result = response.json()
            print(f"Client ID: {result['client_id']}")
            print(f"Client Secret: {result['client_secret']}")
            print(f"Registration Token: {result['registration_access_token']}")
```

## The Sacred Development Workflow

1. **Environment Setup**
   ```bash
   just up  # Start Redis and dependencies
   just generate-rsa-keys  # Create JWT_PRIVATE_KEY_B64
   ```

2. **Development Mode**
   ```bash
   just dev  # Runs with --reload
   ```

3. **Testing**
   ```bash
   just test  # Real tests with real Redis!
   ```

4. **Production Build**
   ```bash
   just build  # Creates Docker image
   ```

**⚡ Remember: NO MOCKS! Real systems only! This is the divine law! ⚡**

## The Divine Integration Checklist

- ✅ **OAuth 2.1 Compliance** - PKCE S256 mandatory!
- ✅ **RFC 7591 Registration** - Public POST /register endpoint!
- ✅ **RFC 7592 Management** - Bearer token protected CRUD!
- ✅ **GitHub OAuth** - User authentication via GitHub!
- ✅ **JWT with RS256** - Cryptographically blessed tokens!
- ✅ **Redis Storage** - Sacred key patterns maintained!
- ✅ **Authlib Security** - No ad-hoc implementations!
- ✅ **ForwardAuth Ready** - Traefik integration blessed!
- ✅ **No Defaults** - All config from environment!
- ✅ **Real Testing** - No mocks, real Redis only!

**🔥 Follow these commandments and your auth service shall be blessed! ⚡**
