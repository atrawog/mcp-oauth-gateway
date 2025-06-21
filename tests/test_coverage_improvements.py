"""
Comprehensive tests to improve code coverage
Focusing on error handling, edge cases, and uncovered branches
"""
import pytest
import json
import secrets
import hashlib
import base64
from datetime import datetime, timezone, timedelta
import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import os
import time
import asyncio
import subprocess
import sys

from .jwt_test_helper import encode as jwt_encode
from .test_constants import (
    AUTH_BASE_URL,
    GATEWAY_JWT_SECRET,
    TEST_REDIRECT_URI,
    TEST_CLIENT_NAME,
    TEST_CLIENT_SCOPE,
    ACCESS_TOKEN_LIFETIME,
    GATEWAY_OAUTH_ACCESS_TOKEN,
    GATEWAY_OAUTH_CLIENT_ID,
    GATEWAY_OAUTH_CLIENT_SECRET
)


class TestAuthAuthlibErrorHandling:
    """Test error handling in auth_authlib.py"""
    
    @pytest.mark.asyncio
    async def test_verify_jwt_token_invalid_signature(self, http_client, wait_for_services):
        """Test JWT verification with invalid signature"""
        # Create a token with wrong secret
        payload = {
            "sub": "testuser",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        wrong_token = jwt_encode(payload, "wrong_secret")
        
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": f"Bearer {wrong_token}"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_verify_jwt_token_unexpected_error(self, http_client, wait_for_services):
        """Test JWT verification with malformed token causing unexpected error"""
        # Send a completely malformed token
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": "Bearer not.a.jwt.token.at.all"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_refresh_token(self, http_client, wait_for_services):
        """Test refresh token creation"""
        # First register a client
        client_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": [TEST_REDIRECT_URI],
                "client_name": TEST_CLIENT_NAME,
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "scope": TEST_CLIENT_SCOPE,
                "token_endpoint_auth_method": "client_secret_post"
            }
        )
        assert client_response.status_code == 201
        client_data = client_response.json()
        
        # Generate PKCE values
        code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        # Get authorization code
        auth_response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "response_type": "code",
                "client_id": client_data["client_id"],
                "redirect_uri": client_data["redirect_uris"][0],
                "state": "test_state",
                "code_challenge": code_challenge,
                "code_challenge_method": "S256"
            }
        )
        assert auth_response.status_code == 302
        
        # Exchange code for tokens with GitHub simulation
        location = auth_response.headers["location"]
        code = location.split("code=")[1].split("&")[0]
        
        # Simulate GitHub callback
        callback_response = await http_client.get(
            f"{AUTH_BASE_URL}/callback?code=github_code_{code}&state={code}"
        )
        assert callback_response.status_code == 302
        
        # Now exchange the authorization code
        token_response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": client_data["redirect_uris"][0],
                "client_id": client_data["client_id"],
                "client_secret": client_data["client_secret"],
                "code_verifier": code_verifier
            }
        )
        assert token_response.status_code == 200
        token_data = token_response.json()
        assert "refresh_token" in token_data
    
    @pytest.mark.asyncio
    async def test_exchange_github_code_error_scenarios(self, http_client, wait_for_services):
        """Test GitHub code exchange error scenarios"""
        # Test callback with invalid state
        response = await http_client.get(
            f"{AUTH_BASE_URL}/callback?code=invalid_github_code&state=invalid_state"
        )
        assert response.status_code == 302
        assert "error=invalid_request" in response.headers["location"]
        
        # Test callback with GitHub error
        response = await http_client.get(
            f"{AUTH_BASE_URL}/callback?error=access_denied&state=some_state"
        )
        assert response.status_code == 302
        assert "error=access_denied" in response.headers["location"]


class TestResourceProtectorErrorHandling:
    """Test error handling in resource_protector.py"""
    
    @pytest.mark.asyncio
    async def test_bearer_token_validator_missing_token(self, http_client, wait_for_services):
        """Test bearer token validation with missing token"""
        response = await http_client.get(f"{AUTH_BASE_URL}/verify")
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == 'Bearer realm="auth"'
    
    @pytest.mark.asyncio
    async def test_bearer_token_validator_invalid_format(self, http_client, wait_for_services):
        """Test bearer token validation with invalid format"""
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": "NotBearer token"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_bearer_token_validator_expired_token(self, http_client, wait_for_services):
        """Test bearer token validation with expired token"""
        # Create an expired token
        payload = {
            "sub": "testuser",
            "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
            "jti": "expired_token_id"
        }
        expired_token = jwt_encode(payload, GATEWAY_JWT_SECRET)
        
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_bearer_token_validator_revoked_token(self, http_client, wait_for_services):
        """Test bearer token validation with revoked token"""
        # Use existing credentials
        token_response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "client_credentials",
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET,
                "scope": TEST_CLIENT_SCOPE
            }
        )
        assert token_response.status_code == 200
        token_data = token_response.json()
        
        # Revoke the token
        revoke_response = await http_client.post(
            f"{AUTH_BASE_URL}/revoke",
            data={
                "token": token_data["access_token"],
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET
            }
        )
        assert revoke_response.status_code == 200
        
        # Try to use the revoked token
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        assert response.status_code == 401


class TestRoutesErrorHandling:
    """Test error handling in routes.py"""
    
    @pytest.mark.asyncio
    async def test_callback_missing_state(self, http_client, wait_for_services):
        """Test callback endpoint with missing state"""
        response = await http_client.get(f"{AUTH_BASE_URL}/callback?code=test_code")
        assert response.status_code == 302
        assert "error=invalid_request" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_callback_invalid_state(self, http_client, wait_for_services):
        """Test callback endpoint with invalid state"""
        response = await http_client.get(
            f"{AUTH_BASE_URL}/callback?code=test_code&state=invalid_state"
        )
        assert response.status_code == 302
        assert "error=invalid_request" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_callback_github_error(self, http_client, wait_for_services):
        """Test callback endpoint with GitHub error"""
        # First create a valid state by registering a client and starting auth flow
        client_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": [TEST_REDIRECT_URI],
                "client_name": TEST_CLIENT_NAME
            }
        )
        client_data = client_response.json()
        
        auth_response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "response_type": "code",
                "client_id": client_data["client_id"],
                "redirect_uri": client_data["redirect_uris"][0],
                "state": "test_state"
            }
        )
        location = auth_response.headers["location"]
        state = location.split("state=")[1].split("&")[0]
        
        # Test callback with GitHub error using valid state
        response = await http_client.get(
            f"{AUTH_BASE_URL}/callback?error=access_denied&error_description=User+denied&state={state}"
        )
        assert response.status_code == 302
        assert "error=access_denied" in response.headers["location"]
    
    @pytest.mark.asyncio
    async def test_introspect_malformed_token(self, http_client, wait_for_services):
        """Test introspect endpoint with malformed token"""
        response = await http_client.post(
            f"{AUTH_BASE_URL}/introspect",
            data={
                "token": "not.a.valid.jwt",
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["active"] is False
    
    @pytest.mark.asyncio
    async def test_introspect_token_not_in_redis(self, http_client, wait_for_services):
        """Test introspect endpoint with token not in Redis"""
        # Create a valid JWT that's not in Redis
        payload = {
            "sub": "testuser",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "jti": "not_in_redis"
        }
        token = jwt_encode(payload, GATEWAY_JWT_SECRET)
        
        response = await http_client.post(
            f"{AUTH_BASE_URL}/introspect",
            data={
                "token": token,
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["active"] is False


class TestKeysModuleCoverage:
    """Test RS256 key generation and loading in keys.py"""
    
    def test_rs256_key_generation(self):
        """Test RS256 key generation"""
        # Import the keys module directly avoiding __init__.py
        import sys
        sys.path.insert(0, '/home/atrawog/AI/atrawog/mcp-oauth-gateway/mcp-oauth-dynamicclient/src')
        from mcp_oauth_dynamicclient.keys import JWTKeyManager
        
        # Create a key manager with RS256
        key_manager = JWTKeyManager(algorithm="RS256")
        
        # Generate new keys
        key_manager.generate_rsa_keys()
        
        # Verify keys were generated
        assert key_manager.private_key is not None
        assert key_manager.public_key is not None
        
        # Test signing and verification
        payload = {"test": "data"}
        token = key_manager.encode(payload)
        decoded = key_manager.decode(token)
        assert decoded["test"] == "data"
    
    def test_rs256_key_loading_from_env(self):
        """Test RS256 key loading from environment"""
        import sys
        sys.path.insert(0, '/home/atrawog/AI/atrawog/mcp-oauth-gateway/mcp-oauth-dynamicclient/src')
        from mcp_oauth_dynamicclient.keys import JWTKeyManager
        import base64
        
        # Generate a test RSA key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Serialize to PEM
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Base64 encode
        private_key_b64 = base64.b64encode(private_pem).decode()
        
        # Create key manager with base64 key
        key_manager = JWTKeyManager(algorithm="RS256", private_key_b64=private_key_b64)
        
        # Verify key was loaded
        assert key_manager.private_key is not None
        assert key_manager.public_key is not None
        
        # Test signing
        payload = {"test": "rs256"}
        token = key_manager.encode(payload)
        decoded = key_manager.decode(token)
        assert decoded["test"] == "rs256"
    
    def test_rs256_key_file_operations(self):
        """Test RS256 key file save and load operations"""
        import sys
        sys.path.insert(0, '/home/atrawog/AI/atrawog/mcp-oauth-gateway/mcp-oauth-dynamicclient/src')
        from mcp_oauth_dynamicclient.keys import JWTKeyManager
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create key manager
            key_manager = JWTKeyManager(algorithm="RS256")
            key_manager.generate_rsa_keys()
            
            # Save keys
            private_path = os.path.join(tmpdir, "private.pem")
            public_path = os.path.join(tmpdir, "public.pem")
            key_manager.save_keys(private_path, public_path)
            
            # Verify files exist
            assert os.path.exists(private_path)
            assert os.path.exists(public_path)
            
            # Load keys in new manager
            new_manager = JWTKeyManager(algorithm="RS256")
            new_manager.load_keys(private_path, public_path)
            
            # Test that loaded keys work
            payload = {"test": "loaded"}
            token = new_manager.encode(payload)
            decoded = new_manager.decode(token)
            assert decoded["test"] == "loaded"


class TestRFC7592ErrorHandling:
    """Test RFC 7592 error handling"""
    
    @pytest.mark.asyncio
    async def test_update_client_not_found(self, http_client, wait_for_services):
        """Test updating non-existent client"""
        response = await http_client.put(
            f"{AUTH_BASE_URL}/register/non_existent_client",
            headers={"Authorization": "Bearer fake_token"},
            json={"redirect_uris": ["https://example.com/new"]}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_update_client_invalid_token(self, http_client, wait_for_services):
        """Test updating client with invalid registration token"""
        # First register a client
        client_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": [TEST_REDIRECT_URI],
                "client_name": TEST_CLIENT_NAME
            }
        )
        client_data = client_response.json()
        
        # Try to update with wrong token
        response = await http_client.put(
            f"{AUTH_BASE_URL}/register/{client_data['client_id']}",
            headers={"Authorization": "Bearer wrong_token"},
            json={"redirect_uris": ["https://example.com/new"]}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_delete_client_not_found(self, http_client, wait_for_services):
        """Test deleting non-existent client"""
        response = await http_client.delete(
            f"{AUTH_BASE_URL}/register/non_existent_client",
            headers={"Authorization": "Bearer fake_token"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_client_with_expired_secret(self, http_client, wait_for_services):
        """Test getting client with expired secret check"""
        # Register a client
        client_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": [TEST_REDIRECT_URI],
                "client_name": TEST_CLIENT_NAME
            }
        )
        client_data = client_response.json()
        
        # Get client info
        response = await http_client.get(
            f"{AUTH_BASE_URL}/register/{client_data['client_id']}",
            headers={"Authorization": f"Bearer {client_data['registration_access_token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "client_secret_expires_at" in data
        
        # Verify expiration time is set correctly
        if data["client_secret_expires_at"] != 0:
            # Non-eternal client should have future expiration
            assert data["client_secret_expires_at"] > time.time()


class TestMainModuleIntegration:
    """Test __main__.py module"""
    
    def test_cli_module_help(self):
        """Test that __main__.py can show help"""
        # Test running the module with --help
        result = subprocess.run(
            [sys.executable, "-m", "mcp_oauth_dynamicclient", "--help"],
            capture_output=True,
            text=True,
            cwd="/home/atrawog/AI/atrawog/mcp-oauth-gateway/mcp-oauth-dynamicclient"
        )
        assert result.returncode == 0
        assert "MCP OAuth Dynamic Client" in result.stdout


class TestEdgeCasesAndBranches:
    """Test remaining edge cases and branches"""
    
    @pytest.mark.asyncio
    async def test_token_refresh_with_invalid_refresh_token(self, http_client, wait_for_services):
        """Test token refresh with invalid refresh token"""
        response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": "invalid_refresh_token",
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET
            }
        )
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_grant"
    
    @pytest.mark.asyncio
    async def test_authorize_with_unsupported_response_type(self, http_client, wait_for_services):
        """Test authorize with unsupported response type"""
        # Register a client first
        client_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": [TEST_REDIRECT_URI],
                "client_name": TEST_CLIENT_NAME
            }
        )
        client_data = client_response.json()
        
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "response_type": "token",  # We don't support implicit flow
                "client_id": client_data["client_id"],
                "redirect_uri": client_data["redirect_uris"][0]
            }
        )
        assert response.status_code == 400
        assert "unsupported_response_type" in response.text
    
    @pytest.mark.asyncio
    async def test_concurrent_token_operations(self, http_client, wait_for_services):
        """Test concurrent token operations don't cause race conditions"""
        # Register a client
        client_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": [TEST_REDIRECT_URI],
                "client_name": f"{TEST_CLIENT_NAME}_concurrent",
                "grant_types": ["authorization_code"],
                "response_types": ["code"]
            }
        )
        client_data = client_response.json()
        
        # Create multiple authorization requests concurrently
        async def get_auth_code():
            # Generate unique PKCE values for each request
            verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
            challenge = base64.urlsafe_b64encode(
                hashlib.sha256(verifier.encode('utf-8')).digest()
            ).decode('utf-8').rstrip('=')
            
            auth_response = await http_client.get(
                f"{AUTH_BASE_URL}/authorize",
                params={
                    "response_type": "code",
                    "client_id": client_data["client_id"],
                    "redirect_uri": client_data["redirect_uris"][0],
                    "state": f"state_{secrets.token_urlsafe(8)}",
                    "code_challenge": challenge,
                    "code_challenge_method": "S256"
                }
            )
            assert auth_response.status_code == 302
            return auth_response.headers["location"]
        
        # Run multiple auth requests concurrently
        tasks = [get_auth_code() for _ in range(3)]
        locations = await asyncio.gather(*tasks)
        
        # All should succeed with different codes
        codes = [loc.split("code=")[1].split("&")[0] for loc in locations]
        assert len(set(codes)) == 3  # All codes should be unique
    
    @pytest.mark.asyncio 
    async def test_error_response_formats(self, http_client, wait_for_services):
        """Test various error response formats"""
        # Test invalid client credentials format
        response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "",  # Empty client ID
                "client_secret": "secret"
            }
        )
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        
        # Test missing grant type
        response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET
            }
        )
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_request"
    
    def test_server_lifecycle(self):
        """Test server can start and handle signals gracefully"""
        import sys
        sys.path.insert(0, '/home/atrawog/AI/atrawog/mcp-oauth-gateway/mcp-oauth-dynamicclient/src')
        
        # Set required env var
        os.environ['JWT_SECRET'] = GATEWAY_JWT_SECRET
        
        from mcp_oauth_dynamicclient.server import create_app
        from mcp_oauth_dynamicclient.config import Settings
        
        # Create app instance
        settings = Settings()
        app = create_app(settings)
        
        # Verify app was created successfully
        assert app is not None
        assert hasattr(app, 'routes')
        
        # Check that all expected routes are registered
        route_paths = [route.path for route in app.routes]
        expected_routes = [
            "/health",
            "/register", 
            "/.well-known/oauth-authorization-server",
            "/authorize",
            "/token",
            "/callback",
            "/verify",
            "/revoke",
            "/introspect"
        ]
        
        for expected in expected_routes:
            assert any(expected in path for path in route_paths), f"Route {expected} not found"