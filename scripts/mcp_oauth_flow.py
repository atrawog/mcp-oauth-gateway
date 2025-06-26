#!/usr/bin/env python3
"""MCP OAuth Flow Helper - Handles the OAuth flow in steps."""

import os
import re
import subprocess
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


def extract_env_vars(output: str):
    """Extract export statements from output."""
    env_vars = {}
    pattern = r"^export\s+(MCP_CLIENT_[A-Z_]+)=(.+)$"

    for line in output.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            if value and value != "None":
                env_vars[key] = value

    return env_vars


def run_oauth_flow():
    """Run the OAuth flow with optional auth code."""
    # Check if auth code was provided as argument
    auth_code = sys.argv[1] if len(sys.argv) > 1 else None

    # Set up environment
    env = os.environ.copy()
    env["MCP_SERVER_URL"] = f"https://mcp-fetch.{env.get('BASE_DOMAIN')}/mcp"

    if auth_code:
        env["MCP_AUTH_CODE"] = auth_code
        print(f"🔐 Using provided authorization code: {auth_code[:10]}...")

    # Run the MCP client
    cmd = [
        sys.executable,
        "-m",
        "mcp_streamablehttp_client.cli",
        "--token",
        "--server-url",
        env["MCP_SERVER_URL"],
    ]

    # Run command and capture output
    result = subprocess.run(cmd, check=False, env=env, capture_output=True, text=True)

    # Print output for user
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    # Extract and save environment variables
    output = result.stdout + "\n" + result.stderr
    env_vars = extract_env_vars(output)

    if env_vars:
        print(f"\n📝 Saving {len(env_vars)} MCP client variables to .env...")
        for key, value in env_vars.items():
            save_env_var(key, value)
            print(f"   ✅ Saved {key}")
        print("\n✅ MCP client credentials saved to .env!")
        return 0
    # Check if we got an authorization URL
    auth_url_match = re.search(r"(https://auth\.[^\s]+/authorize[^\s]+)", output)
    if auth_url_match and not auth_code:
        auth_url = auth_url_match.group(1)
        print("\n" + "=" * 70)
        print("📋 AUTHORIZATION REQUIRED")
        print("=" * 70)
        print("\n1. Visit this URL in your browser:")
        print(f"   {auth_url}")
        print("\n2. Complete GitHub authentication")
        print("\n3. Copy the authorization code from the success page")
        print("\n4. Run this command with the code:")
        print("   just mcp-client-token <authorization-code>")
        print("\n" + "=" * 70)
        return 1
    print("\n⚠️  No MCP client variables found in output")
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_oauth_flow())
