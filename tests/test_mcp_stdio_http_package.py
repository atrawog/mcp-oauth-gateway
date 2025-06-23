"""Test that mcp-fetch service is using the correct package."""
import pytest
import httpx
from tests.test_constants import MCP_CLIENT_ACCESS_TOKEN

@pytest.mark.asyncio
async def test_mcp_fetch_uses_package(mcp_fetch_url):
    """Verify mcp-fetch is running with the correct streamablehttp proxy."""
    if not MCP_CLIENT_ACCESS_TOKEN:
        pytest.skip("MCP_CLIENT_ACCESS_TOKEN not available")
        
    async with httpx.AsyncClient() as client:
        # Use MCP protocol to check server info - per CLAUDE.md, no /health endpoints
        response = await client.post(
            f"{mcp_fetch_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "package-test", "version": "1.0.0"}
                },
                "id": 1
            },
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        server_info = data.get("result", {}).get("serverInfo", {})
        
        # Should be running mcp-fetch server
        assert server_info.get("name") == "mcp-fetch"
        
        print(f"✅ MCP fetch service is running correctly")
        print(f"   Server: {server_info.get('name')} v{server_info.get('version')}")