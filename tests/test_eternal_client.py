from .test_constants import HTTP_OK


"""Test eternal client registration with CLIENT_LIFETIME=0."""

import os

import pytest


base_domain = os.environ.get("BASE_DOMAIN")
if not base_domain:
    raise Exception("BASE_DOMAIN must be set in environment")
AUTH_BASE_URL = f"https://auth.{base_domain}"
CLIENT_LIFETIME = int(os.environ.get("CLIENT_LIFETIME", "7776000"))


@pytest.mark.asyncio
async def test_client_lifetime_from_env(http_client, registered_client):
    """Test that CLIENT_LIFETIME from .env is respected."""
    # Use registered_client fixture which handles cleanup automatically
    data = registered_client

    # Check if client_secret_expires_at matches expected behavior
    expires_at = data.get("client_secret_expires_at")
    created_at = data.get("client_id_issued_at")

    if CLIENT_LIFETIME == 0:
        # Eternal client
        assert expires_at == 0, f"Expected eternal client (0) but got {expires_at}"
    else:
        # Expiring client
        expected_expiry = created_at + CLIENT_LIFETIME
        # Allow 5 second tolerance for processing time
        assert abs(expires_at - expected_expiry) <= 5, f"Expected expiry around {expected_expiry} but got {expires_at}"

    # Test RFC 7592 GET endpoint
    client_id = data["client_id"]
    data["client_secret"]
    registration_token = data.get("registration_access_token")
    assert registration_token, "registration_access_token missing from registration response"

    # Get client registration using Bearer token
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": f"Bearer {registration_token}"},
    )

    assert response.status_code == HTTP_OK
    client_info = response.json()
    assert client_info["client_secret_expires_at"] == expires_at

    # Verify we can still access the client (it exists)
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": f"Bearer {registration_token}"},
    )

    assert response.status_code == HTTP_OK


@pytest.mark.asyncio
async def test_rfc7592_update_client(http_client, _wait_for_services):
    """Test RFC 7592 PUT endpoint to update client registration."""
    from .conftest import RegisteredClientContext

    # Use RegisteredClientContext for automatic cleanup
    async with RegisteredClientContext(http_client) as ctx:
        # Register a client
        original = await ctx.register_client(
            {
                "redirect_uris": ["https://test.example.com/callback"],
                "client_name": "Original Name",
                "scope": "openid",
            }
        )

        client_id = original["client_id"]
        client_secret = original["client_secret"]
        registration_token = original.get("registration_access_token")
        assert registration_token, "registration_access_token missing from registration response"

        # Update the client
        update_data = {
            "redirect_uris": [
                "https://updated.example.com/callback",
                "https://second.example.com/callback",
            ],
            "client_name": "Updated Name",
            "scope": "openid profile email",
        }

        response = await http_client.put(
            f"{AUTH_BASE_URL}/register/{client_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {registration_token}"},
        )

        assert response.status_code == HTTP_OK
        updated = response.json()

        # Verify updates
        assert updated["redirect_uris"] == update_data["redirect_uris"]
        assert updated["client_name"] == update_data["client_name"]
        assert updated["scope"] == update_data["scope"]

        # Verify client_id and secret unchanged
        assert updated["client_id"] == client_id
        assert updated["client_secret"] == client_secret
