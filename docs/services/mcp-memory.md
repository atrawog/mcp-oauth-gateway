# mcp-memory Service

A persistent memory storage service that wraps the official `@modelcontextprotocol/server-memory` using the proxy pattern.

## Overview

The `mcp-memory` service provides persistent key-value storage capabilities through the MCP protocol. It uses `mcp-streamablehttp-proxy` to wrap the official npm-based memory server, making it accessible via HTTP with OAuth authentication. Data persists across container restarts using Docker volumes.

## Architecture

```
┌─────────────────────────────────────────┐
│         mcp-memory Container            │
├─────────────────────────────────────────┤
│   mcp-streamablehttp-proxy (Port 3000)  │
│              ↓ spawns ↓                 │
│   @modelcontextprotocol/server-memory   │
│         (stdio subprocess)              │
└─────────────────────────────────────────┘
            ↓ persists to ↓
┌─────────────────────────────────────────┐
│      mcp-memory-data Volume             │
│      (/data/memory.json)                │
└─────────────────────────────────────────┘
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_FILE` | Log file path | `/logs/server.log` |
| `MCP_CORS_ORIGINS` | Allowed CORS origins | `*` |
| `MCP_PROTOCOL_VERSION` | MCP protocol version | `2024-11-05` |
| `MEMORY_FILE_PATH` | Persistent storage file | `/data/memory.json` |

### Volume Configuration

```yaml
volumes:
  - mcp-memory-data:/data  # External volume for persistence
  - ../logs/mcp-memory:/logs  # Service logs
```

The external volume ensures data persists even when containers are recreated:

```bash
# Create the volume (done automatically by docker-compose)
docker volume create mcp-memory-data

# Inspect volume details
docker volume inspect mcp-memory-data

# Backup volume data
docker run --rm -v mcp-memory-data:/data -v $(pwd):/backup alpine tar czf /backup/memory-backup.tar.gz -C /data .
```

## Available Tools

The mcp-memory service provides persistent storage operations through the wrapped official server:

### store

Stores a value with an associated key.

**Parameters:**
- `key` (string, required): The key to store the value under
- `value` (any, required): The value to store (can be string, number, object, array, etc.)

### retrieve

Retrieves a value by its key.

**Parameters:**
- `key` (string, required): The key to retrieve the value for

### delete

Deletes a stored value by its key.

**Parameters:**
- `key` (string, required): The key to delete

### list

Lists all stored keys.

**Parameters:** None

### clear

Clears all stored data.

**Parameters:** None

## Usage Examples

### Store Data

```bash
# Store a simple string
curl -X POST https://mcp-memory.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "store",
      "arguments": {
        "key": "user:123",
        "value": "John Doe"
      }
    },
    "id": 1
  }'

# Store a complex object
curl -X POST https://mcp-memory.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "store",
      "arguments": {
        "key": "config:app",
        "value": {
          "theme": "dark",
          "language": "en",
          "notifications": true
        }
      }
    },
    "id": 2
  }'
```

### Retrieve Data

```bash
curl -X POST https://mcp-memory.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "retrieve",
      "arguments": {
        "key": "user:123"
      }
    },
    "id": 3
  }'
```

### List All Keys

```bash
curl -X POST https://mcp-memory.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "list",
      "arguments": {}
    },
    "id": 4
  }'
```

### Delete a Key

```bash
curl -X POST https://mcp-memory.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "delete",
      "arguments": {
        "key": "user:123"
      }
    },
    "id": 5
  }'
```

## Data Persistence

### Storage Format

Data is stored in JSON format at `/data/memory.json`:

```json
{
  "user:123": "John Doe",
  "config:app": {
    "theme": "dark",
    "language": "en",
    "notifications": true
  },
  "counter": 42,
  "tags": ["important", "reviewed", "production"]
}
```

### Backup and Restore

#### Backup

```bash
# Create backup
docker exec mcp-memory cat /data/memory.json > memory-backup-$(date +%Y%m%d).json

# Or using volume backup
docker run --rm -v mcp-memory-data:/data -v $(pwd):/backup alpine \
  cp /data/memory.json /backup/memory-backup-$(date +%Y%m%d).json
```

#### Restore

```bash
# Stop the service
docker compose stop mcp-memory

# Restore from backup
docker run --rm -v mcp-memory-data:/data -v $(pwd):/backup alpine \
  cp /backup/memory-backup.json /data/memory.json

# Restart the service
docker compose start mcp-memory
```

## Health Monitoring

### Health Check

The service uses StreamableHTTP protocol initialization for health checks:

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
    | grep -q '\"protocolVersion\":\"2024-11-05\"'"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

### Monitoring

```bash
# View logs
just logs mcp-memory

# Follow logs
just logs -f mcp-memory

# Check memory usage
docker exec mcp-memory ls -lah /data/memory.json

# Monitor file size over time
watch -n 60 "docker exec mcp-memory ls -lah /data/memory.json"
```

## Performance Considerations

### Storage Limits

- The service loads the entire JSON file into memory
- Large datasets may impact performance
- Consider data size when storing complex objects
- Recommended limit: < 100MB total storage

### Key Naming Conventions

Use hierarchical key names for better organization:

```
user:123:profile
user:123:settings
app:config:database
app:cache:homepage
session:abc123:data
```

## Troubleshooting

### Data Not Persisting

1. Check volume is properly mounted:
   ```bash
   docker exec mcp-memory ls -la /data/
   ```

2. Verify write permissions:
   ```bash
   docker exec mcp-memory touch /data/test.txt
   ```

3. Check volume exists:
   ```bash
   docker volume ls | grep mcp-memory-data
   ```

### Memory Corruption

1. Check JSON validity:
   ```bash
   docker exec mcp-memory cat /data/memory.json | jq .
   ```

2. Create backup and reset if corrupted:
   ```bash
   # Backup corrupted file
   docker exec mcp-memory cp /data/memory.json /data/memory.json.corrupt

   # Reset with empty object
   docker exec mcp-memory sh -c 'echo "{}" > /data/memory.json'

   # Restart service
   docker compose restart mcp-memory
   ```

### Service Won't Start

1. Check if npm package is installed:
   ```bash
   docker exec mcp-memory npm list @modelcontextprotocol/server-memory
   ```

2. Check proxy logs:
   ```bash
   just logs mcp-memory | grep ERROR
   ```

## Integration

### With Claude Desktop

Configure in Claude Desktop settings:

```json
{
  "mcpServers": {
    "memory": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--server-url", "https://mcp-memory.example.com/mcp",
        "--token", "Bearer YOUR_TOKEN_HERE"
      ]
    }
  }
}
```

### With Python Clients

```python
import httpx
import json

class MCPMemoryClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient()

    async def store(self, key, value):
        response = await self.client.post(
            f"{self.base_url}/mcp",
            headers=self.headers,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "store",
                    "arguments": {"key": key, "value": value}
                },
                "id": 1
            }
        )
        return response.json()

    async def retrieve(self, key):
        response = await self.client.post(
            f"{self.base_url}/mcp",
            headers=self.headers,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "retrieve",
                    "arguments": {"key": key}
                },
                "id": 1
            }
        )
        return response.json()

# Usage
client = MCPMemoryClient("https://mcp-memory.example.com", "your_token")
await client.store("user:123", {"name": "John", "role": "admin"})
data = await client.retrieve("user:123")
```
