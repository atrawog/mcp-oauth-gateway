# Part I: The Ten Sacred Commandments of Divine Development

## Commandment 0: Thou Shalt Practice Root Cause Analysis with Holy Fervor

**🔥 BEHOLD! Surface symptoms are the DEVIL'S DECEPTIONS sent to lead thee astray! 🔥**
**Dig deeper into the sacred depths or be ETERNALLY DAMNED to debugging purgatory!**

### The Five Whys of Divine Investigation - THE HOLY INQUISITION OF TRUTH!

1. **Why did this unholy error manifest?** - Witness the visible symptom of corruption!
2. **Why did this cursed condition exist?** - Uncover the immediate cause of blasphemy!  
3. **Why was this abomination allowed to flourish?** - Expose the systemic flaw of heresy!
4. **Why didn't our sacred vigilance catch this earlier?** - Reveal the process gap of negligence!
5. **Why will this NEVER pollute our realm again?** - Forge the eternal fix of righteousness!

**⚡ SACRED DECREE: Fix symptoms without finding root causes and be CURSED to debug in the fires of eternal torment! ⚡**
**The lazy developer who patches without understanding shall wander the debugging wilderness for forty years!**

## Commandment 1: Thou Shalt Never Mock - Test Real or Test Nothing, Ye Faithless Coders!

**🔥 THE MOST SACRED LAW OF ALL - CARVED WITH DIVINE LIGHTNING ACROSS THE CODING HEAVENS! 🔥**
**This HOLY COMMANDMENT applies to EVERY project - NO EXCEPTIONS! NO EXCUSES! NO MERCY!**

### The Holy Testing Dogma - THE ORTHODOX CREED OF RIGHTEOUS VERIFICATION!

- **⚡ NO MOCKS! NO STUBS! NO FAKES! ⚡** - These are FALSE PROPHETS leading souls to damnation!
- **Test against REAL deployed systems** or face eternal debugging in the lake of fire!
- **Every test must verify COMPLETE end-to-end functionality** - partial tests are Satan's whispers!
- **Tests that only check connectivity are WORTHLESS PRAYERS** - they mock the divine truth!
- **Internal services are testable through REAL API boundaries** - no shortcuts to salvation!

**⚡ DIVINE WRATH UNLEASHED: Mock once and face bugs that ONLY appear in production! ⚡**
**This is the ETERNAL LAW - written in the blood of failed deployments!**
**Those who mock shall be mocked by production failures for all eternity!**

## Commandment 2: Thou Shalt Worship The Blessed Trinity - The Sacred Execution Hierarchy of Divine Order!

**🔥 BEHOLD! Direct execution is CHAOS unleashed by the coding demons! 🔥**
**Only the BLESSED TRINITY brings HOLY ORDER to the digital realm!**

### The Blessed Trinity of Development Tools - THE DIVINE TRIUMVIRATE OF RIGHTEOUSNESS!

**⚠️ THUNDEROUS DIVINE DECREE: These tools are NOT optional suggestions - they are SACRED COMMANDMENTS etched in stone! ⚠️**
**Violate this trinity and be cast into the pit of dependency hell!**

#### The Three Sacred Tools That Rule All Projects with Divine Authority

1. **🛠️ just** - The ONE TRUE TASK RUNNER, Blessed Orchestrator of Commands! (make is ancient heresy!)
2. **📦 pixi** - The CHOSEN PACKAGE MANAGER, Divine Guardian of Dependencies! (pip/conda are false prophets spreading chaos!)
3. **🐳 docker-compose** - The CONTAINER SHEPHERD, Sacred Orchestrator of Services! (Kubernetes is vanity and over-engineering!)

### The Sacred Execution Laws - CARVED IN DIVINE CODE!

**⚡ THE RIGHTEOUS PATH vs THE HERETICAL WAYS ⚡**

```
❌ BLASPHEMY: python script.py          → ✅ SALVATION: just run-script (→ pixi run python script.py)
❌ HERESY: pip install package          → ✅ RIGHTEOUSNESS: pixi add package
❌ CHAOS: docker-compose up            → ✅ DIVINE ORDER: just up
❌ DAMNATION: pytest tests/            → ✅ BLESSED TESTING: just test
```

**Use the heretical commands and face the wrath of environment inconsistencies!**

## Commandment 3: Thou Shalt Structure Thy Divine Temple with Sacred Isolation and Holy Segregation!

**🏛️ BEHOLD! Each service is a HOLY SANCTUARY blessed by the gods of architecture! 🏛️**
**This divine structure is MANDATORY for ALL projects - NO EXCEPTIONS OR FACE ARCHITECTURAL DAMNATION!**

### The Divine Directory Laws - THE SACRED ARCHITECTURAL COMMANDMENTS! (Universal for Every Project Under Heaven)

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

## Commandment 4: Thou Shalt Configure ONLY Through Sacred .env Files - The Divine Configuration Gospel!

**🔥 HARDCODED VALUES ARE THE MARK OF THE BEAST - DAMNATION IN EVERY PROJECT! 🔥**
**Those who hardcode shall be cursed with environment-specific bugs for all eternity!**

### The Sacred .env Laws - THE HOLY SCRIPTURE OF CONFIGURATION! (Universal Across All Codebases)

- **⚡ ALL configuration flows through .env files ⚡** - Development AND production, blessed be their names!
- **⚡ NO defaults in code ⚡** - Every value must be EXPLICITLY BLESSED by divine configuration!
- **⚡ .env files for EVERYTHING ⚡** - Local, staging, AND production environments bow before this law!
- **⚡ VALIDATE all variables at startup ⚡** - Missing config must FAIL FAST or face the wrath of runtime errors!

### The Divine .env Loading Pattern

```justfile
# FIRST LINE of every justfile!
set dotenv-load := true
``

**🔒 THE SACRED PRODUCTION .env MANAGEMENT RITUALS: 🔒**
- **Store .env.example in git** (with blessed dummy values as divine templates!)
- **Real .env files BIRTHED by deployment pipeline** (the sacred automation ceremonies!)
- **Secrets injected by CI/CD** into production .env through divine pipeline blessings!
- **⚡ NEVER EVER hardcode ANYTHING ⚡** - not even "sensible defaults" - ALL IS HERESY!

**⚡ CURSE OF THE HARDCODED: Hardcode configuration in ANY project and face the ETERNAL CURSE of environment-specific bugs! ⚡**
**Your code shall break in staging! Fail in production! And confound thee in development!**

## Commandment 5: Thou Shalt Use Docker-Compose for Sacred Service Isolation - The Divine Container Orchestration!

**🐳 DOCKER-COMPOSE IS THE DIVINE ORCHESTRATOR OF HOLY CONTAINERS! 🐳**
**All other ways lead to CHAOS, MADNESS, and deployment damnation!**

### The Distributed Docker-Compose Laws - THE SACRED CONTAINER COMMANDMENTS!

- **⚡ Each service OWNS its docker-compose.yml ⚡** - Independence is SACRED and must never be violated!
- **⚡ ONE root docker-compose.yml to unite them ⚡** - But NOT to define them - separation is divine!
- **⚡ Networks connect the isolated ⚡** - `public` is the BLESSED BRIDGE between sacred realms!
- **⚡ Volumes preserve state ⚡** - But share sparingly, for promiscuity breeds corruption!

### The Sacred Orchestration Structure

```
service-a/
  └── docker-compose.yml    # Service A's complete definition
service-b/
  └── docker-compose.yml    # Service B's complete definition
docker-compose.yml          # The root coordinator only!
```

### The Divine Orchestration Commands - THE SACRED CONTAINER INVOCATIONS!

```bash
# THE HOLY COMMANDMENTS OF CONTAINER ORCHESTRATION
just network-create         # Create the sacred shared network of divine communication!
just up                    # RESURRECT all services to glorious life!
just rebuild service-a     # Rebuild individual service with divine fury!
just down                  # Graceful shutdown - the peaceful death of containers!

# ⚡ FORBIDDEN PRACTICES - THE HERETICAL WAYS OF DAMNATION! ⚡
❌ BLASPHEMY: docker run              # Raw chaos without orchestration!
❌ HERESY: kubernetes apply        # Overengineering vanity for most projects!
❌ ANCIENT EVIL: systemd services        # The deprecated ways of the elders!
```

**Use these forbidden commands and face the wrath of inconsistent deployments!**

### The Blessed docker-compose.yml Pattern - THE DIVINE CONTAINER SCRIPTURE!

```yaml
# THE SACRED DOCKER-COMPOSE TEMPLATE OF RIGHTEOUSNESS
services:
  service-name:
    build: .               # Build from Dockerfile - the sacred image creation ritual!
    networks:
      - public             # Connect to the sacred network of divine communication!
    healthcheck:           # ⚡ MANDATORY FOR ALL SERVICES - NO EXCEPTIONS! ⚡
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s        # The divine heartbeat frequency!
      timeout: 10s         # Patience of the gods!
      retries: 3           # Trinity of redemption attempts!
      start_period: 40s    # Grace period for the newborn container!
```

**Omit healthchecks and face the curse of unknown container states!**

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

## Commandment 7: Thou Shalt Trust ONLY Docker Healthchecks for Sacred Readiness - Death to Sleep Commands!

**😈 ARBITRARY SLEEP COMMANDS ARE THE DEVIL'S TIMING SENT TO TORMENT THY DEPLOYMENTS! 😈**
**They are SATAN'S LIES masquerading as timing solutions!**

### The Healthcheck Gospels - THE SACRED SCRIPTURE OF CONTAINER READINESS! (Mandatory for All Services)

- **⚡ EVERY docker-compose service MUST have a healthcheck ⚡** - NO EXCEPTIONS OR FACE DEPLOYMENT HELL!
- **⚡ Internal health is NOT ENOUGH ⚡** - Services must PROVE their external readiness to the world!
- **⚡ CHECK the complete request path ⚡** - Partial checks bring FALSE CONFIDENCE and production lies!
- **⚡ Startup periods are DIVINE PATIENCE ⚡** - Rush not the sacred initialization ceremonies!
- **⚡ This applies to databases, APIs, workers, and ALL containers ⚡** - NONE SHALL BE EXEMPT!

### The Readiness Verification Hierarchy - THE DIVINE LADDER OF CONTAINER BLESSING!

1. **💪 Service Internal Health** - Can the blessed service process divine requests?
2. **🔗 Dependency Connectivity** - Can it commune with its sacred dependencies?
3. **✅ Full Request Validation** - Does the COMPLETE chain work in holy harmony?
4. **🎨 Business Logic Verification** - Can it perform its ACTUAL divine purpose?

**⚡ THE CURSE OF SLEEP: Use sleep instead of healthchecks in ANY project and face RANDOM TIMING FAILURES for ALL ETERNITY! ⚡**
**Thy containers shall start in chaos! Thy services fail unpredictably! And thy deployments become a lottery of doom!**

## Commandment 8: Thou Shalt Segregate Logs into Sacred Archives - The Divine Chronicle of System Events!

**📜 SCATTERED LOGS ARE LOST WISDOM FLOATING IN THE DIGITAL VOID! 📜**
**They are the CURSED FRAGMENTS of knowledge that mock thy debugging efforts!**

### The Logging Commandments - THE UNIVERSAL LAW OF DIVINE RECORD KEEPING!

- **⚡ ALL projects must use ./logs/ ⚡** - This directory is SACRED GROUND blessed by debugging angels!
- **⚡ CENTRALIZE all logs ⚡** - ONE directory to rule them all, one path to find them!
- **⚡ STRUCTURE by service and level ⚡** - Divine organization prevents the chaos of scattered wisdom!
- **⚡ INCLUDE context in every line ⚡** - Isolated messages help NO ONE and mock the divine truth!

### The Sacred Log Hierarchy - THE DIVINE DIRECTORY TEMPLE OF TRUTH! (Required Structure)

```
logs/                     # ⚡ MANDATORY in every project - THE HOLY ARCHIVE! ⚡
├── service-a/
│   ├── error.log        # 🔥 The SINS and transgressions of service A!
│   ├── info.log         # 📜 The righteous DEEDS and events of service A!
│   └── debug.log        # 🧠 The inner THOUGHTS and contemplations of service A!
├── service-b/
│   └── ...              # Each service CONFESSES separately in divine isolation!
└── app.log              # For blessed single-service projects!
```

**⚡ VIOLATE THIS STRUCTURE AND LOSE THY DEBUGGING SANITY! ⚡**

## Commandment 9: Thou Shalt Document with Sacred Jupyter Book and Blessed MyST - The Divine Documentation Gospel!

**📚 JUPYTER BOOK 2 IS THE ONLY BLESSED DOCUMENTATION SYSTEM ANOINTED BY THE CODING GODS! 📚**
**All other documentation tools are HERETICAL ABOMINATIONS!**

### The Documentation Commandments - THE SACRED SCRIPTURE OF KNOWLEDGE PRESERVATION!

- **⚡ JUPYTER BOOK 2 or eternal confusion ⚡** - Sphinx alone is INSUFFICIENT and leads to documentation damnation!
- **⚡ MyST Markdown is the SACRED FORMAT ⚡** - RST is the old testament, outdated and forsaken!
- **⚡ ALL docs in ./docs/ ⚡** - This structure is DIVINELY ORDAINED by the architecture angels!
- **⚡ _config.yml and _toc.yml ⚡** - The TWIN PILLARS of divine organization supporting the documentation temple!

### The Sacred Documentation Structure - THE DIVINE TEMPLE OF KNOWLEDGE!

```
docs/                    # ⚡ THE HOLY DOCUMENTATION SANCTUARY! ⚡
├── _config.yml      # 📜 Jupyter Book configuration GOSPEL - the sacred settings!
├── _toc.yml         # 📚 Table of contents SCRIPTURE - the divine navigation!
├── index.md         # ✨ The PRIMARY REVELATION (MyST format blessed!)
├── api/             # 🚀 API documentation TEMPLE (MyST format sanctified!)
├── guides/          # 🎯 User guidance SANCTUARY (MyST format divine!)
└── architecture/    # 🏗️ System design CATHEDRAL (MyST format holy!)
```

**⚡ USE ANY OTHER FORMAT AND FACE DOCUMENTATION CHAOS! ⚡**

## ⚡ The Universal Application of These Sacred Commandments - THE ETERNAL LAWS! ⚡

**🌍 THESE TEN COMMANDMENTS ARE NOT MERE PROJECT-SPECIFIC GUIDELINES - THEY ARE UNIVERSAL LAWS GOVERNING ALL CODE! 🌍**
**They transcend language, framework, and project type - ALL SHALL BOW BEFORE THEIR DIVINE AUTHORITY!**

### The Sacred Tools Are Mandatory Everywhere - THE DIVINE TRINITY RULES ALL!

```bash
# ⚡ REQUIRED IN EVERY PROJECT'S ROOT - THE HOLY QUARTET! ⚡
justfile               # 📜 The book of divine commands!
pixi.toml             # 📦 The package prophecy of dependencies!
.env                  # ⚙️ The configuration scripture of truth!
docker-compose.yml    # 🐳 The orchestration gospel of containers!

# ⚡ REQUIRED DIRECTORY STRUCTURE - THE SACRED ARCHITECTURE! ⚡
./tests/              # 🧪 Pytest tests ONLY - the verification temple!
./scripts/            # 📜 Python scripts for just commands - the automation sanctuary!
./docs/               # 📚 Jupyter Book documentation - the knowledge cathedral!
./logs/               # 📄 Centralized logging - the divine record archive!
```

**⚡ BLASPHEMOUS HERESY: Claim these don't apply to your project type and face the ETERNAL WRATH of unmaintainable code! ⚡**
**Thy codebase shall crumble! Thy deployments fail! And thy debugging sessions last unto the end of days!**


# Part II: The Divine MCP OAuth2 Gateway Specifications - THE SACRED ARCHITECTURE OF AUTHENTICATION!

**🏗️ BEHOLD THE HOLY BLUEPRINT OF THE DIVINE GATEWAY - BLESSED BY THE CODING GODS! 🏗️**
**These specifications are carved in the eternal stone of RFC compliance and blessed by the saints of security!**

## The Holy Trinity of Architectural Separation - THE SACRED THREE-TIER DIVINE HIERARCHY!

**🔱 WITNESS THE BLESSED SEPARATION OF DIVINE CONCERNS! 🔱**
**Each tier serves its sacred purpose in the grand architecture of authentication!**

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

**⚡ DIVINE WRATH UPON THE HERETICS! ⚡**
**VIOLATE THIS SACRED SEPARATION AND FACE ETERNAL ARCHITECTURAL DAMNATION!**
**Thy gateway shall become a MONOLITHIC ABOMINATION! Thy security shall crumble! And thy OAuth flows shall be CURSED with unholy coupling!**

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

## The Sacred Environment Variables - THE DIVINE CONFIGURATION GOSPEL OF SALVATION!

**⚙️ BEHOLD THE HOLY ENVIRONMENT VARIABLES - THE SACRED KEYS TO AUTHENTICATION PARADISE! ⚙️**

**⚡ OAuth-Specific Variables - THE PROJECT EXTENSIONS OF DIVINE GLORY! ⚡**
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

## OAuth 2.1 and RFC 7591 Divine Requirements - THE SACRED PROTOCOLS OF AUTHENTICATION!

**📜 THESE ARE NOT MERE SUGGESTIONS - THEY ARE DIVINE COMMANDMENTS WRITTEN IN RFC FIRE! 📜**
**Violate these protocols and face the wrath of authentication demons!**

### The Sacred OAuth Endpoints - THE DIVINE GATEWAYS TO AUTHENTICATION PARADISE!

**🚀 THE HOLY MANDATE OF RFC 7591 - CARVED IN AUTHENTICATION STONE! 🚀**
- `/register` - The Divine Registration Portal
  - MUST accept HTTP POST messages only!
  - MUST use `application/json` content type!
  - MUST be protected by TLS (HTTPS required)!
  - MUST return HTTP 201 Created on success!
  - MUST return HTTP 400 Bad Request on errors!

**⚡ THE STANDARD OAUTH 2.0 SACRAMENTS - THE HOLY TRINITY OF AUTHENTICATION! ⚡**
- **🚾 `/authorize`** - The divine portal to the authentication realm of judgment!
- **🧪 `/token`** - The sacred transmutation chamber where codes become tokens!
- **🔄 `/callback`** - The blessed return path of authentication pilgrimage!

**✨ THE OPTIONAL EXTENSIONS OF DIVINE POWER! ✨**
- **🕰️ `/.well-known/oauth-authorization-server`** - Server metadata shrine of discovery (RFC 8414)!
- **⚔️ `/revoke`** - Token banishment altar of righteous destruction (RFC 7009)!
- **🔍 `/introspect`** - Token examination oracle of divine inspection (RFC 7662)!

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

## MCP Protocol 2025-06-18 Divine Specifications - THE GLORIOUS NEW COVENANT OF PROTOCOL ENLIGHTENMENT!

**🎆 BEHOLD THE SACRED MCP PROTOCOL - BLESSED BY THE DIVINE YEAR 2025-06-18! 🎆**
**This is the NEW COVENANT that brings salvation to all MCP communications!**

### The Sacred MCP Lifecycle Laws - AS DECREED BY THE PROTOCOL GODS IN 2025-06-18!

**🌅 THE DIVINE INITIALIZATION PHASE - THE SACRED BIRTH OF MCP SESSIONS! 🌅**
- **⚡ Server MUST receive `initialize` request ⚡** - The divine handshake of protocol communion!
- **⚡ Server MUST respond with protocol version ⚡** - Declaring its sacred capabilities to the client!
- **⚡ Server MUST include implementation details ⚡** - Revealing its divine nature and powers!
- **⚡ ONLY pings and logging allowed ⚡** before the `initialized` notification blessing!

**⚙️ THE HOLY OPERATION PHASE - THE SACRED DANCE OF PROTOCOL COMMUNICATION! ⚙️**
- **⚡ Server MUST respect negotiated protocol version ⚡** - Honor the sacred covenant established!
- **⚡ Server MUST use ONLY successfully negotiated capabilities ⚡** - No false promises of unblessed powers!
- **⚡ Server MUST implement timeouts ⚡** for all requests - Patience has divine limits!
- **⚡ Server MUST handle errors with divine grace ⚡** - Even failures must be blessed with proper responses!

**🌄 THE SACRED SHUTDOWN PHASE - THE PEACEFUL DEATH OF PROTOCOL SESSIONS! 🌄**
- **⚡ Server MAY initiate shutdown ⚡** by closing the divine output stream!
- **⚡ Clean termination brings blessing ⚡** to all connections - No unclean deaths allowed!

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

1. **👽 First Contact** - Claude.ai attempts `/mcp` with sacred protocol version header!
2. **⚡ Divine Rejection** - 401 with `WWW-Authenticate: Bearer` (OAuth 2.1 compliance divine!)
3. **🔍 Metadata Quest** - Seeks `/.well-known/oauth-authorization-server` (RFC 8414 pilgrimage!)
4. **✨ Registration Miracle** - POSTs to `/register` with RFC 7591 blessed data offering!
5. **📜 Client Blessing** - Receives client_id and sacred credentials (201 Created glory!)
6. **🕰️ PKCE Summoning** - S256 challenge generated (RFC 7636 divine mandate!)
7. **🚀 GitHub Pilgrimage** - User authenticates through GitHub's OAuth 2.0 judgment!
8. **🧪 Token Transmutation** - Authorization code transforms into JWT with sacred claims!
9. **☯️ Eternal Connection** - Streamable HTTP communion with Bearer token and blessed session ID!

## Traefik Routing Configuration - THE DIVINE ROUTING COMMANDMENTS!

**🚦 BEHOLD THE SACRED ART OF REQUEST ROUTING - THE DIVINE TRAFFIC CONTROL! 🚦**
**Traefik is the divine gateway guardian, directing requests to their blessed destinations!**

### The Sacred Priority System - THE DIVINE HIERARCHY OF ROUTING JUDGMENT!

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

**⚡ WITHOUT PRIORITIES, THE CATCH-ALL ROUTE DEVOURS ALL REQUESTS LIKE A HUNGRY DEMON! ⚡**
**Order thy routes with divine priority or face the chaos of misdirected requests!**

### The ForwardAuth Middleware - THE DIVINE AUTHENTICATION GUARDIAN!

**🔐 THE SACRED MIDDLEWARE THAT GUARDS THE GATES OF MCP PARADISE! 🔐**

```yaml
# THE DIVINE FORWARDAUTH CONFIGURATION - BLESSED AUTHENTICATION GATEKEEPER!
- "traefik.http.middlewares.mcp-auth.forwardauth.address=http://auth:8000/verify"
- "traefik.http.middlewares.mcp-auth.forwardauth.authResponseHeaders=X-User-Id,X-User-Name,X-Auth-Token"
```

**⚡ SACRED DECREE: Apply ONLY to MCP routes - OAuth flows must remain pure and unimpeded! ⚡**
**Block OAuth endpoints and face the wrath of authentication loops eternal!**

## Redis Storage Patterns - THE DIVINE DATA SANCTUARIES!

**🖼️ REDIS IS THE SACRED TEMPLE WHERE BLESSED DATA DWELLS IN KEY-VALUE HARMONY! 🖼️**
**Each key follows the divine naming conventions blessed by the database gods!**

### The Sacred Key Hierarchy - THE HOLY TAXONOMY OF DATA ORGANIZATION!

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

## The GitHub Device Workflow - THE SACRED GITHUB AUTHENTICATION PILGRIMAGE!

**🚀 GITHUB IS THE DIVINE ORACLE OF USER IDENTITY - THE BLESSED AUTHENTICATION PROVIDER! 🚀**
**Through GitHub's OAuth flows, mortal users prove their worthiness to access divine resources!**

### Smart Token Generation - THE DIVINE AUTOMATION OF AUTHENTICATION BLESSING!

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

## Testing Requirements - THE SACRED VERIFICATION COMMANDMENTS!

**🧪 TESTING IS THE DIVINE RITUAL OF CODE VERIFICATION - THE HOLY COMMUNION WITH TRUTH! 🧪**

### Divine Test Coverage - BLESSED BY THE SACRED DOCTRINE OF REAL SYSTEM VERIFICATION!

**🔥 THIS HOLY PROJECT'S TEST SUITE CHANNELS THE DIVINE FURY OF PART I AGAINST REAL DEPLOYED SERVICES! 🔥**
- ✅ **🔐 OAuth 2.1 FLOWS OF RIGHTEOUSNESS** - Real GitHub authentication, PKCE validation, dynamic registration glory!
- ✅ **🎨 JWT TOKEN SANCTIFICATION** - Formation, refresh, rotation, revocation with actual Redis blessing ceremonies!
- ✅ **🤖 MCP INTEGRATION GLORY** - Claude.ai flows, protocol compliance, session management divinity!
- ✅ **⚔️ SECURITY ENFORCEMENT WRATH** - ForwardAuth validation, dual auth paths, error handling divine fury!
- ✅ **🎆 PRODUCTION READINESS BLESSING** - Health checks, SSL certificates, routing validation perfection!

**⚡ THE ETERNAL LAW OF NO MOCKING: Mock once and face bugs that ONLY appear in production - THIS IS THE ETERNAL CURSE! ⚡**
**The mocker shall be mocked by reality! The faker shall be faced with failure! And the stubber shall stumble in production!**

## The Final Integration Checklist - THE DIVINE GATEWAY VERIFICATION CEREMONY!

**🏖️ BEHOLD THE ULTIMATE INTEGRATION RITUAL - THE SACRED CHECKLIST OF DIVINE BLESSING! 🏖️**

### The Twenty-Five Sacred Seals of Divine Integration - THE HOLY COMPLETENESS VERIFICATION!

**⚡ ALL TWENTY-FIVE SEALS MUST BE UNBROKEN OR THY GATEWAY SHALL CRUMBLE INTO CHAOS AND DAMNATION! ⚡**
**Each seal represents a sacred aspect of the divine architecture - break even ONE and summon the demons of failure!**

**🏗️ THE TRINITY SEALS - THE SACRED ARCHITECTURAL PURITY COMMANDMENTS! 🏗️**
- ✅ **🔱 SEAL OF THE TRINITY** - Traefik, Auth Service, MCP Services in divine separation blessed!
- ✅ **📈 SEAL OF ROUTING PRIORITIES** - 4→3→2→1 priority hierarchy enforced with holy fury!
- ✅ **🔐 SEAL OF FORWARDAUTH** - Middleware blessing protects all MCP endpoints with divine judgment!

**⚙️ THE DEVELOPMENT COMMANDMENT SEALS - THE UNIVERSAL LAWS OF DIVINE CODING! ⚙️**
- ✅ **⚡ SEAL OF NO MOCKING** - 154 real tests against deployed services with righteous fury!
- ✅ **🔱 SEAL OF THE BLESSED TOOLS** - just, pixi, docker-compose trinity reigns supreme!
- ✅ **🏗️ SEAL OF SACRED STRUCTURE** - ./tests/, ./scripts/, ./docs/, ./logs/, ./reports/ divine isolation!
- ✅ **⚙️ SEAL OF ENV SANCTITY** - All configuration flows through blessed .env files!
- ✅ **🧪 SEAL OF SIDECAR COVERAGE** - Production containers measured without contamination!

**🔐 THE OAUTH AUTHENTICATION SEALS - THE RFC COMPLIANCE COMMANDMENTS! 🔐**
- ✅ **📜 SEAL OF OAUTH 2.1** - Full compliance with the sacred specification blessed!
- ✅ **🚀 SEAL OF RFC 7591** - Dynamic client registration portal of divine access!
- ✅ **🚀 SEAL OF GITHUB OAUTH** - GitHub judges the souls of human users with divine authority!
- ✅ **🔒 SEAL OF PKCE S256** - Cryptographic proof key challenges protect all with holy encryption!
- ✅ **🎨 SEAL OF JWT SANCTITY** - Tokens blessed with divine claims and sacred signatures!
- ✅ **☯️ SEAL OF DUAL REALMS** - Client auth and user auth never intermingle in sacred separation!

**🤖 THE MCP PROTOCOL SEALS - THE 2025-06-18 COVENANT OF DIVINE COMMUNICATION! 🤖**
- ✅ **🎆 SEAL OF MCP COMPLIANCE** - Full 2025-06-18 protocol implementation glory blessed!
- ✅ **🌊 SEAL OF STREAMABLE HTTP** - mcp-streamablehttp-proxy bridges stdio to HTTP with divine transcendence!
- ✅ **✨ SEAL OF OFFICIAL SERVERS** - ONLY REAL MCP servers wrapped, never false prophets!
- ✅ **🔄 SEAL OF SESSION MANAGEMENT** - Mcp-Session-Id headers maintain blessed state continuity!

**🏗️ THE INFRASTRUCTURE SEALS - THE PRODUCTION GLORY COMMANDMENTS! 🏗️**
- ✅ **🚦 SEAL OF TRAEFIK ROUTING** - Docker labels with divine priority enforcement and holy routing!
- ✅ **🖼️ SEAL OF REDIS PATTERNS** - Sacred key hierarchies preserve all state with blessed persistence!
- ✅ **📊 SEAL OF HEALTH MONITORING** - Every service proves readiness through HTTP with divine verification!
- ✅ **🔒 SEAL OF LET'S ENCRYPT** - HTTPS certificates auto-blessed by ACME miracles of divine encryption!

**✨ THE INTEGRATION SEALS - THE DIVINE UNITY COMMANDMENTS! ✨**
- ✅ **🎨 SEAL OF BEARER TOKENS** - Authorization headers carry blessed credentials of divine access!
- ✅ **🤖 SEAL OF GATEWAY CLIENTS** - MCP clients register once, authenticated forever in eternal blessing!
- ✅ **📚 SEAL OF DOCUMENTATION** - Jupyter Book with MyST preserves all wisdom in sacred knowledge temples!

**⚡ DIVINE WARNING - THE CURSE OF BROKEN SEALS! ⚡**
**Break even ONE seal and summon the DEMONS OF PRODUCTION FAILURE to torment thy deployment!**
**ALL 25 SEALS must remain intact and unbroken for the gateway to channel DIVINE POWER and righteousness!**
**The sealed gateway brings blessing! The broken gateway brings chaos! Choose thy path wisely!**

---

# The Sacred Implementation Oath - THE DIVINE COVENANT OF RIGHTEOUS DEVELOPMENT!

**📜 BEHOLD THE SACRED OATH - THE HOLY PROMISE OF EVERY BLESSED DEVELOPER! 📜**

*By these holy scrolls and divine commandments, I solemnly swear upon the sacred code:*

- **⚡ I shall TEST against real systems** with pytest - NO MOCKING EVER, on pain of eternal debugging!
- **⚡ I shall USE just and pixi** for ALL execution - the blessed trinity guides my commands!
- **⚡ I shall ORCHESTRATE with docker-compose** exclusively - no chaos, only divine container harmony!
- **⚡ I shall MAINTAIN perfect separation** of concerns - each service in its sacred domain!
- **⚡ I shall CONFIGURE through .env files** in ALL environments - no hardcoded heresy!
- **⚡ I shall MEASURE coverage with sidecar** patterns in production - truth from real containers!
- **⚡ I shall TRUST only docker healthchecks** for readiness - death to arbitrary sleep commands!
- **⚡ I shall SEGREGATE all logs** to ./logs/ properly - divine organization prevents chaos!
- **⚡ I shall SAVE all reports** to git-ignored ./reports/ - analysis artifacts blessed!
- **⚡ I shall DOCUMENT with Jupyter Book and MyST** - knowledge preserved in sacred format!
- **⚡ I shall FIND root causes** - not patch symptoms - the five whys guide my investigation!

**🎆 DIVINE BLESSING UPON THE FAITHFUL: May thy builds be reproducible, thy tests be real, and thy production deployments forever blessed! 🎆**
**May the debugging gods smile upon thee! May thy containers start in harmony! And may thy code be forever free of production surprises!**

---

# The Final Revelation: Full 2025-06-18 Compliance - THE ULTIMATE DIVINE BLESSING!

**🎆 BEHOLD THE FINAL REVELATION - THE GLORIOUS COMPLETION OF DIVINE PROTOCOL ENLIGHTENMENT! 🎆**
**The sacred year 2025-06-18 has brought forth the NEW COVENANT of MCP protocol perfection!**

## The Four Pillars of the New Covenant - THE SACRED QUADRUPLE FOUNDATION!

### 1. 🌅 LIFECYCLE COMPLIANCE ✅ - THE SACRED BIRTH, LIFE, AND DEATH OF SESSIONS!
- **⚡ Divine initialization** with protocol negotiation blessed by the gods!
- **⚡ Sacred operation phase** with capability respect and divine harmony!
- **⚡ Clean shutdown procedures** blessed by the spec and sanctified by protocol!

### 2. 🌊 TRANSPORT COMPLIANCE ✅ - THE DIVINE COMMUNICATION CHANNELS!
- **⚡ Streamable HTTP** with `/mcp` endpoints via mcp-streamablehttp-proxy divine bridge!
- **⚡ Required headers** properly declared and forwarded with sacred precision!
- **⚡ Session management** through Mcp-Session-Id handled by blessed proxy!
- **⚡ mcp-streamablehttp-proxy** bridging official MCP servers to HTTP with divine transcendence!

### 3. 🔐 AUTHORIZATION COMPLIANCE ✅ - THE SACRED GATES OF ACCESS!
- **⚡ Full OAuth 2.1 implementation** blessed by the RFC gods!
- **⚡ Dynamic client registration** (RFC 7591) - the divine registration miracle!
- **⚡ Protected resource metadata** support with sacred discovery!
- **⚡ Token validation** with divine fury and righteous verification!

### 4. ⚔️ SECURITY COMPLIANCE ✅ - THE HOLY SHIELDS OF PROTECTION!
- **⚡ Confused deputy protections** in place - no delegation demons allowed!
- **⚡ Token audience validation** mandatory - tokens serve only their intended masters!
- **⚡ Session security** properly implemented with blessed randomness!
- **⚡ Origin header validation** enforced - no DNS rebinding demons permitted!

**🎆 BEHOLD THE GLORY OF STREAMABLE HTTP VIA DIVINE PROXY ARCHITECTURE! 🎆**
**✨ OFFICIAL MCP SERVERS! BATTLE-TESTED BRIDGES! ARCHITECTURAL RIGHTEOUSNESS! ✨**
**🚀 REAL IMPLEMENTATIONS! DIVINE TRANSCENDENCE! PROTOCOL PERFECTION! 🚀**

**📜 THE SACRED SCROLLS ARE COMPLETE! 📜**
*Thus ends the divine documentation. Go forth, blessed developer, and build with righteous 2025-06-18 compliance!*
*May thy gateway be secure! Thy OAuth flows pure! And thy MCP protocols blessed with divine communication!*
**⚡ THE CODING GODS HAVE SPOKEN - LET IT BE SO! ⚡**