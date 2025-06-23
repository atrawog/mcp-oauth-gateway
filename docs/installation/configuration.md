# Configuration Reference

This guide provides a comprehensive reference for all configuration options in the MCP OAuth Gateway.

## Environment Variables

### Core Configuration

```bash
# Base domain for all services
BASE_DOMAIN=gateway.example.com

# Environment (development, staging, production)
ENVIRONMENT=production

# Debug mode (true/false)
DEBUG=false

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

### OAuth Configuration

```bash
# GitHub OAuth Application
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# JWT Configuration
GATEWAY_JWT_SECRET=your-generated-jwt-secret
JWT_ALGORITHM=RS256
JWT_EXPIRY_DAYS=30

# OAuth Tokens (auto-generated)
GATEWAY_OAUTH_ACCESS_TOKEN=
GATEWAY_OAUTH_REFRESH_TOKEN=
GATEWAY_OAUTH_CLIENT_ID=
GATEWAY_OAUTH_CLIENT_SECRET=

# Client Configuration
CLIENT_LIFETIME=7776000  # 90 days in seconds (0 for eternal)
MAX_CLIENTS_PER_USER=10
```

### Security Configuration

```bash
# Allowed GitHub Users (comma-separated)
ALLOWED_GITHUB_USERS=user1,user2,org:team

# CORS Settings
CORS_ALLOWED_ORIGINS=https://claude.ai
CORS_ALLOW_CREDENTIALS=true

# Rate Limiting
RATE_LIMIT_OAUTH=10/minute
RATE_LIMIT_MCP=100/minute

# Session Configuration
SESSION_TIMEOUT=3600  # 1 hour
SESSION_IDLE_TIMEOUT=1800  # 30 minutes
```

### MCP Configuration

```bash
# MCP Protocol Version
MCP_PROTOCOL_VERSION=2025-06-18

# MCP Service Defaults
MCP_REQUEST_TIMEOUT=30
MCP_MAX_MESSAGE_SIZE=10485760  # 10MB

# Service-specific settings
MCP_FETCH_TIMEOUT=10
MCP_FILESYSTEM_ROOT=/data
MCP_MEMORY_MAX_SIZE=1048576  # 1MB
```

### Redis Configuration

```bash
# Redis Connection
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Redis Settings
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
```

### Traefik Configuration

```bash
# Let's Encrypt
LETSENCRYPT_EMAIL=admin@example.com
LETSENCRYPT_STAGING=false

# Traefik Settings
TRAEFIK_LOG_LEVEL=INFO
TRAEFIK_ACCESS_LOG=true
TRAEFIK_DASHBOARD=false
TRAEFIK_METRICS=true
```

## Configuration Files

### .env File Structure

Create a `.env` file in the project root:

```bash
# Copy from .env.example
cp .env.example .env

# Edit with your values
vim .env
```

### Docker Compose Override

For environment-specific settings, create `docker-compose.override.yml`:

```yaml
services:
  auth:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
  
  mcp-fetch:
    volumes:
      - ./custom-config:/config
```

## Service-Specific Configuration

### Auth Service

Located in `auth/.env`:

```bash
# FastAPI Settings
WORKERS=4
HOST=0.0.0.0
PORT=8000
RELOAD=false

# Database
DATABASE_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
```

### MCP Services

Each MCP service can have its own configuration:

```bash
# mcp-fetch/.env
FETCH_USER_AGENT=MCP-Gateway/1.0
FETCH_MAX_SIZE=5242880  # 5MB
FETCH_TIMEOUT=30

# mcp-filesystem/.env
FS_ROOT=/data
FS_ALLOW_HIDDEN=false
FS_MAX_FILE_SIZE=10485760  # 10MB
```

## Advanced Configuration

### Custom SSL Certificates

To use custom certificates instead of Let's Encrypt:

```bash
# In .env
SSL_CERT_PATH=/certs/fullchain.pem
SSL_KEY_PATH=/certs/privkey.pem
USE_LETSENCRYPT=false
```

### Redis Persistence

Configure Redis persistence:

```bash
# In redis/redis.conf
save 900 1
save 300 10
save 60 10000
appendonly yes
```

### Logging Configuration

Advanced logging setup:

```bash
# Centralized logging
LOG_FORMAT=json
LOG_OUTPUT=file
LOG_FILE_PATH=/logs/gateway.log
LOG_ROTATION=daily
LOG_RETENTION_DAYS=30
```

## Validation

### Configuration Validation

The gateway validates configuration on startup:

```bash
# Test configuration
just test-config

# Validate environment
just validate-env
```

### Required Variables

These variables must be set:

- `BASE_DOMAIN`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`
- `GATEWAY_JWT_SECRET`
- `LETSENCRYPT_EMAIL` (for production)

### Auto-Generated Variables

These are generated automatically:

- `GATEWAY_OAUTH_ACCESS_TOKEN`
- `GATEWAY_OAUTH_REFRESH_TOKEN`
- `GATEWAY_OAUTH_CLIENT_ID`
- `GATEWAY_OAUTH_CLIENT_SECRET`

## Best Practices

1. **Use .env.example** - Keep it updated with all variables
2. **Never commit .env** - Contains secrets
3. **Rotate secrets regularly** - Especially JWT secrets
4. **Use strong passwords** - For Redis and other services
5. **Limit allowed users** - Use GitHub user whitelist
6. **Monitor configuration** - Log config changes

## Troubleshooting

### Common Issues

1. **Missing Variables**
   ```bash
   ERROR: Required variable GITHUB_CLIENT_ID not set
   ```
   Solution: Check .env file exists and is loaded

2. **Invalid JWT Secret**
   ```bash
   ERROR: JWT secret must be at least 32 characters
   ```
   Solution: Use `just generate-jwt-secret`

3. **Redis Connection Failed**
   ```bash
   ERROR: Could not connect to Redis
   ```
   Solution: Ensure Redis service is running

### Debug Mode

Enable debug mode for troubleshooting:

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

## Next Steps

1. Complete [GitHub OAuth Setup](github-oauth.md)
2. Generate secrets with provided commands
3. Start services with `just up`