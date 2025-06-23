"""Helper functions for MCP testing."""

import json
from typing import Any

import httpx


async def initialize_mcp_session(
    http_client: httpx.AsyncClient,
    mcp_url: str,
    auth_token: str,
    protocol_version: str = "2025-06-18",
) -> tuple[str, dict[str, Any]]:
    """Initialize an MCP session properly.

    Returns:
        (session_id, init_result) - The session ID and initialization result
    """
    # Step 1: Initialize the session
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": protocol_version,
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
        "id": "init-1",
    }

    init_response = await http_client.post(
        mcp_url,
        json=init_request,
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )

    if init_response.status_code != 200:
        raise RuntimeError(
            f"Failed to initialize MCP session: {init_response.status_code} - {init_response.text}"
        )

    # Get session ID from response headers
    session_id = init_response.headers.get("Mcp-Session-Id")
    if not session_id:
        raise RuntimeError("No session ID returned from MCP initialization")

    # Parse response based on content type
    content_type = init_response.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        # Parse SSE response
        init_result = None
        for line in init_response.text.strip().split("\n"):
            if line.startswith("data: "):
                init_result = json.loads(line[6:])
                break
        if not init_result:
            raise RuntimeError("Failed to parse SSE response from MCP initialization")
    else:
        init_result = init_response.json()

    if "error" in init_result:
        raise RuntimeError(f"MCP initialization error: {init_result['error']}")

    # Step 2: Send initialized notification
    initialized_notification = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    }

    await http_client.post(
        mcp_url,
        json=initialized_notification,
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Mcp-Session-Id": session_id,
        },
    )

    # Notification may not return 200, that's okay

    return session_id, init_result["result"]


async def call_mcp_tool(
    http_client: httpx.AsyncClient,
    mcp_url: str,
    auth_token: str,
    session_id: str,
    tool_name: str,
    arguments: dict[str, Any],
    request_id: str = "tool-call-1",
) -> dict[str, Any]:
    """Call an MCP tool with proper session handling."""
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
        "id": request_id,
    }

    response = await http_client.post(
        mcp_url,
        json=request,
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Mcp-Session-Id": session_id,
        },
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Tool call failed: {response.status_code} - {response.text}"
        )

    # Parse response based on content type
    content_type = response.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        # Parse SSE response
        result = None
        for line in response.text.strip().split("\n"):
            if line.startswith("data: "):
                result = json.loads(line[6:])
                break
        if not result:
            raise RuntimeError("Failed to parse SSE response from tool call")
        return result
    return response.json()


async def list_mcp_tools(
    http_client: httpx.AsyncClient, mcp_url: str, auth_token: str, session_id: str
) -> dict[str, Any]:
    """List available MCP tools."""
    request = {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": "list-1"}

    response = await http_client.post(
        mcp_url,
        json=request,
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Mcp-Session-Id": session_id,
        },
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Tool listing failed: {response.status_code} - {response.text}"
        )

    # Parse response based on content type
    content_type = response.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        # Parse SSE response
        result = None
        for line in response.text.strip().split("\n"):
            if line.startswith("data: "):
                result = json.loads(line[6:])
                break
        if not result:
            raise RuntimeError("Failed to parse SSE response from tool listing")
        return result
    return response.json()
