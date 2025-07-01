# MCP Integration Architecture

Detailed architecture of how Model Context Protocol (MCP) services integrate with the OAuth gateway, including protocol implementation details and transport mechanisms.

## MCP Protocol Overview

The gateway implements StreamableHTTP transport for MCP, enabling:

- Web-based access to MCP services
- OAuth authentication integration
- Session management
- Both proxy and native implementations

## Transport Architecture

```{mermaid}
graph TB
    subgraph "MCP Clients"
        CLAUDE[Claude.ai]
        DESKTOP[Claude Desktop<br/>+ mcp-streamablehttp-client]
        API[Direct API Clients]
    end

    subgraph "Transport Layer"
        HTTP[HTTPS + Bearer Token]
        SSE[Server-Sent Events]
    end

    subgraph "Gateway Services"
        PROXY[Proxy Pattern<br/>stdio → HTTP]
        NATIVE[Native Pattern<br/>Direct HTTP]
    end

    CLAUDE -->|StreamableHTTP| HTTP
    DESKTOP -->|stdio → HTTP bridge| HTTP
    API -->|Direct HTTP| HTTP

    HTTP --> PROXY
    HTTP --> NATIVE

    PROXY -->|SSE Response| SSE
    NATIVE -->|SSE Response| SSE
```

## StreamableHTTP Protocol

### Request Format

All MCP requests go to the `/mcp` endpoint:

```http
POST /mcp HTTP/1.1
Host: service.example.com
Authorization: Bearer eyJ...
Content-Type: application/json
Mcp-Session-Id: session-123 (optional)

{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {
      "tools": {},
      "resources": {},
      "prompts": {}
    },
    "clientInfo": {
      "name": "claude-ai",
      "version": "1.0"
    }
  },
  "id": 1
}
```

### Response Format (SSE)

Responses use Server-Sent Events:

```
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Mcp-Session-Id: session-123

event: message
data: {"jsonrpc":"2.0","result":{"protocolVersion":"2025-06-18","capabilities":{"tools":{"list":true,"call":true}},"serverInfo":{"name":"mcp-fetch","version":"0.1.0"}},"id":1}

event: done
data: {"status":"complete"}
```

## Protocol Implementation Patterns

### Proxy Pattern Implementation

```python
# mcp-streamablehttp-proxy architecture
class StreamableHTTPProxy:
    def __init__(self, mcp_command: str, mcp_args: List[str]):
        self.sessions = {}  # session_id -> subprocess

    async def handle_request(self, request: Request):
        # 1. Extract session ID
        session_id = request.headers.get("Mcp-Session-Id")

        # 2. Get or create subprocess
        if not session_id or session_id not in self.sessions:
            session_id = generate_session_id()
            subprocess = spawn_mcp_server(self.mcp_command, self.mcp_args)
            self.sessions[session_id] = subprocess

        # 3. Forward request to subprocess
        subprocess = self.sessions[session_id]
        subprocess.stdin.write(request.body + "\n")

        # 4. Stream response
        async def generate():
            while True:
                line = subprocess.stdout.readline()
                if not line:
                    break
                yield f"event: message\ndata: {line}\n\n"
            yield "event: done\ndata: {\"status\":\"complete\"}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
```

### Native Pattern Implementation

```python
# Direct StreamableHTTP implementation
class NativeMCPService:
    def __init__(self):
        self.tools = {}
        self.sessions = {}

    @app.post("/mcp")
    async def handle_mcp(self, request: Request):
        body = await request.json()
        method = body.get("method")

        if method == "initialize":
            return self.handle_initialize(body)
        elif method == "tools/list":
            return self.handle_tools_list(body)
        elif method == "tools/call":
            return self.handle_tool_call(body)

    async def handle_initialize(self, request):
        # Direct protocol implementation
        result = {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "tools": {"list": True, "call": True}
            },
            "serverInfo": {
                "name": "native-service",
                "version": "1.0.0"
            }
        }
        return self.create_sse_response(result, request["id"])
```

## Session Management

### Session Lifecycle

```{mermaid}
stateDiagram-v2
    [*] --> NoSession: Initial Request
    NoSession --> SessionCreated: Initialize
    SessionCreated --> Active: Successful Init
    Active --> Active: Subsequent Requests
    Active --> Terminated: Shutdown/Timeout
    Terminated --> [*]
```

### Session Storage

```python
# Session data structure
sessions = {
    "session-123": {
        "id": "session-123",
        "created_at": "2024-01-01T00:00:00Z",
        "last_activity": "2024-01-01T00:05:00Z",
        "client_info": {
            "name": "claude-ai",
            "version": "1.0"
        },
        "state": {},  # Service-specific state
        "subprocess": subprocess.Popen(...),  # For proxy pattern
    }
}
```

## MCP Methods Implementation

### Core Protocol Methods

| Method | Purpose | Required |
|--------|---------|----------|
| `initialize` | Protocol handshake | Yes |
| `initialized` | Confirm initialization | Yes |
| `tools/list` | List available tools | If tools capability |
| `tools/call` | Execute a tool | If tools capability |
| `resources/list` | List resources | If resources capability |
| `resources/read` | Read a resource | If resources capability |
| `prompts/list` | List prompts | If prompts capability |
| `prompts/get` | Get prompt details | If prompts capability |

### Tool Implementation Example

```python
# Tool registration
tools = {
    "fetch_url": {
        "name": "fetch_url",
        "description": "Fetch content from a URL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "format": "uri"},
                "headers": {"type": "object"}
            },
            "required": ["url"]
        }
    }
}

# Tool execution
async def handle_tool_call(self, request):
    tool_name = request["params"]["name"]
    arguments = request["params"]["arguments"]

    if tool_name == "fetch_url":
        result = await self.fetch_url(
            arguments["url"],
            arguments.get("headers", {})
        )

    return {
        "jsonrpc": "2.0",
        "result": {
            "content": [{"type": "text", "text": result}]
        },
        "id": request["id"]
    }
```

## Authentication Integration

### Bearer Token Flow

```{mermaid}
sequenceDiagram
    participant Client
    participant Traefik
    participant Auth
    participant MCP

    Client->>Traefik: POST /mcp + Bearer Token
    Traefik->>Auth: ForwardAuth /verify
    Auth->>Traefik: 200 OK + Headers
    Note over Traefik: X-User-Id: github|username<br/>X-User-Name: username
    Traefik->>MCP: Forward + Auth Headers
    MCP->>MCP: Process (no auth logic)
    MCP->>Traefik: SSE Response
    Traefik->>Client: SSE Response
```

### Service Implementation

MCP services receive pre-authenticated requests:

```python
# Services DO NOT implement authentication
# They receive headers from ForwardAuth
@app.post("/mcp")
async def handle_mcp(request: Request):
    # Optional: Use auth headers for logging/metrics
    user_id = request.headers.get("X-User-Id")
    user_name = request.headers.get("X-User-Name")

    # Process MCP request without auth checks
    return process_mcp_request(request)
```

## Client Integration Patterns

### Claude.ai Integration

Claude.ai directly supports StreamableHTTP:

1. Attempts connection to `/mcp`
2. Receives 401 → triggers OAuth flow
3. Obtains token via dynamic registration
4. Includes Bearer token in all requests

### Claude Desktop Integration

Uses `mcp-streamablehttp-client` as bridge:

```json
{
  "mcpServers": {
    "gateway-fetch": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--server-url", "https://mcp-fetch.example.com/mcp",
        "--token", "Bearer eyJ..."
      ]
    }
  }
}
```

### Direct API Integration

```python
import httpx
import json

# Initialize connection
async with httpx.AsyncClient() as client:
    # Send initialization
    init_response = await client.post(
        "https://service.example.com/mcp",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {}
            },
            "id": 1
        }
    )

    # Parse SSE response
    session_id = init_response.headers.get("Mcp-Session-Id")

    # Use session for subsequent requests
    tool_response = await client.post(
        "https://service.example.com/mcp",
        headers={
            "Authorization": f"Bearer {token}",
            "Mcp-Session-Id": session_id
        },
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "fetch_url",
                "arguments": {"url": "https://example.com"}
            },
            "id": 2
        }
    )
```

## Protocol Compliance

### Version Support

The gateway supports multiple MCP protocol versions:

- `2025-06-18` (latest, default)
- `2025-03-26`
- `2024-11-05`

Services negotiate version during initialization.

### Capability Negotiation

```python
# Server declares capabilities
capabilities = {
    "tools": {
        "list": True,
        "call": True
    },
    "resources": {
        "list": False,
        "read": False
    },
    "prompts": {
        "list": False,
        "get": False
    }
}

# Client must respect declared capabilities
if "tools" in server_capabilities:
    # Can use tools/list and tools/call
    pass
```

## Error Handling

### Protocol Errors

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": {
      "details": "Missing required field: method"
    }
  },
  "id": null
}
```

### Error Codes

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid Request | Invalid JSON-RPC |
| -32601 | Method not found | Unknown method |
| -32602 | Invalid params | Invalid parameters |
| -32603 | Internal error | Server error |

## Performance Considerations

### Connection Pooling

- Reuse HTTP connections where possible
- Maintain persistent sessions
- Implement connection limits

### Streaming Optimization

- Use chunked transfer encoding
- Flush SSE events immediately
- Implement backpressure handling

### Resource Management

- Session timeout (default: 1 hour)
- Maximum sessions per client
- Subprocess resource limits (proxy pattern)

## Monitoring

### Key Metrics

- Protocol version distribution
- Method call frequency
- Session duration
- Error rates by type
- Tool execution time

### Health Checks

Protocol-based health check:

```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18"},"id":1}' \
  | grep -q '"protocolVersion"'
```
