"""Tests for HTTP-to-stdio proxy functionality."""
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

import pytest
import httpx

from mcp_http_stdio.config import Settings
from mcp_http_stdio.proxy import HTTPToStdioProxy


@pytest.fixture
def settings(tmp_path):
    """Create test settings."""
    settings = Settings(
        mcp_server_url="https://test.example.com/mcp",
        oauth_authorization_url="https://auth.example.com/authorize",
        oauth_token_url="https://auth.example.com/token",
        credential_storage_path=tmp_path / "credentials.json"
    )
    settings.oauth_access_token = "test-token"
    settings.oauth_token_expires_at = datetime.utcnow() + timedelta(hours=1)
    return settings


@pytest.fixture
def proxy(settings):
    """Create proxy instance."""
    return HTTPToStdioProxy(settings)


@pytest.mark.asyncio
async def test_proxy_initialization(proxy, settings):
    """Test proxy initialization."""
    with patch('mcp_http_stdio.proxy.OAuthClient') as mock_oauth_class:
        mock_oauth = mock_oauth_class.return_value
        mock_oauth.__aenter__.return_value = mock_oauth
        mock_oauth.__aexit__.return_value = None
        mock_oauth.ensure_authenticated = AsyncMock(return_value="test-token")
        
        await proxy.start()
        
        assert proxy.http_client is not None
        assert proxy.access_token == "test-token"
        assert proxy._running is True
        
        await proxy.stop()
        assert proxy._running is False


@pytest.mark.asyncio
async def test_handle_initialize_request(proxy, settings):
    """Test handling initialize request."""
    await proxy.start()
    
    request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        },
        "id": "init-1"
    }
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": "2025-06-18",
            "serverInfo": {
                "name": "test-server",
                "version": "1.0.0"
            },
            "capabilities": {}
        },
        "id": "init-1"
    }
    mock_response.headers = {"Mcp-Session-Id": "test-session-id"}
    
    with patch.object(proxy.http_client, 'post', return_value=mock_response) as mock_post:
        response = await proxy._handle_request(request)
        
        # Verify request was forwarded
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == settings.mcp_server_url
        assert call_args[1]["json"] == request
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"
        assert call_args[1]["headers"]["MCP-Protocol-Version"] == "2025-06-18"
        
        # Verify response
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == "init-1"
        assert "result" in response
        
        # Verify session ID was saved
        assert proxy.session_id == "test-session-id"
    
    await proxy.stop()


@pytest.mark.asyncio
async def test_handle_request_with_auth_error(proxy, settings):
    """Test handling request with authentication error."""
    await proxy.start()
    
    request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": "list-1"
    }
    
    # Mock 401 response
    mock_401_response = Mock()
    mock_401_response.status_code = 401
    mock_401_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "401 Unauthorized", request=Mock(), response=mock_401_response
    )
    
    # Mock successful response after re-auth
    mock_success_response = Mock()
    mock_success_response.status_code = 200
    mock_success_response.json.return_value = {
        "jsonrpc": "2.0",
        "result": {"tools": []},
        "id": "list-1"
    }
    mock_success_response.headers = {}
    
    with patch.object(proxy.http_client, 'post') as mock_post:
        mock_post.side_effect = [mock_401_response, mock_success_response]
        
        with patch('mcp_http_stdio.proxy.OAuthClient') as mock_oauth_class:
            mock_oauth = mock_oauth_class.return_value
            mock_oauth.__aenter__.return_value = mock_oauth
            mock_oauth.__aexit__.return_value = None
            mock_oauth.ensure_authenticated = AsyncMock(return_value="new-token")
            
            response = await proxy._handle_request(request)
            
            # Verify re-authentication happened
            mock_oauth.ensure_authenticated.assert_called_once()
            
            # Verify request was retried
            assert mock_post.call_count == 2
            
            # Verify response
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == "list-1"
            assert "result" in response
    
    await proxy.stop()


@pytest.mark.asyncio
async def test_handle_request_with_expired_token(proxy, settings):
    """Test handling request when token is expired."""
    # Set expired token
    settings.oauth_token_expires_at = datetime.utcnow() - timedelta(hours=1)
    settings.oauth_refresh_token = "refresh-token"
    
    await proxy.start()
    
    request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": "list-1"
    }
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "jsonrpc": "2.0",
        "result": {"tools": []},
        "id": "list-1"
    }
    mock_response.headers = {}
    
    with patch.object(proxy.http_client, 'post', return_value=mock_response):
        with patch('mcp_http_stdio.proxy.OAuthClient') as mock_oauth_class:
            mock_oauth = mock_oauth_class.return_value
            mock_oauth.__aenter__.return_value = mock_oauth
            mock_oauth.__aexit__.return_value = None
            mock_oauth.refresh_token = AsyncMock()
            
            # Update settings to simulate successful refresh
            async def update_token():
                settings.oauth_access_token = "new-token"
                settings.oauth_token_expires_at = datetime.utcnow() + timedelta(hours=1)
            
            mock_oauth.refresh_token.side_effect = update_token
            
            response = await proxy._handle_request(request)
            
            # Verify token refresh happened
            mock_oauth.refresh_token.assert_called_once()
            
            # Verify response
            assert response["jsonrpc"] == "2.0"
            assert response["id"] == "list-1"
            assert "result" in response
    
    await proxy.stop()


@pytest.mark.asyncio
async def test_json_rpc_error_handling(proxy, settings):
    """Test JSON-RPC error handling."""
    await proxy.start()
    
    request = {
        "jsonrpc": "2.0",
        "method": "unknown/method",
        "params": {},
        "id": "error-1"
    }
    
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Internal Server Error", request=Mock(), response=mock_response
    )
    
    with patch.object(proxy.http_client, 'post', return_value=mock_response):
        response = await proxy._handle_request(request)
        
        # Verify error response
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == "error-1"
        assert "error" in response
        assert response["error"]["code"] == -32603
    
    await proxy.stop()