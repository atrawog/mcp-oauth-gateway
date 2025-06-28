#!/usr/bin/env python3
"""Create MCP configuration for Claude Code with OAuth bearer token.

Following CLAUDE.md commandments: Real configuration, no hardcoded values.
"""

import json
import os
import sys
from pathlib import Path


def create_mcp_config():
    """Generate MCP config.json for Claude Code with OAuth authentication."""
    # Get required environment variables
    base_domain = os.getenv("BASE_DOMAIN")
    oauth_access_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")

    if not base_domain:
        print("❌ ERROR: BASE_DOMAIN environment variable is not set!")
        print("Please ensure your .env file is loaded.")
        sys.exit(1)

    if not oauth_access_token:
        print("❌ ERROR: GATEWAY_OAUTH_ACCESS_TOKEN environment variable is not set!")
        print("Please run 'just generate-github-token' first to obtain an OAuth token.")
        sys.exit(1)

    # Create the MCP configuration
    mcp_config = {
        "mcpServers": {
            "mcp-fetch": {
                "url": f"https://mcp-fetch.{base_domain}/mcp",
                "transport": {
                    "type": "streamable-http",
                    "headers": {"Authorization": f"Bearer {oauth_access_token}"},
                },
            },
        },
    }

    # Determine output path
    # Claude Code looks for config in specific locations
    config_dir = Path.home() / ".config" / "claude"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "mcp-config.json"

    # Write the configuration
    with open(config_path, "w") as f:
        json.dump(mcp_config, f, indent=2)

    print("✅ MCP configuration created successfully!")
    print(f"📝 Configuration written to: {config_path}")
    print("\n📋 Configuration contents:")
    print(json.dumps(mcp_config, indent=2))

    # Also create a local copy for reference
    local_config_path = Path("mcp-config.json")
    with open(local_config_path, "w") as f:
        json.dump(mcp_config, f, indent=2)

    print(f"\n📝 Local copy saved to: {local_config_path}")

    # Provide instructions
    print("\n🚀 To use this configuration with Claude Code:")
    print("1. The config has been automatically placed in ~/.config/claude/mcp-config.json")
    print("2. Claude Code should detect it automatically")
    print("3. If not, you can manually specify the config path")
    print("\n⚠️  Important notes:")
    print(f"- Your MCP server is at: https://mcp-fetch.{base_domain}/mcp")
    print("- The bearer token will expire in 24 hours (configurable)")
    print("- Run 'just generate-github-token' to refresh the token when needed")
    print("\n🔒 Security reminder:")
    print("- Never commit mcp-config.json to version control!")
    print("- The bearer token provides full access to your MCP server")


if __name__ == "__main__":
    create_mcp_config()
