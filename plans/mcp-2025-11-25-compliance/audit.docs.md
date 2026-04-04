# MCP 2025-11-25 Authorization Spec Compliance Audit

## Summary

The gateway is substantially compliant with the MCP authorization specification but has four concrete gaps: the `WWW-Authenticate` header uses `resource=` instead of the RFC 9728-mandated `resource_metadata=`; neither path-based auth server discovery nor `/.well-known/openid-configuration` is served; `client_id_metadata_document_supported` and `resource_parameters_supported` are absent from auth server metadata; and the `resource` parameter (RFC 8707) is silently ignored on authorization and token requests. The `aud` claim in issued JWTs is hardcoded to the auth server URL rather than the target resource, which will cause audience validation failures when clients enforce RFC 8707 semantics.

---

## Key Components

- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/routes.py`: All OAuth endpoint handlers, including `/.well-known/oauth-authorization-server` metadata, `/authorize`, `/token`
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/auth_authlib.py`: JWT minting (`create_jwt_token`) — sets `aud` claim
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/resource_protector.py`: Token validation — `claims_options` does not include `aud` validation
- `/mnt/compose/mcp-oauth-gateway/servers/mcp-template.subdomain.conf`: SWAG nginx template for all MCP services
- `/mnt/appdata/swag/nginx/proxy-confs/axon.subdomain.conf`: Live deployed MCP service config (representative)
- `/mnt/appdata/swag/nginx/proxy-confs/swag-mcp.subdomain.conf`: Another deployed instance

---

## Compliance Findings

### 1. WWW-Authenticate `resource_metadata` Parameter

**Status: ⚠️ PARTIAL**

The `@error_401` block in every SWAG config (template and all deployed instances) emits:

```nginx
add_header WWW-Authenticate 'Bearer realm="MCP Server", resource="https://$server_name/.well-known/oauth-protected-resource"' always;
```

RFC 9728 Section 4 and the MCP 2025-11-25 spec require the parameter to be named `resource_metadata`, not `resource`. Additionally, the auth service `/verify` endpoint returns a bare `WWW-Authenticate: Bearer` when called without credentials, resulting in **two separate `WWW-Authenticate` headers** reaching the client — one from the auth sub-request forwarded by nginx auth_request, and one from the `@error_401` block. Some clients will reject or misparse duplicate headers.

Affected files (identical pattern in all):
- `/mnt/compose/mcp-oauth-gateway/servers/mcp-template.subdomain.conf` line 244
- `/mnt/appdata/swag/nginx/proxy-confs/axon.subdomain.conf` line 261
- `/mnt/appdata/swag/nginx/proxy-confs/swag-mcp.subdomain.conf` line 259
- `/mnt/appdata/swag/nginx/proxy-confs/docker-mcp.subdomain.conf` line 250
- `/mnt/appdata/swag/nginx/proxy-confs/syslog-mcp.subdomain.conf` line 284

Live confirmation:
```
HTTP/2 401
www-authenticate: Bearer
www-authenticate: Bearer realm="MCP Server", resource="https://axon.tootie.tv/.well-known/oauth-protected-resource"
```

---

### 2. Protected Resource Metadata (RFC 9728)

**Status: ⚠️ PARTIAL**

`/.well-known/oauth-protected-resource` is served as a static JSON response by SWAG for all deployed MCP service domains (e.g. `axon.tootie.tv`). The response includes `resource`, `authorization_servers`, `scopes_supported`, and `bearer_methods_supported`. Live response confirmed valid.

**Missing: path-based discovery.** RFC 9728 allows `/.well-known/oauth-protected-resource/{resource-path}` for compound URIs. In the current config, `/.well-known/oauth-protected-resource/mcp` falls through to `location /` which applies `auth_request`, resulting in a `401` instead of the metadata document. This is a minor issue as most clients use only the exact-match path.

**The `scope` field in `WWW-Authenticate` is absent.** The spec recommends including `scope` in the `WWW-Authenticate` header to indicate what scopes are needed.

---

### 3. Authorization Server Metadata (RFC 8414 + OpenID Connect Discovery)

**Status: ⚠️ PARTIAL**

`/.well-known/oauth-authorization-server` is served at both:
- `https://mcp-auth.tootie.tv/.well-known/oauth-authorization-server` (auth service domain) — works, returns full metadata
- `https://axon.tootie.tv/.well-known/oauth-authorization-server` (per MCP service domain) — proxied to auth service, works

**Missing:**

1. **`/.well-known/openid-configuration`** returns `404` on both the auth service domain and all MCP service domains. The auth service (`routes.py`) has no route for this path. The SWAG configs proxy it to the auth service, but the auth service returns 404. The MCP 2025-11-25 spec requires this endpoint for OpenID Connect compatibility.

2. **Path-based discovery** (`/.well-known/oauth-authorization-server/mcp`) returns `404` on the auth service and `401` on MCP service domains. RFC 8414 Section 3.1 specifies that servers SHOULD respond to subpath variants when the issuer URL contains a path component.

Live confirmed:
```
curl https://mcp-auth.tootie.tv/.well-known/openid-configuration → 404
curl https://axon.tootie.tv/.well-known/openid-configuration → 404
curl https://axon.tootie.tv/.well-known/oauth-authorization-server/mcp → 401
```

---

### 4. Client ID Metadata Documents

**Status: ❌ MISSING**

`client_id_metadata_document_supported` is absent from the `/.well-known/oauth-authorization-server` response. The MCP 2025-11-25 spec requires this field to indicate whether the server supports client ID metadata documents as a registration alternative.

Confirmed via:
```python
"client_id_metadata_document_supported" in metadata  # → False
```

Location to fix: `routes.py` `oauth_metadata()` function, lines 84–103.

---

### 5. Dynamic Client Registration (RFC 7591)

**Status: ✅ COMPLIANT**

`POST /register` is implemented and publicly accessible. Returns HTTP 201, includes `client_id`, `client_secret`, `client_secret_expires_at`, `registration_access_token`, and `registration_client_uri`. RFC 7592 management endpoints (`GET/PUT/DELETE /register/{client_id}`) are implemented. `registration_endpoint` is present in auth server metadata.

---

### 6. Resource Parameter (RFC 8707)

**Status: ❌ MISSING**

Neither the `/authorize` endpoint nor the `/token` endpoint accepts or processes the `resource` parameter. The `authorize` function signature (routes.py lines 221–230) has no `resource` query parameter. The `token_exchange` function (routes.py lines 457–468) has no `resource` form field. The parameter is silently ignored if passed.

As a consequence, the JWT `aud` claim is always set to the auth server's own URL (`https://mcp-auth.tootie.tv`) regardless of which resource the client is requesting access to. Per RFC 8707, the `aud` should match the resource URI when the `resource` parameter is used. Clients enforcing audience validation against the target MCP resource URL will reject these tokens.

Relevant code in `auth_authlib.py` line 102:
```python
"aud": f"https://{self.settings.auth_subdomain}.{self.settings.base_domain}",
```

---

### 7. PKCE S256

**Status: ✅ COMPLIANT**

PKCE S256 is required. The `plain` method is explicitly rejected. `code_challenge_methods_supported: ["S256"]` is present in auth server metadata. Implementation in `auth_authlib.py` `verify_pkce_challenge()` is correct (SHA256 + base64url without padding).

---

### 8. Scope Handling

**Status: ⚠️ PARTIAL**

`scopes_supported` in the Protected Resource Metadata returns `["mcp:read", "mcp:write"]` (static in SWAG nginx config). The auth server metadata returns `scopes_supported: ["openid", "profile", "email"]`. These are inconsistent — the resource advertises MCP-specific scopes but the auth server only advertises OIDC scopes. The `scope` parameter is absent from the `WWW-Authenticate` header on 401 responses, which the spec recommends including.

The token endpoint accepts any scope string and the authorization endpoint defaults to `"openid profile email"` if not specified.

---

### 9. Token Audience Validation

**Status: ⚠️ PARTIAL**

The `aud` claim is set in issued tokens (value: `https://mcp-auth.tootie.tv`). However, the `resource_protector.py` `claims_options` does NOT validate the `aud` claim — only `iss`, `exp`, and `jti` are validated. This means tokens with a tampered or absent `aud` would still be accepted by `/verify`. Additionally, because the `aud` is always the auth server URL and never the target resource URL (no RFC 8707 support), clients that use the resource indicator to scope tokens cannot obtain appropriately-audienced tokens.

---

## Considerations

1. The `WWW-Authenticate` duplicate header issue (bare `Bearer` from auth service + `Bearer realm=... resource=...` from SWAG) could cause client parsing failures. The auth service's response header to nginx's internal `auth_request` sub-request propagates to the client in SWAG's auth_request mechanism.

2. The `resource_metadata` vs `resource` parameter naming error is in all five nginx config files and the template, meaning it will propagate to all future service configs until the template is corrected.

3. The OpenID Connect Discovery (`/.well-known/openid-configuration`) gap is strictly a spec compliance issue — Claude.ai uses `/.well-known/oauth-authorization-server` primarily, so practical impact is limited to clients using OIDC discovery.

4. Path-based discovery gaps only matter for MCP resource URIs with path components (e.g. `https://axon.tootie.tv/mcp`). If clients use the hostname-only URI, exact-match discovery works fine.

5. The `resource` parameter gap (RFC 8707) is the highest-risk missing feature for future MCP client compatibility, as the 2025-11-25 spec explicitly requires server support for audience-bound tokens.

---

## Next Steps

1. **Fix `resource_metadata` parameter name** in `@error_401` blocks across all nginx configs and the template (5 files). Change `resource=` to `resource_metadata=`.

2. **Eliminate duplicate `WWW-Authenticate` header** by suppressing the bare `Bearer` from the auth service's `/verify` endpoint responses to nginx, or by using `auth_request_set` to capture and suppress the auth service's WWW-Authenticate before `@error_401` fires.

3. **Add `/.well-known/openid-configuration` route** in `routes.py` — can alias to the same handler as `oauth_metadata()`.

4. **Add `client_id_metadata_document_supported: false`** (or `true` if implementing) to the auth server metadata response in `routes.py` `oauth_metadata()`.

5. **Add RFC 8707 `resource` parameter support** to `/authorize` and `/token` endpoints in `routes.py`, store it in the auth code, and pass it to `create_jwt_token` so the `aud` claim reflects the resource URI.

6. **Add `aud` validation** to `resource_protector.py` `claims_options` once resource-specific audience support is implemented.

7. **Add `scope` to `WWW-Authenticate`** in `@error_401` blocks, and align `scopes_supported` between Protected Resource Metadata and Auth Server Metadata.
