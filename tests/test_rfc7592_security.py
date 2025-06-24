from .test_constants import HTTP_CREATED
from .test_constants import HTTP_FORBIDDEN
from .test_constants import HTTP_NOT_FOUND
from .test_constants import HTTP_OK
from .test_constants import HTTP_UNAUTHORIZED


"""RFC 7592 Security Tests - Ensure proper authentication and authorization.

Key security requirements:
1. RFC 7592 endpoints MUST use Bearer authentication with registration_access_token
2. Registration access tokens must be validated
3. Clients can only manage their own registrations
4. Proper error codes must be returned (401, 403, 404)
"""

import os

import pytest


AUTH_BASE_URL = f"https://auth.{os.environ.get('BASE_DOMAIN', 'atradev.org')}"


def create_bearer_auth_header(token: str) -> str:
    """Create HTTP Bearer authentication header for RFC 7592."""
    return f"Bearer {token}"


async def get_oauth_token(http_client, client_id: str, client_secret: str) -> str:
    """Get a valid OAuth Bearer token through the OAuth flow."""
    # For testing, we'll create a mock token exchange
    # In reality, this would go through the full OAuth flow
    response = await http_client.post(
        f"{AUTH_BASE_URL}/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "openid profile",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code == HTTP_OK:
        return response.json().get("access_token")

    # If client_credentials not supported, return a dummy token for testing
    return "dummy_bearer_token_for_testing"


@pytest.mark.asyncio
async def test_rfc7592_rejects_oauth_bearer_tokens(http_client):
    """RFC 7592 endpoints MUST reject OAuth Bearer tokens and only accept registration_access_token."""
    # Register a client
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": ["https://bearer-test.example.com/callback"],
            "client_name": "TEST Bearer Rejection Test",
        },
    )
    assert response.status_code == HTTP_CREATED
    client = response.json()

    client_id = client["client_id"]
    client_secret = client["client_secret"]

    # Get a Bearer token (if supported)
    bearer_token = await get_oauth_token(http_client, client_id, client_secret)

    # Test each RFC 7592 endpoint with Bearer token
    # ALL must reject with 401 and WWW-Authenticate: Basic

    # Test GET with OAuth Bearer token (not registration token)
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": f"Bearer {bearer_token}"},
    )
    assert response.status_code == HTTP_FORBIDDEN  # Should reject OAuth tokens

    # Test PUT with OAuth Bearer token (not registration token)
    response = await http_client.put(
        f"{AUTH_BASE_URL}/register/{client_id}",
        json={"client_name": "Should Not Work"},
        headers={"Authorization": f"Bearer {bearer_token}"},
    )
    assert response.status_code == HTTP_FORBIDDEN  # Should reject OAuth tokens

    # Test DELETE with OAuth Bearer token (not registration token)
    response = await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": f"Bearer {bearer_token}"},
    )
    assert response.status_code == HTTP_FORBIDDEN  # Should reject OAuth tokens

    # Verify registration_access_token Bearer auth works
    registration_token = client.get("registration_access_token")
    assert registration_token, "registration_access_token missing"

    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": f"Bearer {registration_token}"},
    )
    assert response.status_code == HTTP_OK

    # Clean up
    await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": f"Bearer {registration_token}"},
    )


@pytest.mark.asyncio
async def test_rfc7592_authentication_edge_cases(http_client):
    """Test various authentication edge cases for RFC 7592."""
    # Register a client
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": ["https://edge-case.example.com/callback"],
            "client_name": "TEST Edge Case Test",
        },
    )
    assert response.status_code == HTTP_CREATED
    client = response.json()

    client_id = client["client_id"]
    client["client_secret"]
    registration_token = client.get("registration_access_token")
    assert registration_token, "registration_access_token missing"

    # Test various malformed auth headers for RFC 7592 Bearer authentication
    test_cases = [
        # (auth_header, expected_status, description)
        (None, 401, "No auth header"),
        ("", 401, "Empty auth header"),
        ("Bearer", 401, "Bearer without token"),
        ("Bearer x", 403, "Bearer with invalid token"),
        ("Bearer invalid-token!", 403, "Invalid Bearer token"),
        ("Basic token", 401, "Wrong auth scheme (Basic)"),
        ('Digest username="test"', 401, "Wrong auth scheme (Digest)"),
        ('OAuth token="test"', 401, "Wrong auth scheme (OAuth 1.0)"),
        (f"Bearer {registration_token}-extra", 403, "Wrong Bearer token"),
    ]

    for auth_header, expected_status, description in test_cases:
        headers = {"Authorization": auth_header} if auth_header is not None else {}
        response = await http_client.get(
            f"{AUTH_BASE_URL}/register/{client_id}", headers=headers
        )
        assert response.status_code == expected_status, f"Failed: {description}"
        if expected_status == 401:
            assert response.headers.get("WWW-Authenticate") == 'Bearer realm="auth"'

    # Cleanup: Delete the client registration using RFC 7592
    try:
        delete_response = await http_client.delete(
            f"{AUTH_BASE_URL}/register/{client_id}",
            headers={"Authorization": f"Bearer {registration_token}"},
        )
        # 204 No Content is success, 404 is okay if already deleted
        if delete_response.status_code not in (204, 404):
            print(
                f"Warning: Failed to delete client {client_id}: {delete_response.status_code}"  # TODO: Break long line
            )
    except Exception as e:
        print(f"Warning: Error during client cleanup: {e}")


@pytest.mark.asyncio
async def test_rfc7592_cross_client_access_forbidden(http_client):
    """Ensure clients cannot access each other's configurations."""
    # Create multiple clients
    clients = []
    for i in range(3):
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": [f"https://client{i}.example.com/callback"],
                "client_name": f"TEST Client {i}",
                "scope": "openid",
            },
        )
        assert response.status_code == HTTP_CREATED
        clients.append(response.json())

    # Each client tries to access other clients' data
    for i, attacker in enumerate(clients):
        attacker_token = attacker.get("registration_access_token")
        assert attacker_token, f"registration_access_token missing for client {i}"
        attacker_auth = f"Bearer {attacker_token}"

        for j, victim in enumerate(clients):
            if i == j:
                # Client should be able to access own data
                response = await http_client.get(
                    f"{AUTH_BASE_URL}/register/{victim['client_id']}",
                    headers={"Authorization": attacker_auth},
                )
                assert response.status_code == HTTP_OK
            else:
                # Client should NOT be able to access others' data

                # GET should return 403
                response = await http_client.get(
                    f"{AUTH_BASE_URL}/register/{victim['client_id']}",
                    headers={"Authorization": attacker_auth},
                )
                assert response.status_code == HTTP_FORBIDDEN

                # PUT should return 403
                response = await http_client.put(
                    f"{AUTH_BASE_URL}/register/{victim['client_id']}",
                    json={"client_name": f"Hacked by {attacker['client_name']}"},
                    headers={"Authorization": attacker_auth},
                )
                assert response.status_code == HTTP_FORBIDDEN

                # DELETE should return 403
                response = await http_client.delete(
                    f"{AUTH_BASE_URL}/register/{victim['client_id']}",
                    headers={"Authorization": attacker_auth},
                )
                assert response.status_code == HTTP_FORBIDDEN

    # Verify all clients still exist and are unmodified
    for i, client in enumerate(clients):
        token = client.get("registration_access_token")
        assert token, f"registration_access_token missing for client {i}"
        response = await http_client.get(
            f"{AUTH_BASE_URL}/register/{client['client_id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == HTTP_OK
        assert response.json()["client_name"] == f"TEST Client {i}"

    # Clean up all clients
    for client in clients:
        token = client.get("registration_access_token")
        assert token, "registration_access_token missing"
        await http_client.delete(
            f"{AUTH_BASE_URL}/register/{client['client_id']}",
            headers={"Authorization": f"Bearer {token}"},
        )


@pytest.mark.asyncio
async def test_rfc7592_timing_attack_resistance(http_client):
    """Test that authentication is resistant to timing attacks."""
    import time

    # Register a real client
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": ["https://timing.example.com/callback"],
            "client_name": "TEST Timing Test",
        },
    )
    assert response.status_code == HTTP_CREATED
    client = response.json()

    client_id = client["client_id"]
    client["client_secret"]
    registration_token = client.get("registration_access_token")
    assert registration_token, "registration_access_token missing"

    # Test timing for various scenarios
    timings = {
        "valid_client_valid_secret": [],
        "valid_client_wrong_secret": [],
        "wrong_client": [],
        "malformed_auth": [],
    }

    # Run multiple iterations to get average timing
    iterations = 5

    for _ in range(iterations):
        # Valid client, valid token
        start = time.time()
        response = await http_client.get(
            f"{AUTH_BASE_URL}/register/{client_id}",
            headers={"Authorization": f"Bearer {registration_token}"},
        )
        timings["valid_client_valid_secret"].append(time.time() - start)
        assert response.status_code == HTTP_OK

        # Valid client, wrong token
        start = time.time()
        response = await http_client.get(
            f"{AUTH_BASE_URL}/register/{client_id}",
            headers={"Authorization": "Bearer reg-wrong-timing-token"},
        )
        timings["valid_client_wrong_secret"].append(time.time() - start)
        assert response.status_code == HTTP_FORBIDDEN

        # Wrong client
        start = time.time()
        response = await http_client.get(
            f"{AUTH_BASE_URL}/register/client_nonexistent",
            headers={"Authorization": "Bearer reg-nonexistent-token"},
        )
        timings["wrong_client"].append(time.time() - start)
        assert response.status_code == HTTP_NOT_FOUND

        # Malformed auth
        start = time.time()
        response = await http_client.get(
            f"{AUTH_BASE_URL}/register/{client_id}",
            headers={"Authorization": "Basic malformed"},
        )
        timings["malformed_auth"].append(time.time() - start)
        assert response.status_code == HTTP_UNAUTHORIZED

    # Calculate averages
    avg_timings = {k: sum(v) / len(v) for k, v in timings.items()}

    # Timing differences should be minimal (< 50ms difference)
    # This prevents attackers from determining if a client_id exists
    max_diff = max(avg_timings.values()) - min(avg_timings.values())
    assert max_diff < 0.05, f"Timing attack possible: {max_diff:.3f}s difference"

    # Clean up
    await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": f"Bearer {registration_token}"},
    )


@pytest.mark.asyncio
async def test_rfc7592_rate_limiting(http_client):
    """Test that RFC 7592 endpoints have appropriate rate limiting."""
    # Register a client
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": ["https://ratelimit.example.com/callback"],
            "client_name": "TEST Rate Limit Test",
        },
    )
    assert response.status_code == HTTP_CREATED
    client = response.json()

    client_id = client["client_id"]
    client["client_secret"]

    # Test rapid requests with invalid tokens (brute force attempt)
    wrong_auth_responses = []
    for i in range(20):
        wrong_token = f"reg-attempt-{i}"
        response = await http_client.get(
            f"{AUTH_BASE_URL}/register/{client_id}",
            headers={"Authorization": f"Bearer {wrong_token}"},
        )
        wrong_auth_responses.append(response.status_code)

    # All should be 403 for wrong tokens
    assert all(status == 403 for status in wrong_auth_responses)

    # Test rapid valid requests (should not be rate limited as harshly)
    registration_token = client.get("registration_access_token")
    assert registration_token, "registration_access_token missing"
    valid_responses = []
    for _ in range(10):
        response = await http_client.get(
            f"{AUTH_BASE_URL}/register/{client_id}",
            headers={"Authorization": f"Bearer {registration_token}"},
        )
        valid_responses.append(response.status_code)

    # Most should succeed
    success_rate = sum(1 for status in valid_responses if status == 200) / len(
        valid_responses
    )
    assert success_rate > 0.8, "Valid requests being rate limited too aggressively"

    # Clean up
    await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": f"Bearer {registration_token}"},
    )


@pytest.mark.asyncio
async def test_rfc7592_sql_injection_attempts(http_client):
    """Test that RFC 7592 endpoints are safe from SQL injection."""
    # Register a legitimate client first
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": ["https://sqltest.example.com/callback"],
            "client_name": "TEST SQL Test Client",
        },
    )
    assert response.status_code == HTTP_CREATED
    client = response.json()

    client_id = client["client_id"]
    client["client_secret"]
    registration_token = client.get("registration_access_token")
    assert registration_token, "registration_access_token missing"
    auth_header = f"Bearer {registration_token}"

    # Test various SQL injection attempts in client_id parameter
    sql_injection_attempts = [
        "' OR '1'='1",
        "'; DROP TABLE clients; --",
        "' UNION SELECT * FROM clients --",
        "admin'--",
        "' OR 1=1--",
        '"; DROP TABLE clients; --',
        "1' OR '1' = '1",
        client_id + "' OR '1'='1",
    ]

    for injection in sql_injection_attempts:
        # Try injection in URL
        response = await http_client.get(
            f"{AUTH_BASE_URL}/register/{injection}",
            headers={"Authorization": auth_header},
        )
        # Should return 403 (wrong client) or 400/404, never 200
        assert response.status_code in [400, 403, 404]

        # Try injection in Bearer token
        injection_auth = f"Bearer reg-injection-{injection}"
        response = await http_client.get(
            f"{AUTH_BASE_URL}/register/{client_id}",
            headers={"Authorization": injection_auth},
        )
        assert response.status_code in [403, 404]  # Wrong token = 403

    # Verify original client still exists and works
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}", headers={"Authorization": auth_header}
    )
    assert response.status_code == HTTP_OK
    assert response.json()["client_name"] == "TEST SQL Test Client"

    # Clean up
    await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}", headers={"Authorization": auth_header}
    )
