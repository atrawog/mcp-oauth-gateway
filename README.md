# MCP OAuth Gateway

An OAuth 2.1 Authorization Server that adds authentication to any MCP (Model Context Protocol) server without code modification. The gateway acts as an OAuth Authorization Server while using GitHub as the Identity Provider (IdP) for user authentication.

📖 **[View Documentation](https://atrawog.github.io/mcp-oauth-gateway)** | 🔧 **[Installation Guide](https://atrawog.github.io/mcp-oauth-gateway/quick-install.html)** | 🏗️ **[Architecture Overview](https://atrawog.github.io/mcp-oauth-gateway/architecture/index.html)**

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
│ • Priority-based routing rules (OAuth > Verify > MCP > Catch-all)                   │
│ • ForwardAuth middleware for MCP endpoints → Auth Service /verify                   │
│ • Request routing based on subdomain and path:                                      │
│   - auth.domain.com/* → Auth Service (no auth required)                             │
│   - *.domain.com/.well-known/* → Auth Service (OAuth discovery)                     │
│   - *.domain.com/mcp → MCP Services (auth required via ForwardAuth)                 │
│ • Docker service discovery via labels                                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
                    │                                              │
                    │ OAuth/Auth Requests                          │ MCP Requests
                    │ (unauthenticated)                            │ (authenticated)
                    ↓                                              ↓
┌───────────────────────────────────────────┐    ┌─────────────────────────────────────┐
│           AUTH SERVICE                    │    │         MCP SERVICES                │
│   (Layer 2: OAuth Authorization Server)   │    │    (Layer 3: Protocol Handlers)     │
├───────────────────────────────────────────┤    ├─────────────────────────────────────┤
│ Container: auth:8000                      │    │ Containers:                         │
│ Package: mcp-oauth-dynamicclient          │    │ • mcp-echo-stateful:3000            │
│                                           │    │ • mcp-echo-stateless:3000           │
│                                           │    │ • mcp-fetch:3000                    │
│ OAuth Endpoints:                          │    │ • mcp-memory:3000                   │
│ • POST /register (RFC 7591)               │    │ • mcp-time:3000                     │
│ • GET /authorize + /callback              │    │ • ... (dynamically enabled)         │
│ • POST /token                             │    │                                     │
│ • GET /.well-known/* (RFC 8414)           │    │ Architecture:                       │
│ • POST /revoke, /introspect               │    │ • mcp-streamablehttp-proxy wrapper  │
│                                           │    │ • Spawns official MCP stdio servers │
│ Management Endpoints (RFC 7592):          │    │ • Bridges stdio ↔ HTTP/SSE          │
│ • GET/PUT/DELETE /register/{client_id}    │    │ • No OAuth knowledge                │
│                                           │    │ • Receives user identity in headers │
│ Internal Endpoints:                       │    │                                     │
│ • GET/POST /verify (ForwardAuth)          │    │ Protocol Endpoints:                 │
│                                           │    │ • POST /mcp (JSON-RPC over HTTP)    │
│ External Integration:                     │←---│ • GET /mcp (SSE for async messages) │
│ • GitHub OAuth (user authentication)      │    │ • Health checks on /health          │
└───────────────────────────────────────────┘    └─────────────────────────────────────┘
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
│ • oauth:client:{client_id} → OAuth client registrations (90 days / eternal)         │
│ • oauth:state:{state} → Authorization flow state (5 minutes)                        │
│ • oauth:code:{code} → Authorization codes + user info (1 year)                      │
│ • oauth:token:{jti} → JWT token tracking for revocation (30 days)                   │
│ • oauth:refresh:{token} → Refresh token data (1 year)                               │
│ • oauth:user_tokens:{username} → User's active tokens index                         │
│ • redis:session:{id}:state → MCP session state (managed by proxy)                   │
│ • redis:session:{id}:messages → MCP message queues                                  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

NETWORK TOPOLOGY:
• All services connected via 'public' Docker network
• Internal service communication only (except Traefik ingress)
• Redis exposed on localhost:6379 for debugging only
• Each MCP service runs in isolated container with no shared state

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
- **registration_access_token**: Bearer token for client management only (RFC 7592)
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
- Provides HTTP transport required for web clients
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

The gateway implements a **multi-layered OAuth 2.1 authorization system** that integrates **client credential authentication** with **GitHub OAuth identity federation**:

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

The gateway implementation combines client credential authentication with GitHub user authentication:

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
║  │   "redirect_uris": ["https://example.com/callback"],                        │  ║
║  │   "client_name": "My MCP Client"                                            │  ║
║  │ }                                                                           │  ║
║  │                                                                             │  ║
║  │ Response:                                                                   │  ║
║  │ • client_id: "client_abc123..."          ← OAuth client credentials         │  ║
║  │ • client_secret: "secret_xyz789..."      ← Used at /token endpoint          │  ║
║  │ • registration_access_token: "reg_tok..."← ONLY for client management       │  ║
║  │ • registration_client_uri: "https://auth.../register/client_abc123"         │  ║
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
║  │ Note: This token is ONLY for managing the client registration,              │  ║
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
║  │ GET /authorize?client_id=client_abc123&redirect_uri=...&code_challenge=...  │  ║
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
║  │ • client_id=client_abc123          ← Authenticates the OAuth client         │  ║
║  │ • client_secret=secret_xyz789      ← Proves client identity                 │  ║
║  │ • code=auth_code_from_step_2       ← Contains GitHub user info              │  ║
║  │ • code_verifier=pkce_verifier      ← PKCE verification                      │  ║
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
║  🛡️ STEP 4: RESOURCE ACCESS (Using the access token)                              ║
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
```

🔑 **ARCHITECTURAL PRINCIPLES:**

- `client_id` + `client_secret` establish OAuth client identity (e.g., Claude.ai application)
- GitHub OAuth provides user identity federation and authentication
- The resultant `access_token` JWT encapsulates both client and user identity claims
- `registration_access_token` is scoped exclusively to client lifecycle management operations

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

## 🚀 Try It Out - Public Test Servers

Before setting up your own gateway, you can test the OAuth flow and MCP integration using my publicly available test servers:

### Available Test Servers

- **Echo Stateless**: https://echo-stateless.atratest.org/mcp
  - Simple echo service without session state
  - Each request is independent
  - Perfect for testing basic OAuth flow and MCP protocol
  - [📖 View Echo Stateless Documentation](https://atrawog.github.io/mcp-oauth-gateway/packages/mcp-echo-streamablehttp-server-stateless.html)

- **Echo Stateful**: https://echo-stateful.atratest.org/mcp
  - Echo service with session state management
  - Includes `replayLastEcho` tool to test stateful operations
  - Demonstrates session persistence across requests
  - [📖 View Echo Stateful Documentation](https://atrawog.github.io/mcp-oauth-gateway/packages/mcp-echo-streamablehttp-server-stateful.html)

### How to Use

These servers are configured to accept **any GitHub user** for authentication:

1. **Make a request** to either test server endpoint
2. **Receive 401 Unauthorized** with OAuth discovery information
3. **Complete OAuth flow** using your GitHub account
4. **Access granted** - Use the bearer token for subsequent MCP requests

The test servers implement the full OAuth 2.1 + MCP 2025-06-18 integration:
- Dynamic client registration (RFC 7591)
- GitHub OAuth for user authentication
- PKCE protection for security
- StreamableHTTP transport for MCP protocol

These servers are ideal for:
- Testing MCP client implementations
- Understanding the OAuth flow
- Validating integration before deployment
- Educational purposes and demos

## 📋 Requirements

### System Requirements

- **Docker** and **Docker Compose** (required for all services)
- **[pixi](https://pixi.sh/latest/)** - Modern Python package manager
- **[just](https://github.com/casey/just)** - Command runner (all commands go through just)
- **Python 3.11+** (managed automatically by pixi)

### Infrastructure Requirements

- **Public IP address and properly configured DNS** (MANDATORY)
  - All subdomains must resolve to your server:
    - `auth.your-domain.com` - OAuth authorization server
    - `service.your-domain.com` - Each MCP service subdomain
  - Ports 80 and 443 must be accessible from the internet


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

```bash
# 1. Copy the example configuration
cp .env.example .env

# 2. Generate required secrets
just generate-all-secrets    # Generates JWT secret, RSA keys, and Redis password

# 3. Edit .env with your configuration
nano .env
```

Edit your `.env` file with the required configuration:

1. **Domain Setup** (REQUIRED)
   ```bash
   BASE_DOMAIN=your-domain.com      # Your actual domain
   ACME_EMAIL=admin@your-domain.com # Email for Let's Encrypt
   ```

2. **GitHub OAuth App** (REQUIRED)
   ```bash
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   ```

3. **Access Control** (REQUIRED)
   ```bash
   # Option 1: Whitelist specific users
   ALLOWED_GITHUB_USERS=user1,user2,user3
   # Option 2: Allow any authenticated GitHub user
   ALLOWED_GITHUB_USERS=*
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

# Echo Diagnostic Services (Choose one or both)
MCP_ECHO_STATEFUL_ENABLED=true      # Echo with session state & replayLastEcho
MCP_ECHO_STATELESS_ENABLED=true     # Echo without state management
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
| mcp-echo-stateful | Diagnostic tools with session state & memory | 2025-06-18 | 3000 |
| mcp-echo-stateless | Diagnostic tools without state management | 2025-06-18 | 3000 |
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
MCP_ECHO_STATEFUL_TESTS_ENABLED=false
MCP_ECHO_STATELESS_TESTS_ENABLED=true

# Test parameters
TEST_HTTP_TIMEOUT=30.0
TEST_MAX_RETRIES=3
TEST_RETRY_DELAY=1.0
```
