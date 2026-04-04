"""Helpers for resolving Redis connectivity from host-run scripts."""

from __future__ import annotations

import subprocess
from urllib.parse import urlsplit
from urllib.parse import urlunsplit


def replace_redis_host(redis_url: str, host: str, port: int) -> str:
    """Return a Redis URL with an updated host and port."""
    parsed = urlsplit(redis_url)

    username = parsed.username or ""
    password = parsed.password or ""
    auth = ""
    if username and password:
        auth = f"{username}:{password}@"
    elif password:
        auth = f":{password}@"
    elif username:
        auth = f"{username}@"

    netloc = f"{auth}{host}:{port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def resolve_runtime_redis_url(redis_url: str) -> str:
    """Resolve a host-runnable Redis URL when Docker DNS is unavailable locally."""
    parsed = urlsplit(redis_url)
    hostname = parsed.hostname
    if hostname not in {"redis", "mcp-oauth-redis"}:
        return redis_url

    try:
        services_result = subprocess.run(
            ["docker", "compose", "ps", "--services", "--filter", "status=running"],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return redis_url

    running_services = {
        service.strip() for service in services_result.stdout.splitlines() if service.strip()
    }
    redis_service_name = next(
        (
            service_name
            for service_name in ("mcp-oauth-redis", "redis")
            if service_name in running_services
        ),
        None,
    )
    if redis_service_name is None:
        return redis_url

    try:
        port_result = subprocess.run(
            ["docker", "compose", "port", redis_service_name, "6379"],
            capture_output=True,
            text=True,
            check=True,
        )
        published = port_result.stdout.strip()
        if published and published != ":0":
            published_host, published_port = published.rsplit(":", maxsplit=1)
            if published_host in {"0.0.0.0", "::", ""}:
                published_host = "127.0.0.1"
            return replace_redis_host(redis_url, published_host, int(published_port))
    except Exception:
        pass

    try:
        inspect_result = subprocess.run(
            [
                "docker",
                "inspect",
                redis_service_name,
                "--format",
                "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        container_ip = inspect_result.stdout.strip()
        if container_ip:
            return replace_redis_host(redis_url, container_ip, 6379)
    except Exception:
        pass

    return redis_url
