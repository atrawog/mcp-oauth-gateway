#!/usr/bin/env python3
"""Run tests with coverage locally to get actual metrics."""

import subprocess
import os
import sys

# Set up environment for local coverage
env = os.environ.copy()
env['COVERAGE_FILE'] = '.coverage.local'

# Install the package in development mode
print("Installing package in development mode...")
subprocess.run([sys.executable, "-m", "pip", "install", "-e", "./mcp-oauth-dynamicclient"], check=True)

# Run tests with coverage
print("\nRunning tests with coverage...")
result = subprocess.run([
    sys.executable, "-m", "coverage", "run",
    "--source=mcp-oauth-dynamicclient/src/mcp_oauth_dynamicclient",
    "-m", "pytest", "tests/", "-v"
], env=env)

if result.returncode == 0:
    print("\nGenerating coverage report...")
    subprocess.run([sys.executable, "-m", "coverage", "report", "-m"], env=env)
    subprocess.run([sys.executable, "-m", "coverage", "html"], env=env)
    
    print("\nGenerating detailed coverage JSON...")
    subprocess.run([sys.executable, "-m", "coverage", "json"], env=env)
else:
    print("\nTests failed, but still generating coverage report...")
    subprocess.run([sys.executable, "-m", "coverage", "report", "-m"], env=env)