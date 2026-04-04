#!/usr/bin/env python3
"""Helpers for managing Codex MCP OAuth credentials."""

import hashlib
import json
import os
import stat
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CODEX_HOME = Path.home() / ".codex"
DEFAULT_CREDENTIALS_FILENAME = ".credentials.json"
DEFAULT_CONFIG_FILENAME = "config.toml"


@dataclass(slots=True)
class CodexCredentialEntry:
    """Serializable representation of a Codex MCP OAuth credential entry."""

    server_name: str
    server_url: str
    client_id: str
    access_token: str
    expires_at: int | None = None
    refresh_token: str | None = None
    scopes: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the entry to the JSON payload Codex stores on disk."""
        return {
            "server_name": self.server_name,
            "server_url": self.server_url,
            "client_id": self.client_id,
            "access_token": self.access_token,
            "expires_at": self.expires_at,
            "refresh_token": self.refresh_token,
            "scopes": self.scopes or [],
        }


def compute_store_key(server_name: str, server_url: str) -> str:
    """Return the deterministic Codex credential-store key for a streamable HTTP MCP server."""
    payload = {"type": "http", "url": server_url, "headers": {}}
    serialized = json.dumps(payload, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
    return f"{server_name}|{digest}"


def resolve_codex_home(codex_home: str | Path | None = None) -> Path:
    """Resolve the effective Codex home directory."""
    if codex_home is not None:
        return Path(codex_home).expanduser()

    env_value = os.getenv("CODEX_HOME")
    if env_value:
        return Path(env_value).expanduser()

    return DEFAULT_CODEX_HOME


def credentials_file_path(codex_home: str | Path | None = None) -> Path:
    """Return the path to Codex's file-backed MCP credential store."""
    return resolve_codex_home(codex_home) / DEFAULT_CREDENTIALS_FILENAME


def config_file_path(codex_home: str | Path | None = None) -> Path:
    """Return the path to Codex's configuration file."""
    return resolve_codex_home(codex_home) / DEFAULT_CONFIG_FILENAME


def load_credentials_store(path: str | Path) -> dict[str, Any]:
    """Load the existing Codex credential store from disk."""
    credentials_path = Path(path)
    if not credentials_path.exists():
        return {}

    contents = credentials_path.read_text(encoding="utf-8")
    if not contents.strip():
        return {}

    data = json.loads(contents)
    if not isinstance(data, dict):
        raise ValueError(f"Codex credentials file must contain a JSON object: {credentials_path}")

    return data


def write_credentials_store(path: str | Path, store: dict[str, Any]) -> None:
    """Write the Codex credential store with restrictive permissions."""
    credentials_path = Path(path)
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(store, separators=(",", ":"))
    credentials_path.write_text(serialized, encoding="utf-8")
    os.chmod(credentials_path, stat.S_IRUSR | stat.S_IWUSR)


def upsert_credential(
    path: str | Path,
    entry: CodexCredentialEntry,
) -> str:
    """Insert or update a single Codex MCP credential entry and return its key."""
    key = compute_store_key(entry.server_name, entry.server_url)
    store = load_credentials_store(path)
    store[key] = entry.to_dict()
    write_credentials_store(path, store)
    return key


def load_codex_server_url(server_name: str, path: str | Path) -> str:
    """Look up an MCP server URL from a Codex config.toml file."""
    config_path = Path(path)
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    mcp_servers = config.get("mcp_servers")
    if not isinstance(mcp_servers, dict):
        raise ValueError(f"No [mcp_servers] section found in {config_path}")

    server_config = mcp_servers.get(server_name)
    if not isinstance(server_config, dict):
        raise ValueError(f"MCP server `{server_name}` not found in {config_path}")

    server_url = server_config.get("url")
    if not isinstance(server_url, str) or not server_url:
        raise ValueError(f"MCP server `{server_name}` is missing a URL in {config_path}")

    return server_url
