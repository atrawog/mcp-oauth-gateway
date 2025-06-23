# Service Management

This guide covers managing MCP services in the gateway, including starting, stopping, scaling, and monitoring individual services.

## Service Overview

The MCP OAuth Gateway manages multiple services:
- **Core Services**: auth, traefik, redis
- **MCP Services**: mcp-fetch, mcp-filesystem, mcp-memory, etc.

## Starting Services

### Start All Services

```bash
# Start all services
just up

# Start in detached mode
just up -d

# Start with build
just up --build
```

### Start Specific Services

```bash
# Start single service
just up mcp-fetch

# Start multiple services
just up auth redis mcp-fetch

# Start with dependencies
just up --with-dependencies mcp-fetch
```

### Service Dependencies

Services start in dependency order:
1. Networks created
2. Redis starts
3. Auth service starts
4. Traefik starts
5. MCP services start

## Stopping Services

### Stop All Services

```bash
# Stop all services gracefully
just down

# Stop and remove volumes
just down -v

# Stop immediately (force)
just down --force
```

### Stop Specific Services

```bash
# Stop single service
just stop mcp-fetch

# Stop multiple services
just stop mcp-fetch mcp-filesystem

# Stop with timeout
just stop --timeout 30 mcp-fetch
```

## Restarting Services

### Restart Commands

```bash
# Restart all services
just restart

# Restart specific service
just restart auth

# Restart with new config
just restart --force-recreate mcp-fetch
```

### Rolling Restarts

For zero-downtime updates:

```bash
# Scale service up
just scale mcp-fetch=2

# Update and restart instances
just rolling-restart mcp-fetch

# Scale back down
just scale mcp-fetch=1
```

## Service Status

### Check Status

```bash
# View all services
just ps

# View specific service
just ps mcp-fetch

# View with details
just ps --format json
```

### Health Checks

```bash
# Check all health endpoints
just health-check

# Check specific service
just health-check mcp-fetch

# Continuous monitoring
watch -n 5 'just health-check'
```

## Service Logs

### View Logs

```bash
# All service logs
just logs

# Specific service logs
just logs auth

# Follow logs (tail -f)
just logs -f mcp-fetch

# Last N lines
just logs --tail 100 auth

# Filter by time
just logs --since 1h mcp-fetch
```

### Log Analysis

```bash
# Search logs
just logs | grep ERROR

# Count errors by service
just logs --format json | jq 'select(.level=="ERROR") | .service' | sort | uniq -c

# Export logs
just logs > gateway-logs.txt
```

## Service Configuration

### Update Configuration

```bash
# Update environment variable
echo "NEW_VAR=value" >> .env

# Reload service with new config
just restart mcp-fetch

# Verify configuration
just exec mcp-fetch env | grep NEW_VAR
```

### Service-Specific Config

```bash
# Edit service config
vim mcp-fetch/.env

# Apply changes
just rebuild mcp-fetch
just restart mcp-fetch
```

## Scaling Services

### Manual Scaling

```bash
# Scale service replicas
just scale mcp-fetch=3

# Scale multiple services
just scale mcp-fetch=3 mcp-filesystem=2

# Scale down
just scale mcp-fetch=1
```

### Auto-Scaling Configuration

```yaml
# docker-compose.yml
services:
  mcp-fetch:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

## Service Maintenance

### Update Services

```bash
# Pull latest images
just pull

# Update specific service
just pull mcp-fetch

# Update and restart
just update mcp-fetch
```

### Backup Service Data

```bash
# Backup Redis data
just backup redis

# Backup service config
just backup-config mcp-fetch

# Full backup
just backup-all
```

### Service Cleanup

```bash
# Remove stopped containers
just cleanup

# Prune unused images
just prune-images

# Deep clean (removes volumes)
just deep-clean
```

## Monitoring Services

### Resource Usage

```bash
# View resource stats
just stats

# Monitor specific service
just stats mcp-fetch

# Export metrics
just stats --format json > metrics.json
```

### Performance Metrics

```bash
# Request latency
just metrics latency

# Throughput
just metrics throughput

# Error rates
just metrics errors
```

## Service Debugging

### Access Service Shell

```bash
# Execute command in service
just exec mcp-fetch sh

# Run interactive shell
just exec -it auth bash

# Check service environment
just exec mcp-fetch env
```

### Debug Mode

```bash
# Enable debug logging
just debug mcp-fetch

# View debug output
just logs -f mcp-fetch

# Disable debug mode
just debug --off mcp-fetch
```

## Common Tasks

### Add New Service

1. Create service directory
2. Add Dockerfile
3. Update docker-compose.yml
4. Configure routing in Traefik
5. Test service

```bash
# Create service structure
just new-service mcp-custom

# Start new service
just up mcp-custom
```

### Remove Service

```bash
# Stop service
just stop mcp-old

# Remove from compose
vim docker-compose.yml

# Clean up
just cleanup
```

### Service Migration

```bash
# Export service data
just export mcp-fetch

# Import to new instance
just import mcp-fetch data.tar

# Verify migration
just test mcp-fetch
```

## Best Practices

1. **Monitor Health** - Regular health checks
2. **Log Rotation** - Prevent disk fill
3. **Resource Limits** - Set CPU/memory limits
4. **Graceful Shutdown** - Use proper stop signals
5. **Backup Data** - Regular service backups
6. **Update Regularly** - Keep services current
7. **Document Changes** - Track config updates

## Troubleshooting

### Service Won't Start

```bash
# Check logs
just logs service-name

# Verify config
just validate-config service-name

# Check dependencies
just deps service-name
```

### Service Crashes

```bash
# View crash logs
just logs --tail 500 service-name

# Check restart count
just ps service-name

# Increase resources
just scale-resources service-name
```

### Network Issues

```bash
# Test connectivity
just exec service-name ping other-service

# Check DNS
just exec service-name nslookup auth

# Verify networks
docker network ls
```

## Related Documentation

- [Commands Reference](commands.md)
- [Monitoring](monitoring.md)
- [Token Management](token-management.md)