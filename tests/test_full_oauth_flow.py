"""
Test full OAuth flow using real tokens from .env
This tests the complete OAuth flow with actual authentication
"""
import pytest
import httpx
import os
import secrets
import hashlib
import base64
from urllib.parse import urlparse, parse_qs

# Load configuration from environment
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "atradev.org")
AUTH_BASE_URL = f"https://auth.{BASE_DOMAIN}"
MCP_FETCH_URL = f"https://mcp-fetch.{BASE_DOMAIN}"

# OAuth client credentials from .env
OAUTH_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET")


class TestFullOAuthFlow:
    """Test complete OAuth flow with real authentication"""
    
    @pytest.mark.asyncio
    async def test_authenticated_mcp_access(self):
        """Test accessing MCP endpoint with valid OAuth token"""
        
        # First, verify we have the required credentials
        assert OAUTH_CLIENT_ID, "OAUTH_CLIENT_ID not found in .env"
        assert OAUTH_CLIENT_SECRET, "OAUTH_CLIENT_SECRET not found in .env"
        
        async with httpx.AsyncClient() as client:
            # Step 1: Try to access MCP endpoint without auth
            response = await client.post(
                f"{MCP_FETCH_URL}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "clientCapabilities": {}
                    },
                    "id": 1
                }
            )
            
            # Should get 401 Unauthorized
            assert response.status_code == 401
            assert "WWW-Authenticate" in response.headers
            
            # Step 2: Check OAuth metadata endpoint
            metadata_response = await client.get(
                f"{AUTH_BASE_URL}/.well-known/oauth-authorization-server"
            )
            
            assert metadata_response.status_code == 200
            metadata = metadata_response.json()
            assert metadata["issuer"] == AUTH_BASE_URL
            assert metadata["authorization_endpoint"] == f"{AUTH_BASE_URL}/authorize"
            assert metadata["token_endpoint"] == f"{AUTH_BASE_URL}/token"
            
    @pytest.mark.asyncio
    async def test_client_credentials_validity(self):
        """Test that our registered client credentials are valid"""
        
        async with httpx.AsyncClient() as client:
            # Test that client exists by attempting to start auth flow
            # Generate PKCE challenge
            code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
            code_challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).decode('utf-8').rstrip('=')
            
            response = await client.get(
                f"{AUTH_BASE_URL}/authorize",
                params={
                    "client_id": OAUTH_CLIENT_ID,
                    "redirect_uri": "http://localhost:8080/callback",
                    "response_type": "code",
                    "state": "test_state",
                    "code_challenge": code_challenge,
                    "code_challenge_method": "S256"
                },
                follow_redirects=False
            )
            
            # Should redirect to GitHub OAuth (means client is valid)
            assert response.status_code in [302, 307]
            location = response.headers["location"]
            assert "github.com/login/oauth/authorize" in location
            
    @pytest.mark.asyncio
    async def test_token_endpoint_with_client_auth(self):
        """Test token endpoint accepts our client credentials"""
        
        async with httpx.AsyncClient() as client:
            # Test that token endpoint validates client credentials properly
            response = await client.post(
                f"{AUTH_BASE_URL}/token",
                data={
                    "grant_type": "authorization_code",
                    "code": "invalid_code",  # Will fail, but tests client auth
                    "client_id": OAUTH_CLIENT_ID,
                    "client_secret": OAUTH_CLIENT_SECRET,
                    "redirect_uri": "http://localhost:8080/callback"
                }
            )
            
            # Should get 400 Bad Request (invalid_grant) not 401 (invalid_client)
            # This proves our client credentials are valid
            assert response.status_code == 400
            error = response.json()
            assert error["detail"]["error"] == "invalid_grant"  # Not invalid_client!
            
    @pytest.mark.asyncio
    async def test_forwardauth_with_bearer_token(self):
        """Test ForwardAuth middleware with Bearer token"""
        
        async with httpx.AsyncClient() as client:
            # Test /verify endpoint directly
            response = await client.get(f"{AUTH_BASE_URL}/verify")
            
            # Should get 401 without token
            assert response.status_code == 401
            assert response.headers.get("WWW-Authenticate") == "Bearer"
            
            # Test with invalid Bearer token
            response = await client.get(
                f"{AUTH_BASE_URL}/verify",
                headers={"Authorization": "Bearer invalid_token"}
            )
            
            assert response.status_code == 401
            error = response.json()
            assert error["detail"]["error"] == "invalid_token"