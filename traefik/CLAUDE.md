# 🔥 CLAUDE.md - The Traefik Service Divine Scripture! ⚡

**🛡️ Behold! The Sacred Reverse Proxy - Divine Router of All Requests! 🛡️**

**⚡ This is Traefik - The Holy Gateway Guardian and Traffic Controller! ⚡**

## 🔱 The Sacred Purpose of Traefik - Divine Routing Supremacy!

**Traefik is the blessed edge router, the first defender, the divine traffic orchestrator!**

This sacred service commands these divine powers:
- **Reverse Proxy Mastery** - Routes all HTTP(S) traffic with divine wisdom!
- **TLS Termination** - Let's Encrypt certificates through ACME blessing!
- **ForwardAuth Guardian** - Enforces authentication with holy middleware!
- **Service Discovery** - Docker labels guide its divine routing decisions!
- **Load Balancing** - Distributes requests with righteous fairness!

**⚡ Traefik is the ONLY component that knows ALL routing paths! ⚡**

## 🏗️ The Sacred Architecture - First Line of Divine Defense!

```
Traefik (Ports 80, 443, 8080)
├── Entrypoints (Divine Gateways!)
│   ├── web (80) - HTTP gateway, redirects to HTTPS!
│   ├── websecure (443) - HTTPS sanctuary of encryption!
│   └── traefik (8080) - Dashboard altar (dev only)!
├── Routers (Sacred Path Matchers!)
│   ├── Priority-based routing (10→4→3→2→1)
│   ├── Host and PathPrefix divine combinations!
│   └── Middleware chains of blessed transformation!
├── Middlewares (Divine Request Transformers!)
│   ├── ForwardAuth - Authentication enforcement!
│   ├── Headers - Custom header injection!
│   └── RedirectScheme - HTTPS enforcement!
└── Services (Backend Destinations!)
    ├── auth@docker - Auth service endpoint!
    └── mcp-*@docker - MCP service endpoints!
```

**⚡ Traefik sees all, routes all, protects all! ⚡**

## 🐳 The Docker Manifestation - Container of Edge Glory!

### The Sacred docker-compose.yml Configuration
```yaml
services:
  traefik:
    image: traefik:v3.0  # The blessed version!
    ports:
      - "80:80"      # HTTP gateway
      - "443:443"    # HTTPS sanctuary
      - "8080:8080"  # Dashboard (dev only)
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro  # Docker discovery!
      - traefik-certificates:/letsencrypt  # TLS certificate storage!
    networks:
      - public  # The sacred network of service communion!
    labels:
      - "traefik.enable=true"  # Self-awareness blessing!
```

**⚡ Traefik discovers services through Docker labels - divine service mesh! ⚡**

## 🔧 The Sacred Configuration - Static and Dynamic Harmony!

### Static Configuration (Command Arguments!)
```yaml
command:

  # Docker Provider
  - "--providers.docker=true"
  - "--providers.docker.exposedbydefault=false"
  - "--providers.docker.network=public"

  # Entrypoints
  - "--entrypoints.web.address=:80"
  - "--entrypoints.websecure.address=:443"

  # Let's Encrypt
  - "--certificatesresolvers.le.acme.email=admin@${BASE_DOMAIN}"
  - "--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json"
  - "--certificatesresolvers.le.acme.tlschallenge=true"

  # Logging
  - "--log.level=INFO"
  - "--accesslog=true"
```

### Dynamic Configuration (Docker Labels!)

**Service labels guide Traefik's routing decisions!**

## 🚦 The Sacred Priority System - Divine Routing Hierarchy!

**⚡ CRITICAL: Without priorities, catch-all routes devour everything! ⚡**

```yaml
# Priority 10 - OAuth Discovery (Highest Divine Priority!)
- "traefik.http.routers.oauth-discovery.priority=10"
- "traefik.http.routers.oauth-discovery.rule=PathPrefix(`/.well-known/oauth-authorization-server`)"

# Priority 4 - OAuth Routes (Sacred Authentication Paths!)
- "traefik.http.routers.auth-oauth.priority=4"
- "traefik.http.routers.auth-oauth.rule=PathPrefix(`/register`) || PathPrefix(`/authorize`) || ..."

# Priority 3 - Auth Verification (Internal Sacred Chamber!)
- "traefik.http.routers.auth-verify.priority=3"
- "traefik.http.routers.auth-verify.rule=PathPrefix(`/verify`)"

# Priority 2 - MCP Routes (Protected Service Paths!)
- "traefik.http.routers.mcp-service.priority=2"
- "traefik.http.routers.mcp-service.rule=Host(`service.${BASE_DOMAIN}`)"

# Priority 1 - Catch-all (Lowest Priority Trap!)
- "traefik.http.routers.catchall.priority=1"
- "traefik.http.routers.catchall.rule=HostRegexp(`{host:.+}`)"
```

**⚡ Order matters! Higher numbers match first! ⚡**

## 🔐 The ForwardAuth Middleware - Divine Authentication Guardian!

### The Sacred ForwardAuth Flow

```yaml
# Middleware Definition
- "traefik.http.middlewares.mcp-auth.forwardauth.address=http://auth:8000/verify"
- "traefik.http.middlewares.mcp-auth.forwardauth.authResponseHeaders=X-User-Id,X-User-Name,X-Auth-Token"
- "traefik.http.middlewares.mcp-auth.forwardauth.trustForwardHeader=true"
```

**The Divine Flow:**
1. **Request arrives** at protected endpoint!
2. **Traefik intercepts** before reaching service!
3. **Forwards to auth** service /verify endpoint!
4. **Auth validates** Bearer token from header!
5. **Success (200)** - Request proceeds with user headers!
6. **Failure (401)** - Client receives unauthorized response!

**⚡ Every MCP route MUST have ForwardAuth middleware! ⚡**

## 🌐 The Host-Based Routing - Subdomain Divine Order!

Each service gets its blessed subdomain:
- `auth.${BASE_DOMAIN}` - Auth service altar!
- `mcp-fetch.${BASE_DOMAIN}` - Fetch service sanctuary!
- `mcp-*.${BASE_DOMAIN}` - Pattern for all MCP services!

**The Sacred Routing Labels:**
```yaml
# Host-based routing with divine precision
- "traefik.http.routers.service-name.rule=Host(`service.${BASE_DOMAIN}`)"

# Multiple hosts for the same service
- "traefik.http.routers.service-name.rule=Host(`service.${BASE_DOMAIN}`) || Host(`alias.${BASE_DOMAIN}`)"

# Path-based routing for specific endpoints
- "traefik.http.routers.service-api.rule=Host(`service.${BASE_DOMAIN}`) && PathPrefix(`/api`)"
```

## 🛡️ The TLS Configuration - HTTPS Divine Encryption!

### Let's Encrypt Automatic Certificates

```yaml
# Router-level TLS configuration
- "traefik.http.routers.service-name.tls=true"
- "traefik.http.routers.service-name.tls.certresolver=le"

# Wildcard certificates (requires DNS challenge)
- "traefik.http.routers.service-name.tls.domains[0].main=${BASE_DOMAIN}"
- "traefik.http.routers.service-name.tls.domains[0].sans=*.${BASE_DOMAIN}"
```

### HTTPS Redirect Middleware

```yaml
# Global HTTP to HTTPS redirect
- "traefik.http.routers.http-catchall.rule=HostRegexp(`{host:.+}`)"
- "traefik.http.routers.http-catchall.entrypoints=web"
- "traefik.http.routers.http-catchall.middlewares=redirect-to-https"
- "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https"
```

## 🔥 Common Issues and Divine Solutions!

### "404 Page Not Found" - Routing Confusion!
- Check router priorities - catch-all eating requests?
- Verify Host rule matches actual domain!
- Ensure service has `traefik.enable=true`!
- Check service is on `public` network!

### "502 Bad Gateway" - Backend Unreachable!
- Verify backend service is running!
- Check port configuration in service labels!
- Ensure services share the `public` network!
- Review health check status!

### "SSL Certificate Error" - TLS Troubles!
- Check Let's Encrypt rate limits!
- Verify domain DNS points to server!
- Review acme.json permissions (600)!
- Check email in certresolver config!

### "Middleware Not Working" - Chain Broken!
- Verify middleware is attached to router!
- Check middleware definition syntax!
- Ensure auth service is reachable!
- Review ForwardAuth response codes!

## 📊 The Sacred Monitoring - Dashboard of Divine Insight!

Access the Traefik dashboard at `http://localhost:8080` (dev only!):

- **Routers Tab** - See all routing rules and priorities!
- **Services Tab** - Monitor backend health status!
- **Middlewares Tab** - Verify authentication chains!
- **Metrics** - Request rates and error counts!

**⚡ Dashboard is dev-only! Disable in production! ⚡**

## 🎯 The Divine Mission - Traefik Responsibilities!

**What Traefik MUST Do:**
- Route ALL external requests to correct services!
- Enforce HTTPS with automatic certificates!
- Apply ForwardAuth to protected endpoints!
- Respect routing priorities religiously!
- Load balance across service instances!

**What Traefik MUST NOT Do:**
- Implement business logic!
- Store application state!
- Modify request/response bodies!
- Make authentication decisions (delegates to auth)!
- Know about MCP protocol details!

**⚡ Traefik routes and protects - nothing more, nothing less! ⚡**

## 🛠️ Debugging Commands - Divine Troubleshooting!

```bash
# View Traefik logs
just logs traefik

# Check routing configuration
curl http://localhost:8080/api/http/routers

# Test specific route
curl -H "Host: service.domain.com" http://localhost

# Verify TLS certificates
openssl s_client -connect domain.com:443 -servername domain.com

# Check ForwardAuth flow
curl -v -H "Authorization: Bearer $TOKEN" https://service.domain.com/endpoint
```

## 🔱 The Sacred Best Practices!

1. **Always set priorities** - Prevent catch-all chaos!
2. **Use specific rules** - Host + Path > Host alone!
3. **Chain middlewares wisely** - Order matters!
4. **Monitor the dashboard** - Early problem detection!
5. **Backup acme.json** - Preserve certificates!
6. **Review access logs** - Security monitoring!
7. **Test routing locally** - Before production!

## 📜 The Sacred Label Reference - Quick Divine Lookup!

```yaml
# Enable Traefik processing
- "traefik.enable=true"

# Define HTTP router
- "traefik.http.routers.NAME.rule=RULE"
- "traefik.http.routers.NAME.priority=NUMBER"
- "traefik.http.routers.NAME.entrypoints=websecure"
- "traefik.http.routers.NAME.middlewares=MIDDLEWARE"
- "traefik.http.routers.NAME.service=SERVICE"
- "traefik.http.routers.NAME.tls=true"
- "traefik.http.routers.NAME.tls.certresolver=le"

# Define service
- "traefik.http.services.NAME.loadbalancer.server.port=PORT"

# Define middleware
- "traefik.http.middlewares.NAME.forwardauth.address=URL"
- "traefik.http.middlewares.NAME.headers.customrequestheaders.NAME=VALUE"
```

**⚡ Master these labels to command Traefik's power! ⚡**

---

**🔥 May your routes be swift, your certificates valid, and your traffic forever secure! ⚡**
