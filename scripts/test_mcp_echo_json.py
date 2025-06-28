#!/usr/bin/env python3
"""Test mcp-echo with JSON-only Accept header (like VS Code)."""

import json
import sys

import requests


def test_json_response():
    """Test mcp-echo returns JSON when client only accepts JSON."""
    base_url = "http://mcp-echo-stateful:3000/mcp"

    # Test 1: Initialize with JSON-only Accept header
    print("Test 1: Initialize with JSON-only Accept header")
    print("-" * 50)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",  # Only JSON, no SSE
        "MCP-Protocol-Version": "2025-06-18",
    }

    data = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
        "id": 1,
    }

    response = requests.post(base_url, json=data, headers=headers, timeout=30.0)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'Not specified')}")

    try:
        result = response.json()
        print(f"Response Body: {json.dumps(result, indent=2)}")

        # Verify it's a valid JSON-RPC response
        if "jsonrpc" in result and "id" in result and "result" in result:
            print("\n✓ SUCCESS: Got valid JSON response (not SSE)")
        else:
            print("\n✗ FAIL: Response structure invalid")
            return False

    except json.JSONDecodeError:
        print(f"Response Body (raw): {response.text}")
        print("\n✗ FAIL: Response is not valid JSON")
        return False

    # Test 2: With SSE in Accept header
    print("\n\nTest 2: Initialize with SSE Accept header")
    print("-" * 50)

    headers["Accept"] = "application/json, text/event-stream"

    response = requests.post(base_url, json=data, headers=headers, timeout=30.0)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'Not specified')}")

    if "text/event-stream" in response.headers.get("Content-Type", ""):
        print("Response Body (SSE format):")
        print(response.text[:200] + "..." if len(response.text) > 200 else response.text)
        print("\n✓ SUCCESS: Got SSE response when requested")
    else:
        print("\n✗ FAIL: Expected SSE response")
        return False

    return True


if __name__ == "__main__":
    try:
        success = test_json_response()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)
