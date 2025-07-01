# Redis Service

The divine storage backend for OAuth tokens, client registrations, and session data.

## Overview

Redis provides persistent storage for the Auth service, maintaining:

- OAuth client registrations
- Access and refresh tokens
- Authorization codes
- CSRF state tokens
- User token indices
- Session data

## Configuration

### Docker Compose

```yaml
services:
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
      - ./logs/redis:/logs
    networks:
      - public
    healthcheck:
      test: ["CMD", "redis-cli", "--pass", "${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s
    ports:
      - "127.0.0.1:6379:6379"  # Local access only
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `REDIS_PASSWORD` | Redis authentication password | Yes |

## Data Schema

### Key Patterns

```
oauth:client:{client_id}        # Client registration data
oauth:state:{state}             # CSRF state (5 min TTL)
oauth:code:{code}               # Auth codes (1 year TTL)
oauth:token:{jti}               # Access tokens (30 days TTL)
oauth:refresh:{token}           # Refresh tokens (1 year TTL)
oauth:user_tokens:{username}    # User token index
```

### Data Structures

#### Client Registration
```json
{
  "client_id": "client_abc123",
  "client_secret": "secret_xyz789",
  "client_name": "My MCP Client",
  "redirect_uris": ["http://localhost:8080/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "registration_access_token": "reg-token123",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-04-01T00:00:00Z"
}
```

#### Token Data
```json
{
  "client_id": "client_abc123",
  "user_id": "github|username",
  "scope": "mcp:*",
  "issued_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-01-31T00:00:00Z"
}
```

## Persistence

### Data Volume

```yaml
volumes:
  redis-data:
    external: true
```

### Backup Strategy

```bash
# Manual backup
docker exec redis redis-cli --pass $REDIS_PASSWORD BGSAVE

# Copy backup file
docker cp redis:/data/dump.rdb ./backups/redis-$(date +%Y%m%d-%H%M%S).rdb
```

### Restore Process

```bash
# Stop Redis
docker compose stop redis

# Copy backup
docker cp ./backups/redis-backup.rdb redis:/data/dump.rdb

# Start Redis
docker compose start redis
```

## Security

### Authentication

- Password required via `requirepass`
- Set strong password via `REDIS_PASSWORD`
- No default password allowed

### Network Security

- Only accessible within Docker network
- Optional local port binding (127.0.0.1 only)
- No external exposure

### Access Control

```bash
# Connect with password
redis-cli -h redis -a $REDIS_PASSWORD

# Or via AUTH command
redis-cli -h redis
> AUTH $REDIS_PASSWORD
```

## Monitoring

### Health Check

```bash
# Via Docker
docker exec redis redis-cli --pass $REDIS_PASSWORD ping
# Response: PONG

# Via justfile
just exec redis redis-cli --pass $REDIS_PASSWORD ping
```

### Memory Usage

```bash
# Memory info
docker exec redis redis-cli --pass $REDIS_PASSWORD INFO memory

# Key statistics
docker exec redis redis-cli --pass $REDIS_PASSWORD INFO keyspace
```

### Performance Metrics

```bash
# Operations per second
docker exec redis redis-cli --pass $REDIS_PASSWORD INFO stats

# Connected clients
docker exec redis redis-cli --pass $REDIS_PASSWORD CLIENT LIST
```

## Maintenance

### View Keys

```bash
# List all OAuth keys
docker exec redis redis-cli --pass $REDIS_PASSWORD KEYS "oauth:*"

# Count by type
docker exec redis redis-cli --pass $REDIS_PASSWORD KEYS "oauth:client:*" | wc -l
```

### Clean Expired Data

```bash
# Redis handles TTL automatically
# Force cleanup of expired keys
docker exec redis redis-cli --pass $REDIS_PASSWORD SCAN 0 MATCH oauth:*
```

### Database Size

```bash
# Total keys
docker exec redis redis-cli --pass $REDIS_PASSWORD DBSIZE

# Database file size
docker exec redis ls -lh /data/dump.rdb
```

## Troubleshooting

### Connection Issues

```bash
# Test from auth service
docker exec auth redis-cli -h redis -a $REDIS_PASSWORD ping

# Check network
docker network inspect public | grep -A5 redis
```

### Memory Issues

```bash
# Check max memory
docker exec redis redis-cli --pass $REDIS_PASSWORD CONFIG GET maxmemory

# Set memory limit
docker exec redis redis-cli --pass $REDIS_PASSWORD CONFIG SET maxmemory 256mb
```

### Performance Issues

```bash
# Slow log
docker exec redis redis-cli --pass $REDIS_PASSWORD SLOWLOG GET 10

# Monitor commands
docker exec redis redis-cli --pass $REDIS_PASSWORD MONITOR
```

## Integration with Auth Service

The Auth service connects to Redis for all storage:

```python
# Auth service configuration
REDIS_URL = f"redis://:{REDIS_PASSWORD}@redis:6379/0"

# Connection pooling
redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    max_connections=50
)
```

## Best Practices

1. **Strong Password**: Use `just generate-redis-password`
2. **Regular Backups**: Implement automated backup
3. **Monitor Memory**: Set appropriate limits
4. **TTL Usage**: Let Redis handle expiration
5. **Connection Pooling**: Reuse connections
6. **Persistence**: Enable AOF for critical data

## Redis Commands Reference

### Client Management
```bash
# Get client data
GET oauth:client:client_123

# List all clients
KEYS oauth:client:*

# Delete client
DEL oauth:client:client_123
```

### Token Management
```bash
# Check token
GET oauth:token:jti_123

# Token TTL
TTL oauth:token:jti_123

# Revoke token
DEL oauth:token:jti_123
```

### User Tokens
```bash
# Get user's tokens
SMEMBERS oauth:user_tokens:username

# Add token to user
SADD oauth:user_tokens:username jti_123

# Remove token
SREM oauth:user_tokens:username jti_123
```
