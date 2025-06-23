#!/usr/bin/env python3
import re
import sys
from pathlib import Path


ENV_FILE = Path(__file__).parent.parent / ".env"


def save_env_var(key: str, value: str):
    """Save or update an environment variable in .env file."""
    lines = []
    found = False

    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)

    if not found:
        lines.append(f"\n{key}={value}\n")

    with open(ENV_FILE, "w") as f:
        f.writelines(lines)


# Read output file
if len(sys.argv) > 1:
    with open(sys.argv[1]) as f:
        output = f.read()

    # Find export statements
    pattern = r"^export\s+(MCP_CLIENT_[A-Z_]+)=(.+)$"
    for line in output.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            if value and value != "None":
                save_env_var(key, value)
                print(f"✅ Saved {key}")
