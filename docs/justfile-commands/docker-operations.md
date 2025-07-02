# Docker Operations Commands

Docker operations follow the divine orchestration pattern using docker-compose. All services are managed through the blessed compose files.

## Core Docker Philosophy

- 🐳 **Compose is the divine orchestrator** - All services through compose
- 🏗️ **One service, one directory** - Divine isolation
- 🌐 **Named networks** - Bridge thy services via public
- 🔥 **Holy Traefik** - The one proxy to rule all services
- ✅ **Health checks mandatory** - Prove thy readiness

## Build Commands

### `build` - Flexible Service Building

```bash
# Build all services
just build

# Build specific services
just build auth mcp-fetch

# The command automatically:
# - Creates the public network
# - Creates required volumes
# - Generates compose includes
# - Generates Traefik middlewares
```

### Build Process Details

1. **Network Creation**: Ensures `public` network exists
2. **Volume Creation**: Creates all required volumes
   - traefik-certificates
   - redis-data
   - coverage-data
   - auth-keys
   - mcp-memory-data
3. **Include Generation**: Based on enabled services in .env
4. **Middleware Generation**: Traefik configuration from templates

## Service Lifecycle

### `up` - Start Services

```bash
# Start all enabled services
just up

# Start with specific options
just up --scale mcp-fetch=2

# Fresh start with rebuild
just up-fresh
```

The `up` command:
- Starts services in detached mode
- Waits for health checks
- Reports service readiness

### `down` - Stop Services

```bash
# Stop all services
just down

# Remove volumes too
just down --volumes

# Remove everything including orphans
just down --volumes --remove-orphans
```

### `rebuild` - No-Cache Rebuild

```bash
# Rebuild all services from scratch
just rebuild

# Rebuild specific services
just rebuild auth mcp-fetch
```

The rebuild process:
1. Stops target services
2. Removes containers
3. Builds with `--no-cache`
4. Starts fresh containers
5. Verifies health

## Service Management

### `logs` - Flexible Log Viewing

```bash
# View all logs
just logs

# Follow specific service
just logs -f auth

# Last 100 lines
just logs --tail 100

# Multiple services
just logs auth redis
```

### `exec` - Container Commands

```bash
# Redis CLI
just exec redis redis-cli

# Python shell in auth
just exec auth python

# Run migrations
just exec auth python manage.py migrate
```

## Docker Compose Architecture

### Main Compose File Structure

```yaml
# docker-compose.yml
include:
  - traefik/docker-compose.yml
  - auth/docker-compose.yml
  # Generated includes based on .env

x-mcp-service: &mcp-service
  restart: unless-stopped
  networks:
    - public
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

### Service-Specific Compose Files

Each service has its own docker-compose.yml:

```yaml
# mcp-fetch/docker-compose.yml
services:
  mcp-fetch:
    <<: *mcp-service
    build:
      context: ./mcp-fetch
      dockerfile: Dockerfile
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

## Network Architecture

All services connect via the `public` network:

```
┌─────────────┐
│   Traefik   │ ← External HTTPS
├─────────────┤
│   public    │ ← Named Docker network
├─────────────┼─────────────┬─────────────┐
│    Auth     │    Redis    │ MCP Services│
└─────────────┴─────────────┴─────────────┘
```

## Volume Management

Persistent data stored in named volumes:

| Volume | Purpose | Used By |
|--------|---------|---------|
| traefik-certificates | SSL certificates | Traefik |
| redis-data | Token/session storage | Redis |
| coverage-data | Test coverage data | Coverage harvester |
| auth-keys | RSA signing keys | Auth service |
| mcp-memory-data | MCP memory service | mcp-memory |

## Health Check Patterns

Every service must implement health checks:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

For MCP services using StreamableHTTP:
```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",...}' \
    | grep -q '\"protocolVersion\"'"]
```

## Common Operations

### Development Workflow

```bash
# Morning startup
just up
just logs -f

# After code changes
just rebuild auth
just logs -f auth

# Check everything
just status
just check-health
```

### Debugging Services

```bash
# Check why service won't start
just logs auth
docker compose ps

# Inspect service
docker compose exec auth env
docker compose exec auth ps aux

# Network debugging
docker compose exec auth ping redis
```

### Production Patterns

```bash
# Clean restart
just down --volumes
just up-fresh

# Update single service
just rebuild mcp-fetch
just logs -f mcp-fetch

# Scale service
docker compose up -d --scale mcp-fetch=3
```

## Environment-Based Configuration

Services enabled via .env:
```bash
MCP_FETCH_ENABLED=true
MCP_FILESYSTEM_ENABLED=false
# ... etc
```

The `generate-includes` script creates docker-compose.includes.yml based on enabled services.

## Troubleshooting

### Service Won't Start
1. Check logs: `just logs <service>`
2. Verify .env configuration
3. Check health endpoint manually
4. Ensure network exists: `docker network ls`

### Can't Connect Between Services
1. Verify both on `public` network
2. Use service names (not localhost)
3. Check firewall rules in containers
4. Test with ping/curl from containers

### Volume Issues
1. List volumes: `docker volume ls`
2. Inspect volume: `docker volume inspect <name>`
3. Clean volumes: `just down --volumes`
4. Recreate: `just volumes-create`

Remember: **Docker Compose for All Services or Container Chaos!**
