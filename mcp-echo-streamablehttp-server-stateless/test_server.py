#!/usr/bin/env python3
"""Test script for the MCP Echo StreamableHTTP Server."""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any


async def send_request(url: str, method: str, params: Dict[str, Any], id: int) -> Dict[str, Any]:
    """Send a JSON-RPC request to the server."""
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": id
    }
    
    print(f"\n→ Sending {method} request:")
    print(json.dumps(request, indent=2))
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=request,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
        )
        
        print(f"\n← Response status: {response.status_code}")
        print(f"← Response headers: {dict(response.headers)}")
        print(f"← Response body:\n{response.text}")
        
        # Parse SSE response
        for line in response.text.strip().split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                return data
        
        raise ValueError("No data found in SSE response")


async def test_server(base_url: str = "http://localhost:3000"):
    """Test the MCP Echo server."""
    url = f"{base_url}/mcp"
    
    print("="*60)
    print("Testing MCP Echo StreamableHTTP Server")
    print("="*60)
    
    try:
        # Test 1: Initialize
        print("\n1. Testing initialize...")
        result = await send_request(url, "initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }, 1)
        assert "result" in result
        assert "protocolVersion" in result["result"]
        print("✓ Initialize successful")
        
        # Test 2: List tools
        print("\n2. Testing tools/list...")
        result = await send_request(url, "tools/list", {}, 2)
        assert "result" in result
        assert "tools" in result["result"]
        tools = result["result"]["tools"]
        assert len(tools) == 2
        assert any(t["name"] == "echo" for t in tools)
        assert any(t["name"] == "printEnv" for t in tools)
        print("✓ List tools successful")
        
        # Test 3: Echo tool
        print("\n3. Testing echo tool...")
        result = await send_request(url, "tools/call", {
            "name": "echo",
            "arguments": {
                "message": "Hello, MCP!"
            }
        }, 3)
        assert "result" in result
        assert "content" in result["result"]
        assert result["result"]["content"][0]["text"] == "Hello, MCP!"
        print("✓ Echo tool successful")
        
        # Test 4: PrintEnv tool
        print("\n4. Testing printEnv tool...")
        result = await send_request(url, "tools/call", {
            "name": "printEnv",
            "arguments": {
                "name": "USER"
            }
        }, 4)
        assert "result" in result
        assert "content" in result["result"]
        print(f"✓ PrintEnv tool successful: {result['result']['content'][0]['text']}")
        
        # Test 5: Error handling - invalid tool
        print("\n5. Testing error handling...")
        try:
            result = await send_request(url, "tools/call", {
                "name": "invalid_tool",
                "arguments": {}
            }, 5)
            print("✗ Expected error but got success")
        except httpx.HTTPStatusError:
            print("✓ Error handling successful")
        
        print("\n" + "="*60)
        print("All tests passed! 🎉")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test MCP Echo Server")
    parser.add_argument("--url", default="http://localhost:3000", help="Base URL of the server")
    args = parser.parse_args()
    
    asyncio.run(test_server(args.url))