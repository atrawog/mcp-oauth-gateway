#!/usr/bin/env python3
"""Save MCP client environment variables to .env file."""

import re
import sys
from pathlib import Path

# Import shared utility function
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import save_env_var


ENV_FILE = Path(__file__).parent.parent / ".env"


# Read from stdin
input_text = sys.stdin.read()

# Find export statements
pattern = r"^export\s+(MCP_CLIENT_[A-Z_]+)=(.+)$"
env_vars = {}

for line in input_text.split("\n"):
    match = re.match(pattern, line.strip())
    if match:
        key = match.group(1)
        value = match.group(2).strip()
        if value and value != "None":
            env_vars[key] = value

# Save to .env
if env_vars:
    print(f"\n📝 Saving {len(env_vars)} MCP client variables to .env...")
    for key, value in env_vars.items():
        save_env_var(key, value, ENV_FILE)
        print(f"   ✅ Saved {key}")
    print("\n✅ MCP client credentials saved to .env!")

# Pass through the original output
print(input_text, end="")
