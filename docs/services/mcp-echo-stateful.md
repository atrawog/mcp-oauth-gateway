# mcp-echo-stateful Service

A stateful echo service with session management that natively implements the StreamableHTTP protocol.

## Overview

The `mcp-echo-stateful` service is a native StreamableHTTP implementation that maintains session state across requests. It provides echo functionality with persistent session data, making it ideal for testing stateful MCP interactions, session management, and debugging OAuth-protected endpoints.

## Architecture

```
┌─────────────────────────────────────────┐
│     mcp-echo-stateful Container         │
├─────────────────────────────────────────┤
│  mcp-echo-streamablehttp-server-stateful│
│        (Native Python + FastAPI)        │
│            Port 3000                    │
│                                         │
│   ┌─────────────────────────────┐      │
│   │    Session State Manager    │      │
│   │  - In-memory session store  │      │
│   │  - Session timeout: 300s    │      │
│   │  - Per-session counters     │      │
│   └─────────────────────────────┘      │
└─────────────────────────────────────────┘
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_FILE` | Log file path | `/logs/server.log` |
| `HOST` | Bind address | `0.0.0.0` |
| `PORT` | Service port | `3000` |
| `MCP_SERVER_NAME` | Server identification | `mcp-echo-streamablehttp-stateful` |
| `MCP_SERVER_VERSION` | Server version | `0.1.0` |
| `MCP_PROTOCOL_VERSION` | MCP protocol version | `2025-06-18` |
| `MCP_SESSION_TIMEOUT` | Session timeout in seconds | `300` |
| `DEBUG` | Enable debug mode | `true` |

### Multi-Subdomain Support

The service supports multiple subdomains for testing different instances:
- `echo-stateful0.example.com` through `echo-stateful9.example.com`
- Each subdomain maintains independent session state
- Useful for testing load balancing and session affinity

## Available Tools

### echo

Echo back the input with session tracking.

**Parameters:**
- `message` (string, required): Message to echo
- `delay` (number, optional): Delay in seconds before responding
- `format` (string, optional): Response format ("plain", "json", "markdown")

**Session State Tracking:**
- Request count per session
- First request timestamp
- Last request timestamp
- Custom session data storage

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "echo",
    "arguments": {
      "message": "Hello, stateful world!",
      "format": "json"
    }
  },
  "id": 1
}
```

### set_session_data

Store custom data in the session.

**Parameters:**
- `key` (string, required): Data key
- `value` (any, required): Data value to store

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "set_session_data",
    "arguments": {
      "key": "user_preference",
      "value": {"theme": "dark", "language": "en"}
    }
  },
  "id": 2
}
```

### get_session_data

Retrieve custom data from the session.

**Parameters:**
- `key` (string, optional): Specific key to retrieve (omit for all data)

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_session_data",
    "arguments": {
      "key": "user_preference"
    }
  },
  "id": 3
}
```

### get_session_info

Get information about the current session.

**Parameters:** None

**Returns:**
- Session ID
- Request count
- Session age
- Time until expiry
- Custom data keys

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_session_info",
    "arguments": {}
  },
  "id": 4
}
```

## Session Management

### Session Lifecycle

1. **Session Creation**:
   - Created on first request
   - Unique session ID generated
   - Returned in `Mcp-Session-Id` header

2. **Session Persistence**:
   - State maintained in memory
   - Survives between requests
   - Timeout after 300 seconds of inactivity

3. **Session Expiry**:
   - Automatic cleanup after timeout
   - Manual termination available
   - Graceful handling of expired sessions

### Working with Sessions

```python
import httpx

class StatefulEchoClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.session_id = None

    async def initialize(self):
        """Initialize session and get session ID"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "echo-client",
                            "version": "1.0"
                        }
                    },
                    "id": 1
                }
            )

            # Save session ID
            self.session_id = response.headers.get("Mcp-Session-Id")
            return response.json()

    async def echo_with_state(self, message):
        """Echo message using existing session"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "echo",
                        "arguments": {"message": message}
                    },
                    "id": 2
                }
            )

            return response.json()
```

## Usage Examples

### Testing Session Persistence

```bash
# First request - creates session
SESSION_ID=$(curl -s -X POST https://echo-stateful.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {"message": "First message"}
    },
    "id": 1
  }' -D - | grep -i "mcp-session-id" | cut -d' ' -f2)

# Subsequent request - uses existing session
curl -X POST https://echo-stateful.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Mcp-Session-Id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_session_info",
      "arguments": {}
    },
    "id": 2
  }'
```

### Storing and Retrieving Session Data

```python
async def test_session_storage():
    client = StatefulEchoClient("https://echo-stateful.example.com", token)
    await client.initialize()

    # Store user preferences
    await client.call_tool("set_session_data", {
        "key": "preferences",
        "value": {
            "notifications": True,
            "email_frequency": "daily",
            "timezone": "UTC"
        }
    })

    # Store user progress
    await client.call_tool("set_session_data", {
        "key": "progress",
        "value": {
            "current_step": 5,
            "completed_steps": [1, 2, 3, 4],
            "total_steps": 10
        }
    })

    # Retrieve all session data
    all_data = await client.call_tool("get_session_data", {})
    print(f"All session data: {all_data}")

    # Retrieve specific data
    prefs = await client.call_tool("get_session_data", {
        "key": "preferences"
    })
    print(f"User preferences: {prefs}")
```

### Multi-Instance Testing

```bash
# Test different instances maintain separate state
for i in {0..2}; do
  echo "Testing echo-stateful$i..."

  curl -X POST "https://echo-stateful$i.example.com/mcp" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"jsonrpc\": \"2.0\",
      \"method\": \"tools/call\",
      \"params\": {
        \"name\": \"echo\",
        \"arguments\": {
          \"message\": \"Instance $i test\"
        }
      },
      \"id\": 1
    }"
done
```

## Testing OAuth and Session Features

### OAuth Flow Testing

```python
class OAuthSessionTester:
    def __init__(self, gateway_url, client_id, client_secret):
        self.gateway_url = gateway_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.session_id = None

    async def test_full_flow(self):
        # 1. Get OAuth token
        self.access_token = await self.get_oauth_token()

        # 2. Initialize MCP session
        session_info = await self.initialize_mcp_session()

        # 3. Test stateful operations
        for i in range(5):
            result = await self.echo_message(f"Message {i}")
            print(f"Echo {i}: {result}")

        # 4. Verify session state
        info = await self.get_session_details()
        assert info["request_count"] == 5

        # 5. Test session timeout
        await asyncio.sleep(301)  # Wait for timeout

        try:
            await self.echo_message("After timeout")
        except Exception as e:
            print(f"Expected timeout error: {e}")
```

### Load Testing with Sessions

```python
async def load_test_sessions(num_sessions=100, requests_per_session=10):
    """Test multiple concurrent sessions"""
    sessions = []

    # Create sessions
    for i in range(num_sessions):
        client = StatefulEchoClient(
            f"https://echo-stateful{i % 10}.example.com",
            token
        )
        await client.initialize()
        sessions.append(client)

    # Send requests from all sessions
    tasks = []
    for session_num, client in enumerate(sessions):
        for req_num in range(requests_per_session):
            task = client.echo_with_state(
                f"Session {session_num}, Request {req_num}"
            )
            tasks.append(task)

    # Execute all requests concurrently
    results = await asyncio.gather(*tasks)

    # Verify session isolation
    for client in sessions:
        info = await client.get_session_info()
        assert info["request_count"] == requests_per_session
```

## Health Monitoring

### Health Check

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-06-18\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
    | grep -q '\"protocolVersion\":\"2025-06-18\"'"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

### Session Monitoring

```bash
# Monitor active sessions
curl https://echo-stateful.example.com/debug/sessions \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Check memory usage
docker stats mcp-echo-stateful

# View debug logs
just logs mcp-echo-stateful | grep -E "(session|state)"
```

## Performance Considerations

### Memory Management

- Each session stores state in memory
- Session timeout prevents memory leaks
- Monitor memory usage with many sessions

### Scaling Strategies

1. **Horizontal Scaling**: Use multiple instances (echo-stateful0-9)
2. **Session Affinity**: Route clients to same instance
3. **External State Store**: For production, consider Redis

## Troubleshooting

### Session Not Persisting

1. Check session ID is included:
   ```bash
   curl -v ... 2>&1 | grep -i "mcp-session-id"
   ```

2. Verify timeout hasn't expired:
   ```bash
   # Check session age
   curl -X POST ... -d '{"method": "tools/call", "params": {"name": "get_session_info"}}'
   ```

### Debug Mode

Enable detailed logging:
```yaml
environment:
  - DEBUG=true
  - LOG_LEVEL=DEBUG
```

## Integration

### With Claude Desktop

```json
{
  "mcpServers": {
    "echo-stateful": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--server-url", "https://echo-stateful.example.com/mcp",
        "--token", "Bearer YOUR_TOKEN_HERE"
      ]
    }
  }
}
```

### Testing Framework Integration

```python
import pytest

@pytest.fixture
async def echo_client():
    client = StatefulEchoClient(
        "https://echo-stateful.example.com",
        os.getenv("TEST_TOKEN")
    )
    await client.initialize()
    yield client
    # Cleanup if needed

@pytest.mark.asyncio
async def test_session_persistence(echo_client):
    # Set data
    await echo_client.set_session_data("test_key", "test_value")

    # Retrieve data
    data = await echo_client.get_session_data("test_key")
    assert data == "test_value"

    # Check session info
    info = await echo_client.get_session_info()
    assert "test_key" in info["data_keys"]
```
