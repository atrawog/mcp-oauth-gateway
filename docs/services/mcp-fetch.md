# mcp-fetch Service

A web content fetching service that wraps the official `mcp-server-fetch` using the proxy pattern.

## Overview

The `mcp-fetch` service provides secure web content fetching capabilities through the MCP protocol. It uses `mcp-streamablehttp-proxy` to wrap the official stdio-based fetch server, making it accessible via HTTP with OAuth authentication.

## Architecture

```
┌─────────────────────────────────────────┐
│          mcp-fetch Container            │
├─────────────────────────────────────────┤
│   mcp-streamablehttp-proxy (Port 3000)  │
│              ↓ spawns ↓                 │
│         mcp-server-fetch                │
│         (stdio subprocess)              │
└─────────────────────────────────────────┘
```

## Configuration

### Docker Compose

```yaml
services:
  mcp-fetch:
    <<: *mcp-service
    build:
      context: ./mcp-fetch
      dockerfile: Dockerfile
    environment:
      - MCP_ALLOWED_DOMAINS=${MCP_FETCH_ALLOWED_DOMAINS:-}
      - MCP_BLOCKED_DOMAINS=${MCP_FETCH_BLOCKED_DOMAINS:-}
      - MCP_LOG_LEVEL=${MCP_LOG_LEVEL:-info}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 40s
    volumes:
      - ./logs/mcp-fetch:/logs
    labels:
      - "traefik.enable=${ENABLE_MCP_FETCH:-true}"
      - "traefik.http.routers.mcp-fetch.rule=Host(`mcp-fetch.${BASE_DOMAIN}`) || Host(`fetch.${BASE_DOMAIN}`)"
      - "traefik.http.routers.mcp-fetch.priority=2"
      - "traefik.http.routers.mcp-fetch.tls=true"
      - "traefik.http.routers.mcp-fetch.tls.certresolver=letsencrypt"
      - "traefik.http.routers.mcp-fetch.middlewares=mcp-auth@file"
      - "traefik.http.services.mcp-fetch.loadbalancer.server.port=3000"
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install both proxy and official server
RUN pip install mcp-streamablehttp-proxy mcp-server-fetch

# Configure proxy to wrap fetch server
ENV MCP_COMMAND="mcp-server-fetch"

# Run the proxy
CMD ["mcp-streamablehttp-proxy", "--port", "3000", "--host", "0.0.0.0"]

EXPOSE 3000
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_MCP_FETCH` | Enable/disable service | `true` |
| `MCP_FETCH_ALLOWED_DOMAINS` | Comma-separated allowed domains | All allowed |
| `MCP_FETCH_BLOCKED_DOMAINS` | Comma-separated blocked domains | None blocked |
| `MCP_LOG_LEVEL` | Logging level | `info` |

## Available Tools

The mcp-fetch service provides these tools through the wrapped server:

### fetch

Fetches content from a URL and returns it.

**Parameters:**
- `url` (string, required): The URL to fetch
- `max_length` (integer, optional): Maximum content length
- `start_index` (integer, optional): Start reading from this index
- `end_index` (integer, optional): Stop reading at this index

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://example.com",
      "max_length": 5000
    }
  },
  "id": 1
}
```

### fetchRaw

Fetches raw content without processing.

**Parameters:**
- `url` (string, required): The URL to fetch

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetchRaw",
    "arguments": {
      "url": "https://api.example.com/data.json"
    }
  },
  "id": 2
}
```

## Security Features

### Domain Filtering

Control which domains can be fetched:

```bash
# Allow specific domains only
MCP_FETCH_ALLOWED_DOMAINS=example.com,api.example.com

# Block specific domains
MCP_FETCH_BLOCKED_DOMAINS=internal.local,private.net
```

### Request Limits

The official mcp-server-fetch implements:
- Maximum content size limits
- Timeout protection
- Redirect following (configurable)

## Usage Examples

### Basic Fetch

```bash
curl -X POST https://mcp-fetch.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "fetch",
      "arguments": {
        "url": "https://example.com"
      }
    },
    "id": 1
  }'
```

### Fetch with Range

```bash
# Fetch only first 1000 characters
curl -X POST https://mcp-fetch.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "fetch",
      "arguments": {
        "url": "https://example.com/large-file.txt",
        "start_index": 0,
        "end_index": 1000
      }
    },
    "id": 1
  }'
```

## Session Management

The proxy maintains sessions for each client:

1. First request creates a session
2. Session ID returned in response headers
3. Include session ID in subsequent requests
4. Sessions timeout after inactivity

```bash
# First request
curl -X POST https://mcp-fetch.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  ...

# Response includes session ID
Mcp-Session-Id: abc-123-def

# Subsequent requests
curl -X POST https://mcp-fetch.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Mcp-Session-Id: abc-123-def" \
  ...
```

## Health Monitoring

### Health Endpoint

```bash
curl https://mcp-fetch.example.com/health

{
  "status": "healthy",
  "subprocess": "running",
  "sessions": 3,
  "uptime": 3600
}
```

### Logs

```bash
# View logs
just logs mcp-fetch

# Follow logs
just logs -f mcp-fetch

# Check file logs
cat logs/mcp-fetch/proxy.log
```

## Troubleshooting

### Service Won't Start

1. Check if mcp-server-fetch is installed:
   ```bash
   docker exec mcp-fetch pip list | grep mcp-server-fetch
   ```

2. Check proxy logs:
   ```bash
   just logs mcp-fetch | grep ERROR
   ```

### Fetch Failures

1. Verify domain is allowed:
   ```bash
   echo $MCP_FETCH_ALLOWED_DOMAINS
   ```

2. Check network connectivity:
   ```bash
   docker exec mcp-fetch curl https://example.com
   ```

3. Test without proxy:
   ```bash
   docker exec mcp-fetch mcp-server-fetch --help
   ```

### Session Issues

1. Check session count:
   ```bash
   curl http://localhost:3000/health | jq .sessions
   ```

2. Clear stuck sessions:
   ```bash
   docker restart mcp-fetch
   ```

## Performance Tuning

### Scaling

For high load, scale horizontally:

```bash
# Scale to 3 instances
docker compose up -d --scale mcp-fetch=3
```

### Resource Limits

Set appropriate limits in docker-compose:

```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

## Integration

### With Claude Desktop

Configure in Claude Desktop settings:

```json
{
  "mcpServers": {
    "fetch": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--server-url", "https://mcp-fetch.example.com/mcp",
        "--token", "Bearer YOUR_TOKEN_HERE"
      ]
    }
  }
}
```

### With Python Clients

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://mcp-fetch.example.com/mcp",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "fetch",
                "arguments": {"url": "https://example.com"}
            },
            "id": 1
        }
    )
```
