#!/usr/bin/env python3
"""Test all MCP Fetch AI Model Hostnames using mcp-streamablehttp-client
Verifies that all 10 hostnames are properly configured and responding.
"""

import asyncio
import json
import os
import subprocess

from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Get all MCP fetch URLs from environment
MCP_FETCH_AI_URLS = os.getenv("MCP_FETCH_AI_URLS", "")
urls = [url.strip() for url in MCP_FETCH_AI_URLS.split(",") if url.strip()]

# Extract hostname names from URLs
MCP_HOSTNAMES = {}
for url in urls:
    # Extract the model name from URL like https://mcp-fetch-aria.atradev.org/mcp
    if "mcp-fetch-" in url:
        parts = url.split("mcp-fetch-")[1].split(".")[0]
        name = parts.capitalize()
        MCP_HOSTNAMES[name] = url

# Get auth token - try MCP_CLIENT_ACCESS_TOKEN first, then GATEWAY_OAUTH_ACCESS_TOKEN
MCP_CLIENT_ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN") or os.getenv(
    "GATEWAY_OAUTH_ACCESS_TOKEN"
)


async def test_mcp_hostname(name: str, url: str) -> tuple[str, bool, str]:
    """Test a single MCP hostname using mcp-streamablehttp-client."""
    if not url:
        return (name, False, "URL not configured in .env")

    if not MCP_CLIENT_ACCESS_TOKEN:
        return (name, False, "MCP_CLIENT_ACCESS_TOKEN not found in .env")

    # Create the JSON-RPC request for initialize
    request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": f"test-client-{name.lower()}", "version": "1.0.0"},
        },
        "id": 1,
    }

    # Use mcp-streamablehttp-client to test the connection
    env = os.environ.copy()
    env["MCP_SERVER_URL"] = url
    env["MCP_AUTH_TOKEN"] = MCP_CLIENT_ACCESS_TOKEN

    # Create a simple test by sending an initialize request
    cmd = [
        "python",
        "-c",
        f"""
import httpx
import json
import sys

url = "{url}"
token = "{MCP_CLIENT_ACCESS_TOKEN}"
request = {json.dumps(request)}

try:
    with httpx.Client() as client:
        response = client.post(
            url,
            json=request,
            headers={{"Authorization": f"Bearer {{token}}"}}
        )

        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                print("SUCCESS")
            else:
                print(f"ERROR: {{response.text}}")
        else:
            print(f"HTTP {{response.status_code}}: {{response.text}}")
except Exception as e:
    print(f"EXCEPTION: {{e}}")
""",
    ]

    try:
        # Run the test
        result = subprocess.run(
            cmd, check=False, capture_output=True, text=True, timeout=10
        )

        output = result.stdout.strip() or result.stderr.strip()

        if "SUCCESS" in output:
            return (name, True, "✅ Connected successfully")
        return (name, False, f"❌ {output}")

    except subprocess.TimeoutExpired:
        return (name, False, "❌ Connection timeout")
    except Exception as e:
        return (name, False, f"❌ Error: {e!s}")


async def test_all_hostnames():
    """Test all MCP hostnames concurrently."""
    print("🔍 Testing MCP Fetch AI Model Hostnames")
    print("=" * 60)

    # Check if we have the token
    if not MCP_CLIENT_ACCESS_TOKEN:
        print("❌ MCP_CLIENT_ACCESS_TOKEN not found in .env")
        print("   Run: just mcp-client-token")
        return

    # Create tasks for all hostnames
    tasks = []
    for name, url in MCP_HOSTNAMES.items():
        task = test_mcp_hostname(name, url)
        tasks.append(task)

    # Run all tests concurrently
    results = await asyncio.gather(*tasks)

    # Display results
    success_count = 0
    failed_count = 0

    print("\n📊 Test Results:")
    print("-" * 60)

    for name, success, message in sorted(results):
        status = "✅" if success else "❌"
        print(f"{status} {name:10} {message}")

        if success:
            success_count += 1
        else:
            failed_count += 1

    print("-" * 60)
    print(f"\n📈 Summary: {success_count} passed, {failed_count} failed")

    # Test accessing a resource through one of the hostnames
    if success_count > 0:
        print("\n🌐 Testing fetch capability on successful hostname...")
        # Pick the first successful hostname
        for name, success, _ in results:
            if success:
                await test_fetch_capability(name, MCP_HOSTNAMES[name])
                break


async def test_fetch_capability(name: str, url: str):
    """Test actual fetch capability through MCP."""
    print(f"\nTesting fetch on {name} ({url})")

    # Create a fetch request
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": "fetch", "arguments": {"url": "https://example.com"}},
        "id": 2,
    }

    cmd = [
        "python",
        "-c",
        f"""
import httpx
import json

url = "{url}"
token = "{MCP_CLIENT_ACCESS_TOKEN}"

# First initialize
init_request = {{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {{
        "protocolVersion": "2025-06-18",
        "capabilities": {{}},
        "clientInfo": {{"name": "test-fetch", "version": "1.0.0"}}
    }},
    "id": 1
}}

# Then fetch
fetch_request = {json.dumps(request)}

try:
    with httpx.Client() as client:
        # Initialize
        headers = {{"Authorization": f"Bearer {{token}}"}}
        init_response = client.post(url, json=init_request, headers=headers)

        if init_response.status_code == 200:
            # Store session ID if provided
            session_id = init_response.headers.get("Mcp-Session-Id")
            if session_id:
                headers["Mcp-Session-Id"] = session_id

            # Now try fetch
            fetch_response = client.post(url, json=fetch_request, headers=headers)

            if fetch_response.status_code == 200:
                result = fetch_response.json()
                if "result" in result:
                    print("✅ Fetch capability working!")
                else:
                    print(f"❌ Fetch failed: {{result}}")
            else:
                print(f"❌ Fetch HTTP {{fetch_response.status_code}}")
        else:
            print(f"❌ Init failed: HTTP {{init_response.status_code}}")

except Exception as e:
    print(f"❌ Exception: {{e}}")
""",
    ]

    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    print(result.stdout.strip() or result.stderr.strip())


if __name__ == "__main__":
    asyncio.run(test_all_hostnames())
