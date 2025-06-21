"""
Comprehensive RFC 7592 (OAuth 2.0 Dynamic Client Registration Management Protocol) compliance tests.

Tests all three endpoints with proper security validation:
- GET /register/{client_id} - Read client configuration
- PUT /register/{client_id} - Update client configuration  
- DELETE /register/{client_id} - Delete client registration

Security requirements per RFC 7592:
- All endpoints MUST use Bearer authentication with registration_access_token
- 401 Unauthorized for missing authentication
- 403 Forbidden for invalid tokens or insufficient permissions
- 404 Not Found for non-existent clients
"""
import pytest
import httpx
import os
import base64
import json
import time

AUTH_BASE_URL = f"https://auth.{os.environ.get('BASE_DOMAIN', 'atradev.org')}"

def create_bearer_auth_header(token: str) -> str:
    """Create HTTP Bearer authentication header for RFC 7592"""
    return f"Bearer {token}"


@pytest.mark.asyncio
async def test_rfc7592_get_client_configuration(http_client):
    """Test RFC 7592 GET /register/{client_id} endpoint"""
    
    # First register a client
    registration_data = {
        "redirect_uris": ["https://test.example.com/callback"],
        "client_name": "TEST RFC 7592 GET Test Client",
        "scope": "openid profile email",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"]
    }
    
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json=registration_data
    )
    assert response.status_code == 201
    client = response.json()
    
    client_id = client['client_id']
    client_secret = client['client_secret']
    
    # Test 1: Valid GET with proper authentication
    registration_token = client.get('registration_access_token')
    assert registration_token, "registration_access_token missing from registration response"
    auth_header = create_bearer_auth_header(registration_token)
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": auth_header}
    )
    
    assert response.status_code == 200
    config = response.json()
    
    # Verify all registered metadata is returned
    assert config['client_id'] == client_id
    assert config['client_secret'] == client_secret
    assert config['redirect_uris'] == registration_data['redirect_uris']
    assert config['client_name'] == registration_data['client_name']
    assert config['scope'] == registration_data['scope']
    assert 'client_id_issued_at' in config
    assert 'client_secret_expires_at' in config
    
    # Test 2: GET without authentication - MUST return 401
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}"
    )
    assert response.status_code == 401
    assert response.headers.get('WWW-Authenticate') == 'Bearer realm="auth"'
    
    # Test 3: GET with wrong token - MUST return 403
    wrong_auth = create_bearer_auth_header("reg-wrong-token")
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": wrong_auth}
    )
    assert response.status_code == 403
    
    # Test 4: GET with wrong client_id in URL - MUST return 404 (client not found)
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/client_wrong_id",
        headers={"Authorization": auth_header}
    )
    assert response.status_code == 404  # Client doesn't exist
    
    # Test 5: GET non-existent client - MUST return 404
    fake_auth = create_bearer_auth_header("reg-fake-token")
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/client_fake",
        headers={"Authorization": fake_auth}
    )
    assert response.status_code == 404
    
    # Clean up
    await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": auth_header}
    )


@pytest.mark.asyncio
async def test_rfc7592_put_update_client(http_client):
    """Test RFC 7592 PUT /register/{client_id} endpoint"""
    
    # Register initial client
    initial_data = {
        "redirect_uris": ["https://original.example.com/callback"],
        "client_name": "TEST Original Name",
        "scope": "openid",
        "grant_types": ["authorization_code"]
    }
    
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json=initial_data
    )
    assert response.status_code == 201
    client = response.json()
    
    client_id = client['client_id']
    client_secret = client['client_secret']
    registration_token = client.get('registration_access_token')
    assert registration_token, "registration_access_token missing from registration response"
    auth_header = create_bearer_auth_header(registration_token)
    
    # Test 1: Valid update with authentication
    update_data = {
        "redirect_uris": [
            "https://updated.example.com/callback",
            "https://secondary.example.com/callback"
        ],
        "client_name": "TEST Updated Name via RFC 7592",
        "scope": "openid profile email",
        "grant_types": ["authorization_code", "refresh_token"],
        "contacts": ["admin@example.com"],
        "logo_uri": "https://example.com/logo.png",
        "policy_uri": "https://example.com/policy"
    }
    
    response = await http_client.put(
        f"{AUTH_BASE_URL}/register/{client_id}",
        json=update_data,
        headers={"Authorization": auth_header}
    )
    
    assert response.status_code == 200
    updated = response.json()
    
    # Verify updates were applied
    assert updated['redirect_uris'] == update_data['redirect_uris']
    assert updated['client_name'] == update_data['client_name']
    assert updated['scope'] == update_data['scope']
    assert updated['grant_types'] == update_data['grant_types']
    
    # Verify immutable fields remain unchanged
    assert updated['client_id'] == client_id
    assert updated['client_secret'] == client_secret
    assert updated['client_id_issued_at'] == client['client_id_issued_at']
    
    # Test 2: PUT without authentication - MUST return 401
    response = await http_client.put(
        f"{AUTH_BASE_URL}/register/{client_id}",
        json={"client_name": "Unauthorized Update"}
    )
    assert response.status_code == 401
    assert response.headers.get('WWW-Authenticate') == 'Bearer realm="auth"'
    
    # Test 3: PUT with wrong token - MUST return 403
    wrong_token = "reg-wrong-token-update"
    wrong_auth = create_bearer_auth_header(wrong_token)
    response = await http_client.put(
        f"{AUTH_BASE_URL}/register/{client_id}",
        json={"client_name": "Wrong Auth Update"},
        headers={"Authorization": wrong_auth}
    )
    assert response.status_code == 403
    
    # Test 4: PUT to wrong client_id - MUST return 404 (client not found)
    response = await http_client.put(
        f"{AUTH_BASE_URL}/register/client_different",
        json={"client_name": "Cross-client Update"},
        headers={"Authorization": auth_header}
    )
    assert response.status_code == 404
    
    # Test 5: PUT with invalid metadata - MUST return 400
    response = await http_client.put(
        f"{AUTH_BASE_URL}/register/{client_id}",
        json={"redirect_uris": []},  # Empty redirect_uris not allowed
        headers={"Authorization": auth_header}
    )
    assert response.status_code == 400
    
    # Test 6: Verify updates persist
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": auth_header}
    )
    assert response.status_code == 200
    persisted = response.json()
    assert persisted['client_name'] == "TEST Updated Name via RFC 7592"
    
    # Clean up
    await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": auth_header}
    )


@pytest.mark.asyncio
async def test_rfc7592_delete_client(http_client):
    """Test RFC 7592 DELETE /register/{client_id} endpoint"""
    
    # Register a client to delete
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": ["https://delete.example.com/callback"],
            "client_name": "TEST Client to Delete"
        }
    )
    assert response.status_code == 201
    client = response.json()
    
    client_id = client['client_id']
    client_secret = client['client_secret']
    registration_token = client.get('registration_access_token')
    assert registration_token, "registration_access_token missing from registration response"
    auth_header = create_bearer_auth_header(registration_token)
    
    # Test 1: DELETE without authentication - MUST return 401
    response = await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}"
    )
    assert response.status_code == 401
    assert response.headers.get('WWW-Authenticate') == 'Bearer realm="auth"'
    
    # Test 2: DELETE with wrong token - MUST return 403
    wrong_token = "reg-wrong-token-delete"
    wrong_auth = create_bearer_auth_header(wrong_token)
    response = await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": wrong_auth}
    )
    assert response.status_code == 403
    
    # Test 3: Valid DELETE with authentication
    response = await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": auth_header}
    )
    assert response.status_code == 204
    assert not response.content  # No content on 204
    
    # Test 4: Verify client is deleted - GET should return 404
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": auth_header}
    )
    assert response.status_code == 404
    
    # Test 5: DELETE already deleted client - MUST return 404
    response = await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": auth_header}
    )
    assert response.status_code == 404
    
    # Test 6: DELETE non-existent client - MUST return 404
    fake_token = "reg-fake-token-nonexistent"
    fake_auth = create_bearer_auth_header(fake_token)
    response = await http_client.delete(
        f"{AUTH_BASE_URL}/register/client_nonexistent",
        headers={"Authorization": fake_auth}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_rfc7592_requires_correct_bearer_token(http_client):
    """Test that RFC 7592 endpoints require the correct registration_access_token"""
    
    # Register a client
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": ["https://bearer.example.com/callback"],
            "client_name": "TEST Bearer Token Test"
        }
    )
    assert response.status_code == 201
    client = response.json()
    
    client_id = client['client_id']
    client_secret = client['client_secret']
    
    # Get the valid registration access token
    registration_token = client.get('registration_access_token')
    assert registration_token, "registration_access_token missing"
    
    # Test with WRONG Bearer token (e.g., an OAuth access token)
    wrong_bearer_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test"
    
    # Test all RFC 7592 endpoints with wrong Bearer token - all MUST return 403
    endpoints = [
        ("GET", f"/register/{client_id}"),
        ("PUT", f"/register/{client_id}"),
        ("DELETE", f"/register/{client_id}")
    ]
    
    for method, path in endpoints:
        if method == "GET":
            response = await http_client.get(
                f"{AUTH_BASE_URL}{path}",
                headers={"Authorization": f"Bearer {wrong_bearer_token}"}
            )
        elif method == "PUT":
            response = await http_client.put(
                f"{AUTH_BASE_URL}{path}",
                json={"client_name": "Updated"},
                headers={"Authorization": f"Bearer {wrong_bearer_token}"}
            )
        else:  # DELETE
            response = await http_client.delete(
                f"{AUTH_BASE_URL}{path}",
                headers={"Authorization": f"Bearer {wrong_bearer_token}"}
            )
        
        assert response.status_code == 403, f"{method} {path} should reject wrong Bearer tokens"
    
    # Test with NO auth header - should return 401
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}"
    )
    assert response.status_code == 401
    assert response.headers.get('WWW-Authenticate') == 'Bearer realm="auth"'
    
    # Test with Basic auth - should return 401 (wrong auth method)
    import base64
    basic_auth = f"Basic {base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()}"
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": basic_auth}
    )
    assert response.status_code == 401
    assert response.headers.get('WWW-Authenticate') == 'Bearer realm="auth"'
    
    # Clean up with correct token
    auth_header = create_bearer_auth_header(registration_token)
    await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": auth_header}
    )


@pytest.mark.asyncio
async def test_rfc7592_client_isolation(http_client):
    """Test that clients cannot access or modify other clients' registrations"""
    
    # Register two different clients
    response1 = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": ["https://client1.example.com/callback"],
            "client_name": "TEST Client 1"
        }
    )
    assert response1.status_code == 201
    client1 = response1.json()
    
    response2 = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": ["https://client2.example.com/callback"],
            "client_name": "TEST Client 2"
        }
    )
    assert response2.status_code == 201
    client2 = response2.json()
    
    # Create auth headers for both clients using their registration tokens
    token1 = client1.get('registration_access_token')
    token2 = client2.get('registration_access_token')
    assert token1 and token2, "Missing registration_access_token"
    
    auth1 = create_bearer_auth_header(token1)
    auth2 = create_bearer_auth_header(token2)
    
    # Test 1: Client 1 cannot GET Client 2's configuration
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client2['client_id']}",
        headers={"Authorization": auth1}
    )
    assert response.status_code == 403
    
    # Test 2: Client 1 cannot UPDATE Client 2's configuration
    response = await http_client.put(
        f"{AUTH_BASE_URL}/register/{client2['client_id']}",
        json={"client_name": "Hacked by Client 1"},
        headers={"Authorization": auth1}
    )
    assert response.status_code == 403
    
    # Test 3: Client 1 cannot DELETE Client 2
    response = await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client2['client_id']}",
        headers={"Authorization": auth1}
    )
    assert response.status_code == 403
    
    # Test 4: Verify Client 2 is unaffected
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client2['client_id']}",
        headers={"Authorization": auth2}
    )
    assert response.status_code == 200
    assert response.json()['client_name'] == "TEST Client 2"
    
    # Clean up both clients
    await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client1['client_id']}",
        headers={"Authorization": auth1}
    )
    await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client2['client_id']}",
        headers={"Authorization": auth2}
    )


@pytest.mark.asyncio
async def test_rfc7592_malformed_requests(http_client):
    """Test RFC 7592 endpoints handle malformed requests properly"""
    
    # Register a client
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": ["https://malformed.example.com/callback"],
            "client_name": "TEST Malformed Test Client"
        }
    )
    assert response.status_code == 201
    client = response.json()
    
    client_id = client['client_id']
    client_secret = client['client_secret']
    registration_token = client.get('registration_access_token')
    assert registration_token, "registration_access_token missing from registration response"
    auth_header = create_bearer_auth_header(registration_token)
    
    # Test 1: Malformed Bearer auth headers
    malformed_auth_tests = [
        "Bearer",  # No token
        "Bearer x",  # Single character token (invalid format)
        "Basic " + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode(),  # Wrong scheme (Basic instead of Bearer)
        "Bearer  double-space",  # Extra space
        "BEARER " + registration_token,  # Wrong case (should still work per spec)
    ]
    
    for bad_auth in malformed_auth_tests:
        response = await http_client.get(
            f"{AUTH_BASE_URL}/register/{client_id}",
            headers={"Authorization": bad_auth}
        )
        # Different malformed headers can return either 401 or 403
        # 401 = malformed/missing auth, 403 = valid format but wrong token
        if bad_auth in ["Bearer x", "Bearer  double-space", "BEARER " + registration_token]:
            assert response.status_code in [401, 403]  # Either is acceptable
        else:
            assert response.status_code == 401, f"Expected 401 for auth header: {bad_auth!r}, got {response.status_code}"
    
    # Test 2: Invalid JSON in PUT request
    response = await http_client.put(
        f"{AUTH_BASE_URL}/register/{client_id}",
        content="not json",
        headers={
            "Authorization": auth_header,
            "Content-Type": "application/json"
        }
    )
    assert response.status_code == 422  # Unprocessable Entity
    
    # Test 3: Invalid client_id format in URL
    invalid_client_ids = [
        "../etc/passwd",  # Path traversal attempt
        "client_%20space",  # URL encoded space
        "client_<script>",  # XSS attempt
        # Empty client_id creates /register/ which may redirect
    ]
    
    for bad_id in invalid_client_ids:
        response = await http_client.get(
            f"{AUTH_BASE_URL}/register/{bad_id}",
            headers={"Authorization": auth_header}
        )
        assert response.status_code in [400, 403, 404]
    
    # Clean up
    await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": auth_header}
    )


@pytest.mark.asyncio
async def test_rfc7592_concurrent_updates(http_client):
    """Test RFC 7592 handles concurrent update requests properly"""
    
    # Register a client
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": ["https://concurrent.example.com/callback"],
            "client_name": "TEST Concurrent Test",
            "scope": "openid"
        }
    )
    assert response.status_code == 201
    client = response.json()
    
    client_id = client['client_id']
    client_secret = client['client_secret']
    registration_token = client.get('registration_access_token')
    assert registration_token, "registration_access_token missing from registration response"
    auth_header = create_bearer_auth_header(registration_token)
    
    # Make multiple concurrent update requests
    import asyncio
    
    async def update_client(name_suffix: int):
        return await http_client.put(
            f"{AUTH_BASE_URL}/register/{client_id}",
            json={
                "redirect_uris": ["https://concurrent.example.com/callback"],
                "client_name": f"Concurrent Update {name_suffix}",
                "scope": "openid profile"
            },
            headers={"Authorization": auth_header}
        )
    
    # Launch 5 concurrent updates
    tasks = [update_client(i) for i in range(5)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # All requests should succeed (last write wins)
    success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
    assert success_count == 5
    
    # Verify final state is consistent
    response = await http_client.get(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": auth_header}
    )
    assert response.status_code == 200
    final_state = response.json()
    assert final_state['client_id'] == client_id
    assert final_state['scope'] == "openid profile"
    assert "Concurrent Update" in final_state['client_name']
    
    # Clean up
    await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": auth_header}
    )


@pytest.mark.asyncio
async def test_rfc7592_client_lifetime_handling(http_client):
    """Test RFC 7592 respects CLIENT_LIFETIME configuration"""
    
    client_lifetime = int(os.environ.get('CLIENT_LIFETIME', '7776000'))
    
    # Register a client
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json={
            "redirect_uris": ["https://lifetime.example.com/callback"],
            "client_name": "TEST Lifetime Test Client"
        }
    )
    assert response.status_code == 201
    client = response.json()
    
    client_id = client['client_id']
    client_secret = client['client_secret']
    registration_token = client.get('registration_access_token')
    assert registration_token, "registration_access_token missing from registration response"
    auth_header = create_bearer_auth_header(registration_token)
    
    # Check expiration handling
    if client_lifetime == 0:
        # Eternal client
        assert client['client_secret_expires_at'] == 0
    else:
        # Expiring client
        expected_expiry = client['client_id_issued_at'] + client_lifetime
        assert abs(client['client_secret_expires_at'] - expected_expiry) <= 5
    
    # Update should maintain expiration settings
    response = await http_client.put(
        f"{AUTH_BASE_URL}/register/{client_id}",
        json={
            "redirect_uris": ["https://updated-lifetime.example.com/callback"],
            "client_name": "Updated Lifetime Test"
        },
        headers={"Authorization": auth_header}
    )
    assert response.status_code == 200
    updated = response.json()
    
    # Expiration should not change on update
    assert updated['client_secret_expires_at'] == client['client_secret_expires_at']
    assert updated['client_id_issued_at'] == client['client_id_issued_at']
    
    # Clean up
    await http_client.delete(
        f"{AUTH_BASE_URL}/register/{client_id}",
        headers={"Authorization": auth_header}
    )