"""
Additional coverage tests for edge cases and error conditions
Following CLAUDE.md - NO MOCKING, real services only!
"""
import pytest
import httpx
import json
import secrets
import hashlib
import base64

import time
from .jwt_test_helper import encode as jwt_encode
from .test_constants import (
    AUTH_BASE_URL,
    JWT_SECRET,
    TEST_REDIRECT_URI,
    TEST_CLIENT_NAME,
    TEST_CLIENT_SCOPE,
    ACCESS_TOKEN_LIFETIME
)

class TestAdditionalCoverage:
    """Test additional edge cases to improve coverage"""
    
    @pytest.mark.asyncio
    async def test_missing_authorization_header_formats(self, http_client, wait_for_services):
        """Test various missing/malformed authorization headers"""
        
        # Test with no Authorization header at all (already covered)
        response = await http_client.get(f"{AUTH_BASE_URL}/verify")
        assert response.status_code == 401
        
        # Test with empty Authorization header
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": ""}
        )
        assert response.status_code == 401
        
        # Test with Authorization but no Bearer
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": "InvalidScheme token123"}
        )
        assert response.status_code == 401
        
        # Test with Bearer but no token
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": "Bearer"}
        )
        assert response.status_code == 401
        
        # Test with Bearer and space but no token - Skip this as httpx doesn't allow it
        # httpx validates headers and won't send "Bearer " with trailing space
    
    @pytest.mark.asyncio
    async def test_token_endpoint_missing_client_credentials(self, http_client, wait_for_services):
        """Test token endpoint with missing client credentials"""
        
        # First register a client
        registration_data = {
            "redirect_uris": [TEST_REDIRECT_URI],
            "client_name": TEST_CLIENT_NAME,
            "scope": TEST_CLIENT_SCOPE
        }
        
        reg_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data
        )
        
        assert reg_response.status_code == 201
        client = reg_response.json()
        
        # Test with missing client_id
        token_response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "some_code",
                "client_secret": client["client_secret"]
            }
        )
        
        # FastAPI returns 422 for missing required fields
        assert token_response.status_code == 422
        
        # Test with missing client_secret for confidential client
        token_response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "some_code",
                "client_id": client["client_id"]
            }
        )
        
        # Returns 400 for missing client_secret
        assert token_response.status_code == 400
        # FastAPI may return different error format
        error_data = token_response.json()
        # Check for error in either format
        assert "error" in error_data or "detail" in error_data
    
    @pytest.mark.asyncio
    async def test_introspect_with_malformed_token(self, http_client, wait_for_services, registered_client):
        """Test introspect endpoint with various malformed tokens"""
        
        # Test with non-JWT token
        response = await http_client.post(
            f"{AUTH_BASE_URL}/introspect",
            data={
                "token": "not_a_jwt_token",
                "client_id": registered_client["client_id"],
                "client_secret": registered_client["client_secret"]
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["active"] is False
        
        # Test with malformed JWT (invalid format)
        response = await http_client.post(
            f"{AUTH_BASE_URL}/introspect",
            data={
                "token": "eyJ.invalid.jwt",
                "client_id": registered_client["client_id"],
                "client_secret": registered_client["client_secret"]
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["active"] is False
    
    @pytest.mark.asyncio
    async def test_registration_with_minimal_data(self, http_client, wait_for_services):
        """Test client registration with only required fields"""
        
        # Register with absolute minimum data
        registration_data = {
            "redirect_uris": [TEST_REDIRECT_URI]
        }
        
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data
        )
        
        assert response.status_code == 201
        client = response.json()
        
        # Should have generated defaults
        assert "client_id" in client
        assert "client_secret" in client
        assert client["client_secret_expires_at"] == 0  # Never expires
        
    @pytest.mark.asyncio
    async def test_jwt_with_invalid_signature(self, http_client, wait_for_services, registered_client):
        """Test JWT verification with invalid signature"""
        
        # Create a JWT with wrong secret
        wrong_secret = "wrong_secret_key_that_is_not_correct"
        
        token_data = {
            "sub": "testuser",
            "jti": secrets.token_urlsafe(16),
            "iat": int(time.time()),
            "exp": int(time.time()) + ACCESS_TOKEN_LIFETIME,
            "scope": "openid profile email",
            "client_id": registered_client["client_id"]
        }
        
        # Sign with wrong secret
        invalid_token = jwt_encode(token_data, wrong_secret, algorithm="HS256")
        
        # Try to verify
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        assert response.status_code == 401
        error = response.json()
        assert "Signature verification failed" in error["detail"]["error_description"]
    
    @pytest.mark.asyncio 
    async def test_authorize_endpoint_missing_parameters(self, http_client, wait_for_services, registered_client):
        """Test authorize endpoint with missing required parameters"""
        
        # Missing response_type
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "client_id": registered_client["client_id"],
                "redirect_uri": registered_client["redirect_uris"][0]
            }
        )
        
        # FastAPI returns 422 for missing required query parameters
        assert response.status_code == 422
        
        # Missing client_id
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "response_type": "code",
                "redirect_uri": TEST_REDIRECT_URI
            }
        )
        
        # FastAPI returns 422 for missing required query parameters
        assert response.status_code == 422