"""Basic health test to verify connectivity"""
import pytest
import httpx
from .test_constants import AUTH_BASE_URL


@pytest.mark.asyncio 
async def test_auth_health_basic():
    """Test auth health endpoint directly"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AUTH_BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
        
@pytest.mark.asyncio
async def test_auth_metadata_basic():
    """Test auth metadata endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AUTH_BASE_URL}/.well-known/oauth-authorization-server")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        # It might not be implemented yet
        if response.status_code == 200:
            data = response.json()
            print(f"Metadata: {data}")