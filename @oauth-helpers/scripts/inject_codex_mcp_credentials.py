#!/usr/bin/env python3
"""Inject MCP OAuth credentials into Codex's file-backed credential store."""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

try:
    from scripts.codex_mcp_credentials import (
        CodexCredentialEntry,
        config_file_path,
        credentials_file_path,
        load_codex_server_url,
        upsert_credential,
    )
except ModuleNotFoundError:
    from codex_mcp_credentials import (
        CodexCredentialEntry,
        config_file_path,
        credentials_file_path,
        load_codex_server_url,
        upsert_credential,
    )

ENV_FILE = Path(__file__).parent.parent / ".env"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Write MCP OAuth credentials into Codex's file-backed credential store.",
    )
    parser.add_argument("server_name", help="Codex MCP server name, for example `arcane`")
    parser.add_argument(
        "--server-url",
        help="Override the MCP server URL instead of reading it from Codex config",
    )
    parser.add_argument(
        "--config-path",
        type=Path,
        help="Path to Codex config.toml. Defaults to CODEX_HOME/config.toml",
    )
    parser.add_argument(
        "--credentials-path",
        type=Path,
        help="Path to Codex .credentials.json. Defaults to CODEX_HOME/.credentials.json",
    )
    parser.add_argument(
        "--codex-home",
        type=Path,
        help="Override CODEX_HOME for config and credential-store resolution",
    )
    parser.add_argument("--client-id", help="OAuth client ID. Defaults to MCP_CLIENT_ID in .env")
    parser.add_argument(
        "--access-token",
        help="OAuth access token. Defaults to MCP_CLIENT_ACCESS_TOKEN in .env",
    )
    parser.add_argument(
        "--refresh-token",
        help="OAuth refresh token. Defaults to MCP_CLIENT_REFRESH_TOKEN in .env",
    )
    parser.add_argument(
        "--expires-at",
        type=int,
        help="Unix epoch expiry in milliseconds. Optional.",
    )
    parser.add_argument(
        "--scopes",
        help="Comma-separated OAuth scopes. Optional; defaults to MCP_CLIENT_SCOPES if present.",
    )
    return parser.parse_args()


def load_scopes(raw_scopes: str | None) -> list[str]:
    """Parse a comma-separated scope string into a normalized list."""
    if not raw_scopes:
        return []
    return [scope.strip() for scope in raw_scopes.split(",") if scope.strip()]


def main() -> int:
    """Inject OAuth credentials for a configured Codex MCP server."""
    load_dotenv(ENV_FILE)
    args = parse_args()

    client_id = args.client_id or os.getenv("MCP_CLIENT_ID") or os.getenv("OAUTH_CLIENT_ID")
    access_token = args.access_token or os.getenv("MCP_CLIENT_ACCESS_TOKEN") or os.getenv(
        "OAUTH_ACCESS_TOKEN"
    )
    refresh_token = args.refresh_token or os.getenv("MCP_CLIENT_REFRESH_TOKEN") or os.getenv(
        "OAUTH_REFRESH_TOKEN"
    )
    scopes = load_scopes(args.scopes or os.getenv("MCP_CLIENT_SCOPES"))

    if not client_id:
        print(
            "ERROR: missing OAuth client ID. Set MCP_CLIENT_ID or pass --client-id.",
            file=sys.stderr,
        )
        return 1

    if not access_token:
        print(
            "ERROR: missing OAuth access token. "
            "Set MCP_CLIENT_ACCESS_TOKEN or pass --access-token.",
            file=sys.stderr,
        )
        return 1

    codex_home = args.codex_home
    config_path = args.config_path or config_file_path(codex_home)
    credentials_path = args.credentials_path or credentials_file_path(codex_home)
    server_url = args.server_url or load_codex_server_url(args.server_name, config_path)

    entry = CodexCredentialEntry(
        server_name=args.server_name,
        server_url=server_url,
        client_id=client_id,
        access_token=access_token,
        expires_at=args.expires_at,
        refresh_token=refresh_token,
        scopes=scopes,
    )
    key = upsert_credential(credentials_path, entry)

    print(f"Injected Codex MCP OAuth credentials for `{args.server_name}`")
    print(f"Credentials file: {credentials_path}")
    print(f"Store key: {key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
