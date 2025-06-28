#!/usr/bin/env python3
"""Test MCP Echo server SSE response handling."""

import json
import time

import requests


def test_mcp_echo():
    """Test the MCP echo server initialize request."""
    url = "http://localhost:3000/mcp"

    # Prepare the initialize request
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

    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

    print("Sending POST request to:", url)
    print("Headers:", json.dumps(headers, indent=2))
    print("Data:", json.dumps(data, indent=2))
    print()

    # Send POST request
    response = requests.post(url, json=data, headers=headers, stream=True, timeout=30.0)

    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    print()

    if response.status_code == 200:
        print("Response content:")
        for line in response.iter_lines():
            if line:
                print(line.decode("utf-8"))
    else:
        print("Error response:", response.text)

    # Now test GET request
    print("\n" + "=" * 50 + "\n")
    print("Testing GET request...")

    get_response = requests.get(url, headers={"Accept": "text/event-stream"}, stream=True, timeout=30.0)
    print(f"GET Response status: {get_response.status_code}")
    print(f"GET Response headers: {dict(get_response.headers)}")
    print()

    if get_response.status_code == 200:
        print("GET Response content (first 5 lines):")
        for i, line in enumerate(get_response.iter_lines()):
            if i >= 5:
                break
            if line:
                print(line.decode("utf-8"))
            time.sleep(0.1)


if __name__ == "__main__":
    test_mcp_echo()
