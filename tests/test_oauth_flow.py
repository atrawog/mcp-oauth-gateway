"""Sacred OAuth Flow Tests - NO MOCKING! Real services only!
Tests the complete OAuth 2.1 flow with RFC 7591 compliance.
"""

import base64
import hashlib
import json
import os
import secrets

import pytest

from .test_constants import AUTH_BASE_URL
from .test_constants import GATEWAY_OAUTH_ACCESS_TOKEN
from .test_constants import HTTP_BAD_REQUEST
from .test_constants import HTTP_CREATED
from .test_constants import HTTP_NOT_FOUND
from .test_constants import HTTP_OK
from .test_constants import HTTP_UNAUTHORIZED
from .test_constants import TEST_INVALID_REDIRECT_URI
from .test_constants import TEST_OAUTH_CALLBACK_URL


class TestOAuthFlow:
    """Test the complete OAuth 2.1 flow."""

    @pytest.mark.asyncio
    async def test_server_metadata(self, http_client, _wait_for_services):
        """Test .well-known/oauth-authorization-server endpoint."""
        response = await http_client.get(f"{AUTH_BASE_URL}/.well-known/oauth-authorization-server")

        assert response.status_code == HTTP_OK
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
    async def test_client_registration_rfc7591(self, http_client, _wait_for_services):
        """Test dynamic client registration per RFC 7591."""
        # MUST have OAuth access token - test FAILS if not available
        assert GATEWAY_OAUTH_ACCESS_TOKEN, "GATEWAY_OAUTH_ACCESS_TOKEN not available - run: just generate-github-token"

        # Track created clients for cleanup
        created_clients = []

        try:
            # Test successful registration
            registration_data = {
                "redirect_uris": ["https://example.com/callback"],
                "client_name": "TEST test_client_registration_rfc7591",
                "client_uri": "https://example.com",
                "scope": "openid profile",
                "contacts": ["admin@example.com"],
            }

            response = await http_client.post(
                f"{AUTH_BASE_URL}/register",
                json=registration_data,
                headers={"Authorization": f"Bearer {GATEWAY_OAUTH_ACCESS_TOKEN}"},
            )

            assert response.status_code == HTTP_CREATED  # MUST return 201 Created
            client = response.json()
            created_clients.append(client)  # Track for cleanup

            # Verify required fields in response
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

            # Verify metadata is echoed back
            assert client["redirect_uris"] == registration_data["redirect_uris"]
            assert client["client_name"] == registration_data["client_name"]
            assert client["client_uri"] == registration_data["client_uri"]

            # Test missing redirect_uris (with proper authentication)
            invalid_data = {"client_name": "TEST test_client_registration_rfc7591_invalid"}
            response = await http_client.post(
                f"{AUTH_BASE_URL}/register",
                json=invalid_data,
                headers={"Authorization": f"Bearer {GATEWAY_OAUTH_ACCESS_TOKEN}"},
            )

            assert response.status_code == HTTP_BAD_REQUEST  # RFC 7591 compliant error
            error = response.json()
            assert error["error"] == "invalid_client_metadata"
            assert "redirect_uris is required" in error["error_description"]

        finally:
            # Clean up all created clients using RFC 7592 DELETE
            for client in created_clients:
                if "registration_access_token" in client and "client_id" in client:
                    try:
                        delete_response = await http_client.delete(
                            f"{AUTH_BASE_URL}/register/{client['client_id']}",
                            headers={
                                "Authorization": f"Bearer {client['registration_access_token']}",  # TODO: Break long line
                            },
                        )
                        # 204 No Content is success, 404 is okay if already deleted
                        if delete_response.status_code not in (204, 404):
                            print(
                                f"Warning: Failed to delete client {client['client_id']}: {delete_response.status_code}",  # TODO: Break long line
                            )
                    except Exception as e:
                        print(f"Warning: Error during client cleanup: {e}")

    @pytest.mark.asyncio
    async def test_authorization_endpoint_validation(self, http_client, registered_client):
        """Test authorization endpoint with invalid client handling."""
        # Test with invalid client_id - MUST NOT redirect
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "client_id": "invalid_client",
                "redirect_uri": TEST_OAUTH_CALLBACK_URL,
                "response_type": "code",
                "state": "test_state",
            },
            follow_redirects=False,
        )

        assert response.status_code == HTTP_BAD_REQUEST  # MUST return error, not redirect
        try:
            error = response.json()
            assert error["error"] == "invalid_client"
        except json.JSONDecodeError:
            # If response is not JSON, check if it's an HTML error page
            content = response.text
            assert "invalid_client" in content or "Client authentication failed" in content

        # Test with valid client but invalid redirect_uri - MUST NOT redirect
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "client_id": registered_client["client_id"],
                "redirect_uri": TEST_INVALID_REDIRECT_URI,
                "response_type": "code",
                "state": "test_state",
            },
            follow_redirects=False,
        )

        assert response.status_code == HTTP_BAD_REQUEST
        error = response.json()
        assert error["error"] == "invalid_redirect_uri"

    @pytest.mark.asyncio
    async def test_pkce_flow(self, http_client, registered_client):
        """Test PKCE (RFC 7636) with S256 challenge method."""
        # Generate PKCE challenge
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode("utf-8").rstrip("=")
        )

        # Start authorization flow with PKCE
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "client_id": registered_client["client_id"],
                "redirect_uri": registered_client["redirect_uris"][0],
                "response_type": "code",
                "state": "pkce_test",
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            },
            follow_redirects=False,
        )

        # Should redirect to GitHub OAuth
        assert response.status_code in [302, 307]  # Accept either redirect code
        location = response.headers["location"]
        assert "github.com/login/oauth/authorize" in location

    @pytest.mark.asyncio
    async def test_token_endpoint_errors(self, http_client, registered_client):
        """Test token endpoint error handling."""
        # Test invalid client
        response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "invalid_code",
                "client_id": "invalid_client",
                "redirect_uri": "http://localhost:8080/callback",
            },
        )

        assert response.status_code == HTTP_UNAUTHORIZED
        assert response.headers.get("WWW-Authenticate") == "Basic"
        error = response.json()
        assert error["error"] == "invalid_client"

        # Test invalid grant
        response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "invalid_code",
                "client_id": registered_client["client_id"],
                "client_secret": registered_client["client_secret"],
                "redirect_uri": registered_client["redirect_uris"][0],
            },
        )

        assert response.status_code == HTTP_BAD_REQUEST
        error = response.json()
        assert error["error"] == "invalid_grant"

    @pytest.mark.asyncio
    async def test_token_introspection(self, http_client, registered_client):
        """Test token introspection endpoint (RFC 7662)."""
        # Test with invalid token
        response = await http_client.post(
            f"{AUTH_BASE_URL}/introspect",
            data={
                "token": "invalid_token",
                "client_id": registered_client["client_id"],
                "client_secret": registered_client["client_secret"],
            },
        )

        # Introspection endpoint might not be implemented yet
        if response.status_code == HTTP_NOT_FOUND:
            pytest.skip("Introspection endpoint not implemented")
        assert response.status_code == HTTP_OK
        result = response.json()
        assert result["active"] is False

    @pytest.mark.asyncio
    async def test_token_revocation(self, http_client, registered_client):
        """Test token revocation endpoint (RFC 7009)."""
        # Revocation always returns 200, even for invalid tokens
        response = await http_client.post(
            f"{AUTH_BASE_URL}/revoke",
            data={
                "token": "any_token",
                "client_id": registered_client["client_id"],
                "client_secret": registered_client["client_secret"],
            },
        )

        # Revocation endpoint might not be implemented yet
        if response.status_code == HTTP_NOT_FOUND:
            pytest.skip("Revocation endpoint not implemented")
        assert response.status_code == HTTP_OK  # Always 200 per RFC 7009

    @pytest.mark.asyncio
    async def test_forwardauth_verification(self, http_client):
        """Test ForwardAuth /verify endpoint."""
        # Test without token
        response = await http_client.get(f"{AUTH_BASE_URL}/verify")

        assert response.status_code == HTTP_UNAUTHORIZED
        assert response.headers.get("WWW-Authenticate") == "Bearer"

        # Test with invalid token
        response = await http_client.get(f"{AUTH_BASE_URL}/verify", headers={"Authorization": "Bearer invalid_token"})

        assert response.status_code == HTTP_UNAUTHORIZED
        error = response.json()
        assert error["error"] == "invalid_token"
