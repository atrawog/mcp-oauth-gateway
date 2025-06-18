"""
Sacred Test Configuration - Following the divine commandment of NO MOCKING!
All tests run against real deployed services
"""
import pytest
import httpx
import asyncio
import os
from typing import AsyncGenerator

# Load environment variables
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "atradev.org")
AUTH_BASE_URL = f"https://auth.{BASE_DOMAIN}"
MCP_FETCH_URL = f"https://mcp-fetch.{BASE_DOMAIN}"


# pytest-asyncio handles event loop automatically with asyncio_mode = auto


@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provides an async HTTP client for tests"""
    # Use proper SSL verification with real certificates
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
async def wait_for_services(http_client: httpx.AsyncClient):
    """Wait for all services to be healthy before running tests"""
    services = [
        (AUTH_BASE_URL, "/health", 200),
        (MCP_FETCH_URL, "/mcp", 401)  # MCP endpoint returns 401 when auth is required
    ]
    
    max_retries = 30
    retry_delay = 2
    
    for base_url, health_path, expected_status in services:
        url = f"{base_url}{health_path}"
        for attempt in range(max_retries):
            try:
                response = await http_client.get(url)
                if response.status_code == expected_status:
                    print(f"✓ Service {base_url} is responding correctly (status: {expected_status})")
                    break
            except Exception as e:
                if attempt == max_retries - 1:
                    pytest.fail(f"Service {base_url} failed to become healthy: {e}")
                await asyncio.sleep(retry_delay)


@pytest.fixture
async def registered_client(http_client: httpx.AsyncClient, wait_for_services) -> dict:
    """Register a test OAuth client"""
    registration_data = {
        "redirect_uris": ["http://localhost:8080/callback"],
        "client_name": "Test Client",
        "scope": "openid profile email"
    }
    
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json=registration_data
    )
    
    assert response.status_code == 201, f"Client registration failed: {response.text}"
    return response.json()