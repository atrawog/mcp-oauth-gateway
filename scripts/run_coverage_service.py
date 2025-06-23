#!/usr/bin/env python3
"""Run the auth service with coverage from source code."""

import os
import subprocess
import sys


# Add source to Python path
sys.path.insert(0, "/src")

# Set coverage environment
os.environ["COVERAGE_FILE"] = "/coverage-data/.coverage"

# Run with coverage
subprocess.run(
    [
        "python",
        "-m",
        "coverage",
        "run",
        "--source=/src",
        "-m",
        "mcp_oauth_dynamicclient.server",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ],
    check=False,
)
