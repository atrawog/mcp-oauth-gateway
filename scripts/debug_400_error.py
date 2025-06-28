#!/usr/bin/env python3
"""Debug script to see what 400 errors we're getting from MCP endpoints."""

import asyncio
import json
import os

import httpx


MCP_CLIENT_ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN")
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "atratest.org")
MCP_PROTOCOL_VERSION = os.getenv("MCP_PROTOCOL_VERSION", "2025-06-18")
MCP_TESTING_URL = f"https://echo-stateless.{BASE_DOMAIN}/mcp"


async def test_request(description: str, headers: dict, json_data: dict):
    """Test a request and show the response."""
    print(f"\n{'=' * 60}")
    print(f"Testing: {description}")
    print(f"URL: {MCP_TESTING_URL}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"JSON: {json.dumps(json_data, indent=2)}")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                MCP_TESTING_URL,
                json=json_data,
                headers=headers,
            )

            print(f"Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")

            try:
                response_json = response.json()
                print(f"Response JSON: {json.dumps(response_json, indent=2)}")
            except:
                print(f"Response Text: {response.text}")

        except Exception as e:
            print(f"Error: {e}")


async def main():
    if not MCP_CLIENT_ACCESS_TOKEN:
        print("❌ No MCP_CLIENT_ACCESS_TOKEN found!")
        return

    # Test 1: Missing Accept header
    await test_request(
        "Missing Accept header",
        {
            "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
        },
        {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
            "id": 1,
        },
    )

    # Test 2: With Accept header
    await test_request(
        "With Accept header",
        {
            "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
        },
        {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
            "id": 1,
        },
    )

    # Test 3: Wrong protocol version (hardcoded)
    await test_request(
        "Wrong protocol version (hardcoded)",
        {
            "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": "2025-03-26",  # Wrong version
        },
        {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",  # Wrong version
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
            "id": 1,
        },
    )


if __name__ == "__main__":
    asyncio.run(main())
