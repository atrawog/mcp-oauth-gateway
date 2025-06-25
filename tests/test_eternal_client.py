from .test_constants import HTTP_CREATED
from .test_constants import HTTP_NO_CONTENT
from .test_constants import HTTP_NOT_FOUND
from .test_constants import HTTP_OK


"""Test eternal client registration with CLIENT_LIFETIME=0."""

import os

import pytest


base_domain = os.environ.get('BASE_DOMAIN')
if not base_domain:
    raise Exception("BASE_DOMAIN must be set in environment")
AUTH_BASE_URL = f"https://auth.{base_domain}"
CLIENT_LIFETIME = int(os.environ.get("CLIENT_LIFETIME", "7776000"))


@pytest.mark.asyncio
async def test_client_lifetime_from_env(http_client):
    """Test that CLIENT_LIFETIME from .env is respected."""
    # Register a client
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": ["https://test.example.com/callback"],
            "client_name": "Test Client Lifetime",
        },
    )

    assert response.status_code == HTTP_CREATED
    data = response.json()

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
        assert abs(expires_at - expected_expiry) <= 5, (
            f"Expected expiry around {expected_expiry} but got {expires_at}"
        )

    # Test RFC 7592 GET endpoint
    client_id = data["client_id"]
    data["client_secret"]
    registration_token = data.get("registration_access_token")
    assert registration_token, (
        "registration_access_token missing from registration response"
    )

    # Get client registration using Bearer token
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": f"Bearer {registration_token}"},
    )

    assert response.status_code == HTTP_OK
    client_info = response.json()
    assert client_info["client_secret_expires_at"] == expires_at

    # Test DELETE endpoint
    response = await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": f"Bearer {registration_token}"},
    )

    assert response.status_code == HTTP_NO_CONTENT

    # Verify client is deleted
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": f"Bearer {registration_token}"},
    )

    assert response.status_code == HTTP_NOT_FOUND


@pytest.mark.asyncio
async def test_rfc7592_update_client(http_client):
    """Test RFC 7592 PUT endpoint to update client registration."""
    # First register a client
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": ["https://test.example.com/callback"],
            "client_name": "Original Name",
            "scope": "openid",
        },
    )

    assert response.status_code == HTTP_CREATED
    original = response.json()

    client_id = original["client_id"]
    client_secret = original["client_secret"]
    registration_token = original.get("registration_access_token")
    assert registration_token, (
        "registration_access_token missing from registration response"
    )

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

    # Clean up
    response = await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": f"Bearer {registration_token}"},
    )
    assert response.status_code == HTTP_NO_CONTENT
