# MCP Services Overview

The MCP OAuth Gateway provides authenticated access to multiple MCP (Model Context Protocol) services. Each service offers specific capabilities while maintaining complete isolation from authentication concerns.

## Available Services

| Service | Description | Protocol Version | Status |
|---------|-------------|------------------|---------|
| [mcp-fetch](#mcp-fetch) | Web content fetching | 2025-03-26 | Stable |
| [mcp-fetchs](#mcp-fetchs) | Native fetch implementation | 2025-06-18 | Stable |
| [mcp-filesystem](#mcp-filesystem) | File system operations | 2025-03-26 | Stable |
| [mcp-memory](#mcp-memory) | Knowledge graph database | 2024-11-05 | Stable |
| [mcp-time](#mcp-time) | Time and timezone operations | 2025-03-26 | Stable |
| [mcp-sequentialthinking](#mcp-sequentialthinking) | Structured reasoning | 2024-11-05 | Stable |
| [mcp-tmux](#mcp-tmux) | Terminal multiplexer | 2025-06-18 | Experimental |
| [mcp-playwright](#mcp-playwright) | Browser automation | 2025-06-18 | Experimental |
| [mcp-everything](#mcp-everything) | Test/demo server | 2025-06-18 | Testing |

## Service Architecture

All MCP services follow the same architectural pattern:

```{mermaid}
graph LR
    A[Client Request] --> B[Traefik]
    B --> C[Auth Validation]
    C --> D{Service Type}
    D -->|Wrapped| E[Proxy → stdio Server]
    D -->|Native| F[HTTP Server]
```

## Service Categories

### Core Services

These provide fundamental capabilities commonly needed by AI assistants:

#### mcp-fetch
- **Purpose**: Fetch content from web URLs
- **Implementation**: Wraps official `@modelcontextprotocol/server-fetch`
- **Key Features**:
  - HTTP/HTTPS support
  - Content extraction
  - Error handling
- **Use Cases**: API calls, web scraping, data retrieval

#### mcp-filesystem
- **Purpose**: Read and write files in a sandboxed workspace
- **Implementation**: Wraps official filesystem server
- **Key Features**:
  - Read/write files
  - List directories
  - Create/delete files
  - Workspace isolation
- **Use Cases**: Code generation, file manipulation, data processing

#### mcp-memory
- **Purpose**: Persistent knowledge graph storage
- **Implementation**: Entity-relation database
- **Key Features**:
  - Create entities and relations
  - Query knowledge graph
  - Persistent storage
  - Graph traversal
- **Use Cases**: Long-term memory, fact storage, relationship tracking

### Utility Services

These provide specialized functionality:

#### mcp-time
- **Purpose**: Time and timezone operations
- **Implementation**: Timezone-aware time service
- **Key Features**:
  - Current time in any timezone
  - Time conversions
  - DST handling
  - Timezone information
- **Use Cases**: Scheduling, time calculations, timezone conversion

#### mcp-sequentialthinking
- **Purpose**: Structured problem-solving
- **Implementation**: Step-by-step reasoning engine
- **Key Features**:
  - Break complex problems into steps
  - Revision and branching
  - State management
  - Progress tracking
- **Use Cases**: Complex reasoning, problem decomposition, planning

### Experimental Services

These are newer or more specialized services:

#### mcp-playwright
- **Purpose**: Browser automation and testing
- **Implementation**: Playwright-based browser control
- **Key Features**:
  - Browser automation
  - Screenshot capture
  - Web testing
  - JavaScript execution
- **Use Cases**: Web testing, UI automation, screenshot generation

#### mcp-tmux
- **Purpose**: Terminal session management
- **Implementation**: tmux integration
- **Key Features**:
  - Session creation
  - Window management
  - Command execution
  - Session persistence
- **Use Cases**: Terminal automation, long-running processes

#### mcp-everything
- **Purpose**: Testing and demonstration
- **Implementation**: Native HTTP server
- **Key Features**:
  - Echo service
  - Math operations
  - Environment info
  - Test tools
- **Use Cases**: Testing, development, protocol validation

## Common Patterns

### Service URLs

All services follow the pattern:
```
https://{service-name}.{base-domain}/mcp
```

Examples:
- `https://mcp-fetch.example.com/mcp`
- `https://mcp-memory.example.com/mcp`

### Authentication

All services require Bearer token authentication:
```http
Authorization: Bearer {jwt-token}
```

### Protocol Initialization

Every service requires initialization:
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "{version}",
    "capabilities": {},
    "clientInfo": {
      "name": "client-name",
      "version": "1.0"
    }
  },
  "id": 1
}
```

### Error Handling

Services return standard JSON-RPC errors:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": "Unknown method: invalid/method"
  },
  "id": 1
}
```

## Service Configuration

### Enabling/Disabling Services

Services can be enabled or disabled via environment variables:
```bash
# Enable core services
MCP_FETCH_ENABLED=true
MCP_FILESYSTEM_ENABLED=true
MCP_MEMORY_ENABLED=true

# Disable resource-intensive services
MCP_PLAYWRIGHT_ENABLED=false
MCP_TMUX_ENABLED=false
```

### Resource Limits

Each service can have resource constraints:
```yaml
deploy:
  resources:
    limits:
      cpus: '0.50'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

### Health Monitoring

All services implement health checks:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

## Best Practices

### 1. Service Selection
- Enable only needed services
- Consider resource constraints
- Monitor service health

### 2. Protocol Versions
- Use compatible versions
- Check service documentation
- Handle version negotiation

### 3. Error Handling
- Implement retry logic
- Handle timeout gracefully
- Log errors for debugging

### 4. Performance
- Reuse sessions when possible
- Batch operations
- Monitor latency

## Testing Services

### Manual Testing
```bash
# Get access token
export TOKEN=$(just mcp-client-token)

# Test service
curl -X POST https://mcp-fetch.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize",...}'
```

### Integration Testing
```bash
# Run service-specific tests
just test tests/test_mcp_fetch_integration.py -v
just test tests/test_mcp_memory_integration.py -v
```

## Infrastructure Services

In addition to MCP services, the gateway includes critical infrastructure:

### [Auth Service](auth.md)
- OAuth 2.1 authorization server
- GitHub OAuth integration
- JWT token management
- ForwardAuth provider

### [Redis Service](redis.md)
- State persistence
- Token storage
- Session management
- Key-value storage

### [Traefik Service](traefik.md)
- Reverse proxy
- SSL/TLS termination
- Authentication enforcement
- Service routing

## Next Steps

### MCP Services
- [Fetch Service](fetch.md) - Web content fetching details
- [Fetchs Service](fetchs.md) - Native fetch implementation
- [Filesystem Service](filesystem.md) - File operations guide
- [Memory Service](memory.md) - Knowledge graph usage
- [Time Service](time.md) - Timezone operations
- [Sequential Thinking Service](sequentialthinking.md) - Structured reasoning
- [Playwright Service](playwright.md) - Browser automation
- [Tmux Service](tmux.md) - Terminal management
- [Everything Service](everything.md) - Test utilities

### Infrastructure
- [Auth Service](auth.md) - OAuth implementation
- [Redis Service](redis.md) - State storage
- [Traefik Service](traefik.md) - Routing and SSL

### Development
- [Adding Services](../development/adding-services.md) - Add new MCP services
