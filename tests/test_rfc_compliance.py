"""Test RFC 6749 and RFC 7591 compliance for OAuth endpoints."""

import json

import pytest

from .test_constants import AUTH_BASE_URL
from .test_constants import HTTP_CREATED
from .test_constants import HTTP_OK
from .test_constants import HTTP_UNAUTHORIZED


class TestRFCCompliance:
    """Test that auth service is fully RFC compliant."""

    @pytest.mark.asyncio
    async def test_authorize_invalid_client_rfc6749_compliance(self, http_client):
        """Test that authorize endpoint is RFC 6749 compliant for invalid_client."""
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "client_id": "non_existent_client",
                "redirect_uri": "https://example.com/callback",
                "response_type": "code",
                "state": "test_state",
                "code_challenge": "test_challenge",
                "code_challenge_method": "S256",
            },
            follow_redirects=False,
        )

        assert response.status_code == HTTP_BAD_REQUEST
        try:
            error = response.json()
            assert error["detail"]["error"] == "invalid_client"
            assert (
                error["detail"]["error_description"] == "Client authentication failed"
            )
        except json.JSONDecodeError:
            # If response is not JSON, check if it's an HTML error page
            content = response.text
            assert (
                "invalid_client" in content or "Client authentication failed" in content
            )
        # RFC 6749 compliant - only error and error_description fields

    @pytest.mark.asyncio
    async def test_token_invalid_client_rfc6749_compliance(self, http_client):
        """Test that token endpoint is RFC 6749 Section 5.2 compliant for invalid_client."""
        response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "test_code",
                "redirect_uri": "https://example.com/callback",
                "client_id": "non_existent_client",
                "client_secret": "test_secret",
            },
        )

        assert response.status_code == HTTP_UNAUTHORIZED
        assert response.headers.get("WWW-Authenticate") == "Basic"
        error = response.json()
        assert error["detail"]["error"] == "invalid_client"
        assert error["detail"]["error_description"] == "Client authentication failed"
        # RFC 6749 Section 5.2 compliant - only error and error_description fields

    @pytest.mark.asyncio
    async def test_oauth_discovery_includes_registration_endpoint(self, http_client):
        """Test that OAuth discovery metadata includes registration endpoint."""
        response = await http_client.get(
            f"{AUTH_BASE_URL}/.well-known/oauth-authorization-server"
        )

        assert response.status_code == HTTP_OK
        metadata = response.json()
        assert metadata["registration_endpoint"] == f"{AUTH_BASE_URL}/register"
        assert metadata["issuer"] == AUTH_BASE_URL

        # Check new optional fields
        assert "service_documentation" in metadata
        assert "op_policy_uri" in metadata
        assert "op_tos_uri" in metadata

    @pytest.mark.asyncio
    async def test_registration_invalid_redirect_uri_rfc7591(self, http_client):
        """Test RFC 7591 compliance for invalid redirect URI."""
        # Test HTTP URI for non-localhost
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": ["http://example.com/callback"],
                "client_name": "TEST Test Client",
            },
        )

        assert response.status_code == HTTP_BAD_REQUEST
        error = response.json()
        assert error["detail"]["error"] == "invalid_redirect_uri"
        assert "localhost" in error["detail"]["error_description"]

    @pytest.mark.asyncio
    async def test_registration_valid_redirect_uris_rfc7591(self, http_client):
        """Test RFC 7591 compliance for valid redirect URIs."""
        # Test various valid redirect URIs
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": [
                    "https://example.com/callback",  # HTTPS
                    "http://localhost:3000/callback",  # HTTP localhost
                    "http://127.0.0.1:8080/callback",  # HTTP 127.0.0.1
                    "myapp://callback",  # App-specific URI
                ],
                "client_name": "TEST Test Client",
            },
        )

        assert response.status_code == HTTP_CREATED
        client = response.json()
        assert "client_id" in client
        assert "client_secret" in client
        assert len(client["redirect_uris"]) == 4

        # Cleanup: Delete the client registration using RFC 7592
        if "registration_access_token" in client and "client_id" in client:
            try:
                delete_response = await http_client.delete(
                    f"{AUTH_BASE_URL}/register/{client['client_id']}",
                    headers={
                        "Authorization": f"Bearer {client['registration_access_token']}"
                    },
                )
                # 204 No Content is success, 404 is okay if already deleted
                if delete_response.status_code not in (204, 404):
                    print(
                        f"Warning: Failed to delete client {client['client_id']}: {delete_response.status_code}"  # TODO: Break long line
                    )
            except Exception as e:
                print(f"Warning: Error during client cleanup: {e}")

    @pytest.mark.asyncio
    async def test_registration_missing_redirect_uris_rfc7591(self, http_client):
        """Test RFC 7591 compliance for missing redirect_uris."""
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register", json={"client_name": "TEST Test Client"}
        )

        # RFC 7591 - Returns 400 with proper error format
        assert response.status_code == HTTP_BAD_REQUEST
        error = response.json()
        assert error["detail"]["error"] == "invalid_client_metadata"
        assert "redirect_uris is required" in error["detail"]["error_description"]
