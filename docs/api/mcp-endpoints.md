# MCP Endpoints

The MCP OAuth Gateway provides secure access to Model Context Protocol services through standardized HTTP endpoints.

## Overview

All MCP services expose a common `/mcp` endpoint that handles:
- Protocol initialization
- Method invocation
- Session management
- Response streaming

## Base Endpoint

```
POST https://{service}.gateway.yourdomain.com/mcp
Authorization: Bearer {access_token}
Content-Type: application/json
MCP-Protocol-Version: 2025-06-18
```

## Request Format

### JSON-RPC 2.0

All requests follow JSON-RPC 2.0 specification:

```json
{
  "jsonrpc": "2.0",
  "method": "methodName",
  "params": {
    "param1": "value1",
    "param2": "value2"
  },
  "id": "unique-request-id"
}
```

### Required Headers

```http
Authorization: Bearer {access_token}
Content-Type: application/json
MCP-Protocol-Version: 2025-06-18
Accept: application/json, text/event-stream
```

### Session Headers

```http
Mcp-Session-Id: {session_id}  # Required after initialization
```

## Protocol Flow

### 1. Initialization

First request must be initialization:

```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {
      "name": "Claude Desktop",
      "version": "1.0.0"
    }
  },
  "id": "init-1"
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2025-06-18",
    "capabilities": {
      "tools": ["fetch", "search"],
      "resources": ["file://", "https://"]
    },
    "serverInfo": {
      "name": "mcp-fetch",
      "version": "1.0.0"
    },
    "sessionId": "session-123"
  },
  "id": "init-1"
}
```

### 2. Method Invocation

After initialization:

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
  "id": "call-1"
}
```

### 3. Session Management

Include session ID in subsequent requests:

```http
POST /mcp
Mcp-Session-Id: session-123
```

## Response Formats

### Successful Response

```json
{
  "jsonrpc": "2.0",
  "result": {
    // Method-specific result
  },
  "id": "request-id"
}
```

### Error Response

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": {
      "method": "unknown_method"
    }
  },
  "id": "request-id"
}
```

### Streaming Response

For long-running operations:

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: message
data: {"jsonrpc":"2.0","method":"progress","params":{"progress":0.5}}

event: message
data: {"jsonrpc":"2.0","result":{...},"id":"request-id"}

event: close
data:
```

## Common Methods

### Core Protocol Methods

- **initialize** - Start MCP session
- **initialized** - Confirm initialization
- **shutdown** - End session cleanly
- **ping** - Keep-alive check

### Tool Methods

- **tools/list** - List available tools
- **tools/call** - Invoke a tool
- **tools/cancel** - Cancel running tool

### Resource Methods

- **resources/list** - List available resources
- **resources/read** - Read resource content

## Service-Specific Endpoints

### Fetch Service

```bash
https://mcp-fetch.gateway.yourdomain.com/mcp
```

Methods:
- `fetch` - Retrieve web content
- `fetchWithOptions` - Advanced fetch

### Filesystem Service

```bash
https://mcp-filesystem.gateway.yourdomain.com/mcp
```

Methods:
- `readFile` - Read file contents
- `writeFile` - Write file contents
- `listDirectory` - List directory contents

### Memory Service

```bash
https://mcp-memory.gateway.yourdomain.com/mcp
```

Methods:
- `store` - Store data
- `retrieve` - Retrieve data
- `delete` - Delete data

## Error Codes

Standard JSON-RPC error codes:

- **-32700** - Parse error
- **-32600** - Invalid request
- **-32601** - Method not found
- **-32602** - Invalid params
- **-32603** - Internal error

MCP-specific codes:

- **-32001** - Not initialized
- **-32002** - Session expired
- **-32004** - Resource not found
- **-32005** - Permission denied

## Examples

### Python Client

```python
import httpx
import json

# Initialize session
async with httpx.AsyncClient() as client:
    # Initialize
    response = await client.post(
        "https://mcp-fetch.gateway.com/mcp",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": "2025-06-18"
        },
        json={
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "Python Client",
                    "version": "1.0"
                }
            },
            "id": "1"
        }
    )

    init_result = response.json()
    session_id = init_result["result"]["sessionId"]

    # Call method
    response = await client.post(
        "https://mcp-fetch.gateway.com/mcp",
        headers={
            "Authorization": f"Bearer {token}",
            "Mcp-Session-Id": session_id
        },
        json={
            "jsonrpc": "2.0",
            "method": "fetch",
            "params": {
                "url": "https://example.com"
            },
            "id": "2"
        }
    )
```

### JavaScript Client

```javascript
// Using mcp-streamablehttp-client
import { Client } from 'mcp-streamablehttp-client';

const client = new Client(
  'https://mcp-fetch.gateway.com',
  { token: accessToken }
);

// Initialize
await client.initialize();

// Call method
const result = await client.request('fetch', {
  url: 'https://example.com'
});
```

### cURL Example

```bash
# Initialize
curl -X POST https://everything.gateway.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "MCP-Protocol-Version: 2025-06-18" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {},
      "clientInfo": {"name": "curl", "version": "1.0"}
    },
    "id": "1"
  }'
```

## Best Practices

1. **Always Initialize** - First request must be initialization
2. **Handle Sessions** - Store and reuse session IDs
3. **Check Capabilities** - Verify service supports required methods
4. **Handle Errors** - Implement proper error handling
5. **Use Streaming** - For long-running operations where supported

## Related Documentation

- [OAuth Endpoints](oauth-endpoints.md) - Authentication flow
- [Error Codes](error-codes.md) - Complete error reference
- [Client Registration](client-registration.md) - Client setup
