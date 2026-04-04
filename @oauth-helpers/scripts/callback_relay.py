#!/usr/bin/env python3
"""Callback relay service for headless Codex MCP OAuth flows."""

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

LOGGER = logging.getLogger(__name__)
DEFAULT_REGISTRY_PATH = Path(".cache/callback-relay/registry.json")
HOP_BY_HOP_HEADERS = {
    "connection",
    "content-length",
    "host",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


@dataclass(slots=True)
class MachineTarget:
    """Serializable machine target used by the relay registry."""

    machine_id: str
    target_url: str
    description: str | None = None


class MachineRegistration(BaseModel):
    """Payload used to register or update a machine target."""

    model_config = ConfigDict(extra="forbid")

    target_url: HttpUrl
    description: str | None = Field(default=None, max_length=200)


class RelayRegistry:
    """Persistent file-backed registry of callback relay targets."""

    def __init__(self, path: str | Path) -> None:
        """Create a registry backed by the provided JSON file path."""
        self.path = Path(path)

    def load(self) -> dict[str, MachineTarget]:
        """Load all registered machine targets."""
        if not self.path.exists():
            return {}

        contents = self.path.read_text(encoding="utf-8").strip()
        if not contents:
            return {}

        data = json.loads(contents)
        if not isinstance(data, dict):
            raise ValueError(f"Relay registry must be a JSON object: {self.path}")

        registry: dict[str, MachineTarget] = {}
        for machine_id, entry in data.items():
            if not isinstance(entry, dict):
                raise ValueError(f"Relay registry entry must be an object: {machine_id}")
            registry[machine_id] = MachineTarget(
                machine_id=machine_id,
                target_url=str(entry["target_url"]),
                description=entry.get("description"),
            )
        return registry

    def get(self, machine_id: str) -> MachineTarget | None:
        """Return a single machine target if it exists."""
        return self.load().get(machine_id)

    def upsert(self, machine_id: str, registration: MachineRegistration) -> MachineTarget:
        """Insert or update a machine target and persist it."""
        registry = self.load()
        target = MachineTarget(
            machine_id=machine_id,
            target_url=str(registration.target_url),
            description=registration.description,
        )
        registry[machine_id] = target
        self._write(registry)
        return target

    def delete(self, machine_id: str) -> bool:
        """Delete a machine target if present."""
        registry = self.load()
        deleted = registry.pop(machine_id, None) is not None
        if deleted:
            self._write(registry)
        return deleted

    def _write(self, registry: dict[str, MachineTarget]) -> None:
        """Persist the machine registry to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            machine_id: asdict(target)
            for machine_id, target in sorted(registry.items(), key=lambda item: item[0])
        }
        self.path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")


def _admin_token() -> str | None:
    """Return the configured relay admin token if one is set."""
    return os.getenv("CALLBACK_RELAY_ADMIN_TOKEN")


def require_admin_token(authorization: str | None = Header(default=None)) -> None:
    """Enforce bearer-token auth on relay administration endpoints."""
    expected = _admin_token()
    if not expected:
        raise HTTPException(status_code=503, detail="relay admin token is not configured")

    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or token != expected:
        raise HTTPException(status_code=401, detail="invalid relay admin token")


def _build_forward_url(
    target_url: str,
    suffix_path: str,
    query_items: list[tuple[str, str]],
) -> str:
    """Build the forwarded target URL for a callback request."""
    parts = urlsplit(target_url)
    base_path = parts.path.rstrip("/")
    extra_path = suffix_path.strip("/")

    if extra_path:
        path = f"{base_path}/{extra_path}" if base_path else f"/{extra_path}"
    else:
        path = base_path or "/"

    query = urlencode(query_items, doseq=True)
    if not query:
        query = parts.query
    elif parts.query:
        query = f"{parts.query}&{query}"

    return urlunsplit((parts.scheme, parts.netloc, path, query, ""))


def _sanitize_response_headers(headers: httpx.Headers) -> dict[str, str]:
    """Remove hop-by-hop headers before returning a proxied response."""
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }


def create_app(
    registry: RelayRegistry | None = None,
    *,
    relay_client: httpx.AsyncClient | None = None,
) -> FastAPI:
    """Create the callback relay FastAPI application."""
    registry_path = os.getenv("CALLBACK_RELAY_REGISTRY", str(DEFAULT_REGISTRY_PATH))
    registry = registry or RelayRegistry(registry_path)

    async def lifespan(_: FastAPI):
        if relay_client is None:
            app.state.relay_client = httpx.AsyncClient(timeout=10.0, follow_redirects=False)
        try:
            yield
        finally:
            if relay_client is None:
                await app.state.relay_client.aclose()

    app = FastAPI(title="Codex Callback Relay", lifespan=lifespan)
    if relay_client is not None:
        app.state.relay_client = relay_client

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        """Expose a lightweight health endpoint."""
        return {"status": "ok"}

    @app.get("/api/machines/{machine_id}")
    async def get_machine(
        machine_id: str,
        _: None = Depends(require_admin_token),
    ) -> dict[str, Any]:
        """Return the relay target for a machine."""
        target = registry.get(machine_id)
        if target is None:
            raise HTTPException(status_code=404, detail="machine target not found")
        return asdict(target)

    @app.put("/api/machines/{machine_id}")
    async def put_machine(
        machine_id: str,
        registration: MachineRegistration,
        _: None = Depends(require_admin_token),
    ) -> dict[str, Any]:
        """Register or update a machine target."""
        target = registry.upsert(machine_id, registration)
        return asdict(target)

    @app.delete("/api/machines/{machine_id}")
    async def delete_machine(machine_id: str, _: None = Depends(require_admin_token)) -> Response:
        """Delete a registered machine target."""
        deleted = registry.delete(machine_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="machine target not found")
        return Response(status_code=204)

    @app.api_route("/callback/{machine_id}", methods=["GET", "POST"])
    @app.api_route("/callback/{machine_id}/{suffix_path:path}", methods=["GET", "POST"])
    async def relay_callback(
        machine_id: str,
        request: Request,
        suffix_path: str = "",
    ) -> Response:
        """Forward the OAuth callback request to the registered machine target."""
        target = registry.get(machine_id)
        if target is None:
            raise HTTPException(status_code=404, detail="machine target not found")

        query_items = list(parse_qsl(request.url.query, keep_blank_values=True))
        forward_url = _build_forward_url(target.target_url, suffix_path, query_items)

        body = await request.body()
        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS
        }
        headers["x-callback-relay-machine-id"] = machine_id

        client: httpx.AsyncClient = request.app.state.relay_client
        try:
            upstream = await client.request(
                request.method,
                forward_url,
                content=body or None,
                headers=headers,
            )
        except httpx.HTTPError as exc:
            LOGGER.warning("Callback relay forwarding failed for %s: %s", machine_id, exc)
            raise HTTPException(
                status_code=502,
                detail=f"failed to reach machine target: {exc}",
            ) from exc

        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=_sanitize_response_headers(upstream.headers),
            media_type=upstream.headers.get("content-type"),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        """Return consistent JSON for relay errors."""
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    return app
