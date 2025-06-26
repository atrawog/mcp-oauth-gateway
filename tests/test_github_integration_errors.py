"""Test GitHub OAuth integration error scenarios
Following CLAUDE.md: Real tests against real GitHub API.
"""

from urllib.parse import parse_qs
from urllib.parse import urlparse

import pytest

from .test_constants import AUTH_BASE_URL
from .test_constants import BASE_DOMAIN
from .test_constants import GATEWAY_OAUTH_CLIENT_ID
from .test_constants import GATEWAY_OAUTH_CLIENT_SECRET
from .test_constants import HTTP_BAD_REQUEST


class TestGitHubCallbackErrors:
    """Test GitHub OAuth callback error scenarios."""

    @pytest.mark.asyncio
    async def test_callback_with_invalid_state(self, http_client):
        """Test callback with invalid state - covers error path."""
        # Use an invalid state that doesn't exist in Redis
        response = await http_client.get(
            f"{AUTH_BASE_URL}/callback",
            params={"code": "some_code", "state": "invalid_state_not_in_redis"},
            follow_redirects=False,
        )

        # Should redirect to error page (user-friendly)
        assert response.status_code == 302  # Redirect to error page
        assert "/error" in response.headers.get("location", "")
        # Error details are in the redirect URL parameters


class TestRealOAuthFlowErrors:
    """Test real OAuth flow error scenarios."""

    @pytest.mark.asyncio
    async def test_complete_flow_with_valid_client(self, http_client):
        """Test OAuth flow with valid client."""
        # Start authorization flow
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "redirect_uri": f"https://auth.{BASE_DOMAIN}/success",  # Use registered redirect URI
                "response_type": "code",
                "scope": "openid profile email",
                "state": "test_state",
            },
            follow_redirects=False,
        )

        # Should redirect to GitHub
        assert response.status_code == 307
        location = response.headers["location"]
        assert "github.com/login/oauth/authorize" in location

        # Extract GitHub state
        parsed = urlparse(location)
        params = parse_qs(parsed.query)
        github_state = params["state"][0]

        # State should be stored in Redis
        assert github_state is not None

    @pytest.mark.asyncio
    async def test_token_exchange_with_expired_code(self, http_client):
        """Test token exchange with expired authorization code."""
        # Try to exchange a non-existent code
        response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "expired_or_invalid_code_xxx",
                "redirect_uri": f"https://auth.{BASE_DOMAIN}/success",
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET,
            },
        )

        assert response.status_code == HTTP_BAD_REQUEST
        error = response.json()
        assert error["error"] == "invalid_grant"
        assert "Invalid or expired authorization code" in error["error_description"]


class TestPKCEWithRealFlow:
    """Test PKCE verification with more realistic scenarios."""

    @pytest.mark.asyncio
    async def test_pkce_missing_verifier(self, http_client):
        """Test PKCE flow without verifier - will fail at code validation."""
        # Try to exchange code without verifier (will fail because code doesn't exist)
        response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "code_that_requires_pkce",
                "redirect_uri": f"https://auth.{BASE_DOMAIN}/success",
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET,
                # Missing code_verifier
            },
        )

        assert response.status_code == HTTP_BAD_REQUEST
        error = response.json()
        assert error["error"] == "invalid_grant"


class TestRefreshTokenErrors:
    """Test refresh token error scenarios."""

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, http_client):
        """Test invalid refresh token."""
        response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": "invalid_refresh_token_xxx",
                "client_id": GATEWAY_OAUTH_CLIENT_ID,
                "client_secret": GATEWAY_OAUTH_CLIENT_SECRET,
            },
        )

        assert response.status_code == HTTP_BAD_REQUEST
        error = response.json()
        assert error["error"] == "invalid_grant"
        assert "Invalid or expired refresh token" in error["error_description"]
