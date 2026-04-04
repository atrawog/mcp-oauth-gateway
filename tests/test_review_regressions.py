"""Regression tests for recent review findings."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
import scripts.generate_compose_includes as compose_includes

pytestmark = pytest.mark.local_only

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = REPO_ROOT / ".env.example"
AUTH_DOCKERFILE = REPO_ROOT / "auth" / "Dockerfile"


def test_auth_image_installs_curl_for_healthcheck() -> None:
    """The auth image must provide the binary used by its Compose healthcheck."""
    dockerfile = AUTH_DOCKERFILE.read_text()

    assert "apt-get install --no-install-recommends -y curl" in dockerfile


def test_compose_includes_skip_missing_optional_services(monkeypatch) -> None:
    """Optional services without compose files must not be emitted into includes."""
    monkeypatch.setenv("MCP_ECHO_STATELESS_ENABLED", "true")
    monkeypatch.setenv("MCP_FETCH_ENABLED", "true")

    compose_data = compose_includes.build_compose_data()

    assert compose_data["include"] == [
        "swag/docker-compose.yaml",
        "auth/docker-compose.yml",
    ]


def test_env_example_contains_test_bootstrap_aliases() -> None:
    """The sample env file must expose the names the test bootstrap can resolve."""
    env_example = ENV_EXAMPLE.read_text()

    required_keys = [
        "GATEWAY_JWT_SECRET=",
        "JWT_ALGORITHM=",
        "JWT_PRIVATE_KEY_B64=",
        "ACCESS_TOKEN_LIFETIME=",
        "REFRESH_TOKEN_LIFETIME=",
        "SESSION_TIMEOUT=",
        "ALLOWED_GITHUB_USERS=",
        "MCP_PROTOCOL_VERSION=",
    ]

    for key in required_keys:
        assert key in env_example, f"Missing {key} from .env.example"


def test_test_constants_accept_oauth_prefixed_env(monkeypatch) -> None:
    """Tests must be able to bootstrap from canonical OAUTH_* variables."""
    base_env = {
        "BASE_DOMAIN": "example.com",
        "REDIS_PASSWORD": "redis-password",
        "GITHUB_CLIENT_ID": "github-client-id",
        "GITHUB_CLIENT_SECRET": "github-client-secret",
        "MCP_PROTOCOL_VERSIONS_SUPPORTED": "2025-06-18,2025-03-26",
        "TEST_HTTP_TIMEOUT": "30.0",
        "TEST_MAX_RETRIES": "3",
        "TEST_RETRY_DELAY": "1.0",
        "TEST_OAUTH_CALLBACK_URL": "https://mcp-auth.example.com/success",
        "TEST_CLIENT_NAME": "test-client",
        "TEST_CLIENT_SCOPE": "mcp:read mcp:write",
        "TEST_INVALID_REDIRECT_URI": "https://evil.example/callback",
        "HEALTH_CHECK_TIMEOUT": "30",
        "HEALTH_CHECK_INTERVAL": "5",
    }
    oauth_env = {
        "OAUTH_JWT_SECRET": "gateway-jwt-secret",
        "OAUTH_JWT_ALGORITHM": "RS256",
        "OAUTH_JWT_PRIVATE_KEY_B64": "LS0tLS1CRUdJTiBLRVktLS0tLQ==",
        "OAUTH_ACCESS_TOKEN_LIFETIME": "86400",
        "OAUTH_REFRESH_TOKEN_LIFETIME": "2592000",
        "OAUTH_SESSION_TIMEOUT": "3600",
        "OAUTH_ALLOWED_GITHUB_USERS": "user1,user2",
        "OAUTH_MCP_PROTOCOL_VERSION": "2025-06-18",
    }

    for key, value in {**base_env, **oauth_env}.items():
        monkeypatch.setenv(key, value)
    for key in [
        "GATEWAY_JWT_SECRET",
        "JWT_ALGORITHM",
        "JWT_PRIVATE_KEY_B64",
        "ACCESS_TOKEN_LIFETIME",
        "REFRESH_TOKEN_LIFETIME",
        "SESSION_TIMEOUT",
        "ALLOWED_GITHUB_USERS",
        "MCP_PROTOCOL_VERSION",
    ]:
        monkeypatch.setenv(key, "")

    module_name = "tests.test_constants"
    original_module = importlib.import_module(module_name) if module_name in sys.modules else None
    sys.modules.pop(module_name, None)
    try:
        constants = importlib.import_module(module_name)
        assert constants.JWT_ALGORITHM == "RS256"
        assert constants.ACCESS_TOKEN_LIFETIME == 86400
        assert constants.ALLOWED_GITHUB_USERS == ["user1", "user2"]
        assert constants.MCP_PROTOCOL_VERSION == "2025-06-18"
    finally:
        sys.modules.pop(module_name, None)
        if original_module is not None:
            sys.modules[module_name] = original_module


def test_test_constants_fill_non_secret_defaults(monkeypatch) -> None:
    """Test-only knobs should have safe defaults when omitted from .env."""
    env_values = {
        "BASE_DOMAIN": "example.com",
        "REDIS_PASSWORD": "redis-password",
        "GITHUB_CLIENT_ID": "github-client-id",
        "GITHUB_CLIENT_SECRET": "github-client-secret",
        "OAUTH_JWT_SECRET": "gateway-jwt-secret",
        "OAUTH_JWT_ALGORITHM": "RS256",
        "OAUTH_JWT_PRIVATE_KEY_B64": "LS0tLS1CRUdJTiBLRVktLS0tLQ==",
        "OAUTH_ACCESS_TOKEN_LIFETIME": "86400",
        "OAUTH_REFRESH_TOKEN_LIFETIME": "2592000",
        "OAUTH_SESSION_TIMEOUT": "3600",
        "OAUTH_ALLOWED_GITHUB_USERS": "user1,user2",
        "OAUTH_MCP_PROTOCOL_VERSION": "2025-06-18",
    }

    for key in list(env_values):
        monkeypatch.setenv(key, env_values[key])
    for key in [
        "GATEWAY_JWT_SECRET",
        "JWT_ALGORITHM",
        "JWT_PRIVATE_KEY_B64",
        "ACCESS_TOKEN_LIFETIME",
        "REFRESH_TOKEN_LIFETIME",
        "SESSION_TIMEOUT",
        "ALLOWED_GITHUB_USERS",
        "MCP_PROTOCOL_VERSION",
    ]:
        monkeypatch.setenv(key, "")

    monkeypatch.setenv("MCP_PROTOCOL_VERSIONS_SUPPORTED", "")

    optional_keys = [
        "TEST_HTTP_TIMEOUT",
        "TEST_MAX_RETRIES",
        "TEST_RETRY_DELAY",
        "TEST_OAUTH_CALLBACK_URL",
        "TEST_CLIENT_NAME",
        "TEST_CLIENT_SCOPE",
        "TEST_INVALID_REDIRECT_URI",
        "HEALTH_CHECK_TIMEOUT",
        "HEALTH_CHECK_INTERVAL",
    ]
    for key in optional_keys:
        monkeypatch.delenv(key, raising=False)

    module_name = "tests.test_constants"
    original_module = importlib.import_module(module_name) if module_name in sys.modules else None
    sys.modules.pop(module_name, None)
    try:
        constants = importlib.import_module(module_name)
        assert constants.MCP_PROTOCOL_VERSIONS_SUPPORTED == ["2025-06-18"]
        assert constants.TEST_HTTP_TIMEOUT == 30.0
        assert constants.TEST_MAX_RETRIES == 3
        assert constants.TEST_RETRY_DELAY == 1.0
        assert constants.TEST_OAUTH_CALLBACK_URL == "https://mcp-auth.example.com/success"
        assert constants.TEST_CLIENT_NAME == "test-client"
        assert constants.TEST_CLIENT_SCOPE == "mcp:read mcp:write"
        assert constants.TEST_INVALID_REDIRECT_URI == "https://evil.example/callback"
        assert constants.HEALTH_CHECK_TIMEOUT == 30
        assert constants.HEALTH_CHECK_INTERVAL == 5
    finally:
        sys.modules.pop(module_name, None)
        if original_module is not None:
            sys.modules[module_name] = original_module
