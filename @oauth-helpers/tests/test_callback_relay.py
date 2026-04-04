"""Local tests for the callback relay service."""

import json
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from callback_relay import RelayRegistry, create_app

pytestmark = pytest.mark.local_only


@pytest.mark.asyncio
async def test_register_and_forward_callback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The relay should persist machine targets and proxy callback requests."""
    monkeypatch.setenv("CALLBACK_RELAY_ADMIN_TOKEN", "relay-secret")
    registry = RelayRegistry(tmp_path / "registry.json")

    captured: dict[str, str] = {}
    target_app = FastAPI()

    @target_app.api_route("/callback", methods=["GET", "POST"])
    async def callback(request: Request) -> JSONResponse:
        captured["path"] = request.url.path
        captured["query"] = request.url.query
        captured["machine"] = request.headers["x-callback-relay-machine-id"]
        return JSONResponse({"ok": True, "query": request.url.query})

    relay_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=target_app),
        base_url="http://machine.internal",
    )
    relay_app = create_app(registry, relay_client=relay_client)
    relay_http = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=relay_app),
        base_url="https://callback.tootie.tv",
    )

    try:
        register_response = await relay_http.put(
            "/api/machines/squirts",
            headers={"Authorization": "Bearer relay-secret"},
            json={
                "target_url": "http://machine.internal/callback",
                "description": "squirts codex box",
            },
        )
        assert register_response.status_code == 200

        callback_response = await relay_http.get(
            "/callback/squirts",
            params={"code": "abc123", "state": "xyz789"},
        )
        assert callback_response.status_code == 200
        assert callback_response.json() == {"ok": True, "query": "code=abc123&state=xyz789"}
        assert captured == {
            "path": "/callback",
            "query": "code=abc123&state=xyz789",
            "machine": "squirts",
        }

        persisted = json.loads((tmp_path / "registry.json").read_text(encoding="utf-8"))
        assert persisted["squirts"]["target_url"] == "http://machine.internal/callback"
    finally:
        await relay_http.aclose()
        await relay_client.aclose()


@pytest.mark.asyncio
async def test_register_requires_admin_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Administrative endpoints should reject missing or invalid bearer tokens."""
    monkeypatch.setenv("CALLBACK_RELAY_ADMIN_TOKEN", "relay-secret")
    relay_app = create_app(RelayRegistry(tmp_path / "registry.json"))
    relay_http = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=relay_app),
        base_url="https://callback.tootie.tv",
    )

    try:
        response = await relay_http.put(
            "/api/machines/squirts",
            json={"target_url": "http://machine.internal/callback"},
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "invalid relay admin token"}
    finally:
        await relay_http.aclose()
