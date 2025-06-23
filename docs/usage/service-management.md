# Service Management

This guide covers managing MCP services in the gateway using the available `just` commands.

## Service Overview

The MCP OAuth Gateway manages multiple services:
- **Core Services**: auth, traefik, redis
- **MCP Services**: mcp-fetch, mcp-filesystem, mcp-memory, etc.

## Starting Services

### Start All Services

```bash
# Start all services in detached mode
just up

# Start with specific docker-compose options
just up --build
just up --force-recreate

# Start all services with fresh build
just up-fresh
```

### Service Dependencies

Services start in dependency order:
1. Networks created via `just network-create`
2. Volumes created via `just volumes-create` 
3. Docker-compose includes generated
4. All services start

## Stopping Services

```bash
# Stop all services
just down

# Stop and remove volumes
just down -v

# Stop and remove orphan containers
just down --remove-orphans
```

## Building and Rebuilding Services

### Build Services

```bash
# Build all services
just build

# Build specific services
just build auth
just build auth mcp-fetch mcp-memory
```

### Rebuild Services

```bash
# Rebuild all services (with --no-cache by default)
just rebuild

# Rebuild specific services
just rebuild auth
just rebuild mcp-fetch mcp-memory
```

## Service Logs

### View Logs

```bash
# All service logs
just logs

# Specific service logs
just logs auth

# Follow logs (real-time)
just logs -f
just logs -f mcp-fetch

# Last N lines
just logs --tail=100
just logs --tail=50 auth
```

### Log Management

```bash
# Purge all container logs (restarts services)
just logs-purge
```

## Service Configuration

### Update Configuration

1. Edit the `.env` file:
```bash
vim .env
```

2. Rebuild and restart the affected service:
```bash
just rebuild auth
```

3. Verify configuration:
```bash
just exec auth env | grep NEW_VAR
```

## Service Health

### Health Checks

```bash
# Comprehensive health check
just check-health

# Quick health check
just health-quick

# Check SSL certificates
just check-ssl
```

### Service Readiness

```bash
# Ensure all services are ready
just ensure-services-ready
```

## Service Access

### Execute Commands in Services

```bash
# Execute command in service
just exec redis redis-cli
just exec auth bash
just exec mcp-fetch sh

# Check service environment
just exec mcp-fetch env
```

## Common Tasks

### Add New MCP Service

1. Create service directory:
```bash
mkdir mcp-custom
```

2. Add Dockerfile in `mcp-custom/`

3. Add service to appropriate docker-compose file

4. Enable service in `.env`:
```bash
echo "ENABLE_MCP_CUSTOM=true" >> .env
```

5. Generate includes and start:
```bash
just generate-includes
just up
```

### Update Service

```bash
# Rebuild specific service from scratch
just rebuild mcp-fetch

# Check logs after update
just logs -f mcp-fetch
```

## Best Practices

1. **Always use `just` commands** - Never run docker commands directly
2. **Check service health** - Use `just ensure-services-ready` before tests
3. **Monitor logs** - Use `just logs -f` to watch for issues
4. **Clean rebuilds** - Use `just rebuild` for clean slate
5. **Manage OAuth data** - Use OAuth backup commands before major changes

## Troubleshooting

### Service Won't Start

```bash
# Check logs
just logs auth

# Ensure dependencies are ready
just ensure-services-ready

# Try fresh rebuild
just rebuild auth
```

### View Docker Status

```bash
# Use docker compose directly (only for debugging)
docker compose ps
```

### Network Issues

```bash
# Ensure network exists
just network-create

# Check service connectivity
just exec auth curl http://redis:6379
```

## Related Documentation

- [Commands Reference](commands.md)
- [Monitoring](monitoring.md)
- [Token Management](token-management.md)