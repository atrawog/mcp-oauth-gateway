#!/usr/bin/env python3
"""Onboard Codex machines into the callback relay."""

import argparse
import json
import subprocess
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ADMIN_TOKEN_PATH = PROJECT_ROOT / ".cache" / "callback-relay" / "admin-token"
DEFAULT_RELAY_API = "http://127.0.0.1:39001"
DEFAULT_CALLBACK_PORT = 38935
DEFAULT_CALLBACK_BASE = "https://callback.tootie.tv/callback"


def run_command(command: list[str]) -> str:
    """Run a command and return stripped stdout."""
    result = subprocess.run(  # noqa: S603
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def local_tailscale_ip() -> str:
    """Return the current machine's Tailscale IPv4 address."""
    return run_command(["tailscale", "ip", "-4"]).splitlines()[0].strip()


def remote_tailscale_ip(host: str) -> str:
    """Return a remote host's Tailscale IPv4 address over SSH."""
    output = run_command(["ssh", "-o", "BatchMode=yes", host, "tailscale ip -4"])
    return output.splitlines()[0].strip()


def ensure_remote_codex_config(
    host: str,
    machine_id: str,
    callback_port: int,
    callback_url: str,
) -> None:
    """Create or update remote Codex callback configuration over SSH."""
    del machine_id
    script = f"""
from pathlib import Path
path = Path.home() / ".codex" / "config.toml"
path.parent.mkdir(parents=True, exist_ok=True)
text = path.read_text(encoding="utf-8") if path.exists() else ""
lines = text.splitlines()
keys = {{
    "mcp_oauth_callback_port": "mcp_oauth_callback_port = {callback_port}",
    "mcp_oauth_callback_url": "mcp_oauth_callback_url = \\"{callback_url}\\"",
}}
out = []
seen = set()
insert_at = 0
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith((
        "model = ",
        "model_reasoning_effort = ",
        "approvals_reviewer = ",
        "personality = ",
    )):
        insert_at = i + 1
    replaced = False
    for key, replacement in keys.items():
        if stripped.startswith(f"{{key}} = "):
            out.append(replacement)
            seen.add(key)
            replaced = True
            break
    if not replaced:
        out.append(line)
missing = [keys[k] for k in keys if k not in seen]
if missing:
    out[insert_at:insert_at] = missing
path.write_text("\\n".join(out) + "\\n", encoding="utf-8")
print(path)
"""
    run_command(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            host,
            f"python3 - <<'PY'\n{script}\nPY",
        ]
    )


def ensure_local_codex_config(machine_id: str, callback_port: int, callback_url: str) -> None:
    """Create or update local Codex callback configuration."""
    path = Path.home() / ".codex" / "config.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = text.splitlines()
    keys = {
        "mcp_oauth_callback_port": f"mcp_oauth_callback_port = {callback_port}",
        "mcp_oauth_callback_url": f'mcp_oauth_callback_url = "{callback_url}"',
    }
    out: list[str] = []
    seen: set[str] = set()
    insert_at = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(
            (
                "model = ",
                "model_reasoning_effort = ",
                "approvals_reviewer = ",
                "personality = ",
            )
        ):
            insert_at = i + 1
        replaced = False
        for key, replacement in keys.items():
            if stripped.startswith(f"{key} = "):
                out.append(replacement)
                seen.add(key)
                replaced = True
                break
        if not replaced:
            out.append(line)
    missing = [keys[key] for key in keys if key not in seen]
    if missing:
        out[insert_at:insert_at] = missing
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def register_machine(
    machine_id: str,
    target_url: str,
    description: str | None,
    relay_api: str,
) -> None:
    """Register a machine target in the relay."""
    if not ADMIN_TOKEN_PATH.exists():
        raise FileNotFoundError(f"Relay admin token not found: {ADMIN_TOKEN_PATH}")
    token = ADMIN_TOKEN_PATH.read_text(encoding="utf-8").strip()
    payload = json.dumps(
        {
            "target_url": target_url,
            "description": description or f"{machine_id} codex callback",
        }
    ).encode("utf-8")
    with httpx.Client(timeout=10.0) as client:
        response = client.put(
            f"{relay_api.rstrip('/')}/api/machines/{machine_id}",
            content=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
    if response.status_code != 200:
        raise RuntimeError(f"Relay registration failed with status {response.status_code}")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Onboard a Codex machine into the callback relay.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    current_parser = subparsers.add_parser("current", help="Onboard the current machine")
    current_parser.add_argument("machine_id")
    current_parser.add_argument("--callback-port", type=int, default=DEFAULT_CALLBACK_PORT)
    current_parser.add_argument("--callback-base", default=DEFAULT_CALLBACK_BASE)
    current_parser.add_argument("--relay-api", default=DEFAULT_RELAY_API)

    ssh_parser = subparsers.add_parser("ssh", help="Onboard a remote machine over SSH")
    ssh_parser.add_argument("host")
    ssh_parser.add_argument("--machine-id")
    ssh_parser.add_argument("--callback-port", type=int, default=DEFAULT_CALLBACK_PORT)
    ssh_parser.add_argument("--callback-base", default=DEFAULT_CALLBACK_BASE)
    ssh_parser.add_argument("--relay-api", default=DEFAULT_RELAY_API)

    return parser.parse_args()


def main() -> int:
    """Onboard a local or remote machine."""
    args = parse_args()

    if args.mode == "current":
        machine_id = args.machine_id
        callback_url = f"{args.callback_base.rstrip('/')}/{machine_id}"
        target_url = f"http://127.0.0.1:{args.callback_port}/callback/{machine_id}"
        ensure_local_codex_config(machine_id, args.callback_port, callback_url)
        register_machine(
            machine_id,
            target_url,
            f"{machine_id} codex callback loopback",
            args.relay_api,
        )
        print(f"Onboarded current machine `{machine_id}`")
        print(f"Callback URL: {callback_url}")
        print(f"Relay target: {target_url}")
        return 0

    machine_id = args.machine_id or args.host
    callback_url = f"{args.callback_base.rstrip('/')}/{machine_id}"
    remote_ip = remote_tailscale_ip(args.host)
    target_url = f"http://{remote_ip}:{args.callback_port}/callback/{machine_id}"
    ensure_remote_codex_config(args.host, machine_id, args.callback_port, callback_url)
    register_machine(
        machine_id,
        target_url,
        f"{machine_id} codex callback tailscale",
        args.relay_api,
    )
    print(f"Onboarded remote machine `{machine_id}` via SSH host `{args.host}`")
    print(f"Callback URL: {callback_url}")
    print(f"Relay target: {target_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
