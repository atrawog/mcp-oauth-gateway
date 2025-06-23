# 🔥 CLAUDE.md - The Auth Service Divine Scripture! ⚡

**🏛️ Behold! The Sacred OAuth Temple - Guardian of Divine Authentication! 🏛️**

**⚡ This is the Auth Service - The Holy Gatekeeper of Token Righteousness! ⚡**

## 🔱 The Sacred Purpose of Auth Service - Divine OAuth Oracle!

**The Auth Service is the blessed authentication guardian, the divine keeper of OAuth flows!**

This sacred service channels the following divine powers:
- **OAuth 2.1 Compliance** - RFC-blessed authentication flows with divine precision!
- **GitHub OAuth Integration** - Judgment of mortal souls through GitHub's oracle!
- **Dynamic Client Registration** - RFC 7591 gateway for MCP supplicants!
- **JWT Token Sanctification** - Divine token minting with cryptographic blessing!
- **ForwardAuth Provider** - Authentication validation for Traefik's divine judgment!

**⚡ The Auth Service knows all OAuth dark arts but remains pure of MCP knowledge! ⚡**

## 🏗️ The Sacred Architecture - Holy Separation of Concerns!

```
Auth Service (Port 8000)
├── OAuth Endpoints (Public divine altars!)
│   ├── /register - RFC 7591 client birth portal!
│   ├── /authorize - OAuth authorization temple!
│   ├── /token - Token transmutation sanctuary!
│   └── /.well-known/* - Divine metadata revelations!
├── Internal Endpoints (Sacred verification chambers!)
│   └── /verify - ForwardAuth judgment altar!
└── GitHub Integration (External oracle communion!)
    └── OAuth flow to GitHub's authentication realm!
```

**⚡ Pure OAuth service - knows nothing of MCP protocols! This is the law! ⚡**

## 📦 The Divine Dependencies - Blessed by mcp-oauth-dynamicclient!

This service channels the power of the **mcp-oauth-dynamicclient** package:
- **FastAPI Framework** - The blessed web temple foundation!
- **Authlib Integration** - OAuth flows with divine RFC compliance!
- **Redis Storage** - Eternal persistence of sacred tokens!
- **PyJWT** - Token crafting with cryptographic blessing!

**⚡ All OAuth logic flows through mcp-oauth-dynamicclient - never reinvent the divine wheel! ⚡**

## 🐳 The Docker Manifestation - Container of Divine Isolation!

### Dockerfile - The Sacred Build Incantation!
```dockerfile
FROM python:3.11-slim  # The blessed Python vessel!

# Install pixi - The holy package manager!
# Copy requirements and sacred source!
# Run with uvicorn - The divine ASGI server!

EXPOSE 8000  # The blessed authentication port!
HEALTHCHECK  # Prove thy divine readiness!
```

### Dockerfile.coverage - The Sidecar Coverage Vessel!
```dockerfile
# Special coverage-enabled container for divine metrics!
# Includes coverage-spy for production measurement!
# Same functionality with blessed instrumentation!
```

**⚡ Two containers - one for production purity, one for coverage divination! ⚡**

## 🔧 The Sacred Configuration - Environment Variables of Power!

**GitHub OAuth Credentials (External Oracle Connection!):**
- `GITHUB_CLIENT_ID` - Your GitHub app's divine identifier!
- `GITHUB_CLIENT_SECRET` - The secret key to GitHub's authentication realm!

**JWT Configuration (Token Minting Altar!):**
- `GATEWAY_JWT_SECRET` - The divine signing key for JWT creation!
- `GATEWAY_JWT_ALGORITHM` - HS256 blessed algorithm (default)!
- `GATEWAY_JWT_EXPIRE_MINUTES` - Token lifetime (43200 = 30 days)!

**Redis Connection (Eternal Storage Temple!):**
- `REDIS_URL` - Connection to the Redis sanctuary!

**Access Control (The Worthy List!):**
- `ALLOWED_GITHUB_USERS` - Comma-separated list of blessed GitHub usernames!

**OAuth Settings (Protocol Configuration!):**
- `OAUTH_REDIRECT_URI` - The sacred return path after authentication!
- `CLIENT_LIFETIME` - Registration lifetime in seconds (0 = eternal)!

**MCP Protocol Settings (Divine Version Declaration!):**
- `MCP_PROTOCOL_VERSION` - Protocol version for OAuth discovery metadata (uses environment default)!
- `MCP_CORS_ORIGINS` - CORS configuration for cross-origin access!

**⚡ All configuration through .env - never hardcode divine secrets! ⚡**

## 🚀 The Sacred Endpoints - Divine OAuth Altars!

### Public Authentication Endpoints (Open to All Supplicants!)

**POST /register - RFC 7591 Client Registration Portal!**
- Dynamic client registration for MCP clients!
- Returns client_id, client_secret, and registration_access_token!
- Supports eternal clients with CLIENT_LIFETIME=0!

**GET /authorize - OAuth Authorization Temple!**
- Redirects to GitHub for user authentication!
- Validates client_id and redirect_uri!
- Implements PKCE for divine security!

**POST /token - Token Transmutation Sanctuary!**
- Exchanges authorization codes for access tokens!
- Validates PKCE challenges with S256!
- Returns JWT tokens with user claims!

**GET /.well-known/oauth-authorization-server - Divine Metadata!**
- Server capabilities and endpoints revelation!
- Required by MCP specification 2025-06-18!

### Internal Verification Endpoints (ForwardAuth Sacred Chamber!)

**GET /verify - Authentication Validation Altar!**
- Called by Traefik ForwardAuth middleware!
- Validates Bearer tokens from Authorization header!
- Returns user information in response headers!


## 🔐 The Security Commandments - Divine Protection Laws!

1. **HTTPS Only** - All endpoints require TLS encryption!
2. **PKCE Mandatory** - S256 challenge method enforced!
3. **Token Validation** - Every request verified with holy fury!
4. **GitHub User Whitelist** - Only the worthy may enter!
5. **No Token Passthrough** - Validate everything, trust nothing!

**⚡ Security is not optional - it's divine law! ⚡**

## 🧪 Testing the Auth Service - Divine Verification Rituals!

```bash
# Service verification via OAuth discovery
just test-auth-discovery

# Full OAuth flow testing
just test-oauth-flow

# ForwardAuth validation
just test-forwardauth

# Client registration testing
just test-registration
```

**⚡ Test with real services - no mocks in this sacred realm! ⚡**

## 🔥 Common Issues and Divine Solutions!

### "GitHub OAuth Error" - Oracle Connection Failed!
- Verify GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET!
- Check OAuth app settings in GitHub!
- Ensure redirect URI matches configuration!

### "JWT Validation Failed" - Token Corruption!
- Check GATEWAY_JWT_SECRET matches across services!
- Verify token hasn't expired (30 day default)!
- Ensure Bearer prefix in Authorization header!

### "Redis Connection Error" - Storage Temple Unreachable!
- Verify Redis container is running!
- Check REDIS_URL configuration!
- Ensure Redis has divine persistence enabled!

## 📜 The Sacred Integration Flow - How Auth Blesses All!

1. **MCP Client Approaches** - Seeks /mcp endpoint access!
2. **Traefik Intercepts** - ForwardAuth middleware activated!
3. **Auth Service Validates** - /verify endpoint judges token!
4. **Token Approved** - Request proceeds to MCP service!
5. **Token Rejected** - 401 Unauthorized with OAuth discovery!

**⚡ This flow protects all MCP endpoints with divine authentication! ⚡**

## 🎯 The Divine Mission - Auth Service Responsibilities!

**What Auth Service MUST Do:**
- Handle all OAuth 2.1 flows with RFC compliance!
- Integrate with GitHub for user authentication!
- Validate tokens for ForwardAuth requests!
- Manage client registrations dynamically!
- Provide OAuth discovery metadata!

**What Auth Service MUST NOT Do:**
- Know anything about MCP protocols!
- Handle MCP-specific requests!
- Store MCP session state!
- Route to MCP services directly!
- Mix authentication with application logic!

**⚡ Separation of concerns is divine law! OAuth here, MCP elsewhere! ⚡**

## 🔱 Remember the Sacred Trinity!

The Auth Service is the second tier of the holy trinity:
1. **Traefik** - Routes requests (knows paths)!
2. **Auth Service** - Validates authentication (knows OAuth)! ← YOU ARE HERE
3. **MCP Services** - Handle protocols (knows MCP)!

**⚡ Each tier has its divine purpose! Never shall they merge! ⚡**

---

**🔥 May your tokens be valid, your flows RFC-compliant, and your authentication forever secure! ⚡**