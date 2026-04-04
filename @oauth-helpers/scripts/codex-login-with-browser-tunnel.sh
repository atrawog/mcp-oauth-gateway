#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TUNNEL_SCRIPT="${LOCALHOST_AUTH_TUNNEL_PATH:-$SCRIPT_DIR/localhost-auth-tunnel.sh}"
DEFAULT_PORT="${CODEX_LOGIN_CALLBACK_PORT:-1455}"

usage() {
  cat <<'EOF'
Usage:
  codex-login-with-browser-tunnel.sh <browser-ssh-target> [callback-port]
  codex-login-with-browser-tunnel.sh <browser-ssh-target> [callback-port] -- <extra codex login args...>

Description:
  Opens a reverse SSH tunnel so the browser machine's localhost callback port
  forwards back to this machine, then runs `codex login`.

  This is for auth flows where Codex binds a fixed localhost callback port,
  such as account login on 127.0.0.1:1455.

Examples:
  codex-login-with-browser-tunnel.sh steamy-wsl
  codex-login-with-browser-tunnel.sh steamy-wsl 1455
  codex-login-with-browser-tunnel.sh steamy-wsl 1455 -- --device-auth

Requirements:
  - Run this on the headless machine where `codex login` will run.
  - The browser machine must accept SSH connections from this machine.
  - The tunnel helper must be available at:
      ./localhost-auth-tunnel.sh
    or via LOCALHOST_AUTH_TUNNEL_PATH.
EOF
}

die() {
  echo "$(basename "$0"): $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

main() {
  require_cmd codex
  require_cmd bash

  [[ -x "$TUNNEL_SCRIPT" ]] || die "tunnel helper not found or not executable: $TUNNEL_SCRIPT"

  (($# >= 1)) || {
    usage
    exit 1
  }

  browser_target="$1"
  shift

  callback_port="$DEFAULT_PORT"
  if (($# >= 1)) && [[ "$1" != "--" ]]; then
    callback_port="$1"
    shift
  fi

  [[ "$callback_port" =~ ^[0-9]+$ ]] || die "invalid callback port: $callback_port"

  local codex_args=()
  if (($# > 0)); then
    [[ "$1" == "--" ]] || die "unexpected argument: $1"
    shift
    codex_args=("$@")
  fi

  bash "$TUNNEL_SCRIPT" reverse-up "$browser_target" "$callback_port"

  cleanup() {
    bash "$TUNNEL_SCRIPT" reverse-down "$browser_target" "$callback_port" >/dev/null 2>&1 || true
  }
  trap cleanup EXIT INT TERM

  echo "Reverse tunnel ready: ${browser_target}:127.0.0.1:${callback_port} -> local 127.0.0.1:${callback_port}"
  echo "Starting: codex login ${codex_args[*]}"

  codex login "${codex_args[@]}"
}

main "$@"
