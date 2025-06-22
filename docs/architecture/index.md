# Architecture & Design

The MCP OAuth Gateway implements a sophisticated multi-tier architecture designed for security, scalability, and maintainability. This section provides comprehensive documentation of the system's architectural decisions and design patterns.

## Core Principles

The gateway architecture is built on several fundamental principles:

### 🔱 Separation of Concerns
- **Clear boundaries** between authentication, routing, and protocol handling
- **Single responsibility** for each service component
- **Minimal coupling** between architectural tiers

### 🛡️ Security First
- **Zero trust** networking model
- **Defense in depth** with multiple security layers
- **Principle of least privilege** for all components

### 📊 Production Readiness
- **High availability** through redundancy
- **Horizontal scalability** for all services
- **Comprehensive monitoring** and observability

### 🧪 Testability
- **Real service testing** without mocking
- **Isolated components** for unit testing
- **End-to-end validation** of all flows

## Architectural Overview

```{mermaid}
graph TB
    subgraph "External Clients"
        C1[Claude.ai]
        C2[MCP Clients]
        C3[Web Browsers]
    end
    
    subgraph "Edge Layer"
        T[Traefik Proxy]
        SSL[Let's Encrypt]
    end
    
    subgraph "Authentication Layer"
        A[Auth Service]
        R[Redis Cache]
        G[GitHub OAuth]
    end
    
    subgraph "Protocol Layer"
        P[mcp-streamablehttp-proxy]
        S1[MCP Fetch]
        S2[MCP Memory]
        S3[Other Services...]
    end
    
    C1 --> T
    C2 --> T
    C3 --> T
    T --> SSL
    T --> A
    T --> P
    A --> R
    A --> G
    P --> S1
    P --> S2
    P --> S3
```

## Key Components

### 1. Edge Layer (Traefik)
- **Reverse proxy** and load balancer
- **TLS termination** with automatic certificate management
- **Request routing** based on hostnames and paths
- **Authentication enforcement** via ForwardAuth middleware

### 2. Authentication Layer
- **OAuth 2.1 implementation** with all required endpoints
- **Dynamic client registration** (RFC 7591)
- **Client management** (RFC 7592)
- **Token validation** and session management

### 3. Protocol Layer
- **MCP protocol handling** via streamable HTTP
- **Service isolation** in Docker containers
- **Health monitoring** for all services
- **Unified API surface** for clients

## Design Patterns

### Trinity Architecture
The system follows a three-tier separation pattern:
1. **Routing tier** - Handles request distribution
2. **Authentication tier** - Manages security
3. **Service tier** - Provides functionality

### Microservices
- Each MCP service runs independently
- Services communicate only through well-defined interfaces
- Failure isolation prevents cascade failures

### Proxy Pattern
- `mcp-streamablehttp-proxy` wraps stdio-based MCP servers
- Provides HTTP interface without modifying original servers
- Enables authentication and monitoring

### Sidecar Pattern
- Coverage collection without code modification
- Monitoring and logging sidecars for observability
- Security policy enforcement at the edge

## Documentation Structure

```{toctree}
:maxdepth: 2

overview
trinity-separation
oauth-flow
mcp-protocol
traefik-routing
security-model
```

### In This Section

- **{doc}`overview`** - High-level system architecture
- **{doc}`trinity-separation`** - The three-tier design principle
- **{doc}`oauth-flow`** - OAuth 2.1 authentication flows
- **{doc}`mcp-protocol`** - MCP protocol implementation
- **{doc}`traefik-routing`** - Request routing and load balancing
- **{doc}`security-model`** - Security architecture and threat model

## Architecture Decisions

### Why Traefik?
- **Native Docker integration** with label-based configuration
- **Automatic service discovery** for dynamic scaling
- **Built-in Let's Encrypt** support for TLS
- **ForwardAuth middleware** for authentication integration

### Why Redis?
- **High performance** for session storage
- **TTL support** for automatic token expiration
- **Atomic operations** for concurrent access
- **Persistence options** for data durability

### Why Microservices?
- **Independent scaling** of services
- **Technology flexibility** per service
- **Fault isolation** and resilience
- **Simplified deployment** and updates

### Why OAuth 2.1?
- **Industry standard** for API authentication
- **Client flexibility** with dynamic registration
- **Token-based** stateless authentication
- **Extensible** with custom claims

## Performance Considerations

### Caching Strategy
- **Token caching** in Redis for fast validation
- **HTTP caching** headers for client optimization
- **Service response caching** where appropriate

### Connection Pooling
- **Database connections** pooled per service
- **HTTP keep-alive** for persistent connections
- **Redis connection** reuse for efficiency

### Resource Limits
- **Memory limits** per container
- **CPU quotas** for fair resource sharing
- **Request rate limiting** for protection

## Scalability

### Horizontal Scaling
- **Stateless services** enable easy scaling
- **Load balancing** via Traefik
- **Session affinity** when required

### Vertical Scaling
- **Resource limits** can be adjusted
- **Container orchestration** ready
- **Database scaling** strategies

## Monitoring & Observability

### Health Checks
- **Docker health** checks for containers
- **HTTP endpoints** for service health
- **Comprehensive status** reporting

### Logging
- **Centralized logging** in ./logs/
- **Structured logs** for parsing
- **Log rotation** and retention

### Metrics
- **Request metrics** from Traefik
- **Service metrics** from applications
- **System metrics** from Docker

## Security Architecture

### Network Security
- **TLS everywhere** with automatic certificates
- **Network isolation** between services
- **Firewall rules** at the edge

### Application Security
- **Input validation** at all endpoints
- **Output encoding** for safety
- **Rate limiting** for protection

### Data Security
- **Encryption at rest** for sensitive data
- **Encryption in transit** via TLS
- **Key rotation** strategies

## Next Steps

- Explore the {doc}`trinity-separation` for detailed component isolation
- Review {doc}`oauth-flow` for authentication implementation
- Check {doc}`security-model` for threat analysis