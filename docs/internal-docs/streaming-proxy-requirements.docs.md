# Streaming Reverse Proxy — Technical Requirements

## Overview

The MCP protocol over HTTP uses three distinct response modes (plain JSON, SSE, and long-lived SSE heartbeat streams), plus a session-termination DELETE method. A Python reverse proxy layer inside the auth service must handle all three modes transparently, propagate the `Mcp-Session-Id` header in both directions, and clean up correctly when the client disconnects. No shared httpx client exists in the auth service today — every outbound call uses a fresh `async with httpx.AsyncClient(...)` context.

---

## Relevant Files

- `/mnt/compose/mcp-oauth-gateway/mcp-streamablehttp-proxy/src/mcp_streamablehttp_proxy/proxy.py` — Canonical MCP-over-HTTP server implementation; defines all three endpoint shapes (POST JSON-RPC, GET SSE heartbeat, DELETE session)
- `/mnt/compose/mcp-oauth-gateway/mcp-template.subdomain.conf` — nginx reference for every streaming-critical directive (timeouts, buffering, chunked encoding, `Connection: ''`)
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/routes.py` — Auth service route layer; where the proxy middleware would live
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/server.py` — FastAPI app factory, middleware chain, CORS setup
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/async_resource_protector.py` — Token validation used by `/verify`; the proxy must call this before forwarding
- `/mnt/compose/mcp-oauth-gateway/mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient/auth_authlib.py` — `AuthManager.fetch_client_metadata` shows the established per-request httpx pattern
- `/mnt/compose/mcp-oauth-gateway/mcp-streamablehttp-client/src/mcp_streamablehttp_client/proxy.py` — Client-side SSE parsing: `text/event-stream` detection + `data: ` line extraction pattern used throughout the test suite
- `/mnt/compose/mcp-oauth-gateway/tests/mcp_helpers.py` — Canonical test helpers: `initialize_mcp_session`, `call_mcp_tool`; documents expected header set for every MCP request
- `/mnt/compose/mcp-oauth-gateway/tests/conftest.py` — `http_client` fixture: `httpx.Limits(max_keepalive_connections=5, max_connections=10)` — connection-pool tuning reference

---

## Architectural Patterns

- **Three response modes on a single POST endpoint**: The MCP proxy server (proxy.py line 418–460) always returns `JSONResponse`. However, MCP clients send `Accept: application/json, text/event-stream` and some native MCP servers return `StreamingResponse` with `media_type="text/event-stream"`. The proxy layer must inspect `Content-Type` on the upstream response and relay it faithfully rather than assuming JSON.
- **GET /mcp is a persistent SSE heartbeat**: `proxy.py` lines 462–516 implement `GET /mcp` as a `StreamingResponse` that emits `: heartbeat\n\n` every 15 seconds and only terminates when the session expires or the client disconnects. nginx uses `proxy_read_timeout 86400s` (line 99 of `mcp-template.subdomain.conf`) for this exact reason. A Python proxy must hold the upstream `GET` open for the same duration.
- **DELETE /mcp terminates sessions**: `proxy.py` lines 518–533 handle `DELETE /mcp`. The Python proxy must forward DELETE with `Mcp-Session-Id` header intact and relay the 200 or 404 response; it must not intercept the body.
- **`Mcp-Session-Id` must travel in both directions**: Set by the upstream on the `initialize` response, then echoed by the client on every subsequent request. nginx forwards it explicitly (`proxy_set_header Mcp-Session-Id $http_mcp_session_id`, line 91). The Python proxy must copy it from upstream response headers into the downstream response, and copy it from the incoming client request into the upstream request.
- **Per-request httpx clients, no shared pool in auth service**: `auth_authlib.py` line 392 (`async with httpx.AsyncClient(timeout=10.0) as client`) and every other caller use ephemeral clients. The streaming proxy is the first place where a long-lived client makes sense — specifically for SSE GET streams that must remain open for up to 24 hours.
- **Token validation via `AsyncResourceProtector`**: `async_resource_protector.py` line 27 (`validate_request`) raises `HTTPException(401)` or `HTTPException(403)` directly. The proxy middleware must call this before opening the upstream connection so auth failures short-circuit before any streaming begins.
- **SSE parsing convention**: The entire test suite (mcp_helpers.py lines 68–79, proxy.py lines 197–205) uses a consistent pattern: iterate lines, find `data: ` prefix, `json.loads(line[6:])`. The proxy does not need to parse SSE; it must stream bytes verbatim.
- **`Connection: ''` (empty) is mandatory for HTTP/1.1 keep-alive with nginx**: `mcp-template.subdomain.conf` line 88 (`proxy_set_header Connection ''`) prevents nginx from forwarding the `Connection: close` header upstream. The Python equivalent is ensuring httpx uses HTTP/1.1 with keep-alive and does not emit `Connection: close` to the MCP backend.
- **`proxy_buffering off` + `proxy_max_temp_file_size 0`**: nginx lines 83 and 86 disable all response buffering. In httpx this maps to using `stream()` context manager and `aiter_bytes()` / `aiter_lines()` rather than `response.content` or `response.text`.
- **CORS is handled at the server.py middleware level**: `server.py` lines 306–314 add `CORSMiddleware`. The proxy must not add its own CORS headers; it must strip any duplicate CORS headers from the upstream backend response before forwarding to avoid header duplication.

---

## Gotchas and Edge Cases

- **Client disconnect during SSE stream requires upstream cancellation**: If the downstream client closes the connection mid-stream (GET /mcp), the async generator in `sse_stream()` (proxy.py line 489) raises `asyncio.CancelledError`. The Python proxy must `await response.aclose()` on the upstream httpx response inside an `except (asyncio.CancelledError, GeneratorExit)` block to prevent the upstream subprocess from leaking.
- **`asyncio.CancelledError` is NOT an Exception subclass in Python 3.8+**: It is a `BaseException`. Any bare `except Exception` in a streaming generator will silently fail to catch it, leaving the upstream connection open. Use `except BaseException` or separate `except asyncio.CancelledError` blocks.
- **The proxy server issues `notifications/initialized` automatically on the `initialize` response** (proxy.py lines 175–181). The Python reverse proxy must relay the raw `initialize` response without injecting its own `notifications/initialized` — the client library (mcp-streamablehttp-client, proxy.py line 211) sends it separately.
- **Session re-use fallback in the proxy server**: `proxy.py` lines 336–343 fall back to the most-recently-active session when no `Mcp-Session-Id` is provided and no method is `initialize`. A reverse proxy that strips `Mcp-Session-Id` from forwarded requests would silently trigger this fallback, causing session mixing across clients.
- **Stale session IDs on reconnect**: `proxy.py` line 480 (`if session_id and session_id not in session_manager.sessions: session_id = None`) shows the upstream server accepts unknown session IDs on GET /mcp by opening a standalone stream rather than returning 404. The Python proxy must pass the client's session ID through unchanged and let the upstream decide.
- **`chunked_transfer_encoding on`** (nginx line 87): When nginx forwards to the Python app, it may re-chunk the body. The Python ASGI server (uvicorn) handles chunked decoding automatically. The Python proxy must set `Transfer-Encoding: chunked` (or rely on httpx streaming) when relaying to the upstream to avoid buffering large tool call results.
- **Timeout asymmetry**: nginx uses `proxy_connect_timeout 240s` but `proxy_read_timeout 86400s` (lines 97–99). httpx uses a single `Timeout` object with `connect`, `read`, `write`, `pool` fields. The proxy client must set `httpx.Timeout(connect=240.0, read=86400.0, write=86400.0, pool=5.0)` — using a single float will apply the same value to all phases and either time out SSE streams or hang indefinitely on connect.
- **Upstream port is per-service configuration**: There is no central registry file. Each MCP service gets its own `{{UPSTREAM_IP}}:{{UPSTREAM_PORT}}` in the nginx template. The Python proxy layer will need a route table (e.g. from env vars or a config dict) mapping hostname or path prefix to backend URL.
- **`proxy_pass_request_body off` in `/_oauth_verify`**: The internal verify sub-request explicitly drops the body (swag `_oauth_verify.conf` line 13). The Python proxy's token validation must extract the `Authorization` header only; it must not attempt to read or buffer the request body before streaming it upstream.
- **OPTIONS preflight is handled inline**: nginx returns 204 directly (`mcp-template.subdomain.conf` lines 108–112). The Python proxy must short-circuit OPTIONS at the route level and never forward it to the upstream MCP service.
- **`proxy_set_header MCP-Protocol-Version`** (nginx line 90): nginx forwards the client's `MCP-Protocol-Version` header, not a hardcoded value. The Python proxy must copy `MCP-Protocol-Version` from the inbound request, not inject a server-side constant.
- **`httpx.AsyncClient` with `follow_redirects=False` pattern**: `auth_authlib.py` line 396 uses `follow_redirects=False` for SSRF protection when fetching client metadata. The streaming proxy upstream connections should similarly not follow redirects unless explicitly intended, as a redirect could bypass auth by pointing to an unprotected internal address.
- **No `mcp.conf` nginx include in the repo**: The template references `include /config/nginx/mcp.conf` at lines 84 and 224, but this file is not checked into the repo under `swag/`. The directives it contains are unknown from source alone; the streaming settings visible directly in the template (buffering, timeouts, headers) are the complete reference available.

---

## Other Docs

- MCP StreamableHTTP transport specification: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports#streamable-http
- RFC 8252 §7.3 — Loopback redirect URIs (port flexibility): https://datatracker.ietf.org/doc/html/rfc8252#section-7.3
- httpx streaming documentation: https://www.python-httpx.org/async/#streaming-responses
- httpx Timeout configuration: https://www.python-httpx.org/advanced/timeouts/
- Starlette `StreamingResponse`: https://www.starlette.io/responses/#streamingresponse
- `/mnt/compose/mcp-oauth-gateway/CLAUDE.md` — Gateway architecture overview, Redis key patterns, sacred env vars
- `/mnt/compose/mcp-oauth-gateway/mcp-streamablehttp-proxy/CLAUDE.md` — Proxy session lifecycle detail, 30s per-request timeout, 5-minute session timeout
