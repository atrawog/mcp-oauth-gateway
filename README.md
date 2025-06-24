# MCP OAuth Gateway

An OAuth 2.1 Authorization Server that adds authentication to any MCP (Model Context Protocol) server without code modification. The gateway acts as an OAuth Authorization Server while using GitHub as the Identity Provider (IdP) for user authentication.

📖 **[View Documentation](https://atrawog.github.io/mcp-oauth-gateway)** | 🔧 **[Installation Guide](https://atrawog.github.io/mcp-oauth-gateway/installation/quick-start.html)** | 🏗️ **[Architecture Overview](https://atrawog.github.io/mcp-oauth-gateway/architecture.html)**

## ⚠️ Important Notice

**This is a reference implementation and test platform for the MCP protocol.** 

- **Primary Purpose**: Reference implementation for MCP protocol development and testing
- **Experimental Nature**: Used as a test platform for future MCP protocol iterations
- **Security Disclaimer**: While this implementation strives for security best practices, this implementation likely contains bugs and security vulnerabilities
- **Production Warning**: NOT recommended for production use without thorough security review
- **Use at Your Own Risk**: This is experimental software intended for development and testing

## 🏗️ Architecture

### Overview

The MCP OAuth Gateway is a **zero-modification authentication layer** for MCP servers. It implements OAuth 2.1 with dynamic client registration (RFC 7591/7592) and leverages GitHub as the identity provider for user authentication. The architecture follows these core principles:

- **Complete Separation of Concerns**: Authentication, routing, and MCP protocol handling are strictly isolated
- **No MCP Server Modifications**: Official MCP servers run unmodified, wrapped only for HTTP transport
- **Standards Compliance**: Full OAuth 2.1, RFC 7591/7592, and MCP protocol compliance
- **Production-Ready Security**: HTTPS everywhere, PKCE mandatory, JWT tokens, secure session management
- **Dynamic Service Discovery**: Services can be enabled/disabled via configuration

### System Components

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                   EXTERNAL CLIENTS                                  │
│         (Claude.ai, MCP CLI tools, IDE extensions, Custom integrations)             │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                     HTTPS │ :443
                                           ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               TRAEFIK REVERSE PROXY                                 │
│                          (Layer 1: Routing & TLS Termination)                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ • Let's Encrypt automatic HTTPS certificates for all subdomains                     │
│ • Priority-based routing rules (OAuth > Verify > MCP > Catch-all)                  │
│ • ForwardAuth middleware for MCP endpoints → Auth Service /verify                  │
│ • Request routing based on subdomain and path:                                      │
│   - auth.domain.com/* → Auth Service (no auth required)                            │
│   - *.domain.com/.well-known/* → Auth Service (OAuth discovery)                    │
│   - *.domain.com/mcp → MCP Services (auth required via ForwardAuth)                │
│ • Docker service discovery via labels                                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
                    │                                              │
                    │ OAuth/Auth Requests                          │ MCP Requests
                    │ (unauthenticated)                           │ (authenticated)
                    ↓                                              ↓
┌───────────────────────────────────────────┐    ┌───────────────────────────────────┐
│           AUTH SERVICE                    │    │         MCP SERVICES                │
│   (Layer 2: OAuth Authorization Server)   │    │    (Layer 3: Protocol Handlers)     │
├───────────────────────────────────────────┤    ├───────────────────────────────────┤
│ Container: auth:8000                      │    │ Containers:                         │
│ Package: mcp-oauth-dynamicclient          │    │ • mcp-fetch:3000                    │
│                                           │    │ • mcp-filesystem:3000               │
│ OAuth Endpoints:                          │    │ • mcp-memory:3000                   │
│ • POST /register (RFC 7591)               │    │ • mcp-time:3000                     │
│ • GET /authorize + /callback              │    │ • ... (dynamically enabled)         │
│ • POST /token                             │    │                                     │
│ • GET /.well-known/* (RFC 8414)          │    │ Architecture:                       │
│ • POST /revoke, /introspect              │    │ • mcp-streamablehttp-proxy wrapper  │
│                                           │    │ • Spawns official MCP stdio servers │
│ Management Endpoints (RFC 7592):          │    │ • Bridges stdio ↔ HTTP/SSE          │
│ • GET/PUT/DELETE /register/{client_id}    │    │ • No OAuth knowledge                │
│                                           │    │ • Receives user identity in headers │
│ Internal Endpoints:                       │    │                                     │
│ • GET/POST /verify (ForwardAuth)         │    │ Protocol Endpoints:                 │
│                                           │    │ • POST /mcp (JSON-RPC over HTTP)    │
│ External Integration:                     │←---│ • GET /mcp (SSE for async messages) │
│ • GitHub OAuth (user authentication)      │    │ • Health checks on /health          │
└───────────────────────────────────────────┘    └───────────────────────────────────┘
                    │                                              ↑
                    │                                              │
                    └──────────────┬───────────────────────────────┘
                                   │
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                REDIS STORAGE LAYER                                  │
│                            (Persistent State Management)                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Container: redis:6379                                                               │
│ Persistence: AOF + RDB snapshots                                                    │
│                                                                                     │
│ Data Structures:                                                                    │
│ • oauth:client:{client_id} → OAuth client registrations (90 days / eternal)        │
│ • oauth:state:{state} → Authorization flow state (5 minutes)                       │
│ • oauth:code:{code} → Authorization codes + user info (1 year)                     │
│ • oauth:token:{jti} → JWT token tracking for revocation (30 days)                  │
│ • oauth:refresh:{token} → Refresh token data (1 year)                              │
│ • oauth:user_tokens:{username} → User's active tokens index                        │
│ • redis:session:{id}:state → MCP session state (managed by proxy)                  │
│ • redis:session:{id}:messages → MCP message queues                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘

NETWORK TOPOLOGY:
• All services connected via 'public' Docker network
• Internal service communication only (except Traefik ingress)
• Redis exposed on localhost:6379 for debugging only
• Each MCP service runs in isolated container with no shared state
```

### Request Flow Scenarios

#### 1. Client Registration Flow (RFC 7591)
```
Client → POST /register → Traefik → Auth Service
                                    ↓
                                    Creates client_id + client_secret
                                    Stores in Redis
                                    ↓
                                    ← Returns credentials + registration_access_token
```

#### 2. User Authentication Flow (OAuth 2.1 + GitHub)
```
Client → GET /authorize → Traefik → Auth Service
                                    ↓
                                    Validates client_id
                                    Stores PKCE challenge in Redis
                                    ↓
                                    → Redirect to GitHub OAuth
                                    ↓
User authenticates with GitHub ← ← ← ┘
         ↓
GitHub → GET /callback → Traefik → Auth Service
                                    ↓
                                    Validates GitHub user
                                    Creates authorization code
                                    Stores in Redis with user info
                                    ↓
                                    → Redirect to client with code
```

#### 3. Token Exchange Flow
```
Client → POST /token → Traefik → Auth Service
        (client_id +              ↓
         client_secret +          Validates client credentials
         auth code +              Validates PKCE verifier
         PKCE verifier)           Retrieves user info from Redis
                                  Creates JWT with user + client claims
                                  ↓
                                  ← Returns access_token + refresh_token
```

#### 4. MCP Request Flow (Authenticated)
```
Client → POST /mcp → Traefik → ForwardAuth Middleware
        (Bearer token)          ↓
                               GET /verify → Auth Service
                                            ↓
                                            Validates JWT
                                            Extracts user info
                                            ↓
                               ← Returns user headers ←
                               ↓
                               Routes to MCP Service
                               (with X-User-Id, X-User-Name headers)
                               ↓
                               MCP Service processes request
                               ↓
                               ← Returns MCP protocol response
```

### Security Architecture

#### Authentication Layers
1. **TLS/HTTPS**: Enforced by Traefik for all external communication
2. **OAuth Client Authentication**: client_id + client_secret at token endpoint
3. **User Authentication**: GitHub OAuth with ALLOWED_GITHUB_USERS whitelist
4. **Token Authentication**: JWT Bearer tokens for API access
5. **PKCE Protection**: Mandatory S256 code challenges

#### Security Boundaries
- **Public Access**: Only /register and /.well-known/* endpoints
- **Client-Authenticated**: /token endpoint requires client credentials
- **User-Authenticated**: /authorize requires GitHub login
- **Bearer-Authenticated**: All /mcp endpoints require valid JWT
- **Registration-Token-Authenticated**: Client management endpoints (RFC 7592)

#### Token Types and Scopes
- **registration_access_token**: Bearer token for client management only
- **access_token**: JWT containing user identity + client_id for MCP access
- **refresh_token**: Opaque token for obtaining new access tokens
- **authorization_code**: One-time code binding user to client

### Architectural Decisions

#### Why Three Layers?
1. **Traefik (Routing)**: Centralizes TLS, routing, and auth enforcement
2. **Auth Service (OAuth)**: Isolated OAuth implementation, no MCP knowledge
3. **MCP Services (Protocol)**: Pure MCP protocol handlers, no auth knowledge

#### Why mcp-streamablehttp-proxy?
- Wraps official stdio-based MCP servers without modification
- Provides HTTP/SSE transport required for web clients
- Manages subprocess lifecycle and session state
- Enables horizontal scaling possibilities

#### Why Redis?
- Fast, reliable state storage for OAuth flows
- Supports atomic operations for security
- Built-in TTL for automatic cleanup
- Enables distributed deployment if needed

#### Why GitHub OAuth?
- Trusted identity provider for developers
- No password management needed
- Strong security with 2FA support
- Rich user profile information

### OAuth Architecture: Client Credentials + User Authentication

The gateway implements a **sophisticated OAuth 2.1 system** with **three distinct authentication flows**:

1. **GitHub Device Flow (RFC 8628)** - For command-line/browserless scenarios
2. **GitHub OAuth Web Flow** - For browser-based end-user authentication  
3. **Dynamic Client Registration (RFC 7591)** - For MCP client registration

#### Authentication Flow Decision Tree

```
Need Authentication?
├─> For Gateway's Own GitHub Access?
│   └─> Use Device Flow: `just generate-github-token`
│       - Shows code: "Visit github.com/login/device"
│       - No browser redirect needed
│       - Stores GITHUB_PAT in .env
│
├─> For MCP Client Token?
│   └─> Use Device Flow: `just mcp-client-token`
│       - Client uses device flow for browserless auth
│       - Stores MCP_CLIENT_ACCESS_TOKEN in .env
│
└─> For End User Access (Browser)?
    └─> Use Standard OAuth Flow
        - User visits protected resource
        - Redirected to GitHub for login
        - Redirected back to gateway
        - JWT issued with user+client identity
```

The gateway implements this sophisticated system that combines client credential authentication with GitHub user authentication:

```
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                        OAUTH CLIENT REGISTRATION (RFC 7591/7592)                  ║
╠═══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                   ║
║  📝 STEP 1: CLIENT REGISTRATION (No Authentication Required)                      ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐  ║
║  │ POST /register                                                              │  ║
║  │ • Public endpoint - any MCP client can register                             │  ║
║  │ • Creates OAuth client application credentials                              │  ║
║  │                                                                             │  ║
║  │ Request Body:                                                               │  ║
║  │ {                                                                           │  ║
║  │   "redirect_uris": ["https://example.com/callback"],                       │  ║
║  │   "client_name": "My MCP Client"                                            │  ║
║  │ }                                                                           │  ║
║  │                                                                             │  ║
║  │ Response:                                                                   │  ║
║  │ • client_id: "client_abc123..."          ← OAuth client credentials        │  ║
║  │ • client_secret: "secret_xyz789..."      ← Used at /token endpoint         │  ║
║  │ • registration_access_token: "reg_tok..."← ONLY for client management      │  ║
║  │ • registration_client_uri: "https://auth.../register/client_abc123"        │  ║
║  └─────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                   ║
║  🔧 OPTIONAL: CLIENT MANAGEMENT (Requires registration_access_token)              ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐  ║
║  │ Authorization: Bearer <registration_access_token>                           │  ║
║  │                                                                             │  ║
║  │ • GET /register/{client_id}    - View client configuration                  │  ║
║  │ • PUT /register/{client_id}    - Update redirect URIs, etc.                 │  ║
║  │ • DELETE /register/{client_id} - Delete client registration                 │  ║
║  │                                                                             │  ║
║  │ Note: This token is ONLY for managing the client registration,             │  ║
║  │       NOT for accessing MCP resources!                                      │  ║
║  └─────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

                                         ↓
                    Client has credentials, now needs user authorization
                                         ↓

╔═══════════════════════════════════════════════════════════════════════════════════╗
║                           USER AUTHENTICATION FLOW (GitHub OAuth)                 ║
╠═══════════════════════════════════════════════════════════════════════════════════╣
║                                                                                   ║
║  👤 STEP 2: USER AUTHORIZATION (Human authenticates via GitHub)                   ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐  ║
║  │ GET /authorize?client_id=client_abc123&redirect_uri=...&code_challenge=... │  ║
║  │                                                                             │  ║
║  │ 1. Gateway validates client_id exists                                       │  ║
║  │ 2. Redirects user to GitHub OAuth:                                          │  ║
║  │    → User logs into GitHub                                                  │  ║
║  │    → GitHub authenticates the human user                                    │  ║
║  │    → Returns to gateway /callback with GitHub user info                     │  ║
║  │ 3. Gateway checks ALLOWED_GITHUB_USERS whitelist                            │  ║
║  │ 4. Creates authorization code tied to:                                      │  ║
║  │    • The OAuth client (client_id)                                           │  ║
║  │    • The GitHub user (username, email, etc.)                                │  ║
║  │ 5. Redirects back to client with code                                       │  ║
║  └─────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                   ║
║  🎫 STEP 3: TOKEN EXCHANGE (Client credentials + Authorization code)              ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐  ║
║  │ POST /token                                                                 │  ║
║  │ Content-Type: application/x-www-form-urlencoded                             │  ║
║  │                                                                             │  ║
║  │ Request:                                                                    │  ║
║  │ • client_id=client_abc123          ← Authenticates the OAuth client        │  ║
║  │ • client_secret=secret_xyz789      ← Proves client identity                │  ║
║  │ • code=auth_code_from_step_2       ← Contains GitHub user info             │  ║
║  │ • code_verifier=pkce_verifier      ← PKCE verification                     │  ║
║  │                                                                             │  ║
║  │ Response:                                                                   │  ║
║  │ • access_token: JWT containing:                                             │  ║
║  │   - sub: GitHub user ID                                                     │  ║
║  │   - username: GitHub username                                               │  ║
║  │   - email: GitHub email                                                     │  ║
║  │   - client_id: client_abc123                                                │  ║
║  │ • refresh_token: For renewing access                                        │  ║
║  └─────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                   ║
║  🛡️ STEP 4: RESOURCE ACCESS (Using the access token)                             ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐  ║
║  │ Authorization: Bearer <access_token>                                        │  ║
║  │                                                                             │  ║
║  │ • Token contains BOTH client_id AND user identity                           │  ║
║  │ • Traefik ForwardAuth validates token via /verify                           │  ║
║  │ • User identity passed to MCP services as headers:                          │  ║
║  │   - X-User-Id: GitHub user ID                                               │  ║
║  │   - X-User-Name: GitHub username                                            │  ║
║  │ • Access granted to /mcp endpoints on all enabled services                  │  ║
║  └─────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

🔑 KEY POINTS:
• client_id + client_secret authenticate the OAuth CLIENT (e.g., Claude.ai)
• GitHub OAuth authenticates the human USER
• The final access_token combines BOTH: which client AND which user
• registration_access_token is ONLY for client management, NOT resource access
```

### OAuth Roles

1. **MCP OAuth Gateway** - OAuth 2.1 Authorization Server
   - **Client Registration**: Implements RFC 7591/7592 for dynamic client registration
   - **User Authentication**: Integrates with GitHub OAuth as the Identity Provider
   - **Token Issuance**: Issues JWT access tokens containing both client and user identity
   - **Token Types**:
     - `registration_access_token`: Only for managing client registrations (RFC 7592)
     - `access_token`: JWT with user claims + client_id for accessing MCP resources
     - `refresh_token`: For renewing access tokens

2. **GitHub OAuth** - Identity Provider (IdP) 
   - Authenticates human users through GitHub's OAuth flow
   - Provides user identity (ID, username, email) to the gateway
   - Gateway validates users against ALLOWED_GITHUB_USERS whitelist
   - User info is embedded in the final JWT access token

3. **MCP Servers** - Protected Resources
   - Run unmodified official MCP servers wrapped with mcp-streamablehttp-proxy
   - Protected by OAuth without any code changes  
   - Receive pre-authenticated requests with user identity in headers
   - Support various protocol versions based on implementation

## 📋 Requirements

### System Requirements

- **Docker** and **Docker Compose** (required for all services)
- **[pixi](https://pixi.sh/latest/)** - Modern Python package manager
- **[just](https://github.com/casey/just)** - Command runner (all commands go through just)
- **Python 3.11+** (managed automatically by pixi)

### Infrastructure Requirements

- **Public IP address and properly configured DNS** (MANDATORY - no exceptions!)
  - All subdomains must resolve to your server:
    - `auth.your-domain.com` - OAuth authorization server
    - `service.your-domain.com` - Each MCP service subdomain
  - Ports 80 and 443 must be accessible from the internet
  - Let's Encrypt certificate provisioning requires public access
  - **NO LOCALHOST DEPLOYMENTS** - The gateway requires real domains

### GitHub OAuth App

You'll need to create a GitHub OAuth App that serves **two distinct purposes**:

1. **End-User Authentication** (Browser-based OAuth flow)
   - When users access protected MCP services via browser/Claude.ai
   - Users are redirected to GitHub for authentication
   - Requires callback URL: `https://auth.yourdomain.com/callback`

2. **Gateway Self-Authentication** (Device flow)
   - When the gateway itself needs GitHub access
   - Uses device flow (no browser redirect)
   - Initiated by `just generate-github-token`

## 🚀 Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/atrawog/mcp-oauth-gateway.git
cd mcp-oauth-gateway

# Install dependencies with pixi
pixi install

# Run initial setup
just setup
```

### 2. Configure Environment

The gateway uses a `.env` file for all configuration. Follow these steps to set it up:

```bash
# 1. Copy the example configuration
cp .env.example .env

# 2. Generate required secrets
just generate-all-secrets    # Generates JWT secret, RSA keys, and Redis password

# 3. Edit .env with your configuration
nano .env
```

#### Essential Configuration Steps

⚠️ **IMPORTANT**: The gateway requires only a few tokens to run. Most tokens in `.env.example` are for testing only!

##### 🔴 REQUIRED Tokens (Gateway Won't Start Without These)

1. **Domain Setup** (REQUIRED - Must be real domains!)
   ```bash
   BASE_DOMAIN=your-domain.com              # Your actual domain
   ACME_EMAIL=admin@your-domain.com        # Email for Let's Encrypt
   ```

2. **GitHub OAuth App** (REQUIRED - Create at github.com/settings/developers)
   ```bash
   GITHUB_CLIENT_ID=your_github_client_id     # From GitHub OAuth App
   GITHUB_CLIENT_SECRET=your_github_client_secret  # From GitHub OAuth App
   ```

3. **Security Keys** (REQUIRED - Generate these)
   ```bash
   # Generate all secrets at once:
   just generate-all-secrets
   
   # Or generate individually:
   just generate-jwt-secret      # Sets: GATEWAY_JWT_SECRET
   just generate-rsa-keys        # Sets: JWT_PRIVATE_KEY_B64
   just generate-redis-password  # Sets: REDIS_PASSWORD
   ```

4. **Access Control** (REQUIRED - Choose one)
   ```bash
   # Option 1: Whitelist specific users
   ALLOWED_GITHUB_USERS=user1,user2,user3
   
   # Option 2: Allow any authenticated GitHub user
   ALLOWED_GITHUB_USERS=*
   ```

##### 🟡 OPTIONAL Tokens (Only for Testing/Development)

These tokens are NOT needed to run the gateway - they're only used by automated tests:

```bash
# GitHub PAT - Only used in tests, NOT by the gateway itself
GITHUB_PAT=ghp_xxx...                    # Generated by: just generate-github-token

# Gateway OAuth tokens - Output from testing, used by test suite
GATEWAY_OAUTH_ACCESS_TOKEN=xxx...        # Generated during OAuth flow
GATEWAY_OAUTH_REFRESH_TOKEN=xxx...       # Generated during OAuth flow
GATEWAY_OAUTH_CLIENT_ID=xxx...           # Generated during client registration
GATEWAY_OAUTH_CLIENT_SECRET=xxx...       # Generated during client registration

# MCP Client tokens - Only for testing mcp-streamablehttp-client
MCP_CLIENT_ACCESS_TOKEN=xxx...           # Generated by: just mcp-client-token
MCP_CLIENT_REFRESH_TOKEN=xxx...          # Generated with access token
MCP_CLIENT_ID=xxx...                     # Generated during registration
MCP_CLIENT_SECRET=xxx...                 # Generated during registration
```

##### 🟢 Service Configuration (OPTIONAL)

5. **Service Selection** (OPTIONAL - All default to enabled)
   ```bash
   # Enable/disable individual MCP services
   MCP_FETCH_ENABLED=true
   MCP_FETCHS_ENABLED=true
   MCP_FILESYSTEM_ENABLED=true
   MCP_MEMORY_ENABLED=true
   MCP_PLAYWRIGHT_ENABLED=false  # Disable if not needed
   MCP_SEQUENTIALTHINKING_ENABLED=true
   MCP_TIME_ENABLED=true
   MCP_TMUX_ENABLED=true
   MCP_EVERYTHING_ENABLED=true
   ```

### 3. Create GitHub OAuth App

1. Go to [GitHub OAuth Apps](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in:
   - **Application name**: `MCP OAuth Gateway`
   - **Homepage URL**: `https://your-domain.com`
   - **Authorization callback URL**: `https://auth.your-domain.com/callback`
4. Save the Client ID and Client Secret to your `.env` file

### 4. Start the Gateway

```bash
# Start all services
just up

# Check service health
just check-health
```

## 🔧 Configuration

All configuration is managed through the `.env` file. The gateway uses dynamic service selection - you can enable or disable individual MCP services based on your needs.

### 🔑 Token Requirements Summary

**Minimum tokens required to run the gateway:**

| Token | Purpose | How to Get | Required? |
|-------|---------|------------|-----------|
| `GITHUB_CLIENT_ID` | GitHub OAuth App ID | Create at github.com/settings/developers | ✅ YES |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App Secret | Create at github.com/settings/developers | ✅ YES |
| `GATEWAY_JWT_SECRET` | JWT signing secret | Run: `just generate-jwt-secret` | ✅ YES |
| `JWT_PRIVATE_KEY_B64` | RSA key for JWT | Run: `just generate-rsa-keys` | ✅ YES |
| `REDIS_PASSWORD` | Redis security | Run: `just generate-redis-password` | ✅ YES |

**Tokens only needed for testing:**

| Token | Purpose | How to Get | Required? |
|-------|---------|------------|-----------|
| `GITHUB_PAT` | GitHub API access in tests | Run: `just generate-github-token` | ❌ NO |
| `GATEWAY_OAUTH_*` tokens | Test suite authentication | Generated during test setup | ❌ NO |
| `MCP_CLIENT_*` tokens | Testing MCP clients | Run: `just mcp-client-token` | ❌ NO |

⚡ **Key Point**: The gateway itself doesn't use OAuth tokens - it only needs GitHub OAuth App credentials to authenticate users!

### Configuration Categories

#### 1. Core Settings (REQUIRED)

```bash
# Domain Configuration - MUST be publicly accessible domains!
BASE_DOMAIN=your-domain.com
ACME_EMAIL=your-email@example.com

# GitHub OAuth App Credentials
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret

# Security Keys (generated by just commands)
GATEWAY_JWT_SECRET=<generated-by-just-generate-jwt-secret>

# Redis Security
REDIS_PASSWORD=your_secure_redis_password
```

#### 2. Access Control

```bash
# User Whitelist Options:
ALLOWED_GITHUB_USERS=user1,user2,user3  # Specific users only
# OR
ALLOWED_GITHUB_USERS=*                  # Any GitHub user
```

#### 3. Token Configuration

```bash
# Token Lifetimes (in seconds)
CLIENT_LIFETIME=7776000        # Client registration: 90 days (0 = eternal)
# Note: Access and refresh token lifetimes are configured in .env
```

#### 4. MCP Service Management

The gateway allows you to enable/disable individual MCP services. All services default to `true` (enabled) if not specified.

```bash
# Core MCP Services
MCP_FETCH_ENABLED=true              # Web content fetching (stdio proxy)
MCP_FETCHS_ENABLED=true             # Native Python fetch implementation
MCP_FILESYSTEM_ENABLED=true         # File system access (sandboxed)
MCP_MEMORY_ENABLED=true             # Persistent memory/knowledge graph
MCP_TIME_ENABLED=true               # Time and timezone operations

# Advanced MCP Services
MCP_SEQUENTIALTHINKING_ENABLED=true # Structured problem solving
MCP_TMUX_ENABLED=true               # Terminal multiplexer integration
MCP_PLAYWRIGHT_ENABLED=false        # Browser automation (resource intensive)
MCP_EVERYTHING_ENABLED=true         # Test server with all features
```

#### 5. Protocol Configuration

```bash
# MCP Protocol Version (used by services that support it)
MCP_PROTOCOL_VERSION=2025-06-18

# Note: Some services only support specific versions:
# - mcp-memory: 2024-11-05
# - mcp-sequentialthinking: 2024-11-05
# - mcp-fetch, mcp-filesystem, mcp-time: 2025-03-26
# - Others: 2025-06-18
```

##### Available MCP Services

| Service | Description | Protocol Version | Container Port |
|---------|-------------|------------------|----------------|
| mcp-fetch | Web content fetching (stdio wrapper) | 2025-03-26 | 3000 |
| mcp-fetchs | Native Python fetch implementation | 2025-06-18 | 3000 |
| mcp-filesystem | File system access (sandboxed) | 2025-03-26 | 3000 |
| mcp-memory | Persistent memory/knowledge graph | 2024-11-05 | 3000 |
| mcp-sequentialthinking | Structured problem solving | 2024-11-05 | 3000 |
| mcp-time | Time and timezone operations | 2025-03-26 | 3000 |
| mcp-tmux | Terminal multiplexer integration | 2025-06-18 | 3000 |
| mcp-playwright | Browser automation | 2025-06-18 | 3000 |
| mcp-everything | Test server with all features | 2025-06-18 | 3000 |

All services use `mcp-streamablehttp-proxy` to wrap official MCP stdio servers, exposing them via HTTP on port 3000.

##### Gateway Extensions Beyond MCP Protocol

The gateway adds several features not specified in the MCP protocol:

- **RFC 7592 Client Management**: Complete client lifecycle management (GET/PUT/DELETE operations)
- **GitHub OAuth Integration**: User authentication through GitHub as Identity Provider
- **Dynamic Service Configuration**: Enable/disable services via environment variables
- **Bearer Token Authentication**: JWT-based API access with user identity claims
- **Automatic HTTPS**: Let's Encrypt certificates for all subdomains
- **Session Persistence**: Redis-backed state management for OAuth flows

#### 6. Test Configuration

```bash
# Enable/disable tests for specific services
MCP_FETCH_TESTS_ENABLED=false
MCP_FETCHS_TESTS_ENABLED=false
MCP_FILESYSTEM_TESTS_ENABLED=false
MCP_MEMORY_TESTS_ENABLED=false
MCP_PLAYWRIGHT_TESTS_ENABLED=false
MCP_SEQUENTIALTHINKING_TESTS_ENABLED=false
MCP_TIME_TESTS_ENABLED=false
MCP_TMUX_TESTS_ENABLED=false
MCP_EVERYTHING_TESTS_ENABLED=false

# Test parameters
TEST_HTTP_TIMEOUT=30.0
TEST_MAX_RETRIES=3
TEST_RETRY_DELAY=1.0
```

### Managing Services

#### Check Which Services Are Enabled

When you run `just up`, the system will show which services are being started:

```bash
just up
# Output:
# Generated docker-compose.includes.yml
# ✅ mcp-fetch is ENABLED
# ✅ mcp-fetchs is ENABLED
# ❌ mcp-playwright is DISABLED
# ... etc
```

#### Disable Unnecessary Services

To improve performance and reduce resource usage, disable services you don't need:

```bash
# Example: Minimal setup with just fetch and filesystem
MCP_FETCH_ENABLED=true
MCP_FETCHS_ENABLED=false
MCP_FILESYSTEM_ENABLED=true
MCP_MEMORY_ENABLED=false
MCP_PLAYWRIGHT_ENABLED=false
MCP_SEQUENTIALTHINKING_ENABLED=false
MCP_TIME_ENABLED=false
MCP_TMUX_ENABLED=false
MCP_EVERYTHING_ENABLED=false
```

#### Apply Configuration Changes

After modifying `.env`:

```bash
# Regenerate service configuration
just down
just up
```

### Environment File Best Practices

1. **Never commit `.env`** - It contains secrets!
2. **Use strong passwords** - Especially for REDIS_PASSWORD
3. **Backup your `.env`** - Keep a secure copy of your configuration
4. **Validate settings** - Use `just check-health` after changes
5. **Start minimal** - Enable only services you need

## 📖 Usage

### Service Management

```bash
# Start all services
just up

# Stop all services  
just down

# Rebuild specific service
just rebuild auth
just rebuild mcp-fetch
just rebuild mcp-memory

# View logs
just logs              # All services
just logs auth         # Specific service
just logs -f traefik   # Follow mode
```

### OAuth Token Management

#### Generate Required Secrets (Gateway Operation)

```bash
# Generate all required secrets at once
just generate-all-secrets

# Or generate individually:
just generate-jwt-secret      # JWT signing secret
just generate-rsa-keys        # RSA private key  
just generate-redis-password  # Redis password
```

#### Generate Test Tokens (Optional)

The gateway uses **GitHub Device Flow** ([RFC 8628](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow)) for test token generation:

```bash
# Generate test OAuth tokens using GitHub Device Flow
just generate-github-token
# This will:
# 1. Request a device code from GitHub
# 2. Display: "Visit https://github.com/login/device and enter: XXXX-XXXX"
# 3. Poll GitHub until you authorize
# 4. Store the GitHub PAT as GITHUB_PAT in .env

# Generate MCP client token (for mcp-streamablehttp-client)
just mcp-client-token
# Uses device flow for browserless authentication

# View OAuth registrations and tokens
just oauth-show-all
just oauth-list-registrations
just oauth-list-tokens

# Cleanup expired tokens
just oauth-purge-expired
```

#### Two OAuth Flows: Device Flow vs Browser Flow

**1. GitHub Device Flow (RFC 8628)** - Used for:
- **Gateway self-authentication**: `just generate-github-token`
- **MCP client tokens**: `just mcp-client-token`
- **When**: No browser available or command-line scenarios
- **Process**: Shows code → User enters at github.com/login/device → Polls for completion

**2. Standard OAuth Flow** - Used for:
- **End-user authentication**: When users access MCP services
- **When**: Browser-based access (Claude.ai, web clients)
- **Process**: Redirect to GitHub → User logs in → Redirect back with auth code

### Testing

```bash
# Run all tests
just test

# Run specific test file
just test tests/test_oauth_flow.py

# Run with verbose output
just test -v

# Run with coverage analysis
just test-sidecar-coverage

# Run specific test suites
just test-oauth-flow
just test-mcp-protocol
just test-claude-integration
```

### Health Monitoring

```bash
# Check all services health
just check-health

# Quick health check
just health-quick

# Check SSL certificates
just check-ssl
```

### OAuth Data Management

```bash
# Backup OAuth data
just oauth-backup

# List backups
just oauth-backup-list

# Restore from latest backup
just oauth-restore

# View backup contents
just oauth-backup-view

# Cleanup test registrations
just test-cleanup-show  # Preview what would be deleted
just test-cleanup       # Actually delete test data
```

## 🧪 Testing the Gateway

### 1. Verify Services Are Running

```bash
just check-health
```

### 2. Test OAuth Flow

```bash
# Run OAuth flow tests
just test tests/test_oauth_flow.py -v

# Test with a real browser
# Visit: https://auth.your-domain.com/.well-known/oauth-authorization-server
```

### 3. Test MCP Integration

```bash
# Test MCP protocol compliance
just test tests/test_mcp_protocol.py -v

# Test specific MCP service
just test tests/test_mcp_fetch_integration.py -v
```

### 4. Generate Coverage Report

```bash
# Run tests with production coverage
just test-sidecar-coverage

# View HTML coverage report
open htmlcov/index.html
```

## 🔍 Monitoring and Troubleshooting

### View Logs

```bash
# All services
just logs

# Specific service with follow
just logs -f auth
just logs -f traefik

# Analyze OAuth flows
just analyze-oauth-logs
```

### Common Issues

#### Services Not Starting

```bash
# Check Docker status
docker compose ps

# Ensure network exists
just network-create

# Check for port conflicts
sudo netstat -tlnp | grep -E ':80|:443'
```

#### SSL Certificate Issues

```bash
# Check certificate status
just check-ssl

# View Traefik logs for ACME errors
just logs traefik | grep -i acme
```

#### Authentication Failures

```bash
# Verify GitHub OAuth credentials
just generate-github-token

# Check Redis connectivity
just exec redis redis-cli -a $REDIS_PASSWORD ping

# Validate tokens
just validate-tokens
```

#### MCP Service Issues

```bash
# Check specific service health
docker inspect mcp-oauth-gateway-mcp-fetch-1 --format='{{json .State.Health}}'

# Test MCP endpoint directly
curl -X POST https://everything.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer $GATEWAY_OAUTH_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
```

## 📚 Additional Information

### Documentation

📖 **[View the full documentation online](https://atrawog.github.io/mcp-oauth-gateway)**

The documentation is also available locally in Jupyter Book format:

```bash
# Build documentation locally
just docs-build

# Open local build in browser
open docs/_build/html/index.html
```

### Development Guidelines

All development must follow the sacred commandments in `CLAUDE.md`:
- **No mocking** - Test against real services only
- **Use just commands** - Never run commands directly
- **Configuration through .env** - No hardcoded values
- **Real deployments only** - No localhost testing

### Project Structure

```
mcp-oauth-gateway/
├── auth/                    # OAuth authorization server
├── mcp-*/                   # Individual MCP services
├── traefik/                 # Reverse proxy configuration
├── tests/                   # Integration tests
├── scripts/                 # Utility scripts
├── docs/                    # Jupyter Book documentation
├── docker-compose.yml       # Main compose file
├── docker-compose.*.yml     # Additional compose configs
├── justfile                 # Command definitions
├── pixi.toml               # Package management
├── .env.example            # Example configuration
└── CLAUDE.md               # Development commandments
```

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please:
1. Follow the sacred commandments in CLAUDE.md
2. Test with real services (no mocking)
3. Use `just` for all commands
4. Update documentation as needed

For questions or issues, please open a GitHub issue.