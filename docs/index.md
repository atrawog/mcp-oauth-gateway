# MCP OAuth Gateway

```{warning}
**Important Notice**: This is a reference implementation and test platform for the MCP protocol. While it strives for security best practices, this implementation likely contains bugs and security vulnerabilities. It is NOT recommended for production use without thorough security review. Use at your own risk.
```

## Welcome

The MCP OAuth Gateway is an OAuth 2.1 Authorization Server that adds authentication to any MCP (Model Context Protocol) server without requiring code modification. The gateway acts as an OAuth Authorization Server while using GitHub as the Identity Provider (IdP) for user authentication.

## Key Features

- **OAuth 2.1 Compliant**: Full implementation of OAuth 2.1 with PKCE support
- **RFC 7591/7592 Support**: Dynamic client registration and management
- **Zero MCP Modification**: Protects any MCP server without code changes
- **GitHub Integration**: Uses GitHub OAuth for user authentication
- **Multiple MCP Services**: Supports various MCP protocol implementations
- **Production Architecture**: Three-tier separation with Traefik routing
- **Comprehensive Testing**: Full integration test suite with no mocking

## Quick Links

::::{grid} 1 1 2 3
:gutter: 2

:::{grid-item-card} Getting Started
:link: installation/quick-start
:link-type: doc

Quick installation and setup guide to get your gateway running
:::

:::{grid-item-card} Architecture
:link: architecture
:link-type: doc

Understand the three-tier architecture and component interactions
:::

:::{grid-item-card} MCP Services
:link: services/overview
:link-type: doc

Explore available MCP services and their capabilities
:::

:::{grid-item-card} API Reference
:link: api/oauth-endpoints
:link-type: doc

Complete API documentation for OAuth and MCP endpoints
:::

:::{grid-item-card} Development
:link: development/guidelines
:link-type: doc

Guidelines for contributing and extending the gateway
:::

:::{grid-item-card} Deployment
:link: deployment/production
:link-type: doc

Production deployment considerations and best practices
:::
::::

## Architecture Overview

The gateway implements a clean three-tier architecture:

```{mermaid}
graph TD
    Client[MCP Client] --> Traefik[Traefik Router]
    User[User Browser] --> Traefik
    
    Traefik --> |OAuth paths| Auth[Auth Service]
    Traefik --> |MCP paths + ForwardAuth| MCP[MCP Services]
    
    Auth --> |User auth| GitHub[GitHub OAuth]
    Auth --> |Token storage| Redis[(Redis)]
    
    MCP --> Proxy[mcp-streamablehttp-proxy]
    Proxy --> |stdio| Servers[Official MCP Servers]
```

## How It Works

1. **Client Registration**: MCP clients register dynamically via RFC 7591
2. **User Authentication**: Users authenticate through GitHub OAuth
3. **Token Issuance**: Gateway issues JWT tokens for authorized clients
4. **Request Routing**: Traefik routes authenticated requests to MCP services
5. **Protocol Bridging**: Proxy converts HTTP to stdio for MCP servers

## Requirements

- **Public Domain**: Real domains with DNS (no localhost deployments)
- **Docker & Docker Compose**: For service orchestration
- **Ports 80/443**: Must be accessible for Let's Encrypt certificates
- **GitHub OAuth App**: For user authentication

## Navigation

Use the navigation menu on the left to explore the documentation:

- **Overview**: High-level introduction to the gateway
- **Architecture**: Detailed component and flow documentation
- **Installation**: Step-by-step setup instructions
- **Services**: Documentation for each MCP service
- **Usage**: Day-to-day operation guides
- **Development**: Contributing and extending the gateway
- **API Reference**: Complete endpoint documentation
- **Deployment**: Production deployment guidance

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.