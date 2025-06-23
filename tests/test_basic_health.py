"""Basic health test to verify connectivity using OAuth discovery endpoint"""
import pytest
import httpx
from .test_constants import AUTH_BASE_URL

@pytest.mark.asyncio 
async def test_auth_oauth_discovery_health():
    """Test auth service health via OAuth discovery endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AUTH_BASE_URL}/.well-known/oauth-authorization-server")
        assert response.status_code == 200
        data = response.json()
        # Verify required OAuth metadata fields are present
        assert "issuer" in data
        assert "authorization_endpoint" in data
        assert "token_endpoint" in data
        assert "registration_endpoint" in data
        
        
@pytest.mark.asyncio
async def test_auth_metadata_basic():
    """Test auth metadata endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AUTH_BASE_URL}/.well-known/oauth-authorization-server")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        assert response.status_code == 200
        data = response.json()
        print(f"Metadata: {data}")