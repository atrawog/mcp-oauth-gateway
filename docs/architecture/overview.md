# Architecture Overview

The MCP OAuth Gateway follows a microservices architecture with clear separation of concerns, implementing the **Holy Trinity** pattern for maximum security and maintainability.

## Trinity Architecture

The system is built on three distinct layers that maintain strict separation of concerns:

```{mermaid}
graph TD
    A[Traefik Router] --> B[Auth Service]
    A --> C[MCP Services]
    B --> D[Redis Storage]
    B --> E[GitHub OAuth]
    C --> F[MCP Server Time]
    C --> G[MCP Server Fetch]
    C --> H[MCP Server Memory]
    
    A -- "Routes OAuth paths" --> B
    A -- "Routes MCP paths" --> C
    A -- "ForwardAuth validation" --> B
```

### Layer 1: Traefik (The Divine Router)
- **Purpose**: Request routing and traffic management
- **Responsibilities**:
  - Routes OAuth paths (`/register`, `/authorize`, `/token`) to Auth Service
  - Routes MCP paths (`/mcp`) to appropriate MCP services
  - Enforces authentication via ForwardAuth middleware
  - Provides HTTPS with Let's Encrypt certificates
  - Priority-based routing to prevent conflicts

### Layer 2: Auth Service (The OAuth Oracle)
- **Purpose**: Authentication and authorization management
- **Responsibilities**:
  - OAuth 2.1 + RFC 7591/7592 compliance
  - GitHub OAuth integration for user authentication
  - JWT token generation and validation
  - Client registration and management
  - Token verification for ForwardAuth requests

### Layer 3: MCP Services (The Protocol Servants)
- **Purpose**: MCP protocol implementation and business logic
- **Responsibilities**:
  - Run official MCP servers via mcp-streamablehttp-proxy
  - Bridge stdio MCP servers to HTTP endpoints
  - Provide `/mcp` endpoints
  - Handle MCP protocol (configurable version)
  - Maintain session state and message handling

## Component Interaction

### Authentication Flow
1. **Initial Request**: Client attempts to access MCP endpoint
2. **Authentication Check**: Traefik ForwardAuth validates with Auth Service
3. **OAuth Flow**: If unauthenticated, client goes through OAuth registration/authorization
4. **Token Validation**: Auth Service validates Bearer tokens
5. **Request Forwarding**: Authenticated requests routed to MCP services

### Service Communication
- **Traefik ↔ Auth Service**: HTTP requests for token validation
- **Traefik ↔ MCP Services**: HTTP requests with authenticated headers
- **Auth Service ↔ Redis**: Token and session storage
- **Auth Service ↔ GitHub**: OAuth user authentication
- **MCP Services ↔ Official Servers**: stdio bridging via proxy

## Security Model

### Dual Authentication Realms
The system implements two separate authentication realms:

1. **MCP Gateway Client Realm** (RFC 7591/7592)
   - Dynamic client registration
   - Client credential management
   - Registration access tokens

2. **User Authentication Realm** (OAuth 2.0)
   - GitHub OAuth integration
   - User identity verification
   - Access token issuance

### Security Principles
- **Zero Trust**: Every request is validated
- **Least Privilege**: Services only know what they need
- **Defense in Depth**: Multiple security layers
- **Explicit Deny**: Default deny with explicit allow

## Protocol Flow

### MCP Protocol Implementation
```{mermaid}
sequenceDiagram
    participant C as Claude.ai
    participant T as Traefik
    participant A as Auth Service
    participant M as MCP Service
    
    C->>T: POST /mcp (no auth)
    T->>A: ForwardAuth validation
    A->>T: 401 Unauthorized
    T->>C: 401 + WWW-Authenticate
    
    C->>T: GET /.well-known/oauth-authorization-server
    T->>A: Route to Auth Service
    A->>C: OAuth metadata
    
    C->>T: POST /register
    T->>A: Client registration
    A->>C: Client credentials
    
    Note over C,A: OAuth authorization flow
    
    C->>T: POST /mcp (with Bearer token)
    T->>A: Token validation
    A->>T: Valid + user headers
    T->>M: Forward with auth headers
    M->>C: MCP response
```

### Service Health and Monitoring
- **Health Checks**: 
  - Auth service exposes `/health` endpoint for HTTP health checks
  - MCP services verified via MCP protocol initialization
- **Dependency Verification**: Services check upstream dependencies
- **Graceful Degradation**: Services handle partial failures
- **Centralized Logging**: All logs flow to `./logs/` directory

## Scalability Considerations

### Horizontal Scaling
- **Stateless Services**: MCP services can be scaled independently
- **Session Affinity**: Redis provides shared session storage
- **Load Balancing**: Traefik handles traffic distribution

### Performance Optimization
- **Connection Pooling**: Efficient resource utilization
- **Caching Strategy**: Redis for session and token caching
- **Health Check Optimization**: Fast startup and readiness detection
  - Auth service: HTTP `/health` endpoint
  - MCP services: Protocol initialization handshake