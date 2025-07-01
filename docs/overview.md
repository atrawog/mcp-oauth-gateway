# Overview

The MCP OAuth Gateway is a comprehensive authentication and authorization gateway for Model Context Protocol (MCP) services. It provides a secure, scalable, and RFC-compliant OAuth 2.1 implementation with dynamic client registration and seamless MCP service integration.

## Architecture Overview

The gateway follows a three-layer architecture as mandated by the divine separation of concerns:

```{mermaid}
graph TB
    subgraph "Layer 1: Traefik"
        T[Traefik Reverse Proxy]
        T --> |"OAuth paths"| A
        T --> |"MCP paths (authenticated)"| M
    end

    subgraph "Layer 2: Auth Service"
        A[Auth Service]
        A --> |"Token validation"| T
        A --> R[Redis Storage]
    end

    subgraph "Layer 3: MCP Services"
        M[MCP Services]
        M --> P[Proxy Pattern Services]
        M --> N[Native StreamableHTTP Services]
    end

    C[MCP Clients] --> |"HTTPS"| T
    U[Users] --> |"GitHub OAuth"| A
```

## Core Components

### 1. Traefik (Layer 1)
The divine router that handles all incoming requests:
- Routes OAuth endpoints to Auth Service
- Routes MCP endpoints to appropriate services
- Enforces authentication via ForwardAuth middleware
- Provides HTTPS with Let's Encrypt certificates
- Implements priority-based routing (4→3→2→1)

### 2. Auth Service (Layer 2)
The OAuth oracle that manages authentication:
- Implements OAuth 2.1 with PKCE support
- RFC 7591 Dynamic Client Registration
- RFC 7592 Client Management
- GitHub OAuth integration for user authentication
- JWT token generation and validation
- Redis-backed token storage

### 3. MCP Services (Layer 3)
The protocol servants that provide functionality:
- **Proxy Pattern**: Uses `mcp-streamablehttp-proxy` to wrap official stdio servers
- **Native Pattern**: Direct StreamableHTTP implementation
- Session management with `Mcp-Session-Id` headers
- Health checks via protocol initialization

## Key Features

### OAuth 2.1 Compliance
```
✅ Authorization Code Flow with PKCE
✅ Dynamic Client Registration (RFC 7591)
✅ Client Management (RFC 7592)
✅ Token Introspection
✅ Token Revocation
✅ Discovery Metadata (RFC 8414)
```

### MCP Protocol Support
```
✅ StreamableHTTP Transport
✅ JSON-RPC 2.0 Messages
✅ Session Management
✅ Multiple Protocol Versions
✅ Official Server Wrapping
✅ Native Implementations
```

### Security Features
```
✅ JWT with RS256 Signing
✅ Bearer Token Authentication
✅ Origin Header Validation
✅ CSRF Protection
✅ Secure Session IDs
✅ Token Expiration Management
```

## Service Types

### Infrastructure Services
1. **Traefik** - Reverse proxy and SSL termination
2. **Auth** - OAuth 2.1 authentication service
3. **Redis** - Token and session storage

### MCP Services

#### Proxy Pattern Services
These wrap official MCP servers using `mcp-streamablehttp-proxy`:
- **mcp-fetch** - Web content fetching
- **mcp-filesystem** - File system operations
- **mcp-memory** - Persistent storage
- **mcp-time** - Time/date operations
- **mcp-everything** - Comprehensive toolset
- **mcp-playwright** - Browser automation
- **mcp-sequentialthinking** - Sequential reasoning
- **mcp-tmux** - Terminal multiplexer

#### Native StreamableHTTP Services
These implement the protocol directly:
- **mcp-fetchs** - Native fetch implementation
- **mcp-echo-stateful** - Stateful echo with sessions
- **mcp-echo-stateless** - Stateless echo service

## Authentication Flow

The gateway supports two authentication realms:

### MCP Client Authentication
1. Client attempts to access `/mcp` endpoint
2. Receives 401 with `WWW-Authenticate: Bearer`
3. Discovers OAuth metadata at `/.well-known/oauth-authorization-server`
4. Registers via POST to `/register` (RFC 7591)
5. Receives client credentials
6. Obtains access token via OAuth flow
7. Uses bearer token for all subsequent requests

### User Authentication
1. User redirected to `/authorize` endpoint
2. Gateway redirects to GitHub OAuth
3. User authenticates with GitHub
4. Callback processes authorization
5. JWT token issued with user claims
6. Token valid for configured lifetime

## Configuration

All configuration flows through the sacred `.env` file:

```bash
# OAuth Configuration
GITHUB_CLIENT_ID=xxx
GITHUB_CLIENT_SECRET=xxx
GATEWAY_JWT_SECRET=xxx
CLIENT_LIFETIME=7776000  # 90 days, or 0 for eternal

# MCP Configuration
MCP_PROTOCOL_VERSION=2025-06-18
ENABLE_MCP_FETCH=true
ENABLE_MCP_FILESYSTEM=true
# ... other services

# Access Control
ALLOWED_GITHUB_USERS=user1,user2
```

## Development Workflow

The blessed trinity of tools:
1. **just** - All commands flow through justfile
2. **pixi** - Python package management
3. **docker-compose** - Service orchestration

```bash
# Common workflows
just up              # Start all services
just test            # Run tests
just logs -f auth    # Follow auth logs
just check-services  # Verify health
```

## Next Steps

- [Architecture Details](architecture/index) - Deep dive into system design
- [Justfile Reference](justfile-reference) - All available commands
- [Service Documentation](services/index) - Individual service details
- [API Reference](api/index) - Endpoint documentation
