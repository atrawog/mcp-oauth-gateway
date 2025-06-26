#!/usr/bin/env python3
"""Wrapper script to run mcp-streamablehttp-client with proper OAuth discovery.

This handles the case where OAuth endpoints are on a different subdomain.
"""

import os
import subprocess
import sys
from urllib.parse import urlparse


def get_auth_domain_from_mcp_url(mcp_url: str) -> str:
    """Extract auth domain from MCP URL by replacing subdomain."""
    parsed = urlparse(mcp_url)
    # Replace mcp-fetch subdomain with auth
    hostname_parts = parsed.hostname.split(".")
    if hostname_parts[0].startswith("mcp-"):
        hostname_parts[0] = "auth"
    else:
        # Prepend auth subdomain
        hostname_parts.insert(0, "auth")

    auth_hostname = ".".join(hostname_parts)
    return f"{parsed.scheme}://{auth_hostname}"


def main():
    """Run mcp-streamablehttp-client with proper environment."""
    # Get command line arguments
    args = sys.argv[1:]

    # Extract server URL if provided
    server_url = None
    for i, arg in enumerate(args):
        if arg in ["--server-url", "-s"] and i + 1 < len(args):
            server_url = args[i + 1]
            break

    # If no server URL in args, check environment
    if not server_url:
        server_url = os.environ.get("MCP_SERVER_URL")

    # Set up environment with OAuth metadata URL hint
    env = os.environ.copy()
    if server_url:
        auth_base = get_auth_domain_from_mcp_url(server_url)
        # Set hint for OAuth discovery
        env["OAUTH_ISSUER"] = auth_base
        env["OAUTH_METADATA_URL"] = f"{auth_base}/.well-known/oauth-authorization-server"

    # Run the actual mcp-streamablehttp-client
    cmd = ["python", "-m", "mcp_streamablehttp_client.cli", *args]

    # Execute with modified environment
    result = subprocess.run(cmd, check=False, env=env)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
