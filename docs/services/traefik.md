# Traefik Service

Traefik serves as the reverse proxy and edge router for the MCP OAuth Gateway, handling all incoming requests, SSL termination, and authentication enforcement.

## Overview

Traefik provides:
- Reverse proxy for all services
- Automatic SSL/TLS with Let's Encrypt
- Authentication enforcement via ForwardAuth
- Service discovery through Docker labels
- Request routing with priority system

## Architecture

The service uses:
- **Version**: Traefik v3.0
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Discovery**: Docker provider with labels
- **SSL**: Let's Encrypt with HTTP challenge

## Configuration

### Environment Variables

```bash
# Domain Configuration (REQUIRED)
BASE_DOMAIN=gateway.yourdomain.com
ACME_EMAIL=admin@yourdomain.com
```

### Docker Compose

```yaml
traefik:
  image: traefik:v3.0
  container_name: traefik
  restart: unless-stopped
  networks:
    - public
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - traefik-certificates:/certificates
  command:
    - "--providers.docker=true"
    - "--providers.docker.exposedbydefault=false"
    - "--entrypoints.web.address=:80"
    - "--entrypoints.websecure.address=:443"
    - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
    - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
```

## Routing System

### Priority-Based Routing

Traefik uses priorities to ensure correct request handling:

```yaml
# Priority 10 - OAuth Discovery (Highest)
PathPrefix(`/.well-known/oauth-authorization-server`)

# Priority 4 - OAuth Routes
PathPrefix(`/register`) || PathPrefix(`/authorize`) || PathPrefix(`/token`)

# Priority 3 - Internal Routes
PathPrefix(`/verify`)

# Priority 2 - MCP Routes with Auth
Host(`service.domain.com`) && PathPrefix(`/mcp`)

# Priority 1 - Catch-all (Lowest)
Host(`service.domain.com`)
```

### Service Configuration

Each service configures routing via Docker labels:

```yaml
labels:
  # Enable Traefik processing
  - "traefik.enable=true"
  
  # Define service port
  - "traefik.http.services.service-name.loadbalancer.server.port=3000"
  
  # Configure routing
  - "traefik.http.routers.service-name.rule=Host(`service.${BASE_DOMAIN}`)"
  - "traefik.http.routers.service-name.priority=2"
  - "traefik.http.routers.service-name.entrypoints=websecure"
  - "traefik.http.routers.service-name.tls.certresolver=letsencrypt"
  
  # Apply authentication
  - "traefik.http.routers.service-name.middlewares=mcp-auth@docker"
```

## Middleware

### ForwardAuth Middleware

Enforces authentication for protected routes:

```yaml
# Define middleware
- "traefik.http.middlewares.mcp-auth.forwardauth.address=http://auth:8000/verify"
- "traefik.http.middlewares.mcp-auth.forwardauth.authResponseHeaders=X-User-Id,X-User-Name,X-Auth-Token"
- "traefik.http.middlewares.mcp-auth.forwardauth.trustForwardHeader=true"

# Apply to routes
- "traefik.http.routers.service.middlewares=mcp-auth@docker"
```

Flow:
1. Request arrives at protected endpoint
2. Traefik calls auth service `/verify`
3. Auth validates Bearer token
4. Success: Request forwarded with user headers
5. Failure: 401 Unauthorized returned

### HTTPS Redirect

Global redirect from HTTP to HTTPS:

```yaml
# HTTP to HTTPS redirect middleware
- "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https"
- "traefik.http.middlewares.redirect-to-https.redirectscheme.permanent=true"

# Global catch-all router
- "traefik.http.routers.http-catchall.rule=hostregexp(`{host:.+}`)"
- "traefik.http.routers.http-catchall.entrypoints=web"
- "traefik.http.routers.http-catchall.middlewares=redirect-to-https"
```

### CORS Middleware

Handles cross-origin requests:

```yaml
# CORS configuration
- "traefik.http.middlewares.mcp-cors.headers.accesscontrolallowmethods=GET,OPTIONS,PUT,POST,DELETE,PATCH"
- "traefik.http.middlewares.mcp-cors.headers.accesscontrolallowheaders=*"
- "traefik.http.middlewares.mcp-cors.headers.accesscontrolalloworiginlist=https://claude.ai"
- "traefik.http.middlewares.mcp-cors.headers.accesscontrolmaxage=100"
- "traefik.http.middlewares.mcp-cors.headers.accesscontrolallowcredentials=true"
```

## SSL/TLS Configuration

### Let's Encrypt Integration

Automatic certificate generation and renewal:

```yaml
command:
  # ACME configuration
  - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
  - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
  - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
  - "--certificatesresolvers.letsencrypt.acme.storage=/certificates/acme.json"

# Router configuration
labels:
  - "traefik.http.routers.service.tls=true"
  - "traefik.http.routers.service.tls.certresolver=letsencrypt"
```

### Certificate Storage

Certificates stored in Docker volume:
- Volume: `traefik-certificates`
- File: `/certificates/acme.json`
- Permissions: 600 (important!)

## Monitoring

### Health Check

```yaml
command:
  - "--ping=true"

healthcheck:
  test: ["CMD", "traefik", "healthcheck", "--ping"]
  interval: 10s
  timeout: 5s
  retries: 5
```

### Access Logs

```yaml
command:
  - "--accesslog=true"
  - "--log.level=INFO"
```

### Dashboard (Development Only)

```yaml
command:
  - "--api.insecure=true"  # Enables dashboard on port 8080
```

Access at: `http://localhost:8080`

## Operations

### Starting Traefik

```bash
# Start Traefik only
just up traefik

# View logs
just logs traefik

# Check SSL certificates
just check-ssl
```

### Common Tasks

```bash
# View routing configuration
curl http://localhost:8080/api/http/routers | jq

# Check service health
curl http://localhost:8080/api/http/services | jq

# Monitor access logs
just logs -f traefik | grep -v "GET /ping"
```

## Troubleshooting

### Common Issues

#### 404 Page Not Found
- Check router priorities
- Verify Host rule matches domain
- Ensure service has `traefik.enable=true`
- Check service is on correct network

#### 502 Bad Gateway
- Service not running or unhealthy
- Wrong port in service configuration
- Network connectivity issue
- Service not on `public` network

#### SSL Certificate Errors
- Check DNS points to server
- Verify ACME email is valid
- Check rate limits (5 certs/week/domain)
- Review acme.json permissions

#### Authentication Issues
- Auth service not reachable
- ForwardAuth middleware misconfigured
- Invalid Bearer token
- User not in allowed list

### Debugging

```bash
# Enable debug logging
docker exec traefik sed -i 's/--log.level=INFO/--log.level=DEBUG/g' /etc/traefik/traefik.yml

# Check specific route
curl -H "Host: service.domain.com" http://localhost/test

# View certificate details
docker exec traefik cat /certificates/acme.json | jq '.letsencrypt.Certificates'

# Test ForwardAuth
curl -v -H "Authorization: Bearer $TOKEN" https://service.domain.com/mcp
```

## Best Practices

1. **Always Set Priorities** - Prevent catch-all confusion
2. **Use Specific Rules** - Combine Host + Path when possible
3. **Monitor Logs** - Watch for routing issues
4. **Backup Certificates** - Save acme.json regularly
5. **Test Locally** - Use Host header to test routing
6. **Health Checks** - Ensure services are ready
7. **Network Isolation** - Keep internal services off public network

## Architecture Notes

- Stateless design (state in acme.json only)
- Service discovery via Docker API
- Dynamic configuration through labels
- No hardcoded routes
- Single instance sufficient

## Related Documentation

- [Components](../architecture/components.md) - System architecture
- [Security](../architecture/security.md) - Security details
- [Monitoring](../usage/monitoring.md) - Monitoring guide