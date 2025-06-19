#!/usr/bin/env python3
"""
Sacred MCP Client Token Generation Script
Uses mcp-streamablehttp-client's --token flag to generate and manage OAuth tokens.
"""
import os
import sys
import subprocess
import json
import re
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urlparse


# Load environment variables
ENV_FILE = Path(__file__).parent.parent / ".env"


def load_env():
    """Load environment variables from .env file"""
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


def ensure_mcp_client_installed() -> bool:
    """Ensure mcp-streamablehttp-client is installed in pixi environment"""
    print("🔍 Checking if mcp-streamablehttp-client is installed...")
    
    # Check if module is available
    check_cmd = ["pixi", "run", "python", "-c", "import mcp_streamablehttp_client"]
    check_result = subprocess.run(
        check_cmd,
        capture_output=True,
        cwd=Path(__file__).parent.parent
    )
    
    if check_result.returncode != 0:
        print("📦 Installing mcp-streamablehttp-client...")
        install_cmd = ["pixi", "run", "install-mcp-client"]
        install_result = subprocess.run(
            install_cmd,
            cwd=Path(__file__).parent.parent
        )
        
        if install_result.returncode != 0:
            print("❌ Failed to install mcp-streamablehttp-client")
            print("Try running manually: pixi run install-mcp-client")
            return False
        
        print("✅ mcp-streamablehttp-client installed successfully")
    else:
        print("✅ mcp-streamablehttp-client is already installed")
    
    return True




def run_mcp_client_token_check(base_domain: str) -> Optional[str]:
    """Run mcp-streamablehttp-client --token to check/generate OAuth tokens"""
    mcp_url = f"https://mcp-fetch.{base_domain}/mcp"
    
    print(f"\n🚀 Running mcp-streamablehttp-client token management...")
    print(f"   MCP URL: {mcp_url}")
    
    # Set environment variable for the server URL
    env = os.environ.copy()
    env["MCP_SERVER_URL"] = mcp_url
    
    print()
    
    try:
        # Run mcp-streamablehttp-client with --token flag using pixi
        cmd = [
            "pixi", "run", "python", "-m", "mcp_streamablehttp_client.cli",
            "--token",
            "--server-url", mcp_url
        ]
        
        print(f"📋 Running: {' '.join(cmd)}")
        print()
        
        # Run the command interactively so user can complete OAuth if needed
        result = subprocess.run(
            cmd,
            env=env,
            cwd=Path(__file__).parent.parent  # Run from project root
        )
        
        if result.returncode == 0:
            print("\n✅ Token check/generation completed successfully!")
            
            # Try to extract token from the credential storage
            return extract_token_from_storage(base_domain)
        else:
            print(f"\n❌ Token operation failed with exit code: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error running mcp-streamablehttp-client: {e}")
        return None
    
    return None


def extract_token_from_storage(base_domain: str) -> Optional[str]:
    """Extract the access token from mcp-streamablehttp-client's credential storage"""
    print("\n🔍 Extracting token from credential storage...")
    
    # Possible credential storage locations
    credential_paths = [
        Path.home() / ".config" / "mcp-streamablehttp-client" / "credentials.json",
        Path.home() / ".mcp-streamablehttp-client" / "credentials.json",
        Path.home() / ".mcp" / "credentials.json",
        Path.cwd() / ".mcp-credentials.json",
        Path(__file__).parent.parent / ".mcp-credentials.json",
    ]
    
    mcp_url = f"https://mcp-fetch.{base_domain}/mcp"
    
    for cred_path in credential_paths:
        if cred_path.exists():
            try:
                with open(cred_path) as f:
                    creds = json.load(f)
                    
                    # Check if we have credentials for our server
                    if "oauth_access_token" in creds:
                        token = creds["oauth_access_token"]
                        print(f"✅ Found access token in: {cred_path}")
                        return token
                    
                    # Check if credentials are stored per-server
                    if mcp_url in creds and "oauth_access_token" in creds[mcp_url]:
                        token = creds[mcp_url]["oauth_access_token"]
                        print(f"✅ Found access token for {mcp_url} in: {cred_path}")
                        return token
                        
            except Exception as e:
                print(f"⚠️  Error reading {cred_path}: {e}")
    
    # Also check .env in mcp-streamablehttp-client directory
    client_env = Path(__file__).parent.parent / "mcp-streamablehttp-client" / ".env"
    if client_env.exists():
        env_vars = {}
        with open(client_env) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    if key.strip() == "OAUTH_ACCESS_TOKEN":
                        print(f"✅ Found access token in: {client_env}")
                        return value.strip()
    
    return None


def main():
    """Main MCP client token generation flow"""
    print("🚀 MCP Client Token Generator")
    print("=============================")
    print("This uses mcp-streamablehttp-client --token to manage OAuth tokens")
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
    
    # Run token check/generation
    token = run_mcp_client_token_check(base_domain)
    
    if token:
        # Save token to .env
        save_env_var("MCP_CLIENT_ACCESS_TOKEN", token)
        print(f"\n✅ MCP client token saved to .env!")
        print(f"   MCP_CLIENT_ACCESS_TOKEN={token[:20]}...")
        
        # Show usage
        print("\n📋 You can now use the token with:")
        print(f"   pixi run python -m mcp_streamablehttp_client.cli \\")
        print(f"     --server-url https://mcp-fetch.{base_domain}/mcp")
        print()
        print("Or set it in your environment:")
        print(f"   export OAUTH_ACCESS_TOKEN={token}")
        
    else:
        print("\n⚠️  Could not extract token after operation")
        print("\nThe token may have been saved to mcp-streamablehttp-client's credential storage.")
        print("You can check the token status again with:")
        print(f"  pixi run python -m mcp_streamablehttp_client.cli --token --server-url https://mcp-fetch.{base_domain}/mcp")


if __name__ == "__main__":
    main()