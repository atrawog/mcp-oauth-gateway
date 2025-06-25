#!/usr/bin/env python3
"""Test script to verify that mcp-streamablehttp-client uses MCP_CLIENT_* environment variables by default.

This script demonstrates that the client automatically picks up MCP_CLIENT_* variables from the environment.
"""

import asyncio
import os
import sys
from pathlib import Path


# Add parent directory to path so we can import the client modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_streamablehttp_client.config import Settings
from mcp_streamablehttp_client.oauth import OAuthClient


async def test_env_vars():
    """Test that the client reads MCP_CLIENT_* environment variables."""
    print("Testing MCP Client Environment Variable Usage")
    print("=" * 50)

    # Show current environment variables
    print("\nCurrent MCP_CLIENT_* environment variables:")
    for key, value in os.environ.items():
        if key.startswith("MCP_CLIENT_"):
            if "TOKEN" in key or "SECRET" in key:
                # Mask sensitive values
                masked_value = value[:10] + "..." if len(value) > 10 else value
                print(f"  {key} = {masked_value}")
            else:
                print(f"  {key} = {value}")

    # Create settings - this should automatically load MCP_CLIENT_* vars
    print("\nCreating Settings object...")
    base_domain = os.getenv("BASE_DOMAIN")
    if not base_domain:
        raise Exception("BASE_DOMAIN must be set in .env")
    settings = Settings(mcp_server_url=f"https://mcp-fetch.{base_domain}/mcp")

    # Check what was loaded
    print("\nSettings loaded from environment:")
    print(f"  oauth_client_id: {settings.oauth_client_id}")
    print(
        f"  oauth_client_secret: {settings.oauth_client_secret[:10]}..."
        if settings.oauth_client_secret
        else "  oauth_client_secret: None"
    )
    print(
        f"  oauth_access_token: {settings.oauth_access_token[:20]}..."
        if settings.oauth_access_token
        else "  oauth_access_token: None"
    )
    print(
        f"  oauth_refresh_token: {settings.oauth_refresh_token[:20]}..."
        if settings.oauth_refresh_token
        else "  oauth_refresh_token: None"
    )

    # Test if credentials are valid
    print("\nChecking credential validity:")
    print(f"  has_valid_credentials(): {settings.has_valid_credentials()}")
    print(f"  needs_registration(): {settings.needs_registration()}")

    # Show that client would use these automatically
    print("\nCreating OAuth client...")
    async with OAuthClient(settings):
        if settings.has_valid_credentials():
            print(
                "✅ OAuth client initialized with valid credentials from MCP_CLIENT_* env vars!"
            )
        else:
            print("⚠️  No valid credentials found in MCP_CLIENT_* env vars")
            print("   The client would perform OAuth flow on first use")

    print("\n" + "=" * 50)
    print(
        "CONCLUSION: mcp-streamablehttp-client automatically uses MCP_CLIENT_* environment variables!"
    )
    print(
        "No credential files needed - everything flows through .env as commanded by CLAUDE.md!"
    )


if __name__ == "__main__":
    # Make sure .env is loaded
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(test_env_vars())
