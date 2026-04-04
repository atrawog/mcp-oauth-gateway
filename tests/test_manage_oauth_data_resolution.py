"""Tests for Redis connection resolution in OAuth management scripts."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


pytestmark = pytest.mark.local_only


MODULE_PATH = Path("scripts/manage_oauth_data.py")


def load_module():
    """Load the OAuth management script as a module for testing."""
    spec = importlib.util.spec_from_file_location("manage_oauth_data", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_runtime_redis_url_uses_localhost_when_port_is_published(monkeypatch: pytest.MonkeyPatch) -> None:
    """Published Redis ports should be addressed through localhost from the host."""
    module = load_module()

    def fake_run(command: list[str], **_: object):
        if command == ["docker", "compose", "ps", "--services", "--filter", "status=running"]:
            return module.subprocess.CompletedProcess(command, 0, stdout="mcp-oauth\nmcp-oauth-redis\n")
        if command == ["docker", "compose", "port", "mcp-oauth-redis", "6379"]:
            return module.subprocess.CompletedProcess(command, 0, stdout="127.0.0.1:6380\n")
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    resolved = module.resolve_runtime_redis_url("redis://:secret@mcp-oauth-redis:6379/0")

    assert resolved == "redis://:secret@127.0.0.1:6380/0"


def test_resolve_runtime_redis_url_uses_container_ip_when_port_not_published(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When Redis is not published to the host, use the running container IP."""
    module = load_module()

    def fake_run(command: list[str], **_: object):
        if command == ["docker", "compose", "ps", "--services", "--filter", "status=running"]:
            return module.subprocess.CompletedProcess(command, 0, stdout="mcp-oauth\nmcp-oauth-redis\n")
        if command == ["docker", "compose", "port", "mcp-oauth-redis", "6379"]:
            return module.subprocess.CompletedProcess(command, 0, stdout=":0\n")
        if command == [
            "docker",
            "inspect",
            "mcp-oauth-redis",
            "--format",
            "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
        ]:
            return module.subprocess.CompletedProcess(command, 0, stdout="10.6.0.3\n")
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    resolved = module.resolve_runtime_redis_url("redis://:secret@mcp-oauth-redis:6379/0")

    assert resolved == "redis://:secret@10.6.0.3:6379/0"
