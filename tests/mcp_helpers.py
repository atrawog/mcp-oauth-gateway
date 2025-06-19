"""
Helper functions for MCP testing
"""
import json
import httpx
from typing import Optional, Dict, Any, Tuple


async def initialize_mcp_session(
    http_client: httpx.AsyncClient,
    mcp_url: str,
    auth_token: str,
    protocol_version: str = "2025-06-18"
) -> Tuple[str, Dict[str, Any]]:
    """
    Initialize an MCP session properly.
    
    Returns:
        (session_id, init_result) - The session ID and initialization result
    """
    # Step 1: Initialize the session
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": protocol_version,
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        },
        "id": "init-1"
    }
    
    init_response = await http_client.post(
        f"{mcp_url}/mcp",
        json=init_request,
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    )
    
    if init_response.status_code != 200:
        raise RuntimeError(f"Failed to initialize MCP session: {init_response.status_code} - {init_response.text}")
    
    # Get session ID from response headers
    session_id = init_response.headers.get("Mcp-Session-Id")
    if not session_id:
        raise RuntimeError("No session ID returned from MCP initialization")
    
    init_result = init_response.json()
    if "error" in init_result:
        raise RuntimeError(f"MCP initialization error: {init_result['error']}")
    
    # Step 2: Send initialized notification  
    initialized_notification = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    
    notify_response = await http_client.post(
        f"{mcp_url}/mcp",
        json=initialized_notification,
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "Mcp-Session-Id": session_id
        }
    )
    
    # Notification may not return 200, that's okay
    
    return session_id, init_result["result"]


async def call_mcp_tool(
    http_client: httpx.AsyncClient,
    mcp_url: str,
    auth_token: str,
    session_id: str,
    tool_name: str,
    arguments: Dict[str, Any],
    request_id: str = "tool-call-1"
) -> Dict[str, Any]:
    """
    Call an MCP tool with proper session handling.
    """
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": request_id
    }
    
    response = await http_client.post(
        f"{mcp_url}/mcp",
        json=request,
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "Mcp-Session-Id": session_id
        }
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Tool call failed: {response.status_code} - {response.text}")
    
    return response.json()


async def list_mcp_tools(
    http_client: httpx.AsyncClient,
    mcp_url: str,
    auth_token: str,
    session_id: str
) -> Dict[str, Any]:
    """
    List available MCP tools.
    """
    request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": "list-1"
    }
    
    response = await http_client.post(
        f"{mcp_url}/mcp",
        json=request,
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "Mcp-Session-Id": session_id
        }
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Tool listing failed: {response.status_code} - {response.text}")
    
    return response.json()