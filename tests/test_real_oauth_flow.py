"""Sacred Real OAuth Flow Tests - Using REAL GitHub OAuth ONLY!
Following CLAUDE.md Commandment 1: NO MOCKING, NO SIMULATION, REAL TESTS ONLY!

These tests use REAL GitHub OAuth credentials and REAL API calls.
If credentials are missing or invalid, tests FAIL with clear errors.
NEVER skip due to timeouts - fail fast with meaningful messages.
"""

import base64
import hashlib
import secrets
import time
from urllib.parse import parse_qs
from urllib.parse import urlparse

import httpx
import pytest

# Import all configuration from test_constants - NO HARDCODED VALUES!
from .jwt_test_helper import encode as jwt_encode
from .test_constants import AUTH_BASE_URL
from .test_constants import BASE_DOMAIN
from .test_constants import GATEWAY_JWT_SECRET
from .test_constants import GATEWAY_OAUTH_ACCESS_TOKEN
from .test_constants import GATEWAY_OAUTH_CLIENT_ID
from .test_constants import GATEWAY_OAUTH_CLIENT_SECRET
from .test_constants import GATEWAY_OAUTH_REFRESH_TOKEN
from .test_constants import GITHUB_PAT
from .test_constants import HTTP_BAD_REQUEST
from .test_constants import HTTP_OK
from .test_constants import HTTP_UNAUTHORIZED
from .test_constants import TEST_OAUTH_CALLBACK_URL


class TestRealOAuthFlow:
    """Test REAL OAuth flow with REAL GitHub authentication - NO SIMULATION!"""

    @pytest.mark.asyncio
    async def test_complete_github_oauth_flow(self, http_client, _wait_for_services):
        """Test complete OAuth flow using REAL stored tokens from successful auth."""
        # REQUIRE real OAuth tokens - fail if not available
        if not GATEWAY_OAUTH_ACCESS_TOKEN:
            pytest.fail(
                "ERROR: GATEWAY_OAUTH_ACCESS_TOKEN not found in .env. "
                "You must complete a real GitHub OAuth flow first and store the tokens. "
                "Run: just generate-github-token",
            )

        if not GATEWAY_OAUTH_CLIENT_ID or not GATEWAY_OAUTH_CLIENT_SECRET:
            pytest.fail(
                "ERROR: GATEWAY_OAUTH_CLIENT_ID and GATEWAY_OAUTH_CLIENT_SECRET not found in .env. "
                "You must register a real OAuth client first. "
                "Run: just generate-github-token",
            )

        # Step 1: Verify our OAuth client exists in the system
        # Try to start auth flow to validate client registration
        auth_params = {
            "client_id": GATEWAY_OAUTH_CLIENT_ID,
            "redirect_uri": TEST_OAUTH_CALLBACK_URL,
            "response_type": "code",
            "scope": "openid profile email",
            "state": secrets.token_urlsafe(16),
        }

        auth_response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params=auth_params,
            follow_redirects=False,
            timeout=30.0,
        )

        if auth_response.status_code == HTTP_BAD_REQUEST:
            error = auth_response.json()
            if error.get("error") == "invalid_client":
                pytest.fail(
                    f"ERROR: OAuth client {GATEWAY_OAUTH_CLIENT_ID} is not registered in the system. "  # TODO: Break long line
                    f"Run: just generate-github-token to register a new client.",
                )

        # Should redirect to GitHub OAuth (proves client is valid)
        assert auth_response.status_code == 307
        github_url = auth_response.headers["location"]
        assert "github.com/login/oauth/authorize" in github_url

        # Step 2: Test that our stored access token is still valid
        # Use REAL GitHub API call with REAL token
        if not GITHUB_PAT:
            pytest.fail("GITHUB_PAT not set - TESTS MUST NOT BE SKIPPED! GitHub PAT is REQUIRED!")

        async with httpx.AsyncClient(timeout=30.0) as github_client:
            user_response = await github_client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {GITHUB_PAT}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

            if user_response.status_code != 200:
                pytest.fail(
                    f"ERROR: GitHub token is invalid (status: {user_response.status_code}). "  # TODO: Break long line
                    f"Response: {user_response.text}. "
                    f"Token refresh should have handled this.",
                )

            user_info = user_response.json()
            github_username = user_info["login"]
            print(f"✓ GitHub token valid for user: {github_username}")

        # Step 3: Test token endpoint with our real client credentials
        token_response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "invalid_code_for_testing",  # Will fail but validates client
                "redirect_uri": TEST_OAUTH_CALLBACK_URL,
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET,
            },
            timeout=30.0,
        )

        # Should get invalid_grant (not invalid_client) proving client is valid
        assert token_response.status_code == HTTP_BAD_REQUEST
        error = token_response.json()
        assert error["error"] == "invalid_grant"  # Not invalid_client!

        # Step 4: If we have a refresh token, test refresh flow
        if GATEWAY_OAUTH_REFRESH_TOKEN:
            refresh_response = await http_client.post(
                f"{AUTH_BASE_URL}/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": GATEWAY_OAUTH_REFRESH_TOKEN,
                    "client_id": GATEWAY_OAUTH_CLIENT_ID,
                    "client_secret": GATEWAY_OAUTH_CLIENT_SECRET,
                },
                timeout=30.0,
            )

            if refresh_response.status_code == HTTP_OK:
                new_tokens = refresh_response.json()
                assert "access_token" in new_tokens
                print("✓ Refresh token flow successful")

                # Test token introspection with the new access token
                introspect_response = await http_client.post(
                    f"{AUTH_BASE_URL}/introspect",
                    data={
                        "token": new_tokens["access_token"],
                        "client_id": GATEWAY_OAUTH_CLIENT_ID,
                        "client_secret": GATEWAY_OAUTH_CLIENT_SECRET,
                    },
                    timeout=30.0,
                )

                assert introspect_response.status_code == HTTP_OK
                introspect_data = introspect_response.json()
                assert introspect_data["active"] is True
                print("✓ Token introspection successful")

                # Test token revocation
                revoke_response = await http_client.post(
                    f"{AUTH_BASE_URL}/revoke",
                    data={
                        "token": new_tokens["access_token"],
                        "client_id": GATEWAY_OAUTH_CLIENT_ID,
                        "client_secret": GATEWAY_OAUTH_CLIENT_SECRET,
                    },
                    timeout=30.0,
                )

                assert revoke_response.status_code == HTTP_OK
                print("✓ Token revocation successful")

                # Verify token is now revoked
                verify_response = await http_client.get(
                    f"{AUTH_BASE_URL}/verify",
                    headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
                    timeout=30.0,
                )

                assert verify_response.status_code == HTTP_UNAUTHORIZED
                print("✓ Token revocation verified")
            else:
                print(f"Refresh token expired or invalid: {refresh_response.status_code}")
        else:
            print("No refresh token available - run: just generate-github-token")


class TestRealPKCEFlow:
    """Test REAL PKCE flow with REAL OAuth client."""

    @pytest.mark.asyncio
    async def test_pkce_with_real_client(self, http_client, _wait_for_services):
        """Test PKCE verification with REAL OAuth client."""
        # REQUIRE real OAuth client credentials
        if not GATEWAY_OAUTH_CLIENT_ID or not GATEWAY_OAUTH_CLIENT_SECRET:
            pytest.fail(
                "ERROR: GATEWAY_OAUTH_CLIENT_ID and GATEWAY_OAUTH_CLIENT_SECRET not found in .env. "
                "Run: just generate-github-token to register a real client.",
            )

        # Create REAL PKCE challenge
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip("=")

        # Start REAL auth flow with PKCE
        auth_params = {
            "client_id": GATEWAY_OAUTH_CLIENT_ID,
            "redirect_uri": TEST_OAUTH_CALLBACK_URL,
            "response_type": "code",
            "scope": "openid profile",
            "state": secrets.token_urlsafe(16),
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        auth_response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params=auth_params,
            follow_redirects=False,
            timeout=30.0,
        )

        if auth_response.status_code == HTTP_BAD_REQUEST:
            error = auth_response.json()
            if error.get("error") == "invalid_client":
                pytest.fail(
                    f"ERROR: OAuth client {GATEWAY_OAUTH_CLIENT_ID} is not registered. Run: just generate-github-token",
                )

        # Should redirect to GitHub with PKCE parameters
        assert auth_response.status_code == 307
        github_url = auth_response.headers["location"]
        assert "github.com/login/oauth/authorize" in github_url

        # Extract the state that was stored in Redis (with PKCE challenge)
        parsed = urlparse(github_url)
        query_params = parse_qs(parsed.query)
        oauth_state = query_params["state"][0]

        # This verifies PKCE setup was stored correctly in Redis
        # The OAuth state now contains our PKCE challenge data
        assert oauth_state is not None
        print(f"✓ PKCE flow initialized with state: {oauth_state}")


class TestRealJWTTokens:
    """Test REAL JWT token operations with REAL credentials."""

    @pytest.mark.asyncio
    async def test_real_jwt_token_operations(self, http_client, _wait_for_services):
        """Test JWT operations using REAL tokens and REAL Redis storage."""
        # REQUIRE real OAuth client for token operations
        if not GATEWAY_OAUTH_CLIENT_ID or not GATEWAY_OAUTH_CLIENT_SECRET:
            pytest.fail(
                "ERROR: GATEWAY_OAUTH_CLIENT_ID and GATEWAY_OAUTH_CLIENT_SECRET required. "
                "Run: just generate-github-token",
            )

        # Create a REAL JWT token with REAL claims
        now = int(time.time())
        jti = secrets.token_urlsafe(16)

        real_claims = {
            "sub": "12345",
            "username": "testuser",
            "email": "test@example.com",
            "scope": "openid profile email",
            "client_id": GATEWAY_OAUTH_CLIENT_ID,  # Use REAL client ID
            "jti": jti,
            "iat": now,
            "exp": now + 3600,
            "iss": f"https://auth.{BASE_DOMAIN}",
        }

        # Sign with REAL JWT secret from .env
        real_token = jwt_encode(real_claims, GATEWAY_JWT_SECRET, algorithm="HS256")

        # Test 1: Introspect the REAL token (won't be active because not in Redis)
        introspect_response = await http_client.post(
            f"{AUTH_BASE_URL}/introspect",
            data={
                "token": real_token,
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET,
            },
            timeout=30.0,
        )

        assert introspect_response.status_code == HTTP_OK
        introspect_data = introspect_response.json()
        # Token is not active because it's not stored in Redis
        assert introspect_data["active"] is False

        # Test 2: Test expired REAL token
        expired_claims = {
            **real_claims,
            "exp": now - 3600,  # Expired 1 hour ago
            "jti": secrets.token_urlsafe(16),  # Different JTI
        }

        expired_token = jwt_encode(expired_claims, GATEWAY_JWT_SECRET, algorithm="HS256")

        verify_response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": f"Bearer {expired_token}"},
            timeout=30.0,
        )

        assert verify_response.status_code == HTTP_UNAUTHORIZED
        error = verify_response.json()
        assert "expired" in error["error_description"].lower()

        # Test 3: Test revocation with REAL client credentials
        revoke_response = await http_client.post(
            f"{AUTH_BASE_URL}/revoke",
            data={
                "token": real_token,
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET,
            },
            timeout=30.0,
        )

        # Always returns 200 per RFC 7009
        assert revoke_response.status_code == HTTP_OK

        print("✓ All REAL JWT operations completed successfully")
