# Proxy-Agnostic Routing: Service Registry Architecture

The gateway currently delegates all routing to SWAG/nginx via per-service `subdomain.conf` files.
Each conf hardcodes the upstream IP and port, and emits a static `/.well-known/oauth-protected-resource`
JSON blob. Making the system proxy-agnostic requires adding a service registry to the auth service that
maps service names (or Host headers) to backend URLs, and generating `oauth-protected-resource` responses
dynamically rather than from nginx config.

## Relevant Files

- `/mnt/compose/mcp-oauth-gateway/mcp-template.subdomain.conf`: nginx template every MCP service uses — shows the full proxy, auth_request, and well-known routing surface that must be replicated in Python
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/config.py`: Settings class — only OAuth config today, zero knowledge of MCP backends
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/routes.py`: All OAuth endpoints including `/verify` (ForwardAuth target) and `/.well-known/oauth-authorization-server`
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/async_resource_protector.py`: Derives `resource` from `x-forwarded-host` header; generates `/.well-known/oauth-protected-resource` URL dynamically using the forwarded host — this is how audience validation already works proxy-agnostically
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/server.py`: `create_app()` — FastAPI app factory; CORS and middleware plumbing lives here
- `/mnt/compose/mcp-oauth-gateway/auth/docker-compose.yml`: Defines `mcp-oauth` container (port 8000), `callback-relay`, and `mcp-oauth-redis` — all on `mcp-net`
- `/mnt/compose/mcp-oauth-gateway/swag/docker-compose.yaml`: SWAG on `mcp-net` + `jakenet`; bind-mounts `./proxy-confs` into nginx config dir
- `/mnt/compose/mcp-oauth-gateway/swag/proxy-confs/_oauth_verify.conf`: Reusable nginx snippet — proxies `/_oauth_verify` to `http://mcp-oauth:8000/verify`
- `/mnt/compose/mcp-oauth-gateway/docker-compose.yml`: Root compose — declares `mcp-net` (name from `MCP_NETWORK`) and `jakenet` as external networks
- `/mnt/compose/mcp-oauth-gateway/.env.example`: Has `MCP_<SERVICE>_ENABLED`, `MCP_<SERVICE>_URLS`, and `MCP_<SERVICE>_TESTS_ENABLED` patterns for every known service
- `/mnt/compose/mcp-oauth-gateway/scripts/generate_compose_includes.py`: Reads `MCP_*_ENABLED` env vars to build `docker-compose.includes.yml` — the canonical list of known services lives in `OPTIONAL_SERVICE_INCLUDES`
- `/mnt/compose/mcp-oauth-gateway/tests/test_constants.py`: `_get_mcp_service_urls()` shows the URL resolution chain: `MCP_<SERVICE>_URLS` → `MCP_<SERVICE>_URL` → `MCP_TESTING_URL` → derived from `BASE_DOMAIN`
- `/mnt/compose/mcp-oauth-gateway/mcp-template.docker-compose.yml`: Template shows MCP services run on port 3000 internally, no host-port exposure required on same Docker network

## Architectural Patterns

- **External networks, no host ports**: All inter-container traffic flows over `mcp-net` (Docker bridge, name from `$MCP_NETWORK`). MCP services do not expose host ports — nginx resolves them by container name. A gateway-side reverse proxy needs the same network membership to reach `http://mcp-fetch:3000`.

- **Two-variable service registry already exists in `.env`**: Every service has `MCP_<SERVICE>_ENABLED` and `MCP_<SERVICE>_URLS` (comma-separated, full URLs including `/mcp` path). `test_constants.py` already parses this into a URL list. This is the seed of a runtime service registry.

- **`/verify` is already proxy-agnostic**: `async_resource_protector.py` derives the `resource` URI from `x-forwarded-host` + `x-forwarded-proto` at validation time, not from config. `/.well-known/oauth-protected-resource` is constructed on the fly. This same pattern should drive the routing table lookup.

- **`oauth-protected-resource` is currently nginx-static**: Each nginx subdomain conf returns a hardcoded JSON with `"resource": "https://{{DOMAIN}}"` and `"authorization_servers": ["https://{{AUTH_DOMAIN}}"]`. In a proxy-agnostic design this must be served dynamically by the auth service (or a thin per-service FastAPI layer) keyed on the incoming Host header.

- **Service name ↔ subdomain ↔ container name convention**: The `generate_compose_includes.py` maps e.g. `MCP_FETCH_ENABLED` → `mcp-fetch/docker-compose.yml`. Container names follow `mcp-<service>` convention (seen in nginx upstream syntax `http://mcp-fetch:3000`). `test_constants.py` maps `fetch` → default subdomain `fetch` → default URL `https://fetch.{BASE_DOMAIN}/mcp`. These three mappings need to be unified in the new registry.

- **`Settings` has no defaults — all config is explicit**: `config.py` uses Pydantic `Field(alias=...)` with no defaults for required fields. New backend URL config must follow this same pattern.

- **CORS is handled at the FastAPI layer** (`server.py` `CORSMiddleware`) when not behind a proxy. The nginx `_cors_headers.conf` snippet is a duplicate for the SWAG path. A proxy-agnostic gateway running behind no nginx must handle CORS itself — already done.

- **`mcp-net` is the single shared network**: SWAG, auth, and all MCP services share this one network. The auth service container is already on it, so it can already reach MCP container hostnames without any network change.

## Gotchas and Edge Cases

- **`jakenet` is a separate homelab-wide network** — not relevant to MCP service routing, but SWAG is also attached to it. A proxy-agnostic auth service only needs `mcp-net`.

- **`MCP_<SERVICE>_URLS` values already include the `/mcp` path suffix** — `test_constants.py` line 72 strips trailing slashes but keeps the path. Routing logic must not double-append `/mcp`.

- **Metadata-document clients (MCP 2025-11-25) use an HTTPS URL as `client_id`** — the `/verify` path already reconstructs `resource` from forwarded headers, but a proxy-agnostic `/mcp` proxy endpoint would need to ensure the token's `aud` claim matches the service URL it is routing to, not the auth service URL.

- **`docker-compose.includes.yml` is generated at deploy time** by `generate_compose_includes.py`. The list of known services lives there, not in the auth service. A service registry needs a source of truth — either extend this script to emit a config file for the auth service, or have the auth service parse the same `MCP_<SERVICE>_ENABLED`/`MCP_<SERVICE>_URLS` env vars directly.

- **Port 3000 is the internal MCP service port by convention** (template healthcheck hits `localhost:3000`), but the nginx template shows `UPSTREAM_PORT` as a placeholder suggesting it is not hardcoded. The `MCP_<SERVICE>_URLS` env vars point to the public HTTPS URL; for direct backend routing the auth service needs the internal `http://mcp-<service>:3000` address, which is not currently expressed in any config.

- **SWAG auth_request does not forward the request body** (`proxy_pass_request_body off` in `_oauth_verify.conf`). The `/verify` endpoint must never read the request body for this reason. This constraint goes away in a proxy-agnostic design where the auth service handles the full request.

- **`callback-relay` container shares the auth Dockerfile** but runs a different command (`scripts/callback_relay_server.py`). It is unrelated to MCP routing.

- **Alias proliferation in `.env`**: Many variables exist twice (`OAUTH_JWT_SECRET` / `GATEWAY_JWT_SECRET`, `OAUTH_ALLOWED_GITHUB_USERS` / `ALLOWED_GITHUB_USERS`). New service registry vars should use a single canonical name — `MCP_<SERVICE>_INTERNAL_URL` is the proposed pattern for the Docker-internal address.

- **`/verify` currently returns JSON** with user claims; nginx extracts them via `auth_request_set $auth_user_id $upstream_http_x_user_id`. In a proxy-agnostic design these must be forwarded as request headers to the MCP backend — the same information but injected directly in the forwarded request, not extracted from the sub-request.

## Service Registry Design Requirements

Given the above, the minimal service registry config must express:

| Variable pattern | Example | Purpose |
|---|---|---|
| `MCP_<SERVICE>_ENABLED` | `MCP_FETCH_ENABLED=true` | Already exists — gates service inclusion |
| `MCP_<SERVICE>_URLS` | `MCP_FETCH_URLS=https://fetch.tootie.tv/mcp` | Already exists — public URL for tests and client-facing `resource` field |
| `MCP_<SERVICE>_INTERNAL_URL` | `MCP_FETCH_INTERNAL_URL=http://mcp-fetch:3000` | **New** — Docker-internal backend URL for direct proxy |

The auth service can then:
1. Load all enabled service entries at startup into an in-memory registry.
2. Match incoming `Host` headers (or path prefixes) to a registry entry.
3. Validate the Bearer token with the public URL as the `resource` audience.
4. Forward the verified request to the internal URL, injecting `X-User-*` headers.
5. Serve `/.well-known/oauth-protected-resource` dynamically using the public URL.

## Other Docs

- `/mnt/compose/mcp-oauth-gateway/docs/internal-docs/streaming-proxy-requirements.docs.md` — sister doc on StreamableHTTP proxy requirements
- `/mnt/compose/mcp-oauth-gateway/CLAUDE.md` — full gateway architecture overview, Redis key patterns, and SWAG nginx routing rules
- [RFC 9728 — OAuth 2.0 Protected Resource Metadata](https://www.rfc-editor.org/rfc/rfc9728)
- [RFC 8252 §7.3 — Loopback Redirect URI port flexibility](https://www.rfc-editor.org/rfc/rfc8252#section-7.3)
- [MCP Authorization spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)
