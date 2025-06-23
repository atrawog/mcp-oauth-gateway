# Overview

The MCP OAuth Gateway is a comprehensive solution for adding OAuth 2.1 authentication to MCP (Model Context Protocol) servers without requiring any modifications to the MCP server implementations themselves.

## What is MCP?

MCP (Model Context Protocol) is an emerging standard for communication between AI assistants and external tools/services. It defines a protocol for:
- Tool discovery and invocation
- Resource access and management
- Prompt and context handling
- Session management

## Why an OAuth Gateway?

While MCP servers provide powerful capabilities, they typically lack built-in authentication and authorization mechanisms. The MCP OAuth Gateway addresses this by:

1. **Adding Security**: Protecting MCP endpoints with industry-standard OAuth 2.1
2. **Maintaining Compatibility**: Working with unmodified MCP servers
3. **Enabling Multi-tenancy**: Supporting multiple clients and users
4. **Providing Audit Trail**: Tracking access and usage

## Core Capabilities

### OAuth 2.1 Implementation

The gateway provides a complete OAuth 2.1 authorization server with:
- Authorization code flow with PKCE
- Dynamic client registration (RFC 7591)
- Client management endpoints (RFC 7592)
- Token introspection and revocation
- JWT-based access tokens

### MCP Service Protection

- **Transparent Protection**: MCP servers require no OAuth awareness
- **Protocol Bridging**: HTTP-to-stdio conversion for compatibility
- **Session Management**: Stateful connections for MCP protocol
- **Multiple Services**: Support for various MCP implementations

### GitHub Integration

The gateway uses GitHub as an Identity Provider (IdP) for:
- User authentication
- Access control based on GitHub usernames
- Leveraging existing GitHub accounts
- No password management required

## Supported MCP Services

The gateway currently supports these MCP services:

| Service | Description | Use Cases |
|---------|-------------|-----------|
| **fetch** | Web content retrieval | API calls, web scraping |
| **filesystem** | File operations | Read/write workspace files |
| **memory** | Knowledge graph database | Persistent data storage |
| **time** | Timezone operations | Time conversions, scheduling |
| **sequential-thinking** | Structured reasoning | Complex problem solving |
| **playwright** | Browser automation | Web testing, scraping |
| **tmux** | Terminal multiplexing | Session management |
| **everything** | Test/demo server | Development, testing |

## Key Design Principles

### 1. **Separation of Concerns**
- Traefik handles routing
- Auth service manages OAuth
- MCP services remain pure protocol implementations

### 2. **No Modification Required**
- Official MCP servers used as-is
- OAuth layer added transparently
- Protocol compliance maintained

### 3. **Production Ready**
- Health checks for all services
- Comprehensive error handling
- Structured logging
- Automated SSL certificates

### 4. **Standards Compliance**
- OAuth 2.1 specification
- RFC 7591 (Dynamic Client Registration)
- RFC 7592 (Client Management)
- MCP protocol specifications

## Use Cases

### 1. **Secure MCP Deployment**
Deploy MCP services securely on the internet with proper authentication and authorization.

### 2. **Multi-tenant MCP Platform**
Provide MCP services to multiple clients/applications with isolated access control.

### 3. **Enterprise Integration**
Integrate MCP services into enterprise environments with OAuth-based SSO.

### 4. **Development Platform**
Test and develop MCP clients with a fully-featured OAuth flow.

## Limitations and Considerations

```{warning}
- **Not for Production**: This is a reference implementation with potential security vulnerabilities
- **Public Domain Required**: Cannot run on localhost due to OAuth and SSL requirements
- **GitHub Dependency**: Requires GitHub for user authentication
- **Resource Requirements**: Each service runs in its own container
```

## Next Steps

- [Quick Start Guide](installation/quick-start.md) - Get up and running quickly
- [Architecture Details](architecture.md) - Deep dive into the system design
- [Configuration Reference](installation/configuration.md) - Detailed configuration options
- [API Documentation](api/oauth-endpoints.md) - Complete API reference