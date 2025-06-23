# Architecture

The MCP OAuth Gateway implements a clean three-tier architecture that separates routing, authentication, and MCP services. This design ensures security, scalability, and maintainability.

## High-Level Architecture

```{mermaid}
graph TB
    subgraph "External Clients"
        C1[Claude.ai]
        C2[IDE Plugins]
        C3[Custom Apps]
    end
    
    subgraph "Gateway Layer"
        T[Traefik<br/>Reverse Proxy]
        A[Auth Service<br/>OAuth Server]
        R[(Redis<br/>Token Store)]
    end
    
    subgraph "MCP Layer"
        P1[Proxy 1]
        P2[Proxy 2]
        P3[Proxy N]
        S1[MCP Server 1]
        S2[MCP Server 2]
        S3[MCP Server N]
    end
    
    subgraph "External Services"
        GH[GitHub OAuth]
    end
    
    C1 & C2 & C3 --> T
    T -->|OAuth paths| A
    T -->|MCP paths<br/>+ForwardAuth| P1 & P2 & P3
    A <--> R
    A <--> GH
    P1 --> S1
    P2 --> S2
    P3 --> S3
```

## Component Responsibilities

### 1. Traefik (Reverse Proxy)

**Primary Role**: Request routing and SSL termination

- **Route OAuth requests** to the Auth Service
- **Route MCP requests** to appropriate MCP services
- **Enforce authentication** via ForwardAuth middleware
- **Manage SSL certificates** with Let's Encrypt
- **Load balance** requests across service instances

**Key Features**:
- Priority-based routing rules
- Automatic HTTPS with ACME
- Docker service discovery
- Middleware chain support

### 2. Auth Service (OAuth Server)

**Primary Role**: OAuth 2.1 authorization server

- **Implement OAuth flows**: Authorization code with PKCE
- **Manage client registrations**: RFC 7591/7592 compliance
- **Issue and validate tokens**: JWT-based access tokens
- **Integrate with GitHub**: User authentication via OAuth
- **Store token state**: Redis-backed persistence

**Key Endpoints**:
- `/register` - Dynamic client registration
- `/authorize` - Authorization endpoint
- `/token` - Token exchange
- `/verify` - ForwardAuth validation
- `/.well-known/*` - OAuth discovery

### 3. MCP Services

**Primary Role**: Protocol implementation without auth awareness

- **Implement MCP protocol**: Tools, resources, prompts
- **Process requests**: Handle MCP JSON-RPC calls
- **Maintain sessions**: Stateful protocol support
- **Know nothing about OAuth**: Complete separation

**Service Types**:
- **Wrapped Services**: Official MCP servers via proxy
- **Native Services**: Direct HTTP implementations

### 4. Redis

**Primary Role**: Distributed state storage

- **OAuth state**: Authorization codes, PKCE verifiers
- **Access tokens**: JWT tracking and revocation
- **Client registrations**: Dynamic client data
- **Session state**: MCP session management

## Request Flow Patterns

### OAuth Authorization Flow

```{mermaid}
sequenceDiagram
    participant Client
    participant Traefik
    participant Auth
    participant GitHub
    participant Redis
    
    Client->>Traefik: GET /authorize
    Traefik->>Auth: Route to Auth Service
    Auth->>Client: Redirect to GitHub
    Client->>GitHub: Authenticate
    GitHub->>Client: Redirect with code
    Client->>Traefik: GET /callback?code=...
    Traefik->>Auth: Route to Auth Service
    Auth->>GitHub: Exchange code
    GitHub->>Auth: User info
    Auth->>Redis: Store authorization code
    Auth->>Client: Redirect with auth code
    Client->>Traefik: POST /token
    Traefik->>Auth: Route to Auth Service
    Auth->>Redis: Validate code
    Auth->>Client: Return JWT token
```

### MCP Request Flow

```{mermaid}
sequenceDiagram
    participant Client
    participant Traefik
    participant Auth
    participant MCP
    participant Server
    
    Client->>Traefik: POST /mcp<br/>Bearer token
    Traefik->>Auth: ForwardAuth /verify
    Auth->>Traefik: 200 OK + headers
    Traefik->>MCP: Forward request
    MCP->>Server: stdio JSON-RPC
    Server->>MCP: stdio response
    MCP->>Traefik: HTTP response
    Traefik->>Client: Final response
```

## Security Architecture

### Authentication Layers

1. **Client Authentication**: OAuth client credentials
2. **User Authentication**: GitHub OAuth integration
3. **Token Validation**: JWT signature verification
4. **Request Authorization**: ForwardAuth middleware

### Security Boundaries

- **Public Endpoints**: Registration, discovery
- **Authenticated Endpoints**: Token, MCP services
- **Internal Only**: Redis, service-to-service

### Token Security

- **JWT Signing**: RS256 with RSA keys
- **Token Storage**: Redis with TTL
- **Token Revocation**: Immediate invalidation
- **Session Binding**: User-specific tokens

## Deployment Architecture

### Container Structure

```
mcp-oauth-gateway/
├── traefik/          # Reverse proxy container
├── auth/             # OAuth server container
├── mcp-fetch/        # MCP service container
├── mcp-filesystem/   # MCP service container
├── mcp-memory/       # MCP service container
└── redis/            # State storage container
```

### Network Architecture

- **Public Network**: External-facing services
- **Internal Networks**: Service-to-service communication
- **Bridge Networks**: Docker compose networking

### Volume Management

- **Certificates**: Traefik Let's Encrypt storage
- **Logs**: Centralized logging directory
- **Data**: Service-specific persistence

## Scalability Considerations

### Horizontal Scaling

- **Stateless Auth Service**: Multiple instances possible
- **Load Balanced MCP**: Round-robin distribution
- **Redis Cluster**: For high availability

### Performance Optimization

- **Connection Pooling**: Redis connections
- **Token Caching**: Reduce validation overhead
- **Health Checks**: Automatic failover

## Next Steps

- [Component Architecture](architecture/components.md) - Detailed component design
- [OAuth Flow](architecture/oauth-flow.md) - Complete OAuth implementation
- [MCP Integration](architecture/mcp-integration.md) - Protocol bridging details
- [Security Architecture](architecture/security.md) - Security deep dive