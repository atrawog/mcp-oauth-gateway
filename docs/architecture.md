# Architecture

## Overview

The MCP OAuth Gateway is a **zero-modification authentication layer** for MCP servers. It implements OAuth 2.1 with dynamic client registration (RFC 7591/7592) and leverages GitHub as the identity provider for user authentication. The architecture follows these core principles:

- **Complete Separation of Concerns**: Authentication, routing, and MCP protocol handling are strictly isolated
- **No MCP Server Modifications**: Official MCP servers run unmodified, wrapped only for HTTP transport
- **Standards Compliance**: Full OAuth 2.1, RFC 7591/7592, and MCP protocol compliance
- **Production-Ready Security**: HTTPS everywhere, PKCE mandatory, JWT tokens, secure session management
- **Dynamic Service Discovery**: Services can be enabled/disabled via configuration

## System Components

```{mermaid}
graph TB
    subgraph "External Clients"
        C1[Claude.ai]
        C2[MCP CLI tools]
        C3[IDE extensions]
        C4[Custom integrations]
    end
    
    subgraph "Traefik Reverse Proxy - Layer 1"
        direction TB
        T[Traefik :443/:80]
        T1[Let's Encrypt<br/>Auto HTTPS]
        T2[Priority-based<br/>Routing]
        T3[ForwardAuth<br/>Middleware]
        T4[Docker Service<br/>Discovery]
        T --> T1
        T --> T2
        T --> T3
        T --> T4
    end
    
    subgraph "Auth Service - Layer 2"
        direction TB
        A[Auth Service :8000]
        A1[OAuth Endpoints<br/>/register, /authorize<br/>/token, /callback]
        A2[Management<br/>RFC 7592]
        A3[Internal<br/>/verify]
        A4[Discovery<br/>/.well-known/*]
        A --> A1
        A --> A2
        A --> A3
        A --> A4
    end
    
    subgraph "MCP Services - Layer 3"
        direction TB
        M1[mcp-fetch:3000]
        M2[mcp-filesystem:3000]
        M3[mcp-memory:3000]
        M4[mcp-time:3000]
        M5[... more services]
        MP[mcp-streamablehttp-proxy<br/>stdio ↔ HTTP bridge]
        M1 & M2 & M3 & M4 & M5 --> MP
    end
    
    subgraph "Storage Layer"
        R[(Redis :6379)]
        R1[oauth:client:ID]
        R2[oauth:state:STATE]
        R3[oauth:code:CODE]
        R4[oauth:token:JTI]
        R5[oauth:refresh:TOKEN]
        R6[redis:session:ID]
        R --> R1 & R2 & R3 & R4 & R5 & R6
    end
    
    subgraph "External Services"
        GH[GitHub OAuth]
    end
    
    C1 & C2 & C3 & C4 -.->|HTTPS :443| T
    T -->|OAuth/Auth<br/>unauthenticated| A
    T -->|MCP requests<br/>authenticated| M1 & M2 & M3 & M4 & M5
    T3 -.->|/verify| A3
    A <--> R
    A <--> GH
    
    classDef external fill:#f9f,stroke:#333,stroke-width:2px
    classDef layer1 fill:#9cf,stroke:#333,stroke-width:2px
    classDef layer2 fill:#fc9,stroke:#333,stroke-width:2px
    classDef layer3 fill:#9fc,stroke:#333,stroke-width:2px
    classDef storage fill:#c9f,stroke:#333,stroke-width:2px
    
    class C1,C2,C3,C4,GH external
    class T,T1,T2,T3,T4 layer1
    class A,A1,A2,A3,A4 layer2
    class M1,M2,M3,M4,M5,MP layer3
    class R,R1,R2,R3,R4,R5,R6 storage
```

## Component Details

### Layer 1: Traefik Reverse Proxy

**Container**: `traefik:443/80`  
**Role**: Routing & TLS Termination

#### Responsibilities
- **Let's Encrypt Certificates**: Automatic HTTPS for all subdomains
- **Priority-based Routing**: OAuth > Verify > MCP > Catch-all
- **ForwardAuth Middleware**: Enforces authentication for MCP endpoints
- **Docker Service Discovery**: Auto-detects services via labels

#### Request Routing Rules
```yaml
# Priority 10: OAuth Discovery (highest)
*.domain.com/.well-known/* → Auth Service

# Priority 4: OAuth Endpoints
auth.domain.com/[register|authorize|token|callback] → Auth Service

# Priority 3: Verify Endpoint
auth.domain.com/verify → Auth Service

# Priority 2: MCP Endpoints (with ForwardAuth)
*.domain.com/mcp → MCP Services

# Priority 1: Catch-all (lowest)
*.domain.com/* → Default handling
```

### Layer 2: Auth Service (OAuth Authorization Server)

**Container**: `auth:8000`  
**Package**: `mcp-oauth-dynamicclient`  
**Role**: OAuth 2.1 Implementation

#### OAuth Endpoints (Public)
- `POST /register` - RFC 7591 dynamic client registration
- `GET /authorize` - Initiate authorization flow with GitHub
- `GET /callback` - Handle GitHub OAuth callback
- `POST /token` - Exchange authorization code for tokens
- `GET /.well-known/*` - RFC 8414 OAuth discovery

#### Management Endpoints (RFC 7592)
- `GET /register/{client_id}` - View client configuration
- `PUT /register/{client_id}` - Update client metadata
- `DELETE /register/{client_id}` - Delete client registration

*Note: Requires Bearer registration_access_token*

#### Internal Endpoints
- `GET/POST /verify` - ForwardAuth token validation

#### External Integration
- **GitHub OAuth**: User authentication via github.com OAuth

### Layer 3: MCP Services (Protocol Handlers)

**Containers**: `mcp-*:3000`  
**Architecture**: mcp-streamablehttp-proxy wrapper

#### Service Architecture
```
┌─────────────────────────────────┐
│  HTTP Request on port 3000      │
└─────────────┬───────────────────┘
              ↓
┌─────────────────────────────────┐
│  mcp-streamablehttp-proxy       │
│  • Session management           │
│  • stdio ↔ HTTP bridge          │
│  • Error handling               │
└─────────────┬───────────────────┘
              ↓
┌─────────────────────────────────┐
│  Official MCP stdio server      │
│  • Unmodified implementation    │
│  • Protocol-specific logic      │
└─────────────────────────────────┘
```

#### Available Services
| Service | Description | Protocol Version |
|---------|-------------|------------------|
| mcp-fetch | Web content fetching | 2025-03-26 |
| mcp-fetchs | Native Python implementation | 2025-06-18 |
| mcp-filesystem | File system access | 2025-03-26 |
| mcp-memory | Knowledge graph | 2024-11-05 |
| mcp-time | Time operations | 2025-03-26 |
| ... | And more | Various |

### Storage Layer: Redis

**Container**: `redis:6379`  
**Persistence**: AOF + RDB snapshots

#### Data Structures

| Key Pattern | Description | TTL |
|-------------|-------------|-----|
| `oauth:client:{client_id}` | Client registrations | 90 days / eternal |
| `oauth:state:{state}` | Authorization flow state | 5 minutes |
| `oauth:code:{code}` | Authorization codes + user info | 1 year |
| `oauth:token:{jti}` | JWT token tracking | 30 days |
| `oauth:refresh:{token}` | Refresh token data | 1 year |
| `oauth:user_tokens:{username}` | User's active tokens | No TTL |
| `redis:session:{id}:state` | MCP session state | Session-based |
| `redis:session:{id}:messages` | MCP message queues | Session-based |

## Request Flow Scenarios

### 1. Client Registration Flow (RFC 7591)

```{mermaid}
sequenceDiagram
    participant Client
    participant Traefik
    participant Auth
    participant Redis
    
    Client->>Traefik: POST /register<br/>{redirect_uris, client_name}
    Traefik->>Auth: Route (no auth required)
    Auth->>Auth: Generate client_id<br/>Generate client_secret<br/>Generate registration_access_token
    Auth->>Redis: Store client data<br/>TTL: 90 days / eternal
    Redis-->>Auth: OK
    Auth->>Client: 201 Created<br/>{client_id, client_secret,<br/>registration_access_token,<br/>registration_client_uri}
```

### 2. User Authentication Flow (OAuth 2.1 + GitHub)

```{mermaid}
sequenceDiagram
    participant User
    participant Client
    participant Traefik
    participant Auth
    participant GitHub
    participant Redis
    
    Client->>Traefik: GET /authorize<br/>?client_id=abc&redirect_uri=...&code_challenge=xyz
    Traefik->>Auth: Route to Auth Service
    Auth->>Redis: Validate client_id exists
    Redis-->>Auth: Client data
    Auth->>Auth: Store PKCE challenge
    Auth->>Redis: Store oauth:state:{state}<br/>TTL: 5 minutes
    Auth->>Client: 302 Redirect<br/>Location: github.com/login/oauth/authorize
    
    Client->>GitHub: User authenticates
    User->>GitHub: Login + Authorize
    GitHub->>Client: 302 Redirect<br/>Location: /callback?code=gh_code&state=...
    
    Client->>Traefik: GET /callback?code=gh_code&state=...
    Traefik->>Auth: Route to Auth Service
    Auth->>Redis: Get oauth:state:{state}
    Redis-->>Auth: State data + PKCE
    Auth->>GitHub: POST /login/oauth/access_token<br/>Exchange GitHub code
    GitHub-->>Auth: GitHub access_token
    Auth->>GitHub: GET /user<br/>Get user info
    GitHub-->>Auth: User data (id, login, email)
    Auth->>Auth: Validate ALLOWED_GITHUB_USERS
    Auth->>Auth: Generate authorization code
    Auth->>Redis: Store oauth:code:{code}<br/>with user info<br/>TTL: 1 year
    Auth->>Client: 302 Redirect<br/>Location: redirect_uri?code=auth_code&state=...
```

### 3. Token Exchange Flow

```{mermaid}
sequenceDiagram
    participant Client
    participant Traefik
    participant Auth
    participant Redis
    
    Client->>Traefik: POST /token<br/>client_id=abc<br/>client_secret=xyz<br/>code=auth_code<br/>code_verifier=pkce_verifier
    Traefik->>Auth: Route to Auth Service
    Auth->>Redis: Get oauth:client:{client_id}
    Redis-->>Auth: Client data
    Auth->>Auth: Validate client_secret
    Auth->>Redis: Get oauth:code:{code}
    Redis-->>Auth: Code data + user info
    Auth->>Auth: Validate PKCE<br/>SHA256(code_verifier) = code_challenge
    Auth->>Auth: Generate JWT<br/>sub: user_id<br/>username: github_login<br/>email: user_email<br/>client_id: abc
    Auth->>Auth: Generate refresh_token
    Auth->>Redis: Store oauth:token:{jti}<br/>TTL: 30 days
    Auth->>Redis: Store oauth:refresh:{token}<br/>TTL: 1 year
    Auth->>Redis: Delete oauth:code:{code}
    Auth->>Client: 200 OK<br/>{access_token: JWT,<br/>refresh_token: token,<br/>expires_in: 2592000}
```

### 4. MCP Request Flow (Authenticated)

```{mermaid}
sequenceDiagram
    participant Client
    participant Traefik
    participant Auth
    participant MCP
    participant StdioServer
    
    Client->>Traefik: POST /mcp<br/>Authorization: Bearer {JWT}<br/>{jsonrpc: "2.0", method: "initialize"}
    
    Note over Traefik: ForwardAuth Middleware
    Traefik->>Auth: GET /verify<br/>Authorization: Bearer {JWT}
    Auth->>Auth: Validate JWT signature<br/>Check expiration<br/>Extract claims
    Auth->>Traefik: 200 OK<br/>X-User-Id: 12345<br/>X-User-Name: johndoe<br/>X-Auth-Token: {JWT}
    
    Note over Traefik: Route to MCP Service
    Traefik->>MCP: POST /mcp<br/>+ User headers<br/>+ Request body
    
    Note over MCP: mcp-streamablehttp-proxy
    MCP->>MCP: Create/find session<br/>for user
    MCP->>StdioServer: Write JSON-RPC<br/>to stdin
    StdioServer->>StdioServer: Process MCP<br/>protocol request
    StdioServer->>MCP: Write response<br/>to stdout
    MCP->>Traefik: HTTP 200<br/>JSON-RPC response
    Traefik->>Client: Forward response
```

## Security Architecture

### Authentication Layers

```{mermaid}
graph TB
    subgraph "Security Layers"
        L1[1. TLS/HTTPS<br/>Traefik + Let's Encrypt]
        L2[2. OAuth Client Auth<br/>client_id + client_secret]
        L3[3. User Authentication<br/>GitHub OAuth + Whitelist]
        L4[4. Token Authentication<br/>JWT Bearer tokens]
        L5[5. PKCE Protection<br/>S256 code challenges]
    end
    
    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 --> L5
    
    classDef security fill:#faa,stroke:#333,stroke-width:2px
    class L1,L2,L3,L4,L5 security
```

### Security Boundaries

| Boundary | Access Level | Authentication Required |
|----------|--------------|------------------------|
| **Public Access** | `/register`, `/.well-known/*` | None |
| **Client-Authenticated** | `/token` | client_id + client_secret |
| **User-Authenticated** | `/authorize` | GitHub login |
| **Bearer-Authenticated** | All `/mcp` endpoints | Valid JWT |
| **Registration-Authenticated** | `/register/{client_id}` | registration_access_token |

### Token Types and Security

```{mermaid}
graph LR
    subgraph "Token Types"
        RT[registration_access_token<br/>RFC 7592 client management]
        AT[access_token<br/>JWT with user + client claims]
        RFT[refresh_token<br/>Renew access tokens]
        AC[authorization_code<br/>One-time user-client binding]
    end
    
    subgraph "Security Properties"
        S1[32-byte random]
        S2[RS256/HS256 signed]
        S3[Opaque token]
        S4[5-min expiry]
    end
    
    RT --> S1
    AT --> S2
    RFT --> S3
    AC --> S4
```

### PKCE Flow Protection

```{mermaid}
graph LR
    CV[code_verifier<br/>43-128 chars random] --> H[SHA256 Hash]
    H --> CC[code_challenge]
    CC --> AUTH[/authorize request]
    AUTH --> CODE[auth code]
    CODE --> TOKEN[/token request]
    CV --> TOKEN
    TOKEN --> V{Verify<br/>SHA256(verifier) = challenge?}
    V -->|Yes| GRANT[Grant tokens]
    V -->|No| DENY[Deny 400]
```

## Architectural Decisions

### Why Three Layers?

1. **Traefik (Routing)**
   - Centralizes all routing logic
   - Handles TLS termination uniformly
   - Enforces authentication via middleware
   - No business logic = high reliability

2. **Auth Service (OAuth)**
   - Isolated OAuth implementation
   - No knowledge of MCP protocols
   - Reusable across different services
   - Single responsibility principle

3. **MCP Services (Protocol)**
   - Pure protocol implementations
   - No authentication concerns
   - Can use official servers unmodified
   - Easy to add/remove services

### Why mcp-streamablehttp-proxy?

```{mermaid}
graph TB
    subgraph "Benefits"
        B1[Wraps official servers<br/>without modification]
        B2[HTTP/SSE transport<br/>for web clients]
        B3[Session management<br/>and lifecycle control]
        B4[Error translation<br/>stdio → HTTP]
        B5[Horizontal scaling<br/>possibilities]
    end
    
    subgraph "Architecture"
        HTTP[HTTP Request] --> PROXY[mcp-streamablehttp-proxy]
        PROXY --> STDIO[stdio pipes]
        STDIO --> MCP[Official MCP Server]
    end
    
    B1 & B2 & B3 & B4 & B5 -.-> PROXY
```

### Why Redis?

| Feature | Benefit |
|---------|---------|
| **Fast in-memory storage** | Low latency for auth flows |
| **Built-in TTL** | Automatic token expiration |
| **Atomic operations** | Secure state transitions |
| **Persistence options** | Survives restarts |
| **Pub/Sub capabilities** | Future real-time features |
| **Cluster support** | Horizontal scaling ready |

### Why GitHub OAuth?

- **Trusted Identity Provider**: No password management
- **Developer-Focused**: Target audience already has accounts
- **Strong Security**: 2FA, security keys, audit logs
- **Rich Profile Data**: Username, email, organizations
- **OAuth Standards**: Well-documented, reliable
- **No Cost**: Free for public and private repos

## Network Topology

```{mermaid}
graph TB
    subgraph "Internet"
        USERS[External Users]
    end
    
    subgraph "Docker Host"
        subgraph "Public Network"
            TRAEFIK[Traefik :443/:80]
        end
        
        subgraph "Internal Network"
            AUTH[Auth :8000]
            REDIS[Redis :6379]
            MCP1[mcp-fetch :3000]
            MCP2[mcp-filesystem :3000]
            MCPN[... more services]
        end
    end
    
    USERS -.->|HTTPS Only| TRAEFIK
    TRAEFIK -->|Internal HTTP| AUTH
    TRAEFIK -->|Internal HTTP| MCP1
    TRAEFIK -->|Internal HTTP| MCP2
    AUTH <-->|Redis Protocol| REDIS
    
    style USERS fill:#f96,stroke:#333,stroke-width:2px
    style TRAEFIK fill:#9cf,stroke:#333,stroke-width:2px
    style AUTH fill:#fc9,stroke:#333,stroke-width:2px
    style REDIS fill:#c9f,stroke:#333,stroke-width:2px
    style MCP1 fill:#9fc,stroke:#333,stroke-width:2px
    style MCP2 fill:#9fc,stroke:#333,stroke-width:2px
```

### Network Security

- **Single Entry Point**: All traffic through Traefik
- **Internal Isolation**: Services can't be accessed directly
- **No External Ports**: Only 80/443 exposed
- **TLS Everywhere**: HTTPS enforced externally
- **Network Segmentation**: Separate networks for different concerns

## Next Steps

- [System Components](architecture/components.md) - Detailed component design
- [OAuth Flow](architecture/oauth-flow.md) - Complete OAuth implementation
- [MCP Integration](architecture/mcp-integration.md) - Protocol bridging details
- [Security Architecture](architecture/security.md) - Security deep dive