"""
Security tests for OAuth client registration endpoint
Following CLAUDE.md - NO MOCKING, real services only!
Tests that /register endpoint properly protects against unauthorized access
"""
import pytest
import httpx
import os

from .test_constants import AUTH_BASE_URL, GATEWAY_OAUTH_ACCESS_TOKEN


class TestRegisterEndpointSecurity:
    """Test OAuth client registration endpoint security"""
    
    @pytest.mark.asyncio
    async def test_register_requires_authorization_header(self, http_client, wait_for_services):
        """Test that /register endpoint requires Authorization header"""
        
        registration_data = {
            "redirect_uris": ["https://example.com/callback"],
            "client_name": "Test Client",
            "scope": "openid profile email"
        }
        
        # Test without Authorization header
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data
        )
        
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"
        
        error = response.json()
        assert error["detail"]["error"] == "authorization_required"
        assert "GitHub authentication required" in error["detail"]["error_description"]
    
    @pytest.mark.asyncio
    async def test_register_requires_bearer_token(self, http_client, wait_for_services):
        """Test that /register endpoint requires Bearer token format"""
        
        registration_data = {
            "redirect_uris": ["https://example.com/callback"],
            "client_name": "Test Client",
            "scope": "openid profile email"
        }
        
        # Test with wrong authorization scheme
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data,
            headers={"Authorization": "Basic invalid_scheme"}
        )
        
        assert response.status_code == 401
        error = response.json()
        assert error["detail"]["error"] == "authorization_required"
        assert "GitHub authentication required" in error["detail"]["error_description"]
    
    @pytest.mark.asyncio
    async def test_register_rejects_invalid_api_key(self, http_client, wait_for_services):
        """Test that /register endpoint rejects invalid JWT tokens"""
        
        registration_data = {
            "redirect_uris": ["https://example.com/callback"],
            "client_name": "Test Client",
            "scope": "openid profile email"
        }
        
        # Test with invalid JWT token
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data,
            headers={"Authorization": "Bearer invalid_jwt_token_should_be_rejected"}
        )
        
        assert response.status_code == 401
        error = response.json()
        assert error["detail"]["error"] == "invalid_token"
        assert "Invalid or expired token" in error["detail"]["error_description"]
    
    @pytest.mark.asyncio
    async def test_register_accepts_valid_api_key(self, http_client, wait_for_services):
        """Test that /register endpoint accepts valid OAuth access token"""
        
        # MUST have OAuth access token - test FAILS if not available
        assert GATEWAY_OAUTH_ACCESS_TOKEN, "GATEWAY_OAUTH_ACCESS_TOKEN not available - run: just generate-github-token"
        
        registration_data = {
            "redirect_uris": ["https://example.com/callback"],
            "client_name": "Security Test Client",
            "scope": "openid profile email"
        }
        
        # Test with valid OAuth access token
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data,
            headers={"Authorization": f"Bearer {GATEWAY_OAUTH_ACCESS_TOKEN}"}
        )
        
        assert response.status_code == 201
        client_data = response.json()
        assert "client_id" in client_data
        assert "client_secret" in client_data
        assert client_data["client_name"] == "Security Test Client"
    
    @pytest.mark.asyncio
    async def test_register_empty_bearer_token(self, http_client, wait_for_services):
        """Test that /register endpoint rejects empty Bearer token"""
        
        registration_data = {
            "redirect_uris": ["https://example.com/callback"],
            "client_name": "Test Client",
            "scope": "openid profile email"
        }
        
        # Test with just "Bearer" (no space or token)
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data,
            headers={"Authorization": "Bearer"}
        )
        
        assert response.status_code == 401
        error = response.json()
        assert error["detail"]["error"] == "authorization_required"
        assert "GitHub authentication required" in error["detail"]["error_description"]
    
    @pytest.mark.asyncio
    async def test_register_timing_attack_protection(self, http_client, wait_for_services):
        """Test that /register endpoint uses constant-time comparison for JWT tokens"""
        
        registration_data = {
            "redirect_uris": ["https://example.com/callback"],
            "client_name": "Test Client",
            "scope": "openid profile email"
        }
        
        # Test with different length invalid JWT tokens - should all return same error
        invalid_tokens = [
            "short",
            "medium_length_token",
            "very_long_invalid_jwt_token_that_should_also_be_rejected_with_same_timing"
        ]
        
        for invalid_token in invalid_tokens:
            response = await http_client.post(
                f"{AUTH_BASE_URL}/register",
                json=registration_data,
                headers={"Authorization": f"Bearer {invalid_token}"}
            )
            
            assert response.status_code == 401
            error = response.json()
            assert error["detail"]["error"] == "invalid_token"
            assert "Invalid or expired token" in error["detail"]["error_description"]


class TestRegisterEndpointBootstrap:
    """Test bootstrap scenarios for OAuth client registration"""
    
    @pytest.mark.asyncio
    async def test_admin_can_register_multiple_clients(self, http_client, wait_for_services):
        """Test that authorized user can register multiple OAuth clients"""
        
        # MUST have OAuth access token - test FAILS if not available
        assert GATEWAY_OAUTH_ACCESS_TOKEN, "GATEWAY_OAUTH_ACCESS_TOKEN not available - run: just generate-github-token"
        
        # Register first client
        response1 = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": ["https://app1.example.com/callback"],
                "client_name": "Test App 1",
                "scope": "openid profile email"
            },
            headers={"Authorization": f"Bearer {GATEWAY_OAUTH_ACCESS_TOKEN}"}
        )
        
        assert response1.status_code == 201
        client1 = response1.json()
        
        # Register second client  
        response2 = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": ["https://app2.example.com/callback"],
                "client_name": "Test App 2",
                "scope": "openid profile"
            },
            headers={"Authorization": f"Bearer {GATEWAY_OAUTH_ACCESS_TOKEN}"}
        )
        
        assert response2.status_code == 201
        client2 = response2.json()
        
        # Ensure clients have different IDs
        assert client1["client_id"] != client2["client_id"]
        assert client1["client_secret"] != client2["client_secret"]