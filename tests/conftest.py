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
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "localhost")
AUTH_BASE_URL = f"http://auth.{BASE_DOMAIN}:8000"
MCP_FETCH_URL = f"http://mcp-fetch.{BASE_DOMAIN}:3000"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provides an async HTTP client for tests"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
async def wait_for_services(http_client: httpx.AsyncClient):
    """Wait for all services to be healthy before running tests"""
    services = [
        (AUTH_BASE_URL, "/health"),
        (MCP_FETCH_URL, "/health")
    ]
    
    max_retries = 30
    retry_delay = 2
    
    for base_url, health_path in services:
        url = f"{base_url}{health_path}"
        for attempt in range(max_retries):
            try:
                response = await http_client.get(url)
                if response.status_code == 200:
                    print(f"✓ Service {base_url} is healthy")
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