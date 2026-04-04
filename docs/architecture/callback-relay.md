# Codex OAuth Callback Relay

## Purpose

This document explains the callback relay used to make `codex mcp login` work when the browser that completes OAuth cannot directly deliver the final callback to the machine running Codex.

The relay exists because Codex uses OAuth authorization code flow with PKCE and expects the final browser redirect to hit a local HTTP callback listener. In practice, that listener is often not reachable from the browser machine, especially when:

- Codex is running on a remote box
- the browser is running somewhere else
- the callback would otherwise point at `localhost`
- the machine is behind NAT
- the machine is headless

The relay solves only the callback delivery problem. It does not mint tokens on behalf of Codex and it does not bypass Codex's own OAuth state handling.

## What the relay does

The relay accepts a public callback URL such as:

```text
https://callback.tootie.tv/callback/squirts?code=...&state=...
```

and forwards that request to the Codex machine's local callback listener, for example:

```text
http://127.0.0.1:38935/callback/squirts?code=...&state=...
```

If the forwarded request reaches the live Codex listener while the `codex mcp login` command is still waiting, Codex finishes the OAuth flow normally and stores the resulting credentials itself.

## Architecture

### Public entrypoint

- Public hostname: `https://callback.tootie.tv`
- Reverse proxy: SWAG
- SWAG upstream target on `squirts`: `100.75.111.118:39001`

### Relay service

- Service code: [callback_relay.py](/mnt/compose/mcp-oauth-gateway/@oauth-helpers/scripts/callback_relay.py)
- Server runner: [callback_relay_server.py](/mnt/compose/mcp-oauth-gateway/@oauth-helpers/scripts/callback_relay_server.py)
- Just recipe: [justfile](/mnt/compose/mcp-oauth-gateway/justfile)
- Health endpoint: `GET /healthz`
- Registry endpoints:
  - `PUT /api/machines/{machine_id}`
  - `GET /api/machines/{machine_id}`
  - `DELETE /api/machines/{machine_id}`
- Public callback endpoints:
  - `GET /callback/{machine_id}`
  - `POST /callback/{machine_id}`
  - `GET /callback/{machine_id}/{suffix_path}`
  - `POST /callback/{machine_id}/{suffix_path}`

### Machine registry

The relay keeps a small file-backed registry that maps a machine ID to its callback target URL.

Current default path:

```text
.cache/callback-relay/registry.json
```

Admin token path on `squirts`:

```text
.cache/callback-relay/admin-token
```

The admin token is required for the registry API and is sent as:

```text
Authorization: Bearer <token>
```

### Service placement

Preferred deployment is the dedicated compose service:

```bash
docker compose up -d --build callback-relay
```

Relevant files:

- [auth/docker-compose.yml](/mnt/compose/mcp-oauth-gateway/auth/docker-compose.yml)
- [auth/Dockerfile](/mnt/compose/mcp-oauth-gateway/auth/Dockerfile)

The compose service persists its registry under:

```text
/app/.cache/callback-relay/registry.json
```

On `squirts`, the relay was initially run as a user `systemd` transient unit:

```bash
systemd-run --user --unit=callback-relay --collect --same-dir \
  --setenv=CALLBACK_RELAY_ADMIN_TOKEN=... \
  --setenv=CALLBACK_RELAY_HOST=0.0.0.0 \
  --setenv=CALLBACK_RELAY_PORT=39001 \
  /mnt/compose/mcp-oauth-gateway/.venv/bin/python \
  /mnt/compose/mcp-oauth-gateway/@oauth-helpers/scripts/callback_relay_server.py
```

This makes the relay reachable from SWAG on:

```text
http://100.75.111.118:39001
```

## End-to-end flow

### 1. Codex starts login

User runs:

```bash
codex mcp login arcane
```

Codex starts a temporary local callback listener, for example on port `38935`, and generates an authorization URL.

Because Codex is configured with:

```toml
mcp_oauth_callback_port = 38935
mcp_oauth_callback_url = "https://callback.tootie.tv/callback/squirts"
```

the generated OAuth request includes:

```text
redirect_uri=https://callback.tootie.tv/callback/squirts
```

### 2. Browser completes OAuth

The browser is redirected through the OAuth gateway and finally lands on:

```text
https://callback.tootie.tv/callback/squirts?code=...&state=...
```

### 3. SWAG forwards to relay

SWAG receives the request and proxies it to the relay on `squirts`.

### 4. Relay looks up the machine target

The relay resolves `squirts` in its registry and retrieves a target URL such as:

```text
http://127.0.0.1:38935/callback/squirts
```

or for another machine:

```text
http://100.88.16.79:38935/callback/dookie
```

### 5. Relay forwards the request

The relay forwards the original HTTP method, query string, and request body to that target URL. It also adds:

```text
x-callback-relay-machine-id: <machine-id>
```

### 6. Codex handles the callback

If Codex is still listening and the callback path and state are correct, it accepts the request, validates the authorization state and PKCE flow, exchanges the code for tokens, and completes login.

The user sees Codex report:

```text
Successfully logged in to MCP server 'arcane'.
```

## Why this works

The relay does not need access to:

- Codex's PKCE `code_verifier`
- Codex's authorization state store
- Codex's credential storage internals

The relay only needs to transport the final browser callback to the correct machine and callback path while the Codex process is waiting.

That keeps the design aligned with Codex's native behavior instead of reimplementing Codex's login completion logic.

## Per-machine setup

Each Codex machine needs:

1. A fixed callback port
2. A unique public relay callback path
3. A relay registry entry pointing back to that machine's live callback listener

### Codex config

Example for machine `squirts`:

```toml
mcp_oauth_callback_port = 38935
mcp_oauth_callback_url = "https://callback.tootie.tv/callback/squirts"
```

Example for machine `dookie`:

```toml
mcp_oauth_callback_port = 38935
mcp_oauth_callback_url = "https://callback.tootie.tv/callback/dookie"
```

### Relay registration

The important rule is:

- if the relay and Codex run on the same host, use loopback
- if the relay forwards to another host, use that host's reachable Tailscale IP or hostname

Examples:

#### Same host

```json
{
  "target_url": "http://127.0.0.1:38935/callback/squirts",
  "description": "squirts codex callback"
}
```

#### Different host

```json
{
  "target_url": "http://100.88.16.79:38935/callback/dookie",
  "description": "dookie codex callback"
}
```

### Registration command

```bash
curl -X PUT http://127.0.0.1:39001/api/machines/<machine-id> \
  -H "Authorization: Bearer <relay-admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"target_url":"http://<reachable-host>:38935/callback/<machine-id>","description":"<notes>"}'
```

## Current known-good examples

### `squirts`

- Public callback URL:
  `https://callback.tootie.tv/callback/squirts`
- Relay target:
  `http://127.0.0.1:38935/callback/squirts`

Why loopback works here:

- the relay runs on `squirts`
- Codex also runs on `squirts`
- relay can reach Codex through `127.0.0.1`

### `dookie`

- Public callback URL:
  `https://callback.tootie.tv/callback/dookie`
- Relay target:
  `http://100.88.16.79:38935/callback/dookie`

Why loopback does not work here:

- the relay runs on `squirts`
- Codex runs on `dookie`
- `127.0.0.1` on `squirts` is not `dookie`
- relay must use `dookie`'s reachable Tailscale address

## Failure modes and what they mean

### `502 Bad Gateway` in browser

This means the relay could not successfully forward the callback to the machine target.

Common causes:

- wrong target host
- wrong target path
- no listener on the target port
- Codex login process already exited

### `Invalid OAuth callback`

This means the relay reached something on the target port, but the path was wrong for the live Codex callback listener.

Example of wrong path:

```text
http://127.0.0.1:38935/callback
```

when Codex expects:

```text
http://127.0.0.1:38935/callback/squirts
```

### `Authorization state not found`

This means a callback reached Codex, but the request did not match the currently active OAuth login state.

Common causes:

- replaying an old callback URL
- sending a synthetic test callback into a live login attempt
- using a stale browser tab from a previous login attempt

### Relay healthy but callback still fails

Check whether the machine callback listener is alive while `codex mcp login` is waiting:

```bash
ss -ltn '( sport = :38935 )'
```

If `38935` is not listening when the browser callback lands, the relay cannot help because there is no live local target.

## Operational commands

### Check relay health

```bash
curl https://callback.tootie.tv/healthz
curl http://127.0.0.1:39001/healthz
```

### Check relay service

```bash
systemctl --user status callback-relay.service
journalctl --user -u callback-relay.service -n 100 --no-pager
```

### Query machine registration

```bash
curl http://127.0.0.1:39001/api/machines/squirts \
  -H "Authorization: Bearer <relay-admin-token>"
```

### Update machine registration

```bash
curl -X PUT http://127.0.0.1:39001/api/machines/squirts \
  -H "Authorization: Bearer <relay-admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"target_url":"http://127.0.0.1:38935/callback/squirts","description":"squirts codex callback"}'
```

### Delete machine registration

```bash
curl -X DELETE http://127.0.0.1:39001/api/machines/squirts \
  -H "Authorization: Bearer <relay-admin-token>"
```

## Implementation notes

### Files

- Relay app: [callback_relay.py](/mnt/compose/mcp-oauth-gateway/@oauth-helpers/scripts/callback_relay.py)
- Relay server runner: [callback_relay_server.py](/mnt/compose/mcp-oauth-gateway/@oauth-helpers/scripts/callback_relay_server.py)
- Tests: [test_callback_relay.py](/mnt/compose/mcp-oauth-gateway/tests/test_callback_relay.py)

### Registry format

The registry stores entries like:

```json
{
  "squirts": {
    "machine_id": "squirts",
    "target_url": "http://127.0.0.1:38935/callback/squirts",
    "description": "squirts codex callback"
  }
}
```

### Header handling

The relay strips hop-by-hop headers before returning the upstream response. It preserves the meaningful callback request data and forwards:

- method
- query string
- body
- most headers

### Health and admin auth

- `/healthz` is public
- `/api/machines/*` requires `CALLBACK_RELAY_ADMIN_TOKEN`

## Important constraints

This relay design assumes:

- Codex honors `mcp_oauth_callback_url` literally
- the machine callback listener is reachable from the relay host
- the browser callback occurs while Codex is still waiting

This relay does not solve:

- Codex exiting too quickly before the callback arrives
- machines that are not reachable from the relay host
- missing or expired OAuth state caused by stale browser tabs

## Recommended future improvements

1. Add a machine onboarding script that:
   - picks a machine ID
   - updates `~/.codex/config.toml`
   - registers the machine with the relay

2. Add a persistent `systemd --user` unit file instead of a transient unit.

3. Add relay request logging with explicit machine ID, target URL, and forwarding result.

4. Add a readiness probe that verifies both:
   - relay health
   - live reachability of the registered callback target

5. Add a cleanup or lease model so stale machine registrations can expire automatically.

## Summary

The relay makes `codex mcp login` work across machines by turning a public callback URL into a forwarded request to the live local Codex callback listener.

The key configuration rule is:

- public callback path must be unique per machine
- relay target must point to the exact callback path Codex expects on the real machine

When those two are aligned, the relay stays simple and Codex can complete OAuth without any changes to Codex itself.
