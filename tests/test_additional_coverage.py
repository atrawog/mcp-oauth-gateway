"""Additional coverage tests for edge cases and error conditions
Following CLAUDE.md - NO MOCKING, real services only!
"""

import os
import secrets
import time

import pytest

from .jwt_test_helper import encode as jwt_encode
from .test_constants import ACCESS_TOKEN_LIFETIME
from .test_constants import AUTH_BASE_URL
from .test_constants import GATEWAY_OAUTH_ACCESS_TOKEN
from .test_constants import HTTP_BAD_REQUEST
from .test_constants import HTTP_CREATED
from .test_constants import HTTP_OK
from .test_constants import HTTP_UNAUTHORIZED
from .test_constants import HTTP_UNPROCESSABLE_ENTITY
from .test_constants import TEST_OAUTH_CALLBACK_URL


class TestAdditionalCoverage:
    """Test additional edge cases to improve coverage."""

    @pytest.mark.asyncio
    async def test_missing_authorization_header_formats(self, http_client, _wait_for_services):
        """Test various missing/malformed authorization headers."""
        # Test with no Authorization header at all (already covered)
        response = await http_client.get(f"{AUTH_BASE_URL}/verify", timeout=30.0)
        assert response.status_code == HTTP_UNAUTHORIZED

        # Test with empty Authorization header
        response = await http_client.get(f"{AUTH_BASE_URL}/verify", headers={"Authorization": ""}, timeout=30.0)
        assert response.status_code == HTTP_UNAUTHORIZED

        # Test with Authorization but no Bearer
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": "InvalidScheme token123"},
            timeout=30.0,
        )
        assert response.status_code == HTTP_UNAUTHORIZED

        # Test with Bearer but no token
        response = await http_client.get(f"{AUTH_BASE_URL}/verify", headers={"Authorization": "Bearer"}, timeout=30.0)
        assert response.status_code == HTTP_UNAUTHORIZED

        # Test with Bearer and space but no token - Skip this as httpx doesn't allow it
        # httpx validates headers and won't send "Bearer " with trailing space

    @pytest.mark.asyncio
    async def test_token_endpoint_missing_client_credentials(self, http_client, _wait_for_services, registered_client):
        """Test token endpoint with missing client credentials."""
        # Use registered_client fixture which provides unique name and handles cleanup
        client = registered_client

        # Test with missing client_id
        token_response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "some_code",
                "client_secret": client["client_secret"],
            },
            timeout=30.0,
        )

        # FastAPI returns 422 for missing required fields
        assert token_response.status_code == HTTP_UNPROCESSABLE_ENTITY

        # Test with missing client_secret for confidential client
        token_response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "some_code",
                "client_id": client["client_id"],
            },
            timeout=30.0,
        )

        # Returns 400 for missing client_secret
        assert token_response.status_code == HTTP_BAD_REQUEST
        # FastAPI may return different error format
        error_data = token_response.json()
        # Check for error in either format
        assert "error" in error_data or "detail" in error_data

    @pytest.mark.asyncio
    async def test_introspect_with_malformed_token(
        self,
        http_client,
        _wait_for_services,
        registered_client,
    ):
        """Test introspect endpoint with various malformed tokens."""
        # Test with non-JWT token
        response = await http_client.post(
            f"{AUTH_BASE_URL}/introspect",
            data={
                "token": "not_a_jwt_token",
                "client_id": registered_client["client_id"],
                "client_secret": registered_client["client_secret"],
            },
            timeout=30.0,
        )

        assert response.status_code == HTTP_OK
        result = response.json()
        assert result["active"] is False

        # Test with malformed JWT (invalid format)
        response = await http_client.post(
            f"{AUTH_BASE_URL}/introspect",
            data={
                "token": "eyJ.invalid.jwt",
                "client_id": registered_client["client_id"],
                "client_secret": registered_client["client_secret"],
            },
            timeout=30.0,
        )

        assert response.status_code == HTTP_OK
        result = response.json()
        assert result["active"] is False

    @pytest.mark.asyncio
    async def test_registration_with_minimal_data(self, http_client, _wait_for_services, unique_client_name):
        """Test client registration with only required fields."""
        # MUST have OAuth access token - test FAILS if not available
        assert GATEWAY_OAUTH_ACCESS_TOKEN, "GATEWAY_OAUTH_ACCESS_TOKEN not available - run: just generate-github-token"

        client = None
        try:
            # Register with absolute minimum data
            registration_data = {
                "redirect_uris": [TEST_OAUTH_CALLBACK_URL],
                "client_name": unique_client_name,
            }

            response = await http_client.post(
                f"{AUTH_BASE_URL}/register",
                json=registration_data,
                headers={"Authorization": f"Bearer {GATEWAY_OAUTH_ACCESS_TOKEN}"},
                timeout=30.0,
            )

            assert response.status_code == HTTP_CREATED
            client = response.json()

            # Should have generated defaults
            assert "client_id" in client
            assert "client_secret" in client
            # Check client_secret_expires_at matches CLIENT_LIFETIME from .env
            client_lifetime = int(os.environ.get("CLIENT_LIFETIME", "7776000"))
            if client_lifetime == 0:
                assert client["client_secret_expires_at"] == 0  # Never expires
            else:
                # Should be created_at + CLIENT_LIFETIME
                created_at = client.get("client_id_issued_at")
                expected_expiry = created_at + client_lifetime
                assert abs(client["client_secret_expires_at"] - expected_expiry) <= 5

        finally:
            # Clean up the created client using RFC 7592 DELETE
            if client and "registration_access_token" in client and "client_id" in client:
                try:
                    delete_response = await http_client.delete(
                        f"{AUTH_BASE_URL}/register/{client['client_id']}",
                        headers={
                            "Authorization": f"Bearer {client['registration_access_token']}",  # TODO: Break long line
                        },
                        timeout=30.0,
                    )
                    # 204 No Content is success, 404 is okay if already deleted
                    if delete_response.status_code not in (204, 404):
                        print(
                            f"Warning: Failed to delete client {client['client_id']}: {delete_response.status_code}",  # TODO: Break long line
                        )
                except Exception as e:
                    print(f"Warning: Error during client cleanup: {e}")

    @pytest.mark.asyncio
    async def test_jwt_with_invalid_signature(
        self,
        http_client,
        _wait_for_services,
        registered_client,
    ):
        """Test JWT verification with invalid signature."""
        # Create a JWT with wrong secret
        wrong_secret = "wrong_secret_key_that_is_not_correct"

        token_data = {
            "sub": "testuser",
            "jti": secrets.token_urlsafe(16),
            "iat": int(time.time()),
            "exp": int(time.time()) + ACCESS_TOKEN_LIFETIME,
            "scope": "openid profile email",
            "client_id": registered_client["client_id"],
        }

        # Sign with wrong secret
        invalid_token = jwt_encode(token_data, wrong_secret, algorithm="HS256")

        # Try to verify
        response = await http_client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": f"Bearer {invalid_token}"},
            timeout=30.0,
        )

        assert response.status_code == HTTP_UNAUTHORIZED
        error = response.json()
        # Handle both OAuth 2.0 format and custom format
        if "error_description" in error or ("detail" in error and isinstance(error["detail"], dict)):
            assert "The access token is invalid or expired" in error["error_description"]
        else:
            raise AssertionError(f"Unexpected error structure: {error}")

    @pytest.mark.asyncio
    async def test_authorize_endpoint_missing_parameters(
        self,
        http_client,
        _wait_for_services,
        registered_client,
    ):
        """Test authorize endpoint with missing required parameters."""
        # Missing response_type
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "client_id": registered_client["client_id"],
                "redirect_uri": registered_client["redirect_uris"][0],
            },
            timeout=30.0,
        )

        # FastAPI returns 422 for missing required query parameters
        assert response.status_code == HTTP_UNPROCESSABLE_ENTITY

        # Missing client_id
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={"response_type": "code", "redirect_uri": TEST_OAUTH_CALLBACK_URL},
            timeout=30.0,
        )

        # FastAPI returns 422 for missing required query parameters
        assert response.status_code == HTTP_UNPROCESSABLE_ENTITY
