"""Regression tests for root project dependency declarations."""

from __future__ import annotations

import tomllib
from pathlib import Path


def test_root_project_declares_tabulate_for_oauth_management_script() -> None:
    """The root uv environment must include packages imported by root scripts."""
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    dependencies = pyproject["project"]["dependencies"]

    assert any(dependency.startswith("tabulate") for dependency in dependencies)
import pytest


pytestmark = pytest.mark.local_only
