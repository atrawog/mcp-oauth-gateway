# Localhost Auth Tunnel

## Purpose

This helper covers OAuth and login flows that redirect to a fixed browser-local
callback such as:

- `http://127.0.0.1:1455/...`
- `http://localhost:6274/oauth/callback`

It is for flows where the client lets you choose the callback port, but not the
callback host.

## Why This Exists

Public callback relays work only when the client can be pointed at a non-local
callback URL. Some auth flows hardcode `localhost`, which means the browser
always tries to connect to the machine where the browser is running.

The workaround is to forward the browser machine's local callback port to the
same local callback port on the remote headless machine.

## Script

The standalone helper lives at:

- [localhost-auth-tunnel.sh](/mnt/compose/mcp-oauth-gateway/@oauth-helpers/scripts/localhost-auth-tunnel.sh)

It does not depend on the repo `justfile`.

## Usage

Run this on the machine where the browser is running:

```bash
./localhost-auth-tunnel.sh up <ssh-target> <port> [port...]
```

Or run it on the headless machine and create the browser-facing listener on the
browser machine over SSH:

```bash
./localhost-auth-tunnel.sh reverse-up <browser-ssh-target> <port> [port...]
```

Examples:

```bash
./localhost-auth-tunnel.sh up dookie 1455
./localhost-auth-tunnel.sh up dookie 6274
./localhost-auth-tunnel.sh up dookie 1455 6274
./localhost-auth-tunnel.sh reverse-up steamy-wsl 1455
```

Check tunnel status:

```bash
./localhost-auth-tunnel.sh status dookie 1455
```

Stop the tunnel:

```bash
./localhost-auth-tunnel.sh down dookie 1455
```

Reverse-mode status and stop:

```bash
./localhost-auth-tunnel.sh reverse-status steamy-wsl 1455
./localhost-auth-tunnel.sh reverse-down steamy-wsl 1455
```

Print the raw `ssh -L` command without starting it:

```bash
./localhost-auth-tunnel.sh print dookie 1455
```

## Example Flows

### Codex Account Login

If the login server binds `127.0.0.1:1455` on the remote machine:

```bash
./localhost-auth-tunnel.sh up dookie 1455
```

Then complete the normal login flow in your browser. The browser's
`127.0.0.1:1455` callback will be forwarded to `dookie`.

### Run It From The Headless Machine

If you would rather run the script on the headless machine itself, use
`reverse-up` and point it at the browser machine:

```bash
./localhost-auth-tunnel.sh reverse-up browser-box 1455
```

That creates this effective SSH command:

```bash
ssh -N -R 127.0.0.1:1455:127.0.0.1:1455 browser-box
```

Meaning:

- the browser machine listens on `127.0.0.1:1455`
- traffic there is forwarded back to `127.0.0.1:1455` on the headless machine

This requires the browser machine to be running an SSH server and to allow you
to log in over SSH.

### Claude MCP

If `MCP_OAUTH_CALLBACK_PORT=6274` on the remote machine:

```bash
./localhost-auth-tunnel.sh up dookie 6274
```

Then add/login to the MCP server normally.

## Notes

- The script binds only to local `127.0.0.1` by default.
- It forwards each local port to `127.0.0.1:<same-port>` on the remote machine.
- It uses SSH control sockets so the tunnel can be checked and shut down cleanly.
- State is stored under `${XDG_STATE_HOME:-$HOME/.local/state}/localhost-auth-tunnel/`.
- `reverse-*` commands require SSH access from the headless machine to the browser machine.
