#!/usr/bin/env python3
"""Helper script to run Python scripts inside a Docker container with proper Redis access."""
import os
import subprocess
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: run_in_container.py <script.py> [args...]")
        sys.exit(1)

    script = sys.argv[1]
    args = sys.argv[2:]

    # Build docker run command
    cmd = [
        "docker", "run", "--rm",
        "--network", "public",
        "-v", f"{os.getcwd()}:/app",
        "-w", "/app",
        "--env-file", ".env",
        "-e", "REDIS_URL=redis://redis:6379",  # Override for container context
        "python:3.11-slim",
        "python", script
    ] + args

    # Run the command
    result = subprocess.run(cmd, check=False)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
