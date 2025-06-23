"""Security tests for OAuth client registration endpoint
Following CLAUDE.md - NO MOCKING, real services only!
Tests OAuth 2.0 security model where registration is public (RFC 7591)
and security is enforced at authorization/token issuance stage.
"""

import pytest

from .test_constants import AUTH_BASE_URL
from .test_constants import GATEWAY_OAUTH_ACCESS_TOKEN


class TestRegisterEndpointSecurity:
    """Test OAuth client registration endpoint security."""

    @pytest.mark.asyncio
    async def test_register_is_public_endpoint(self, http_client, wait_for_services):
        """Test that /register endpoint is public per RFC 7591."""
        registration_data = {
            "redirect_uris": ["https://example.com/callback"],
            "client_name": "TEST test_register_is_public_endpoint",
            "scope": "openid profile email",
        }

        # Test without Authorization header - should succeed per RFC 7591
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register", json=registration_data
        )

        # Registration should succeed without authentication
        assert response.status_code == 201
        client_data = response.json()
        assert "client_id" in client_data
        assert "client_secret" in client_data
        assert client_data["client_name"] == "TEST test_register_is_public_endpoint"

        # Security is enforced at authorization/token stage, not registration

        # Cleanup: Delete the client registration using RFC 7592
        if "registration_access_token" in client_data:
            try:
                delete_response = await http_client.delete(
                    f"{AUTH_BASE_URL}/register/{client_data['client_id']}",
                    headers={
                        "Authorization": f"Bearer {client_data['registration_access_token']}"
                    },
                )
                assert delete_response.status_code in (204, 404)
            except Exception as e:
                print(f"Warning: Error during client cleanup: {e}")

    @pytest.mark.asyncio
    async def test_register_ignores_authorization_headers(
        self, http_client, wait_for_services
    ):
        """Test that /register endpoint ignores auth headers per RFC 7591."""
        registration_data = {
            "redirect_uris": ["https://example.com/callback"],
            "client_name": "TEST test_register_ignores_authorization_headers",
            "scope": "openid profile email",
        }

        # Test with various authorization schemes - all should succeed
        # because registration is public per RFC 7591
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data,
            headers={"Authorization": "Basic invalid_scheme"},
        )

        # Should succeed regardless of auth header
        assert response.status_code == 201
        client_data = response.json()
        assert "client_id" in client_data
        assert (
            client_data["client_name"]
            == "TEST test_register_ignores_authorization_headers"
        )

        # Cleanup: Delete the client registration using RFC 7592
        if "registration_access_token" in client_data:
            try:
                delete_response = await http_client.delete(
                    f"{AUTH_BASE_URL}/register/{client_data['client_id']}",
                    headers={
                        "Authorization": f"Bearer {client_data['registration_access_token']}"
                    },
                )
                assert delete_response.status_code in (204, 404)
            except Exception as e:
                print(f"Warning: Error during client cleanup: {e}")

    @pytest.mark.asyncio
    async def test_security_enforced_at_authorization_stage(
        self, http_client, wait_for_services
    ):
        """Test that security is enforced at authorization, not registration."""
        # First, register a client publicly (no auth required)
        registration_data = {
            "redirect_uris": ["https://example.com/callback"],
            "client_name": "TEST test_security_enforced_at_authorization_stage",
            "scope": "openid profile email",
        }

        response = await http_client.post(
            f"{AUTH_BASE_URL}/register", json=registration_data
        )

        assert response.status_code == 201
        client_data = response.json()
        client_id = client_data["client_id"]

        # Now try to use the client for authorization - THIS requires user auth
        auth_response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "client_id": client_id,
                "redirect_uri": "https://example.com/callback",
                "response_type": "code",
                "state": "test_state",
            },
            follow_redirects=False,
        )

        # Should redirect to GitHub for user authentication
        # Both 302 and 307 are valid redirect status codes
        assert auth_response.status_code in [302, 307]
        assert "github.com/login/oauth/authorize" in auth_response.headers["location"]

        # Cleanup: Delete the client registration using RFC 7592
        if "registration_access_token" in client_data:
            try:
                delete_response = await http_client.delete(
                    f"{AUTH_BASE_URL}/register/{client_data['client_id']}",
                    headers={
                        "Authorization": f"Bearer {client_data['registration_access_token']}"
                    },
                )
                assert delete_response.status_code in (204, 404)
            except Exception as e:
                print(f"Warning: Error during client cleanup: {e}")

    @pytest.mark.asyncio
    async def test_register_with_valid_token_still_succeeds(
        self, http_client, wait_for_services
    ):
        """Test that /register endpoint succeeds even with valid token (public endpoint)."""
        # Even if we have a valid token, registration should still work
        # because it's a public endpoint per RFC 7591
        registration_data = {
            "redirect_uris": ["https://example.com/callback"],
            "client_name": "TEST test_register_with_valid_token_still_succeeds",
            "scope": "openid profile email",
        }

        # Test with valid OAuth access token (if available)
        headers = {}
        if GATEWAY_OAUTH_ACCESS_TOKEN:
            headers["Authorization"] = f"Bearer {GATEWAY_OAUTH_ACCESS_TOKEN}"

        response = await http_client.post(
            f"{AUTH_BASE_URL}/register", json=registration_data, headers=headers
        )

        # Should succeed regardless of token presence
        assert response.status_code == 201
        client_data = response.json()
        assert "client_id" in client_data
        assert "client_secret" in client_data
        assert (
            client_data["client_name"]
            == "TEST test_register_with_valid_token_still_succeeds"
        )

        # Cleanup: Delete the client registration using RFC 7592
        if "registration_access_token" in client_data:
            try:
                delete_response = await http_client.delete(
                    f"{AUTH_BASE_URL}/register/{client_data['client_id']}",
                    headers={
                        "Authorization": f"Bearer {client_data['registration_access_token']}"
                    },
                )
                assert delete_response.status_code in (204, 404)
            except Exception as e:
                print(f"Warning: Error during client cleanup: {e}")

    @pytest.mark.asyncio
    async def test_token_endpoint_requires_authentication(
        self, http_client, wait_for_services
    ):
        """Test that token endpoint requires proper client authentication."""
        # First register a client (public, no auth)
        reg_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": ["https://example.com/callback"],
                "client_name": "TEST test_token_endpoint_requires_authentication",
            },
        )

        assert reg_response.status_code == 201
        client = reg_response.json()

        # Now try to get tokens without proper client authentication
        token_response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": "fake_code",
                "redirect_uri": "https://example.com/callback",
                "client_id": client["client_id"],
                "client_secret": "wrong_secret",  # Wrong secret
            },
        )

        # Should fail due to invalid client authentication
        assert token_response.status_code == 401
        error = token_response.json()
        assert error["detail"]["error"] == "invalid_client"

        # Cleanup: Delete the client registration using RFC 7592
        if "registration_access_token" in client:
            try:
                delete_response = await http_client.delete(
                    f"{AUTH_BASE_URL}/register/{client['client_id']}",
                    headers={
                        "Authorization": f"Bearer {client['registration_access_token']}"
                    },
                )
                assert delete_response.status_code in (204, 404)
            except Exception as e:
                print(f"Warning: Error during client cleanup: {e}")

    @pytest.mark.asyncio
    async def test_multiple_clients_can_register_publicly(
        self, http_client, wait_for_services
    ):
        """Test that multiple clients can register without authentication."""
        # Register multiple clients to verify public registration works
        clients = []

        for i in range(3):
            registration_data = {
                "redirect_uris": [f"https://client{i}.example.com/callback"],
                "client_name": f"TEST test_multiple_clients_can_register_publicly_{i}",
                "scope": "openid profile email",
            }

            response = await http_client.post(
                f"{AUTH_BASE_URL}/register", json=registration_data
            )

            # All registrations should succeed
            assert response.status_code == 201
            client_data = response.json()
            assert "client_id" in client_data
            assert "client_secret" in client_data
            assert (
                client_data["client_name"]
                == f"TEST test_multiple_clients_can_register_publicly_{i}"
            )
            clients.append(client_data)

        # Ensure all clients have unique IDs
        client_ids = [c["client_id"] for c in clients]
        assert len(set(client_ids)) == 3

        # Cleanup: Delete all client registrations using RFC 7592
        for client in clients:
            if "registration_access_token" in client:
                try:
                    delete_response = await http_client.delete(
                        f"{AUTH_BASE_URL}/register/{client['client_id']}",
                        headers={
                            "Authorization": f"Bearer {client['registration_access_token']}"
                        },
                    )
                    assert delete_response.status_code in (204, 404)
                except Exception as e:
                    print(f"Warning: Error during client cleanup: {e}")


class TestRegisterEndpointBootstrap:
    """Test bootstrap scenarios for OAuth client registration."""

    @pytest.mark.asyncio
    async def test_anyone_can_register_multiple_clients(
        self, http_client, wait_for_services
    ):
        """Test that anyone can register multiple OAuth clients (public endpoint)."""
        # RFC 7591: Dynamic client registration is a public endpoint
        # No authentication required for registration

        # Register first client without any authentication
        response1 = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": ["https://app1.example.com/callback"],
                "client_name": "TEST test_anyone_can_register_multiple_clients_1",
                "scope": "openid profile email",
            },
        )

        assert response1.status_code == 201
        client1 = response1.json()

        # Register second client also without authentication
        response2 = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": ["https://app2.example.com/callback"],
                "client_name": "TEST test_anyone_can_register_multiple_clients_2",
                "scope": "openid profile",
            },
        )

        assert response2.status_code == 201
        client2 = response2.json()

        # Ensure clients have different IDs
        assert client1["client_id"] != client2["client_id"]
        assert client1["client_secret"] != client2["client_secret"]

        # Security note: While registration is public, using these clients
        # for authorization requires user authentication via GitHub OAuth

        # Cleanup: Delete both client registrations using RFC 7592
        for client in [client1, client2]:
            if "registration_access_token" in client:
                try:
                    delete_response = await http_client.delete(
                        f"{AUTH_BASE_URL}/register/{client['client_id']}",
                        headers={
                            "Authorization": f"Bearer {client['registration_access_token']}"
                        },
                    )
                    assert delete_response.status_code in (204, 404)
                except Exception as e:
                    print(f"Warning: Error during client cleanup: {e}")
