# Codex Login With Browser Tunnel

## Purpose

This helper wraps `codex login` for headless machines when the login flow uses
a fixed localhost callback port such as `127.0.0.1:1455`.

It opens a reverse SSH tunnel to the browser machine, then runs `codex login`
locally on the headless machine.

## Script

- [codex-login-with-browser-tunnel.sh](/mnt/compose/mcp-oauth-gateway/@oauth-helpers/scripts/codex-login-with-browser-tunnel.sh)

## Usage

Run this on the headless machine:

```bash
./codex-login-with-browser-tunnel.sh <browser-ssh-target> [callback-port]
```

Examples:

```bash
./codex-login-with-browser-tunnel.sh steamy-wsl
./codex-login-with-browser-tunnel.sh steamy-wsl 1455
./codex-login-with-browser-tunnel.sh steamy-wsl 1455 -- --device-auth
```

## Behavior

The wrapper:

1. Opens a reverse tunnel using [localhost-auth-tunnel.sh](/mnt/compose/mcp-oauth-gateway/@oauth-helpers/scripts/localhost-auth-tunnel.sh)
2. Runs `codex login`
3. Tears the tunnel down on exit

Default callback port:

- `1455`

Override with:

- positional `callback-port`
- or `CODEX_LOGIN_CALLBACK_PORT`

## Requirements

- Run it on the headless machine where `codex login` runs.
- The browser machine must accept SSH connections from that machine.
- The tunnel helper must be available locally.
