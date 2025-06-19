#!/usr/bin/env python3
"""
Helper script to save OAuth environment variables to .env file.
This runs after mcp-streamablehttp-client to capture the env vars it set.
"""
import os
from pathlib import Path

ENV_FILE = Path(__file__).parent.parent / ".env"

# OAuth variables to save
OAUTH_VARS = [
    "OAUTH_ACCESS_TOKEN",
    "OAUTH_REFRESH_TOKEN", 
    "OAUTH_CLIENT_ID",
    "OAUTH_CLIENT_SECRET",
    "OAUTH_ISSUER",
    "OAUTH_TOKEN_URL",
    "OAUTH_AUTHORIZATION_URL",
    "OAUTH_DEVICE_AUTH_URL",
    "OAUTH_REGISTRATION_URL",
]

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

def main():
    """Save OAuth environment variables to .env"""
    saved_count = 0
    
    for var in OAUTH_VARS:
        value = os.environ.get(var)
        if value:
            # Map to MCP_CLIENT_ prefix for tokens
            if var == "OAUTH_ACCESS_TOKEN":
                save_env_var("MCP_CLIENT_ACCESS_TOKEN", value)
                print(f"✅ Saved MCP_CLIENT_ACCESS_TOKEN")
                saved_count += 1
            elif var == "OAUTH_REFRESH_TOKEN":
                save_env_var("MCP_CLIENT_REFRESH_TOKEN", value) 
                print(f"✅ Saved MCP_CLIENT_REFRESH_TOKEN")
                saved_count += 1
            elif var == "OAUTH_CLIENT_ID":
                save_env_var("MCP_CLIENT_ID", value)
                print(f"✅ Saved MCP_CLIENT_ID")
                saved_count += 1
            elif var == "OAUTH_CLIENT_SECRET":
                save_env_var("MCP_CLIENT_SECRET", value)
                print(f"✅ Saved MCP_CLIENT_SECRET")
                saved_count += 1
            else:
                # Save other vars as-is
                save_env_var(var, value)
                print(f"✅ Saved {var}")
                saved_count += 1
    
    if saved_count > 0:
        print(f"\n✅ Saved {saved_count} OAuth variables to .env")
    else:
        print("\n⚠️  No OAuth variables found in environment")
        print("The mcp-streamablehttp-client should have set them.")

if __name__ == "__main__":
    main()