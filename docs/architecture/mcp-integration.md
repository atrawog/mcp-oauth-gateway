# MCP Integration

This document explains how the MCP OAuth Gateway integrates with MCP (Model Context Protocol) servers to provide authentication without requiring any modifications to the MCP implementations.

## Overview

The gateway achieves transparent MCP protection through:
1. **Protocol Bridging**: HTTP to stdio conversion
2. **Session Management**: Stateful MCP connections
3. **Authentication Layer**: OAuth validation before MCP access
4. **Service Isolation**: Each MCP service runs independently

## MCP Protocol Basics

### What is MCP?

MCP (Model Context Protocol) is a protocol for communication between AI assistants and external tools. It defines:

- **Tools**: Functions that can be invoked
- **Resources**: Data that can be accessed
- **Prompts**: Templates for interactions
- **Lifecycle**: Initialization and session management

### Protocol Structure

MCP uses JSON-RPC 2.0 over various transports:
- **stdio**: Standard input/output (original)
- **HTTP**: RESTful endpoints
- **WebSocket**: Persistent connections

## Architecture

### Component Interaction

```{mermaid}
graph TB
    subgraph "Client Layer"
        C[MCP Client<br/>Claude.ai/IDE]
    end
    
    subgraph "Gateway Layer"
        T[Traefik]
        A[Auth Service]
    end
    
    subgraph "MCP Layer"
        P[mcp-streamablehttp-proxy]
        S[Official MCP Server<br/>stdio-based]
        N[Native HTTP Server]
    end
    
    C -->|HTTPS + Bearer Token| T
    T -->|ForwardAuth| A
    T -->|Authenticated Request| P
    T -->|Authenticated Request| N
    P <-->|stdio| S
```

## The Proxy Bridge

### mcp-streamablehttp-proxy

The proxy is the key component that enables OAuth protection for stdio-based MCP servers:

#### Responsibilities

1. **HTTP Endpoint**: Exposes `/mcp` for HTTP requests
2. **Process Management**: Spawns MCP server subprocesses
3. **Protocol Translation**: Converts between HTTP and stdio
4. **Session Handling**: Maintains stateful connections
5. **Health Monitoring**: Provides health check endpoints

#### Request Flow

```{mermaid}
sequenceDiagram
    participant Client
    participant Proxy
    participant MCPServer
    
    Note over Client,MCPServer: Initialization
    Client->>Proxy: POST /mcp<br/>{"method": "initialize"}
    Proxy->>Proxy: Create session
    Proxy->>MCPServer: Spawn subprocess
    Proxy->>MCPServer: Write to stdin
    MCPServer->>Proxy: Read from stdout
    Proxy->>Client: HTTP Response<br/>Mcp-Session-Id: xxx
    
    Note over Client,MCPServer: Subsequent Requests
    Client->>Proxy: POST /mcp<br/>Mcp-Session-Id: xxx
    Proxy->>Proxy: Find session
    Proxy->>MCPServer: Write to stdin
    MCPServer->>Proxy: Read from stdout
    Proxy->>Client: HTTP Response
```

### Session Management

Sessions are critical for MCP's stateful protocol:

```python
# Session structure
{
    "session_id": "unique_identifier",
    "process": subprocess_handle,
    "created_at": timestamp,
    "last_accessed": timestamp,
    "client_info": {
        "name": "client_name",
        "version": "1.0"
    }
}
```

#### Session Lifecycle

1. **Creation**: On first `initialize` request
2. **Usage**: Subsequent requests use session ID
3. **Timeout**: Sessions expire after inactivity
4. **Cleanup**: Process termination on timeout/error

## Authentication Integration

### ForwardAuth Flow

```{mermaid}
graph LR
    subgraph "1. Request Arrives"
        A[Client Request<br/>Bearer Token]
    end
    
    subgraph "2. Traefik Validates"
        B[ForwardAuth to<br/>/verify endpoint]
        C{Token Valid?}
    end
    
    subgraph "3. Route Decision"
        D[Forward to MCP]
        E[Return 401]
    end
    
    A --> B
    B --> C
    C -->|Yes| D
    C -->|No| E
```

### Headers Passed to MCP

After successful authentication, these headers are added:
- `X-User-Id`: GitHub user ID
- `X-User-Name`: GitHub username
- `X-Auth-Token`: Original bearer token

## MCP Service Types

### 1. Wrapped stdio Services

These use official MCP servers with the proxy:

```yaml
# Example: mcp-fetch
services:
  mcp-fetch:
    image: ghcr.io/atrawog/mcp-streamablehttp-proxy:latest
    environment:
      - SERVER_COMMAND=npx @modelcontextprotocol/server-fetch
```

**Characteristics**:
- Run official MCP implementations
- No modification required
- Full protocol compliance
- Process isolation per session

### 2. Native HTTP Services

These implement streamable HTTP directly:

```yaml
# Example: mcp-everything
services:
  mcp-everything:
    image: ghcr.io/modelcontextprotocol/servers/everything:latest
    environment:
      - NODE_ENV=production
```

**Characteristics**:
- Direct HTTP implementation
- No proxy needed
- Better performance
- Shared process model

## Protocol Implementation Details

### Initialization Handshake

```json
// Client Request
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {
      "name": "claude",
      "version": "1.0"
    }
  },
  "id": 1
}

// Server Response
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2025-06-18",
    "capabilities": {
      "tools": true,
      "resources": true
    },
    "serverInfo": {
      "name": "mcp-fetch",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

### Tool Invocation

```json
// List Tools
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 2
}

// Call Tool
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://example.com"
    }
  },
  "id": 3
}
```

## Health Checks

### Proxy Health Check

```bash
# Basic health
GET /health

# Protocol health
POST /mcp
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {
      "name": "healthcheck",
      "version": "1.0"
    }
  },
  "id": 1
}
```

### Docker Health Configuration

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \\
    -H 'Content-Type: application/json' \\
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",...}' \\
    | grep -q 'protocolVersion'"]
  interval: 30s
  timeout: 5s
  retries: 3
```

## Service Configuration

### Environment Variables

```bash
# Protocol version
MCP_PROTOCOL_VERSION=2025-06-18

# Service identification
SERVER_NAME=mcp-fetch

# Proxy configuration
SERVER_COMMAND="npx @modelcontextprotocol/server-fetch"
SESSION_TIMEOUT=3600
```

### Docker Compose Labels

```yaml
labels:
  # Routing
  - "traefik.http.routers.mcp-fetch.rule=Host(`mcp-fetch.${BASE_DOMAIN}`)"
  - "traefik.http.routers.mcp-fetch.priority=2"
  
  # Authentication
  - "traefik.http.routers.mcp-fetch.middlewares=mcp-auth@docker"
  
  # Service
  - "traefik.http.services.mcp-fetch.loadbalancer.server.port=3000"
```

## Error Handling

### Protocol Errors

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": "Missing required parameter: protocolVersion"
  },
  "id": 1
}
```

### HTTP Errors

- **401 Unauthorized**: Invalid/missing token
- **403 Forbidden**: Valid token but insufficient permissions
- **404 Not Found**: Invalid session ID
- **500 Internal Server Error**: MCP server crash

## Performance Considerations

### Session Pooling

- Pre-spawn processes for faster initialization
- Reuse sessions when possible
- Implement session timeout and cleanup

### Resource Limits

- Maximum sessions per service
- Memory limits per subprocess
- CPU throttling if needed

### Monitoring

Key metrics to track:
- Session creation rate
- Average session lifetime
- Request latency
- Error rates by type

## Next Steps

- [Security Architecture](security.md) - Security implementation details
- [Services Overview](../services/overview.md) - Available MCP services
- [Development Guidelines](../development/guidelines.md) - Development best practices