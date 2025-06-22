"""Test that mcp-fetch service is using the mcp-stdio-http package."""
import pytest
import httpx

@pytest.mark.asyncio
async def test_mcp_fetch_uses_package(mcp_fetch_url):
    """Verify mcp-fetch is running with the mcp-stdio-http package."""
    async with httpx.AsyncClient() as client:
        # Check health endpoint which includes server command info
        response = await client.get(f"{mcp_fetch_url}/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "healthy"
        
        # The server command should show it's running via mcp-stdio-http command
        # not the old mcp_stdio_http_proxy.py script
        server_command = health_data.get("server_command", "")
        
        # Should NOT contain the old proxy script name
        assert "mcp_stdio_http_proxy.py" not in server_command
        
        # Should be running the mcp_server_fetch module
        assert "mcp_server_fetch" in server_command
        
        print(f"✅ MCP fetch service is using the package correctly")
        print(f"   Server command: {server_command}")