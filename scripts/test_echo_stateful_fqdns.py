#!/usr/bin/env python3
"""Test script to verify all echo-stateful FQDNs are working correctly."""

import asyncio
import os
import sys

import httpx


async def test_fqdn(url: str, token: str) -> tuple[str, bool, str]:
    """Test a single FQDN by sending an initialize request."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Send MCP initialize request
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": os.getenv("MCP_PROTOCOL_VERSION", "2025-06-18"),
                        "capabilities": {},
                        "clientInfo": {"name": "fqdn-test", "version": "1.0"},
                    },
                    "id": 1,
                },
            )

            if response.status_code == 200:
                # Check if response contains expected protocol version
                content = response.text
                if "protocolVersion" in content:
                    return url, True, "✅ Success"
                return url, False, f"❌ Invalid response: {content[:100]}..."
            return url, False, f"❌ HTTP {response.status_code}: {response.text[:100]}..."

        except Exception as e:
            return url, False, f"❌ Error: {e!s}"


async def main():
    """Test all echo-stateful FQDNs."""
    # Get the token
    token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    if not token:
        print("❌ GATEWAY_OAUTH_ACCESS_TOKEN not set in environment")
        sys.exit(1)

    # Get all URLs from environment
    urls_env = os.getenv("MCP_ECHO_STATEFUL_URLS", "")
    if not urls_env:
        print("❌ MCP_ECHO_STATEFUL_URLS not set in environment")
        sys.exit(1)

    urls = [url.strip() for url in urls_env.split(",") if url.strip()]

    print(f"🧪 Testing {len(urls)} echo-stateful FQDNs...")
    print("=" * 80)

    # Test all URLs concurrently
    results = await asyncio.gather(*[test_fqdn(url, token) for url in urls])

    # Print results
    success_count = 0
    for url, success, message in results:
        print(f"{url}: {message}")
        if success:
            success_count += 1

    print("=" * 80)
    print(f"✅ Passed: {success_count}/{len(urls)}")
    print(f"❌ Failed: {len(urls) - success_count}/{len(urls)}")

    # Exit with error if any failed
    if success_count < len(urls):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
