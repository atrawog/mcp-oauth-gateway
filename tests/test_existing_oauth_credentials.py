"""
Sacred OAuth Tests Using Existing Credentials - Real tokens from .env!
This test uses the GATEWAY_OAUTH_CLIENT_ID, GATEWAY_OAUTH_CLIENT_SECRET that are already registered
"""
import pytest
import httpx
import secrets
import hashlib
import base64
import json
import os

import time
from .test_constants import AUTH_BASE_URL, MCP_FETCH_URL, GATEWAY_JWT_SECRET, GITHUB_PAT, BASE_DOMAIN, TEST_REDIRECT_URI
from .jwt_test_helper import encode as jwt_encode

# Use the existing OAuth credentials from .env - these are optional
GATEWAY_OAUTH_CLIENT_ID = os.getenv("GATEWAY_OAUTH_CLIENT_ID")
GATEWAY_OAUTH_CLIENT_SECRET = os.getenv("GATEWAY_OAUTH_CLIENT_SECRET")

class TestExistingOAuthCredentials:
    """Test using the pre-registered OAuth client from .env"""
    
    @pytest.mark.asyncio
    async def test_token_endpoint_with_existing_client(self, http_client, wait_for_services):
        """Test token endpoint using existing client credentials"""
        
        # Fail with clear error if credentials not available
        if not GATEWAY_OAUTH_CLIENT_ID or not GATEWAY_OAUTH_CLIENT_SECRET:
            pytest.fail("ERROR: GATEWAY_OAUTH_CLIENT_ID and GATEWAY_OAUTH_CLIENT_SECRET must be set in .env for this test. These should contain valid OAuth client credentials from a previous registration.")
        
        # Test 1: Invalid grant with correct client credentials
        response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "invalid_code_xxx",
                "redirect_uri": "https://example.com/callback",
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET
            }
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        # If client doesn't exist, fail with clear error
        if response.status_code == 401:
            error = response.json()
            if error.get("detail", {}).get("error") == "invalid_client":
                pytest.fail(f"ERROR: OAuth client {GATEWAY_OAUTH_CLIENT_ID} is not registered in the system. Run client registration first or update .env with valid credentials.")
        
        assert response.status_code == 400  # Should be invalid_grant
        error = response.json()
        assert error.get("detail", {}).get("error") == "invalid_grant"
        
        # Test 2: Test client credentials without secret (public client)
        response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "some_code",
                "redirect_uri": "https://example.com/callback",
                "client_id": GATEWAY_OAUTH_CLIENT_ID
                # No client_secret - testing public client flow
            }
        )
        
        # Should still fail because code is invalid
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_introspect_with_existing_client(self, http_client, wait_for_services):
        """Test introspection endpoint with existing client"""
        
        # Create a test JWT token
        now = int(time.time())
        jti = secrets.token_urlsafe(16)
        
        test_claims = {
            "sub": "12345",
            "username": "testuser",
            "email": "test@example.com",
            "scope": "openid profile email",
            "client_id": GATEWAY_OAUTH_CLIENT_ID,
            "jti": jti,
            "iat": now,
            "exp": now + 3600,
            "iss": AUTH_BASE_URL
        }
        
        test_token = jwt_encode(test_claims, GATEWAY_JWT_SECRET, algorithm="HS256")
        
        # Introspect the token (it won't be active because it's not in Redis)
        response = await http_client.post(
            f"{AUTH_BASE_URL}/introspect",
            data={
                "token": test_token,
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["active"] is False  # Not in Redis
    
    @pytest.mark.asyncio
    async def test_revoke_with_existing_client(self, http_client, wait_for_services):
        """Test revocation with existing client credentials"""
        
        # Create a test token
        test_token = jwt_encode(
            {
                "sub": "12345",
                "jti": secrets.token_urlsafe(16),
                "exp": int(time.time()) + 3600
            },
            GATEWAY_JWT_SECRET,
            algorithm="HS256"
        )
        
        # Revoke it
        response = await http_client.post(
            f"{AUTH_BASE_URL}/revoke",
            data={
                "token": test_token,
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET
            }
        )
        
        # Always returns 200 per RFC
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_github_pat_usage(self, http_client, wait_for_services):
        """Test using GitHub PAT to verify user info"""
        
        if not GITHUB_PAT:
            pytest.fail("GITHUB_PAT not set - TESTS MUST NOT BE SKIPPED! GitHub PAT is REQUIRED!")
        
        # We can use the GitHub PAT to get user info directly
        async with httpx.AsyncClient() as github_client:
            user_response = await github_client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {GITHUB_PAT}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if user_response.status_code == 200:
                user_info = user_response.json()
                print(f"GitHub user: {user_info.get('login')}")
                
                # This verifies our PAT is valid and we could use it
                # to simulate GitHub OAuth responses if needed
                assert "login" in user_info
            else:
                # PAT might be expired or invalid
                pytest.fail(f"GitHub PAT is not valid (status: {user_response.status_code}). Token refresh should have handled this.")

class TestCompleteFlowWithExistingClient:
    """Test a more complete flow using existing credentials"""
    
    @pytest.mark.asyncio
    async def test_authorization_to_token_flow(self, http_client, wait_for_services):
        """Test the authorization flow with existing client"""
        
        # Fail with clear error if credentials not available
        if not GATEWAY_OAUTH_CLIENT_ID or not GATEWAY_OAUTH_CLIENT_SECRET:
            pytest.fail("ERROR: GATEWAY_OAUTH_CLIENT_ID and GATEWAY_OAUTH_CLIENT_SECRET must be set in .env for this test.")
        
        # Start authorization with existing client
        auth_params = {
            "client_id": GATEWAY_OAUTH_CLIENT_ID,
            "redirect_uri": TEST_REDIRECT_URI,  # Use TEST_REDIRECT_URI from constants
            "response_type": "code",
            "scope": "openid profile email",
            "state": secrets.token_urlsafe(16),
            "code_challenge": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("="),
            "code_challenge_method": "S256"
        }
        
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params=auth_params,
            follow_redirects=False
        )
        
        # If client doesn't exist, fail with clear error
        if response.status_code == 400:
            error = response.json()
            if error.get("detail", {}).get("error") == "invalid_client":
                pytest.fail(f"ERROR: OAuth client {GATEWAY_OAUTH_CLIENT_ID} is not registered in the system. Run client registration first.")
        
        # Should redirect to GitHub
        assert response.status_code == 307
        location = response.headers["location"]
        assert "github.com/login/oauth/authorize" in location
        
        # Extract the state that was stored in Redis
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(location)
        query_params = parse_qs(parsed.query)
        github_state = query_params["state"][0]
        
        # We can't complete the GitHub flow automatically,
        # but we've exercised the authorization setup code
        
        # Test what happens with an invalid callback
        callback_response = await http_client.get(
            f"{AUTH_BASE_URL}/callback",
            params={
                "code": "fake_github_code",
                "state": github_state
            },
            follow_redirects=False
        )
        
        # Will fail at GitHub token exchange
        assert callback_response.status_code in [307, 500]

class TestJWTOperations:
    """Test JWT-specific operations to increase coverage"""
    
    @pytest.mark.asyncio
    async def test_verify_various_jwt_errors(self, http_client, wait_for_services):
        """Test different JWT error conditions"""
        
        # Test 1: Malformed JWT
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": "Bearer not.a.valid.jwt"}
        )
        
        assert response.status_code == 401
        
        # Test 2: JWT with wrong signature
        wrong_secret_token = jwt_encode(
            {"sub": "12345", "exp": int(time.time()) + 3600},
            "wrong_secret",
            algorithm="HS256"
        )
        
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": f"Bearer {wrong_secret_token}"}
        )
        
        assert response.status_code == 401
        
        # Test 3: Valid JWT but missing jti (will pass decode but fail Redis check)
        no_jti_token = jwt_encode(
            {
                "sub": "12345",
                "username": "testuser",
                "exp": int(time.time()) + 3600
            },
            GATEWAY_JWT_SECRET,
            algorithm="HS256"
        )
        
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": f"Bearer {no_jti_token}"}
        )
        
        # Should fail without jti (jti is marked as essential in auth service)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_introspect_expired_token(self, http_client, wait_for_services):
        """Test introspecting an expired token"""
        
        # Create an expired token
        expired_token = jwt_encode(
            {
                "sub": "12345",
                "jti": "expired_jti",
                "iat": int(time.time()) - 7200,
                "exp": int(time.time()) - 3600  # Expired 1 hour ago
            },
            GATEWAY_JWT_SECRET,
            algorithm="HS256"
        )
        
        response = await http_client.post(
            f"{AUTH_BASE_URL}/introspect",
            data={
                "token": expired_token,
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["active"] is False  # Expired tokens are inactive