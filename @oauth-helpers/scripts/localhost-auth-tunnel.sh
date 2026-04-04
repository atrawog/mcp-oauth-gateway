#!/usr/bin/env bash

set -euo pipefail

SCRIPT_NAME="$(basename "$0")"
STATE_ROOT="${XDG_STATE_HOME:-$HOME/.local/state}/localhost-auth-tunnel"
SOCKET_DIR="$STATE_ROOT/sockets"
LOG_DIR="$STATE_ROOT/logs"

mkdir -p "$SOCKET_DIR" "$LOG_DIR"

usage() {
  cat <<'EOF'
Usage:
  localhost-auth-tunnel.sh up <ssh-target> <port> [port...]
  localhost-auth-tunnel.sh reverse-up <ssh-target> <port> [port...]
  localhost-auth-tunnel.sh down <ssh-target> <port> [port...]
  localhost-auth-tunnel.sh reverse-down <ssh-target> <port> [port...]
  localhost-auth-tunnel.sh status <ssh-target> <port> [port...]
  localhost-auth-tunnel.sh reverse-status <ssh-target> <port> [port...]
  localhost-auth-tunnel.sh print <ssh-target> <port> [port...]
  localhost-auth-tunnel.sh reverse-print <ssh-target> <port> [port...]

Description:
  Manage SSH local forwards for OAuth/login flows that redirect to browser-local
  localhost ports such as:

    http://127.0.0.1:1455/...
    http://localhost:6274/oauth/callback

  Run this on the machine where the browser is running. The script forwards the
  local browser-facing port to the same localhost port on the remote machine.
  For reverse-* actions, run this on the headless machine. The script opens the
  browser-facing listener on the SSH target and forwards it back to this machine.

Examples:
  localhost-auth-tunnel.sh up dookie 1455
  localhost-auth-tunnel.sh reverse-up steamy-wsl 1455
  localhost-auth-tunnel.sh up dookie 6274
  localhost-auth-tunnel.sh up dookie 1455 6274
  localhost-auth-tunnel.sh status dookie 1455
  localhost-auth-tunnel.sh down dookie 1455

Behavior:
  - Uses SSH ControlMaster sockets so the tunnel can be checked and stopped.
  - Binds only to 127.0.0.1 on the local machine.
  - Forwards each local port to 127.0.0.1:<same-port> on the remote machine.
  - reverse-* uses SSH remote forwarding (-R) instead of local forwarding (-L).

Environment:
  LOCALHOST_AUTH_TUNNEL_BIND_HOST   Local bind host. Default: 127.0.0.1
  LOCALHOST_AUTH_TUNNEL_REMOTE_HOST Remote host for the forwarded port. Default: 127.0.0.1
  LOCALHOST_AUTH_TUNNEL_SSH_OPTS    Extra ssh options, appended as a raw string

Notes:
  - Use fixed callback ports in the client when possible.
  - This script does not start the auth flow itself; it only manages the tunnel.
EOF
}

die() {
  echo "$SCRIPT_NAME: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

sanitize_target() {
  printf '%s' "$1" | tr '/:@ ' '____'
}

validate_port() {
  local port="$1"
  [[ "$port" =~ ^[0-9]+$ ]] || die "invalid port: $port"
  (( port >= 1 && port <= 65535 )) || die "port out of range: $port"
}

socket_path() {
  local target="$1"
  local port="$2"
  local safe_target
  safe_target="$(sanitize_target "$target")"
  printf '%s/%s-%s.sock' "$SOCKET_DIR" "$safe_target" "$port"
}

log_path() {
  local target="$1"
  local port="$2"
  local safe_target
  safe_target="$(sanitize_target "$target")"
  printf '%s/%s-%s.log' "$LOG_DIR" "$safe_target" "$port"
}

ssh_extra_opts=()
if [[ -n "${LOCALHOST_AUTH_TUNNEL_SSH_OPTS:-}" ]]; then
  # shellcheck disable=SC2206
  ssh_extra_opts=(${LOCALHOST_AUTH_TUNNEL_SSH_OPTS})
fi

BIND_HOST="${LOCALHOST_AUTH_TUNNEL_BIND_HOST:-127.0.0.1}"
REMOTE_HOST="${LOCALHOST_AUTH_TUNNEL_REMOTE_HOST:-127.0.0.1}"

start_tunnel() {
  local target="$1"
  local port="$2"
  local mode="${3:-local}"
  local socket
  local log_file
  local forward_flag
  local forward_spec

  socket="$(socket_path "$target" "$port")"
  log_file="$(log_path "$target" "$port")"

  if ssh -S "$socket" -O check "$target" >/dev/null 2>&1; then
    echo "already running: $target port $port"
    return 0
  fi

  rm -f "$socket"

  if [[ "$mode" == "reverse" ]]; then
    forward_flag="-R"
    forward_spec="${BIND_HOST}:${port}:${REMOTE_HOST}:${port}"
  else
    forward_flag="-L"
    forward_spec="${BIND_HOST}:${port}:${REMOTE_HOST}:${port}"
  fi

  ssh \
    -fN \
    -M \
    -S "$socket" \
    -o BatchMode=yes \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    "${ssh_extra_opts[@]}" \
    "$forward_flag" "$forward_spec" \
    "$target" \
    >>"$log_file" 2>&1

  if [[ "$mode" == "reverse" ]]; then
    echo "started: $target remote ${BIND_HOST}:${port} -> local ${REMOTE_HOST}:${port}"
  else
    echo "started: $target ${BIND_HOST}:${port} -> ${REMOTE_HOST}:${port}"
  fi
}

stop_tunnel() {
  local target="$1"
  local port="$2"
  local socket

  socket="$(socket_path "$target" "$port")"

  if ssh -S "$socket" -O exit "$target" >/dev/null 2>&1; then
    rm -f "$socket"
    echo "stopped: $target port $port"
    return 0
  fi

  echo "not running: $target port $port"
}

status_tunnel() {
  local target="$1"
  local port="$2"
  local mode="${3:-local}"
  local socket

  socket="$(socket_path "$target" "$port")"

  if ssh -S "$socket" -O check "$target" >/dev/null 2>&1; then
    if [[ "$mode" == "reverse" ]]; then
      echo "running: $target remote ${BIND_HOST}:${port} -> local ${REMOTE_HOST}:${port}"
    else
      echo "running: $target ${BIND_HOST}:${port} -> ${REMOTE_HOST}:${port}"
    fi
  else
    echo "stopped: $target port $port"
    return 1
  fi
}

print_command() {
  local target="$1"
  local port="$2"
  local mode="${3:-local}"

  if [[ "$mode" == "reverse" ]]; then
    printf 'ssh -N -R %s:%s:%s:%s %s\n' \
      "$BIND_HOST" \
      "$port" \
      "$REMOTE_HOST" \
      "$port" \
      "$target"
  else
    printf 'ssh -N -L %s:%s:%s:%s %s\n' \
      "$BIND_HOST" \
      "$port" \
      "$REMOTE_HOST" \
      "$port" \
      "$target"
  fi
}

main() {
  require_cmd ssh

  (( $# >= 3 )) || {
    usage
    exit 1
  }

  local action="$1"
  shift
  local target="$1"
  shift

  for port in "$@"; do
    validate_port "$port"
    case "$action" in
      up)
        start_tunnel "$target" "$port" "local"
        ;;
      reverse-up)
        start_tunnel "$target" "$port" "reverse"
        ;;
      down)
        stop_tunnel "$target" "$port"
        ;;
      reverse-down)
        stop_tunnel "$target" "$port"
        ;;
      status)
        status_tunnel "$target" "$port" "local"
        ;;
      reverse-status)
        status_tunnel "$target" "$port" "reverse"
        ;;
      print)
        print_command "$target" "$port" "local"
        ;;
      reverse-print)
        print_command "$target" "$port" "reverse"
        ;;
      -h|--help|help)
        usage
        return 0
        ;;
      *)
        die "unknown action: $action"
        ;;
    esac
  done
}

main "$@"
