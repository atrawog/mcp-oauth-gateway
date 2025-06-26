# Redis Service

Redis provides persistent state storage for the MCP OAuth Gateway, managing OAuth flows, client registrations, tokens, and session state.

## Overview

Redis serves as the central state store providing:
- OAuth flow state management
- Client registration persistence
- Token storage and indexing
- Session state for MCP services
- High-performance key-value storage

## Architecture

The service uses:
- **Version**: Redis 7 Alpine
- **Port**: 6379 (internal only)
- **Persistence**: AOF and RDB enabled
- **Volume**: redis-data for persistent storage

## Configuration

### Environment Variables

```bash
# Redis Security (REQUIRED)
REDIS_PASSWORD=your-secure-redis-password
REDIS_URL=redis://redis:6379
```

### Docker Compose

```yaml
redis:
  image: redis:7-alpine
  container_name: redis
  restart: unless-stopped
  networks:
    - internal
  ports:
    - "127.0.0.1:6379:6379"  # Local access only
  volumes:
    - redis-data:/data
  command: >
    redis-server
    --requirepass ${REDIS_PASSWORD}
    --appendonly yes
    --appendfilename "redis.aof"
    --save 60 1
    --save 300 10
    --save 900 100
  healthcheck:
    test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${REDIS_PASSWORD}", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
```

## Data Schema

### OAuth State Management

```redis
# Temporary OAuth flow state
oauth:state:{state}              # TTL: 5 minutes
{
  "client_id": "...",
  "redirect_uri": "...",
  "code_challenge": "...",
  "code_challenge_method": "S256"
}

# Authorization codes
oauth:code:{code}                # TTL: 1 year
{
  "client_id": "...",
  "user_id": "...",
  "redirect_uri": "...",
  "scope": "...",
  "code_challenge": "..."
}
```

### Client Registration

```redis
# Client registration data
oauth:client:{client_id}         # No TTL (eternal or CLIENT_LIFETIME)
{
  "client_id": "...",
  "client_secret": "...",
  "client_name": "...",
  "redirect_uris": [...],
  "created_at": "...",
  "expires_at": "..."
}

# Client ID index
oauth:client_index               # Set of all client IDs
```

### Token Management

```redis
# Active JWT tokens
oauth:token:{jti}                # TTL: ACCESS_TOKEN_LIFETIME
{
  "user_id": "...",
  "username": "...",
  "client_id": "...",
  "scope": "...",
  "exp": ...
}

# Refresh tokens
oauth:refresh:{token}            # TTL: REFRESH_TOKEN_LIFETIME
{
  "user_id": "...",
  "client_id": "...",
  "jti": "..."
}

# User token index
oauth:user_tokens:{username}     # Set of user's JTIs
```

### MCP Session State

```redis
# Session state
redis:session:{session_id}:state # MCP session metadata
{
  "client_id": "...",
  "created_at": "...",
  "last_active": "..."
}

# Session messages
redis:session:{session_id}:messages # List of pending messages
```

## Persistence Configuration

### Append-Only File (AOF)
- Enabled for durability
- Logs every write operation
- Automatic rewrite on size threshold

### RDB Snapshots
- Save after 60 seconds if 1+ keys changed
- Save after 300 seconds if 10+ keys changed
- Save after 900 seconds if 100+ keys changed

### Volume Persistence
- Data stored in `redis-data` Docker volume
- Survives container restarts
- Backup recommended for production

## Operations

### Starting Redis

```bash
# Start Redis only
just up redis

# View logs
just logs redis

# Check health
docker exec redis redis-cli -a $REDIS_PASSWORD ping
```

### Accessing Redis CLI

```bash
# Access Redis CLI
docker exec -it redis redis-cli -a $REDIS_PASSWORD

# Common commands
KEYS oauth:*              # List OAuth keys
GET oauth:client:123      # Get client data
TTL oauth:token:456       # Check token TTL
DBSIZE                    # Total key count
```

### Monitoring

```bash
# Memory usage
docker exec redis redis-cli -a $REDIS_PASSWORD INFO memory

# Connected clients
docker exec redis redis-cli -a $REDIS_PASSWORD CLIENT LIST

# Stats
docker exec redis redis-cli -a $REDIS_PASSWORD INFO stats
```

## Backup and Restore

### Manual Backup

```bash
# Trigger RDB snapshot
docker exec redis redis-cli -a $REDIS_PASSWORD BGSAVE

# Copy backup file
docker cp redis:/data/dump.rdb ./redis-backup-$(date +%Y%m%d).rdb
```

### Restore from Backup

```bash
# Stop Redis
just down redis

# Copy backup to volume
docker run --rm -v redis-data:/data -v $(pwd):/backup alpine \
  cp /backup/redis-backup.rdb /data/dump.rdb

# Start Redis
just up redis
```

## Security Considerations

1. **Password Protection** - Always set strong REDIS_PASSWORD
2. **Network Isolation** - Only accessible within Docker network
3. **No External Ports** - Bound to 127.0.0.1 only
4. **Command Restrictions** - Consider disabling dangerous commands
5. **Memory Limits** - Set maxmemory policy for production

## Performance Tuning

### Memory Management
```redis
# Set max memory (in redis.conf or runtime)
CONFIG SET maxmemory 2gb
CONFIG SET maxmemory-policy allkeys-lru
```

### Connection Limits
```redis
# Adjust max clients
CONFIG SET maxclients 10000
```

### Persistence Tuning
```redis
# Adjust save intervals for performance
CONFIG SET save "3600 1 1800 10 300 100"
```

## Troubleshooting

### Common Issues

#### Connection Refused
- Check Redis is running: `docker ps | grep redis`
- Verify password: `echo $REDIS_PASSWORD`
- Check network connectivity

#### Memory Issues
- Monitor memory: `docker stats redis`
- Check eviction policy
- Consider increasing container memory

#### Persistence Issues
- Check volume permissions
- Verify disk space
- Review AOF/RDB settings

### Debugging

```bash
# View detailed logs
just logs redis --tail=100

# Check Redis configuration
docker exec redis redis-cli -a $REDIS_PASSWORD CONFIG GET "*"

# Monitor commands in real-time
docker exec redis redis-cli -a $REDIS_PASSWORD MONITOR
```

## Architecture Notes

- Single Redis instance (consider Redis Sentinel for HA)
- All data in memory with disk persistence
- No clustering (sufficient for gateway needs)
- Atomic operations ensure consistency
- Used only by Auth service

## Related Services

- [Auth Service](auth.md) - Primary Redis consumer
- [Components](../architecture/components.md) - System architecture
