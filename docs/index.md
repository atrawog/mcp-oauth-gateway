# MCP OAuth Gateway Documentation

```{toctree}
:hidden:

overview
```

## Welcome to MCP OAuth Gateway

The **MCP OAuth Gateway** is a comprehensive OAuth 2.1 compliant gateway for Model Context Protocol (MCP) services. It provides secure authentication, dynamic client registration, and seamless integration with multiple MCP service implementations.

## Key Features

### 🔐 OAuth 2.1 Compliance
- Full implementation of OAuth 2.1 specification
- RFC 7591 Dynamic Client Registration
- RFC 7592 Client Management
- PKCE (RFC 7636) support for enhanced security
- GitHub OAuth integration for user authentication

### 🚀 MCP Protocol Support
- StreamableHTTP transport implementation
- Support for both proxy pattern (wrapping official servers) and native implementations
- Session management with secure session IDs
- Multiple protocol version support (2024-11-05, 2025-03-26, 2025-06-18)

### 🏗️ Production-Ready Architecture
- Traefik reverse proxy with automatic SSL via Let's Encrypt
- Redis for token and session storage
- Docker Compose orchestration
- Health checks for all services
- Comprehensive logging and monitoring

### 🛠️ Developer Experience
- Blessed trinity of tools: `just`, `pixi`, `docker-compose`
- Automated testing with real services (no mocks!)
- Sidecar coverage testing for production containers
- Comprehensive justfile with 100+ commands

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-oauth-gateway
cd mcp-oauth-gateway

# Copy and configure environment
cp .env.example .env
# Edit .env with your configuration

# Generate JWT secret
just generate-jwt-secret

# Build and start all services
just up

# Check service health
just check-services
```

## Documentation Structure

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} Getting Started
:link: overview
:link-type: doc

Learn about the gateway architecture and core concepts
:::

:::{grid-item-card} Development Tools
:link: justfile-reference
:link-type: doc

Complete reference for all justfile commands and workflows
:::

:::{grid-item-card} Python Packages
:link: packages/index
:link-type: doc

Documentation for all Python packages in the gateway
:::

:::{grid-item-card} Service Implementations
:link: services/index
:link-type: doc

Detailed documentation for all MCP and infrastructure services
:::

::::

## Sacred Commandments

This project follows the **Ten Sacred Commandments of Divine Python Development** as decreed in CLAUDE.md:

1. **No Mocks or Burn in Production Hell** - Real testing only!
2. **The Holy Trinity of Tools** - just, pixi, docker-compose
3. **Sacred Project Structure** - Divine isolation is mandatory
4. **Configuration Through .env** - All config flows through .env
5. **Docker Compose for All Services** - Compose is the divine orchestrator
6. **Pytest and Coverage** - Pytest is the only true test runner
7. **Real Health Checks** - Only healthchecks save from random failures
8. **Centralized Logging** - Scattered logs = lost wisdom
9. **Document with Jupyter Book** - Divine documentation tooling

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/yourusername/mcp-oauth-gateway/issues)
- Documentation: You're already here!
- CLAUDE.md: The sacred development guidelines
