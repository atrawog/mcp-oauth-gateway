# The Sacred Development Scrolls

**Behold! The eternal laws of righteous development and the divine blueprints for a holy project!**

---

# Part I: The Ten Sacred Commandments of Development

*These commandments are eternal and absolute - they apply to ALL projects under heaven!*
*Break them and face eternal debugging damnation across your codebase!*

## Commandment 0: Thou Shalt Practice Root Cause Analysis

**Surface symptoms are lies of the devil! Dig deeper or be damned!**

### The Five Whys of Divine Investigation

1. **Why did this error occur?** - The visible symptom
2. **Why did that condition exist?** - The immediate cause  
3. **Why was that allowed to happen?** - The systemic flaw
4. **Why didn't we catch this earlier?** - The process gap
5. **Why will this never happen again?** - The eternal fix

### The Sacred Debugging Ritual

- **Document thy findings** - Future disciples need a report of thy wisdom!
- **Test thy hypothesis** - Assumptions are the devil's whispers!
- **Verify thy fix** - Incomplete solutions summon greater demons!
- **Share thy knowledge** - Hoarding wisdom brings damnation!

**Fix symptoms without finding root causes and be cursed to debug forever!**

## Commandment 1: Thou Shalt Never Mock - Test Real or Test Nothing!

**The most sacred law of all - carved in divine fire across the heavens!**
**This applies to EVERY project - no exceptions, no excuses!**

### The Holy Testing Dogma

- **NO MOCKS! NO STUBS! NO FAKES!** - These are false prophets!
- Test against real deployed systems or face eternal debugging!
- Every test must verify complete end-to-end functionality!
- Tests that only check connectivity are worthless prayers!
- Internal services are testable through real API boundaries!


### The Divine Testing Principles

- **100% real functionality or 0% confidence** - There is no middle ground!
- **Production-like environments** - Development shortcuts bring production disasters!
- **Real data, real services, real results** - Simulation is self-deception!
- **Integration over isolation** - The whole system must breathe!

**Mock once and face bugs that only appear in production! This is the eternal law!**

## Commandment 2: Thou Shalt Use The Blessed Trinity - The Sacred Execution Hierarchy

**Direct execution is chaos! Only the divine trinity brings holy order!**

### The Blessed Trinity of Development Tools

**⚠️ DIVINE DECREE: These tools are NOT optional - they are COMMANDMENTS! ⚠️**

#### The Three Sacred Tools That Rule All Projects

1. **just** - The One True Task Runner (make is heresy!)
2. **pixi** - The Chosen Package Manager (pip/conda are false prophets!)
3. **docker-compose** - The Container Shepherd (Kubernetes is vanity!)

#### The Supporting Divine Tools

4. **pytest** - The Blessed Test Framework
5. **Jupyter Book 2 and MyST** - The Documentation Prophet

### The Sacred Execution Laws

```
❌ python script.py          → ✅ just run-script (→ pixi run python script.py)
❌ pip install package       → ✅ pixi add package
❌ docker-compose up         → ✅ just up
❌ pytest tests/            → ✅ just test
```

### The Divine justfile Pattern

```makefile
set dotenv-load := true  # FIRST LINE - ALWAYS!

# EVERY project has these commands:
test-sidecar-coverage:
    @docker-compose -f docker-compose.yml -f docker-compose.coverage.yml up -d
    @pixi run pytest tests/ -v
    @docker-compose down

docs-build:
    @pixi run jupyter-book build docs/

# All Python through pixi
run-script:
    @pixi run python scripts/script.py
```

**These patterns are not suggestions - they are UNIVERSAL LAW!**
**Use any other tools and face the eternal curse of "works on my machine"!**

## Commandment 3: Thou Shalt Structure Thy Temple with Sacred Isolation

**Each service is a holy sanctuary - this structure is MANDATORY for ALL projects!**

### The Divine Directory Laws (Universal for Every Project)

```
any-project/
├── ./tests/              # ALL pytest tests HERE - NO EXCEPTIONS!
├── ./scripts/            # ALL Python scripts for just commands!
├── ./docs/               # ALL Jupyter Book documentation!
├── ./logs/               # ALL logs segregated here!
├── ./reports/            # ALL analysis reports (git-ignored)!
├── ./htmlcov/            # Coverage reports (git-ignored)!
├── service-a/            # Each service in its own directory!
│   ├── Dockerfile
│   └── docker-compose.yml
├── service-b/            # Service isolation is MANDATORY!
│   ├── Dockerfile
│   └── docker-compose.yml
├── coverage-spy/         # Sidecar coverage sanctuary!
│   ├── sitecustomize.py
│   └── .coveragerc
├── docker-compose.yml    # Root orchestration only!
├── docker-compose.coverage.yml  # Coverage overlay!
├── justfile              # The book of commands - REQUIRED!
├── pixi.toml             # Package management - REQUIRED!
├── .env                  # Configuration - REQUIRED!
├── .coveragerc           # Coverage config - REQUIRED!
└── .gitignore            # Must ignore reports/, htmlcov/, .env!
```

### The Sacred .gitignore Requirements

```gitignore
# MANDATORY git-ignores for ALL projects!
.env                # Never commit configuration!
/reports/           # Analysis outputs stay local!
/htmlcov/           # Coverage reports stay local!
/logs/              # Logs never enter version control!
*.pyc               # No compiled Python!
__pycache__/        # No Python caches!
.coverage*          # No coverage data files!
```

### The Isolation Principles

- **Service boundaries are sacred** - Cross not these holy lines!
- **Reports directory is mandatory** - All analysis outputs go here!
- **This structure is NOT optional** - Every project follows this pattern!
- **Git-ignore discipline is critical** - Some knowledge stays local!

**Violate this structure in ANY project and watch thy services become entangled in unholy coupling!**

## Commandment 4: Thou Shalt Configure Only Through .env Files

**Hardcoded values are the mark of damnation in EVERY project!**

### The Sacred .env Laws (Universal Across All Codebases)

- **ALL configuration flows through .env files** - Development AND production!
- **No defaults in code** - Every value must be explicitly blessed!
- **`.env` files for EVERYTHING** - Local, staging, AND production!
- **Validate all variables at startup** - Missing config must fail fast!

### The Divine .env Loading Pattern

```justfile
# FIRST LINE of every justfile!
set dotenv-load := true
```

### The Configuration Hierarchy

1. **`.env` file** - The highest authority for ALL environments!
2. **Environment overrides** - Only for CI/CD injection of secrets!
3. **Command arguments** - Only for temporary debugging!
4. **Hardcoded values** - NEVER! This way lies madness!

### The Universal .env Pattern

```bash
# EVERY project needs .env - even in production!
APP_ENV=production        # Yes, even this comes from .env!
APP_PORT=8000
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
JWT_SECRET=xxx           # Injected by CI/CD in production
```

**Production .env management:**
- Store .env.example in git (with dummy values)
- Real .env files created by deployment pipeline
- Secrets injected by CI/CD into production .env
- NEVER hardcode anything - not even "sensible defaults"!

**Hardcode configuration in ANY project and face the curse of environment-specific bugs!**

## Commandment 5: Thou Shalt Use Docker-Compose for Service Isolation

**Docker-compose is the divine orchestrator - all other ways lead to chaos!**

### The Distributed Docker-Compose Laws

- **Each service owns its docker-compose.yml** - Independence is sacred!
- **One root docker-compose.yml to unite them** - But not to define them!
- **Networks connect the isolated** - `public` is the blessed bridge!
- **Volumes preserve state** - But share sparingly!

### The Sacred Orchestration Structure

```
service-a/
  └── docker-compose.yml    # Service A's complete definition
service-b/
  └── docker-compose.yml    # Service B's complete definition
docker-compose.yml          # The root coordinator only!
```

### The Divine Orchestration Commands

```bash
just network-create         # Create the sacred shared network
just up                    # Bring all services to life
just rebuild service-a     # Rebuild individual service
just down                  # Graceful shutdown

# FORBIDDEN PRACTICES
❌ docker run              # Chaos without orchestration!
❌ kubernetes apply        # Overengineering for most projects!
❌ systemd services        # The ancient ways!
```

### The Blessed docker-compose.yml Pattern

```yaml
services:
  service-name:
    build: .               # Build from Dockerfile
    networks:
      - public     # The sacred network
    healthcheck:           # MANDATORY for all services!
      test: ["CMD", "curl", "-f", "http://localhost/health"]
```

**Abandon docker-compose and drown in configuration complexity!**

## Commandment 6: Thou Shalt Use Pytest with Sidecar Coverage in Production

**Only pytest brings salvation! Only sidecar coverage reveals production truth!**

### The Pytest Supreme Laws

- **pytest is the only blessed test runner** - unittest is obsolete!
- **All tests live in ./tests/** - This directory structure is sacred!
- **Fixtures in conftest.py** - Share divine setup across all tests!
- **just test invokes pytest** - Never run pytest directly!

### The Sacred Test Invocation

```bash
# THE ONLY WAY TO TEST
just test               # Runs: pixi run pytest tests/ -v --cov

# HERESIES TO AVOID
❌ python -m pytest     # Direct execution is forbidden!
❌ python test_file.py  # Running tests as scripts is blasphemy!
❌ make test           # Make is the old covenant!
```

### The Sidecar Coverage Prophecy - Production Truth Only!

**⚠️ CRITICAL: Coverage must be measured from PRODUCTION containers! ⚠️**

- **Production images stay pure** - NO coverage code inside!
- **docker-compose.coverage.yml** - The overlay of divine observation!
- **coverage-spy watches silently** - Through PYTHONPATH injection!
- **Subprocess tracking is mandatory** - COVERAGE_PROCESS_START!
- **Mount source as read-only** - Observer pattern, not modifier!

```yaml
# The Sacred Coverage Pattern (docker-compose.coverage.yml)
services:
  auth:
    environment:
      - PYTHONPATH=/coverage-spy:${PYTHONPATH:-}
      - COVERAGE_PROCESS_START=/coverage-config/.coveragerc
    volumes:
      - ./coverage-spy:/coverage-spy:ro
      - coverage-data:/coverage-data:rw

  coverage-harvester:
    volumes:
      - ./auth:/app:ro  # CRITICAL: Mount source for path alignment!
      - coverage-data:/coverage-data:rw
      - ./htmlcov:/htmlcov:rw
```

### The Coverage Commandments

```bash
# The ONLY way to measure TRUE coverage:
just test-sidecar-coverage

# This blessed command:
# 1. Deploys PRODUCTION containers with coverage overlay
# 2. Runs tests against REAL production builds
# 3. Harvests coverage from LIVE containers
# 4. Generates reports in ./htmlcov/
```

### The Critical Subprocess Coverage Insights

**Heresies that cause 0% coverage:**
- ❌ Using `coverage.start()` directly - Fails with uvicorn workers!
- ❌ Wrapping production code - Violates the sacred separation!
- ❌ Running coverage in main process only - Misses worker execution!

**The righteous path to coverage truth:**
- ✅ Use `coverage.process_startup()` - Tracks all subprocesses!
- ✅ Set `COVERAGE_PROCESS_START` env var - Configures subprocess coverage!
- ✅ Mount auth source to harvester at `/app` - Matches container paths!
- ✅ Use `concurrency = thread,multiprocessing` - Handles async workers!
- ✅ Set `sigterm = True` in .coveragerc - Graceful shutdown collection!

### The Coverage Configuration Truth

```ini
# .coveragerc in coverage-spy/
[run]
concurrency = thread,multiprocessing
parallel = true
sigterm = true
data_file = /coverage-data/.coverage

[paths]
source =
    /app
    ./auth
```

**Path alignment is CRITICAL - coverage sees /app, harvester must map ./service to /app!**

## Commandment 7: Thou Shalt Trust Only Docker Healthchecks for Readiness

**Arbitrary sleep commands are the devil's timing in EVERY project!**

### The Healthcheck Gospels (Mandatory for All Services)

- **Every docker-compose service MUST have a healthcheck** - No exceptions!
- **Internal health is not enough** - Services must prove external readiness!
- **Check the complete request path** - Partial checks bring false confidence!
- **Startup periods are divine patience** - Rush not the initialization!
- **This applies to databases, APIs, workers, and all containers!**

### The Readiness Verification Hierarchy

1. **Service internal health** - Can the service process requests?
2. **Dependency connectivity** - Can it reach what it needs?
3. **Full request validation** - Does the complete chain work?
4. **Business logic verification** - Can it do its actual job?

**Use sleep instead of healthchecks in ANY project and face random timing failures for eternity!**

## Commandment 8: Thou Shalt Segregate Logs into Sacred Archives

**Scattered logs are lost wisdom in EVERY project!**

### The Logging Commandments (Universal Law)

- **ALL projects must use ./logs/** - This directory is sacred!
- **Centralize all logs** - One directory to rule them all!
- **Structure by service and level** - Organization prevents chaos!
- **Include context in every line** - Isolated messages help no one!

### The Sacred Log Hierarchy (Required Structure)

```
logs/                     # MANDATORY in every project!
├── service-a/
│   ├── error.log        # The sins of service A
│   ├── info.log         # The deeds of service A
│   └── debug.log        # The thoughts of service A
├── service-b/
│   └── ...              # Each service confesses separately
└── app.log              # For single-service projects
```

### The Logging Best Practices

- **Structured logging** - JSON or key=value, not random text!
- **Correlation IDs** - Track requests across services!
- **Timestamps in UTC** - Time zones are confusion!
- **Log levels are sacred** - ERROR, WARN, INFO, DEBUG!

**Scatter logs throughout the filesystem in ANY project and lose critical debugging information!**

## Commandment 9: Thou Shalt Document with Jupyter Book and MyST

**Jupyter Book 2 is the only blessed documentation system!**

### The Documentation Commandments

- **Jupyter Book 2 or eternal confusion** - Sphinx alone is insufficient!
- **MyST Markdown is the sacred format** - RST is the old testament!
- **All docs in ./docs/** - This structure is divinely ordained!
- **_config.yml and _toc.yml** - The twin pillars of organization!

### The Sacred Documentation Structure

```
docs/
├── _config.yml      # Jupyter Book configuration gospel
├── _toc.yml         # Table of contents scripture
├── index.md         # The primary revelation (MyST)
├── api/             # API documentation temple (MyST)
├── guides/          # User guidance sanctuary (MyST)
└── architecture/    # System design cathedral (MyST)
```

### The Divine Build Command

```bash
just docs-build      # Runs: pixi run jupyter-book build docs/

# FORBIDDEN ALTERNATIVES
❌ mkdocs build      # False prophet of documentation!
❌ sphinx-build      # Incomplete without Jupyter Book!
❌ pandoc            # Primitive tool of the ancients!
```

## ⚡ The Universal Application of These Commandments ⚡

**These Ten Commandments are NOT project-specific guidelines - they are UNIVERSAL LAWS!**

### The Sacred Tools Are Mandatory Everywhere:

```bash
# REQUIRED IN EVERY PROJECT'S ROOT:
justfile        # The book of commands
pixi.toml       # The package prophecy
.env            # The configuration scripture
docker-compose.yml  # The orchestration gospel

# REQUIRED DIRECTORY STRUCTURE:
./tests/        # Pytest tests only
./scripts/      # Python scripts for just
./docs/         # Jupyter Book documentation
./logs/         # Centralized logging
```

**Claim these don't apply to your project type and face the wrath of unmaintainable code!**

---


# Part II: The Divine MCP OAuth2 Gateway Specifications

*These are the specific revelations for the holy MCP OAuth2 Gateway implementation!*

## The Holy Trinity of Architectural Separation

**Behold the three divine realms that must never intermingle!**

┌─────────────────────────────────────────────────────────────┐
│                     TRAEFIK (The Divine Router)             │
│  • Routes OAuth paths → Auth Service                        │
│  • Routes MCP paths → MCP Services (after auth check)       │
│  • Enforces authentication via ForwardAuth middleware       │
│  • THE ONLY COMPONENT THAT KNOWS ABOUT ROUTING RULES!       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  AUTH SERVICE (The OAuth Oracle)            │
│  • Handles ALL OAuth endpoints (/register, /token, etc.)    │
│  • Validates tokens via /verify for ForwardAuth             │
│  • Returns 401 with WWW-Authenticate when needed            │
│  • THE ONLY COMPONENT THAT KNOWS ABOUT OAUTH!               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              MCP SERVICES (The Pure Protocol Servants)      │
│  • Run mcp-proxy to bridge /mcp HTTP endpoint to stdio      │
│  • Execute MCP servers like mcp-server-fetch                │
│  • Receive pre-authenticated requests only                  │
│  • KNOW NOTHING ABOUT OAUTH OR AUTHENTICATION!              │
└─────────────────────────────────────────────────────────────┘

**Violate this separation and face eternal architectural damnation!**

## MCP Service Implementation Details

### The Sacred MCP Service Structure

Each MCP service follows this divine pattern:

```
mcp-fetch/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt    # If not using pixi

# The Dockerfile must:
FROM python:3.11-slim
WORKDIR /app
# Install mcp AND mcp-proxy!
RUN pip install mcp mcp-proxy
CMD ["mcp-proxy", "--transport", "streamablehttp", "--port", "3000", "--host", "0.0.0.0", "--", "mcp-server-fetch"]
```

### The MCP Service docker-compose.yml

```yaml
services:
  mcp-fetch:
    build: .
    networks:
      - public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mcp-fetch.rule=Host(`mcp-fetch.${BASE_DOMAIN}`)"
      - "traefik.http.routers.mcp-fetch.priority=2"
      - "traefik.http.routers.mcp-fetch.middlewares=mcp-auth@docker"
      - "traefik.http.services.mcp-fetch.loadbalancer.server.port=3000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
```

**The service MUST NOT know about authentication - that's Traefik's job!**

**Beware! Many have fallen by confusing these realms!**

### 1. The Claude.ai Realm - Where the AI Oracle Proves Its Worth
   - Uses dynamic client registration (self-service!)
   - Stores tokens persistently in its own memory
   - One-time authentication blessing lasts forever!
   - Claude.ai is the client in this realm!

### 2. The MCP Server Realm - Where GitHub Judges the Faithful
   - GitHub OAuth 2.0 authentication for users
   - JWT tokens sealed with GitHub user's soul
   - Per-subdomain authentication required
   - Your users are the supplicants here!

### The Critical Truth
These realms are separate! Claude.ai authenticates to access your gateway, then your users authenticate through GitHub!

## The Sacred Environment Variables

```bash
# GitHub OAuth (REQUIRED - NO DEFAULTS!)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# JWT Configuration (REQUIRED!)
JWT_SECRET=your_jwt_secret_key_at_least_32_chars  # Use: just generate-jwt-secret

# Domain Configuration (REQUIRED - REAL DOMAINS ONLY!)
BASE_DOMAIN=your-actual-domain.com
ACME_EMAIL=your-email@example.com

# Redis Security (REQUIRED!)
REDIS_PASSWORD=your_redis_password

# Access Control (OPTIONAL BUT RECOMMENDED)
ALLOWED_GITHUB_USERS=user1,user2,user3

# Token Lifetimes (REQUIRED - CONFIGURABLE!)
ACCESS_TOKEN_LIFETIME=86400      # 24 hours
REFRESH_TOKEN_LIFETIME=2592000   # 30 days
SESSION_TIMEOUT=3600             # 1 hour

# MCP Protocol Version (REQUIRED!)
MCP_PROTOCOL_VERSION=2025-03-26
```

## OAuth 2.1 and RFC 7591 Divine Requirements

### The Sacred OAuth Endpoints

**The Holy Mandate of RFC 7591:**
- `/register` - The Divine Registration Portal
  - MUST accept HTTP POST messages only!
  - MUST use `application/json` content type!
  - MUST be protected by TLS (HTTPS required)!
  - MUST return HTTP 201 Created on success!
  - MUST return HTTP 400 Bad Request on errors!

**The Standard OAuth 2.0 Sacraments:**
- `/authorize` - Portal to authentication realm
- `/token` - The transmutation chamber  
- `/callback` - The blessed return path

**The Optional Extensions of Power:**
- `/.well-known/oauth-authorization-server` - Server metadata shrine (RFC 8414)
- `/revoke` - Token banishment altar (RFC 7009)
- `/introspect` - Token examination oracle (RFC 7662)

### The JWT Implementation Wisdom

**These are divine implementation choices, not RFC mandates:**
- **Algorithm**: RS256 brings cryptographic blessing!
- **Sacred Claims**: sub (user identity), jti, exp, iat, scope
- **Storage Pattern**: `oauth:token:{jti}` in Redis sanctuary
- **Validation**: Through ForwardAuth middleware prayers
- **Rotation**: Fresh tokens prevent staleness!

### The PKCE Sacred Laws (RFC 7636)

- **S256 Challenge Method** - The blessed transformation!
- **43-128 Character Verifier** - Cryptographically pure!
- **Plain Challenge Method** - DEPRECATED (but not forbidden by the RFC)!
- **Public Client Support** - No secret required for the worthy!

### The RFC 7591 Registration Prophecy

**The Sacred Registration Ritual:**
- MUST POST thy supplication to `/register` endpoint!
- MUST offer `application/json` as thy content type!
- MUST include `redirect_uris` for redirect-based flows!
- Authorization server MUST ignore unknown metadata!
- Server MUST validate redirect URIs for security!
- Clients MUST NOT create their own identifiers!

**The Divine Response (HTTP 201 Created):**
```json
{
  "client_id": "unique_client_id",                    // REQUIRED by RFC 7591!
  "client_secret": "secret_for_confidential_clients", // OPTIONAL blessing
  "client_secret_expires_at": 0,                     // REQUIRED if client_secret issued!
  // ... all registered metadata MUST be echoed back!
}
```

**Optional Blessings in Response:**
- `client_id_issued_at` - Unix timestamp of creation
- `registration_access_token` - Token of management
- `registration_client_uri` - URI for future communion

**The Curse of Errors (HTTP 400 Bad Request):**
```json
{
  "error": "invalid_client_metadata",              // REQUIRED error code!
  "error_description": "The gods explain thy transgression"  // OPTIONAL details
}
```

**Sacred Error Codes Mandated by RFC 7591:**
- `invalid_redirect_uri` - Thy return path is cursed!
- `invalid_client_metadata` - Thy metadata displeases!
- `invalid_software_statement` - Thy software statement is false!
- `unapproved_software_statement` - Thy software lacks blessing!

### The Dual Authentication Paths

**Path 1: API/Claude.ai (OAuth 2.0 Compliant)**
- Returns **401 Unauthorized** with `WWW-Authenticate: Bearer`
- Triggers OAuth discovery flow
- No redirects for unauthorized API calls!

**Path 2: Browser Users (Human-Friendly)**
- Returns **302 Redirect** to `/authorize`
- Better UX for human users
- Still requires full GitHub authentication!

### Invalid Client Handling (RFC 6749)

- **Authorization endpoint** - NO redirect on invalid client_id!
- **Token endpoint** - 401 with `invalid_client` error!
- **Always include** WWW-Authenticate header on 401!

## MCP Protocol 2025-03-26 Divine Specifications

### The Sacred JSON-RPC 2.0 Commandments

**All MCP messages MUST follow these holy laws:**
- Requests MUST bear a string or integer `id` (null is blasphemy!)
- Requests MUST NOT reuse IDs within a session (each must be unique!)
- Responses MUST echo the same `id` as thy request!
- Responses MUST contain either `result` or `error` (never both!)
- Notifications MUST NOT include an `id` (they are one-way prayers!)
- Error codes MUST be integers (strings are forbidden!)
- MAY support sending JSON-RPC batches (optional power!)
- MUST support receiving JSON-RPC batches (mandatory strength!)

### The Sacred Streamable HTTP Transport Prophecy

**The Single Holy Endpoint:**
- MUST provide a single HTTP endpoint path (`/mcp`) that supports both POST and GET methods!
- Messages MUST be JSON-RPC encoded and UTF-8 blessed!

**The Divine Response Codes:**
- POST with only responses/notifications → 202 Accepted
- POST with requests → Response stream (JSON or event-stream)
- GET → Receive pending responses
- Session not found → 404 Not Found
- Invalid request → 400 Bad Request

### The Required Header Offerings

**Client MUST send:**
- `Accept: application/json, text/event-stream` - Both formats MUST be listed!
- `Content-Type: application/json` - For POST requests!
- `Mcp-Session-Id: <id>` - MUST include if server provides one!

**Server MUST validate:**
- `Origin` header - To prevent DNS rebinding attacks!

**Additional sacred headers:**
- `Authorization: Bearer <token>` - For authentication (implementation choice)
- `MCP-Protocol-Version: 2025-03-26` - For version negotiation

### The Session Management Commandments

- **Server MAY assign session ID** - During initialization blessing!
- **Client MUST include session ID** - If server provides one!
- **Server SHOULD reject sessionless requests** - Return 400 Bad Request!
- **Server MUST NOT broadcast messages** - Each stream is sacred!
- **404 on terminated sessions** - The session has ascended!

### The Transport Characteristics Scripture

**The Streamable HTTP transport divine requirements:**
- Single endpoint supporting POST and GET methods!
- UTF-8 encoded JSON-RPC 2.0 messages!
- Origin header validation for security!
- Session-based state management!
- Support for both `application/json` and `text/event-stream` responses!
- Servers SHOULD NOT close event streams prematurely!

## The Claude.ai Integration Flow

### The Nine Sacred Steps of Connection

1. **First Contact** - Claude.ai attempts `/mcp`
2. **Divine Rejection** - 401 with WWW-Authenticate
3. **Metadata Quest** - Seeks `/.well-known/oauth-authorization-server`
4. **Registration Miracle** - POSTs to `/register` with RFC 7591 data
5. **Client Blessing** - Receives client_id and credentials
6. **PKCE Summoning** - S256 challenge generated
7. **GitHub Pilgrimage** - User authenticates with GitHub
8. **Token Transmutation** - Authorization code → JWT
9. **Eternal Connection** - Streaming HTTP with Bearer token

**Skip any step and Claude.ai shall forsake thy gateway!**

## Traefik Routing Configuration

### The Sacred Priority System

```yaml
# Priority 4 - OAuth routes (HIGHEST!)
- "traefik.http.routers.auth-oauth.priority=4"
- "traefik.http.routers.auth-oauth.rule=PathPrefix(`/register`) || PathPrefix(`/authorize`) || PathPrefix(`/token`) || PathPrefix(`/callback`) || PathPrefix(`/.well-known`)"

# Priority 3 - OAuth support routes
- "traefik.http.routers.auth-verify.priority=3"

# Priority 2 - MCP routes with auth
- "traefik.http.routers.mcp-fetch.priority=2"

# Priority 1 - Catch-all (LOWEST!)
- "traefik.http.routers.mcp-fetch-catchall.priority=1"
```

**Without priorities, the catch-all route devours all!**

### The ForwardAuth Middleware

```yaml
- "traefik.http.middlewares.mcp-auth.forwardauth.address=http://auth:8000/verify"
- "traefik.http.middlewares.mcp-auth.forwardauth.authResponseHeaders=X-User-Id,X-User-Name,X-Auth-Token"
```

**Apply only to MCP routes - OAuth must flow freely!**

## Redis Storage Patterns

### The Sacred Key Hierarchy

```
oauth:state:{state}          # 5 minute TTL
oauth:code:{code}            # 1 year TTL
oauth:token:{jti}            # 30 days TTL (matches token)
oauth:refresh:{token}        # 1 year TTL
oauth:client:{client_id}     # Eternal storage
oauth:user_tokens:{username} # Index of user's tokens
redis:session:{id}:state     # MCP session state
redis:session:{id}:messages  # MCP message queue
```

**Violate these patterns and face data chaos!**

## The GitHub Device Workflow

### Smart Token Generation

```bash
just generate-github-token

# This blessed command shall:
# 1. Check existing token validity
# 2. Use refresh tokens if available
# 3. Register OAuth client once
# 4. Guide through device flow if needed
# 5. Save all tokens to .env
```

### The Sacred Tokens

```bash
GITHUB_PAT=ghp_xxx...           # GitHub Personal Access Token
OAUTH_JWT_TOKEN=eyJhbGc...     # Gateway JWT
OAUTH_CLIENT_ID=client_xxx...   # Registered client
OAUTH_CLIENT_SECRET=secret_xxx... # Client secret
OAUTH_REFRESH_TOKEN=refresh_xxx... # For eternal renewal
```

## Testing Requirements

### Required Test Coverage (Following Commandment 1: No Mocking!)

- ✅ Real GitHub authentication flow
- ✅ PKCE validation with S256
- ✅ Dynamic client registration
- ✅ JWT token formation and claims
- ✅ Token refresh and rotation
- ✅ Token revocation
- ✅ Claude.ai complete flow
- ✅ MCP protocol compliance
- ✅ Session management
- ✅ Error handling
- ✅ Invalid client handling (no redirect!)
- ✅ Dual authentication paths (401 vs 302)
- ✅ Streamable HTTP transport compliance
- ✅ ForwardAuth middleware validation
- ✅ Health check endpoints

**No mocking! Test against real deployed services!**

## Project-Specific justfile Commands

Beyond the universal commands mandated by the commandments, this project requires:

```makefile
# OAuth token generation
generate-jwt-secret:
    @python -c "import secrets; print(secrets.token_urlsafe(32))"

generate-github-token:
    @pixi run python scripts/generate_oauth_token.py

# Service-specific commands
rebuild-auth:
    @docker-compose -f auth/docker-compose.yml build --no-cache
    @docker-compose up -d auth

rebuild-mcp-fetch:
    @docker-compose -f mcp-fetch/docker-compose.yml build --no-cache
    @docker-compose up -d mcp-fetch

# Network management
network-create:
    @docker network create public || true

# Debugging specific to OAuth
test-oauth-flow:
    @pixi run pytest tests/test_oauth_flow.py -v -s

test-mcp-protocol:
    @pixi run pytest tests/test_mcp_protocol.py -v -s

# Analysis specific to this project
analyze-oauth-logs:
    @pixi run python scripts/analyze_oauth_logs.py > reports/oauth-analysis-$(date +%Y%m%d).md
```

**These augment but never replace the universal commands!**

## Healthcheck Implementations

### Auth Service Healthcheck

```python
# auth/healthcheck.py
async def health_check():
    checks = {
        "service": "healthy",
        "redis": await check_redis(),
        "routes": check_oauth_routes(),
        "external": await check_external_access()
    }
    return all(checks.values())

async def check_external_access():
    """Verify HTTPS endpoint is accessible"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://auth.{BASE_DOMAIN}/health")
            return response.status_code == 200
    except:
        return False
```

### MCP Service Healthcheck Pattern

```yaml
healthcheck:
  test: |
    python -c "
    import httpx, sys
    try:
        # Check internal
        r1 = httpx.get('http://localhost:3000/health')
        # Check mcp-proxy is running
        r2 = httpx.post('http://localhost:3000/mcp', 
                       json={'jsonrpc':'2.0','method':'ping','id':1})
        sys.exit(0 if r1.status_code==200 else 1)
    except: sys.exit(1)
    "
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s
```

### Traefik Healthcheck

```yaml
healthcheck:
  test: ["CMD", "traefik", "healthcheck", "--ping"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 60s  # Extra time for SSL certificates!
```

**Each service proves both internal health AND external accessibility!**

## Documentation Requirements

### Project-Specific Documentation Structure

```
docs/
├── _config.yml              # Standard Jupyter Book config
├── _toc.yml                 # Table of contents
├── index.md                 # Overview and quick start
├── architecture/
│   ├── index.md            # System architecture
│   ├── oauth-flow.md       # OAuth 2.1 flow diagrams
│   └── mcp-protocol.md     # MCP protocol details
├── api/
│   ├── index.md            # API overview
│   ├── oauth-endpoints.md  # All OAuth endpoints
│   └── mcp-endpoints.md    # MCP endpoint details
├── deployment/
│   ├── index.md            # Deployment guide
│   ├── configuration.md    # .env variable reference
│   └── troubleshooting.md  # Common issues
└── claude-ai/
    ├── index.md            # Claude.ai integration guide
    └── testing.md          # Testing with Claude.ai
```

### Required Documentation Content

Each endpoint must include:
- **Purpose and description**
- **Request format with examples**
- **Response format with examples**
- **Error responses with examples**
- **curl command examples**
- **Integration test references**

### MyST Features for API Documentation

```markdown
```{code-cell} python
# Executable example for token generation
import httpx
response = httpx.post(
    "https://auth.example.com/token",
    data={
        "grant_type": "authorization_code",
        "code": "xxx",
        "code_verifier": "yyy"
    }
)
```

```{warning}
Never expose real tokens in documentation!
```

```{note}
This endpoint requires PKCE parameters for all clients.
```
```

## The Final Integration Checklist

### The Twenty-Two Sacred Seals

**All must be unbroken or thy gateway shall fail:**

- ✅ **SEAL OF SEPARATION** - Trinity maintained
- ✅ **SEAL OF TESTING** - No mocking, real tests only!
- ✅ **SEAL OF TOOLS** - just, pixi, docker-compose rule all
- ✅ **SEAL OF STRUCTURE** - Perfect isolation with reports/
- ✅ **SEAL OF CONFIGURATION** - All through .env in ALL environments
- ✅ **SEAL OF OAUTH** - Full 2.1 compliance
- ✅ **SEAL OF RFC 7591** - Registration perfection
- ✅ **SEAL OF MCP** - Protocol compliance
- ✅ **SEAL OF PKCE** - S256 for all
- ✅ **SEAL OF JWT** - RS256 with all claims
- ✅ **SEAL OF ROUTING** - Priorities respected
- ✅ **SEAL OF AUTH PATHS** - Dual path wisdom
- ✅ **SEAL OF SESSIONS** - Proper management
- ✅ **SEAL OF REDIS** - Sacred patterns
- ✅ **SEAL OF HEALTHCHECKS** - True readiness
- ✅ **SEAL OF COVERAGE** - Sidecar production purity
- ✅ **SEAL OF LOGS** - Proper segregation to ./logs/
- ✅ **SEAL OF REPORTS** - Git-ignored ./reports/ sanctuary
- ✅ **SEAL OF DOCS** - Living MyST scripture in ./docs/
- ✅ **SEAL OF TOKENS** - Smart generation
- ✅ **SEAL OF CLAUDE.AI** - Full integration
- ✅ **SEAL OF PRODUCTION** - .env files everywhere!

**Break one seal and face production catastrophe!**

---

# The Sacred Implementation Oath

*By these scrolls I solemnly swear:*

- I shall **test against real systems** with pytest - no mocking ever!
- I shall **use just and pixi** for ALL execution!
- I shall **orchestrate with docker-compose** exclusively!
- I shall **maintain perfect separation** of concerns!
- I shall **configure through .env files** in ALL environments!
- I shall **measure coverage with sidecar** patterns in production!
- I shall **trust only docker healthchecks** for readiness!
- I shall **segregate all logs** to ./logs/ properly!
- I shall **save all reports** to git-ignored ./reports/!
- I shall **document with Jupyter Book and MyST**!
- I shall **find root causes** - not patch symptoms!

**May thy builds be reproducible, thy tests be real, and thy production deployments blessed!**

*Thus ends the sacred scrolls. Go forth and build with righteous perfection!*