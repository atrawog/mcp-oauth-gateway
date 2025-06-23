# Architecture Overview

The MCP OAuth Gateway is an OAuth 2.1 Authorization Server that adds authentication to any MCP server without requiring code modifications. It uses GitHub as the Identity Provider (IdP) for user authentication while acting as the Authorization Server for MCP clients.

```{caution}
This is a **reference implementation** and **test platform** for the MCP protocol. It is designed to explore and validate MCP protocol concepts and future iterations. While security best practices are followed, this implementation likely contains bugs and security vulnerabilities. It should not be deployed in production without extensive security review.
```

## Core Concept

The gateway solves a critical problem: MCP servers typically run without authentication. This gateway wraps any MCP server with OAuth 2.1 protection, allowing:

- **Zero modification** to existing MCP server code
- **Standard OAuth flows** for client authentication
- **GitHub OAuth** for user identity verification
- **Dynamic client registration** via RFC 7591
- **Automatic token management** and validation

## OAuth Architecture

### OAuth Roles and Responsibilities

1. **MCP OAuth Gateway (This Project)**
   - **Role**: OAuth 2.1 Authorization Server (AS)
   - **Responsibilities**:
     - Issues access tokens to MCP clients
     - Manages client registrations (RFC 7591)
     - Validates tokens for protected resources
     - Implements OAuth endpoints (`/authorize`, `/token`, `/register`)

2. **GitHub OAuth**
   - **Role**: Identity Provider (IdP)
   - **Responsibilities**:
     - Authenticates end users
     - Provides user identity claims
     - Issues GitHub access tokens (which the gateway exchanges for its own tokens)
     - Never directly interacts with MCP clients

3. **MCP Clients (e.g., Claude.ai)**
   - **Role**: OAuth Clients
   - **Interact with**: MCP OAuth Gateway (not GitHub directly)
   - **Flow**: Register → Authorize → Get tokens → Access MCP services

4. **MCP Servers**
   - **Role**: Protected Resources
   - **Requirements**: None - run unmodified
   - **Protection**: Traefik + Auth Service validate all requests

## Trinity Architecture

The system is built on three distinct layers that maintain strict separation of concerns:

```{mermaid}
graph TD
    A[MCP Client] --> B[Traefik Router]
    B --> C[Auth Service<br/>OAuth AS]
    B --> D[MCP Services<br/>Protected Resources]
    C --> E[Redis Storage]
    C --> F[GitHub OAuth<br/>Identity Provider]
    D --> G[MCP Server Time]
    D --> H[MCP Server Fetch]
    D --> I[MCP Server Memory]
    
    A -- "1. OAuth Flow" --> C
    C -- "2. User Auth" --> F
    F -- "3. User Identity" --> C
    C -- "4. Access Token" --> A
    A -- "5. API Request + Token" --> D
    B -- "ForwardAuth validation" --> C
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

## How It Protects Any MCP Server

The gateway achieves zero-modification protection through a clever proxy architecture:

1. **Original MCP Servers**: Run as stdio-based processes (unchanged)
2. **Proxy Layer**: `mcp-streamablehttp-proxy` wraps each MCP server
   - Converts HTTP requests to stdio JSON-RPC
   - Manages subprocess lifecycle
   - Provides HTTP endpoints (`/mcp`)
3. **Authentication Layer**: Traefik + Auth Service
   - Validates OAuth tokens before forwarding
   - Adds user context headers
   - Rejects unauthorized requests

### Example: Protecting MCP Fetch Server

```yaml
# Original server runs unmodified
mcp-fetch:
  image: atrawog/mcp-streamablehttp-proxy:latest
  environment:
    - SERVER_COMMAND=npx -y @modelcontextprotocol/server-fetch
    
# Traefik adds OAuth protection
labels:
  - "traefik.http.middlewares.mcp-auth.forwardauth.address=http://auth:8000/verify"
  - "traefik.http.routers.mcp-fetch.middlewares=mcp-auth"
```

The original MCP server code requires **zero changes** - authentication is added entirely through infrastructure.

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
  - Auth service verified via `/.well-known/oauth-authorization-server` endpoint
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
  - Auth service: OAuth discovery endpoint
  - MCP services: Protocol initialization handshake