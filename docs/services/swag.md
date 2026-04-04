# SWAG Service

SWAG (Secure Web Application Gateway) by LinuxServer.io is the reverse proxy that routes all
requests, enforces OAuth authentication via nginx `auth_request`, and handles SSL termination for
the gateway.

## Overview

SWAG bundles nginx + certbot (Let's Encrypt) into a single container with automatic certificate
renewal. For this gateway it replaces Traefik as the routing and authentication enforcement layer.

Responsibilities:
- Reverse proxy for all MCP services and the auth service
- Automatic SSL/TLS via built-in certbot (Let's Encrypt or ZeroSSL)
- `auth_request`-based ForwardAuth enforcing OAuth tokens on MCP endpoints
- Unauthenticated passthrough for OAuth discovery and token endpoints
- DNS rebinding protection and CORS headers

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  SWAG (nginx + certbot)              │
│                                                     │
│  *.subdomain.conf per MCP service                   │
│  ┌─────────────────────────────────────────────┐   │
│  │  location /_oauth_verify  (internal)        │   │
│  │    → proxy to auth:8000/verify              │   │
│  │                                             │   │
│  │  location /mcp            (protected)       │   │
│  │    auth_request /_oauth_verify              │   │
│  │    → proxy to MCP service                   │   │
│  │                                             │   │
│  │  location /register|/authorize|/token …    │   │
│  │    (no auth) → proxy to auth:8000           │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
            ↕ mcp-net (internal Docker network)
┌──────────┐    ┌────────────────┐    ┌─────────────┐
│ auth:8000│    │ mcp-service:N  │    │  (other MCP)│
└──────────┘    └────────────────┘    └─────────────┘
```

## Docker Compose Configuration

Reference file: `swag/docker-compose.yaml`

```yaml
services:
  swag:
    image: lscr.io/linuxserver/swag
    container_name: swag
    cap_add:
      - NET_ADMIN
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=${TZ:-UTC}
      - URL=${SWAG_URL}                                    # Base domain, e.g. example.com
      - SUBDOMAINS=${SWAG_SUBDOMAINS:-www,}                # Comma-separated subdomains to cert
      - VALIDATION=${SWAG_VALIDATION:-http}                # http or dns
      - CERTPROVIDER=${SWAG_CERTPROVIDER:-}                # blank = Let's Encrypt, zerossl = ZeroSSL
      - DNSPLUGIN=${SWAG_DNSPLUGIN:-cloudflare}            # DNS plugin when VALIDATION=dns
      - EMAIL=${SWAG_EMAIL:-}                              # Let's Encrypt account email
      - ONLY_SUBDOMAINS=${SWAG_ONLY_SUBDOMAINS:-false}     # true = cert only subdomains, not base URL
      - EXTRA_DOMAINS=${SWAG_EXTRA_DOMAINS:-}              # Additional domains beyond URL+SUBDOMAINS
      - STAGING=${SWAG_STAGING:-false}                     # true = use Let's Encrypt staging
    volumes:
      - ${SWAG_CONFIG_PATH:-./config}:/config
      # Bind-mount proxy-confs so gateway nginx configs are picked up automatically
      - ${SWAG_PROXY_CONFS_PATH:-./proxy-confs}:/config/nginx/proxy-confs
    ports:
      - "443:443"
      - "80:80"
    networks:
      - mcp-net    # Internal — allows SWAG to reach auth:8000 and MCP services
      - jakenet    # Broader homelab connectivity
    restart: unless-stopped

networks:
  mcp-net:
    name: ${MCP_NETWORK:-mcp-oauth}
    external: true
  jakenet:
    external: true
```

### Key Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SWAG_URL` | Yes | Base domain (e.g. `example.com`) |
| `SWAG_SUBDOMAINS` | Yes | Comma-separated subdomains to include in the cert |
| `SWAG_VALIDATION` | Yes | Challenge type: `http` or `dns` |
| `SWAG_EMAIL` | Recommended | Email for Let's Encrypt account |
| `SWAG_STAGING` | No | Set `true` to test against LE staging before going live |
| `SWAG_ONLY_SUBDOMAINS` | No | `true` to exclude the apex domain from the cert |
| `SWAG_DNSPLUGIN` | Conditional | Required when `VALIDATION=dns` (e.g. `cloudflare`) |

## nginx Proxy-Conf Structure

SWAG reads all `*.conf` files inside `/config/nginx/proxy-confs/`. Each MCP service gets its own
`<service>.subdomain.conf` file.

The gateway ships a template at `mcp-template.subdomain.conf` that must be copied and customized
per service.

```
/config/nginx/proxy-confs/
├── auth.subdomain.conf          # Auth service (mcp-oauth)
├── mcp-fetch.subdomain.conf     # mcp-fetch MCP service
├── mcp-memory.subdomain.conf    # mcp-memory MCP service
└── ...                          # one file per subdomain/service
```

### Template Placeholders

When creating a new conf from `mcp-template.subdomain.conf`, replace these placeholders:

| Placeholder | Example | Description |
|---|---|---|
| `{{SERVICE_NAME}}` | `axon` | Used in nginx server_name and comments |
| `{{DOMAIN}}` | `axon.example.com` | Full subdomain FQDN |
| `{{UPSTREAM_IP}}` | `100.75.111.118` | IP of the upstream host (Tailscale or LAN) |
| `{{UPSTREAM_PORT}}` | `3002` | Port the MCP service listens on |
| `{{AUTH_DOMAIN}}` | `mcp-auth.example.com` | Domain of the auth service for metadata responses |

## auth_request ForwardAuth Pattern

Authentication enforcement is done via nginx's `auth_request` module. An internal-only location
proxies each request's Authorization header to the auth service, which returns 200 (valid) or
401/403 (invalid).

### Internal Verification Location

```nginx
location = /_oauth_verify {
    internal;
    include /config/nginx/resolver.conf;
    proxy_pass http://mcp-oauth:8000/verify;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Original-URI $request_uri;
    proxy_set_header X-Original-Method $request_method;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Authorization $http_authorization;
}
```

The `internal` directive ensures this location is only reachable via `auth_request`, not by
external clients.

### Applying auth_request to a Location

```nginx
location /mcp {
    auth_request /_oauth_verify;
    auth_request_set $auth_status $upstream_status;
    # ... proxy_pass to upstream
}
```

If `/_oauth_verify` returns a non-2xx status, nginx rejects the request with 401/403 before the
upstream ever sees it.

## OAuth Endpoint Routing (Unauthenticated)

OAuth discovery, registration, and token exchange endpoints must be reachable without a token.
These locations proxy directly to `auth:8000` with no `auth_request`.

```nginx
# RFC 8414 discovery
location = /.well-known/oauth-authorization-server {
    include /config/nginx/resolver.conf;
    include /config/nginx/proxy.conf;
    add_header Cache-Control "public, max-age=3600" always;
    proxy_pass http://mcp-oauth:8000;
}

location = /.well-known/openid-configuration {
    include /config/nginx/resolver.conf;
    include /config/nginx/proxy.conf;
    add_header Cache-Control "public, max-age=3600" always;
    proxy_pass http://mcp-oauth:8000;
}

location = /jwks {
    include /config/nginx/resolver.conf;
    include /config/nginx/proxy.conf;
    add_header Cache-Control "public, max-age=3600" always;
    proxy_pass http://mcp-oauth:8000;
}

# RFC 7591 dynamic client registration
location = /register {
    include /config/nginx/resolver.conf;
    include /config/nginx/proxy.conf;
    add_header Cache-Control "no-store" always;
    proxy_pass http://mcp-oauth:8000;
}

location = /authorize {
    include /config/nginx/resolver.conf;
    include /config/nginx/proxy.conf;
    proxy_pass http://mcp-oauth:8000;
}

location = /token {
    include /config/nginx/resolver.conf;
    include /config/nginx/proxy.conf;
    add_header Cache-Control "no-store" always;
    proxy_pass http://mcp-oauth:8000;
}

location = /revoke {
    include /config/nginx/resolver.conf;
    include /config/nginx/proxy.conf;
    add_header Cache-Control "no-store" always;
    proxy_pass http://mcp-oauth:8000;
}

location = /callback {
    include /config/nginx/resolver.conf;
    include /config/nginx/proxy.conf;
    proxy_pass http://mcp-oauth:8000;
}
```

The `/.well-known/oauth-protected-resource` location is served inline (no upstream proxy) and
returns a static JSON response pointing to the auth server.

## MCP Endpoint Routing (Auth-Protected)

The `/mcp` location enforces authentication and forwards MCP-specific headers:

```nginx
location /mcp {
    # DNS rebinding check
    if ($origin_valid = 0) {
        add_header Content-Type "application/json" always;
        return 403 '{"error": "origin_not_allowed", "message": "Origin header validation failed"}';
    }

    auth_request /_oauth_verify;
    auth_request_set $auth_status $upstream_status;

    include /config/nginx/resolver.conf;
    include /config/nginx/mcp.conf;

    # Streaming support
    proxy_max_temp_file_size 0;
    chunked_transfer_encoding on;
    proxy_set_header Connection '';

    # MCP protocol headers forwarded to upstream
    proxy_set_header MCP-Protocol-Version $http_mcp_protocol_version;
    proxy_set_header Mcp-Session-Id $http_mcp_session_id;
    proxy_set_header Accept $http_accept;

    # Long timeouts for streaming MCP sessions
    proxy_connect_timeout 240s;
    proxy_send_timeout 86400s;
    proxy_read_timeout 86400s;

    proxy_pass $mcp_upstream_proto://$mcp_upstream_app:$mcp_upstream_port;
}
```

## CORS Headers Pattern

CORS is applied on the `/mcp` location to allow Claude.ai and Anthropic proxy origins.

```nginx
add_header Access-Control-Allow-Origin $http_origin always;
add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, MCP-Protocol-Version, Mcp-Session-Id, Last-Event-ID" always;
add_header Access-Control-Allow-Credentials "true" always;
add_header Access-Control-Max-Age "3600" always;

# Preflight
if ($request_method = 'OPTIONS') {
    add_header Access-Control-Allow-Origin $http_origin always;
    add_header Access-Control-Allow-Methods "GET, POST, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, MCP-Protocol-Version, Mcp-Session-Id, Last-Event-ID" always;
    add_header Access-Control-Allow-Credentials "true" always;
    add_header Access-Control-Max-Age "3600" always;
    add_header Content-Length 0;
    return 204;
}
```

The DNS rebinding protection block validates `$http_origin` against a whitelist before CORS
headers are applied:

```nginx
set $origin_valid 0;
if ($http_origin = "")                              { set $origin_valid 1; }
if ($http_origin = "https://$server_name")          { set $origin_valid 1; }
if ($http_origin ~ "^https://localhost(:[0-9]+)?$") { set $origin_valid 1; }
if ($http_origin ~ "^https://(.*\.)?anthropic\.com$") { set $origin_valid 1; }
if ($http_origin ~ "^https://(.*\.)?claude\.ai$")    { set $origin_valid 1; }
```

## TLS / Certificate Handling

SWAG's built-in certbot handles certificate issuance and renewal automatically.

- Certificates are stored under `/config/etc/letsencrypt/` inside the container.
- The `SWAG_CONFIG_PATH` volume persists certificates across container restarts.
- Renewal runs automatically via a cron job inside the container; no external cron needed.
- HTTP validation (`VALIDATION=http`) requires port 80 to be accessible from the internet.
- DNS validation (`VALIDATION=dns`) works behind firewalls; requires a supported DNS plugin
  (e.g. `cloudflare`) and API credentials mounted at `/config/dns-conf/`.

Nginx is configured to use the certificates via SWAG's shared `/config/nginx/ssl.conf` include,
which every subdomain conf references:

```nginx
include /config/nginx/ssl.conf;
```

## JSON Error Responses

The template defines named error locations that return machine-readable JSON bodies, which is
required by the MCP and OAuth specs:

```nginx
error_page 401 @error_401;
location @error_401 {
    internal;
    add_header Content-Type "application/json" always;
    add_header WWW-Authenticate 'Bearer resource_metadata="https://$server_name/.well-known/oauth-protected-resource", scope="mcp:read mcp:write"' always;
    return 401 '{"error": "unauthorized", "message": "Valid authorization token required"}';
}

error_page 403 @error_403;
location @error_403 {
    internal;
    add_header Content-Type "application/json" always;
    return 403 '{"error": "forbidden", "message": "Insufficient permissions or origin not allowed"}';
}
```

## Troubleshooting

### Checking nginx Logs

```bash
# Access log (all requests)
docker exec swag tail -f /config/log/nginx/access.log

# Error log (nginx errors and upstream failures)
docker exec swag tail -f /config/log/nginx/error.log

# SWAG container log (certbot renewal, startup)
docker logs -f swag
```

### Testing a Conf File

```bash
# Validate nginx config without reloading
docker exec swag nginx -t

# Reload nginx after editing a conf (no downtime)
docker exec swag nginx -s reload
```

### Common Errors

| Symptom | Likely Cause | Fix |
|---|---|---|
| `502 Bad Gateway` on `/mcp` | Upstream container not running or wrong IP/port | Check `{{UPSTREAM_IP}}:{{UPSTREAM_PORT}}` is reachable from the SWAG container |
| `401` on `/mcp` even with valid token | `/_oauth_verify` can't reach `auth:8000` | Verify both SWAG and auth are on `mcp-net` |
| `403 origin_not_allowed` | Origin not in whitelist | Add origin to `$origin_valid` block in conf |
| `502` on `/register` or `/token` | Auth service is down | `docker logs auth` and check health |
| Certificate not renewing | Port 80 blocked (HTTP validation) | Open port 80 or switch to DNS validation |
| nginx fails to start | Syntax error in a conf file | Run `docker exec swag nginx -t` to identify the file |
| `upstream sent invalid header` | Upstream is returning SSE but nginx buffers it | Ensure `mcp.conf` include is present; check `proxy_buffering off` |

### Testing auth_request Directly

```bash
# Test the verify endpoint with a valid token
curl -i http://localhost:8000/verify \
  -H "Authorization: Bearer $TOKEN"

# Should return 200 with X-User-Id, X-User-Name headers on success
# Should return 401 for missing/expired tokens
```

### Listing Active Certificates

```bash
docker exec swag certbot certificates
```

## Reference

- Template file: `mcp-template.subdomain.conf`
- Docker Compose: `swag/docker-compose.yaml`
- LinuxServer SWAG docs: https://docs.linuxserver.io/general/swag
- nginx auth_request module: https://nginx.org/en/docs/http/ngx_http_auth_request_module.html
