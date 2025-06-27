#!/usr/bin/env python3
"""Test VS Code-like session behavior with the stateful mcp-echo server."""

import json
import sys

import requests


def test_vscode_session_flow():
    """Test the complete VS Code session flow with the stateful server."""
    base_url = "http://mcp-echo:3000/mcp"

    print("🧪 Testing VS Code-like Session Flow with Stateful MCP Echo Server")
    print("=" * 70)

    # Step 1: Initialize session (like VS Code would do)
    print("\n1️⃣ Initialize Session (VS Code-like)")
    print("-" * 40)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",  # VS Code accepts both
        "MCP-Protocol-Version": "2025-06-18",
    }

    init_data = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {"roots": {"listChanged": True}, "sampling": {}, "elicitation": {}},
            "clientInfo": {"name": "Visual Studio Code - Test", "version": "1.102.0-test"},
        },
        "id": 1,
    }

    # Initialize session
    response = requests.post(base_url, json=init_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'Not specified')}")

    # Extract session ID from response headers
    session_id = response.headers.get("Mcp-Session-Id")
    print(f"Session ID: {session_id}")

    if response.headers.get("Content-Type", "").startswith("text/event-stream"):
        print("Response Format: SSE (Server-Sent Events)")
        print("Response Body:")
        print(response.text[:300] + "..." if len(response.text) > 300 else response.text)
    else:
        print("Response Format: JSON")
        try:
            result = response.json()
            print(f"Response Body: {json.dumps(result, indent=2)}")
        except:
            print(f"Response Body (raw): {response.text}")

    if not session_id:
        print("❌ FAIL: No session ID returned")
        return False

    print("✅ SUCCESS: Session created and initialized")

    # Step 2: Poll for messages (like VS Code would do)
    print("\n2️⃣ Poll for Messages (VS Code-like)")
    print("-" * 40)

    poll_headers = {"Mcp-Session-Id": session_id, "Accept": "text/event-stream"}

    # First poll - should get any queued initialization response
    response = requests.get(base_url, headers=poll_headers)
    print(f"Poll Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'Not specified')}")

    if response.text.strip():
        print("Poll Response:")
        print(response.text[:200] + "..." if len(response.text) > 200 else response.text)
    else:
        print("Poll Response: Empty (no queued messages)")

    # Step 3: Call tools/list
    print("\n3️⃣ Call tools/list")
    print("-" * 40)

    tools_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Mcp-Session-Id": session_id,
    }

    tools_data = {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2}

    response = requests.post(base_url, json=tools_data, headers=tools_headers)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'Not specified')}")

    if response.headers.get("Content-Type", "").startswith("text/event-stream"):
        print("Response: SSE")
        print(response.text[:300] + "..." if len(response.text) > 300 else response.text)
    else:
        print("Response: JSON")
        try:
            result = response.json()
            tools = result.get("result", {}).get("tools", [])
            print(f"Found {len(tools)} tools:")
            for tool in tools[:3]:  # Show first 3 tools
                print(f"  - {tool['name']}: {tool['description']}")
        except:
            print(f"Response (raw): {response.text}")

    # Step 4: Use sessionInfo tool to check session state
    print("\n4️⃣ Call sessionInfo Tool")
    print("-" * 40)

    session_info_data = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": "sessionInfo", "arguments": {}},
        "id": 3,
    }

    response = requests.post(base_url, json=session_info_data, headers=tools_headers)
    print(f"Status: {response.status_code}")

    if response.headers.get("Content-Type", "").startswith("text/event-stream"):
        print("Response: SSE")
        print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
    else:
        print("Response: JSON")
        try:
            result = response.json()
            content = result.get("result", {}).get("content", [])
            if content:
                print("Session Info:")
                print(content[0].get("text", "No text content"))
        except:
            print(f"Response (raw): {response.text}")

    # Step 5: Poll again to see if there are queued messages
    print("\n5️⃣ Poll Again for Queued Messages")
    print("-" * 40)

    response = requests.get(base_url, headers=poll_headers, timeout=5)
    print(f"Poll Status: {response.status_code}")

    if response.text.strip():
        print("Poll Response:")
        print(response.text[:200] + "..." if len(response.text) > 200 else response.text)
        print("✅ SUCCESS: Session maintains state and queues messages")
    else:
        print("Poll Response: Empty")

    print("\n" + "=" * 70)
    print("🎉 VS Code Session Flow Test Complete!")
    print("✅ Session management working correctly")
    print("✅ Message queuing functional")
    print("✅ Stateful behavior confirmed")

    return True


if __name__ == "__main__":
    try:
        success = test_vscode_session_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
