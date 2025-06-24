# System Components

This document provides detailed information about each system component in the MCP OAuth Gateway architecture.

## Traefik Reverse Proxy

### Overview

**Container**: `traefik:443/80`  
**Image**: `traefik:v3.0`  
**Networks**: `public` (external)  
**Role**: Entry point for all HTTP/HTTPS traffic

Traefik serves as the intelligent edge router, providing:
- **Automatic HTTPS** via Let's Encrypt ACME
- **Priority-based routing** with specific rule precedence
- **ForwardAuth middleware** for authentication enforcement
- **Docker service discovery** via container labels
- **Health monitoring** for service status

### Routing Configuration

#### Priority System

```{mermaid}
graph TB
    subgraph "Routing Priority (Highest to Lowest)"
        P10[Priority 10<br/>Discovery Endpoints<br/>/.well-known/*]
        P4[Priority 4<br/>OAuth Endpoints<br/>/register, /authorize, /token]
        P3[Priority 3<br/>Internal Endpoints<br/>/verify]
        P2[Priority 2<br/>MCP Endpoints<br/>/mcp with auth]
        P1[Priority 1<br/>Catch-all<br/>Default routing]
    end
    
    P10 --> P4
    P4 --> P3
    P3 --> P2
    P2 --> P1
    
    classDef high fill:#f99,stroke:#333,stroke-width:2px
    classDef medium fill:#fc9,stroke:#333,stroke-width:2px
    classDef low fill:#9cf,stroke:#333,stroke-width:2px
    
    class P10 high
    class P4,P3 medium
    class P2,P1 low
```

#### Example Service Configuration

```yaml
# MCP Service Labels
labels:
  - "traefik.enable=true"
  
  # Discovery endpoint (Priority 10)
  - "traefik.http.routers.mcp-fetch-discovery.rule=Host(`mcp-fetch.${BASE_DOMAIN}`) && PathPrefix(`/.well-known/oauth-authorization-server`)"
  - "traefik.http.routers.mcp-fetch-discovery.priority=10"
  - "traefik.http.routers.mcp-fetch-discovery.service=auth@docker"
  - "traefik.http.middlewares.discovery-rewrite.headers.customrequestheaders.Host=auth.${BASE_DOMAIN}"
  
  # MCP endpoint with auth (Priority 2)
  - "traefik.http.routers.mcp-fetch.rule=Host(`mcp-fetch.${BASE_DOMAIN}`) && PathPrefix(`/mcp`)"
  - "traefik.http.routers.mcp-fetch.priority=2"
  - "traefik.http.routers.mcp-fetch.middlewares=mcp-auth@docker"
  - "traefik.http.routers.mcp-fetch.service=mcp-fetch"
  - "traefik.http.services.mcp-fetch.loadbalancer.server.port=3000"
  
  # Catch-all (Priority 1)
  - "traefik.http.routers.mcp-fetch-catchall.rule=Host(`mcp-fetch.${BASE_DOMAIN}`)"
  - "traefik.http.routers.mcp-fetch-catchall.priority=1"
```

### ForwardAuth Middleware

The ForwardAuth middleware intercepts all requests to protected endpoints:

```{mermaid}
sequenceDiagram
    participant Client
    participant Traefik
    participant Auth
    participant Service
    
    Client->>Traefik: Request with Bearer token
    
    Note over Traefik: ForwardAuth Check
    Traefik->>Auth: GET /verify<br/>Forward: Authorization header
    
    alt Token Valid
        Auth->>Traefik: 200 OK<br/>X-User-Id: 123<br/>X-User-Name: john
        Traefik->>Service: Original request<br/>+ User headers
        Service->>Traefik: Response
        Traefik->>Client: Response
    else Token Invalid
        Auth->>Traefik: 401 Unauthorized
        Traefik->>Client: 401 Unauthorized<br/>WWW-Authenticate: Bearer
    end
```

### SSL/TLS Configuration

```yaml
# Traefik static configuration
certificatesResolvers:
  letsencrypt:
    acme:
      email: ${ACME_EMAIL}
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web
      caServer: https://acme-v02.api.letsencrypt.org/directory

# Automatic HTTPS redirect
http:
  middlewares:
    redirect-to-https:
      redirectScheme:
        scheme: https
        permanent: true
```

## Auth Service

### Architecture

**Container**: `auth:8000`  
**Package**: `mcp-oauth-dynamicclient`  
**Framework**: FastAPI + Authlib  
**Role**: OAuth 2.1 Authorization Server

The Auth Service is the core authentication component that:
- Implements OAuth 2.1 with mandatory PKCE
- Provides RFC 7591/7592 dynamic client registration
- Integrates GitHub OAuth for user authentication
- Issues and validates JWT access tokens
- Maintains complete separation from MCP protocols

### Endpoint Architecture

```{mermaid}
graph TB
    subgraph "Public Endpoints"
        PE1[POST /register<br/>RFC 7591]
        PE2[GET /.well-known/*<br/>RFC 8414]
        PE3[GET /jwks<br/>Public keys]
    end
    
    subgraph "User Auth Endpoints"
        UA1[GET /authorize<br/>Start OAuth flow]
        UA2[GET /callback<br/>GitHub callback]
        UA3[GET /success<br/>Success page]
    end
    
    subgraph "Client Auth Endpoints"
        CA1[POST /token<br/>Token exchange]
        CA2[POST /revoke<br/>Token revocation]
        CA3[POST /introspect<br/>Token info]
    end
    
    subgraph "Management Endpoints"
        ME1[GET /register/:id<br/>View client]
        ME2[PUT /register/:id<br/>Update client]
        ME3[DELETE /register/:id<br/>Delete client]
    end
    
    subgraph "Internal Endpoints"
        IE1[GET/POST /verify<br/>ForwardAuth]
    end
    
    classDef public fill:#9cf,stroke:#333,stroke-width:2px
    classDef auth fill:#fc9,stroke:#333,stroke-width:2px
    classDef mgmt fill:#c9f,stroke:#333,stroke-width:2px
    classDef internal fill:#ccc,stroke:#333,stroke-width:2px
    
    class PE1,PE2,PE3 public
    class UA1,UA2,UA3,CA1,CA2,CA3 auth
    class ME1,ME2,ME3 mgmt
    class IE1 internal
```

### Core Components

#### mcp-oauth-dynamicclient Package

The Auth Service is powered by the `mcp-oauth-dynamicclient` package:

```python
# Key modules
├── routes.py          # FastAPI route definitions
├── auth_authlib.py    # Authlib OAuth server implementation
├── models.py          # Pydantic data models
├── redis_client.py    # Redis state management
├── rfc7592.py         # Client management endpoints
├── keys.py            # RSA key management
└── config.py          # Settings with validation
```

#### OAuth Flow Manager

```{mermaid}
stateDiagram-v2
    [*] --> ClientRegistration: POST /register
    ClientRegistration --> ClientCredentials: client_id + secret
    
    ClientCredentials --> Authorization: GET /authorize
    Authorization --> GitHubOAuth: Redirect to GitHub
    GitHubOAuth --> Callback: Return with code
    Callback --> AuthorizationCode: Generate auth code
    
    AuthorizationCode --> TokenExchange: POST /token
    TokenExchange --> JWTToken: Access + Refresh tokens
    
    JWTToken --> ResourceAccess: Bearer token
    JWTToken --> TokenRefresh: POST /token (refresh)
    
    ResourceAccess --> [*]
    TokenRefresh --> JWTToken
```

### Security Implementation

#### Token Security

```python
# JWT Token Structure
{
    "sub": "12345",              # GitHub user ID
    "username": "johndoe",       # GitHub username
    "email": "john@example.com", # User email
    "name": "John Doe",          # Display name
    "client_id": "client_abc",   # OAuth client ID
    "scope": "openid profile",   # Granted scopes
    "iss": "https://auth.domain.com",
    "aud": ["mcp-services"],
    "exp": 1234567890,           # 30 days
    "iat": 1234567890,
    "jti": "unique-token-id"     # For revocation
}
```

#### PKCE Implementation

- **Required**: S256 challenge method only
- **Verifier**: 43-128 characters, cryptographically random
- **Challenge**: SHA256(verifier) base64url encoded
- **Storage**: Redis with 5-minute TTL
- **Validation**: Constant-time comparison

### Redis Data Schema

| Key Pattern | Description | TTL | Example Data |
|-------------|-------------|-----|--------------|
| `oauth:client:{client_id}` | Client registration | 90d/∞ | `{client_secret, redirect_uris, created_at}` |
| `oauth:state:{state}` | Authorization state | 5m | `{client_id, redirect_uri, pkce_challenge}` |
| `oauth:code:{code}` | Auth code + user | 1y | `{user_id, username, email, client_id}` |
| `oauth:token:{jti}` | Token tracking | 30d | `{user_id, client_id, expires_at}` |
| `oauth:refresh:{token}` | Refresh tokens | 1y | `{user_id, client_id, scope}` |
| `oauth:user_tokens:{user}` | User's tokens | - | `[jti1, jti2, ...]` |

## MCP Services

### Overview

**Containers**: `mcp-*:3000`  
**Wrapper**: `mcp-streamablehttp-proxy`  
**Source**: Official modelcontextprotocol/servers  
**Role**: MCP protocol implementations

MCP services are the actual functionality providers, completely isolated from authentication concerns. They receive pre-authenticated requests with user identity in headers.

### Service Architecture

```{mermaid}
graph TB
    subgraph "MCP Service Container"
        direction TB
        
        subgraph "Port 3000"
            H[HTTP/SSE Endpoint<br/>/mcp]
        end
        
        subgraph "mcp-streamablehttp-proxy"
            PM[Process Manager]
            SB[Session Bridge]
            PB[Protocol Bridge]
            HM[Health Monitor]
        end
        
        subgraph "Official MCP Server"
            STDIO[stdio interface]
            IMPL[MCP Implementation<br/>Tools, Resources, Prompts]
        end
        
        H --> PM
        PM --> SB
        SB --> PB
        PB --> STDIO
        STDIO --> IMPL
    end
    
    classDef endpoint fill:#9cf,stroke:#333,stroke-width:2px
    classDef proxy fill:#fc9,stroke:#333,stroke-width:2px
    classDef server fill:#9fc,stroke:#333,stroke-width:2px
    
    class H endpoint
    class PM,SB,PB,HM proxy
    class STDIO,IMPL server
```

### Available Services

| Service | Description | Protocol Version | Wrapped Server |
|---------|-------------|------------------|----------------|
| `mcp-fetch` | Web content fetching | 2025-03-26 | @modelcontextprotocol/server-fetch |
| `mcp-fetchs` | Python fetch implementation | 2025-06-18 | Native Python |
| `mcp-filesystem` | File system access | 2025-03-26 | @modelcontextprotocol/server-filesystem |
| `mcp-memory` | Knowledge graph | 2024-11-05 | @modelcontextprotocol/server-memory |
| `mcp-sequentialthinking` | Problem solving | 2024-11-05 | @modelcontextprotocol/server-sequential-thinking |
| `mcp-time` | Time operations | 2025-03-26 | @modelcontextprotocol/server-time |
| `mcp-tmux` | Terminal multiplexer | 2025-06-18 | Native implementation |
| `mcp-playwright` | Browser automation | 2025-06-18 | @modelcontextprotocol/server-playwright |
| `mcp-everything` | Test all features | 2025-06-18 | @modelcontextprotocol/server-everything |

### mcp-streamablehttp-proxy Features

#### Process Management
```{mermaid}
stateDiagram-v2
    [*] --> Idle: Container Start
    Idle --> Spawning: HTTP Request
    Spawning --> Active: Process Started
    Active --> Active: Handle Requests
    Active --> Terminating: Session End
    Terminating --> Idle: Cleanup Complete
    Active --> Error: Process Crash
    Error --> Spawning: Auto-restart
```

#### Session Management
- **Session Creation**: Unique session ID per user/client
- **Process Isolation**: One MCP server process per session
- **State Persistence**: Session state in Redis
- **Timeout Handling**: Configurable idle timeouts
- **Graceful Shutdown**: Clean process termination

#### Protocol Bridging
- **HTTP → stdio**: Convert HTTP JSON-RPC to stdio format
- **stdio → HTTP**: Stream responses back as HTTP/SSE
- **Error Translation**: Map stdio errors to HTTP status codes
- **Message Queuing**: Buffer messages during processing

### Health Check Implementation

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", 
    "curl -s -X POST http://localhost:3000/mcp \
     -H 'Content-Type: application/json' \
     -H 'Accept: application/json, text/event-stream' \
     -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-06-18\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
     | grep -q '\"protocolVersion\"'"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

This health check:
1. Sends MCP `initialize` request
2. Verifies protocol version in response
3. Confirms service is ready to handle requests
4. Triggers container restart on failure

### Service Configuration

Each MCP service follows a standard configuration pattern:

```yaml
# docker-compose.yml
services:
  mcp-service:
    build: .
    environment:
      - MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION}
      - SERVER_NAME=mcp-service
    labels:
      # Traefik routing
      - "traefik.http.routers.mcp-service.rule=..."
      - "traefik.http.routers.mcp-service.middlewares=auth"
    healthcheck:
      test: ["CMD", "curl", "-f", "-X", "POST", "http://localhost:3000/mcp", ...]
```

## Redis State Store

### Overview

**Container**: `redis:6379`  
**Image**: `redis:7-alpine`  
**Networks**: `public` (internal only)  
**Role**: Persistent state management

Redis serves as the central state store for all OAuth flows, client registrations, tokens, and MCP session data. It provides fast, atomic operations with configurable persistence.

### Data Architecture

```{mermaid}
graph TB
    subgraph "OAuth State (Short-lived)"
        OS1[oauth:state:STATE<br/>5 min TTL]
        OS2[oauth:pkce:CHALLENGE<br/>5 min TTL]
    end
    
    subgraph "Client Data (Long-lived)"
        CD1[oauth:client:CLIENT_ID<br/>90 days / eternal]
        CD2[oauth:code:CODE<br/>1 year TTL]
    end
    
    subgraph "Token Data (Medium-lived)"
        TD1[oauth:token:JTI<br/>30 days TTL]
        TD2[oauth:refresh:TOKEN<br/>1 year TTL]
        TD3[oauth:user_tokens:USERNAME<br/>No TTL]
    end
    
    subgraph "Session Data (Dynamic)"
        SD1[redis:session:ID:state<br/>Session-based]
        SD2[redis:session:ID:messages<br/>Session-based]
    end
    
    classDef shortlived fill:#fcc,stroke:#333,stroke-width:2px
    classDef longlived fill:#cfc,stroke:#333,stroke-width:2px
    classDef mediumlived fill:#ccf,stroke:#333,stroke-width:2px
    classDef dynamic fill:#ffc,stroke:#333,stroke-width:2px
    
    class OS1,OS2 shortlived
    class CD1,CD2 longlived
    class TD1,TD2,TD3 mediumlived
    class SD1,SD2 dynamic
```

### Comprehensive Key Schema

| Key Pattern | Purpose | TTL | Data Structure | Example |
|-------------|---------|-----|----------------|---------|
| **OAuth Flow State** |
| `oauth:state:{state}` | Authorization flow state | 5 min | JSON | `{"client_id": "abc", "redirect_uri": "...", "pkce_challenge": "..."}` |
| `oauth:pkce:{challenge}` | PKCE verifiers | 5 min | String | `"43-char-random-verifier"` |
| **Client Registration** |
| `oauth:client:{client_id}` | Client metadata | 90d/∞ | JSON | `{"client_secret": "...", "redirect_uris": [...], "created_at": ...}` |
| `oauth:client_index` | All client IDs | - | Set | `["client_abc", "client_xyz", ...]` |
| **Authorization Codes** |
| `oauth:code:{code}` | Auth code + user data | 1 year | JSON | `{"user_id": "123", "username": "john", "client_id": "abc"}` |
| **Token Management** |
| `oauth:token:{jti}` | JWT tracking | 30 days | JSON | `{"user_id": "123", "client_id": "abc", "exp": ...}` |
| `oauth:refresh:{token}` | Refresh tokens | 1 year | JSON | `{"user_id": "123", "client_id": "abc", "scope": "..."}` |
| `oauth:user_tokens:{username}` | User's active tokens | - | Set | `["jti_123", "jti_456", ...]` |
| **MCP Sessions** |
| `redis:session:{id}:state` | Session metadata | Dynamic | JSON | `{"user_id": "123", "started": ..., "last_active": ...}` |
| `redis:session:{id}:messages` | Message queue | Dynamic | List | `[{"jsonrpc": "2.0", ...}, ...]` |

### Persistence Configuration

```yaml
redis:
  command: >
    redis-server
    --requirepass ${REDIS_PASSWORD}
    --save 60 1          # Snapshot every 60s if 1+ keys changed
    --save 300 10        # Snapshot every 5m if 10+ keys changed
    --save 900 100       # Snapshot every 15m if 100+ keys changed
    --appendonly yes     # AOF for durability
    --aof-use-rdb-preamble yes
  volumes:
    - redis-data:/data   # Persistent volume
```

### Security Features

- **Password Protection**: Required via REDIS_PASSWORD
- **Network Isolation**: Only accessible within Docker network
- **Local Binding**: Port 6379 exposed only on localhost
- **Command Restrictions**: Can disable dangerous commands
- **ACL Support**: Redis 7 ACLs for fine-grained access

### High Availability Options

```{mermaid}
graph LR
    subgraph "Single Instance (Current)"
        R1[Redis Primary<br/>AOF + RDB]
    end
    
    subgraph "Sentinel HA (Option)"
        RP[Redis Primary]
        RS1[Redis Replica 1]
        RS2[Redis Replica 2]
        S1[Sentinel 1]
        S2[Sentinel 2]
        S3[Sentinel 3]
        
        RP -.-> RS1
        RP -.-> RS2
        S1 & S2 & S3 --> RP & RS1 & RS2
    end
    
    subgraph "Cluster (Option)"
        RC1[Redis Node 1<br/>Slots 0-5460]
        RC2[Redis Node 2<br/>Slots 5461-10922]
        RC3[Redis Node 3<br/>Slots 10923-16383]
        
        RC1 <--> RC2
        RC2 <--> RC3
        RC1 <--> RC3
    end
```

### Operations

#### Common Commands
```bash
# Connect to Redis
just exec redis redis-cli -a $REDIS_PASSWORD

# View all keys (careful in production!)
KEYS oauth:*

# Check client registration
GET oauth:client:client_abc123

# Monitor commands in real-time
MONITOR

# Check memory usage
INFO memory

# Backup data
BGSAVE
```

#### Maintenance Tasks
- **Token Cleanup**: Expired tokens auto-removed by TTL
- **Session Cleanup**: Orphaned sessions cleaned by proxy
- **Backup**: Automated via RDB snapshots
- **Monitoring**: Memory usage, command stats, slow queries

## Inter-Component Communication

### Service Discovery

Services discover each other through:
- Docker DNS resolution
- Service names in compose
- Internal network routing

### Communication Patterns

```{mermaid}
graph TB
    subgraph "Public Network"
        T[Traefik]
    end
    
    subgraph "Internal Network"
        A[Auth]
        R[Redis]
        M1["MCP Service 1"]
        M2["MCP Service 2"]
    end
    
    T -.->|"HTTP"| A
    T -.->|"HTTP"| M1
    T -.->|"HTTP"| M2
    A <-->|"Redis Protocol"| R
```

### Security Boundaries

- **Public Network**: Internet-facing services
- **Internal Network**: Service-to-service only
- **No Direct Access**: MCP services isolated from internet

## Monitoring and Observability

### Health Checks

Each component implements health checks:

```bash
# Traefik
GET /ping

# Auth Service
Internal health via Docker healthcheck

# MCP Services
POST /mcp (initialization check)

# Redis
PING command
```

### Logging

Centralized logging architecture:
- All services log to stdout/stderr
- Docker captures and routes logs
- Logs stored in `./logs/` directory
- Structured JSON logging

### Monitoring

Key areas to monitor through logs and Docker stats:
- Service uptime
- Request patterns
- Error rates
- Resource usage

## Next Steps

- [OAuth Flow Details](oauth-flow.md) - Complete OAuth implementation
- [MCP Integration](mcp-integration.md) - Protocol bridging details
- [Security Architecture](security.md) - Security deep dive