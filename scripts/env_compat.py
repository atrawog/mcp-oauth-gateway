"""Helpers for reading environment variables with compatibility aliases."""

from __future__ import annotations

import os
from collections.abc import Mapping


ENV_ALIASES: dict[str, tuple[str, ...]] = {
    "GATEWAY_JWT_SECRET": ("OAUTH_JWT_SECRET",),
    "JWT_ALGORITHM": ("OAUTH_JWT_ALGORITHM",),
    "JWT_PRIVATE_KEY_B64": ("OAUTH_JWT_PRIVATE_KEY_B64",),
    "ACCESS_TOKEN_LIFETIME": ("OAUTH_ACCESS_TOKEN_LIFETIME",),
    "REFRESH_TOKEN_LIFETIME": ("OAUTH_REFRESH_TOKEN_LIFETIME",),
    "SESSION_TIMEOUT": ("OAUTH_SESSION_TIMEOUT",),
    "CLIENT_LIFETIME": ("OAUTH_CLIENT_LIFETIME",),
    "ALLOWED_GITHUB_USERS": ("OAUTH_ALLOWED_GITHUB_USERS",),
    "MCP_PROTOCOL_VERSION": ("OAUTH_MCP_PROTOCOL_VERSION",),
}


def get_env_value(
    key: str,
    default: str | None = None,
    env: Mapping[str, str] | None = None,
) -> str | None:
    """Return an env var, falling back to canonical aliases when needed."""
    source = os.environ if env is None else env

    value = source.get(key)
    if value not in (None, ""):
        return value

    for alias in ENV_ALIASES.get(key, ()):
        alias_value = source.get(alias)
        if alias_value not in (None, ""):
            return alias_value

    return default


def get_auth_subdomain(env: Mapping[str, str] | None = None) -> str:
    """Return the configured auth subdomain."""
    source = os.environ if env is None else env
    return source.get("AUTH_SUBDOMAIN", "mcp-auth")


def get_auth_base_url(
    base_domain: str | None = None,
    env: Mapping[str, str] | None = None,
) -> str:
    """Return the public auth base URL."""
    source = os.environ if env is None else env
    domain = base_domain or source.get("BASE_DOMAIN", "localhost")
    return f"https://{get_auth_subdomain(source)}.{domain}"
