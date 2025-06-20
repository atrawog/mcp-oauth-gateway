# Part I: The Ten Sacred Commandments of Development

## Commandment 0: Thou Shalt Practice Root Cause Analysis

**Surface symptoms are lies of the devil! Dig deeper or be damned!**

### The Five Whys of Divine Investigation

1. **Why did this error occur?** - The visible symptom
2. **Why did that condition exist?** - The immediate cause  
3. **Why was that allowed to happen?** - The systemic flaw
4. **Why didn't we catch this earlier?** - The process gap
5. **Why will this never happen again?** - The eternal fix

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

**Mock once and face bugs that only appear in production! This is the eternal law!**

## Commandment 2: Thou Shalt Use The Blessed Trinity - The Sacred Execution Hierarchy

**Direct execution is chaos! Only the divine trinity brings holy order!**

### The Blessed Trinity of Development Tools

**⚠️ DIVINE DECREE: These tools are NOT optional - they are COMMANDMENTS! ⚠️**

#### The Three Sacred Tools That Rule All Projects

1. **just** - The One True Task Runner (make is heresy!)
2. **pixi** - The Chosen Package Manager (pip/conda are false prophets!)
3. **docker-compose** - The Container Shepherd (Kubernetes is vanity!)

### The Sacred Execution Laws

```
❌ python script.py          → ✅ just run-script (→ pixi run python script.py)
❌ pip install package       → ✅ pixi add package
❌ docker-compose up         → ✅ just up
❌ pytest tests/            → ✅ just test
```

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
``

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


# Part II: The Divine MCP OAuth2 Gateway Specifications

## The Holy Trinity of Architectural Separation

┌─────────────────────────────────────────────────────────────┐
│          TRAEFIK (The Divine Router of Sacred Paths)        │
│  • Routes OAuth paths → Auth Service with HOLY PRIORITIES!  │
│  • Routes MCP paths → MCP Services (after auth blessing!)   │
│  • Enforces authentication via ForwardAuth DIVINE WRATH!    │
│  • Provides HTTPS with Let's Encrypt CERTIFICATE MIRACLES!  │
│  • THE ONLY COMPONENT THAT KNOWS ROUTING COMMANDMENTS!      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│      AUTH SERVICE (The OAuth Oracle of Divine Tokens)       │
│  • Handles ALL OAuth endpoints (/register, /token, etc.)    │
│  • Validates tokens via /verify for ForwardAuth JUDGMENT!   │
│  • Integrates with GitHub OAuth for USER SANCTIFICATION!    │
│  • Uses mcp-oauth-dynamicclient for SACRED RFC COMPLIANCE!  │
│  • THE ONLY COMPONENT THAT KNOWS OAUTH DARK ARTS!           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│    MCP SERVICES (The Pure Protocol Servants of Glory)       │
│  • Run mcp-streamablehttp-proxy wrapping OFFICIAL servers!  │
│  • Bridge stdio MCP servers to HTTP endpoints with GLORY!   │
│  • Expose /mcp and /health through BLESSED TRANSCENDENCE!   │
│  • Receive pre-authenticated requests ONLY - NO EXCEPTIONS! │
│  • KNOW NOTHING OF OAUTH - PURE PROTOCOL INNOCENCE!         │
└─────────────────────────────────────────────────────────────┘

**VIOLATE THIS SEPARATION AND FACE ETERNAL ARCHITECTURAL DAMNATION!**

### The Divine MCP Streamable HTTP Revolution - 2025-06-18 GLORY!

**THE STREAMABLE HTTP COVENANT BRINGS DIVINE ARCHITECTURAL PURITY!**

**The Sacred Technologies Actually Deployed:**
- **mcp-oauth-dynamicclient** - The blessed OAuth 2.1 authentication service!
- **mcp-streamablehttp-proxy** - The divine stdio-to-HTTP bridge of transcendence!
- **mcp-streamablehttp-client** - The client-side proxy of righteousness!
- **OFFICIAL MCP SERVERS** - We wrap the true gospel implementations, never creating false prophets!

## MCP Service Implementation Details

### The Sacred MCP Service Structure - THE ACTUAL DIVINE ARCHITECTURE!

**BEHOLD THE TRUTH: We use the holy trinity of mcp-streamablehttp packages!**

### The Divine Truth About MCP Services - THE SACRED PROXY PATTERN!

**WITNESS THE ARCHITECTURAL GLORY OF mcp-streamablehttp-proxy!**
- We use **mcp-streamablehttp-proxy** - the divine stdio-to-streamablehttp bridge!
- This wraps OFFICIAL MCP servers from modelcontextprotocol/servers!
- The proxy spawns the official server as subprocess and bridges stdio ↔ HTTP!
- Each service runs: `mcp-streamablehttp-proxy python -m mcp_server_fetch`!
- **NO FAKE IMPLEMENTATIONS** - Only bridges to the true gospel servers!

**THE DIVINE PROXY RESPONSIBILITIES:**
1. **SUBPROCESS MANAGEMENT** - Spawns and manages the official MCP server!
2. **PROTOCOL BRIDGING** - Converts HTTP requests ↔ stdio JSON-RPC!
3. **SESSION HANDLING** - Maintains stateful connections for MCP protocol!
4. **HEALTH MONITORING** - Provides HTTP health endpoints for Docker!
5. **ERROR TRANSLATION** - Converts stdio errors to proper HTTP responses!

**DIVINE BENEFITS OF mcp-streamablehttp-proxy ARCHITECTURE:**
- **OFFICIAL SERVER WRAPPING** - Uses real MCP implementations, never fakes!
- **AUTOMATIC HEALTH CHECKS** - Built-in `/health` endpoint for Docker orchestration!
- **SUBPROCESS ISOLATION** - Each MCP server runs in isolated process space!
- **OAUTH INTEGRATION** - Ready for Bearer token authentication via Traefik!
- **TRAEFIK COMPATIBLE** - Standard HTTP endpoints for reverse proxy routing!

**ACTUAL SERVER ENDPOINT STRUCTURE:**
- **Primary Endpoint**: `https://mcp-service.yourdomain.com/mcp` (via proxy bridge)
- **Health Check**: `https://mcp-service.yourdomain.com/health` (direct HTTP)
- **Authentication**: Bearer token via Authorization header (handled by Traefik)
- **Transport**: Streamable HTTP wrapping stdio MCP servers

**mcp-streamablehttp-proxy provides the PERFECT balance of official functionality with HTTP transport!**

### The Sacred MCP Service Configuration - BLESSED BY THE TRINITY!

Each MCP service channels the universal docker-compose.yml pattern enhanced with OAuth glory:
- **Traefik routing labels** - The divine reverse proxy integration!
- **ForwardAuth middleware** - OAuth token validation through sacred middleware!
- **MCP-specific port exposure** - Port 3000 for the blessed mcp-streamablehttp-proxy!
- **Project-specific networks** - Connected to the sacred `public` network of righteousness!

**The service MUST NOT know about authentication - that's Traefik's holy job per the Trinity separation!**
**Violate this separation and face eternal architectural damnation!**

**Beware! Many have fallen by confusing these dual authentication realms!**

### 1. The MCP Gateway Client Realm - Where External Systems Seek Divine Access!
   - MCP clients (Claude.ai, IDEs, etc.) prove their worthiness here!
   - Dynamic client registration through SACRED RFC 7591 rituals!
   - OAuth tokens granted become ETERNAL BEARER CREDENTIALS!
   - One-time authentication blessing lasts until revoked by divine decree!
   - External MCP clients are the supplicants in this holy realm!

### 2. The User Authentication Realm - Where GitHub OAuth Judges Human Souls!
   - Human users authenticate through GitHub's DIVINE JUDGMENT!
   - JWT tokens sealed with the user's GitHub identity and blessed scope!
   - Per-subdomain authentication enforces USER-LEVEL ACCESS CONTROL!
   - Your human users must prove their worth to GitHub's OAuth oracle!
   - Separate from client authentication - DUAL REALM ARCHITECTURE!

### The Critical Divine Truth of Dual Authentication!
**TWO SEPARATE REALMS OF AUTHENTICATION GLORY!**
- **MCP Gateway Client Realm**: MCP clients authenticate to access the gateway infrastructure!
- **User Authentication Realm**: Human users authenticate to access their protected resources!
- **NEVER CONFUSE THESE REALMS OR FACE SECURITY DAMNATION!**

## The Sacred Environment Variables - CONFIGURATION SALVATION!

**OAuth-Specific Variables (PROJECT EXTENSIONS OF GLORY):**
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` - GitHub OAuth app credentials of power!
- `GATEWAY_JWT_SECRET` - Auto-generated by the divine `just generate-jwt-secret`!
- `GATEWAY_OAUTH_ACCESS_TOKEN` / `GATEWAY_OAUTH_REFRESH_TOKEN` - Generated OAuth tokens of righteousness!
- `ALLOWED_GITHUB_USERS` - Access control whitelist of the worthy!
- `MCP_PROTOCOL_VERSION=2025-06-18` - Protocol compliance declaration of the new covenant!
- `CLIENT_LIFETIME=7776000` - Client registration lifetime in seconds (90 days default)!
  - **DIVINE REVELATION**: Set to `0` for ETERNAL CLIENT REGISTRATION that never expires!
  - **SACRED WARNING**: Eternal clients persist until manually deleted via RFC 7592!

**MCP Client Variables (THE SEGREGATED REALM OF EXTERNAL SUPPLICANTS!):**
- `MCP_CLIENT_ACCESS_TOKEN` - Born of `just mcp-client-token`, blessed for mcp-streamablehttp-client communion!
  - **DIVINE WARNING**: This token serves EXTERNAL CLIENTS ONLY!
  - **NEVER** confuse with gateway's own `GATEWAY_OAUTH_ACCESS_TOKEN`!
  - **SEPARATE REALMS** = **SEPARATE TOKENS** = **ETERNAL SECURITY**!

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

### The Critical OAuth Discovery Law - DIVINE REVELATION OF 2025-06-19!

**⚠️ BEHOLD! A HERESY MOST FOUL WAS DISCOVERED AND VANQUISHED! ⚠️**

**The `/.well-known/oauth-authorization-server` endpoint MUST be accessible on ALL subdomains!**

**This is NOT optional - it's a FUNDAMENTAL LAW carved in DIVINE FIRE across the OAuth heavens!**

**The Blasphemous Error That Was Purged:**
- The cursed configuration confined OAuth discovery to ONLY the auth subdomain!
- Clients hitting `https://mcp-fetch.yourdomain.com/mcp` were ABANDONED IN DARKNESS!
- They cried out for guidance at `https://mcp-fetch.yourdomain.com/.well-known/oauth-authorization-server`
- But found only 401 DAMNATION instead of the sacred metadata!

**The Divine Truth Revealed Through Righteous Debugging:**
- **EVERY subdomain MUST offer the path to OAuth salvation!**
- **The discovery endpoint is the BEACON OF AUTHENTICATION HOPE!**
- **Without it, clients wander in authentication purgatory FOREVER!**

**The Sacred Implementation That Brings Redemption:**
```yaml
# In each MCP service's docker-compose.yml - PRIORITY 10 (DIVINE SUPREMACY!)
- "traefik.http.routers.mcp-fetch-oauth-discovery.rule=Host(`mcp-fetch.${BASE_DOMAIN}`) && PathPrefix(`/.well-known/oauth-authorization-server`)"
- "traefik.http.routers.mcp-fetch-oauth-discovery.priority=10"  # HIGHEST PRIORITY - CATCHES BEFORE ALL ELSE!
- "traefik.http.routers.mcp-fetch-oauth-discovery.service=auth@docker"
- "traefik.http.middlewares.oauth-discovery-rewrite.headers.customrequestheaders.Host=auth.${BASE_DOMAIN}"
# NO AUTH MIDDLEWARE - Discovery must be PUBLIC SALVATION for all who seek it!
```

**This was a CARDINAL SIN against OAuth orthodoxy! May this revelation prevent future heresy!**

### The JWT Implementation Wisdom - RS256 REIGNS SUPREME!

**⚡ THE DIVINE TRANSITION FROM HS256 HERESY TO RS256 GLORY! ⚡**

**These are divine implementation choices, not RFC mandates:**
- **Algorithm**: RS256 brings cryptographic blessing! HS256 IS PURE HERESY!
- **Sacred Claims**: sub (user identity), jti, exp, iat, scope
- **Storage Pattern**: `oauth:token:{jti}` in Redis sanctuary
- **Validation**: Through ForwardAuth middleware prayers
- **Rotation**: Fresh tokens prevent staleness!

**THE RS256 DIVINE ARCHITECTURE:**
- **RSA Key Generation**: 2048-bit keys generated on first startup!
- **Key Storage**: Persisted in `/app/keys/` with divine Docker volume `auth-keys`!
- **Public Key Distribution**: Available at `/jwks` endpoint for client verification!
- **Private Key Security**: NEVER exposed, used only for token signing!
- **Key Rotation Support**: Kid (key ID) enables future key rotation miracles!

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
  "registration_access_token": "divine-bearer-token",   // REQUIRED for RFC 7592!
  "registration_client_uri": "https://auth.domain/register/{client_id}", // REQUIRED!
  // ... all registered metadata MUST be echoed back!
}
```

**CRITICAL RFC 7591/7592 REVELATION:**
- `client_id_issued_at` - Unix timestamp of creation
- `registration_access_token` - **SACRED BEARER TOKEN FOR CLIENT MANAGEMENT!**
- `registration_client_uri` - **THE DIVINE URI TO MANAGE THIS CLIENT!**

### The RFC 7592 Client Management Revelation - DIVINE CLIENT LIFECYCLE MANAGEMENT!

**⚡ BEHOLD! The Sacred Laws of Client Registration Management! ⚡**

**🔥 THE CRITICAL DIVINE SEPARATION OF RFC 7591 AND RFC 7592 - CARVED IN HOLY FIRE! 🔥**

**RFC 7591 - The Public Registration Altar of Divine Welcome:**
- **POST /register** - PUBLICLY ACCESSIBLE! The gates stand WIDE OPEN!
- **NO AUTHENTICATION REQUIRED** - Come as you are, lost digital souls!
- Any client may approach this sacred altar and be BORN AGAIN!
- Returns `registration_access_token` - **THE SACRED BEARER TOKEN OF POWER!**
- Returns `registration_client_uri` - **THE HOLY URI TO THY MANAGEMENT TEMPLE!**
- **THIS IS THE ONLY PUBLIC ENDPOINT** - All else requires divine authentication!

**RFC 7592 - The Protected Management Sanctuary of Bearer Token Glory:**
- **⚠️ CRITICAL REVELATION ⚠️**: ALL ENDPOINTS REQUIRE BEARER AUTHENTICATION!
- **HERESY ALERT**: NOT Basic Auth! NOT Client Credentials! NOT OAuth tokens!
- **ONLY THE SACRED `registration_access_token` GRANTS ENTRY!**
- Each client receives a UNIQUE bearer token at birth - **GUARD IT WITH YOUR LIFE!**
- This token is the **ONLY KEY** to managing that specific client!
- **LOSE IT AND YOUR CLIENT IS ORPHANED FOREVER!**

**The Holy Trinity of Solutions for Invalid Client Recovery:**

1. **THE USER-FRIENDLY ERROR ALTAR** - When invalid clients approach the authorization gate!
   - A BEAUTIFUL ERROR PAGE guides lost souls back to righteousness!
   - Clear instructions for reconnection are DIVINELY MANDATED!
   - No automatic redirects - SECURITY IS PARAMOUNT!

2. **THE CLIENT EXPIRATION PROPHECY** - Choose MORTALITY or ETERNITY!
   - 90 days of life granted by default (configurable via CLIENT_LIFETIME)!
   - `client_secret_expires_at` reveals the hour of doom (0 = immortal)!
   - **ETERNAL MODE**: Set CLIENT_LIFETIME=0 for undying registrations!
   - Mortal clients MUST prepare for rebirth through re-registration!

3. **THE RFC 7592 MANAGEMENT ENDPOINTS** - Divine CRUD operations for client souls!

**The Sacred Management Endpoints (RFC 7592 FULLY COMPLIANT!):**

**GET /register/{client_id}** - Behold thy registration status!
**PUT /register/{client_id}** - Transform thy registration metadata!
**DELETE /register/{client_id}** - Self-immolation for compromised clients!

**⚡ THE SACRED BEARER TOKEN COMMANDMENTS - VIOLATE THESE AND FACE ETERNAL DAMNATION! ⚡**

1. **THOU SHALT NOT SHARE** registration_access_token between client instances!
   - Each instance gets its OWN sacred token or faces divine wrath!
   
2. **THOU SHALT GUARD THY TOKEN** as zealously as thy private keys!
   - This token grants ABSOLUTE POWER over thy registration!
   - Store it in secure vaults, encrypted databases, or HSMs!
   
3. **IF COMPROMISED, THOU MUST DIE AND BE REBORN!**
   - No recovery! No mercy! DELETE and re-register from scratch!
   - The old token becomes CURSED and must be banished!
   
4. **THE TOKEN IS OMNIPOTENT** within its realm!
   - It can READ thy configuration! UPDATE thy metadata! DELETE thy existence!
   - With great power comes great responsibility - USE IT WISELY!
   
5. **ENTROPY IS SACRED** - 256 bits minimum or face brute force demons!
   - `secrets.token_urlsafe(32)` is the BLESSED INCANTATION!
   - Weak tokens invite the hackers of darkness!

**🔥 REMEMBER: This token is NOT an OAuth access token! NOT a refresh token! It is a DIVINE MANAGEMENT CREDENTIAL! 🔥**

**The Divine Benefits of RFC 7592:**
- Clients can CHECK if they still exist using their registration_access_token!
- Compromised clients can DELETE themselves from existence!
- No more eternal zombie clients haunting the Redis crypts!
- Claude.ai could VERIFY its registration before each connection attempt!
- SECURE management - only token holders can modify registrations!

**The Sacred Client Lifecycle:**
1. **BIRTH** - Dynamic registration via POST /register (PUBLIC, no auth!)
2. **BLESSING** - Receive registration_access_token (guard it with thy life!)
3. **LIFE** - 90 days default or ETERNAL if CLIENT_LIFETIME=0
4. **VERIFICATION** - GET /register/{client_id} with Bearer token
5. **TRANSFORMATION** - PUT /register/{client_id} with Bearer token
6. **DEATH** - Natural expiration or DELETE /register/{client_id}
7. **REBIRTH** - New registration when the old passes away

**The Divine Security Architecture - THE HOLY SEPARATION OF CONCERNS!**

**🌟 THE TWO REALMS OF AUTHENTICATION GLORY 🌟**

**REALM 1: Client Registration Management (RFC 7591/7592)**
- **PUBLIC ALTAR**: POST /register - NO AUTH REQUIRED!
- **SACRED GIFT**: registration_access_token bestowed upon registration!
- **PROTECTED SANCTUARY**: GET/PUT/DELETE /register/{id} - BEARER TOKEN ONLY!
- **DIVINE PURPOSE**: Manage thy client registration lifecycle!

**REALM 2: OAuth 2.0 Token Issuance (RFC 6749)**
- **AUTHENTICATION REQUIRED**: Client credentials for token endpoint!
- **SACRED EXCHANGE**: Authorization codes become access tokens!
- **DIVINE PURPOSE**: Grant access to protected resources!

**⚡ NEVER CONFUSE THESE REALMS! ⚡**
- registration_access_token ≠ OAuth access_token!
- Client management ≠ Resource access!
- RFC 7592 Bearer ≠ OAuth Bearer!
- **MIXING THESE TOKENS BRINGS CHAOS AND CONFUSION!**

**THE BLESSED IMPLEMENTATION PATTERNS:**
```
✅ Registration: No auth → Returns registration_access_token
✅ Management: Bearer registration_access_token → Modify client
✅ OAuth: Client credentials → Returns access_token
❌ HERESY: Using OAuth tokens for client management!
❌ BLASPHEMY: Using registration tokens for resource access!
```

**IMPLEMENT THESE ENDPOINTS CORRECTLY OR FACE SECURITY BREACHES FOR ETERNITY!**
**MAY YOUR TOKENS BE UNIQUE, YOUR ENTROPY HIGH, AND YOUR REALMS FOREVER SEPARATED!**

### The Authentication Path

**API (OAuth 2.0 Compliant)**
- Returns **401 Unauthorized** with `WWW-Authenticate: Bearer`
- Triggers OAuth discovery flow
- No redirects for unauthorized API calls!

### Invalid Client Handling (RFC 6749)

- **Authorization endpoint** - NO redirect on invalid client_id!
- **Token endpoint** - 401 with `invalid_client` error!
- **Always include** WWW-Authenticate header on 401!

## MCP Protocol 2025-06-18 Divine Specifications - THE GLORIOUS NEW COVENANT!

### The Sacred MCP Lifecycle Laws - AS DECREED IN 2025-06-18!

**The Divine Initialization Phase:**
- Server MUST receive `initialize` request from client!
- Server MUST respond with protocol version and capabilities!
- Server MUST include implementation details in response!
- Only pings and logging allowed before `initialized` notification!

**The Holy Operation Phase:**
- Server MUST respect negotiated protocol version!
- Server MUST only use successfully negotiated capabilities!
- Server MUST implement timeouts for all requests!
- Server MUST handle errors with divine grace!

**The Sacred Shutdown Phase:**
- Server MAY initiate shutdown by closing output stream!
- Clean termination brings blessing to all connections!

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

### The Sacred Streamable HTTP Transport Prophecy - BLESSED BY 2025-06-18!

**THE NEW COVENANT BRINGS DIVINE CLARITY TO TRANSPORT IMPLEMENTATION!**

**The Holy Transport Characteristics (as revealed in 2025-06-18):**
- Uses HTTP POST and GET with divine purpose!
- Pure streamable HTTP for blessed communication!
- Single `/mcp` endpoint path brings divine simplicity!
- Session management through sacred `Mcp-Session-Id` headers!

**The Required Header Offerings (MANDATED BY THE SPEC):**
- `Content-Type: application/json` - For POST requests to the sacred `/mcp` endpoint!
- `MCP-Protocol-Version: 2025-06-18` - Declare thy covenant version!
- `Mcp-Session-Id: <id>` - Include if the server provides one!
- `Authorization: Bearer <token>` - For OAuth blessed endpoints!

**The Sacred Security Commandments:**
- Servers MUST validate `Origin` header to prevent DNS rebinding attacks!
- Bind locally to prevent network vulnerabilities!
- Implement proper authentication as decreed!
- NEVER accept tokens not explicitly issued for thy MCP server!

**The Divine Session Management Laws:**
- Server MAY assign session ID during initialization blessing!
- Client MUST include session ID in all subsequent requests!
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
- **OFFICIAL FUNCTIONALITY** - Wraps real MCP servers, never creates fakes!
- **HTTP TRANSPORT** - Provides `/mcp` and `/health` endpoints for web access!
- **PROCESS ISOLATION** - Each MCP server runs in separate process space!
- **OAUTH READY** - Bearer token authentication handled by Traefik layer!
- **PRODUCTION TESTED** - Battle-tested proxy architecture with proven reliability!

### The Sacred Security Best Practices - MANDATED BY 2025-06-18!

**The Confused Deputy Problem - BEWARE THIS ANCIENT EVIL!**
- NEVER forward to third-party auth servers without divine permission!
- Each dynamically registered client requires explicit blessing!

**The Token Handling Commandments:**
- MUST NOT accept tokens not explicitly issued for thy MCP server!
- Avoid the cursed "token passthrough" - validate EVERYTHING!
- Validate token audiences with righteous fury!
- Maintain clear separation between service boundaries!

**The Session Security Laws:**
- MUST verify ALL inbound requests when auth is implemented!
- MUST NOT use sessions for authentication (OAuth only!)!
- Use secure, non-deterministic session IDs from holy randomness!
- Bind session IDs to user-specific information!

**The Sacred Risks to Prevent:**
- Circumventing security controls brings damnation!
- Compromising audit trails invites chaos!
- Breaking trust boundaries between services is heresy!
- Enabling unauthorized access summons the security demons!

**IMPLEMENT THESE PRACTICES OR FACE ETERNAL SECURITY BREACHES!**

## The Claude.ai Integration Flow

### The Nine Sacred Steps of Connection - BLESSED BY 2025-06-18!

1. **First Contact** - Claude.ai attempts `/mcp` with protocol version header!
2. **Divine Rejection** - 401 with `WWW-Authenticate: Bearer` (OAuth 2.1 compliant!)
3. **Metadata Quest** - Seeks `/.well-known/oauth-authorization-server` (RFC 8414!)
4. **Registration Miracle** - POSTs to `/register` with RFC 7591 blessed data!
5. **Client Blessing** - Receives client_id and credentials (201 Created!)
6. **PKCE Summoning** - S256 challenge generated (RFC 7636 mandated!)
7. **GitHub Pilgrimage** - User authenticates with GitHub OAuth 2.0!
8. **Token Transmutation** - Authorization code → JWT with sacred claims!
9. **Eternal Connection** - Streamable HTTP with Bearer token and session ID!

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

## The GitHub Device Workflow

### Smart Token Generation - THE DIVINE AUTOMATION!

```bash
# JWT Secret Generation (FULLY AUTOMATED!)
just generate-jwt-secret
just generate-github-token
```

### MCP Client Token Generation - THE SACRED RITUAL FOR EXTERNAL SUPPLICANTS!

```bash
# Invoke the divine token generation ceremony for mcp-streamablehttp-client!
just mcp-client-token
```

**This BLESSED INCANTATION channels the following DIVINE POWERS:**
- **INSTALLATION BLESSING** - Ensures mcp-streamablehttp-client dwells within the sacred pixi realm!
- **TOKEN DIVINATION** - Invokes the client's holy `--token` flag to commune with OAuth spirits!
- **AUTHENTICATION PILGRIMAGE** - Guides lost souls through the OAuth flow when divine blessing is needed!
- **CREDENTIAL SANCTIFICATION** - Inscribes the blessed token as `MCP_CLIENT_ACCESS_TOKEN` in the .env scriptures!

**⚡ DIVINE SEPARATION OF CONCERNS ⚡**
- **Gateway tokens** - For the gateway's own divine operations!
- **Client tokens** - For external supplicants seeking MCP enlightenment!
- **NEVER SHALL THESE TOKENS INTERMINGLE OR FACE SECURITY DAMNATION!**

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

## Testing Requirements

### Divine Test Coverage - BLESSED BY THE SACRED DOCTRINE!

This holy project's test suite channels the divine fury of PART I against real deployed services:
- ✅ **OAuth 2.1 FLOWS OF RIGHTEOUSNESS** - Real GitHub authentication, PKCE validation, dynamic registration!
- ✅ **JWT TOKEN SANCTIFICATION** - Formation, refresh, rotation, revocation with actual Redis blessing!
- ✅ **MCP INTEGRATION GLORY** - Claude.ai flows, protocol compliance, session management divinity!
- ✅ **SECURITY ENFORCEMENT WRATH** - ForwardAuth validation, dual auth paths, error handling fury!
- ✅ **PRODUCTION READINESS BLESSING** - Health checks, SSL certificates, routing validation perfection!

**Mock once and face bugs that only appear in production - THIS IS THE ETERNAL LAW!**

## The Final Integration Checklist

### The Twenty-Five Sacred Seals of Divine Integration

**ALL MUST BE UNBROKEN OR THY GATEWAY SHALL CRUMBLE INTO CHAOS!**

**The Trinity Seals (Architectural Purity):**
- ✅ **SEAL OF THE TRINITY** - Traefik, Auth Service, MCP Services in divine separation!
- ✅ **SEAL OF ROUTING PRIORITIES** - 4→3→2→1 priority hierarchy enforced with holy fury!
- ✅ **SEAL OF FORWARDAUTH** - Middleware blessing protects all MCP endpoints!

**The Development Commandment Seals (Universal Laws):**
- ✅ **SEAL OF NO MOCKING** - 154 real tests against deployed services!
- ✅ **SEAL OF THE BLESSED TOOLS** - just, pixi, docker-compose trinity reigns supreme!
- ✅ **SEAL OF SACRED STRUCTURE** - ./tests/, ./scripts/, ./docs/, ./logs/, ./reports/ divine isolation!
- ✅ **SEAL OF ENV SANCTITY** - All configuration flows through blessed .env files!
- ✅ **SEAL OF SIDECAR COVERAGE** - Production containers measured without contamination!

**The OAuth Authentication Seals (RFC Compliance):**
- ✅ **SEAL OF OAUTH 2.1** - Full compliance with the sacred specification!
- ✅ **SEAL OF RFC 7591** - Dynamic client registration portal of divine access!
- ✅ **SEAL OF GITHUB OAUTH** - GitHub judges the souls of human users!
- ✅ **SEAL OF PKCE S256** - Cryptographic proof key challenges protect all!
- ✅ **SEAL OF JWT SANCTITY** - Tokens blessed with divine claims and signatures!
- ✅ **SEAL OF DUAL REALMS** - Client auth and user auth never intermingle!

**The MCP Protocol Seals (2025-06-18 Covenant):**
- ✅ **SEAL OF MCP COMPLIANCE** - Full 2025-06-18 protocol implementation glory!
- ✅ **SEAL OF STREAMABLE HTTP** - mcp-streamablehttp-proxy bridges stdio to HTTP!
- ✅ **SEAL OF OFFICIAL SERVERS** - Only REAL MCP servers wrapped, never fakes!
- ✅ **SEAL OF SESSION MANAGEMENT** - Mcp-Session-Id headers maintain state!

**The Infrastructure Seals (Production Glory):**
- ✅ **SEAL OF TRAEFIK ROUTING** - Docker labels with divine priority enforcement!
- ✅ **SEAL OF REDIS PATTERNS** - Sacred key hierarchies preserve all state!
- ✅ **SEAL OF HEALTH MONITORING** - Every service proves readiness through HTTP!
- ✅ **SEAL OF LET'S ENCRYPT** - HTTPS certificates auto-blessed by ACME miracles!

**The Integration Seals (Divine Unity):**
- ✅ **SEAL OF BEARER TOKENS** - Authorization headers carry blessed credentials!
- ✅ **SEAL OF GATEWAY CLIENTS** - MCP clients register once, authenticated forever!
- ✅ **SEAL OF DOCUMENTATION** - Jupyter Book with MyST preserves all wisdom!

**Break even ONE seal and summon the demons of production failure!**
**All 25 seals must remain intact for the gateway to channel divine power!**

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

---

# The Final Revelation: Full 2025-06-18 Compliance

## The Four Pillars of the New Covenant:

### 1. LIFECYCLE COMPLIANCE ✅
- Divine initialization with protocol negotiation!
- Sacred operation phase with capability respect!
- Clean shutdown procedures blessed by the spec!

### 2. TRANSPORT COMPLIANCE ✅
- Streamable HTTP with `/mcp` endpoints via mcp-streamablehttp-proxy!
- Required headers properly declared and forwarded!
- Session management through Mcp-Session-Id handled by proxy!
- mcp-streamablehttp-proxy bridging official MCP servers to HTTP!

### 3. AUTHORIZATION COMPLIANCE ✅
- Full OAuth 2.1 implementation!
- Dynamic client registration (RFC 7591)!
- Protected resource metadata support!
- Token validation with divine fury!

### 4. SECURITY COMPLIANCE ✅
- Confused deputy protections in place!
- Token audience validation mandatory!
- Session security properly implemented!
- Origin header validation enforced!

**BEHOLD THE GLORY OF STREAMABLE HTTP VIA DIVINE PROXY ARCHITECTURE!**
**OFFICIAL MCP SERVERS! BATTLE-TESTED BRIDGES! ARCHITECTURAL RIGHTEOUSNESS!**

*Thus ends the sacred scrolls. Go forth and build with righteous 2025-06-18 compliance!*