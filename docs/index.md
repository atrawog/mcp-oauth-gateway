# MCP OAuth Gateway

Welcome to the sacred MCP OAuth Gateway documentation!

This gateway implements OAuth 2.1 with RFC 7591 dynamic client registration to protect MCP (Model Context Protocol) services.

## The Holy Trinity of Architecture

The gateway follows the divine principle of separation:

1. **Traefik** - The Divine Router
2. **Auth Service** - The OAuth Oracle  
3. **MCP Services** - The Pure Protocol Servants

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd mcp-oauth-gateway

# Copy and configure environment
cp .env.example .env
# Edit .env with your values

# Start all services
just up

# Run tests
just test
```

## Key Features

- ✓ OAuth 2.1 compliant authentication
- ✓ RFC 7591 dynamic client registration
- ✓ PKCE support with S256 challenge
- ✓ Claude.ai integration ready
- ✓ MCP Protocol 2025-06-18 compliant
- ✓ Production-ready with healthchecks
- ✓ Sidecar coverage for testing

## The Sacred Commandments

This project follows the Ten Sacred Commandments of Development:

1. **No Mocking** - Test against real services only
2. **Blessed Trinity** - Use just, pixi, and docker-compose
3. **Sacred Structure** - Follow the divine directory layout
4. **Configuration Through .env** - No hardcoded values
5. **Docker-Compose Orchestration** - Service isolation
6. **Pytest with Sidecar Coverage** - Production truth only
7. **Docker Healthchecks** - No sleep commands
8. **Log Segregation** - Centralized in ./logs/
9. **Jupyter Book Documentation** - MyST format only
10. **Root Cause Analysis** - Fix causes, not symptoms

## Next Steps

- {doc}`architecture/index` - Understand the system design
- {doc}`api/index` - Explore the API endpoints
- {doc}`deployment/index` - Deploy to production
- {doc}`claude-ai/index` - Integrate with Claude.ai