# Python Packages Overview

The MCP OAuth Gateway consists of six Python packages, each serving a specific role in the architecture. All packages follow the sacred commandments of CLAUDE.md and are managed through the blessed pixi package manager.

## Package Architecture

```{mermaid}
graph TB
    subgraph "OAuth Layer"
        OAUTH[mcp-oauth-dynamicclient<br/>OAuth 2.1 Server]
    end

    subgraph "Client Layer"
        CLIENT[mcp-streamablehttp-client<br/>Client Bridge]
    end

    subgraph "Proxy Layer"
        PROXY[mcp-streamablehttp-proxy<br/>stdio to HTTP Bridge]
    end

    subgraph "Native Services"
        FETCH[mcp-fetch-streamablehttp-server<br/>Native Fetch]
        ECHO1[mcp-echo-streamablehttp-server-stateful<br/>Stateful Echo]
        ECHO2[mcp-echo-streamablehttp-server-stateless<br/>Stateless Echo]
    end

    CLIENT --> OAUTH
    CLIENT --> PROXY
    CLIENT --> FETCH
    CLIENT --> ECHO1
    CLIENT --> ECHO2

    PROXY --> |wraps| STDIO[Official MCP Servers]
```

## Package Summary

| Package | Version | Purpose | Key Dependencies |
|---------|---------|---------|------------------|
| **mcp-oauth-dynamicclient** | 0.2.0 | OAuth 2.1 server with RFC 7591/7592 | FastAPI, Authlib, Redis |
| **mcp-streamablehttp-client** | 0.2.0 | Client bridge for stdio↔HTTP | httpx, mcp, click |
| **mcp-streamablehttp-proxy** | 0.2.0 | Proxy for wrapping stdio servers | FastAPI, mcp, httpx |
| **mcp-fetch-streamablehttp-server** | 0.1.4 | Native fetch with SSRF protection | FastAPI, httpx, beautifulsoup4 |
| **mcp-echo-streamablehttp-server-stateful** | 0.2.0 | Stateful echo with sessions | FastAPI, mcp |
| **mcp-echo-streamablehttp-server-stateless** | 0.2.0 | Stateless echo service | FastAPI, mcp |

## Package Categories

### 🔐 OAuth Infrastructure

**[mcp-oauth-dynamicclient](mcp-oauth-dynamicclient)**
- Full OAuth 2.1 implementation
- Dynamic client registration (RFC 7591)
- Client management (RFC 7592)
- GitHub OAuth integration
- JWT token management
- Redis-backed storage

### 🌉 Bridge Components

**[mcp-streamablehttp-client](mcp-streamablehttp-client)**
- Enables stdio MCP clients to access HTTP servers
- OAuth token management
- CLI tool for testing
- Claude Desktop integration

**[mcp-streamablehttp-proxy](mcp-streamablehttp-proxy)**
- Wraps official stdio MCP servers
- Provides HTTP endpoints
- Session management
- Process lifecycle handling

### 🛠️ Native MCP Services

**[mcp-fetch-streamablehttp-server](mcp-fetch-streamablehttp-server)**
- Direct StreamableHTTP implementation
- Web content fetching
- SSRF protection
- HTML to markdown conversion

**[mcp-echo-streamablehttp-server-stateful](mcp-echo-streamablehttp-server-stateful)**
- Session-aware echo service
- 11 diagnostic tools
- Testing and debugging
- State persistence

**[mcp-echo-streamablehttp-server-stateless](mcp-echo-streamablehttp-server-stateless)**
- Pure functional echo
- No session state
- Production diagnostics
- Minimal overhead

## Common Patterns

### FastAPI Base
Most servers use FastAPI with Uvicorn:
```python
app = FastAPI(title="MCP Service")
uvicorn.run(app, host="0.0.0.0", port=3000)
```

### Protocol Implementation
All services implement MCP protocol:
```python
@app.post("/mcp")
async def handle_mcp(request: Request):
    # JSON-RPC message handling
    # Protocol version negotiation
    # Session management
```

### No Authentication in Services
Following the divine separation:
- OAuth handled entirely by auth service
- MCP services receive pre-authenticated requests
- Traefik enforces authentication via ForwardAuth

### Health Checks
All services implement health endpoints:
```python
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

## Installation

All packages are managed through pixi:

```bash
# Installed automatically via pixi.toml
pixi install

# Or install individually for development
cd mcp-oauth-dynamicclient
pixi run pip install -e .
```

## Development Workflow

1. **Local Development**
   ```bash
   cd <package-name>
   pixi run python -m <module_name>
   ```

2. **Testing**
   ```bash
   # Run package tests
   just pypi-test <package-name>

   # Run all package tests
   just pypi-test all
   ```

3. **Building**
   ```bash
   # Build package
   just pypi-build <package-name>

   # Build all packages
   just pypi-build all
   ```

## Integration Points

### With Traefik
- Services expose HTTP endpoints
- Traefik handles routing and auth
- ForwardAuth middleware integration

### With Docker
- Each service has Dockerfile
- Composed via docker-compose
- Health checks for orchestration

### With OAuth Gateway
- Services trust pre-authenticated requests
- Bearer tokens in Authorization header
- No OAuth logic in services

## Next Steps

- Explore individual [package documentation](mcp-oauth-dynamicclient)
- Review [service implementations](../services/index)
- Check [API reference](../api/index)
