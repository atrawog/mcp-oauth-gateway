# MCP OAuth Gateway: Complete Documentation

Welcome to the comprehensive documentation for the MCP OAuth Gateway - a production-ready OAuth 2.1 authentication system for Model Context Protocol (MCP) services.

```{image} https://img.shields.io/badge/MCP-2025--06--18-blue
:alt: MCP Protocol Version
```
```{image} https://img.shields.io/badge/OAuth-2.1-green
:alt: OAuth 2.1 Compliant
```
```{image} https://img.shields.io/badge/RFC-7591%20%7C%207592-orange
:alt: RFC Compliant
```

## Overview

The MCP OAuth Gateway is an OAuth 2.1 Authorization Server that adds authentication to any MCP (Model Context Protocol) server without requiring code modifications. It acts as a complete Authorization Server while using GitHub as the Identity Provider (IdP) for user authentication.

```{warning}
**Reference Implementation and Test Platform**

This gateway serves as a reference implementation for MCP protocol development and a test platform for future protocol iterations. While we follow security best practices, this implementation:

- Is primarily intended for MCP protocol testing and development
- Likely contains bugs and security vulnerabilities
- Should NOT be used in production without thorough security review
- Is experimental software that may change significantly

**Use at your own risk** - especially in production environments.
```

**Key Points:**
- **Zero Code Modification**: Protects any MCP server without changing the server code
- **OAuth Authorization Server**: Issues and manages tokens for MCP clients
- **GitHub Identity Provider**: Uses GitHub OAuth for user identity verification only
- **MCP 2025-06-18 Compliant**: Full support for required OAuth 2.1 with RFC 7591

## ✨ Key Features

### 🔐 Security & Authentication
- **OAuth 2.1 Compliant** - Full RFC 6749 implementation with modern security
- **RFC 7591 Dynamic Registration** - Automatic client onboarding (required by MCP 2025-06-18)
- **PKCE S256 Support** - Enhanced security for public clients
- **JWT Token Security** - Stateless, secure authentication

### 🏗️ Architecture Excellence
- **Trinity Separation** - Traefik, Auth Service, MCP Services isolation
- **Production Ready** - Health checks, monitoring, logging
- **Scalable Design** - Microservices architecture
- **Docker Native** - Full containerization with orchestration

### 🤖 MCP Protocol Support
- **MCP 2025-06-18** - Latest protocol version support
- **Multiple Services** - Fetch, Memory, Time, Sequential Thinking, Filesystem
- **Streamable HTTP** - HTTP transport for stdio-based servers
- **Real Integration** - No mocking, production-grade testing

### 🚨 Extensions Beyond MCP 2025-06-18 Protocol
- **RFC 7592 Client Management** - This gateway implements RFC 7592 (OAuth 2.0 Dynamic Client Registration Management Protocol)
- **NOT part of MCP spec** - RFC 7592 is an extension NOT included in MCP 2025-06-18
- **Full lifecycle management** - Read, update, and delete operations on registered clients
- **Supported by mcp-streamablehttp-client** - Our client library includes RFC 7592 support

### 🚀 Developer Experience
- **Comprehensive Testing** - 100% real service testing
- **Complete Documentation** - Every component documented
- **Easy Setup** - Single command deployment
- **Debugging Tools** - Extensive logging and monitoring

## 🏛️ The Holy Trinity Architecture

The gateway follows the divine principle of separation:

```{mermaid}
graph TB
    subgraph "Traefik - The Divine Router"
        T[Traefik Proxy]
    end
    
    subgraph "Auth Service - The OAuth Oracle"
        A[Auth Service]
        R[Redis Store]
    end
    
    subgraph "MCP Services - The Pure Protocol Servants"
        M1[MCP Fetch]
        M2[MCP Memory]
        M3[MCP Time]
        M4[MCP Sequential Thinking]
        M5[MCP Filesystem]
        M6[MCP Everything]
        M7[MCP Fetchs]
        M8[MCP Tmux]
        M9[MCP Playwright]
    end
    
    Client --> T
    T --> A
    T --> M1
    T --> M2
    T --> M3
    T --> M4
    T --> M5
    T --> M6
    T --> M7
    T --> M8
    T --> M9
    A --> R
```

1. **Traefik** - Routes requests and enforces authentication
2. **Auth Service** - Handles OAuth flows and token validation
3. **MCP Services** - Provide protocol functionality with no auth knowledge

## 🚀 Quick Start

Get up and running in minutes:

```bash
# Clone the repository
git clone https://github.com/atrawog/mcp-oauth-gateway.git
cd mcp-oauth-gateway

# Setup environment
cp .env.example .env
# Edit .env with your GitHub OAuth credentials

# Start all services
just up

# Run comprehensive tests
just test

# Generate OAuth tokens
just generate-oauth-token
```

## 📦 Available Services

| Service | Description | Capabilities |
|---------|-------------|--------------|
| **mcp-fetch** | Web content retrieval | HTTP requests, content fetching |
| **mcp-memory** | Knowledge graph storage | Entity management, relations, observations |
| **mcp-time** | Temporal operations | Current time, timezone conversions |
| **mcp-sequentialthinking** | Structured reasoning | Multi-step problem solving |
| **mcp-filesystem** | File operations | Read, write, directory management |
| **mcp-everything** | Combined functionality | All-in-one MCP capabilities |
| **mcp-fetchs** | Enhanced web fetching | Advanced HTTP operations, content processing |
| **mcp-tmux** | Terminal multiplexer | Session management, command execution |
| **mcp-playwright** | Browser automation | Web testing, screenshot capture, page interactions |

## 🐍 Python Packages

| Package | Purpose | Features |
|---------|---------|----------|
| **mcp-oauth-dynamicclient** | OAuth client library | RFC 7591 (MCP required), RFC 7592 (NOT in MCP spec), PKCE |
| **mcp-streamablehttp-proxy** | Protocol bridge | stdio ↔ HTTP conversion |
| **mcp-streamablehttp-client** | Testing client | Protocol testing, OAuth integration |
| **mcp-fetch-streamablehttp-server** | Fetch server | Direct HTTP MCP implementation |

## 🎯 Use Cases

### AI Integration
- **Claude.ai** - Direct integration with Anthropic's AI assistant
- **Custom AI Systems** - Any MCP-compatible AI platform
- **Research Platforms** - Academic and research applications

### Business Applications
- **Content Management** - Automated web content retrieval
- **Knowledge Systems** - Graph-based information storage
- **Scheduling Systems** - Global timezone coordination
- **Problem Solving** - Structured analytical workflows

### Development Tools
- **API Testing** - Comprehensive MCP protocol testing
- **Integration Testing** - Real service validation
- **Development Workflows** - Debugging and monitoring tools

## 📖 Documentation Sections

```{grid} 2
:gutter: 3

```{grid-item-card} 🚀 Getting Started
:link: quickstart/index
:link-type: doc

Installation, setup, and basic usage to get you running quickly.
```

```{grid-item-card} 🏗️ Architecture
:link: architecture/index
:link-type: doc

Deep dive into system design, OAuth flows, and security model.
```

```{grid-item-card} 🛠️ Services
:link: services/index
:link-type: doc

Complete documentation for all MCP services and their capabilities.
```

```{grid-item-card} 📦 Packages
:link: packages/index
:link-type: doc

Python package documentation with API references and examples.
```

```{grid-item-card} 🔌 API Reference
:link: api/index
:link-type: doc

Complete API documentation for OAuth and MCP endpoints.
```

```{grid-item-card} 🚀 Integration
:link: integration/index
:link-type: doc

Integration guides for Claude.ai and custom MCP clients.
```
```

## 🛡️ Security & Compliance

### MCP 2025-06-18 Protocol Requirements
- **OAuth 2.1** - Modern authentication standard
- **RFC 7591** - Dynamic client registration (REQUIRED by MCP 2025-06-18)
- **PKCE** - Proof Key for Code Exchange
- **TLS/HTTPS** - All communications encrypted

### Extensions Beyond MCP 2025-06-18
- **RFC 7592** - Client configuration management (NOT part of MCP 2025-06-18 spec!)
  - Allows clients to read their registration (GET /register/{client_id})
  - Allows clients to update their registration (PUT /register/{client_id})
  - Allows clients to delete themselves (DELETE /register/{client_id})
- **GitHub OAuth Integration** - User identity provider
- **JWT Token Management** - Stateless authentication
- **No Hardcoded Secrets** - Environment-based configuration

## 📊 Testing & Quality

- **100% Real Testing** - No mocking, production-grade validation
- **Comprehensive Coverage** - Every endpoint and service tested
- **Integration Tests** - Full OAuth and MCP protocol flows
- **Performance Testing** - Load and stress testing included
- **Security Testing** - Authentication and authorization validation

## 💡 The Sacred Commandments

This project follows the **Ten Sacred Commandments of Divine Python Development**:

1. **No Mocking** - Test against real services only
2. **Blessed Trinity** - Use just, pixi, and docker-compose
3. **Sacred Structure** - Follow divine directory layout
4. **Configuration Through .env** - No hardcoded values
5. **Docker-Compose Orchestration** - Service isolation
6. **Pytest with Sidecar Coverage** - Production truth only
7. **Docker Healthchecks** - No sleep commands allowed
8. **Log Segregation** - Centralized in ./logs/
9. **Jupyter Book Documentation** - MyST format blessed
10. **Root Cause Analysis** - Fix causes, not symptoms

## 🔗 External Resources

- [MCP Specification](https://modelcontextprotocol.org) - Official MCP protocol documentation
- [OAuth 2.1](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1) - OAuth 2.1 specification
- [RFC 7591](https://datatracker.ietf.org/doc/html/rfc7591) - Dynamic client registration
- [RFC 7592](https://datatracker.ietf.org/doc/html/rfc7592) - Client configuration management
- [Claude.ai](https://claude.ai) - Anthropic's AI assistant
- [Traefik](https://traefik.io) - Cloud native reverse proxy

## 🤝 Contributing

We welcome contributions! Please see our {doc}`development/contributing` guide for details on:

- Setting up development environment
- Running tests and ensuring quality
- Submitting pull requests
- Following coding standards
- Adding new services and features

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](https://github.com/atrawog/mcp-oauth-gateway/blob/main/LICENSE) file for details.

---

**Ready to get started?** Check out our {doc}`quickstart/installation` guide!