"""Validate the callback relay compose service wiring."""

from __future__ import annotations

import os

import pytest
import yaml

pytestmark = pytest.mark.local_only

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
AUTH_COMPOSE = os.path.join(REPO_ROOT, "auth", "docker-compose.yml")
AUTH_DOCKERFILE = os.path.join(REPO_ROOT, "auth", "Dockerfile")


def _load_yaml(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


class TestCallbackRelayCompose:
    """Verify the callback relay service is deployed via compose."""

    def test_callback_relay_service_exists(self) -> None:
        """The auth compose file should define the dedicated relay service."""
        compose = _load_yaml(AUTH_COMPOSE)
        assert "services" in compose
        assert "callback-relay" in compose["services"]

    def test_callback_relay_uses_auth_image_build(self) -> None:
        """The relay should reuse the auth Dockerfile build context."""
        compose = _load_yaml(AUTH_COMPOSE)
        service = compose["services"]["callback-relay"]
        assert service["build"]["context"] == ".."
        assert service["build"]["dockerfile"] == "auth/Dockerfile"

    def test_callback_relay_runs_dedicated_server_command(self) -> None:
        """The relay service should launch the callback relay runner."""
        compose = _load_yaml(AUTH_COMPOSE)
        service = compose["services"]["callback-relay"]
        assert service["command"] == ["python", "/app/scripts/callback_relay_server.py"]

    def test_callback_relay_persists_registry_state(self) -> None:
        """The relay service should persist its registry under .cache."""
        compose = _load_yaml(AUTH_COMPOSE)
        service = compose["services"]["callback-relay"]
        volumes = service.get("volumes", [])
        assert "../.cache/callback-relay:/app/.cache/callback-relay" in volumes

    def test_auth_dockerfile_copies_relay_runtime(self) -> None:
        """The auth Dockerfile should include the relay runtime files."""
        with open(AUTH_DOCKERFILE, encoding="utf-8") as handle:
            dockerfile = handle.read()

            assert "COPY @oauth-helpers/scripts/callback_relay.py /app/scripts/callback_relay.py" in dockerfile
            assert (
                "COPY @oauth-helpers/scripts/callback_relay_server.py /app/scripts/callback_relay_server.py"
                in dockerfile
            )
