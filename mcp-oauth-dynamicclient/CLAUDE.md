# 🔥 CLAUDE.md - The mcp-oauth-dynamicclient Package Divine Scripture! ⚡

**📦 Behold! The Sacred OAuth Library - Divine Authentication Power Incarnate! 📦**

**⚡ This is mcp-oauth-dynamicclient - The Holy Engine of RFC-Compliant OAuth Glory! ⚡**

## 🔱 The Sacred Purpose - Divine OAuth Implementation Library!

**mcp-oauth-dynamicclient is the blessed Python package that powers ALL OAuth magic!**

This sacred library channels these divine powers:
- **RFC 7591 Compliance** - Dynamic client registration with holy precision!
- **RFC 7592 Management** - Client lifecycle control with divine CRUD!
- **OAuth 2.1 + PKCE** - Modern authentication flows blessed by standards!
- **JWT Token Crafting** - Cryptographic token minting with sacred claims!
- **Redis Integration** - Eternal storage of authentication state!
- **FastAPI + Authlib** - The blessed framework combination!

**⚡ This package IS the OAuth implementation - all services consume its power! ⚡**

## 🏗️ The Sacred Architecture - Modular Divine Components!

```
mcp_oauth_dynamicclient/
├── Core Modules (The Sacred Foundations!)
│   ├── __init__.py - Package initialization and exports!
│   ├── config.py - Configuration management with pydantic!
│   ├── models.py - Data models and schemas of truth!
│   └── keys.py - RSA key generation and management!
├── OAuth Modules (The Authentication Engines!)
│   ├── routes.py - FastAPI route definitions!
│   ├── auth_authlib.py - Authlib integration glory!
│   ├── resource_protector.py - Token validation guardian!
│   └── async_resource_protector.py - Async validation power!
├── Storage Module (The Persistence Layer!)
│   ├── redis_client.py - Redis connection and operations!
├── RFC Implementation (The Standards Compliance!)
│   ├── rfc7592.py - Client management endpoints!
├── Server Module (The Application Core!)
│   ├── server.py - FastAPI app factory!
│   └── __main__.py - CLI entry point!
└── CLI Module (The Command Interface!)
    └── cli.py - Token generation and management!
```

**⚡ Each module has its divine purpose in the OAuth machinery! ⚡**

## 📖 The Sacred Modules - Divine Component Details!

### config.py - The Configuration Oracle!
```python
class Settings(BaseSettings):
    """Divine configuration with automatic validation!"""
    
    # GitHub OAuth settings
    github_client_id: str
    github_client_secret: str
    
    # JWT configuration
    gateway_jwt_secret: str
    gateway_jwt_algorithm: str = "HS256"
    gateway_jwt_expire_minutes: int = 43200  # 30 days
    
    # Redis connection
    redis_url: str = "redis://redis:6379/0"
    
    # OAuth settings
    client_lifetime: int = 7776000  # 90 days (0 = eternal)
    
    model_config = SettingsConfigDict(env_file=".env")
```

**⚡ All configuration flows through pydantic validation! ⚡**

### models.py - The Data Schema Temple!
```python
# OAuth client registration model
class OAuthClient(BaseModel):
    client_id: str
    client_secret: str
    redirect_uris: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    
# Token models with divine claims
class TokenData(BaseModel):
    sub: str  # Subject (user ID)
    name: Optional[str]  # User display name
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    jti: str  # JWT ID for tracking
```

**⚡ Type safety through pydantic brings reliability! ⚡**

### routes.py - The Sacred Endpoint Definitions!

**The OAuth Flow Endpoints:**
- `POST /register` - RFC 7591 dynamic registration!
- `GET /authorize` - OAuth authorization initiation!
- `POST /token` - Token exchange sanctuary!
- `GET /callback` - GitHub OAuth return path!
- `GET /.well-known/oauth-authorization-server` - Metadata!

**The Management Endpoints (RFC 7592):**
- `GET /register/{client_id}` - View registration!
- `PUT /register/{client_id}` - Update registration!
- `DELETE /register/{client_id}` - Revoke registration!

**The Internal Endpoints:**
- `GET /verify` - ForwardAuth validation!

### auth_authlib.py - The Authlib Integration Glory!
```python
# OAuth server configuration with Authlib
oauth_server = AuthorizationServer(
    query_client=query_client,
    save_token=save_token,
)

# Grant type registration
oauth_server.register_grant(AuthorizationCodeGrant)
oauth_server.register_grant(RefreshTokenGrant)

# PKCE extension for divine security
oauth_server.register_extension(CodeChallengeExtension)
```

**⚡ Authlib provides RFC-compliant OAuth implementation! ⚡**

### redis_client.py - The Eternal Storage Interface!
```python
class RedisClient:
    """Divine Redis operations for OAuth state!"""
    
    async def store_client(self, client_data: dict) -> None:
        """Store client registration eternally!"""
        
    async def store_token(self, token: str, data: dict) -> None:
        """Store token with TTL blessing!"""
        
    async def get_and_delete(self, key: str) -> Optional[str]:
        """Atomic get-and-delete for security!"""
```

**⚡ Redis provides persistent state across restarts! ⚡**

### rfc7592.py - The Client Management Scripture!
```python
# RFC 7592 compliant client management
async def get_client_registration(client_id: str, token: str):
    """View client registration with bearer auth!"""
    
async def update_client_registration(client_id: str, token: str, data: dict):
    """Update registration with validation!"""
    
async def delete_client_registration(client_id: str, token: str):
    """Revoke client with divine finality!"""
```

**⚡ Full RFC 7592 compliance for client lifecycle! ⚡**

## 🔧 Installation and Sacred Setup!

### Package Installation (The Blessed Way!)
```bash
# Via pixi (the divine package manager)
pixi add mcp-oauth-dynamicclient

# Or install from source with divine intent
cd mcp-oauth-dynamicclient
pixi install -e .
```

### Environment Configuration
```bash
# Required divine variables
GITHUB_CLIENT_ID=your-github-app-id
GITHUB_CLIENT_SECRET=your-github-secret
GATEWAY_JWT_SECRET=your-secret-key
REDIS_URL=redis://redis:6379/0
ALLOWED_GITHUB_USERS=user1,user2
CLIENT_LIFETIME=7776000  # or 0 for eternal
```

## 🚀 Using the Sacred Library!

### As a FastAPI Application
```python
from mcp_oauth_dynamicclient import create_app

# Create the blessed FastAPI app
app = create_app()

# Run with uvicorn divine power
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### CLI Token Generation
```bash
# Generate GitHub token with divine automation
pixi run mcp-oauth-token

# The sacred flow:
# 1. Opens browser for GitHub auth
# 2. Captures callback automatically  
# 3. Saves tokens to .env file
# 4. Ready for immediate use!
```

### As a Library in Your Service
```python
from mcp_oauth_dynamicclient import (
    create_oauth_server,
    verify_token,
    RedisClient,
    Settings
)

# Initialize components
settings = Settings()
redis = RedisClient(settings.redis_url)
oauth_server = create_oauth_server(settings, redis)

# Use in your routes
token_data = await verify_token(bearer_token)
```

## 🔐 The Security Architecture - Divine Protection Patterns!

### Token Security
- **JWT with HS256** - HMAC signature validation!
- **30-day expiration** - Configurable lifetime!
- **JTI tracking** - Unique token identifiers!
- **Redis blacklist** - Revocation support!

### Client Security  
- **Secure random secrets** - 32-byte entropy!
- **Registration tokens** - RFC 7592 bearer auth!
- **Redirect URI validation** - No open redirects!
- **Client expiration** - Optional time limits!

### PKCE Protection
- **S256 mandatory** - SHA256 code challenges!
- **43-128 char verifiers** - RFC compliance!
- **One-time codes** - Atomic redemption!
- **5-minute expiry** - Short-lived codes!

## 🧪 Testing the Package - Divine Verification!

```bash
# Run all package tests
pixi run pytest tests/test_mcp_oauth_dynamicclient.py -v

# Test specific components
pixi run pytest tests/test_oauth_flow.py -v
pixi run pytest tests/test_rfc7592_compliance.py -v

# Coverage measurement
pixi run pytest --cov=mcp_oauth_dynamicclient
```

**⚡ Real integration tests - no mocking allowed! ⚡**

## 🔥 Common Issues and Divine Solutions!

### "Import Error" - Package Not Found!
- Ensure pixi installation completed!
- Check PYTHONPATH includes package!
- Verify __init__.py exports!

### "Redis Connection Failed" - Storage Unavailable!
- Check REDIS_URL configuration!
- Verify Redis container running!
- Test connection with redis-cli!

### "JWT Validation Failed" - Token Corruption!
- Verify GATEWAY_JWT_SECRET matches!
- Check token hasn't expired!
- Ensure HS256 algorithm used!

### "GitHub OAuth Error" - External Auth Failed!
- Verify GitHub app credentials!
- Check redirect URI configuration!
- Ensure user is in allowed list!

## 📚 The Sacred API Reference - Quick Divine Lookup!

### Core Functions
```python
# App creation
app = create_app(settings: Optional[Settings] = None)

# Token operations  
token_data = await verify_token(token: str) -> TokenData
access_token = create_access_token(data: dict) -> str

# Client operations
client = await register_client(data: ClientRegistration) -> OAuthClient
client = await get_client(client_id: str) -> Optional[OAuthClient]

# OAuth operations
auth_url = create_authorization_url(client_id: str, redirect_uri: str)
tokens = await exchange_code(code: str, verifier: str) -> TokenResponse
```

### Decorators and Utilities
```python
# Require authentication
@require_auth
async def protected_route(token_data: TokenData = Depends(get_current_user)):
    pass

# Redis operations
async with get_redis() as redis:
    await redis.set("key", "value")
```

## 🎯 The Divine Mission - Package Responsibilities!

**What mcp-oauth-dynamicclient MUST Do:**
- Implement RFC-compliant OAuth flows!
- Provide reusable authentication components!
- Handle all token lifecycle management!
- Integrate with GitHub OAuth seamlessly!
- Store state in Redis reliably!

**What mcp-oauth-dynamicclient MUST NOT Do:**
- Know about MCP protocols!
- Implement service-specific logic!
- Handle routing or proxy concerns!
- Manage Docker orchestration!
- Make infrastructure decisions!

**⚡ Pure OAuth implementation - focused and reusable! ⚡**

## 🔱 The Sacred Integration Pattern!

Services use this package through divine dependency:
```yaml
# In service's pixi.toml
[dependencies]
mcp-oauth-dynamicclient = { path = "../mcp-oauth-dynamicclient" }
```

Then import and use the blessed components:
```python
from mcp_oauth_dynamicclient import create_app

# The auth service is just a thin wrapper!
app = create_app()
```

**⚡ Don't reinvent OAuth - use this blessed package! ⚡**

---

**🔥 May your tokens be valid, your flows RFC-compliant, and your authentication forever secure! ⚡**