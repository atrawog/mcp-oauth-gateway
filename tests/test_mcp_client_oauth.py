"""Sacred Tests for mcp-streamablehttp-client OAuth functionality
Following CLAUDE.md Commandment 1: NO MOCKING! Test against real deployed services only!

These tests verify the OAuth client functionality that MCP clients use to authenticate.
All tests use REAL auth service, REAL OAuth flows, and REAL tokens.
"""

import json
import os
import secrets
import time

import httpx
import pytest

from .test_constants import AUTH_BASE_URL
from .test_constants import GATEWAY_OAUTH_ACCESS_TOKEN
from .test_constants import HTTP_BAD_REQUEST
from .test_constants import HTTP_CREATED
from .test_constants import HTTP_OK
from .test_constants import HTTP_UNAUTHORIZED
from .test_constants import MCP_PROTOCOL_VERSION
from .test_constants import MCP_TESTING_URL


# MCP Client tokens from environment
MCP_CLIENT_ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN")
MCP_CLIENT_ID = os.getenv("MCP_CLIENT_ID")
MCP_CLIENT_SECRET = os.getenv("MCP_CLIENT_SECRET")


class TestMCPClientOAuthRegistration:
    """Test OAuth client registration flows used by MCP clients."""

    @pytest.mark.asyncio
    async def test_dynamic_client_registration(self, http_client: httpx.AsyncClient, _wait_for_services):
        """Test that MCP clients can register dynamically per RFC 7591."""
        # Create unique client for this test
        client_name = "TEST test_dynamic_client_registration"

        registration_data = {
            "redirect_uris": ["http://localhost:8080/callback"],  # Local callback for CLI tools
            "client_name": client_name,
            "scope": "read write",
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
        }

        # Register without authentication (public endpoint)
        response = await http_client.post(f"{AUTH_BASE_URL}/register", json=registration_data, timeout=30.0)

        assert response.status_code == HTTP_CREATED
        client_data = response.json()

        # Verify registration response
        assert "client_id" in client_data
        assert "client_secret" in client_data
        # Check client_secret_expires_at matches CLIENT_LIFETIME from .env
        client_lifetime = int(os.environ.get("CLIENT_LIFETIME", "7776000"))
        if client_lifetime == 0:
            assert client_data["client_secret_expires_at"] == 0  # Never expires
        else:
            # Should be created_at + CLIENT_LIFETIME
            created_at = client_data.get("client_id_issued_at")
            expected_expiry = created_at + client_lifetime
            assert abs(client_data["client_secret_expires_at"] - expected_expiry) <= 5
        assert client_data["client_name"] == client_name

        print("✅ Dynamic client registration successful")
        print(f"   Client ID: {client_data['client_id']}")

        # Cleanup: Delete the client registration using RFC 7592
        if "registration_access_token" in client_data and "client_id" in client_data:
            try:
                delete_response = await http_client.delete(
                    f"{AUTH_BASE_URL}/register/{client_data['client_id']}",
                    headers={
                        "Authorization": f"Bearer {client_data['registration_access_token']}"  # TODO: Break long line
                    },
                    timeout=30.0,
                )
                # 204 No Content is success, 404 is okay if already deleted
                if delete_response.status_code not in (204, 404):
                    print(
                        f"Warning: Failed to delete client {client_data['client_id']}: {delete_response.status_code}"  # TODO: Break long line
                    )
            except Exception as e:
                print(f"Warning: Error during client cleanup: {e}")

        return client_data

    @pytest.mark.asyncio
    async def test_client_registration_with_auth_token(self, http_client: httpx.AsyncClient, _wait_for_services):
        """Test client registration with bearer token (authenticated registration)."""
        assert GATEWAY_OAUTH_ACCESS_TOKEN, "Need OAuth token for authenticated registration"

        client_name = "TEST test_client_registration_with_auth_token"

        registration_data = {
            "redirect_uris": ["http://localhost:3000/callback"],
            "client_name": client_name,
            "scope": "openid profile email",
        }

        # Register with authentication
        response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data,
            headers={
                "Authorization": f"Bearer {GATEWAY_OAUTH_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            timeout=30.0,
        )

        assert response.status_code == HTTP_CREATED
        client_data = response.json()

        assert client_data["client_name"] == client_name
        print("✅ Authenticated client registration successful")

        # Cleanup: Delete the client registration using RFC 7592
        if "registration_access_token" in client_data and "client_id" in client_data:
            try:
                delete_response = await http_client.delete(
                    f"{AUTH_BASE_URL}/register/{client_data['client_id']}",
                    headers={
                        "Authorization": f"Bearer {client_data['registration_access_token']}"  # TODO: Break long line
                    },
                    timeout=30.0,
                )
                # 204 No Content is success, 404 is okay if already deleted
                if delete_response.status_code not in (204, 404):
                    print(
                        f"Warning: Failed to delete client {client_data['client_id']}: {delete_response.status_code}"  # TODO: Break long line
                    )
            except Exception as e:
                print(f"Warning: Error during client cleanup: {e}")

        return client_data


class TestMCPClientOAuthFlows:
    """Test OAuth flows that MCP clients use."""

    @pytest.mark.asyncio
    async def test_authorization_code_flow_initiation(self, http_client: httpx.AsyncClient, _wait_for_services):
        """Test starting the authorization code flow."""
        # First register a client
        client_name = "TEST test_authorization_code_flow_initiation"

        registration_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": ["http://localhost:8080/callback"],
                "client_name": client_name,
            },
            timeout=30.0,
        )

        assert registration_response.status_code == HTTP_CREATED
        client = registration_response.json()

        # Start authorization flow
        auth_params = {
            "response_type": "code",
            "client_id": client["client_id"],
            "redirect_uri": "http://localhost:8080/callback",
            "scope": "read write",
            "state": secrets.token_urlsafe(16),
        }

        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize", params=auth_params, follow_redirects=False, timeout=30.0
        )

        # Should redirect to GitHub for authentication
        assert response.status_code == 307
        location = response.headers["location"]
        assert "github.com/login/oauth/authorize" in location

        print("✅ Authorization flow initiated successfully")
        print(f"   Redirecting to: {location.split('?')[0]}")

        # Cleanup: Delete the client registration using RFC 7592
        if "registration_access_token" in client and "client_id" in client:
            try:
                delete_response = await http_client.delete(
                    f"{AUTH_BASE_URL}/register/{client['client_id']}",
                    headers={
                        "Authorization": f"Bearer {client['registration_access_token']}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                    },
                    timeout=30.0,
                )
                # 204 No Content is success, 404 is okay if already deleted
                if delete_response.status_code not in (204, 404):
                    print(
                        f"Warning: Failed to delete client {client['client_id']}: {delete_response.status_code}"  # TODO: Break long line
                    )
            except Exception as e:
                print(f"Warning: Error during client cleanup: {e}")

    @pytest.mark.asyncio
    async def test_pkce_flow_for_cli_clients(self, http_client: httpx.AsyncClient, _wait_for_services):
        """Test PKCE flow commonly used by CLI MCP clients."""
        # Register a public client (no secret needed for PKCE)
        registration_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": ["http://localhost:8080/callback"],
                "client_name": "TEST test_pkce_flow_for_cli_clients",
                "token_endpoint_auth_method": "none",  # Public client
            },
            timeout=30.0,
        )

        assert registration_response.status_code == HTTP_CREATED
        client = registration_response.json()

        # Generate PKCE challenge
        import base64
        import hashlib

        verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")
        challenge_bytes = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(challenge_bytes).decode("utf-8").rstrip("=")

        # Start PKCE flow
        auth_params = {
            "response_type": "code",
            "client_id": client["client_id"],
            "redirect_uri": "http://localhost:8080/callback",
            "state": secrets.token_urlsafe(16),
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }

        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize", params=auth_params, follow_redirects=False, timeout=30.0
        )

        assert response.status_code == 307
        print("✅ PKCE flow initiated successfully")

        # Cleanup: Delete the client registration using RFC 7592
        if "registration_access_token" in client and "client_id" in client:
            try:
                delete_response = await http_client.delete(
                    f"{AUTH_BASE_URL}/register/{client['client_id']}",
                    headers={
                        "Authorization": f"Bearer {client['registration_access_token']}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                    },
                    timeout=30.0,
                )
                # 204 No Content is success, 404 is okay if already deleted
                if delete_response.status_code not in (204, 404):
                    print(
                        f"Warning: Failed to delete client {client['client_id']}: {delete_response.status_code}"  # TODO: Break long line
                    )
            except Exception as e:
                print(f"Warning: Error during client cleanup: {e}")

    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, http_client: httpx.AsyncClient, _wait_for_services):
        """Test token refresh flow used by long-running MCP clients."""
        # This test would need a valid refresh token from a completed OAuth flow
        # For now, test the endpoint exists and returns proper errors

        # Register a client first
        registration_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": ["http://localhost:8080/callback"],
                "client_name": "TEST test_token_refresh_flow",
            },
            timeout=30.0,
        )

        assert registration_response.status_code == HTTP_CREATED
        client = registration_response.json()

        # Try to use refresh token grant (will fail without valid refresh token)
        response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": "invalid_refresh_token",
                "client_id": client["client_id"],
                "client_secret": client["client_secret"],
            },
            timeout=30.0,
        )

        assert response.status_code == HTTP_BAD_REQUEST
        error = response.json()
        assert error["error"] == "invalid_grant"

        print("✅ Token refresh endpoint working correctly")

        # Cleanup: Delete the client registration using RFC 7592
        if "registration_access_token" in client and "client_id" in client:
            try:
                delete_response = await http_client.delete(
                    f"{AUTH_BASE_URL}/register/{client['client_id']}",
                    headers={
                        "Authorization": f"Bearer {client['registration_access_token']}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                    },
                    timeout=30.0,
                )
                # 204 No Content is success, 404 is okay if already deleted
                if delete_response.status_code not in (204, 404):
                    print(
                        f"Warning: Failed to delete client {client['client_id']}: {delete_response.status_code}"  # TODO: Break long line
                    )
            except Exception as e:
                print(f"Warning: Error during client cleanup: {e}")


class TestMCPClientTokenValidation:
    """Test token validation scenarios for MCP clients."""

    @pytest.mark.asyncio
    async def test_access_token_validation(self, http_client: httpx.AsyncClient, _wait_for_services):
        """Test validating access tokens before making MCP requests."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")

        # Test token against MCP endpoint
        response = await http_client.post(
            f"{MCP_TESTING_URL}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={
                "Content-Type": "application/json",
                "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Accept": "application/json, text/event-stream",
            },
            timeout=30.0,
        )

        assert response.status_code == HTTP_OK
        print("✅ MCP client token is valid and working")

    @pytest.mark.asyncio
    async def test_expired_token_handling(self, http_client: httpx.AsyncClient, _wait_for_services):
        """Test handling of expired tokens."""
        # Use an obviously invalid token
        response = await http_client.post(
            f"{MCP_TESTING_URL}",
            json={"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1},
            headers={"Authorization": "Bearer expired_token_12345"},
            timeout=30.0,
        )

        assert response.status_code == HTTP_UNAUTHORIZED
        assert "WWW-Authenticate" in response.headers
        print("✅ Expired token correctly rejected with 401")

    @pytest.mark.asyncio
    async def test_token_introspection(self, http_client: httpx.AsyncClient, _wait_for_services):
        """Test token introspection for validity checking."""
        # First register a client
        registration_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": ["http://localhost:8080/callback"],
                "client_name": "TEST test_token_introspection",
            },
            timeout=30.0,
        )

        assert registration_response.status_code == HTTP_CREATED
        client = registration_response.json()

        # Test introspection with MCP client token
        if MCP_CLIENT_ACCESS_TOKEN:
            response = await http_client.post(
                f"{AUTH_BASE_URL}/introspect",
                data={
                    "token": MCP_CLIENT_ACCESS_TOKEN,
                    "client_id": client["client_id"],
                    "client_secret": client["client_secret"],
                },
                timeout=30.0,
            )

            assert response.status_code == HTTP_OK
            result = response.json()

            if result["active"]:
                print("✅ Token introspection shows token is active")
                print(f"   Username: {result.get('username', 'N/A')}")
                print(f"   Scope: {result.get('scope', 'N/A')}")
            else:
                print("⚠️  Token is not active")

        # Cleanup: Delete the client registration using RFC 7592
        if "registration_access_token" in client and "client_id" in client:
            try:
                delete_response = await http_client.delete(
                    f"{AUTH_BASE_URL}/register/{client['client_id']}",
                    headers={
                        "Authorization": f"Bearer {client['registration_access_token']}",
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                    },
                    timeout=30.0,
                )
                # 204 No Content is success, 404 is okay if already deleted
                if delete_response.status_code not in (204, 404):
                    print(
                        f"Warning: Failed to delete client {client['client_id']}: {delete_response.status_code}"  # TODO: Break long line
                    )
            except Exception as e:
                print(f"Warning: Error during client cleanup: {e}")


class TestMCPClientCredentialStorage:
    """Test credential storage patterns used by MCP clients."""

    @pytest.mark.asyncio
    async def test_credential_format(self, http_client: httpx.AsyncClient, _wait_for_services, tmp_path):
        """Test the credential storage format expected by MCP clients."""
        # Register a client
        registration_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": ["http://localhost:8080/callback"],
                "client_name": "TEST test_credential_format",
            },
            timeout=30.0,
        )

        assert registration_response.status_code == HTTP_CREATED
        client = registration_response.json()

        # Create credential file format used by MCP clients
        credentials = {
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "access_token": MCP_CLIENT_ACCESS_TOKEN,
            "token_type": "Bearer",
            "expires_at": int(time.time()) + 3600,  # 1 hour from now
            "refresh_token": None,  # Would be set after OAuth flow
            "registration_response": client,
        }

        # Save to file
        cred_file = tmp_path / "mcp_credentials.json"
        with open(cred_file, "w") as f:
            json.dump(credentials, f, indent=2)

        # Verify file can be read back
        with open(cred_file) as f:
            loaded = json.load(f)

        assert loaded["client_id"] == client["client_id"]
        assert loaded["client_secret"] == client["client_secret"]

        print("✅ Credential storage format verified")
        print(f"   Stored at: {cred_file}")

        # Cleanup: Delete the client registration using RFC 7592
        if "registration_access_token" in client and "client_id" in client:
            async with httpx.AsyncClient(timeout=30.0) as cleanup_client:
                try:
                    delete_response = await cleanup_client.delete(
                        f"{AUTH_BASE_URL}/register/{client['client_id']}",
                        headers={
                            "Authorization": f"Bearer {client['registration_access_token']}"  # TODO: Break long line
                        },
                    )
                    # 204 No Content is success, 404 is okay if already deleted
                    if delete_response.status_code not in (204, 404):
                        print(
                            f"Warning: Failed to delete client {client['client_id']}: {delete_response.status_code}"  # TODO: Break long line
                        )
                except Exception as e:
                    print(f"Warning: Error during client cleanup: {e}")


class TestMCPClientErrorScenarios:
    """Test error handling scenarios for MCP clients."""

    @pytest.mark.asyncio
    async def test_network_error_handling(self, _wait_for_services):
        """Test handling of network errors."""
        # Try to connect to non-existent service
        async with httpx.AsyncClient(timeout=30.0) as client:
            with pytest.raises(httpx.ConnectError):
                await client.get("https://non-existent-service.example.com")

        print("✅ Network errors properly raised")

    @pytest.mark.asyncio
    async def test_oauth_discovery_endpoint(self, http_client: httpx.AsyncClient, _wait_for_services):
        """Test OAuth discovery endpoint that clients use to find auth URLs."""
        response = await http_client.get(f"{AUTH_BASE_URL}/.well-known/oauth-authorization-server", timeout=30.0)

        assert response.status_code == HTTP_OK
        metadata = response.json()

        # Verify endpoints that MCP clients need
        assert "authorization_endpoint" in metadata
        assert "token_endpoint" in metadata
        assert "registration_endpoint" in metadata

        print("✅ OAuth discovery endpoint working")
        print(f"   Authorization: {metadata['authorization_endpoint']}")
        print(f"   Token: {metadata['token_endpoint']}")
        print(f"   Registration: {metadata['registration_endpoint']}")


class TestMCPClientRealWorldScenarios:
    """Test real-world scenarios that MCP clients encounter."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, http_client: httpx.AsyncClient, _wait_for_services):
        """Test handling multiple concurrent MCP requests with same token."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - TESTS MUST NOT BE SKIPPED!")

        import asyncio

        async def make_mcp_request(request_id: int):
            response = await http_client.post(
                f"{MCP_TESTING_URL}",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {
                            "name": f"concurrent-client-{request_id}",
                            "version": "1.0.0",
                        },
                    },
                    "id": request_id,
                },
                headers={
                    "Content-Type": "application/json",
                    "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
                    "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                    "Accept": "application/json, text/event-stream",
                },
                timeout=30.0,
            )
            return response

        # Make 5 concurrent requests
        tasks = [make_mcp_request(i) for i in range(1, 6)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == HTTP_OK

        print(f"✅ Handled {len(responses)} concurrent requests successfully")

    @pytest.mark.asyncio
    async def test_client_reregistration(self, http_client: httpx.AsyncClient, _wait_for_services):
        """Test re-registering a client (common when credentials are lost)."""
        client_name = "TEST test_client_reregistration"

        # Register once
        response1 = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": ["http://localhost:8080/callback"],
                "client_name": client_name,
            },
            timeout=30.0,
        )

        assert response1.status_code == HTTP_CREATED
        client1 = response1.json()

        # Register again with same name
        response2 = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json={
                "redirect_uris": ["http://localhost:8080/callback"],
                "client_name": client_name,
            },
            timeout=30.0,
        )

        assert response2.status_code == HTTP_CREATED
        client2 = response2.json()

        # Should get different client IDs
        assert client1["client_id"] != client2["client_id"]

        print("✅ Client re-registration works correctly")
        print(f"   First ID: {client1['client_id']}")
        print(f"   Second ID: {client2['client_id']}")

        # Cleanup: Delete both client registrations using RFC 7592
        for client in [client1, client2]:
            if "registration_access_token" in client and "client_id" in client:
                try:
                    delete_response = await http_client.delete(
                        f"{AUTH_BASE_URL}/register/{client['client_id']}",
                        headers={
                            "Authorization": f"Bearer {client['registration_access_token']}"  # TODO: Break long line
                        },
                        timeout=30.0,
                    )
                    # 204 No Content is success, 404 is okay if already deleted
                    if delete_response.status_code not in (204, 404):
                        print(
                            f"Warning: Failed to delete client {client['client_id']}: {delete_response.status_code}"  # TODO: Break long line
                        )
                except Exception as e:
                    print(f"Warning: Error during client cleanup: {e}")
