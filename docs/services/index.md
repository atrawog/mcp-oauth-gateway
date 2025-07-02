# Service Implementations

The MCP OAuth Gateway consists of infrastructure services and MCP services, all orchestrated through Docker Compose following the divine architectural separation.

## Service Architecture

```{mermaid}
graph TB
    subgraph "Infrastructure Layer"
        TRAEFIK[Traefik<br/>Reverse Proxy]
        AUTH[Auth Service<br/>OAuth 2.1]
        REDIS[Redis<br/>Storage]
    end

    subgraph "MCP Services - Proxy Pattern"
        FETCH[mcp-fetch]
        FS[mcp-filesystem]
        MEM[mcp-memory]
        TIME[mcp-time]
        EVERYTHING[mcp-everything]
        PLAYWRIGHT[mcp-playwright]
        SEQ[mcp-sequentialthinking]
        TMUX[mcp-tmux]
    end

    subgraph "MCP Services - Native Pattern"
        FETCHS[mcp-fetchs]
        ECHO1[mcp-echo-stateful]
        ECHO2[mcp-echo-stateless]
    end

    TRAEFIK --> |routes| AUTH
    TRAEFIK --> |authenticated| FETCH
    TRAEFIK --> |authenticated| FETCHS
    AUTH --> |storage| REDIS
```

## Service Categories

### 🏗️ Infrastructure Services

Core services that provide authentication, routing, and storage:

| Service | Purpose | Technology |
|---------|---------|------------|
| **[Traefik](traefik)** | Reverse proxy, SSL, routing | Traefik v3.0 |
| **[Auth](auth)** | OAuth 2.1 server | mcp-oauth-dynamicclient |
| **[Redis](redis)** | Token and session storage | Redis 7.0 |

### 🔧 MCP Services - Proxy Pattern

Services that wrap official MCP stdio servers using `mcp-streamablehttp-proxy`:

| Service | Purpose | Wrapped Server |
|---------|---------|----------------|
| **[mcp-fetch](mcp-fetch)** | Web content fetching | mcp-server-fetch |
| **[mcp-filesystem](mcp-filesystem)** | File operations | mcp-server-filesystem |
| **[mcp-memory](mcp-memory)** | Persistent storage | @modelcontextprotocol/server-memory |
| **[mcp-time](mcp-time)** | Time/date operations | mcp-server-time |
| **[mcp-everything](mcp-everything)** | Comprehensive toolset | mcp-server-everything |
| **[mcp-playwright](mcp-playwright)** | Browser automation | @modelcontextprotocol/server-playwright |
| **[mcp-sequentialthinking](mcp-sequentialthinking)** | Sequential reasoning | @modelcontextprotocol/server-sequential-thinking |
| **[mcp-tmux](mcp-tmux)** | Terminal multiplexer | mcp-server-tmux |

### 🚀 MCP Services - Native Pattern

Services with direct StreamableHTTP implementation:

| Service | Purpose | Implementation |
|---------|---------|----------------|
| **[mcp-fetchs](mcp-fetchs)** | Native fetch with SSRF protection | mcp-fetch-streamablehttp-server |
| **[mcp-echo-stateful](mcp-echo-stateful)** | Stateful diagnostic echo | mcp-echo-streamablehttp-server-stateful |
| **[mcp-echo-stateless](mcp-echo-stateless)** | Stateless production echo | mcp-echo-streamablehttp-server-stateless |

## Common Service Patterns

### Docker Compose Structure

Each service follows the blessed pattern:

```yaml
services:
  service-name:
    <<: *mcp-service  # Inherit common config
    build:
      context: ./service-name
      dockerfile: Dockerfile
    environment:
      - SERVICE_CONFIG=${SERVICE_CONFIG}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    labels:
      # Traefik routing labels
      - "traefik.enable=true"
      - "traefik.http.routers.service.rule=Host(`service.${BASE_DOMAIN}`)"
      - "traefik.http.routers.service.priority=2"
      - "traefik.http.routers.service.middlewares=mcp-auth@docker"
```

### Health Check Patterns

#### For Proxy Services
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
```

#### For Native MCP Services
```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",...}' \
    | grep -q '\"protocolVersion\"'"]
```

### Authentication Pattern

All MCP services:
1. Receive requests through Traefik
2. Traefik validates token via ForwardAuth
3. Service receives pre-authenticated request
4. No OAuth code in MCP services

## Service Configuration

### Enable/Disable Services

In `.env`:
```bash
# MCP Services
MCP_FETCH_ENABLED=true
MCP_FILESYSTEM_ENABLED=false
MCP_MEMORY_ENABLED=true
# ... etc
```

### Service URLs

Services are accessible at:
- `https://service-name.${BASE_DOMAIN}/mcp`

With multiple URLs supported:
```bash
MCP_FETCH_URLS=https://fetch.example.com/mcp,https://mcp-fetch.example.com/mcp
```

## Deployment Patterns

### Development
```bash
# Start specific services
just up auth mcp-fetch mcp-echo-stateful

# Watch logs
just logs -f mcp-fetch
```

### Production
```bash
# Start all enabled services
just up

# Check health
just check-health
```

### Scaling
```bash
# Scale stateless services
docker compose up -d --scale mcp-echo-stateless=3
```

## Monitoring

### Service Status
```bash
# Check all services
just status

# Check specific service
docker compose ps mcp-fetch
```

### Logs
```bash
# Container logs
just logs mcp-fetch

# File-based logs
just logs-files mcp-fetch
```

### Health Endpoints
- Infrastructure: `/health`
- MCP Services: `/health` or protocol check

## Troubleshooting

### Service Won't Start
1. Check logs: `just logs <service>`
2. Verify dependencies running
3. Check health endpoint manually
4. Review environment variables

### Authentication Issues
1. Verify token is valid
2. Check Traefik middleware
3. Review auth service logs
4. Test `/verify` endpoint

### Network Issues
1. Ensure on `public` network
2. Check service discovery
3. Verify Traefik routing
4. Test internal connectivity

## Best Practices

1. **Use Health Checks**: Every service must prove readiness
2. **Central Logging**: All logs to `./logs/`
3. **Environment Config**: All config via `.env`
4. **Graceful Shutdown**: Handle SIGTERM properly
5. **Resource Limits**: Set appropriate limits
6. **Security First**: Never bypass auth layer
