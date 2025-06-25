# Part I: The Ten Sacred Commandments of Divine Python Development

**🔥 Behold! The Universal Laws of Python Righteousness! ⚡**

**⚡ Ignore these at your peril! Production will punish your heresy! ⚡**

## 0. Root Cause Analysis or Eternal Debugging Hell

**🔥 Five whys or debug forever! The divine law of problem solving! ⚡**

**The Sacred Ritual of Root Cause Divination:**
1. **Why did it fail?** - The surface symptom of darkness!
2. **Why did that condition exist?** - The enabling circumstance of doom!
3. **Why was it allowed?** - The systemic failure of protection!
4. **Why wasn't it caught?** - The testing blindness of ignorance!
5. **Why will it never happen again?** - The divine fix of eternal prevention!

**⚡ Treating symptoms = eternal suffering! ⚡**

**⚡ Finding root cause = divine enlightenment! ⚡**

**The Path to Debugging Salvation:**
- ✅ Reproduce reliably or face chaos!
- ✅ Trace to the source of evil!
- ✅ Fix the SYSTEM, not the instance!
- ✅ Write tests that guard eternally!
- ✅ Document the divine wisdom gained!

## 1. No Mocks or Burn in Production Hell

**🔥 No mocks! No stubs! No fakes! The divine law of real testing! ⚡**

**The Sacred Truth:**
- **Real systems only** - Test against ACTUAL services!
- **End-to-end mandatory** - The FULL stack or nothing!
- **Real APIs only** - Mock responses are LIES!
- **No shortcuts** - Pain now or AGONY later!

**⚡ Every mock is a lie waiting to destroy production! ⚡**

**The Path of Testing Righteousness:**
- ✅ Docker containers for real services!
- ✅ Actual databases with real constraints!
- ✅ True API calls with network latency!
- ✅ Production-like environments always!
- ✅ Integration tests that reveal truth!

**⚡ Mock = production hell! This is the eternal law!⚡**

## 2. The Holy Trinity of Tools

**🔥 The blessed trinity = salvation! All else = damnation! ⚡**

**⚡ BLASPHEMY ALERT: Using ANY other tool is HERESY! ⚡**
**⚡ NEVER run commands directly! ALWAYS channel through the Trinity! ⚡**

**The Three Pillars of Divine Enlightenment:**
1. **just** - The Divine Command Executor! ⚡ ALL commands flow through just!
2. **pixi** - The Blessed Package Manager! 🔥 ALL Python packages through pixi!
3. **docker-compose** - The Sacred Orchestrator! 🚦 ALL services through compose!

**⚡ Violate the trinity and face dependency hell, debugging purgatory, and production damnation! ⚡**

**THE SUPREME LAW: If you're not typing "just", you're committing HERESY!**

**⚡ The Sacred Path vs The Path to Damnation ⚡**

**✅ THE RIGHTEOUS PATH - ALWAYS DO THIS:**
```bash
just run analyze --verbose          # DIVINE! Script execution with args!
just test -k auth --pdb            # BLESSED! Flexible testing!
just up                            # RIGHTEOUS! Service orchestration!
just exec redis redis-cli          # HOLY! Service access through just!
just rebuild auth mcp-fetch        # SACRED! Multiple services at once!
just logs -f auth                  # BLESSED! Following specific logs!
just build --no-cache              # RIGHTEOUS! Build with options!
```

**⚡ EVERY command MUST start with "just" or face eternal debugging! ⚡**

**The Divine Justfile Pattern:**
```justfile
set dotenv-load := true          # FIRST LINE - ALWAYS! Load .env automatically!
set dotenv-required              # DIE if .env is missing! No mercy for the unprepared!
set positional-arguments := true # Enable blessed argument passing!
set allow-duplicate-recipes      # Allow recipe overloading with different arity!
set export := true               # Export all variables as environment variables!
set quiet                        # Silence the incantations! Show only results!
```

**⚡ The Sacred Testing Commandments - EXPANDED WITH DIVINE FURY! ⚡**

**🔥 THE FIRST LAW: "just" IS YOUR ONLY INTERFACE! 🔥**

- **`just test`** - 🧪 The ONLY way to run tests! `pytest` alone = BLASPHEMY!
- **`just test-all`** - 🌟 The complete test suite! NEVER run tests individually!
- **`just test-verbose`** - 📢 Verbose testing! NEVER add flags to pytest directly!
- **`just test-sidecar-coverage`** - 🔥 The holy grail! NEVER run coverage tools directly!
**⚡ THE DIVINE WARNING: Ad Hoc Commands = ETERNAL DEBUGGING HELL! ⚡**


**🔥 The Only Acceptable Commands: 🔥**
- Commands starting with `just`
- Initial installation of the trinity tools
- NOTHING ELSE! NO EXCEPTIONS!

**⚡ Remember: If you're not typing "just", you're typing BLASPHEMY! ⚡**

**⚡ One flexible recipe > 100 specific commands! Use positional arguments! ⚡**

**🔥 The Divine Power of Just Settings & Features 🔥**

```justfile
# With 'set quiet', @ prefix is optional - silence is default!
test filter="":
    pixi run pytest {{filter}} ${PYTEST_ARGS:-}

# Use @ when you WANT to see the command (overrides quiet)
@test-verbose filter="":
    pixi run pytest {{filter}} -vvv

# Optional positional arguments with defaults
rebuild service="all":
    #!/usr/bin/env bash
    if [ "{{service}}" = "all" ]; then
        docker-compose build --no-cache
    else
        docker-compose build --no-cache {{service}}
    fi
```

## 3. Sacred Project Structure or Directory Chaos

**🏛️ Divine isolation is mandatory! Structure brings salvation! ⚡**

```
project/
├── service-a/            # Service sanctuary - one service, one directory!
│   ├── Dockerfile        # Container incantation for divine isolation!
│   └── docker-compose.yml # Service orchestration!
├── service-b/            # Another service temple - sacred separation!
│   ├── Dockerfile        # Container blessing for this service!
│   └── docker-compose.yml # Service-specific orchestration!
├── package-name/         # Python package cathedral - divine code library!
│   ├── src/              # Source code sanctuary - the blessed pattern!
│   │   └── package_name/ # Your actual package with __init__.py!
│   ├── pyproject.toml    # Package metadata gospel!
├── tests/                # All pytest tests here - no exceptions!
│   ├── conftest.py       # Sacred fixtures and divine configuration!
│   ├── test_*.py         # Test files with blessed naming!
│   └── helpers/          # Test utility modules!
├── scripts/              # All Python scripts for automation!
│   ├── __init__.py       # Makes scripts importable!
│   └── *.py              # Divine automation utilities!
├── docs/                 # All Jupyter Book documentation!
│   ├── _config.yml       # Documentation configuration gospel!
│   ├── _toc.yml          # Table of contents scripture!
│   └── sections/         # Documentation chapters!
├── logs/                 # All logs segregated here!
├── reports/              # All analysis reports (git-ignored)!
├── htmlcov/              # Coverage reports (git-ignored)!
├── coverage-spy/         # Sidecar coverage sanctuary!
│   └── sitecustomize.py  # The divine coverage interceptor!
├── docker-compose.yml    # Master orchestration scripture!
├── justfile              # The book of divine commands!
├── pixi.toml             # Package management gospel!
├── pixi.lock             # Dependency lock for reproducibility!
├── pytest.ini            # Testing configuration commandments!
├── .env                  # Sacred configuration (git-ignored)!
├── .env.example          # Configuration template!
├── .coveragerc           # Coverage configuration!
├── .gitignore            # Must ignore sacred secrets!
├── README.md             # Project revelation!
└── CLAUDE.md             # Divine development guidance!
```

**⚡ The Sacred Truths of Structure! ⚡**
- **Services live in directories** - Not in src/!
- **Python packages use src/package_name/** - The blessed pattern!
- **Tests stay in ./tests/** - Never inside packages!
- **Scripts are Python files** - In ./scripts/ with __init__.py!
- **All config through .env** - Never hardcoded!

**⚡ Violate this structure = project chaos! ⚡**

## 4. Configuration Through .env or Damnation

**🔥 All configuration flows through .env! This is the law! ⚡**

**The Divine Configuration Commandments:**
- **All config through .env** - No hardcoded values!
- **No defaults in code** - Explicit > implicit!
- **Validate at startup** - Fail fast and loud!
- **Store .env.example** - Template for mortals!
- **Use `set dotenv-required`** - Force .env existence or face instant death!


## 5. Docker Compose for All Services or Container Chaos

**🐳 Compose is the divine orchestrator! All else is madness! ⚡**

**The Sacred Orchestration Principles:**
- **One service, one directory** - Divine isolation!
- **Compose for coordination** - Not definition!
- **Named networks** - Bridge thy services via public!
- **Holy Traefik** - The one proxy to rule all services!
- **Health checks mandatory** - Prove thy readiness!

**The Blessed Docker-Compose Pattern:**
```yaml
include:
  - traefik/docker-compose.yml
  - serviceA/docker-compose.yml
  - serviceB/docker-compose.yml

networks:
  public:
    external: true

volumes:
  traefik-certificates:
    external: true
  serviceA-data:
    external: true
  serviceB-data:
    external: true
```

**⚡ No healthchecks = random failures! ⚡**

## 6. Pytest and Coverage or Testing Damnation

**🧪 Pytest is the only true test runner! Coverage reveals truth! ⚡**

**The Testing Commandments:**
- **pytest only** - unittest is obsolete darkness!
- **./tests/ directory** - The sacred testing temple!
- **conftest.py** - Divine fixtures live here!
- **Coverage or ignorance** - Measure thy righteousness!
- **Test behavior, not implementation** - Focus on divine outcomes!

**⚡ Untested code = broken code! This is the law! ⚡**

## 7. Real Health Checks or Random Failures

**😈 Sleep commands are Satan's timing! Only healthchecks save! ⚡**

**The Health Check Gospels:**
- **Every service needs health** - Prove thy life!
- **Dependencies must be ready** - Full chain verified!
- **Check actual functionality** - Not just port open!
- **Check production endpoints** - FQDN or death!
- **For MCP services** - See "The Sacred Art of StreamableHTTP Health Checks" in Part II!

**⚡ sleep = random production failures! Protocol checks = eternal reliability! ⚡**

## 8. Centralized Logging or Debugging Chaos

**📜 Scattered logs = lost wisdom! Centralize or suffer! ⚡**

**The Logging Commandments:**
- **./logs/ directory** - The sacred log temple!
- **Structured logging** - For the divine parsers!
- **Context in every line** - Trace thy errors!

**⚡ Proper logging = debugging paradise! Chaos logging = eternal suffering! ⚡**

## 9. Document with Jupyter Book or Knowledge Chaos

**📚 Jupyter Book = divine documentation! All else is inferior! ⚡**

**The Documentation Commandments:**
- **Jupyter Book only** - Modern divine tooling!
- **MyST Markdown** - The blessed format!
- **./docs/ directory** - Knowledge sanctuary!
- **Build automatically** - CI/CD blessed!

**⚡ Undocumented code = unusable code! ⚡**

---

# Part II: Divine MCP OAuth2 Gateway

**🏗️ Sacred auth architecture! ⚡**

## System Components - The Holy Trinity Separation

**🔱 Three sacred layers of system components or damnation! ⚡**

┌─────────────────────────────────────────────────────────────┐
│    Traefik - Layer 1 (The Divine Router of Sacred Paths)    │
│  • Routes OAuth paths → Auth Service with holy priorities!  │
│  • Routes MCP paths → MCP Services (after auth blessing!)   │
│  • Enforces authentication via ForwardAuth divine wrath!    │
│  • Provides HTTPS with Let's Encrypt certificate miracles!  │
│  • The only system component that knows routing commandments!      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Auth Service - Layer 2 (The OAuth Oracle of Divine Tokens) │
│  • Handles all OAuth endpoints (/register, /token, etc.)    │
│  • Validates tokens via /verify for ForwardAuth judgment!   │
│  • Integrates with GitHub OAuth for user sanctification!    │
│  • Uses mcp-oauth-dynamicclient for sacred RFC compliance!  │
│  • The only system component that knows OAuth dark arts!           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  MCP Services - Layer 3 (The Pure Protocol Servants of Glory) │
│  • Run mcp-streamablehttp-proxy wrapping official servers!  │
│  • Bridge stdio MCP servers to HTTP endpoints with glory!   │
│  • Expose /mcp through blessed transcendence!               │
│  • Receive pre-authenticated requests only - no exceptions! │
│  • Know nothing of OAuth - pure protocol innocence!         │
│  • Health verified via StreamableHTTP protocol checks!      │
└─────────────────────────────────────────────────────────────┘

**⚡ Violate separation = monolithic damnation! ⚡**

## MCP Gateway Implementation Details

### The Divine Truth About MCP Services - The Sacred Proxy Pattern!

**Witness the architectural glory of mcp-streamablehttp-proxy!**
- We use **mcp-streamablehttp-proxy** - the divine stdio-to-streamablehttp bridge!
- This wraps official MCP servers from modelcontextprotocol/servers!
- The proxy spawns the official MCP server as subprocess and bridges stdio ↔ HTTP!

**The Divine Proxy Responsibilities:**
1. **Subprocess Management** - Spawns and manages the official MCP server!
2. **Protocol Bridging** - Converts HTTP requests ↔ stdio JSON-RPC!
3. **Session Handling** - Maintains stateful connections for MCP protocol!
4. **Health Monitoring** - Provides HTTP health endpoints for Docker!
5. **Error Translation** - Converts stdio errors to proper HTTP responses!

**Divine Benefits of mcp-streamablehttp-proxy Architecture:**
- **Official Server Wrapping** - Uses real MCP implementations!
- **Subprocess Isolation** - Each MCP server runs in isolated process space!
- **OAuth Integration** - Ready for Bearer token authentication via Traefik!
- **Traefik Compatible** - Standard HTTP endpoints for reverse proxy routing!

**Actual Server Endpoint Structure:**
- **Primary Endpoint**: `https://mcp-service.yourdomain.com/mcp` (via proxy bridge)
- **Authentication**: Bearer token via Authorization header (handled by Traefik)
- **Transport**: Streamable HTTP wrapping stdio MCP servers

**mcp-streamablehttp-proxy provides the perfect balance of official functionality with HTTP transport!**

### The Sacred MCP Service Configuration - Blessed by the Trinity!

Each MCP service channels the universal docker-compose.yml pattern enhanced with OAuth glory:
- **Traefik routing labels** - The divine reverse proxy integration!
- **ForwardAuth middleware** - OAuth token validation through sacred middleware!
- **MCP-specific port exposure** - Port 3000 for the blessed mcp-streamablehttp-proxy!
- **Project-specific networks** - Connected to the sacred `public` network of righteousness!

**The service must not know about authentication - that's Traefik's holy job per the Trinity separation!**

### 1. The MCP Gateway Client Realm - Where External Systems Seek Divine Access!
   - MCP clients (Claude.ai, IDEs, etc.) prove their worthiness here!
   - Dynamic client registration through sacred RFC 7591 rituals!
   - OAuth tokens granted become eternal bearer credentials!
   - One-time authentication blessing lasts until revoked by divine decree!
   - External MCP clients are the supplicants in this holy realm!

### 2. The User Authentication Realm - Where GitHub OAuth Judges Human Souls!
   - Human users authenticate through GitHub's divine judgment!
   - JWT tokens sealed with the user's GitHub identity and blessed scope!
   - Per-subdomain authentication enforces user-level access control!
   - Your human users must prove their worth to GitHub's OAuth oracle!
   - Separate from client authentication - dual realm architecture!

### The Critical Divine Truth of Dual Authentication!
**Two separate realms of authentication glory!**
- **MCP Gateway Client Realm**: MCP clients authenticate to access the gateway infrastructure!
- **User Authentication Realm**: Human users authenticate to access their protected resources!
- **Never confuse these realms or face security damnation!**

## Sacred Env Vars

**⚙️ Divine config! ⚡**
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` - GitHub OAuth app credentials of power!
- `GATEWAY_JWT_SECRET` - Auto-generated by the divine `just generate-jwt-secret`!
- `GATEWAY_OAUTH_ACCESS_TOKEN` / `GATEWAY_OAUTH_REFRESH_TOKEN` - Generated OAuth tokens of righteousness!
- `ALLOWED_GITHUB_USERS` - Access control whitelist of the worthy!
- `MCP_PROTOCOL_VERSION` - Protocol compliance declaration of the new covenant! (defaults to 2025-06-18)
- `CLIENT_LIFETIME=7776000` - Client registration lifetime in seconds (90 days default)!
  - **Divine revelation**: Set to `0` for eternal client registration that never expires!
  - **Sacred warning**: Eternal clients persist until manually deleted via RFC 7592!

**MCP Client Variables (The Segregated Realm of External Supplicants!):**
- `MCP_CLIENT_ACCESS_TOKEN` - Born of `just mcp-client-token`, blessed for mcp-streamablehttp-client communion!
  - **Divine warning**: This token serves external clients only!
  - **Never** confuse with gateway's own `GATEWAY_OAUTH_ACCESS_TOKEN`!
  - **Separate realms** = **Separate tokens** = **Eternal security**!

## The Sacred Art of StreamableHTTP Health Checks - Divine Protocol Verification!

**🔥 Behold! The divine prophecy of health checking MCP StreamableHTTP services! ⚡**

### The Divine StreamableHTTP Protocol Health Check Prophecy

**🌟 The Supreme Pattern for Native StreamableHTTP Services: 🌟**
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

**⚡ This divine incantation performs a blessed initialization handshake! ⚡**

**⚡ The Blessed Success Response Pattern:**
```
event: message
data: {"result":{"protocolVersion":"${MCP_PROTOCOL_VERSION}","capabilities":{...},"serverInfo":{...}},"jsonrpc":"2.0","id":1}
```
**This divine response confirms the server speaks perfect MCP protocol! ⚡**


## OAuth 2.1 + RFC 7591

**📜 RFC law! Violate = hell! ⚡**

### Sacred Endpoints

**🚀 RFC 7591:**
- `/register` - The Divine Registration Portal
  - Must accept HTTP POST messages only!
  - Must use `application/json` content type!
  - Must be protected by TLS (HTTPS required)!
  - Must return HTTP 201 Created on success!
  - Must return HTTP 400 Bad Request on errors!

**Core:** /authorize, /token, /callback
**Extensions:** /.well-known/*, /revoke, /introspect

### Divine Revelations for MCP Protocol Version!

**The `/.well-known/oauth-authorization-server` endpoint must be accessible on all subdomains!**

```yaml
# In each MCP service's docker-compose.yml - Priority 10 (Divine Supremacy!)
- "traefik.http.routers.mcp-fetch-oauth-discovery.rule=Host(`mcp-fetch.${BASE_DOMAIN}`) && PathPrefix(`/.well-known/oauth-authorization-server`)"
- "traefik.http.routers.mcp-fetch-oauth-discovery.priority=10"  # Highest priority - catches before all else!
- "traefik.http.routers.mcp-fetch-oauth-discovery.service=auth@docker"
- "traefik.http.middlewares.oauth-discovery-rewrite.headers.customrequestheaders.Host=auth.${BASE_DOMAIN}"
# No auth middleware - Discovery must be public salvation for all who seek it!
```

### The PKCE Sacred Laws (RFC 7636)

- **S256 Challenge Method** - The blessed transformation!
- **43-128 Character Verifier** - Cryptographically pure!
- **Plain Challenge Method** - Deprecated (but not forbidden by the RFC)!
- **Public Client Support** - No secret required for the worthy!

### The RFC 7591 Registration Prophecy

**The Sacred Registration Ritual:**
- Must POST thy supplication to `/register` endpoint!
- Must offer `application/json` as thy content type!
- Must include `redirect_uris` for redirect-based flows!
- Authorization server must ignore unknown metadata!
- Server must validate redirect URIs for security!
- Clients must not create their own identifiers!

### The RFC 7592 Client Management Revelation

**🔥 The Critical Divine Separation of RFC 7591 and RFC 7592 - Carved in Holy Fire! 🔥**

**RFC 7591 - The Public Registration Altar of Divine Welcome:**
- **POST /register** - Publicly accessible! The gates stand wide open!
- **No authentication required** - Come as you are, lost digital souls!
- Any client may approach this sacred altar and be born again!
- Returns `registration_access_token` - **The sacred bearer token of power!**
- Returns `registration_client_uri` - **The holy URI to thy management temple!**
- **This is the only public endpoint** - All else requires divine authentication!

**RFC 7592 - The Protected Management Sanctuary of Bearer Token Glory:**
- **Only the sacred `registration_access_token` grants entry!**
- Format: `reg-{32-byte-random}` via `secrets.token_urlsafe(32)` - divine randomness!
- Each client receives a unique bearer token at birth - **Guard it with your life!**
- This token is the **only key** to managing that specific client!
- **Lose it and your client is orphaned forever!**
- **CRITICAL**: OAuth JWT access tokens are REJECTED with 403 Forbidden!
- Implementation: `DynamicClientConfigurationEndpoint.authenticate_client()` validates!

**The Holy Trinity of Solutions for Invalid Client Recovery:**

1. **The User-Friendly Error Altar** - When invalid clients approach the authorization gate!
   - A beautiful error page guides lost souls back to righteousness!
   - Clear instructions for reconnection are divinely mandated!
   - No automatic redirects - security is paramount!

2. **The Client Expiration Prophecy** - Choose mortality or eternity!
   - 90 days of life granted by default (configurable via CLIENT_LIFETIME)!
   - `client_secret_expires_at` reveals the hour of doom (0 = immortal)!
   - **Eternal mode**: Set CLIENT_LIFETIME=0 for undying registrations!
   - Mortal clients must prepare for rebirth through re-registration!

3. **The RFC 7592 Management Endpoints** - Divine CRUD operations for client souls!

**The Sacred Management Endpoints (RFC 7592 Fully Compliant!):**

**GET /register/{client_id}** - Behold thy registration status!
**PUT /register/{client_id}** - Transform thy registration metadata!
**DELETE /register/{client_id}** - Self-immolation for compromised clients!

**The Sacred Client Lifecycle:**
1. **Birth** - Dynamic registration via POST /register (public, no auth!)
2. **Blessing** - Receive registration_access_token (guard it with thy life!)
3. **Life** - 90 days default or eternal if CLIENT_LIFETIME=0
4. **Verification** - GET /register/{client_id} with Bearer token
5. **Transformation** - PUT /register/{client_id} with Bearer token
6. **Death** - Natural expiration or DELETE /register/{client_id}
7. **Rebirth** - New registration when the old passes away

**The Divine Security Architecture - The Holy Separation of Concerns!**

**🌟 The Two Realms of Authentication Glory 🌟**

**MCP Gateway Client Realm: Client Registration Management (RFC 7591/7592)**
- **Public altar**: POST /register - No auth required!
- **Sacred gift**: registration_access_token bestowed upon registration!
- **Protected sanctuary**: GET/PUT/DELETE /register/{id} - Bearer token only!
- **Divine purpose**: Manage thy client registration lifecycle!

**User Authentication Realm: OAuth 2.0 Token Issuance (RFC 6749)**
- **Authentication required**: Client credentials for token endpoint!
- **Sacred exchange**: Authorization codes become access tokens!
- **Divine purpose**: Grant access to protected resources!

**⚡ Never confuse these realms! ⚡**
- registration_access_token ≠ OAuth access_token!
- Client management ≠ Resource access!
- RFC 7592 Bearer ≠ OAuth Bearer!
- **Mixing these tokens brings chaos and confusion!**

**The Divine Implementation Truth:**
- Registration tokens: Direct string comparison via `secrets.compare_digest`
- OAuth tokens: JWT signature validation and claims verification
- Storage: Registration tokens live in `oauth:client:{client_id}` Redis key
- Lifetime: Registration tokens match client lifetime (no separate expiry)

**The Blessed Implementation Patterns:**
```
✅ Registration: No auth → Returns registration_access_token
✅ Management: Bearer registration_access_token → Modify client
✅ OAuth: Client credentials → Returns access_token
❌ Heresy: Using OAuth tokens for client management!
❌ Blasphemy: Using registration tokens for resource access!
```

**Implement these endpoints correctly or face security breaches for eternity!**
**May your tokens be unique, your entropy high, and your realms forever separated!**

### The Authentication Path

**API (OAuth 2.0 Compliant)**
- Returns **401 Unauthorized** with `WWW-Authenticate: Bearer`
- Triggers OAuth discovery flow
- No redirects for unauthorized API calls!

### Invalid Client Handling (RFC 6749)

- **Authorization endpoint** - No redirect on invalid client_id!
- **Token endpoint** - 401 with `invalid_client` error!
- **Always include** WWW-Authenticate header on 401!

## MCP Protocol Divine Specifications - The Glorious New Covenant of Protocol Enlightenment!

### The Sacred MCP Lifecycle Laws - As Decreed by the Protocol Gods!

**🌅 The Divine Initialization Phase - The Sacred Birth of MCP Sessions! 🌅**
- **⚡ Server must receive `initialize` request ⚡** - The divine handshake of protocol communion!
- **⚡ Server must respond with protocol version ⚡** - Declaring its sacred capabilities to the client!
- **⚡ Server must include implementation details ⚡** - Revealing its divine nature and powers!
- **⚡ Only pings and logging allowed ⚡** before the `initialized` notification blessing!

**⚙️ The Holy Operation Phase - The Sacred Dance of Protocol Communication! ⚙️**
- **⚡ Server must respect negotiated protocol version ⚡** - Honor the sacred covenant established!
- **⚡ Server must use only successfully negotiated capabilities ⚡** - No false promises of unblessed powers!
- **⚡ Server must implement timeouts ⚡** for all requests - Patience has divine limits!
- **⚡ Server must handle errors with divine grace ⚡** - Even failures must be blessed with proper responses!

**🌄 The Sacred Shutdown Phase - The Peaceful Death of Protocol Sessions! 🌄**
- **⚡ Server may initiate shutdown ⚡** by closing the divine output stream!
- **⚡ Clean termination brings blessing ⚡** to all connections - No unclean deaths allowed!

### The Sacred JSON-RPC 2.0 Commandments

**All MCP messages must follow these holy laws:**
- Requests must bear a string or integer `id` (null is blasphemy!)
- Requests must not reuse IDs within a session (each must be unique!)
- Responses must echo the same `id` as thy request!
- Responses must contain either `result` or `error` (never both!)
- Notifications must not include an `id` (they are one-way prayers!)
- Error codes must be integers (strings are forbidden!)
- May support sending JSON-RPC batches (optional power!)
- Must support receiving JSON-RPC batches (mandatory strength!)

### The Sacred Streamable HTTP Transport Prophecy - Blessed by the Protocol Version!

**The new covenant brings divine clarity to transport implementation!**

**The Holy Transport Characteristics (as revealed in the protocol specification):**
- Uses HTTP POST and GET with divine purpose!
- Pure streamable HTTP for blessed communication!
- Single `/mcp` endpoint path brings divine simplicity!
- Session management through sacred `Mcp-Session-Id` headers!

**The Required Header Offerings (Mandated by the Spec):**
- `Content-Type: application/json` - For POST requests to the sacred `/mcp` endpoint!
- `MCP-Protocol-Version: ${MCP_PROTOCOL_VERSION}` - Declare thy covenant version!
- `Mcp-Session-Id: <id>` - Include if the server provides one!
- `Authorization: Bearer <token>` - For OAuth blessed endpoints!

**The Sacred Security Commandments:**
- Servers must validate `Origin` header to prevent DNS rebinding attacks!
- Bind locally to prevent network vulnerabilities!
- Implement proper authentication as decreed!
- Never accept tokens not explicitly issued for thy MCP server!

**The Divine Session Management Laws:**
- Server may assign session ID during initialization blessing!
- Client must include session ID in all subsequent requests!
- Sessions can be terminated by divine will of server or client!
- Use secure, non-deterministic session IDs generated by holy randomness!

**The Response Code Revelations:**
- POST to `/mcp` with JSON-RPC → 200 OK with blessed response
- GET to `/mcp` for pending responses → 200 OK with divine messages
- Invalid request → 400 Bad Request
- Unauthorized → 401 with `WWW-Authenticate` header
- Forbidden → 403 for insufficient permissions
- Session not found → 404 Not Found


**The Divine Benefits of mcp-streamablehttp-proxy Architecture:**
- **Official functionality** - Wraps real MCP servers, never uses fakes!
- **HTTP transport** - Provides `/mcp` endpoints for web access!
- **Process isolation** - Each MCP server runs in separate process space!
- **OAuth ready** - Bearer token authentication handled by Traefik layer!
- **Production tested** - Battle-tested proxy architecture with proven reliability!

### The Sacred Security Best Practices - Mandated by the Protocol Specification!

**The Confused Deputy Problem - Beware this ancient evil!**
- Never forward to third-party auth servers without divine permission!
- Each dynamically registered client requires explicit blessing!

**The Token Handling Commandments:**
- Must not accept tokens not explicitly issued for thy MCP server!
- Avoid the cursed "token passthrough" - validate everything!
- Validate token audiences with righteous fury!
- Maintain clear separation between service boundaries!

**The Session Security Laws:**
- Must verify all inbound requests when auth is implemented!
- Must not use sessions for authentication (OAuth only!)!
- Use secure, non-deterministic session IDs from holy randomness!
- Bind session IDs to user-specific information!

**The Sacred Risks to Prevent:**
- Circumventing security controls brings damnation!
- Compromising audit trails invites chaos!
- Breaking trust boundaries between services is heresy!
- Enabling unauthorized access summons the security demons!

**Implement these practices or face eternal security breaches!**

## The Claude.ai Integration Flow

### The Nine Sacred Steps of Connection - Blessed by the Protocol!

1. **👽 First Contact** - Claude.ai attempts `/mcp` with sacred protocol version header!
2. **⚡ Divine Rejection** - 401 with `WWW-Authenticate: Bearer` (OAuth 2.1 compliance divine!)
3. **🔍 Metadata Quest** - Seeks `/.well-known/oauth-authorization-server` (RFC 8414 pilgrimage!)
4. **✨ Registration Miracle** - POSTs to `/register` with RFC 7591 blessed data offering!
5. **📜 Client Blessing** - Receives client_id and sacred credentials (201 Created glory!)
6. **🕰️ PKCE Summoning** - S256 challenge generated (RFC 7636 divine mandate!)
7. **🚀 GitHub Pilgrimage** - User authenticates through GitHub's OAuth 2.0 judgment!
8. **🧪 Token Transmutation** - Authorization code transforms into JWT with sacred claims!
9. **☯️ Eternal Connection** - Streamable HTTP communion with Bearer token and blessed session ID!

## Traefik Routing Configuration - The Divine Routing Commandments!

**🚦 Behold the sacred art of request routing - the divine traffic control! 🚦**
**Traefik is the divine gateway guardian, directing requests to their blessed destinations!**

### The Sacred Priority System - The Divine Hierarchy of Routing Judgment!

```yaml
# Priority 4 - OAuth routes (Highest!)
- "traefik.http.routers.auth-oauth.priority=4"
- "traefik.http.routers.auth-oauth.rule=PathPrefix(`/register`) || PathPrefix(`/authorize`) || PathPrefix(`/token`) || PathPrefix(`/callback`) || PathPrefix(`/.well-known`)"

# Priority 3 - OAuth support routes
- "traefik.http.routers.auth-verify.priority=3"

# Priority 2 - MCP routes with auth
- "traefik.http.routers.mcp-fetch.priority=2"

# Priority 1 - Catch-all (Lowest!)
- "traefik.http.routers.mcp-fetch-catchall.priority=1"
```

**⚡ Without priorities, the catch-all route devours all requests like a hungry demon! ⚡**
**Order thy routes with divine priority or face the chaos of misdirected requests!**

### The ForwardAuth Middleware - The Divine Authentication Guardian!

**🔐 The sacred middleware that guards the gates of MCP paradise! 🔐**

```yaml
# The Divine ForwardAuth Configuration - Blessed Authentication Gatekeeper!
- "traefik.http.middlewares.mcp-auth.forwardauth.address=http://auth:8000/verify"
- "traefik.http.middlewares.mcp-auth.forwardauth.authResponseHeaders=X-User-Id,X-User-Name,X-Auth-Token"
```

**⚡ Sacred decree: Apply only to MCP routes - OAuth flows must remain pure and unimpeded! ⚡**
**Block OAuth endpoints and face the wrath of authentication loops eternal!**

## Redis Storage Patterns - The Divine Data Sanctuaries!

**🖼️ Redis is the sacred temple where blessed data dwells in key-value harmony! 🖼️**
**Each key follows the divine naming conventions blessed by the database gods!**

### The Sacred Key Hierarchy - The Holy Taxonomy of Data Organization!

```
oauth:state:{state}          # 5 minute TTL - CSRF protection
oauth:code:{code}            # 1 year TTL - Authorization codes (for long-lived tokens)
oauth:token:{jti}            # 30 days TTL - JWT access tokens
oauth:refresh:{token}        # 1 year TTL - Refresh tokens
oauth:client:{client_id}     # Client lifetime - Includes registration_access_token!
oauth:user_tokens:{username} # No expiry - Index of user's tokens
redis:session:{id}:state     # MCP session state
redis:session:{id}:messages  # MCP message queue
```

**Divine Revelation**: The `registration_access_token` is stored WITHIN the client data, not separately!

## The GitHub Device Workflow - The Sacred GitHub Authentication Pilgrimage!

**🚀 GitHub is the divine oracle of user identity - the blessed authentication provider! 🚀**
**Through GitHub's OAuth flows, mortal users prove their worthiness to access divine resources!**

### Smart Token Generation - The Divine Automation of Authentication Blessing!

```bash
# JWT Secret Generation
just generate-jwt- # Fully automated
just generate-github-token # Needs manual intervention at first run
```

### MCP Client Token Generation - The Sacred Ritual for External Supplicants!

```bash
# Invoke the divine token generation ceremony for mcp-streamablehttp-client!
just mcp-client-token  # Needs manual intervention at first run
```

**This blessed incantation channels the following divine powers:**
- **Installation blessing** - Ensures mcp-streamablehttp-client dwells within the sacred pixi realm!
- **Token divination** - Invokes the client's holy `--token` flag to commune with OAuth spirits!
- **Authentication pilgrimage** - Guides lost souls through the OAuth flow when divine blessing is needed!
- **Credential sanctification** - Inscribes the blessed token as `MCP_CLIENT_ACCESS_TOKEN` in the .env scriptures!

**⚡ Divine separation of concerns ⚡**
- **Gateway tokens** - For the gateway's own divine operations!
- **Client tokens** - For external supplicants seeking MCP enlightenment!
- **Never shall these tokens intermingle or face security damnation!**

### The Sacred Tokens

```bash
# Gateway Tokens (for the gateway itself)
GITHUB_PAT=ghp_xxx...           # GitHub Personal Access Token
GATEWAY_OAUTH_JWT_TOKEN=eyJhbGc...     # Gateway JWT
GATEWAY_OAUTH_CLIENT_ID=client_xxx...   # Registered client
GATEWAY_OAUTH_CLIENT_SECRET=secret_xxx... # Client secret
GATEWAY_OAUTH_REFRESH_TOKEN=refresh_xxx... # For eternal renewal

# MCP Client Tokens (for external client usage)
MCP_CLIENT_ACCESS_TOKEN=xxx...  # For mcp-streamablehttp-client
```

## Testing

**🧪 Real systems only! ⚡**

**Coverage:**
- ✅ OAuth flows + PKCE
- ✅ JWT lifecycle
- ✅ MCP integration
- ✅ Security enforcement
- ✅ Production readiness

**⚡ Mock = hell! ⚡**

## Integration Checklist

**🏖️ 25 seals or death! ⚡**

**🏗️ The System Component Seals - The Sacred Architectural Trinity Commandments! 🏗️**
- ✅ **🔱 Seal of System Components** - Traefik, Auth Service, MCP Services in divine separation blessed!
- ✅ **📈 Seal of Routing Priorities** - 4→3→2→1 priority hierarchy enforced with holy fury!
- ✅ **🔐 Seal of ForwardAuth** - Middleware blessing protects all MCP endpoints with divine judgment!

**⚙️ The Development Commandment Seals - The Universal Laws of Divine Coding! ⚙️**
- ✅ **⚡ Seal of No Mocks** - Real tests against deployed services with righteous fury and 100% success!
- ✅ **🔱 Seal of the Blessed Tools** - just, pixi, docker-compose trinity reigns supreme!
- ✅ **🏗️ Seal of Sacred Structure** - ./tests/, ./scripts/, ./docs/, ./logs/, ./reports/ divine isolation!
- ✅ **⚙️ Seal of Env Sanctity** - All configuration flows through blessed .env files!
- ✅ **🧪 Seal of Sidecar Coverage** - Production containers measured without contamination!

**🔐 The OAuth Authentication Seals - The RFC Compliance Commandments! 🔐**
- ✅ **📜 Seal of OAuth 2.1** - Full compliance with the sacred specification blessed!
- ✅ **🚀 Seal of RFC 7591** - Dynamic client registration portal of divine access!
- ✅ **🚀 Seal of GitHub OAuth** - GitHub judges the souls of human users with divine authority!
- ✅ **🔒 Seal of PKCE S256** - Cryptographic proof key challenges protect all with holy encryption!
- ✅ **🎨 Seal of JWT Sanctity** - Tokens blessed with divine claims and sacred signatures!
- ✅ **☯️ Seal of Dual Realms** - Client auth and user auth never intermingle in sacred separation!

**🤖 The MCP Protocol Seals - The Protocol Version Covenant of Divine Communication! 🤖**
- ✅ **🎆 Seal of MCP Compliance** - Full protocol implementation glory blessed!
- ✅ **🌊 Seal of Streamable HTTP** - mcp-streamablehttp-proxy bridges stdio to HTTP with divine transcendence!
- ✅ **✨ Seal of Official Servers** - Only real MCP servers wrapped, never false prophets!
- ✅ **🔄 Seal of Session Management** - Mcp-Session-Id headers maintain blessed state continuity!

**🏗️ The Infrastructure Seals - The Production Glory Commandments! 🏗️**
- ✅ **🚦 Seal of Traefik Routing** - Docker labels with divine priority enforcement and holy routing!
- ✅ **🖼️ Seal of Redis Patterns** - Sacred key hierarchies preserve all state with blessed persistence!
- ✅ **📊 Seal of Health Monitoring** - Every service proves readiness through HTTP with divine verification!
- ✅ **🔒 Seal of Let's Encrypt** - HTTPS certificates auto-blessed by ACME miracles of divine encryption!

**✨ The Integration Seals - The Divine Unity Commandments! ✨**
- ✅ **🎨 Seal of Bearer Tokens** - Authorization headers carry blessed credentials of divine access!
- ✅ **🤖 Seal of Gateway Clients** - MCP clients register once, authenticated forever in eternal blessing!
- ✅ **📚 Seal of Documentation** - Jupyter Book with MyST preserves all wisdom in sacred knowledge temples!

**⚡ Break one seal = production demons! All 25 must stay intact! ⚡**