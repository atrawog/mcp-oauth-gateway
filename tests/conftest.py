"""
Sacred Test Configuration - Following the divine commandment of NO MOCKING!
All tests run against real deployed services
NO HARDCODED VALUES - Everything from .env per Commandment 4!
"""
import pytest
import httpx
import asyncio
import os
from typing import AsyncGenerator
from dotenv import load_dotenv

# SACRED LAW: Load .env file BEFORE importing test_constants
# This ensures all environment variables are available!
load_dotenv()

# Import all configuration from test_constants
from .test_constants import (
    AUTH_BASE_URL, 
    MCP_FETCH_URL,
    SESSION_TIMEOUT,
    TEST_HTTP_TIMEOUT,
    TEST_MAX_RETRIES,
    TEST_RETRY_DELAY,
    TEST_CALLBACK_URL,
    TEST_CLIENT_NAME,
    TEST_CLIENT_SCOPE,
    GATEWAY_OAUTH_ACCESS_TOKEN
)

# MCP Client tokens for external client testing
MCP_CLIENT_ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN")
MCP_CLIENT_ID = os.getenv("MCP_CLIENT_ID")
MCP_CLIENT_SECRET = os.getenv("MCP_CLIENT_SECRET")

# pytest-asyncio handles event loop automatically with asyncio_mode = auto

@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provides an async HTTP client for tests"""
    # Use timeout from test_constants - already validated!
    async with httpx.AsyncClient(timeout=TEST_HTTP_TIMEOUT) as client:
        yield client

@pytest.fixture
async def wait_for_services(http_client: httpx.AsyncClient):
    """Wait for all services to be healthy before running tests"""
    services = [
        (AUTH_BASE_URL, "/health", 200),
        (MCP_FETCH_URL, "/mcp", 401)  # MCP endpoint returns 401 when auth is required
    ]
    
    # Use retry configuration from test_constants - already validated!
    
    for base_url, health_path, expected_status in services:
        url = f"{base_url}{health_path}"
        for attempt in range(TEST_MAX_RETRIES):
            try:
                response = await http_client.get(url)
                if response.status_code == expected_status:
                    print(f"✓ Service {base_url} is responding correctly (status: {expected_status})")
                    break
            except Exception as e:
                if attempt == TEST_MAX_RETRIES - 1:
                    pytest.fail(f"Service {base_url} failed to become healthy: {e}")
                await asyncio.sleep(TEST_RETRY_DELAY)

@pytest.fixture
async def registered_client(http_client: httpx.AsyncClient, wait_for_services) -> dict:
    """Register a test OAuth client dynamically - no hardcoded values!"""
    # MUST have OAuth access token - test FAILS if not available
    assert GATEWAY_OAUTH_ACCESS_TOKEN, "GATEWAY_OAUTH_ACCESS_TOKEN not available - run: just generate-github-token"
    
    # Use test configuration from test_constants - already validated!
    
    registration_data = {
        "redirect_uris": [TEST_CALLBACK_URL],
        "client_name": TEST_CLIENT_NAME,
        "scope": TEST_CLIENT_SCOPE
    }
    
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json=registration_data,
        headers={"Authorization": f"Bearer {GATEWAY_OAUTH_ACCESS_TOKEN}"}
    )
    
    assert response.status_code == 201, f"Client registration failed: {response.text}"
    return response.json()

@pytest.fixture
def mcp_client_token():
    """Provides MCP client access token for external client testing"""
    if not MCP_CLIENT_ACCESS_TOKEN:
        pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")
    return MCP_CLIENT_ACCESS_TOKEN

@pytest.fixture
def mcp_client_credentials():
    """Provides MCP client credentials for external client testing"""
    if not MCP_CLIENT_ID or not MCP_CLIENT_SECRET:
        pytest.fail("No MCP client credentials available - token refresh should have set these!")
    return {
        "client_id": MCP_CLIENT_ID,
        "client_secret": MCP_CLIENT_SECRET,
        "access_token": MCP_CLIENT_ACCESS_TOKEN
    }

@pytest.fixture
async def mcp_authenticated_client(http_client: httpx.AsyncClient, mcp_client_token: str) -> httpx.AsyncClient:
    """Provides an HTTP client with MCP authentication headers pre-configured"""
    # Create a new client with auth headers
    http_client.headers["Authorization"] = f"Bearer {mcp_client_token}"
    return http_client