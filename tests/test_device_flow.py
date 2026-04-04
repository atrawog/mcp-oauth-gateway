"""Local tests for OAuth device authorization flow."""

import json
import sys
from fnmatch import fnmatch
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi import FastAPI

pytestmark = pytest.mark.local_only

PACKAGE_SRC = Path(__file__).resolve().parents[1] / "mcp-oauth-dynamicclient" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from mcp_oauth_dynamicclient.auth_authlib import AuthManager  # noqa: E402
from mcp_oauth_dynamicclient.config import Settings  # noqa: E402
from mcp_oauth_dynamicclient.keys import RSAKeyManager  # noqa: E402
from mcp_oauth_dynamicclient.routes import DEVICE_CODE_GRANT, create_oauth_router  # noqa: E402


class FakeRedis:
    """Very small async Redis replacement for router tests."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.sets: dict[str, set[str]] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str) -> None:
        self.values[key] = value

    async def setex(self, key: str, ttl: int, value: str) -> None:
        del ttl
        self.values[key] = value

    async def delete(self, *keys: str) -> int:
        deleted = 0
        for key in keys:
            deleted += int(self.values.pop(key, None) is not None)
            self.sets.pop(key, None)
        return deleted

    async def exists(self, key: str) -> int:
        return int(key in self.values or key in self.sets)

    async def sadd(self, key: str, *members: str) -> int:
        bucket = self.sets.setdefault(key, set())
        before = len(bucket)
        bucket.update(members)
        return len(bucket) - before

    async def srem(self, key: str, *members: str) -> int:
        bucket = self.sets.get(key, set())
        before = len(bucket)
        for member in members:
            bucket.discard(member)
        return before - len(bucket)

    async def keys(self, pattern: str) -> list[str]:
        return [key for key in self.values if fnmatch(key, pattern)]


def _error_code(response: httpx.Response) -> str:
    """Extract the OAuth error code from local FastAPI responses."""
    payload = response.json()
    if "error" in payload:
        return payload["error"]
    return payload["detail"]["error"]


def _build_settings() -> Settings:
    """Create settings for local router tests."""
    return Settings.model_validate(
        {
            "github_client_id": "github-client",
            "github_client_secret": "github-secret",
            "OAUTH_JWT_SECRET": "x" * 64,
            "OAUTH_JWT_ALGORITHM": "RS256",
            "base_domain": "example.test",
            "auth_subdomain": "auth",
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


async def _create_test_client() -> tuple[httpx.AsyncClient, FakeRedis]:
    """Create an ASGI client backed by the OAuth router."""
    settings = _build_settings()
    fake_redis = FakeRedis()
    original_load_or_generate_keys = RSAKeyManager.load_or_generate_keys
    RSAKeyManager.load_or_generate_keys = lambda self: None  # type: ignore[assignment]
    try:
        auth_manager = AuthManager(settings)
    finally:
        RSAKeyManager.load_or_generate_keys = original_load_or_generate_keys

    async def fake_exchange_github_code(code: str) -> dict[str, object]:
        del code
        return {
            "id": 12345,
            "login": "headless-user",
            "email": "headless@example.test",
            "name": "Headless User",
        }

    async def fake_create_jwt_token(
        claims: dict,
        redis_client: FakeRedis,
        resource: str | None = None,
    ) -> str:
        del claims, redis_client, resource
        return "access-token"

    async def fake_create_refresh_token(user_data: dict, redis_client: FakeRedis) -> str:
        del user_data, redis_client
        return "refresh-token"

    auth_manager.exchange_github_code = fake_exchange_github_code  # type: ignore[method-assign]
    auth_manager.create_jwt_token = fake_create_jwt_token  # type: ignore[method-assign]
    auth_manager.create_refresh_token = fake_create_refresh_token  # type: ignore[method-assign]

    app = FastAPI()
    app.include_router(
        create_oauth_router(
            settings=settings,
            redis_manager=SimpleNamespace(client=fake_redis),
            auth_manager=auth_manager,
        )
    )

    transport = httpx.ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url="https://auth.example.test")

    await fake_redis.set(
        "oauth:client:headless-client",
        json.dumps(
            {
                "client_id": "headless-client",
                "client_secret": "",
                "redirect_uris": json.dumps([]),
                "client_name": "Headless Client",
                "scope": "openid profile email",
                "response_types": json.dumps(["code"]),
                "grant_types": json.dumps(
                    ["authorization_code", "refresh_token", DEVICE_CODE_GRANT]
                ),
                "token_endpoint_auth_method": "none",
            }
        ),
    )

    return client, fake_redis


@pytest.mark.asyncio
async def test_device_metadata_advertised() -> None:
    """Server metadata should advertise device authorization support."""
    client, _redis = await _create_test_client()
    try:
        response = await client.get("/.well-known/oauth-authorization-server")
    finally:
        await client.aclose()

    assert response.status_code == 200
    payload = response.json()
    assert payload["device_authorization_endpoint"] == "https://auth.example.test/device/code"
    assert DEVICE_CODE_GRANT in payload["grant_types_supported"]


@pytest.mark.asyncio
async def test_device_flow_end_to_end() -> None:
    """A headless client should be able to complete the full device flow."""
    client, fake_redis = await _create_test_client()
    try:
        device_response = await client.post(
            "/device/code",
            data={
                "client_id": "headless-client",
                "scope": "openid profile email",
                "resource": "https://mcp.example.test/mcp",
            },
        )
        assert device_response.status_code == 200
        device_payload = device_response.json()
        assert device_payload["verification_uri"] == "https://auth.example.test/activate"
        assert "user_code" in device_payload

        pending_response = await client.post(
            "/token",
            data={
                "grant_type": DEVICE_CODE_GRANT,
                "client_id": "headless-client",
                "device_code": device_payload["device_code"],
            },
        )
        assert pending_response.status_code == 400
        assert _error_code(pending_response) == "authorization_pending"

        activate_response = await client.post(
            "/activate",
            data={"user_code": device_payload["user_code"]},
            follow_redirects=False,
        )
        assert activate_response.status_code in {302, 307}

        parsed_redirect = urlparse(activate_response.headers["location"])
        assert parsed_redirect.netloc == "github.com"
        github_state = parse_qs(parsed_redirect.query)["state"][0]

        callback_response = await client.get(
            "/callback",
            params={"code": "github-code", "state": github_state},
            follow_redirects=False,
        )
        assert callback_response.status_code in {302, 307}
        assert callback_response.headers["location"] == "https://auth.example.test/device/success"

        device_key = f"oauth:device:{device_payload['device_code']}"
        stored_device = json.loads(fake_redis.values[device_key])
        stored_device["last_polled_at"] = 0
        fake_redis.values[device_key] = json.dumps(stored_device)

        token_response = await client.post(
            "/token",
            data={
                "grant_type": DEVICE_CODE_GRANT,
                "client_id": "headless-client",
                "device_code": device_payload["device_code"],
                "resource": "https://mcp.example.test/mcp",
            },
        )
        assert token_response.status_code == 200
        assert token_response.json() == {
            "access_token": "access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "refresh-token",
            "scope": "openid profile email",
        }

        consumed_response = await client.post(
            "/token",
            data={
                "grant_type": DEVICE_CODE_GRANT,
                "client_id": "headless-client",
                "device_code": device_payload["device_code"],
            },
        )
        assert consumed_response.status_code == 400
        assert _error_code(consumed_response) == "expired_token"
    finally:
        await client.aclose()
