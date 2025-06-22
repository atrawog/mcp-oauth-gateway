# MCP Protocol Implementation

This document details the Model Context Protocol (MCP) implementation in the gateway, including protocol specifications, transport mechanisms, and service integration patterns.

## Protocol Overview

The MCP OAuth Gateway implements the **MCP 2025-06-18** specification, providing:
- **JSON-RPC 2.0** message format
- **Streamable HTTP** transport
- **Session management** for stateful connections
- **Tool invocation** framework

## Protocol Architecture

```{mermaid}
graph TB
    subgraph "MCP Client"
        C[Client Application]
        SDK[MCP SDK]
    end
    
    subgraph "Transport Layer"
        HTTP[HTTP/HTTPS]
        WS[WebSocket]
    end
    
    subgraph "Gateway"
        P[mcp-streamablehttp-proxy]
        S[Session Manager]
    end
    
    subgraph "MCP Servers"
        STDIO[stdio MCP Server]
        NATIVE[Native HTTP Server]
    end
    
    C --> SDK
    SDK --> HTTP
    SDK --> WS
    HTTP --> P
    WS --> P
    P --> S
    P --> STDIO
    P --> NATIVE
```

## Message Format

### JSON-RPC 2.0 Structure

All MCP messages follow JSON-RPC 2.0:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://example.com"
    }
  },
  "id": "unique-request-id"
}
```

### Response Format

Success response:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": "Fetched content...",
    "status": 200
  },
  "id": "unique-request-id"
}
```

Error response:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "details": "URL is required"
    }
  },
  "id": "unique-request-id"
}
```

## Protocol Lifecycle

### 1. Initialization Phase

```{mermaid}
sequenceDiagram
    Client->>Server: initialize request
    Server->>Client: initialize response (capabilities)
    Client->>Server: initialized notification
    Note over Client,Server: Session established
```

Initialize request:
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {
      "tools": true,
      "prompts": true,
      "resources": true,
      "logging": true
    }
  },
  "id": 1
}
```

Initialize response:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2025-06-18",
    "capabilities": {
      "tools": {
        "listSupported": true
      }
    },
    "serverInfo": {
      "name": "mcp-fetch",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

### 2. Operation Phase

During operation, clients can:
- List available tools
- Call tools with arguments
- Subscribe to notifications
- Manage resources

### 3. Shutdown Phase

Clean shutdown sequence:
```json
{
  "jsonrpc": "2.0",
  "method": "shutdown",
  "id": "final-request"
}
```

## Transport Implementation

### Streamable HTTP Transport

The gateway uses streamable HTTP for MCP communication:

```http
POST /mcp HTTP/1.1
Host: mcp-fetch.example.com
Authorization: Bearer <token>
Content-Type: application/json
MCP-Protocol-Version: 2025-06-18
Mcp-Session-Id: session-123

{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {...},
  "id": 1
}
```

### Session Management

Sessions maintain state across requests:

```python
# Session structure
{
    "session_id": "session-123",
    "client_id": "client-abc",
    "created_at": "2024-01-01T00:00:00Z",
    "last_accessed": "2024-01-01T00:01:00Z",
    "state": {
        "initialized": true,
        "capabilities": {...}
    }
}
```

## Tool Framework

### Tool Definition

Tools are defined with structured metadata:

```json
{
  "name": "fetch",
  "description": "Fetch content from a URL",
  "inputSchema": {
    "type": "object",
    "properties": {
      "url": {
        "type": "string",
        "format": "uri",
        "description": "The URL to fetch"
      },
      "method": {
        "type": "string",
        "enum": ["GET", "POST", "PUT", "DELETE"],
        "default": "GET"
      }
    },
    "required": ["url"]
  }
}
```

### Tool Invocation

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://api.example.com/data",
      "method": "GET"
    }
  },
  "id": "request-123"
}
```

## Service Integration

### Proxy Architecture

The `mcp-streamablehttp-proxy` bridges stdio MCP servers to HTTP:

```python
# Proxy flow
1. Receive HTTP request
2. Parse JSON-RPC message
3. Forward to stdio subprocess
4. Read stdio response
5. Return HTTP response
```

### Native HTTP Servers

Some services implement HTTP directly:

```python
# Direct HTTP implementation
@app.post("/mcp")
async def handle_mcp(request: MCPRequest):
    if request.method == "initialize":
        return handle_initialize(request)
    elif request.method == "tools/call":
        return handle_tool_call(request)
    # ... other methods
```

## Protocol Features

### 1. Tool Discovery

List available tools:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "fetch",
        "description": "Fetch content from a URL",
        "inputSchema": {...}
      },
      {
        "name": "parse_html",
        "description": "Parse HTML content",
        "inputSchema": {...}
      }
    ]
  },
  "id": 1
}
```

### 2. Batch Requests

Multiple operations in one request:
```json
[
  {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {...},
    "id": 1
  },
  {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {...},
    "id": 2
  }
]
```

### 3. Notifications

One-way messages without response:
```json
{
  "jsonrpc": "2.0",
  "method": "log",
  "params": {
    "level": "info",
    "message": "Processing started"
  }
}
```

## Error Handling

### Standard Error Codes

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid request | Not valid JSON-RPC |
| -32601 | Method not found | Unknown method |
| -32602 | Invalid params | Invalid parameters |
| -32603 | Internal error | Server error |

### Custom Error Codes

| Code | Message | Description |
|------|---------|-------------|
| -32000 | Session not found | Invalid session ID |
| -32001 | Not initialized | Called before init |
| -32002 | Tool not found | Unknown tool name |

## Security Considerations

### Authentication
- Bearer token required for all requests
- Tokens validated via ForwardAuth
- Session tied to authenticated user

### Input Validation
- Schema validation for all inputs
- SQL injection prevention
- Path traversal protection

### Rate Limiting
- Per-client request limits
- Concurrent session limits
- Resource usage quotas

## Testing Protocol Compliance

### Protocol Test Suite

```bash
# Run protocol compliance tests
just test-mcp-protocol

# Test specific protocol features
just test-file tests/test_mcp_protocol_compliance.py
just test-file tests/test_mcp_session_management.py
```

### Manual Protocol Testing

```bash
# Initialize session
mcp-streamablehttp-client query https://mcp-fetch.example.com/mcp \
  --token TOKEN \
  '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2025-06-18"}, "id": 1}'

# List tools
mcp-streamablehttp-client query https://mcp-fetch.example.com/mcp \
  --token TOKEN \
  '{"jsonrpc": "2.0", "method": "tools/list", "id": 2}'
```

## Implementation Examples

### Implementing a New Tool

```python
@tool
def my_custom_tool(arg1: str, arg2: int = 10) -> dict:
    """
    Description of what the tool does.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2 (optional)
    
    Returns:
        dict: Result of the operation
    """
    # Tool implementation
    return {"result": f"Processed {arg1} with {arg2}"}
```

### Handling Protocol Messages

```python
async def handle_message(message: dict) -> dict:
    if message.get("method") == "initialize":
        return {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": "2025-06-18",
                "capabilities": get_capabilities()
            },
            "id": message.get("id")
        }
    elif message.get("method") == "tools/call":
        return await handle_tool_call(message)
    # ... other methods
```

## Performance Optimization

### Connection Pooling
- Reuse HTTP connections
- Persistent sessions
- Efficient subprocess management

### Caching
- Tool metadata caching
- Session state caching
- Response caching for idempotent operations

### Resource Management
- Subprocess lifecycle management
- Memory usage monitoring
- Timeout enforcement

## Troubleshooting

### Common Issues

1. **Protocol Version Mismatch**
   ```
   Error: Unsupported protocol version
   Solution: Use MCP-Protocol-Version: 2025-06-18 header
   ```

2. **Session Expired**
   ```
   Error: Session not found
   Solution: Re-initialize with new session
   ```

3. **Tool Not Available**
   ```
   Error: Unknown tool
   Solution: Check tools/list for available tools
   ```

### Debug Tools

```bash
# Protocol version check
curl -H "Authorization: Bearer TOKEN" \
     https://mcp-service.example.com/mcp \
     -d '{"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1}'

# Session debugging
just logs mcp-fetch | grep session

# Message tracing
MCP_DEBUG=1 mcp-streamablehttp-client query ...
```

## Related Documentation

- [MCP Specification](https://modelcontextprotocol.org) - Official protocol docs
- {doc}`../services/index` - Available MCP services
- {doc}`../packages/mcp-streamablehttp-proxy` - Proxy implementation