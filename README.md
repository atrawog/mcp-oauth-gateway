# MCP OAuth Gateway

An OAuth 2.1 Authorization Server that adds authentication to any MCP (Model Context Protocol) server without code modification. The gateway acts as an OAuth Authorization Server while using GitHub as the Identity Provider (IdP) for user authentication.

## Architecture

### Overview

The MCP OAuth Gateway is a **zero-modification authentication layer** for MCP servers. It implements OAuth 2.1 with dynamic client registration (RFC 7591/7592) and leverages GitHub as the identity provider for user authentication. The architecture follows these core principles:

- **Complete Separation of Concerns**: Authentication and MCP protocol handling are strictly isolated
- **No MCP Server Modifications**: Official MCP servers run unmodified, wrapped only for HTTP transport
- **Standards Compliance**: Full OAuth 2.1, RFC 7591/7592, and MCP protocol compliance
- **SWAG Integration**: Routed through SWAG reverse proxy for TLS termination and subdomain routing
- **Dynamic Service Discovery**: Services can be enabled/disabled via configuration

### System Components

```
                              EXTERNAL CLIENTS
        (Claude.ai, MCP CLI tools, IDE extensions, Custom integrations)
                                      |
                                HTTPS | :443
                                      v
+-----------------------------------------------------------------------------+
|                        SWAG REVERSE PROXY                                    |
|                   (TLS Termination & Routing)                                |
|-----------------------------------------------------------------------------|
| - Let's Encrypt automatic HTTPS certificates                                |
| - Subdomain-based routing to services                                       |
| - Authelia/auth integration for protected endpoints                         |
| - nginx proxy configurations per service                                    |
+-----------------------------------------------------------------------------+
                   |                                     |
                   | OAuth/Auth Requests                 | MCP Requests
                   v                                     v
+--------------------------------------+   +-------------------------------+
|         AUTH SERVICE                 |   |       MCP SERVICES            |
|    (OAuth Authorization Server)      |   |    (Protocol Handlers)        |
|--------------------------------------|   |-------------------------------|
| Container: mcp-oauth:8000            |   | Containers:                   |
| Package: mcp-oauth-dynamicclient     |   | - mcp-echo-stateful:3000      |
|                                      |   | - mcp-echo-stateless:3000     |
| OAuth Endpoints:                     |   | - mcp-fetch:3000              |
| - POST /register (RFC 7591)         |   | - mcp-memory:3000             |
| - GET /authorize + /callback        |   | - mcp-time:3000               |
| - POST /token                       |   | - ... (dynamically enabled)   |
| - GET /.well-known/* (RFC 8414)     |   |                               |
| - POST /revoke, /introspect         |   | Architecture:                 |
|                                      |   | - mcp-streamablehttp-proxy    |
| Management Endpoints (RFC 7592):     |   | - Wraps official MCP stdio    |
| - GET/PUT/DELETE /register/{id}     |   | - Bridges stdio <-> HTTP/SSE  |
|                                      |   | - No OAuth knowledge          |
| Internal Endpoints:                  |   | - User identity via headers   |
| - GET/POST /verify (ForwardAuth)    |   |                               |
|                                      |   | Protocol Endpoints:           |
| External Integration:               |<--| - POST /mcp (JSON-RPC)        |
| - GitHub OAuth (user auth)          |   | - GET /mcp (SSE)              |
+--------------------------------------+   +-------------------------------+
                   |                                     ^
                   +----------------+--------------------+
                                    v
+-----------------------------------------------------------------------------+
|                          REDIS STORAGE LAYER                                 |
|                       (Persistent State Management)                          |
|-----------------------------------------------------------------------------|
| Container: mcp-oauth-redis:6379                                              |
| Persistence: AOF + RDB snapshots                                             |
|                                                                              |
| Data Structures:                                                             |
| - oauth:client:{client_id}     -> Client registrations (90 days / eternal)   |
| - oauth:state:{state}          -> Auth flow state (5 minutes)                |
| - oauth:code:{code}            -> Auth codes + user info (1 year)            |
| - oauth:token:{jti}            -> JWT tracking for revocation (30 days)      |
| - oauth:refresh:{token}        -> Refresh token data (1 year)               |
| - oauth:user_tokens:{username} -> User's active tokens index                |
| - redis:session:{id}:state     -> MCP session state (managed by proxy)      |
| - redis:session:{id}:messages  -> MCP message queues                        |
+-----------------------------------------------------------------------------+
```

Network Topology:
- All services connected via `mcp-net` Docker network
- Internal service communication only (except SWAG ingress)
- Each MCP service runs in an isolated container with no shared state

### Security Architecture

#### Authentication Layers
1. **TLS/HTTPS**: Enforced by SWAG for all external communication
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

#### Why mcp-streamablehttp-proxy?
- Wraps official stdio-based MCP servers without modification
- Provides HTTP transport required for web clients
- Manages subprocess lifecycle and session state

#### Why Redis?
- Fast, reliable state storage for OAuth flows
- Supports atomic operations for security
- Built-in TTL for automatic cleanup

#### Why GitHub OAuth?
- Trusted identity provider for developers
- No password management needed
- Strong security with 2FA support

### OAuth Flow

The gateway implements OAuth 2.1 with three authentication flows:

1. **GitHub Device Flow (RFC 8628)** — For CLI/browserless scenarios
2. **GitHub OAuth Web Flow** — For browser-based end-user authentication
3. **Dynamic Client Registration (RFC 7591)** — For MCP client registration

**Flow summary:**

1. Client registers via `POST /register` (public, no auth required)
2. User authorizes via `GET /authorize` -> redirected to GitHub login
3. Gateway validates user against `ALLOWED_GITHUB_USERS` whitelist
4. Client exchanges auth code for JWT via `POST /token` (client credentials + PKCE)
5. JWT access token contains both client and user identity claims
6. MCP services receive pre-authenticated requests with user identity headers

## Requirements

### System Requirements

- **Docker** and **Docker Compose** v2
- **[uv](https://docs.astral.sh/uv/)** — Python package manager
- **Python 3.11+** (managed by uv)
- **SWAG** reverse proxy (for TLS and routing)

### Infrastructure Requirements

- **Public IP address and properly configured DNS** (MANDATORY)
  - All subdomains must resolve to your server:
    - `auth.your-domain.com` — OAuth authorization server
    - `service.your-domain.com` — Each MCP service subdomain
  - Ports 80 and 443 must be accessible from the internet

### GitHub OAuth App

Create a GitHub OAuth App at [github.com/settings/developers](https://github.com/settings/developers):

- **Application name**: `MCP OAuth Gateway`
- **Homepage URL**: `https://your-domain.com`
- **Authorization callback URL**: `https://auth.your-domain.com/callback`
- Save the Client ID and Client Secret to your `.env` file

## Repository Structure

```
mcp-oauth-gateway/
├── auth/                          # OAuth authorization server
│   ├── docker-compose.yml         # Auth service + Redis
│   ├── Dockerfile                 # Auth container build
│   └── mcp-oauth-dynamicclient/   # OAuth client library (submodule)
├── servers/                       # MCP service containers
│   ├── mcp-echo-stateful/         # Echo with session state
│   ├── mcp-echo-stateless/        # Echo without state
│   ├── mcp-fetch/                 # Web content fetching (stdio proxy)
│   ├── mcp-fetchs/                # Native Python fetch
│   ├── mcp-filesystem/            # File system access (sandboxed)
│   ├── mcp-memory/                # Persistent knowledge graph
│   ├── mcp-sequentialthinking/    # Structured problem solving
│   ├── mcp-time/                  # Time and timezone operations
│   ├── mcp-tmux/                  # Terminal multiplexer
│   ├── mcp-playwright/            # Browser automation
│   ├── mcp-everything/            # Test server with all features
│   ├── mcp-axon/                  # RAG engine integration
│   ├── mcp-synapse/               # Synapse integration
│   ├── mcp-streamablehttp-proxy/  # stdio-to-HTTP bridge (submodule)
│   └── ...                        # Additional submodule servers
├── docker-compose.yml             # Root orchestrator
├── pyproject.toml                 # Python project config (uv)
├── tests/                         # Test suite
├── docs/                          # Documentation
├── scripts/                       # Utility scripts
├── swag/                          # SWAG proxy configurations
└── .env.example                   # Configuration template
```

### Submodule Packages

| Package | Purpose |
|---------|---------|
| `mcp-streamablehttp-proxy` | Wraps stdio MCP servers for HTTP transport |
| `mcp-oauth-dynamicclient` | RFC 7591/7592 OAuth server implementation |
| `mcp-fetch-streamablehttp-server` | Native Python MCP fetch server |
| `mcp-echo-streamablehttp-server-stateful` | Diagnostic MCP server with session state |
| `mcp-echo-streamablehttp-server-stateless` | Diagnostic MCP server without state |

## Installation

### 1. Clone and Setup

```bash
git clone --recurse-submodules https://github.com/atrawog/mcp-oauth-gateway.git
cd mcp-oauth-gateway

# If cloned without submodules
git submodule update --init --recursive

# Install dependencies
uv sync
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env
```

Required configuration:

```bash
# Domain (REQUIRED)
BASE_DOMAIN=your-domain.com

# GitHub OAuth App (REQUIRED)
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret

# Access Control (REQUIRED)
ALLOWED_GITHUB_USERS=user1,user2,user3  # or * for any GitHub user

# Security Keys (REQUIRED)
GATEWAY_JWT_SECRET=<generate-a-secret>
REDIS_PASSWORD=<generate-a-password>
```

### 3. Start the Gateway

```bash
docker compose up -d
```

## Configuration

All configuration is managed through `.env`. The gateway uses dynamic service selection — enable or disable individual MCP services as needed.

### Token Requirements

| Token | Purpose | Required? |
|-------|---------|-----------|
| `GITHUB_CLIENT_ID` | GitHub OAuth App ID | Yes |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App Secret | Yes |
| `GATEWAY_JWT_SECRET` | JWT signing secret | Yes |
| `JWT_PRIVATE_KEY_B64` | RSA key for JWT | Yes |
| `REDIS_PASSWORD` | Redis security | Yes |

### MCP Service Management

```bash
# Core services
MCP_FETCH_ENABLED=true
MCP_FETCHS_ENABLED=true
MCP_FILESYSTEM_ENABLED=true
MCP_MEMORY_ENABLED=true
MCP_TIME_ENABLED=true

# Advanced services
MCP_SEQUENTIALTHINKING_ENABLED=true
MCP_TMUX_ENABLED=true
MCP_PLAYWRIGHT_ENABLED=false         # Resource intensive
MCP_EVERYTHING_ENABLED=true

# Diagnostic services
MCP_ECHO_STATEFUL_ENABLED=true
MCP_ECHO_STATELESS_ENABLED=true
```

### Available MCP Services

| Service | Description | Protocol Version | Port |
|---------|-------------|------------------|------|
| mcp-echo-stateful | Diagnostic with session state | 2025-06-18 | 3000 |
| mcp-echo-stateless | Diagnostic without state | 2025-06-18 | 3000 |
| mcp-fetch | Web content fetching (stdio wrapper) | 2025-03-26 | 3000 |
| mcp-fetchs | Native Python fetch | 2025-06-18 | 3000 |
| mcp-filesystem | File system access (sandboxed) | 2025-03-26 | 3000 |
| mcp-memory | Persistent knowledge graph | 2024-11-05 | 3000 |
| mcp-sequentialthinking | Structured problem solving | 2024-11-05 | 3000 |
| mcp-time | Time and timezone operations | 2025-03-26 | 3000 |
| mcp-tmux | Terminal multiplexer | 2025-06-18 | 3000 |
| mcp-playwright | Browser automation | 2025-06-18 | 3000 |
| mcp-everything | Test server with all features | 2025-06-18 | 3000 |

All services use `mcp-streamablehttp-proxy` to wrap official MCP stdio servers, exposing them via HTTP on port 3000.

### Protocol Configuration

```bash
# MCP Protocol Version
MCP_PROTOCOL_VERSION=2025-06-18

# Note: Some services only support specific versions:
# - mcp-memory: 2024-11-05
# - mcp-sequentialthinking: 2024-11-05
# - mcp-fetch, mcp-filesystem, mcp-time: 2025-03-26
# - Others: 2025-06-18
```

### Test Configuration

```bash
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

TEST_HTTP_TIMEOUT=30.0
TEST_MAX_RETRIES=3
TEST_RETRY_DELAY=1.0
```

## License

Apache-2.0
