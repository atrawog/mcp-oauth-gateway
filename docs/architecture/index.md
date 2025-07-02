# Architecture Overview

The MCP OAuth Gateway implements a comprehensive OAuth 2.1 compliant authentication system for Model Context Protocol services, following the divine architectural principles of CLAUDE.md.

## High-Level Architecture

```{mermaid}
graph TB
    subgraph "External Clients"
        CLAUDE[Claude.ai]
        DESKTOP[Claude Desktop]
        API[API Clients]
    end

    subgraph "Gateway Infrastructure"
        subgraph "Layer 1: Routing"
            TRAEFIK[Traefik<br/>SSL + Routing]
        end

        subgraph "Layer 2: Authentication"
            AUTH[Auth Service<br/>OAuth 2.1]
            REDIS[(Redis<br/>Token Storage)]
        end

        subgraph "Layer 3: MCP Services"
            PROXY[Proxy Pattern<br/>Services]
            NATIVE[Native Pattern<br/>Services]
        end
    end

    subgraph "External Auth"
        GITHUB[GitHub OAuth]
    end

    CLAUDE -->|HTTPS| TRAEFIK
    DESKTOP -->|HTTPS| TRAEFIK
    API -->|HTTPS| TRAEFIK

    TRAEFIK -->|ForwardAuth| AUTH
    TRAEFIK -->|Authenticated| PROXY
    TRAEFIK -->|Authenticated| NATIVE

    AUTH <-->|OAuth Flow| GITHUB
    AUTH <-->|Storage| REDIS
```

## Core Design Principles

### 1. Divine Separation of Concerns

Each layer has a single, well-defined responsibility:

- **Layer 1 (Traefik)**: Routing and SSL only
- **Layer 2 (Auth)**: OAuth and authentication only
- **Layer 3 (MCP)**: Protocol implementation only

### 2. No Mocks, Real Systems

All components are real, production-ready systems:

- Real OAuth 2.1 implementation
- Real Redis for storage
- Real SSL certificates
- Real health checks

### 3. Configuration Through Environment

All configuration flows through `.env`:

```bash
# Base configuration
BASE_DOMAIN=example.com
ACME_EMAIL=admin@example.com

# OAuth configuration
GITHUB_CLIENT_ID=xxx
GITHUB_CLIENT_SECRET=xxx

# Service enablement
MCP_FETCH_ENABLED=true
MCP_FILESYSTEM_ENABLED=true
```

## Architectural Patterns

### Authentication Pattern

The gateway implements a dual-realm authentication model:

1. **MCP Client Realm**: For external MCP clients (Claude.ai, IDEs)
2. **User Authentication Realm**: For human users via GitHub OAuth

### Service Implementation Patterns

Two blessed patterns for MCP services:

1. **Proxy Pattern**: Wraps official stdio servers
2. **Native Pattern**: Direct StreamableHTTP implementation

### Communication Patterns

All communication follows these patterns:

- External → Gateway: HTTPS with Bearer tokens
- Internal services: Docker network communication
- No service-to-service authentication (trust boundary at edge)

## Security Architecture

### Defense in Depth

Multiple security layers:

1. **Network Layer**: HTTPS only, no HTTP
2. **Authentication Layer**: OAuth 2.1 with PKCE
3. **Authorization Layer**: ForwardAuth middleware
4. **Application Layer**: No auth logic in services

### Zero Trust Model

- Every external request authenticated
- No implicit trust between layers
- Minimal privilege access
- Comprehensive audit logging

## Data Flow

### Client Registration Flow

```
1. Client → POST /register
2. Auth → Generate client_id
3. Auth → Store in Redis
4. Auth → Return credentials
5. Client → Store registration_access_token
```

### Request Authentication Flow

```
1. Client → Request with Bearer token
2. Traefik → ForwardAuth to /verify
3. Auth → Validate token in Redis
4. Auth → Return user info headers
5. Traefik → Forward to MCP service
6. Service → Process request
7. Service → Return response
```

## Scalability Architecture

### Horizontal Scaling

- **Traefik**: Multiple instances with shared config
- **Auth**: Stateless with Redis backend
- **MCP Services**: Scale based on pattern
  - Stateless: Easy horizontal scaling
  - Stateful: Requires session affinity

### Performance Optimization

- Connection pooling
- Redis caching
- Health check optimization
- Resource limits per service

## Deployment Architecture

### Container Orchestration

All services run in Docker containers:

- Shared docker-compose configuration
- Named volumes for persistence
- Health checks for reliability
- Centralized logging

### Network Architecture

Single shared network (`public`):

- Service discovery by name
- Internal communication
- No external exposure except Traefik

## Monitoring Architecture

### Health Monitoring

Three-tier health check system:

1. **Container Health**: Docker health checks
2. **Application Health**: HTTP health endpoints
3. **Protocol Health**: MCP initialization checks

### Logging Architecture

Centralized logging pattern:

```
./logs/
├── traefik/
├── auth/
├── redis/
└── {service-name}/
```

## Technology Stack

### Infrastructure
- **Traefik v3.0**: Reverse proxy and SSL
- **Redis 7.0**: Token and session storage
- **Docker Compose**: Container orchestration

### Languages & Frameworks
- **Python 3.12**: Primary language
- **FastAPI**: Web framework
- **Authlib**: OAuth implementation
- **httpx**: HTTP client

### Protocols
- **OAuth 2.1**: Authentication
- **MCP**: Model Context Protocol
- **StreamableHTTP**: Transport protocol

## Next Steps

- [System Components](system-components) - Detailed component architecture
- [OAuth Flow](oauth-flow) - Authentication flow details
- [MCP Integration](mcp-integration) - Protocol implementation
- [Security](security) - Security architecture deep dive
