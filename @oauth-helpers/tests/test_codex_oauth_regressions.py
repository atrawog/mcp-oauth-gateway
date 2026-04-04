"""Local regressions for Codex-facing OAuth discovery and token audience behavior."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

pytestmark = pytest.mark.local_only

PACKAGE_SRC = Path(__file__).resolve().parents[2] / "mcp-oauth-dynamicclient" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from mcp_oauth_dynamicclient.async_resource_protector import AsyncResourceProtector  # noqa: E402
from mcp_oauth_dynamicclient.auth_authlib import AuthManager  # noqa: E402
from mcp_oauth_dynamicclient.config import Settings  # noqa: E402
from mcp_oauth_dynamicclient.keys import RSAKeyManager  # noqa: E402


class FakeRedis:
    """Tiny async Redis substitute for local token tests."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def setex(self, key: str, ttl: int, value: str) -> None:
        del ttl
        self.values[key] = value

    async def sadd(self, key: str, *members: str) -> int:
        del key, members
        return 0


def _build_settings(*, algorithm: str = "HS256") -> Settings:
    """Create isolated settings for local-only tests."""
    return Settings.model_validate(
        {
            "github_client_id": "github-client",
            "github_client_secret": "github-secret",
            "OAUTH_JWT_SECRET": "x" * 64,
            "OAUTH_JWT_ALGORITHM": algorithm,
            "base_domain": "tootie.tv",
            "auth_subdomain": "mcp-auth",
            "redis_url": "redis://localhost:6379/0",
            "redis_password": None,
            "OAUTH_ACCESS_TOKEN_LIFETIME": 3600,
            "OAUTH_REFRESH_TOKEN_LIFETIME": 7200,
            "OAUTH_SESSION_TIMEOUT": 3600,
            "OAUTH_CLIENT_LIFETIME": 7200,
            "OAUTH_DEVICE_CODE_LIFETIME": 600,
            "OAUTH_DEVICE_CODE_INTERVAL": 1,
            "OAUTH_ALLOWED_GITHUB_USERS": "*",
            "OAUTH_MCP_PROTOCOL_VERSION": "2025-06-18",
        }
    )


def _decode_payload(token: str) -> dict[str, object]:
    """Decode the JWT payload without verifying the signature."""
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def _build_request(headers: dict[str, str]) -> Request:
    """Construct a minimal ASGI request for direct validator calls."""
    raw_headers = [(key.lower().encode(), value.encode()) for key, value in headers.items()]
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": "/mcp",
        "raw_path": b"/mcp",
        "query_string": b"",
        "headers": raw_headers,
        "client": ("127.0.0.1", 12345),
        "server": ("axon.tootie.tv", 443),
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_codex_challenge_uses_resource_metadata_and_configured_auth_subdomain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The RFC challenge must advertise the correct auth server and PRM URL."""

    class FakeValidator:
        def __init__(self, settings, redis_client, key_manager) -> None:
            del settings, redis_client, key_manager

        def request_invalid(self, request: Request) -> str | None:
            del request
            return None

        async def authenticate_token(self, token_string: str) -> dict[str, object] | None:
            del token_string
            return None

    monkeypatch.setattr(
        "mcp_oauth_dynamicclient.async_resource_protector.JWTBearerTokenValidator",
        FakeValidator,
    )

    protector = AsyncResourceProtector(
        _build_settings(),
        redis_client=SimpleNamespace(),
        key_manager=SimpleNamespace(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await protector.validate_request(
            _build_request(
                {
                    "host": "axon.tootie.tv",
                    "x-forwarded-proto": "https",
                    "authorization": "Bearer bad-token",
                }
            ),
            resource="https://axon.tootie.tv",
        )

    challenge = exc_info.value.headers["WWW-Authenticate"]
    assert exc_info.value.status_code == 401
    assert (
        'as_uri="https://mcp-auth.tootie.tv/.well-known/oauth-authorization-server"'
        in challenge
    )
    assert (
        'resource_metadata="https://axon.tootie.tv/.well-known/oauth-protected-resource"'
        in challenge
    )
    assert "resource_uri=" not in challenge
    assert "https://auth.tootie.tv/" not in challenge


@pytest.mark.asyncio
async def test_codex_fallback_audience_uses_configured_auth_subdomain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tokens minted without an RFC 8707 resource must still use the configured auth host."""
    original_load_or_generate_keys = RSAKeyManager.load_or_generate_keys
    monkeypatch.setattr(RSAKeyManager, "load_or_generate_keys", lambda self: None)
    try:
        manager = AuthManager(_build_settings())
    finally:
        RSAKeyManager.load_or_generate_keys = original_load_or_generate_keys

    token = await manager.create_jwt_token(
        {
            "sub": "user-123",
            "client_id": "client-123",
            "scope": "mcp:read",
        },
        redis_client=FakeRedis(),
    )

    payload = _decode_payload(token)
    assert payload["aud"] == "https://mcp-auth.tootie.tv"
