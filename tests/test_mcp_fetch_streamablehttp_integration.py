"""Integration tests for native MCP fetch streamablehttp server."""

import json
import pytest
import httpx
from unittest.mock import patch, AsyncMock

from tests.conftest import assert_integration_test, ensure_services_ready


@pytest.fixture
def fetch_native_base_url(base_domain):
    """Base URL for native fetch service."""
    return f"https://mcp-fetch-native.{base_domain}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_health_check(fetch_native_base_url):
    """Test health check endpoint."""
    await ensure_services_ready()
    
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(f"{fetch_native_base_url}/health")
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_requires_auth(fetch_native_base_url):
    """Test that MCP endpoint requires authentication."""
    await ensure_services_ready()
    
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            f"{fetch_native_base_url}/mcp",
            json={"jsonrpc": "2.0", "method": "initialize", "id": 1},
            headers={"Content-Type": "application/json"}
        )
        
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_cors_preflight(fetch_native_base_url):
    """Test CORS preflight handling."""
    await ensure_services_ready()
    
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.options(
            f"{fetch_native_base_url}/mcp",
            headers={
                "Origin": "https://claude.ai",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization"
            }
        )
        
    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "*"
    assert "POST" in response.headers["Access-Control-Allow-Methods"]
    assert "Authorization" in response.headers["Access-Control-Allow-Headers"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_initialize(fetch_native_base_url, valid_oauth_token):
    """Test MCP initialization."""
    await ensure_services_ready()
    
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            f"{fetch_native_base_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {}
                },
                "id": 1
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {valid_oauth_token}",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    assert "result" in data
    
    result = data["result"]
    assert result["protocolVersion"] == "2025-06-18"
    assert "serverInfo" in result
    assert result["serverInfo"]["name"] == "mcp-fetch-streamablehttp"
    assert "capabilities" in result
    assert "tools" in result["capabilities"]
    
    # Check session ID header
    assert "Mcp-Session-Id" in response.headers


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_list_tools(fetch_native_base_url, valid_oauth_token):
    """Test listing available tools."""
    await ensure_services_ready()
    
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            f"{fetch_native_base_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 2
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {valid_oauth_token}"
            }
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 2
    assert "result" in data
    
    result = data["result"]
    assert "tools" in result
    assert len(result["tools"]) >= 1
    
    # Check fetch tool
    fetch_tool = next((t for t in result["tools"] if t["name"] == "fetch"), None)
    assert fetch_tool is not None
    assert fetch_tool["description"] == "Fetch a URL and return its contents"
    assert "inputSchema" in fetch_tool


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_call_tool_fetch(fetch_native_base_url, valid_oauth_token):
    """Test calling the fetch tool."""
    await ensure_services_ready()
    
    # Mock httpx to avoid actual external requests
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = "<html><head><title>Test Page</title></head><body>Hello World</body></html>"
    mock_response.headers = {"content-type": "text/html"}
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_instance
        
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                f"{fetch_native_base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "fetch",
                        "arguments": {
                            "url": "https://example.com",
                            "method": "GET"
                        }
                    },
                    "id": 3
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {valid_oauth_token}"
                }
            )
            
    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert "result" in data
    
    result = data["result"]
    assert "content" in result
    assert len(result["content"]) >= 1
    
    content = result["content"][0]
    assert content["type"] == "text"
    assert "Hello World" in content["text"]
    assert content.get("title") == "Test Page"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_invalid_json_rpc(fetch_native_base_url, valid_oauth_token):
    """Test handling of invalid JSON-RPC requests."""
    await ensure_services_ready()
    
    async with httpx.AsyncClient(verify=False) as client:
        # Missing jsonrpc version
        response = await client.post(
            f"{fetch_native_base_url}/mcp",
            json={"method": "test", "id": 1},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {valid_oauth_token}"
            }
        )
        
    assert response.status_code == 400
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert "error" in data
    assert data["error"]["code"] == -32600
    assert "Invalid Request" in data["error"]["message"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_unknown_method(fetch_native_base_url, valid_oauth_token):
    """Test handling of unknown methods."""
    await ensure_services_ready()
    
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            f"{fetch_native_base_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "unknown/method",
                "id": 1
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {valid_oauth_token}"
            }
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert "error" in data
    assert data["error"]["code"] == -32601
    assert "Method not found" in data["error"]["message"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_oauth_discovery(fetch_native_base_url):
    """Test OAuth discovery endpoint routing."""
    await ensure_services_ready()
    
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(
            f"{fetch_native_base_url}/.well-known/oauth-authorization-server"
        )
        
    assert response.status_code == 200
    data = response.json()
    
    # Should be routed to auth service
    assert "issuer" in data
    assert "authorization_endpoint" in data
    assert "token_endpoint" in data
    assert "registration_endpoint" in data