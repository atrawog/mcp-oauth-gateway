#!/usr/bin/env python3
"""Shared utility functions for mcp-oauth-gateway project."""

from pathlib import Path
from typing import Optional

from dotenv import set_key


def get_project_root() -> Path:
    """Get the project root directory (where this utils.py is located)."""
    return Path(__file__).parent


def save_env_var(
    key: str,
    value: str,
    env_file: Optional[Path] = None,
) -> None:
    """Save or update an environment variable in .env file."""
    if env_file is None:
        env_file = get_project_root() / ".env"
    set_key(str(env_file), key, value, quote_mode="never")
