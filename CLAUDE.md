# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository implements an OAuth 2.1 gateway for Model Context Protocol (MCP) servers. It wraps stdio-based MCP servers with OAuth authentication, allowing AI assistants to securely access MCP tools through authenticated HTTP/SSE connections.

**Core Innovation**: Transforms any stdio MCP server into an OAuth-protected StreamableHTTP service, enabling secure multi-user access with session management.

## Architecture

### Three-Layer Design

```
Client (Claude Desktop/Cursor)
    ↓ HTTP/SSE + OAuth tokens
Traefik (Reverse Proxy + ForwardAuth)
    ↓ Authenticated requests with user headers
Auth Service (mcp-oauth-dynamicclient)
    ↓ Token validation + user context
MCP Services (StreamableHTTP wrapped)
    ↓ MCP protocol over HTTP
Upstream MCP Servers (stdio)
```

### Key Components

1. **Traefik Layer**:
   - Entry point for all requests
   - Routes to auth service via ForwardAuth middleware
   - Injects user context headers (X-User-Id, X-User-Name) after auth
   - Forwards authenticated requests to MCP services

2. **Auth Service (mcp-oauth-dynamicclient)**:
   - RFC 7591/7592 compliant dynamic client registration
   - GitHub OAuth integration (authorization code + device flow)
   - PKCE-secured token exchange
   - JWT token validation
   - Redis-backed state storage
   - Auto-registers MCP servers from Docker labels

3. **MCP Services**:
   - **StreamableHTTP Proxy**: Wraps stdio MCP servers with HTTP/SSE transport
   - **StreamableHTTP Client**: Provides stdio interface to HTTP MCP servers
   - **Echo Servers**: Diagnostic tools with 9-11 comprehensive test tools
     - Stateless: Simple request/response echoing
     - Stateful: Session-based message queuing and polling

### OAuth Flow Selection

The system supports two OAuth flows based on client capabilities:

- **Authorization Code Flow** (Web Flow): For clients with browser access (Claude Desktop, Cursor)
- **Device Flow**: For headless/CLI clients without browser access

Decision tree in README.md section "Understanding the OAuth Flow" provides detailed flow selection logic.

## Repository Structure

**Submodule Organization**: This is a monorepo using Git submodules. Each MCP service and client library is a separate submodule:

- `mcp-oauth-dynamicclient/` - OAuth auth service
- `mcp-streamablehttp-proxy/` - Stdio → HTTP/SSE wrapper
- `mcp-streamablehttp-client/` - HTTP/SSE → stdio wrapper
- `mcp-echo-streamablehttp-server-stateless/` - Diagnostic echo server (stateless)
- `mcp-echo-streamablehttp-server-stateful/` - Diagnostic echo server (stateful)
- `mcp-echo-base/` - Shared base class for echo servers (eliminates 400+ lines duplication)

**Development Pattern**: Work inside submodules, test locally, then update parent repo to reference new commits.

## Code Patterns

### Echo Server Refactoring (Template Method Pattern)

Recent refactoring (documented in `docs/MCP_ECHO_SERVER_REFACTORING_PLAN.md`) eliminated 400+ lines of duplication between stateful/stateless echo servers:

1. **Base Class** (`mcp-echo-base/src/mcp_echo_base/server_base.py`):
   - Abstract base class `MCPEchoServerBase`
   - 100% identical methods: request handling, header validation, error responses, SSE streaming
   - Template methods: allow customization via abstract methods
   - Concrete implementations: 6 shared methods (~200 lines)
   - Uses `ContextVar` for per-request isolation (not `asyncio.current_task()` id dicts)

2. **Subclass Pattern**:
   - Stateless: Inherits base, implements 6 abstract methods
   - Stateful: Inherits base, adds SessionManager, implements session-aware methods
   - **Result**: 20% reduction in stateless (259 lines), 17-19% expected in stateful (250-270 lines)

3. **Abstract Methods** (must implement):
   - `get_server_type()` - Return "stateless" or "stateful"
   - `get_supported_versions()` - Protocol versions list
   - `get_additional_headers()` - Subclass-specific headers (e.g., mcp-session-id)
   - `get_additional_request_data()` - Subclass-specific data fields
   - `handle_initialize()` - Initialize request handler
   - `_log_request()` - Logging with subclass format

**Key Insight**: When adding new echo server variants, inherit from `MCPEchoServerBase` to avoid duplicating 200+ lines of HTTP/SSE handling code.

### Script Stack

Scripts in `scripts/` use **Starlette/uvicorn** consistently (not aiohttp):
- `scripts/callback_receiver.py` - OAuth callback server using Starlette `Route` + uvicorn
- `scripts/check_services_ready.py` - Uses Rich console markup (not ANSI escape codes)
- `utils.py` - `save_env_var` delegates to `python-dotenv` `set_key`

### Token Types

- **Access Token**: Short-lived JWT for API authentication (1 hour default)
- **Refresh Token**: Long-lived opaque token for renewing access tokens (30 days default)
- **Cookie-based**: Access token in HTTP-only cookie + refresh token in separate cookie

## Development Commands

All commands run through `justfile` (requires `just` command runner):

### Testing
```bash
just test [args]              # Run all tests with pytest
just test-parallel [args]     # Run tests in parallel (faster)
just test-unit               # Unit tests only
just test-integration        # Integration tests only
```

### Services
```bash
just up                      # Start all services
just up-fresh               # Start with fresh state (removes volumes)
just down                   # Stop all services
just logs [service]         # View logs (all or specific service)
just ensure-services-ready  # Wait for services to be healthy
```

### Development
```bash
just lint                   # Run ruff linter on all Python code
just format                 # Auto-format with ruff
just type-check            # Run mypy type checker
just docs-build            # Build Jupyter Book documentation
just docs-serve            # Serve docs locally
```

### Docker Operations
```bash
just build [service]        # Build Docker images
just rebuild [service]      # Rebuild from scratch (--no-cache)
just exec <service> <cmd>   # Execute command in container
```

## Environment Configuration

Configuration is environment-based. Copy `example.env` to `.env` and customize:

### Critical Variables
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` - GitHub OAuth app credentials
- `REDIS_HOST` / `REDIS_PORT` - State storage backend
- `GATEWAY_JWT_SECRET` - Secret for signing JWT tokens (generate with `just generate-jwt-secret`)
- `AUTH_SERVICE_PORT` - Auth service port (default: 3100)
- `ALLOWED_ORIGINS` - CORS origins for web clients

### Service Registration
MCP services auto-register via Docker labels:
- `mcp.server.name` - Service identifier
- `mcp.server.url` - Base URL for service
- `mcp.server.protocol` - MCP protocol version

See `docker-compose.yml` for examples.

## Testing Patterns

### Test Organization
- **Unit Tests**: Mock subprocess calls, test logic in isolation
- **Integration Tests**: Run against real fixtures, test end-to-end flows
- **Parallel Execution**: Use `just test-parallel` for faster CI/CD

### Echo Server Testing
Echo servers provide diagnostic tools for testing OAuth flows:
- **Stateless Tools** (9): headers_dump, request_echo, server_info, latency_test, error_test, metadata_echo, streaming_echo, client_info, network_diagnostics
- **Stateful Tools** (11): Same as stateless + session_info, session_echo

Use these tools to validate:
- OAuth token propagation (X-User-Id, X-User-Name headers)
- Session management (stateful only)
- Network connectivity through Traefik
- Error handling and logging

## Documentation

- **README.md** - Complete setup, architecture, configuration guide
- **docs/** - Jupyter Book documentation (architecture diagrams, OAuth flows)
- **MCP_ECHO_SERVER_REFACTORING_PLAN.md** - Code duplication analysis and refactoring guide

Build docs with `just docs-build`, serve locally with `just docs-serve`.

## Package Manager

This project uses **pixi** for Python dependency management (not pip/poetry/uv). Each submodule has its own `pixi.toml` for isolated environments.

## Important Notes

- **Submodule Workflow**: Always `git submodule update --init --recursive` after clone
- **Redis Required**: Auth service won't start without Redis connection
- **GitHub OAuth App**: Must create GitHub OAuth app and configure callback URLs before running
- **Port Conflicts**: Default ports (3100-3104) must be available or override in `.env`
- **Cookie Security**: In production, set `SECURE_COOKIES=true` to require HTTPS
