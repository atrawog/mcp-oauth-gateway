#!/usr/bin/env python3
"""Sacred MCP Client Token Generation Script.

Uses mcp-streamablehttp-client's --token flag to generate OAuth tokens and saves them to .env.
"""

import os
import re
import subprocess
import sys
from pathlib import Path


# Load environment variables
ENV_FILE = Path(__file__).parent.parent / ".env"


def load_env() -> dict[str, str]:
    """Load environment variables from .env file."""
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


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


def extract_oauth_vars_from_output(output: str) -> dict[str, str]:
    """Extract OAuth environment variables from command output."""
    oauth_vars = {}

    # Pattern to match environment variable assignments
    # Matches: OAUTH_ACCESS_TOKEN=value or OAUTH_ACCESS_TOKEN = value
    pattern = r"^(OAUTH_[A-Z_]+)\s*=\s*(.+)$"

    for line in output.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            oauth_vars[key] = value
            print(
                f"   Found: {key}={value[:20]}..."
                if len(value) > 20
                else f"   Found: {key}={value}"
            )

    return oauth_vars


def ensure_mcp_client_installed() -> bool:
    """Ensure mcp-streamablehttp-client is installed in pixi environment."""
    print("🔍 Checking if mcp-streamablehttp-client is installed...")

    # Check if module is available
    check_cmd = ["pixi", "run", "python", "-c", "import mcp_streamablehttp_client"]
    check_result = subprocess.run(
        check_cmd, check=False, capture_output=True, cwd=Path(__file__).parent.parent
    )

    if check_result.returncode != 0:
        print("📦 Installing mcp-streamablehttp-client...")
        install_cmd = ["pixi", "run", "install-mcp-client"]
        install_result = subprocess.run(
            install_cmd, check=False, cwd=Path(__file__).parent.parent
        )

        if install_result.returncode != 0:
            print("❌ Failed to install mcp-streamablehttp-client")
            print("Try running manually: pixi run install-mcp-client")
            return False

        print("✅ mcp-streamablehttp-client installed successfully")
    else:
        print("✅ mcp-streamablehttp-client is already installed")

    return True


def main():
    """Main MCP client token generation flow."""
    print("🚀 MCP Client Token Generator")
    print("=============================")
    print(
        "This uses mcp-streamablehttp-client --token to generate and save OAuth tokens"
    )
    print()

    # Load environment
    env_vars = load_env()
    os.environ.update(env_vars)

    # Check for required configuration
    base_domain = os.getenv("BASE_DOMAIN")
    if not base_domain:
        print("❌ Missing BASE_DOMAIN in .env")
        sys.exit(1)

    # Ensure mcp-streamablehttp-client is installed
    if not ensure_mcp_client_installed():
        sys.exit(1)

    # Construct MCP URL
    mcp_url = f"https://mcp-fetch.{base_domain}/mcp"

    print("\n🚀 Running mcp-streamablehttp-client token management...")
    print(f"   MCP URL: {mcp_url}")
    print()

    # Set environment variable for the server URL
    env = os.environ.copy()
    env["MCP_SERVER_URL"] = mcp_url

    # Run mcp-streamablehttp-client with --token flag using pixi
    cmd = [
        "pixi",
        "run",
        "python",
        "-m",
        "mcp_streamablehttp_client.cli",
        "--token",
        "--server-url",
        mcp_url,
    ]

    print(f"📋 Running: {' '.join(cmd)}")
    print()

    # Run the command and capture output
    result = subprocess.run(
        cmd,
        check=False,
        env=env,
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
    )

    # Print output for user to see OAuth flow
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode == 0:
        print("\n✅ Token check/generation completed!")

        # Extract OAuth variables from output
        print("\n🔍 Extracting OAuth variables from output...")
        combined_output = result.stdout + "\n" + result.stderr
        oauth_vars = extract_oauth_vars_from_output(combined_output)

        if oauth_vars:
            print(f"\n📝 Found {len(oauth_vars)} OAuth variables to save")

            # Save to .env with MCP_CLIENT_ prefix for client tokens
            for key, value in oauth_vars.items():
                # Map standard OAuth vars to MCP client-specific ones
                if key == "OAUTH_ACCESS_TOKEN":
                    save_env_var("MCP_CLIENT_ACCESS_TOKEN", value)
                    print("   ✅ Saved MCP_CLIENT_ACCESS_TOKEN")
                elif key == "OAUTH_REFRESH_TOKEN":
                    save_env_var("MCP_CLIENT_REFRESH_TOKEN", value)
                    print("   ✅ Saved MCP_CLIENT_REFRESH_TOKEN")
                elif key == "OAUTH_CLIENT_ID":
                    save_env_var("MCP_CLIENT_ID", value)
                    print("   ✅ Saved MCP_CLIENT_ID")
                elif key == "OAUTH_CLIENT_SECRET":
                    save_env_var("MCP_CLIENT_SECRET", value)
                    print("   ✅ Saved MCP_CLIENT_SECRET")
                else:
                    # Save other OAuth vars as-is
                    save_env_var(key, value)
                    print(f"   ✅ Saved {key}")

            print("\n✅ OAuth tokens and configuration saved to .env!")
            print("\n📋 You can now use the client with:")
            print("   export OAUTH_ACCESS_TOKEN=$MCP_CLIENT_ACCESS_TOKEN")
            print("   pixi run python -m mcp_streamablehttp_client.cli \\")
            print(f"     --server-url {mcp_url}")
        else:
            print("\n⚠️  No OAuth variables found in output")
            print("The client may already be configured with valid tokens.")
    else:
        print(f"\n❌ Token operation failed with exit code: {result.returncode}")
        print("\nPlease check the error messages above and try again.")


if __name__ == "__main__":
    main()
