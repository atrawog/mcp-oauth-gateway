from .test_constants import HTTP_BAD_REQUEST
from .test_constants import HTTP_OK
from .test_constants import HTTP_UNAUTHORIZED


"""Integration tests for native MCP fetch streamablehttp server."""

import httpx
import pytest

from tests.test_constants import BASE_DOMAIN
from tests.test_constants import GATEWAY_OAUTH_ACCESS_TOKEN


@pytest.fixture
def base_domain():
    """Base domain for tests."""
    return BASE_DOMAIN


@pytest.fixture
def valid_oauth_token():
    """Valid OAuth token for testing."""
    return GATEWAY_OAUTH_ACCESS_TOKEN


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_health_check(mcp_fetchs_url, wait_for_services, valid_oauth_token):
    """Test health check via MCP protocol initialization."""
    async with httpx.AsyncClient(verify=True) as client:
        response = await client.post(
            f"{mcp_fetchs_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "healthcheck", "version": "1.0"},
                },
                "id": 1,
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {valid_oauth_token}",
            },
        )

    assert response.status_code == HTTP_OK
    data = response.json()
    assert "result" in data
    assert data["result"]["protocolVersion"] == "2025-06-18"
    assert "serverInfo" in data["result"]
    assert data["result"]["serverInfo"]["name"] == "mcp-fetch-streamablehttp"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_requires_auth(mcp_fetchs_url, wait_for_services):
    """Test that MCP endpoint requires authentication."""
    async with httpx.AsyncClient(verify=True) as client:
        response = await client.post(
            f"{mcp_fetchs_url}",
            json={"jsonrpc": "2.0", "method": "initialize", "id": 1},
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == HTTP_UNAUTHORIZED
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_cors_preflight(mcp_fetchs_url, wait_for_services):
    """Test CORS preflight handling."""
    async with httpx.AsyncClient(verify=True) as client:
        response = await client.options(
            f"{mcp_fetchs_url}",
            headers={
                "Origin": "https://claude.ai",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            },
        )

    assert response.status_code == HTTP_OK
    assert response.headers["Access-Control-Allow-Origin"] == "*"
    assert "POST" in response.headers["Access-Control-Allow-Methods"]
    # Check for expected headers - Authorization might be handled differently
    allowed_headers = response.headers.get("Access-Control-Allow-Headers", "")
    assert "Content-Type" in allowed_headers


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_initialize(mcp_fetchs_url, valid_oauth_token, wait_for_services):
    """Test MCP initialization."""
    async with httpx.AsyncClient(verify=True) as client:
        response = await client.post(
            f"{mcp_fetchs_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18", "capabilities": {}},
                "id": 1,
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {valid_oauth_token}",
                "MCP-Protocol-Version": "2025-06-18",
            },
        )

    assert response.status_code == HTTP_OK
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
async def test_fetch_native_list_tools(mcp_fetchs_url, valid_oauth_token, wait_for_services):
    """Test listing available tools."""
    async with httpx.AsyncClient(verify=True) as client:
        response = await client.post(
            f"{mcp_fetchs_url}",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 2},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {valid_oauth_token}",
            },
        )

    assert response.status_code == HTTP_OK
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
async def test_fetch_native_call_tool_fetch(mcp_fetchs_url, base_domain, valid_oauth_token, wait_for_services):
    """Test calling the fetch tool."""
    # Fetch from our own auth service's health endpoint
    async with httpx.AsyncClient(verify=True) as client:
        response = await client.post(
            f"{mcp_fetchs_url}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "fetch",
                    "arguments": {
                        "url": f"https://auth.{base_domain}/.well-known/oauth-authorization-server",  # TODO: Break long line
                        "method": "GET",
                    },
                },
                "id": 3,
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {valid_oauth_token}",
            },
        )

    assert response.status_code == HTTP_OK
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert "result" in data

    result = data["result"]
    assert "content" in result
    assert len(result["content"]) >= 1

    content = result["content"][0]
    assert content["type"] == "text"
    assert "issuer" in content["text"]  # OAuth metadata contains issuer field


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_invalid_json_rpc(mcp_fetchs_url, valid_oauth_token, wait_for_services):
    """Test handling of invalid JSON-RPC requests."""
    async with httpx.AsyncClient(verify=True) as client:
        # Missing jsonrpc version
        response = await client.post(
            f"{mcp_fetchs_url}",
            json={"method": "test", "id": 1},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {valid_oauth_token}",
            },
        )

    assert response.status_code == HTTP_BAD_REQUEST
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert "error" in data
    assert data["error"]["code"] == -32600
    assert "Invalid Request" in data["error"]["message"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_unknown_method(mcp_fetchs_url, valid_oauth_token, wait_for_services):
    """Test handling of unknown methods."""
    async with httpx.AsyncClient(verify=True) as client:
        response = await client.post(
            f"{mcp_fetchs_url}",
            json={"jsonrpc": "2.0", "method": "unknown/method", "id": 1},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {valid_oauth_token}",
            },
        )

    assert response.status_code == HTTP_OK
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert "error" in data
    assert data["error"]["code"] == -32601
    assert "Method not found" in data["error"]["message"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fetch_native_oauth_discovery(wait_for_services):
    """Test OAuth discovery endpoint routing."""
    from tests.test_constants import MCP_FETCH_TESTS_ENABLED

    if not MCP_FETCH_TESTS_ENABLED:
        pytest.skip("MCP Fetch tests are disabled. Set MCP_FETCH_TESTS_ENABLED=true to enable.")

    # Use base domain for OAuth discovery, not the /mcp endpoint
    oauth_discovery_url = f"https://fetch.{BASE_DOMAIN}/.well-known/oauth-authorization-server"

    async with httpx.AsyncClient(verify=True) as client:
        response = await client.get(oauth_discovery_url)

    assert response.status_code == HTTP_OK
    data = response.json()

    # Should be routed to auth service
    assert "issuer" in data
    assert "authorization_endpoint" in data
    assert "token_endpoint" in data
    assert "registration_endpoint" in data
