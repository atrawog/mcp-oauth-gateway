"""Debug test for MCP proxy issue."""

import json
import os

import httpx
import pytest

from .test_constants import MCP_PROTOCOL_VERSION
from .test_constants import HTTP_OK
from .test_constants import HTTP_CREATED
from .test_constants import HTTP_NO_CONTENT
from .test_constants import HTTP_UNAUTHORIZED
from .test_constants import HTTP_NOT_FOUND
from .test_constants import HTTP_UNPROCESSABLE_ENTITY


MCP_CLIENT_ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN")


@pytest.mark.asyncio
async def test_simple_initialize(
    http_client: httpx.AsyncClient, wait_for_services, capfd, mcp_fetch_url
):
    """Simple test to debug initialize issue."""
    if not MCP_CLIENT_ACCESS_TOKEN:
        pytest.fail(
            "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
        )

    print(f"\nMCP_FETCH_URL: {mcp_fetch_url}")
    print(f"MCP_PROTOCOL_VERSION: {MCP_PROTOCOL_VERSION}")
    print(f"Token: {MCP_CLIENT_ACCESS_TOKEN[:20]}...")

    request_data = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "debug-test", "version": "1.0.0"},
        },
        "id": 1,
    }

    print(f"\nRequest: {json.dumps(request_data, indent=2)}")

    response = await http_client.post(
        f"{mcp_fetch_url}",
        json=request_data,
        headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

    print(f"\nResponse status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    print(f"Response body: {response.text}")

    if response.status_code == HTTP_OK:
        data = response.json()
        if "error" in data:
            print(f"\nJSON-RPC Error: {data['error']}")
            raise AssertionError(f"Got error: {data['error']}")
        print(f"\nJSON-RPC Result: {json.dumps(data.get('result', {}), indent=2)}")

        # Now test with session ID
        session_id = response.headers.get("Mcp-Session-Id")
        print(f"\nSession ID from header: {session_id}")

        if session_id:
            # Try tools/list with session ID
            tools_response = await http_client.post(
                f"{mcp_fetch_url}",
                json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
                headers={
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Mcp-Session-Id": session_id,
                }, timeout=30.0)
            print(f"\nTools response status: {tools_response.status_code}")
            print(f"Tools response: {tools_response.text}")
