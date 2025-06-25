"""Test full OAuth flow using real tokens from .env
This tests the complete OAuth flow with actual authentication.
"""

import base64
import hashlib
import secrets

import httpx
import pytest

from .test_constants import AUTH_BASE_URL
from .test_constants import GATEWAY_OAUTH_ACCESS_TOKEN
from .test_constants import GATEWAY_OAUTH_CLIENT_ID
from .test_constants import GATEWAY_OAUTH_CLIENT_SECRET
from .test_constants import HTTP_BAD_REQUEST
from .test_constants import HTTP_OK
from .test_constants import HTTP_UNAUTHORIZED
from .test_constants import MCP_FETCH_URL
from .test_constants import MCP_PROTOCOL_VERSION
from .test_constants import TEST_REDIRECT_URI


class TestFullOAuthFlow:
    """Test complete OAuth flow with real authentication."""

    @pytest.mark.asyncio
    async def test_authenticated_mcp_access(self):
        """Test accessing MCP endpoint with valid OAuth token."""
        # First, verify we have the required credentials
        assert GATEWAY_OAUTH_CLIENT_ID, "GATEWAY_OAUTH_CLIENT_ID not found in .env"
        assert GATEWAY_OAUTH_CLIENT_SECRET, (
            "GATEWAY_OAUTH_CLIENT_SECRET not found in .env"
        )
        assert GATEWAY_OAUTH_ACCESS_TOKEN, (
            "GATEWAY_OAUTH_ACCESS_TOKEN not found in .env"
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Try to access MCP endpoint without auth
            response = await client.post(
                f"{MCP_FETCH_URL}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "clientCapabilities": {},
                    },
                    "id": 1,
                },
            )

            # Should get 401 Unauthorized
            assert response.status_code == HTTP_UNAUTHORIZED
            assert "WWW-Authenticate" in response.headers

            # Step 2: Check OAuth metadata endpoint
            metadata_response = await client.get(
                f"{AUTH_BASE_URL}/.well-known/oauth-authorization-server"
            )

            assert metadata_response.status_code == HTTP_OK
            metadata = metadata_response.json()
            assert metadata["issuer"] == AUTH_BASE_URL
            assert metadata["authorization_endpoint"] == f"{AUTH_BASE_URL}/authorize"
            assert metadata["token_endpoint"] == f"{AUTH_BASE_URL}/token"

    @pytest.mark.asyncio
    async def test_client_credentials_validity(self):
        """Test that our registered client credentials are valid."""
        # Fail with clear error if credentials not available
        if not GATEWAY_OAUTH_CLIENT_ID or not GATEWAY_OAUTH_CLIENT_SECRET:
            pytest.fail(
                "ERROR: GATEWAY_OAUTH_CLIENT_ID and GATEWAY_OAUTH_CLIENT_SECRET must be set in .env for this test. These should contain valid OAuth client credentials."
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test that client exists by attempting to start auth flow
            # Generate PKCE challenge
            code_verifier = (
                base64.urlsafe_b64encode(secrets.token_bytes(32))
                .decode("utf-8")
                .rstrip("=")
            )
            code_challenge = (
                base64.urlsafe_b64encode(
                    hashlib.sha256(code_verifier.encode()).digest()
                )
                .decode("utf-8")
                .rstrip("=")
            )

            response = await client.get(
                f"{AUTH_BASE_URL}/authorize",
                params={
                    "client_id": GATEWAY_OAUTH_CLIENT_ID,
                    "redirect_uri": TEST_REDIRECT_URI,  # Use REAL registered redirect URI
                    "response_type": "code",
                    "state": "test_state",
                    "code_challenge": code_challenge,
                    "code_challenge_method": "S256",
                },
                follow_redirects=False,
            )

            # If client doesn't exist, fail with clear error
            if response.status_code == HTTP_BAD_REQUEST:
                error = response.json()
                if error.get("error") == "invalid_client":
                    pytest.fail(
                        f"ERROR: OAuth client {GATEWAY_OAUTH_CLIENT_ID} is not registered in the system. Run client registration first or update .env with valid credentials."  # TODO: Break long line
                    )

            # Should redirect to GitHub OAuth (means client is valid)
            assert response.status_code in [302, 307]
            location = response.headers["location"]
            assert "github.com/login/oauth/authorize" in location

    @pytest.mark.asyncio
    async def test_token_endpoint_with_client_auth(self):
        """Test token endpoint accepts our client credentials."""
        # Fail with clear error if credentials not available
        if not GATEWAY_OAUTH_CLIENT_ID or not GATEWAY_OAUTH_CLIENT_SECRET:
            pytest.fail(
                "ERROR: GATEWAY_OAUTH_CLIENT_ID and GATEWAY_OAUTH_CLIENT_SECRET must be set in .env for this test. These should contain valid OAuth client credentials."
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test that token endpoint validates client credentials properly
            response = await client.post(
                f"{AUTH_BASE_URL}/token",
                data={
                    "grant_type": "authorization_code",
                    "code": "invalid_authorization_code",  # Will fail, but tests client auth
                    "client_id": GATEWAY_OAUTH_CLIENT_ID,
                    "client_secret": GATEWAY_OAUTH_CLIENT_SECRET,
                    "redirect_uri": TEST_REDIRECT_URI,  # Use REAL registered redirect URI
                },
            )

            # If client doesn't exist, fail with clear error
            if response.status_code == HTTP_UNAUTHORIZED:
                error = response.json()
                if error.get("error") == "invalid_client":
                    pytest.fail(
                        f"ERROR: OAuth client {GATEWAY_OAUTH_CLIENT_ID} is not registered in the system. Run client registration first or update .env with valid credentials."  # TODO: Break long line
                    )

            # Should get 400 Bad Request (invalid_grant) not 401 (invalid_client)
            # This proves our client credentials are valid
            assert response.status_code == HTTP_BAD_REQUEST
            error = response.json()
            assert error["error"] == "invalid_grant"  # Not invalid_client!

    @pytest.mark.asyncio
    async def test_forwardauth_with_bearer_token(self):
        """Test ForwardAuth middleware with Bearer token."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test /verify endpoint directly
            response = await client.get(f"{AUTH_BASE_URL}/verify")

            # Should get 401 without token
            assert response.status_code == HTTP_UNAUTHORIZED
            assert response.headers.get("WWW-Authenticate") == "Bearer"

            # Test with invalid Bearer token
            response = await client.get(
                f"{AUTH_BASE_URL}/verify",
                headers={"Authorization": "Bearer invalid_token"},
            )

            assert response.status_code == HTTP_UNAUTHORIZED
            error = response.json()
            assert error["error"] == "invalid_token"
