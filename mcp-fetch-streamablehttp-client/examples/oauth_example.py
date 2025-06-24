#!/usr/bin/env python3
"""OAuth authentication example for mcp-fetch-streamablehttp-client."""

import asyncio
import json
import os
from mcp_fetch_streamablehttp_client import MCPFetchClient, MCPError


async def fetch_github_user(client: MCPFetchClient, token: str):
    """Fetch GitHub user information using OAuth token."""
    print("\nFetching GitHub user info...")
    
    result = await client.fetch(
        "https://api.github.com/user",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    )
    
    if result.status == 200:
        user_data = json.loads(result.text)
        print(f"  Username: {user_data.get('login')}")
        print(f"  Name: {user_data.get('name')}")
        print(f"  Public repos: {user_data.get('public_repos')}")
        print(f"  Followers: {user_data.get('followers')}")
    else:
        print(f"  Failed with status: {result.status}")


async def fetch_protected_resource(client: MCPFetchClient):
    """Example of fetching a protected resource through MCP gateway."""
    print("\nFetching protected resource...")
    
    # The MCP gateway itself handles authentication via the Bearer token
    # passed in the client constructor
    result = await client.fetch("https://api.example.com/protected/data")
    
    print(f"  Status: {result.status}")
    if result.status == 200:
        print(f"  Content preview: {result.text[:200]}...")


async def main():
    # Configuration from environment
    server_url = os.getenv("MCP_SERVER_URL", "https://mcp-fetch.example.com")
    mcp_token = os.getenv("MCP_CLIENT_ACCESS_TOKEN")  # For MCP gateway auth
    github_token = os.getenv("GITHUB_TOKEN")  # For GitHub API
    
    if not mcp_token:
        print("❌ Error: MCP_CLIENT_ACCESS_TOKEN not set")
        print("   Run: just mcp-client-token")
        return
    
    print(f"Connecting to MCP server at {server_url}")
    print("Using OAuth Bearer token for authentication")
    
    # Create client with OAuth authentication
    async with MCPFetchClient(
        server_url,
        access_token=mcp_token,  # This authenticates to the MCP gateway
        timeout=60.0  # Longer timeout for OAuth flows
    ) as client:
        try:
            # Initialize the session
            print("\n1. Initializing authenticated MCP session...")
            info = await client.initialize(
                client_name="oauth-example-client",
                client_version="1.0.0"
            )
            
            print(f"   Connected to: {info['serverInfo']['name']}")
            print(f"   Session established with OAuth authentication")
            
            # Example 1: Fetch from a public API
            print("\n2. Fetching public API (no additional auth needed)...")
            result = await client.fetch("https://api.github.com/meta")
            meta = json.loads(result.text)
            print(f"   GitHub API version: {meta.get('api_version')}")
            
            # Example 2: Fetch using GitHub token (if available)
            if github_token:
                await fetch_github_user(client, github_token)
            else:
                print("\n3. Skipping GitHub user fetch (GITHUB_TOKEN not set)")
            
            # Example 3: Fetch protected resource through MCP gateway
            # The gateway handles auth via our Bearer token
            await fetch_protected_resource(client)
            
            # Example 4: Demonstrate error handling for unauthorized requests
            print("\n4. Testing unauthorized request handling...")
            try:
                result = await client.fetch(
                    "https://api.github.com/user",
                    headers={"Authorization": "token invalid-token"}
                )
                print(f"   Status: {result.status}")
                if result.status == 401:
                    print("   ✓ Correctly received 401 Unauthorized")
            except MCPError as e:
                print(f"   MCP Error: {e}")
            
        except MCPError as e:
            print(f"\n❌ MCP Error: {e}")
            
            # OAuth-specific error handling
            if hasattr(e, 'code') and e.code == -32603:  # Internal error
                print("\n   Possible authentication issues:")
                print("   - Check if MCP_CLIENT_ACCESS_TOKEN is valid")
                print("   - Verify the token hasn't expired")
                print("   - Run 'just mcp-client-token' to get a new token")


if __name__ == "__main__":
    print("MCP Fetch Client - OAuth Authentication Example")
    print("=" * 50)
    asyncio.run(main())