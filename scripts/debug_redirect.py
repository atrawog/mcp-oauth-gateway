#!/usr/bin/env python3
"""Debug MCP redirect issue."""

import httpx


# Test direct request
print("Test 1: Direct request to /mcp (no redirect follow)")
r = httpx.post(
    f"https://mcp-fetch.{os.getenv('BASE_DOMAIN')}/mcp",
    headers={"Authorization": "Bearer test"},
    json={"jsonrpc": "2.0", "method": "ping", "id": 1},
    follow_redirects=False,
)
print(f"  Status: {r.status_code}")
if r.status_code == 307:
    print(f"  Location: {r.headers.get('location')}")
print(f"  Headers: {dict(r.headers)}")
print()

# Test with redirect follow
print("Test 2: Request to /mcp with redirect follow")
try:
    r = httpx.post(
        f"https://mcp-fetch.{os.getenv('BASE_DOMAIN')}/mcp",
        headers={"Authorization": "Bearer test"},
        json={"jsonrpc": "2.0", "method": "ping", "id": 1},
        follow_redirects=True,
    )
    print(f"  Status: {r.status_code}")
    print(f"  Final URL: {r.url}")
    print(f"  Body: {r.text[:100]}")
except Exception as e:
    print(f"  Error: {e}")
print()

# Test direct to /mcp/
print("Test 3: Direct request to /mcp/ (with trailing slash)")
r = httpx.post(
    f"https://mcp-fetch.{os.getenv('BASE_DOMAIN')}/mcp/",
    headers={"Authorization": "Bearer test"},
    json={"jsonrpc": "2.0", "method": "ping", "id": 1},
    follow_redirects=False,
)
print(f"  Status: {r.status_code}")
print(f"  Body: {r.text[:100]}")
