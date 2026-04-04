#!/usr/bin/env python3
"""Generate docker-compose includes based on enabled services."""

import os
from pathlib import Path

import yaml

BASE_INCLUDES = [
    "swag/docker-compose.yaml",
    "auth/docker-compose.yml",
]

OPTIONAL_SERVICE_INCLUDES = {
    "MCP_FETCH_ENABLED": "mcp-fetch/docker-compose.yml",
    "MCP_FETCHS_ENABLED": "mcp-fetchs/docker-compose.yml",
    "MCP_FILESYSTEM_ENABLED": "mcp-filesystem/docker-compose.yml",
    "MCP_MEMORY_ENABLED": "mcp-memory/docker-compose.yml",
    "MCP_PLAYWRIGHT_ENABLED": "mcp-playwright/docker-compose.yml",
    "MCP_SEQUENTIALTHINKING_ENABLED": "mcp-sequentialthinking/docker-compose.yml",
    "MCP_TIME_ENABLED": "mcp-time/docker-compose.yml",
    "MCP_TMUX_ENABLED": "mcp-tmux/docker-compose.yml",
    "MCP_ECHO_STATEFUL_ENABLED": "mcp-echo-stateful/docker-compose.yml",
    "MCP_ECHO_STATELESS_ENABLED": "mcp-echo-stateless/docker-compose.yml",
    "MCP_EVERYTHING_ENABLED": "mcp-everything/docker-compose.yml",
}


def _repo_root() -> Path:
    """Return the repository root."""
    return Path(__file__).parent.parent


def _is_enabled(env_var: str) -> bool:
    """Return whether an optional service is enabled."""
    return os.getenv(env_var, "false").lower() == "true"


def build_compose_data() -> dict[str, object]:
    """Build compose include data for the currently enabled services."""
    includes = list(BASE_INCLUDES)
    repo_root = _repo_root()

    for env_var, include_path in OPTIONAL_SERVICE_INCLUDES.items():
        if not _is_enabled(env_var):
            continue

        if (repo_root / include_path).exists():
            includes.append(include_path)

    return {
        "include": includes,
        "networks": {"public": {"external": True}},
        "volumes": {
            "redis-data": {"external": True},
            "coverage-data": {"external": True},
            "auth-keys": {"external": True},
            "mcp-memory-data": {"external": True},
        },
    }


def main():
    """Generate docker-compose.includes.yml based on enabled services."""
    compose_data = build_compose_data()

    # Write the generated file
    output_path = _repo_root() / "docker-compose.includes.yml"
    with open(output_path, "w") as f:
        yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)

    print(f"Generated {output_path}")
    for env_var, include_path in OPTIONAL_SERVICE_INCLUDES.items():
        service_name = include_path.split("/")[0]
        if not _is_enabled(env_var):
            print(f"❌ {service_name} is DISABLED")
            continue

        if include_path in compose_data["include"]:
            print(f"✅ {service_name} is ENABLED")
        else:
            print(f"⚠️  {service_name} enabled but skipped because {include_path} is missing")


if __name__ == "__main__":
    main()
