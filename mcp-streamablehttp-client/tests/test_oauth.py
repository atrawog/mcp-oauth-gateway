"""Tests for OAuth client functionality."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import pytest
import httpx
from httpx import Response

from mcp_http_stdio.config import Settings
from mcp_http_stdio.oauth import OAuthClient


@pytest.fixture
def settings(tmp_path):
    """Create test settings."""
    return Settings(
        mcp_server_url="https://test.example.com/mcp",
        oauth_authorization_url="https://auth.example.com/authorize",
        oauth_token_url="https://auth.example.com/token",
        oauth_device_auth_url="https://auth.example.com/device/code",
        oauth_registration_url="https://auth.example.com/register",
        credential_storage_path=tmp_path / "credentials.json"
    )


@pytest.fixture
def oauth_client(settings):
    """Create OAuth client instance."""
    return OAuthClient(settings)


@pytest.mark.asyncio
async def test_client_registration(oauth_client, settings):
    """Test OAuth client registration."""
    # Mock the HTTP response
    mock_response = Mock(spec=Response)
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "client_id_issued_at": 1234567890,
        "client_secret_expires_at": 0
    }
    
    with patch.object(oauth_client.client, 'post', return_value=mock_response) as mock_post:
        await oauth_client.register_client()
        
        # Verify registration request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == settings.oauth_registration_url
        
        # Verify client credentials were saved
        assert settings.oauth_client_id == "test-client-id"
        assert settings.oauth_client_secret == "test-client-secret"


@pytest.mark.asyncio
async def test_device_flow_auth(oauth_client, settings):
    """Test device flow authentication."""
    # Mock device code response
    device_response = Mock(spec=Response)
    device_response.status_code = 200
    device_response.json.return_value = {
        "device_code": "test-device-code",
        "user_code": "TEST-CODE",
        "verification_uri": "https://auth.example.com/device",
        "expires_in": 600,
        "interval": 5
    }
    
    # Mock token response (after user authorization)
    token_response = Mock(spec=Response)
    token_response.status_code = 200
    token_response.json.return_value = {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    
    # Mock pending response
    pending_response = Mock(spec=Response)
    pending_response.status_code = 400
    pending_response.json.return_value = {
        "error": "authorization_pending"
    }
    
    # Set up client credentials
    settings.oauth_client_id = "test-client"
    settings.oauth_client_secret = "test-secret"
    
    with patch.object(oauth_client.client, 'post') as mock_post:
        # First call returns device code, second returns pending, third returns token
        mock_post.side_effect = [device_response, pending_response, token_response]
        
        with patch('mcp_http_stdio.oauth.console'):  # Suppress console output
            with patch('asyncio.sleep'):  # Speed up test
                await oauth_client.device_flow_auth()
        
        # Verify tokens were saved
        assert settings.oauth_access_token == "test-access-token"
        assert settings.oauth_refresh_token == "test-refresh-token"
        assert settings.oauth_token_expires_at is not None


@pytest.mark.asyncio
async def test_token_refresh(oauth_client, settings):
    """Test token refresh functionality."""
    # Set up existing tokens
    settings.oauth_client_id = "test-client"
    settings.oauth_refresh_token = "old-refresh-token"
    settings.oauth_access_token = "old-access-token"
    
    # Mock refresh response
    refresh_response = Mock(spec=Response)
    refresh_response.status_code = 200
    refresh_response.json.return_value = {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    
    with patch.object(oauth_client.client, 'post', return_value=refresh_response) as mock_post:
        await oauth_client.refresh_token()
        
        # Verify refresh request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == settings.oauth_token_url
        assert call_args[1]["data"]["grant_type"] == "refresh_token"
        assert call_args[1]["data"]["refresh_token"] == "old-refresh-token"
        
        # Verify new tokens were saved
        assert settings.oauth_access_token == "new-access-token"
        assert settings.oauth_refresh_token == "new-refresh-token"


@pytest.mark.asyncio
async def test_ensure_authenticated_with_valid_token(oauth_client, settings):
    """Test ensure_authenticated when token is already valid."""
    # Set up valid token
    settings.oauth_access_token = "valid-token"
    settings.oauth_token_expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Mock load_credentials
    with patch.object(settings, 'load_credentials'):
        token = await oauth_client.ensure_authenticated()
    
    assert token == "valid-token"


@pytest.mark.asyncio
async def test_ensure_authenticated_needs_refresh(oauth_client, settings):
    """Test ensure_authenticated when token needs refresh."""
    # Set up expired token
    settings.oauth_access_token = "expired-token"
    settings.oauth_refresh_token = "refresh-token"
    settings.oauth_token_expires_at = datetime.utcnow() - timedelta(hours=1)
    
    # Mock refresh response
    refresh_response = Mock(spec=Response)
    refresh_response.status_code = 200
    refresh_response.json.return_value = {
        "access_token": "new-token",
        "refresh_token": "new-refresh-token",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    
    with patch.object(settings, 'load_credentials'):
        with patch.object(oauth_client.client, 'post', return_value=refresh_response):
            token = await oauth_client.ensure_authenticated()
    
    assert token == "new-token"


@pytest.mark.asyncio
async def test_credential_persistence(settings):
    """Test saving and loading credentials."""
    # Set credentials
    settings.oauth_client_id = "test-client"
    settings.oauth_client_secret = "test-secret"
    settings.oauth_access_token = "test-token"
    settings.oauth_refresh_token = "test-refresh"
    settings.oauth_token_expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Save credentials
    settings.save_credentials()
    
    # Verify file was created with correct permissions
    assert settings.credential_storage_path.exists()
    stat = settings.credential_storage_path.stat()
    assert oct(stat.st_mode)[-3:] == "600"
    
    # Load credentials into new settings instance
    new_settings = Settings(
        mcp_server_url="https://test.example.com/mcp",
        oauth_authorization_url="https://auth.example.com/authorize",
        oauth_token_url="https://auth.example.com/token",
        credential_storage_path=settings.credential_storage_path
    )
    new_settings.load_credentials()
    
    # Verify credentials were loaded
    assert new_settings.oauth_client_id == "test-client"
    assert new_settings.oauth_client_secret == "test-secret"
    assert new_settings.oauth_access_token == "test-token"
    assert new_settings.oauth_refresh_token == "test-refresh"