"""Unit tests for Codex MCP OAuth credential helpers."""

import json
import os
import stat
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest
from codex_mcp_credentials import (
    CodexCredentialEntry,
    compute_store_key,
    load_codex_server_url,
    upsert_credential,
)

pytestmark = pytest.mark.local_only


def test_compute_store_key_matches_known_codex_value() -> None:
    """The key format must match Codex's Rust implementation exactly."""
    assert (
        compute_store_key("arcane", "https://arcane.tootie.tv/mcp")
        == "arcane|a66557511e2868e0"
    )


def test_load_codex_server_url_reads_named_server(tmp_path) -> None:
    """Server URLs should be resolved from Codex config.toml."""
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        '\n'.join(
            [
                '[mcp_servers.arcane]',
                'url = "https://arcane.tootie.tv/mcp"',
                '',
                '[mcp_servers.pulse]',
                'url = "https://pulse.tootie.tv/mcp"',
            ]
        ),
        encoding="utf-8",
    )

    assert load_codex_server_url("arcane", config_path) == "https://arcane.tootie.tv/mcp"


def test_upsert_credential_writes_expected_payload_and_permissions(tmp_path) -> None:
    """Injected credentials should preserve existing entries and use restrictive permissions."""
    credentials_path = tmp_path / ".credentials.json"
    credentials_path.write_text(
        json.dumps({"existing|123": {"server_name": "existing"}}),
        encoding="utf-8",
    )

    key = upsert_credential(
        credentials_path,
        CodexCredentialEntry(
            server_name="arcane",
            server_url="https://arcane.tootie.tv/mcp",
            client_id="client_123",
            access_token="token_456",  # noqa: S106
            expires_at=1234567890,
            refresh_token="rotate_789",  # noqa: S106
            scopes=["openid", "profile"],
        ),
    )

    data = json.loads(credentials_path.read_text(encoding="utf-8"))
    assert data["existing|123"]["server_name"] == "existing"
    assert key == "arcane|a66557511e2868e0"
    assert data[key] == {
        "server_name": "arcane",
        "server_url": "https://arcane.tootie.tv/mcp",
        "client_id": "client_123",
        "access_token": "token_456",
        "expires_at": 1234567890,
        "refresh_token": "rotate_789",
        "scopes": ["openid", "profile"],
    }

    mode = stat.S_IMODE(os.stat(credentials_path).st_mode)
    assert mode == 0o600
