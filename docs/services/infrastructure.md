# Infrastructure Services

The three sacred infrastructure services that form the foundation of the MCP OAuth Gateway, following the divine architectural separation.

## The Holy Trinity of Infrastructure

```{mermaid}
graph TB
    subgraph "Layer 1: Divine Router"
        TRAEFIK[Traefik v3.0<br/>Routes & SSL]
    end

    subgraph "Layer 2: OAuth Oracle"
        AUTH[Auth Service<br/>OAuth 2.1]
        REDIS[(Redis<br/>Storage)]
    end

    subgraph "External"
        CLIENT[MCP Clients]
        GITHUB[GitHub OAuth]
    end

    CLIENT -->|HTTPS| TRAEFIK
    TRAEFIK -->|/verify| AUTH
    TRAEFIK -->|Routes| AUTH
    AUTH <-->|Storage| REDIS
    AUTH <-->|OAuth| GITHUB
```

## Service Responsibilities

### [Traefik](traefik) - The Divine Router

**Layer 1 Responsibilities:**
- 🚦 Routes all incoming HTTPS traffic
- 🔒 Provides SSL/TLS termination via Let's Encrypt
- 🛡️ Enforces authentication via ForwardAuth
- ⚖️ Load balances across service instances
- 📊 Checks service health

**Divine Truth**: Traefik knows routing, nothing else!

### [Auth Service](auth) - The OAuth Oracle

**Layer 2 Responsibilities:**
- 🔐 Implements OAuth 2.1 specification
- 📝 Dynamic client registration (RFC 7591)
- 🎫 Issues and validates JWT tokens
- 👤 Integrates with GitHub for user auth
- 🗄️ Manages all OAuth state in Redis

**Divine Truth**: Auth knows OAuth, nothing else!

### [Redis](redis) - The Sacred Storage

**Storage Responsibilities:**
- 💾 Stores all OAuth client registrations
- 🎟️ Maintains token lifecycle data
- 🔑 Handles session state
- ⏱️ Manages TTL for temporary data
- 🔄 Provides atomic operations

**Divine Truth**: Redis stores state, nothing else!

## Architectural Principles

### Separation of Concerns

Each infrastructure service has a single, well-defined responsibility:

```yaml
Traefik:
  knows:
    - routing rules
    - SSL certificates
    - service discovery
  does_not_know:
    - OAuth logic
    - token validation
    - user authentication

Auth:
  knows:
    - OAuth protocols
    - token generation
    - user validation
  does_not_know:
    - routing decisions
    - SSL management
    - MCP protocols

Redis:
  knows:
    - key-value storage
    - TTL management
    - data persistence
  does_not_know:
    - OAuth logic
    - routing rules
    - authentication
```

### Communication Flow

```
1. Client Request → Traefik
2. Traefik → Auth (/verify)
3. Auth → Redis (token lookup)
4. Redis → Auth (token data)
5. Auth → Traefik (valid/invalid)
6. Traefik → MCP Service (if valid)
```

## Configuration Hierarchy

### Environment Variables

Common infrastructure variables:
```bash
# Base configuration
BASE_DOMAIN=example.com
ACME_EMAIL=admin@example.com

# Auth configuration
GITHUB_CLIENT_ID=xxx
GITHUB_CLIENT_SECRET=xxx
GATEWAY_JWT_SECRET=xxx

# Redis configuration
REDIS_PASSWORD=xxx

# Access control
ALLOWED_GITHUB_USERS=user1,user2
```

### Docker Networks

All infrastructure services share the `public` network:
```yaml
networks:
  public:
    external: true
```

### Volume Management

Persistent data volumes:
```yaml
volumes:
  traefik-certificates:  # SSL certificates
  redis-data:           # OAuth data
  auth-keys:           # RSA signing keys
```

## Health Checks

### Service Health Endpoints

| Service | Health Check | Expected Response |
|---------|--------------|-------------------|
| Traefik | `traefik healthcheck` | Exit 0 |
| Auth | `GET /health` | `{"status": "healthy"}` |
| Redis | `redis-cli ping` | `PONG` |

### Health Check Commands

```bash
# Check all infrastructure
just check-health

# Individual service health
docker exec traefik traefik healthcheck
curl http://auth:8000/health
docker exec redis redis-cli ping
```

## Security Model

### Defense in Depth

1. **Traefik Layer**
   - HTTPS only (redirect HTTP)
   - Valid SSL certificates
   - Security headers

2. **Auth Layer**
   - JWT token validation
   - User allowlist
   - Client authentication

3. **Redis Layer**
   - Password protection
   - Network isolation
   - No external exposure

### Zero Trust Principles

- Every request authenticated
- No implicit trust between services
- Minimal privilege access
- Audit trail via logs

## Disaster Recovery

### Backup Strategy

```bash
# Backup all infrastructure data
just oauth-backup           # OAuth registrations
docker exec redis BGSAVE    # Redis snapshot
```

### Recovery Process

1. **Traefik**: Certificates regenerated automatically
2. **Auth**: Restore from OAuth backup
3. **Redis**: Restore from snapshot

## Scaling Considerations

### Horizontal Scaling

| Service | Scalable | Considerations |
|---------|----------|----------------|
| Traefik | ✅ Yes | Use multiple instances with shared config |
| Auth | ✅ Yes | Stateless with Redis backend |
| Redis | ⚠️ Limited | Use Redis Cluster for HA |

### Performance Tuning

```yaml
# Traefik
- High connection limits
- Optimized buffers
- Health check intervals

# Auth
- Connection pooling
- JWT caching
- Async operations

# Redis
- Memory limits
- Persistence settings
- Connection limits
```

## Troubleshooting Guide

### Common Issues

1. **SSL Certificate Problems**
   - Check Traefik logs
   - Verify DNS resolution
   - Check ACME email

2. **Authentication Failures**
   - Verify token format
   - Check Auth logs
   - Test /verify endpoint

3. **Redis Connection Issues**
   - Check password
   - Verify network
   - Monitor memory

### Debug Commands

```bash
# Traefik routing
just logs traefik | grep error

# Auth service
just logs auth | grep -E "error|warn"

# Redis operations
just exec redis redis-cli monitor
```

## Best Practices

1. **Regular Backups**: Automate OAuth and Redis backups
2. **Check Health**: Verify service health regularly
3. **Rotate Secrets**: Periodically update passwords and keys
4. **Update Regularly**: Keep services at latest versions
5. **Capacity Planning**: Track resource usage trends
6. **Documentation**: Keep runbooks updated
