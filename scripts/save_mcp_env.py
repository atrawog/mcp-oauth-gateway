#!/usr/bin/env python3
"""
Save MCP client environment variables to .env file
"""
import sys
import re
from pathlib import Path

ENV_FILE = Path(__file__).parent.parent / ".env"

def save_env_var(key: str, value: str):
    """Save or update an environment variable in .env file"""
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

# Read from stdin
input_text = sys.stdin.read()

# Find export statements
pattern = r'^export\s+(MCP_CLIENT_[A-Z_]+)=(.+)$'
env_vars = {}

for line in input_text.split('\n'):
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
        save_env_var(key, value)
        print(f"   ✅ Saved {key}")
    print("\n✅ MCP client credentials saved to .env!")

# Pass through the original output
print(input_text, end='')