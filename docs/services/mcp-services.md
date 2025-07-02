# MCP Services

The Model Context Protocol services that provide actual functionality to MCP clients, all protected by the OAuth gateway.

## Service Architecture

MCP services follow two blessed implementation patterns:

```{mermaid}
graph TB
    subgraph "Proxy Pattern Services"
        PROXY[mcp-streamablehttp-proxy]
        STDIO[Official stdio MCP Server]
        PROXY -->|spawns| STDIO
    end

    subgraph "Native Pattern Services"
        NATIVE[Native StreamableHTTP<br/>Implementation]
    end

    subgraph "Client Access"
        CLIENT[MCP Client]
        CLIENT -->|HTTPS + Bearer| PROXY
        CLIENT -->|HTTPS + Bearer| NATIVE
    end
```

## Implementation Patterns

### Proxy Pattern

Services using `mcp-streamablehttp-proxy` to wrap official servers:

| Service | Wrapped Server | Purpose |
|---------|----------------|---------|
| [mcp-fetch](mcp-fetch) | mcp-server-fetch | Web content fetching |
| [mcp-filesystem](mcp-filesystem) | mcp-server-filesystem | File system operations |
| [mcp-memory](mcp-memory) | @modelcontextprotocol/server-memory | Persistent storage |
| [mcp-time](mcp-time) | mcp-server-time | Time/date operations |
| [mcp-everything](mcp-everything) | mcp-server-everything | Comprehensive toolset |
| [mcp-playwright](mcp-playwright) | @modelcontextprotocol/server-playwright | Browser automation |
| [mcp-sequentialthinking](mcp-sequentialthinking) | @modelcontextprotocol/server-sequential-thinking | Sequential reasoning |
| [mcp-tmux](mcp-tmux) | mcp-server-tmux | Terminal multiplexer |

### Native Pattern

Services with direct StreamableHTTP implementation:

| Service | Package | Purpose |
|---------|---------|---------|
| [mcp-fetchs](mcp-fetchs) | mcp-fetch-streamablehttp-server | Secure fetch with SSRF protection |
| [mcp-echo-stateful](mcp-echo-stateful) | mcp-echo-streamablehttp-server-stateful | Stateful diagnostics |
| [mcp-echo-stateless](mcp-echo-stateless) | mcp-echo-streamablehttp-server-stateless | Stateless testing |

## Common Configuration

### Docker Compose Pattern

All MCP services follow this blessed pattern:

```yaml
services:
  mcp-service:
    <<: *mcp-service  # Inherit common configuration
    build:
      context: ./mcp-service
      dockerfile: Dockerfile
    environment:
      # Service-specific config
      - SERVICE_CONFIG=${SERVICE_CONFIG}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    labels:
      # Traefik routing
      - "traefik.enable=true"
      - "traefik.http.routers.service.rule=Host(`service.${BASE_DOMAIN}`)"
      - "traefik.http.routers.service.priority=2"
      - "traefik.http.routers.service.tls=true"
      - "traefik.http.routers.service.tls.certresolver=letsencrypt"
      - "traefik.http.routers.service.middlewares=mcp-auth@file"
      - "traefik.http.services.service.loadbalancer.server.port=3000"
```

### Common Extension

Defined in main docker-compose.yml:

```yaml
x-mcp-service: &mcp-service
  restart: unless-stopped
  networks:
    - public
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
  volumes:
    - ./logs/${SERVICE_NAME}:/logs
```

## Health Check Patterns

### Standard HTTP Health Check

For services with dedicated health endpoints:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

### MCP Protocol Health Check

For native StreamableHTTP services:

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"${MCP_PROTOCOL_VERSION:-2025-06-18}\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
    | grep -q '\"protocolVersion\":\"${MCP_PROTOCOL_VERSION:-2025-06-18}\"'"]
```

## Service Management

### Enable/Disable Services

Control which services run via .env:

```bash
# Core services (usually all enabled)
ENABLE_MCP_FETCH=true
ENABLE_MCP_FILESYSTEM=true
ENABLE_MCP_MEMORY=true
ENABLE_MCP_TIME=true

# Optional services
ENABLE_MCP_EVERYTHING=false
ENABLE_MCP_PLAYWRIGHT=false
ENABLE_MCP_SEQUENTIALTHINKING=false
ENABLE_MCP_TMUX=false

# Testing services
ENABLE_MCP_ECHO_STATEFUL=true
ENABLE_MCP_ECHO_STATELESS=true
```

### Service URLs

Each service can have multiple URLs:

```bash
# Primary and alternative URLs
MCP_FETCH_URLS=https://fetch.example.com/mcp,https://mcp-fetch.example.com/mcp
MCP_FILESYSTEM_URLS=https://fs.example.com/mcp,https://filesystem.example.com/mcp
```

## Authentication Flow

All MCP services are protected by ForwardAuth:

```
1. Client sends request with Bearer token
2. Traefik intercepts and validates via Auth service
3. If valid, request forwarded to MCP service
4. MCP service processes without auth logic
5. Response returned through Traefik
```

## Logging

### Log Structure

All services log to `./logs/{service-name}/`:

```
logs/
├── mcp-fetch/
│   ├── access.log
│   └── error.log
├── mcp-filesystem/
│   └── service.log
└── mcp-memory/
    └── memory.log
```

### Log Rotation

Configured via logrotate:

```bash
# Setup rotation
just logs-rotation-setup

# Manual rotation
just logs-rotate
```

## Performance Considerations

### Proxy Pattern Services

- Additional process overhead (subprocess)
- Memory usage: proxy + wrapped server
- Startup time includes subprocess spawn
- Session management in proxy layer

### Native Pattern Services

- Direct HTTP handling
- Lower memory footprint
- Faster startup
- Session handling varies by service

## Scaling Strategies

### Stateless Services

Easy horizontal scaling:

```bash
# Scale stateless services
docker compose up -d --scale mcp-fetch=3
docker compose up -d --scale mcp-echo-stateless=5
```

### Stateful Services

Require session affinity:

```yaml
# Traefik sticky sessions
- "traefik.http.services.service.loadbalancer.sticky=true"
- "traefik.http.services.service.loadbalancer.sticky.cookie.name=mcp_session"
```

## Health Checks

### Service Health Status

```bash
# Check all MCP services
just check-services

# Individual service health
curl https://service.example.com/health
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   - Check Docker logs: `just logs service-name`
   - Verify wrapped server installed (proxy pattern)
   - Check port conflicts

2. **Authentication Errors**
   - Verify Bearer token valid
   - Check ForwardAuth middleware applied
   - Review Auth service logs

3. **Protocol Errors**
   - Verify protocol version compatibility
   - Check request format
   - Enable debug logging

### Debug Commands

```bash
# Service logs
just logs -f mcp-fetch

# Container inspection
docker exec mcp-fetch ps aux
docker exec mcp-fetch env

# Network testing
docker exec mcp-fetch ping auth
docker exec mcp-fetch curl http://localhost:3000/health
```

## Best Practices

1. **Health Checks**: Every service must have health validation
2. **Logging**: Centralized logs with rotation
3. **Health Checks**: Verify service status
4. **Error Handling**: Graceful degradation
5. **Resource Limits**: Set appropriate constraints
6. **Documentation**: Keep service docs updated
