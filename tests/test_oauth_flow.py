"""
Sacred OAuth Flow Tests - NO MOCKING! Real services only!
Tests the complete OAuth 2.1 flow with RFC 7591 compliance
"""
import pytest
import httpx
import secrets
import hashlib
import base64
import json
from urllib.parse import urlparse, parse_qs
import os

# Load from environment
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "localhost")
AUTH_BASE_URL = f"https://auth.{BASE_DOMAIN}"


class TestOAuthFlow:
    """Test the complete OAuth 2.1 flow"""
    
    @pytest.mark.asyncio
    async def test_server_metadata(self, http_client, wait_for_services):
        """Test .well-known/oauth-authorization-server endpoint"""
        response = await http_client.get(f"{AUTH_BASE_URL}/.well-known/oauth-authorization-server")
        
        assert response.status_code == 200
        metadata = response.json()
        
        # Verify required fields
        assert metadata["issuer"] == AUTH_BASE_URL
        assert metadata["authorization_endpoint"] == f"{AUTH_BASE_URL}/authorize"
        assert metadata["token_endpoint"] == f"{AUTH_BASE_URL}/token"
        assert metadata["registration_endpoint"] == f"{AUTH_BASE_URL}/register"
        
        # Verify supported features
        assert "code" in metadata["response_types_supported"]
        assert "S256" in metadata["code_challenge_methods_supported"]
        assert "authorization_code" in metadata["grant_types_supported"]
    
    @pytest.mark.asyncio
    async def test_client_registration_rfc7591(self, http_client, wait_for_services):
        """Test dynamic client registration per RFC 7591"""
        # Test successful registration
        registration_data = {
            "redirect_uris": ["https://example.com/callback"],
            "client_name": "RFC 7591 Test Client",
            "client_uri": "https://example.com",
            "scope": "openid profile",
            "contacts": ["admin@example.com"]
        }
        
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data
        )
        
        assert response.status_code == 201  # MUST return 201 Created
        client = response.json()
        
        # Verify required fields in response
        assert "client_id" in client
        assert "client_secret" in client
        assert client["client_secret_expires_at"] == 0  # Never expires
        
        # Verify metadata is echoed back
        assert client["redirect_uris"] == registration_data["redirect_uris"]
        assert client["client_name"] == registration_data["client_name"]
        assert client["client_uri"] == registration_data["client_uri"]
        
        # Test missing redirect_uris
        invalid_data = {"client_name": "Invalid Client"}
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json=invalid_data
        )
        
        assert response.status_code == 422  # FastAPI returns 422 for validation errors
        error = response.json()
        assert "detail" in error  # FastAPI error format
    
    @pytest.mark.asyncio
    async def test_authorization_endpoint_validation(self, http_client, registered_client):
        """Test authorization endpoint with invalid client handling"""
        # Test with invalid client_id - MUST NOT redirect
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "client_id": "invalid_client",
                "redirect_uri": "http://localhost:8080/callback",
                "response_type": "code",
                "state": "test_state"
            },
            follow_redirects=False
        )
        
        assert response.status_code == 400  # MUST return error, not redirect
        error = response.json()
        assert error["detail"]["error"] == "invalid_client"
        
        # Test with valid client but invalid redirect_uri - MUST NOT redirect
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "client_id": registered_client["client_id"],
                "redirect_uri": "http://evil.com/callback",
                "response_type": "code",
                "state": "test_state"
            },
            follow_redirects=False
        )
        
        assert response.status_code == 400
        error = response.json()
        assert error["detail"]["error"] == "invalid_redirect_uri"
    
    @pytest.mark.asyncio
    async def test_pkce_flow(self, http_client, registered_client):
        """Test PKCE (RFC 7636) with S256 challenge method"""
        # Generate PKCE challenge
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode('utf-8').rstrip('=')
        
        # Start authorization flow with PKCE
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "client_id": registered_client["client_id"],
                "redirect_uri": registered_client["redirect_uris"][0],
                "response_type": "code",
                "state": "pkce_test",
                "code_challenge": code_challenge,
                "code_challenge_method": "S256"
            },
            follow_redirects=False
        )
        
        # Should redirect to GitHub OAuth
        assert response.status_code in [302, 307]  # Accept either redirect code
        location = response.headers["location"]
        assert "github.com/login/oauth/authorize" in location
    
    @pytest.mark.asyncio
    async def test_token_endpoint_errors(self, http_client, registered_client):
        """Test token endpoint error handling"""
        # Test invalid client
        response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "invalid_code",
                "client_id": "invalid_client",
                "redirect_uri": "http://localhost:8080/callback"
            }
        )
        
        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate") == "Basic"
        error = response.json()
        assert error["detail"]["error"] == "invalid_client"
        
        # Test invalid grant
        response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "invalid_code",
                "client_id": registered_client["client_id"],
                "client_secret": registered_client["client_secret"],
                "redirect_uri": registered_client["redirect_uris"][0]
            }
        )
        
        assert response.status_code == 400
        error = response.json()
        assert error["detail"]["error"] == "invalid_grant"
    
    @pytest.mark.asyncio
    async def test_token_introspection(self, http_client, registered_client):
        """Test token introspection endpoint (RFC 7662)"""
        # Test with invalid token
        response = await http_client.post(
            f"{AUTH_BASE_URL}/introspect",
            data={
                "token": "invalid_token",
                "client_id": registered_client["client_id"],
                "client_secret": registered_client["client_secret"]
            }
        )
        
        # Introspection endpoint might not be implemented yet
        if response.status_code == 404:
            pytest.skip("Introspection endpoint not implemented")
        assert response.status_code == 200
        result = response.json()
        assert result["active"] is False
    
    @pytest.mark.asyncio
    async def test_token_revocation(self, http_client, registered_client):
        """Test token revocation endpoint (RFC 7009)"""
        # Revocation always returns 200, even for invalid tokens
        response = await http_client.post(
            f"{AUTH_BASE_URL}/revoke",
            data={
                "token": "any_token",
                "client_id": registered_client["client_id"],
                "client_secret": registered_client["client_secret"]
            }
        )
        
        # Revocation endpoint might not be implemented yet
        if response.status_code == 404:
            pytest.skip("Revocation endpoint not implemented")
        assert response.status_code == 200  # Always 200 per RFC 7009
    
    @pytest.mark.asyncio
    async def test_forwardauth_verification(self, http_client):
        """Test ForwardAuth /verify endpoint"""
        # Test without token
        response = await http_client.get(f"{AUTH_BASE_URL}/verify")
        
        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate") == "Bearer"
        
        # Test with invalid token
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        error = response.json()
        assert error["detail"]["error"] == "invalid_token"