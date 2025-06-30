# 🔥 CLAUDE.md - The Auth Service Divine Scripture! ⚡

**🏛️ Behold! The Sacred OAuth Temple - Guardian of Divine Authentication! 🏛️**

**⚡ This is the Auth Service - The Holy Gatekeeper of Token Righteousness! ⚡**

## 🔱 The Sacred Purpose of Auth Service - Divine OAuth Oracle!

**The Auth Service is the blessed authentication guardian, the divine keeper of OAuth flows!**

This sacred service channels the following divine powers:
- **OAuth 2.1 Compliance** - RFC-blessed authentication flows with divine precision!
- **GitHub OAuth Integration** - Judgment of mortal souls through GitHub's oracle!
- **Dynamic Client Registration** - RFC 7591 gateway for MCP supplicants!
- **Client Management API** - RFC 7592 lifecycle control with bearer token blessing!
- **JWT Token Sanctification** - Divine token minting with RS256/HS256 cryptographic blessing!
- **ForwardAuth Provider** - Authentication validation for Traefik's divine judgment!
- **Token Introspection** - RFC 7662 token examination oracle!
- **Token Revocation** - RFC 7009 token banishment altar!

**⚡ The Auth Service knows all OAuth dark arts but remains pure of MCP knowledge! ⚡**

## 🏗️ The Sacred Architecture - Holy Separation of Concerns!

```
Auth Service (Port 8000)
├── OAuth Endpoints (Public divine altars!)
│   ├── POST /register - RFC 7591 client birth portal!
│   ├── GET /authorize - OAuth authorization temple!
│   ├── POST /token - Token transmutation sanctuary!
│   ├── GET /callback - GitHub OAuth return path!
│   ├── GET /.well-known/oauth-authorization-server - Divine metadata revelations!
│   └── GET /jwks - RS256 public key distribution altar!
├── Client Management (RFC 7592 sacred CRUD chambers!)
│   ├── GET /register/{client_id} - View client registration!
│   ├── PUT /register/{client_id} - Update client metadata!
│   └── DELETE /register/{client_id} - Client self-immolation!
├── Token Operations (Divine token control!)
│   ├── POST /revoke - RFC 7009 token banishment!
│   └── POST /introspect - RFC 7662 token examination!
├── Internal Endpoints (Sacred verification chambers!)
│   ├── GET/POST /verify - ForwardAuth judgment altar!
│   ├── GET /error - User-friendly error sanctuary!
│   └── GET /success - OAuth success celebration!
└── GitHub Integration (External oracle communion!)
    └── OAuth flow to GitHub's authentication realm!
```

**⚡ Pure OAuth service - knows nothing of MCP protocols! This is the law! ⚡**

## 📦 The Divine Dependencies - Blessed by mcp-oauth-dynamicclient!

This service channels the power of the **mcp-oauth-dynamicclient** package:
- **FastAPI Framework** - The blessed web temple foundation!
- **Authlib Integration** - OAuth flows with divine RFC compliance!
- **Authlib ResourceProtector** - Token validation with async divine power!
- **Redis Storage** - Eternal persistence of sacred tokens!
- **Authlib JWT** - Token crafting with RS256/HS256 cryptographic blessing!
- **Cryptography** - RSA key management for divine RS256 signatures!
- **HTTPX + AsyncOAuth2Client** - GitHub OAuth integration with async glory!

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
- `JWT_SECRET` - The divine signing key for HS256 JWT creation!
- `JWT_ALGORITHM` - RS256 or HS256 blessed algorithms (NO DEFAULTS!)!
- `JWT_PRIVATE_KEY_B64` - Base64 encoded RSA private key for RS256 glory!
- `ACCESS_TOKEN_LIFETIME` - Access token lifetime in seconds (NO DEFAULTS!)!
- `REFRESH_TOKEN_LIFETIME` - Refresh token lifetime in seconds (NO DEFAULTS!)!

**Redis Connection (Eternal Storage Temple!):**
- `REDIS_URL` - Connection to the Redis sanctuary!
- `REDIS_PASSWORD` - Redis authentication (NO DEFAULTS!)!

**Access Control (The Worthy List!):**
- `ALLOWED_GITHUB_USERS` - Comma-separated list of blessed GitHub usernames (* = all)!

**OAuth Settings (Protocol Configuration!):**
- `SESSION_TIMEOUT` - OAuth state token lifetime in seconds (NO DEFAULTS!)!
- `CLIENT_LIFETIME` - Registration lifetime in seconds (0 = eternal, NO DEFAULTS!)!

**MCP Protocol Settings (Divine Version Declaration!):**
- `MCP_PROTOCOL_VERSION` - Protocol version for OAuth discovery metadata (NO DEFAULTS!)!

**Domain Configuration:**
- `BASE_DOMAIN` - The sacred domain for all OAuth endpoints!

**⚡ All configuration through .env - never hardcode divine secrets! ⚡**

## 🚀 The Sacred Endpoints - Divine OAuth Altars!

### Public Authentication Endpoints (Open to All Supplicants!)

**POST /register - RFC 7591 Client Registration Portal!**
- Dynamic client registration for MCP clients!
- Returns client_id, client_secret, and registration_access_token!
- Supports eternal clients with CLIENT_LIFETIME=0!
- Validates redirect_uris (HTTPS required except localhost)!
- Generates secure random credentials with divine entropy!

**GET /authorize - OAuth Authorization Temple!**
- Redirects to GitHub for user authentication!
- Validates client_id and redirect_uri!
- Implements PKCE for divine security (S256 only)!
- Stores state in Redis with 5-minute TTL!
- Returns user-friendly error page for invalid clients!

**POST /token - Token Transmutation Sanctuary!**
- Exchanges authorization codes for access tokens!
- Validates PKCE challenges with S256 (plain method REJECTED)!
- Returns JWT tokens with user claims!
- Supports refresh_token grant type!
- Uses Authlib for RFC-compliant token generation!

**GET /.well-known/oauth-authorization-server - Divine Metadata!**
- Server capabilities and endpoints revelation!
- Required by MCP specification 2025-06-18!
- Includes JWKS URI for RS256 public key discovery!

**GET /jwks - RS256 Public Key Distribution!**
- Serves RSA public key in JWK format!
- Enables RS256 token verification by clients!
- Key ID: "blessed-key-1" for rotation support!

### Client Management Endpoints (RFC 7592 Sacred CRUD!)

**GET /register/{client_id} - View Client Registration!**
- Requires registration_access_token Bearer auth!
- Returns current client metadata!
- 404 if client not found or expired!

**PUT /register/{client_id} - Update Client Registration!**
- Requires registration_access_token Bearer auth!
- Updates redirect_uris and metadata!
- Validates all URIs for security!

**DELETE /register/{client_id} - Client Self-Immolation!**
- Requires registration_access_token Bearer auth!
- Permanently removes client registration!
- Returns 204 No Content on success!

### Token Operations (Divine Token Control!)

**POST /revoke - RFC 7009 Token Revocation!**
- Revokes access or refresh tokens!
- Always returns 200 (per RFC 7009)!
- Removes token from Redis immediately!

**POST /introspect - RFC 7662 Token Introspection!**
- Examines token validity and claims!
- Returns active status and metadata!
- Client authentication required!

### Internal Verification Endpoints (ForwardAuth Sacred Chamber!)

**GET/POST /verify - Authentication Validation Altar!**
- Called by Traefik ForwardAuth middleware!
- Uses Authlib AsyncResourceProtector!
- Validates Bearer tokens from Authorization header!
- Returns user information in response headers!

### User Experience Endpoints (Divine Error Handling!)

**GET /error - User-Friendly Error Sanctuary!**
- Beautiful error pages for OAuth failures!
- Clear instructions for recovery!
- No caching headers for security!
- Explains expired states and common issues!

**GET /success - OAuth Success Celebration!**
- Displays authorization codes for out-of-band flows!
- Shows success confirmation!
- Used with urn:ietf:wg:oauth:2.0:oob redirect URI!

**GET /callback - GitHub OAuth Return Path!**
- Handles GitHub OAuth callback!
- Validates state from Redis!
- Exchanges GitHub code for user info!
- Generates authorization code!


## 🔐 The Security Commandments - Divine Protection Laws!

1. **HTTPS Only** - All endpoints require TLS encryption (except localhost for dev)!
2. **PKCE Mandatory** - S256 challenge method enforced (plain method REJECTED)!
3. **Token Validation** - Every request verified with Authlib ResourceProtector!
4. **GitHub User Whitelist** - Only the worthy may enter (* allows all authenticated)!
5. **No Token Passthrough** - Validate everything, trust nothing!
6. **Registration Token Separation** - RFC 7592 tokens ≠ OAuth access tokens!
7. **RS256 Algorithm Support** - Cryptographic signatures with RSA keys!
8. **State Token Expiry** - 5-minute TTL prevents replay attacks!
9. **Secure Random Generation** - 32-byte tokens via secrets.token_urlsafe!
10. **No Default Values** - All config must be explicit in .env!

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

## 🔑 RS256 Key Management - Divine Cryptographic Power!

### Generate RSA Keys for RS256 (The Blessed Algorithm!)
```bash
# Generate RSA keys and save to .env
just generate-rsa-keys

# This creates JWT_PRIVATE_KEY_B64 in your .env file
# The public key is derived from the private key automatically
```

**RS256 Benefits over HS256:**
- **Public key verification** - Clients can verify without secret!
- **Key rotation support** - JWKS endpoint enables smooth transitions!
- **Enhanced security** - Asymmetric cryptography is divine!
- **Standards compliance** - Industry best practice!

## 🔥 Common Issues and Divine Solutions!

### "GitHub OAuth Error" - Oracle Connection Failed!
- Verify GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET!
- Check OAuth app settings in GitHub!
- Ensure redirect URI matches configuration!

### "JWT Validation Failed" - Token Corruption!
- Check JWT_SECRET matches across services (HS256)!
- Verify JWT_PRIVATE_KEY_B64 is set (RS256)!
- Ensure JWT_ALGORITHM matches token type!
- Verify token hasn't expired!
- Ensure Bearer prefix in Authorization header!

### "Redis Connection Error" - Storage Temple Unreachable!
- Verify Redis container is running!
- Check REDIS_URL and REDIS_PASSWORD configuration!
- Ensure Redis has divine persistence enabled!

### "State Token Expired" - 5-Minute TTL Exceeded!
- OAuth state tokens expire after 5 minutes!
- Complete authentication flow quickly!
- Close old browser tabs before retrying!
- User-friendly error page explains the issue!

### "Registration Access Token Invalid" - RFC 7592 Auth Failed!
- Registration tokens are separate from OAuth tokens!
- Use the token returned during client registration!
- Tokens match client lifetime (eternal if CLIENT_LIFETIME=0)!

## 📜 The Sacred Integration Flow - How Auth Blesses All!

1. **MCP Client Approaches** - Seeks /mcp endpoint access!
2. **Traefik Intercepts** - ForwardAuth middleware activated!
3. **Auth Service Validates** - /verify endpoint judges token!
4. **Token Approved** - Request proceeds to MCP service!
5. **Token Rejected** - 401 Unauthorized with OAuth discovery!

**⚡ This flow protects all MCP endpoints with divine authentication! ⚡**

## 🔧 Implementation Details - Divine Technical Revelations!

### JWT Token Structure (The Sacred Claims!)
```json
{
  "sub": "user_id",          // GitHub user ID
  "username": "github_login", // GitHub username
  "email": "user@email.com", // GitHub email
  "name": "Display Name",    // GitHub name
  "scope": "openid profile", // OAuth scopes
  "client_id": "client_xxx", // OAuth client
  "jti": "unique_token_id",  // JWT ID for tracking
  "iat": 1234567890,         // Issued at timestamp
  "exp": 1234567890,         // Expiration timestamp
  "iss": "https://auth.domain", // Issuer
  "aud": "https://auth.domain"  // Audience
}
```

### Redis Key Patterns (The Sacred Storage Schema!)
```
oauth:state:{state}          # OAuth state (5 min TTL)
oauth:code:{code}            # Auth codes (1 year TTL for long-lived)
oauth:token:{jti}            # JWT tracking (access token lifetime)
oauth:refresh:{token}        # Refresh tokens (refresh token lifetime)
oauth:client:{client_id}     # Client data (client lifetime)
oauth:user_tokens:{username} # User token index (no expiry)
```

### Client Registration Response (RFC 7591 Blessed Format!)
```json
{
  "client_id": "client_xxx",
  "client_secret": "secret_xxx",
  "client_secret_expires_at": 0,  // 0 = never expires
  "registration_access_token": "reg-xxx",  // RFC 7592 management
  "registration_client_uri": "https://auth.domain/register/{id}"
}
```

## 🎯 The Divine Mission - Auth Service Responsibilities!

**What Auth Service MUST Do:**
- Handle all OAuth 2.1 flows with RFC compliance!
- Integrate with GitHub for user authentication!
- Validate tokens for ForwardAuth requests!
- Manage client registrations dynamically!
- Provide OAuth discovery metadata!
- Support both HS256 and RS256 algorithms!
- Implement full RFC 7591/7592 compliance!
- Provide user-friendly error pages!

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

## ✨ Divine Implementation Highlights - The Sacred Features!

### Authlib Integration Glory
- **ResourceProtector** - Divine token validation with async power!
- **AsyncOAuth2Client** - GitHub integration with blessed async/await!
- **JsonWebToken** - JWT handling with multiple algorithm support!
- **RFC Compliance** - Built on Authlib's proven foundations!

### Security Enhancements
- **No Default Values** - Every config must be explicit (divine law)!
- **PKCE Enforcement** - Plain method rejected, only S256 blessed!
- **Secure Random** - 32-byte tokens via secrets.token_urlsafe!
- **Dual Algorithm Support** - RS256 for future, HS256 for compatibility!

### User Experience Blessings
- **Beautiful Error Pages** - Clear guidance for lost souls!
- **State Expiry Messages** - Explains 5-minute timeout clearly!
- **Success Confirmations** - Visual feedback for completed flows!
- **No Cache Headers** - Prevents browser confusion!

### RFC Implementation Completeness
- **RFC 6749** - OAuth 2.0 core (with 2.1 enhancements)!
- **RFC 7591** - Dynamic client registration (fully compliant)!
- **RFC 7592** - Client management protocol (all CRUD operations)!
- **RFC 7636** - PKCE implementation (S256 only)!
- **RFC 7009** - Token revocation endpoint!
- **RFC 7662** - Token introspection endpoint!
- **RFC 8414** - Authorization server metadata!

---

**🔥 May your tokens be valid, your flows RFC-compliant, and your authentication forever secure! ⚡**
