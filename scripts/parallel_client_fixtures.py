# Add these fixtures to conftest.py for parallel-safe client registration

import os
import time
import uuid

import httpx
import pytest


# Import these from your test_constants module or define them
# from .test_constants import AUTH_BASE_URL, TEST_OAUTH_CALLBACK_URL, TEST_CLIENT_SCOPE, TEST_HTTP_TIMEOUT

# Placeholder constants - replace with actual imports when integrating into conftest.py
AUTH_BASE_URL = "http://auth:8000"
TEST_OAUTH_CALLBACK_URL = "https://test.example.com/callback"
TEST_CLIENT_SCOPE = "mcp"
TEST_HTTP_TIMEOUT = 30.0


@pytest.fixture
def worker_id(request):
    """Return the current pytest-xdist worker ID.

    Returns 'master' if not running in parallel mode.
    Returns 'gw0', 'gw1', etc. when running with pytest-xdist.
    """
    return os.environ.get("PYTEST_XDIST_WORKER", "master")


@pytest.fixture
def unique_test_id(request, worker_id):
    """Generate a unique test identifier including worker ID.

    Format: {worker_id}_{timestamp}_{uuid}_{test_name}.
    """
    test_name = request.node.name.replace("[", "_").replace("]", "_").replace(" ", "_")
    timestamp = int(time.time() * 1000)  # Millisecond precision
    unique_part = str(uuid.uuid4())[:8]
    return f"{worker_id}_{timestamp}_{unique_part}_{test_name}"


@pytest.fixture
def unique_client_name(unique_test_id):
    """Generate a guaranteed unique client name for OAuth registration.

    This ensures no conflicts between parallel test workers.
    """
    # Keep the TEST prefix for consistency with existing patterns
    return f"TEST {unique_test_id}"


@pytest.fixture
async def registered_client(http_client: httpx.AsyncClient, unique_client_name):
    """Create and register a test OAuth client with automatic cleanup.

    Each test gets its own unique client to prevent parallel conflicts.
    """
    # Register client with unique name
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": [TEST_OAUTH_CALLBACK_URL],
            "client_name": unique_client_name,
            "scope": TEST_CLIENT_SCOPE,
        },
        timeout=TEST_HTTP_TIMEOUT,
    )
    assert response.status_code == 201
    client_data = response.json()

    # Store the registration access token for cleanup
    registration_token = client_data.get("registration_access_token")

    yield client_data

    # Cleanup: Delete the client using RFC 7592
    if registration_token and "registration_client_uri" in client_data:
        try:
            delete_response = await http_client.delete(
                client_data["registration_client_uri"],
                headers={"Authorization": f"Bearer {registration_token}"},
                timeout=TEST_HTTP_TIMEOUT,
            )
            # 204 No Content is expected for successful deletion
            assert delete_response.status_code in (204, 404)
        except Exception as e:
            # Log but don't fail the test if cleanup fails
            print(f"Warning: Failed to cleanup client {client_data['client_id']}: {e}")
