#!/usr/bin/env python3
"""Test MCP redirect behavior."""

import os
import sys

import httpx


# Get OAuth token from environment
oauth_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
if not oauth_token:
    print("ERROR: No GATEWAY_OAUTH_ACCESS_TOKEN found in environment")
    sys.exit(1)

base_url = "https://mcp-fetch.atradev.org"

# Test 1: Direct request to /mcp (no trailing slash)
print("Test 1: Request to /mcp (no trailing slash)")
response = httpx.post(
    f"{base_url}/mcp",
    json={"jsonrpc": "2.0", "method": "ping", "id": 1},
    headers={
        "Authorization": f"Bearer {oauth_token}",
        "Content-Type": "application/json",
    },
    follow_redirects=False,
)
print(f"  Status: {response.status_code}")
if response.status_code == 307:
    print(f"  Location: {response.headers.get('location')}")
print(f"  Headers: {dict(response.headers)}")

# Test 2: Request to /mcp/ (with trailing slash)
print("\nTest 2: Request to /mcp/ (with trailing slash)")
response = httpx.post(
    f"{base_url}/mcp/",
    json={"jsonrpc": "2.0", "method": "ping", "id": 2},
    headers={
        "Authorization": f"Bearer {oauth_token}",
        "Content-Type": "application/json",
    },
    follow_redirects=False,
)
print(f"  Status: {response.status_code}")
print(f"  Body preview: {response.text[:200]}")

# Test 3: Follow redirects
print("\nTest 3: Request to /mcp with follow_redirects=True")
response = httpx.post(
    f"{base_url}/mcp",
    json={"jsonrpc": "2.0", "method": "ping", "id": 3},
    headers={
        "Authorization": f"Bearer {oauth_token}",
        "Content-Type": "application/json",
    },
    follow_redirects=True,
)
print(f"  Status: {response.status_code}")
print(f"  Final URL: {response.url}")
print(f"  Body preview: {response.text[:200]}")
