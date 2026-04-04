# Auth Middleware Refactor — Eliminating nginx auth_request

The auth service (`mcp-oauth-dynamicclient`) already contains all the primitives
needed to inline token verification as Python middleware and proxy directly to MCP
backends. The nginx `auth_request` subrequest pattern is a thin wrapper around
`AsyncResourceProtector.validate_request()`, which is a pure async function that
raises `HTTPException` on failure. Origin validation is the most nontrivial piece to
port because it currently lives in nginx `if` blocks with no Python equivalent.

## Relevant Files

- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/routes.py` — all route definitions; `/verify` endpoint at line 1299; route protection map below
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/async_resource_protector.py` — `AsyncResourceProtector.validate_request()`, the single auth entry point
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/resource_protector.py` — `JWTBearerTokenValidator`: JWT decode + Redis revocation check; `IntrospectionBearerTokenValidator` variant
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/server.py` — `create_app()` builds the FastAPI app; existing middleware stack at lines 307-400
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/auth_authlib.py` — `create_jwt_token()` at line 123 defines full JWT claims shape; `verify_jwt_token()` at line 189
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/config.py` — `Settings` — all config keys; `auth_subdomain` and `base_domain` used to construct issuer/audience URLs
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/rfc7592.py` — `DynamicClientConfigurationEndpoint`; uses its own `registration_access_token` Bearer, not the JWT Bearer
- `/mnt/compose/mcp-oauth-gateway/mcp-template.subdomain.conf` — current nginx config; origin validation rules (lines 31-47); auth_request + header injection pattern (lines 76-95, 244-261, 265-278)
- `/mnt/compose/mcp-oauth-gateway/swag/proxy-confs/_oauth_verify.conf` — nginx snippet wiring `/verify` as an internal `auth_request` target

## Architectural Patterns

- **Single auth entry point**: All token validation flows through `AsyncResourceProtector.validate_request(request, resource=None)`. It raises `HTTPException(401)` with RFC 9728-compliant `WWW-Authenticate` headers on any failure. To become middleware, wrap this call and attach the returned token dict to `request.state.token`.
- **Resource/audience binding**: The `resource` parameter to `validate_request` controls whether audience (`aud`) is validated. When `None`, audience validation is skipped. When a URL is passed, the token's `aud` claim must contain that URL (trailing-slash normalized). In the gateway proxy scenario, `resource` should be the upstream MCP service URL, exactly as it appears in the token's `aud`.
- **WWW-Authenticate header construction**: Built at lines 39-63 of `async_resource_protector.py`. Constructed from `settings.auth_subdomain + settings.base_domain` and the request's `host`/`x-forwarded-proto` headers. The format is RFC 9728 (`as_uri` + `resource_metadata` params). This runs fine inside middleware without nginx involvement.
- **JWT claims shape**: `create_jwt_token()` stores `sub`, `username`, `email`, `name`, `scope`, `client_id`, `jti`, `iat`, `exp`, `iss`, `aud`, `azp`. The `validate_request` return value is a raw `dict` of these claims. The gateway can inject `X-User-Id` from `token["sub"]`, `X-User-Name` from `token["username"]`, and reconstruct `X-Auth-Token` by re-forwarding the original `Authorization` header value.
- **Lazy ResourceProtector initialization**: `require_oauth` is a `nonlocal` variable inside `create_oauth_router()` initialized on first request (lines 46-65). A middleware version should use the same deferred pattern or accept `redis_manager` as a closure.
- **Two independent Bearer realms**: RFC 7592 management routes (`/register/{client_id}` GET/PUT/DELETE) use `registration_access_token` (a `reg-` prefixed opaque string compared via `secrets.compare_digest`). They do NOT use `AsyncResourceProtector` and must never be wired through JWT auth middleware.

## Route Protection Map

### Fully Public — No Auth Middleware

| Route | Reason |
|---|---|
| `GET /.well-known/oauth-authorization-server` | RFC 8414 discovery — must be unauthenticated |
| `GET /.well-known/openid-configuration` | OIDC discovery — must be unauthenticated |
| `GET /jwks` | Public key distribution — must be unauthenticated |
| `POST /register` | RFC 7591 — explicitly public |
| `GET /authorize` | Initiates auth flow — client not yet authenticated |
| `GET /callback` | GitHub OAuth return — no token yet |
| `POST /token` | Client sends code, not bearer token |
| `POST /device/code` | Device flow initiation — no user token yet |
| `GET /activate` | Device UI page — browser, no token |
| `POST /activate` | Device code submit — no token |
| `GET /device/success` | Completion page — no token |
| `POST /revoke` | RFC 7009 — authenticated by client credentials, not JWT |
| `POST /introspect` | RFC 7662 — authenticated by client credentials, not JWT |
| `GET /error` | Error display page |
| `GET /success` | Success display page |
| `GET /verify` + `POST /verify` | The endpoint itself validates tokens; cannot self-protect |

### RFC 7592 Protected (registration_access_token, NOT JWT)

| Route | Auth Mechanism |
|---|---|
| `GET /register/{client_id}` | `Bearer reg-{opaque}` via `DynamicClientConfigurationEndpoint.authenticate_client()` |
| `PUT /register/{client_id}` | Same |
| `DELETE /register/{client_id}` | Same |

### MCP Backend Routes (new — JWT Bearer required)

These do not exist yet. The refactor creates them. They need `AsyncResourceProtector` middleware before proxying to MCP backends.

## Gotchas and Edge Cases

- **`/verify` returns JSON body, not response headers**: The nginx template reads `$upstream_http_x_user_id`, `$upstream_http_x_user_name`, `$upstream_http_x_auth_token` (lines 78-80, 246-248, 267-269), but the `/verify` endpoint only returns a JSON body (lines 1334-1342). **The `X-User-*` values nginx injects into MCP requests are always empty strings in the current system.** The refactored middleware should inject these headers explicitly during proxying from the decoded JWT claims.
- **Origin validation lives entirely in nginx**: The `$origin_valid` logic (template lines 31-47) allows: empty origin, `https://$server_name`, `https://localhost[:{port}]`, `https://*.anthropic.com`, `https://*.claude.ai`. There is zero origin enforcement in Python today. Any Python middleware replacement must implement these rules from scratch. The allowed-origin set is hardcoded in the nginx template with no env-var equivalent.
- **`resource` parameter is path-sensitive**: `validate_request` constructs `resource` as `{proto}://{forwarded_host}{forwarded_path}`. In the direct-proxy scenario, `forwarded_host` and `forwarded_path` come from the incoming request, not from nginx headers. The resource URI used at token-issue time (in `/token` via RFC 8707 `resource` parameter) must exactly match what the middleware constructs, modulo trailing-slash normalization.
- **Audience validation is opt-in**: If `resource=None` is passed to `validate_request`, the `aud` claim is never checked. In the nginx model this was acceptable because nginx enforced service isolation at the subdomain level. In a Python proxy, the middleware must pass the correct upstream resource URL to enforce per-service audience scoping.
- **`require_oauth` is shared state inside a closure**: The `nonlocal require_oauth` pattern in `create_oauth_router()` means the same `AsyncResourceProtector` instance is reused across all requests after first initialization. Moving auth to middleware requires externalizing this to app-level state (e.g., `app.state.require_oauth`) to avoid creating new instances per-request.
- **`/verify` is currently called by both nginx AND could be called by Traefik**: The docstring says "validates Bearer tokens for Traefik" but the nginx template uses it too via `proxy_pass http://mcp-oauth:8000/verify`. The endpoint is generic forward-auth. It can be deprecated entirely once middleware is inline but should be kept during transition.
- **JWT `aud` claim shape varies**: If RFC 8707 `resource` indicators were used during token issuance, `aud` is a list; if not, it is a single string. `validate_request` normalizes both at lines 106-113 of `async_resource_protector.py`. The Redis token store (written by `create_jwt_token`) stores `aud` as whatever `json.dumps` produces — a string or list.
- **Token Redis key does not store the JWT string**: `oauth:token:{jti}` stores the claims dict (without `jti`, `exp`, `iat` — only `**claims` from the input). The raw token string is not retrievable from Redis. `X-Auth-Token` forwarding must use the original `Authorization: Bearer {token}` header value from the inbound request, not anything from Redis.
- **Settings field aliases**: Config fields use `Field(alias="OAUTH_*")` but `populate_by_name=True` allows both the alias and the Python field name. When writing middleware that instantiates `Settings`, env vars need the `OAUTH_` prefix (e.g., `OAUTH_JWT_ALGORITHM`, not `JWT_ALGORITHM`).
- **`MCP_CORS_ORIGINS` env var controls CORS middleware** (server.py lines 300-314): Currently defaults to `*`. When the Python server proxies directly to MCP backends, CORS handling moves entirely into Python and this env var becomes the sole control surface for origin allowlist — distinct from the DNS-rebinding origin validation for `/mcp` which needs separate implementation.

## Existing Middleware Stack Order (server.py)

Starlette processes middleware in reverse registration order (last-added runs first on ingress):

1. `CORSMiddleware` — registered via `app.add_middleware()` (line 307) — outermost
2. `log_proxy_headers` — registered via `@app.middleware("http")` (line 317) — runs after CORS
3. Request handlers (routes)

A new auth+proxy middleware for MCP backends should be registered after `log_proxy_headers` so auth decisions appear in the structured log. It should also be implemented as a FastAPI dependency on route handlers (not a blanket `@app.middleware("http")`) to avoid accidentally applying JWT auth to the public OAuth endpoints listed above.

## Relevant Docs

- `mcp-oauth-dynamicclient/CLAUDE.md` — in-repo guide for this package; covers sacred endpoint list, Redis patterns, JWT algorithm rules
- `CLAUDE.md` (project root) — system architecture diagram, nginx routing rules, dual-realm auth table, env var reference
- [RFC 9728 — OAuth 2.0 Protected Resource Metadata](https://www.rfc-editor.org/rfc/rfc9728) — defines `WWW-Authenticate` `resource_metadata` parameter used by `AsyncResourceProtector`
- [RFC 8707 — Resource Indicators for OAuth 2.0](https://www.rfc-editor.org/rfc/rfc8707) — defines `aud` binding to resource URLs
- [RFC 8252 §7.3 — Loopback Interface Redirects](https://www.rfc-editor.org/rfc/rfc8252#section-7.3) — justifies port-agnostic matching for `127.0.0.1`/`localhost` redirect URIs
