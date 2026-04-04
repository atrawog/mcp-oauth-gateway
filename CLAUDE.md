# MCP OAuth Gateway — Development Guide

## Part I: Project Rules

### 0. Root Cause Analysis
Always apply five whys before fixing:
1. What failed? → What enabled it? → Why wasn't it prevented? → Why wasn't it caught? → How to prevent recurrence?
- Fix the system, not the symptom. Write tests that guard the fix.

### 1. No Mocks — Real Systems Only
- Test against actual running services (Docker containers)
- Real Redis, real HTTP, real auth flows
- No stubs, no fakes, no mock responses

### 2. The Tool Trinity
**All commands flow through these three tools. No exceptions.**
- `just` — task runner (all commands)
- `uv` — Python package manager
- `docker compose` — service orchestration

```bash
just test                  # run tests
just up                    # start services
just rebuild auth          # rebuild a service
just logs -f auth          # follow logs
```

justfile settings (first lines):
```justfile
set dotenv-load := true
set dotenv-required
set positional-arguments := true
set export := true
set quiet
```

### 3. Project Structure
```
project/
├── service-a/            # One service per directory
│   ├── Dockerfile
│   └── docker-compose.yml
├── package-name/
│   ├── src/package_name/ # Python src layout
│   └── pyproject.toml
├── tests/                # All tests here (never inside packages)
│   ├── conftest.py
│   └── test_*.py
├── scripts/              # Automation scripts (with __init__.py)
├── docs/                 # Jupyter Book documentation
├── logs/                 # Centralized logs
├── docker-compose.yml    # Master orchestration
├── justfile
├── pyproject.toml
├── uv.lock
├── .env                  # Secrets (gitignored)
└── .env.example          # Template (tracked)
```

### 4. Configuration
- All config via `.env` — no hardcoded values
- No defaults in code — explicit is required
- Validate at startup — fail fast

### 5. Docker Compose
- `docker compose` (not `docker-compose`)
- Health checks required on every service
- Named networks via external `public` network
- SWAG is the sole reverse proxy

```yaml
include:
  - swag/docker-compose.yml
  - serviceA/docker-compose.yml
networks:
  public:
    external: true
```

### 6. Testing
- pytest only, in `./tests/`
- Real services — no mocks
- `conftest.py` for fixtures
- 85%+ coverage target

### 7. Health Checks
No `sleep` commands — use protocol-level health checks:
```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d \"{\\\"jsonrpc\\\":\\\"2.0\\\",\\\"method\\\":\\\"initialize\\\",\\\"params\\\":{\\\"protocolVersion\\\":\\\"${MCP_PROTOCOL_VERSION:-2025-06-18}\\\",\\\"capabilities\\\":{},\\\"clientInfo\\\":{\\\"name\\\":\\\"healthcheck\\\",\\\"version\\\":\\\"1.0\\\"}},\\\"id\\\":1}\" \
    | grep -q \"\\\"protocolVersion\\\":\\\"${MCP_PROTOCOL_VERSION:-2025-06-18}\\\"\""]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

### 8. Logging
- All logs to `./logs/`
- Structured logging with context on every line

### 9. Documentation
- Jupyter Book in `./docs/`
- MyST Markdown format

---

## Part II: MCP OAuth Gateway

### Quick Command Reference

```bash
# Service management
just up               # Start all services
just down             # Stop all services
just rebuild [svc]    # Rebuild and restart service(s)
just logs -f [svc]    # Follow logs for a service
just status           # Show service health summary
just check-health     # Detailed health check all services

# Testing
just test             # Run full test suite
just test -k auth     # Run auth tests only
just test-parallel    # Run tests in parallel
just ensure-services-ready  # Pre-flight check before tests

# Secrets / setup
just generate-jwt-secret    # Generate GATEWAY_JWT_SECRET
just generate-rsa-keys      # Generate JWT_PRIVATE_KEY_B64 (RS256)
just generate-redis-password
just generate-all-secrets   # Generate all secrets at once
just generate-github-token  # GitHub Device Flow for GATEWAY tokens
just mcp-client-token       # Generate MCP_CLIENT_ACCESS_TOKEN

# OAuth management
just oauth-stats                        # Redis token/client counts
just oauth-list-registrations           # List all client registrations
just oauth-delete-registration <id>     # Delete a client registration
just oauth-purge-expired                # Remove expired clients/tokens

# Submodules
just submodule-init   # Init and update all git submodules

# PyPI packages
just pypi-build [pkg]    # Build wheel for package (or all)
just pypi-publish [pkg]  # Full build+test+upload to PyPI
```

### System Architecture — Three Layers

```
┌─────────────────────────────────────────────────────────────┐
│      SWAG - Layer 1 (nginx Reverse Proxy)                   │
│  • Routes OAuth paths → Auth Service via proxy-confs        │
│  • Routes MCP paths → MCP Services (after auth check)       │
│  • Enforces authentication via auth_request directive        │
│  • Provides HTTPS with Let's Encrypt                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Auth Service - Layer 2 (OAuth Oracle)                      │
│  • Handles all OAuth endpoints (/register, /token, etc.)    │
│  • Validates tokens via /verify for auth_request            │
│  • Integrates with GitHub OAuth for user auth               │
│  • Uses mcp-oauth-dynamicclient for RFC compliance          │
│  • Knows nothing about MCP protocols                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  MCP Services - Layer 3 (Protocol Servants)                 │
│  • Run mcp-streamablehttp-proxy wrapping official servers   │
│  • Bridge stdio MCP servers to HTTP /mcp endpoints          │
│  • Receive pre-authenticated requests only                  │
│  • Know nothing of OAuth                                    │
└─────────────────────────────────────────────────────────────┘
```

**Critical rule**: Each layer knows only its concern. Never mix them.

### MCP Service Implementation Patterns

#### Pattern 1: Proxy Pattern (wraps official stdio servers)
Uses `mcp-streamablehttp-proxy` to bridge stdio ↔ HTTP.

Services: **mcp-fetch**, **mcp-filesystem**, **mcp-memory**, **mcp-time**, **mcp-everything**, **mcp-playwright**, **mcp-sequentialthinking**, **mcp-tmux**

#### Pattern 2: Native StreamableHTTP (direct HTTP implementation)
FastAPI + Uvicorn with direct StreamableHTTP protocol support. No stdio bridge.

Services: **mcp-fetchs**, **mcp-echo-stateful**, **mcp-echo-stateless**, **mcp-axon**, **mcp-synapse**, **mcp-unraid**

Both patterns expose `/mcp` endpoint, use Bearer token auth via SWAG, and require health checks.

### Dual Authentication Realms

**Never confuse these two realms:**

| Realm | Purpose | Entry Point | Token Type |
|-------|---------|-------------|------------|
| MCP Gateway Client | MCP clients access gateway | POST /register (public) | `registration_access_token` (reg-xxx) |
| User Auth | Human users authenticate | GET /authorize → GitHub | JWT access token |

- `registration_access_token` ≠ OAuth `access_token`
- RFC 7592 Bearer ≠ OAuth Bearer
- Registration tokens: `secrets.compare_digest` comparison
- OAuth tokens: JWT signature validation

### Sacred Env Vars

```bash
# GitHub OAuth
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...

# JWT
GATEWAY_JWT_SECRET=...        # HS256 signing (just generate-jwt-secret)
JWT_PRIVATE_KEY_B64=...       # RS256 RSA key (just generate-rsa-keys)
JWT_ALGORITHM=RS256

# OAuth tokens (gateway's own credentials)
GATEWAY_OAUTH_ACCESS_TOKEN=...
GATEWAY_OAUTH_REFRESH_TOKEN=...
GATEWAY_OAUTH_CLIENT_ID=...
GATEWAY_OAUTH_CLIENT_SECRET=...

# MCP Client tokens (external clients only — separate realm!)
MCP_CLIENT_ACCESS_TOKEN=...   # just mcp-client-token

# Access control
ALLOWED_GITHUB_USERS=user1,user2  # or '*' for any GitHub user

# Protocol
MCP_PROTOCOL_VERSION=2025-06-18  # Services may use different versions

# Client lifetime
CLIENT_LIFETIME=7776000  # 90 days; 0 = never expires
```

### OAuth Endpoints

**RFC 7591 (public):**
- `POST /register` — Dynamic client registration (no auth, returns `registration_access_token`)
- Returns HTTP 201 on success, 400 on error

**Core OAuth:**
- `GET /authorize` — Initiates GitHub OAuth (validates client_id, PKCE state)
- `POST /token` — Exchanges auth code for JWT (PKCE S256 required)
- `GET /callback` — GitHub OAuth return

**RFC 7592 (requires Bearer `registration_access_token`):**
- `GET /register/{client_id}` — View registration
- `PUT /register/{client_id}` — Update metadata
- `DELETE /register/{client_id}` — Delete registration

**Discovery & extensions:**
- `GET /.well-known/oauth-authorization-server` — Server metadata (RFC 8414, must be accessible on all subdomains)
- `GET /jwks` — RS256 public keys
- `POST /revoke` — RFC 7009 token revocation
- `POST /introspect` — RFC 7662 token introspection
- `GET/POST /verify` — SWAG auth_request validation

**Error handling:**
- Authorization endpoint: no redirect on invalid `client_id` (show error page)
- Token endpoint: 401 with `invalid_client`
- Always include `WWW-Authenticate: Bearer` on 401

### Client ID Metadata Document Support (MCP 2025-11-25)

MCP clients (Claude Code, native apps) may use an HTTPS URL as `client_id` — no pre-registration needed.

- **Auto-fetch**: Gateway fetches `{client_id}/.well-known/oauth-client-id-metadata` at `/authorize` and `/token`
- **Public clients**: `token_endpoint_auth_method: none` — no `client_secret` required
- **PKCE required**: S256 mandatory for public clients (OAuth 2.1 §4.1.1)
- **Loopback port flexibility**: `http://127.0.0.1` and `http://localhost` accept any port (RFC 8252 §7.3)
- **Refresh token rotation**: New refresh token issued on every use (OAuth 2.1 §4.3.1)
- **Auth code TTL**: 10 minutes (not 1 year)

Metadata document format:
```json
{
  "client_id": "https://your-app.example.com",
  "redirect_uris": ["http://127.0.0.1/callback"],
  "token_endpoint_auth_method": "none",
  "grant_types": ["authorization_code"],
  "response_types": ["code"],
  "client_name": "My MCP Client"
}
```

### Claude.ai Connection Flow

1. Attempts `/mcp` → receives 401 with `WWW-Authenticate: Bearer`
2. Fetches `/.well-known/oauth-authorization-server`
3. `POST /register` (RFC 7591) → receives `client_id` + credentials
4. Generates S256 PKCE challenge
5. User authenticates via GitHub OAuth
6. Auth code → JWT exchange at `/token`
7. StreamableHTTP requests with `Authorization: Bearer <jwt>` + `Mcp-Session-Id`

### SWAG nginx Routing

**Critical**: OAuth routes must NOT have `auth_request` — this causes auth loops.

```nginx
# auth.subdomain.conf — OAuth service (NO auth_request here!)
server {
    listen 443 ssl;
    server_name auth.*;

    location ~* ^/(register|authorize|token|callback|\.well-known)(/|$) {
        proxy_pass http://auth:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /verify {
        proxy_pass http://auth:8000/verify;
        proxy_pass_request_body off;
        proxy_set_header Content-Length "";
        proxy_set_header X-Original-URI $request_uri;
    }
}

# mcp-fetch.subdomain.conf — MCP service (auth_request enforced)
server {
    listen 443 ssl;
    server_name mcp-fetch.*;

    auth_request /auth-verify;
    auth_request_set $auth_user_id $upstream_http_x_user_id;
    auth_request_set $auth_user_name $upstream_http_x_user_name;
    auth_request_set $auth_token $upstream_http_x_auth_token;

    location = /auth-verify {
        internal;
        proxy_pass http://auth:8000/verify;
        proxy_pass_request_body off;
        proxy_set_header Content-Length "";
        proxy_set_header X-Original-URI $request_uri;
        proxy_set_header Authorization $http_authorization;
    }

    location /mcp {
        proxy_pass http://mcp-fetch:3000/mcp;
        proxy_set_header X-User-Id $auth_user_id;
        proxy_set_header X-User-Name $auth_user_name;
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }

    error_page 401 = @error401;
    location @error401 {
        add_header WWW-Authenticate 'Bearer realm="MCP Gateway"' always;
        return 401;
    }
}
```

### Redis Key Patterns

```
oauth:state:{state}          # 5 min TTL — CSRF protection
oauth:code:{code}            # 10 min TTL — Authorization codes
oauth:token:{jti}            # 30 days TTL — JWT access tokens
oauth:refresh:{token}        # 1 year TTL — Refresh tokens
oauth:client:{client_id}     # Client lifetime — includes registration_access_token
oauth:user_tokens:{username} # No expiry — index of user's tokens
```

`registration_access_token` is stored inside `oauth:client:{client_id}`, not as a separate key.

### MCP Protocol Requirements

**Initialization** (required before any other operations):
```json
POST /mcp
{
  "jsonrpc": "2.0", "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {"name": "client", "version": "1.0"}
  },
  "id": 1
}
```
Response includes `Mcp-Session-Id` header — include in all subsequent requests.

**JSON-RPC rules:**
- Requests: string/integer `id`, unique per session
- Responses: same `id`, either `result` or `error` (never both)
- Notifications: no `id`
- Error codes: integers only

**Required headers for POST /mcp:**
- `Content-Type: application/json`
- `MCP-Protocol-Version: ${MCP_PROTOCOL_VERSION}`
- `Mcp-Session-Id: <id>` (if server provided one)
- `Authorization: Bearer <token>`

**HTTP status codes:**
- 200: successful response
- 400: invalid request
- 401: unauthorized (include `WWW-Authenticate`)
- 403: forbidden
- 404: session not found

### Token Generation

```bash
# Gateway setup (automated)
just generate-jwt-secret      # Creates GATEWAY_JWT_SECRET
just generate-rsa-keys        # Creates JWT_PRIVATE_KEY_B64

# Gateway OAuth tokens (needs manual browser step first run)
just generate-github-token

# MCP client token (separate realm — external clients only)
just mcp-client-token         # Creates MCP_CLIENT_ACCESS_TOKEN
```

### Integration Checklist

- [ ] SWAG, Auth Service, MCP Services in separate containers
- [ ] OAuth endpoints have NO `auth_request` (prevents auth loops)
- [ ] MCP endpoints all protected by `auth_request`
- [ ] OAuth 2.1 + PKCE S256 enforced (plain method rejected)
- [ ] RFC 7591 public registration returns `registration_access_token`
- [ ] RFC 7592 management requires `registration_access_token` Bearer (not OAuth token)
- [ ] GitHub OAuth configured with correct redirect URIs
- [ ] All services have Docker health checks using MCP initialize handshake
- [ ] `/.well-known/oauth-authorization-server` accessible on all subdomains
- [ ] Redis key patterns match schema above
- [ ] No hardcoded secrets — all from `.env`
- [ ] RS256 keys generated for JWT signing
- [ ] `CLIENT_LIFETIME=0` for non-expiring client registrations (if desired)
