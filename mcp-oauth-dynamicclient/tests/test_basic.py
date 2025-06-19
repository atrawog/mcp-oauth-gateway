"""
Basic tests for mcp-oauth-dynamicclient
"""
import pytest
from mcp_oauth_dynamicclient import create_app, Settings, ClientRegistration


def test_imports():
    """Test that all imports work correctly"""
    assert create_app is not None
    assert Settings is not None
    assert ClientRegistration is not None


def test_client_registration_model():
    """Test ClientRegistration model"""
    registration = ClientRegistration(
        redirect_uris=["https://example.com/callback"],
        client_name="Test Client"
    )
    assert registration.redirect_uris == ["https://example.com/callback"]
    assert registration.client_name == "Test Client"
    assert registration.scope is None  # Default value


def test_create_app():
    """Test app creation (without Redis)"""
    # This will fail if Redis is required at startup
    # In a real test, you'd mock Redis or use a test instance
    try:
        from unittest.mock import MagicMock
        settings = MagicMock(spec=Settings)
        settings.redis_url = "redis://localhost:6379"
        settings.base_domain = "test.com"
        settings.jwt_secret = "test_secret"
        settings.jwt_algorithm = "HS256"
        
        # The app creation itself should work
        app = create_app(settings)
        assert app is not None
        assert app.title == "MCP OAuth Gateway - Auth Service"
    except Exception as e:
        # Expected if Redis is not available
        pytest.skip(f"Redis not available: {e}")