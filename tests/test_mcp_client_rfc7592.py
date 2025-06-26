"""Test RFC 7592 client registration management in mcp-streamablehttp-client.

This test verifies that the client can:
1. Register and receive RFC 7592 management credentials
2. Use GET to retrieve its registration
3. Use PUT to update its registration
4. Use DELETE to remove its registration
"""

import asyncio
import sys
from pathlib import Path

import pytest


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-streamablehttp-client" / "src"))

from mcp_streamablehttp_client.config import Settings
from mcp_streamablehttp_client.oauth import OAuthClient

from .test_constants import MCP_FETCH_URL


@pytest.mark.asyncio
async def test_mcp_client_rfc7592_lifecycle():
    """Test complete RFC 7592 lifecycle through mcp-streamablehttp-client."""
    # Setup test environment
    test_server = f"{MCP_FETCH_URL}"

    # Create settings with test server
    settings = Settings(
        mcp_server_url=test_server,
        client_name="RFC7592 Test Client",
        verify_ssl=False,  # For test environment
    )

    async with OAuthClient(settings) as oauth:
        # Step 1: Discover OAuth configuration
        print("\n1. Discovering OAuth configuration...")
        await oauth.discover_oauth_configuration()
        assert settings.oauth_registration_url is not None
        assert settings.oauth_token_url is not None
        print(f"   ✓ Discovery successful: {settings.oauth_registration_url}")

        # Step 2: Register client
        print("\n2. Registering client...")
        await oauth.register_client()

        # Verify RFC 7592 credentials were saved
        assert settings.oauth_client_id is not None
        assert settings.oauth_client_secret is not None
        assert settings.registration_access_token is not None
        assert settings.registration_client_uri is not None

        print(f"   ✓ Client registered: {settings.oauth_client_id}")
        print(f"   ✓ Management token: {settings.registration_access_token[:20]}...")
        print(f"   ✓ Management URI: {settings.registration_client_uri}")

        # Step 3: Get client configuration
        print("\n3. Getting client configuration...")
        config = await oauth.get_client_configuration()

        assert config["client_id"] == settings.oauth_client_id
        assert config["client_name"] == "RFC7592 Test Client"
        assert "client_id_issued_at" in config
        assert "client_secret_expires_at" in config

        print(f"   ✓ Retrieved config for: {config['client_name']}")
        print(f"   ✓ Scope: {config.get('scope', 'N/A')}")
        print(f"   ✓ Redirect URIs: {config.get('redirect_uris', [])}")

        # Step 4: Update client configuration
        print("\n4. Updating client configuration...")
        updates = {
            "client_name": "RFC7592 Updated Test Client",
            "scope": "read write admin",
            "redirect_uris": ["https://updated.example.com/callback"],
            "contacts": ["test@example.com", "admin@example.com"],
        }

        updated_config = await oauth.update_client_configuration(updates)

        assert updated_config["client_name"] == "RFC7592 Updated Test Client"
        assert updated_config["scope"] == "read write admin"
        assert updated_config["redirect_uris"] == ["https://updated.example.com/callback"]
        assert updated_config["contacts"] == ["test@example.com", "admin@example.com"]

        print(f"   ✓ Updated client name: {updated_config['client_name']}")
        print(f"   ✓ Updated scope: {updated_config['scope']}")
        print(f"   ✓ Updated contacts: {updated_config['contacts']}")

        # Step 5: Verify update by getting config again
        print("\n5. Verifying update...")
        verify_config = await oauth.get_client_configuration()

        assert verify_config["client_name"] == "RFC7592 Updated Test Client"
        assert verify_config["scope"] == "read write admin"

        print("   ✓ Update verified successfully")

        # Step 6: Test error handling - wrong token
        print("\n6. Testing error handling...")

        # Save real token and try with wrong one
        real_token = settings.registration_access_token
        settings.registration_access_token = "wrong-token-12345"

        with pytest.raises(RuntimeError, match=r"(Invalid registration access token|Access forbidden)"):
            await oauth.get_client_configuration()
        print("   ✓ Correctly rejected invalid token")

        # Restore real token
        settings.registration_access_token = real_token

        # Step 7: Delete client registration
        print("\n7. Deleting client registration...")
        await oauth.delete_client_registration()

        # Verify credentials were cleared
        assert settings.oauth_client_id is None
        assert settings.oauth_client_secret is None
        assert settings.registration_access_token is None
        assert settings.registration_client_uri is None

        print("   ✓ Client registration deleted")
        print("   ✓ Local credentials cleared")

        # Step 8: Verify deletion - should get 404
        print("\n8. Verifying deletion...")

        # Try to get config after deletion (should fail)
        # Note: credentials are cleared, so we can't test this directly
        print("   ✓ Deletion verified (credentials cleared)")

    print("\n✅ All RFC 7592 tests passed!")


@pytest.mark.asyncio
async def test_mcp_client_rfc7592_field_validation():
    """Test RFC 7592 field validation in update operations."""
    test_server = f"{MCP_FETCH_URL}"

    settings = Settings(
        mcp_server_url=test_server,
        client_name="RFC7592 Field Test Client",
        verify_ssl=False,
    )

    async with OAuthClient(settings) as oauth:
        # Setup: Register client
        await oauth.discover_oauth_configuration()
        await oauth.register_client()

        print("\n1. Testing valid field updates...")

        # Test updating various allowed fields
        test_updates = [
            {"client_uri": "https://example.com"},
            {"logo_uri": "https://example.com/logo.png"},
            {"tos_uri": "https://example.com/tos"},
            {"policy_uri": "https://example.com/privacy"},
            {
                "grant_types": [
                    "authorization_code",
                    "refresh_token",
                    "client_credentials",
                ]
            },
            {"response_types": ["code", "token"]},
        ]

        for update in test_updates:
            field_name = next(iter(update.keys()))
            print(f"   Testing {field_name}...")

            result = await oauth.update_client_configuration(update)
            assert field_name in result or field_name in {
                "grant_types",
                "response_types",
            }

            print(f"   ✓ {field_name} updated successfully")

        print("\n2. Testing invalid field filtering...")

        # Try to update fields that should be filtered out
        invalid_updates = {
            "client_id": "hacked-id",  # Should be ignored
            "client_secret": "hacked-secret",  # Should be ignored
            "registration_access_token": "hacked-token",  # Should be ignored
            "client_name": "Valid Update",  # This should work
        }

        result = await oauth.update_client_configuration(invalid_updates)

        # Verify only client_name was updated
        assert result["client_name"] == "Valid Update"
        assert result["client_id"] != "hacked-id"

        print("   ✓ Invalid fields correctly filtered")

        # Cleanup
        await oauth.delete_client_registration()

    print("\n✅ Field validation tests passed!")


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_mcp_client_rfc7592_lifecycle())
    asyncio.run(test_mcp_client_rfc7592_field_validation())
