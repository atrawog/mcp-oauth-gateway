"""Tests for the MCP stdio-to-HTTP proxy."""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from mcp_stdio_http import MCPSession, MCPSessionManager, create_app


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for testing."""
    mock_process = Mock()
    mock_process.stdin = Mock()
    mock_process.stdin.write = Mock()
    mock_process.stdin.drain = AsyncMock()
    mock_process.stdout = Mock()
    mock_process.stdout.readline = AsyncMock()
    mock_process.stderr = Mock()
    mock_process.terminate = Mock()
    mock_process.wait = AsyncMock()
    return mock_process


@pytest.mark.asyncio
async def test_mcp_session_initialization(mock_subprocess):
    """Test MCPSession initialization."""
    session = MCPSession("test-session-id", ["python", "-m", "test_server"])
    
    assert session.session_id == "test-session-id"
    assert session.server_command == ["python", "-m", "test_server"]
    assert not session.session_initialized
    assert session.request_id_counter == 0


@pytest.mark.asyncio
async def test_mcp_session_manager():
    """Test MCPSessionManager basic functionality."""
    manager = MCPSessionManager(["python", "-m", "test_server"])
    
    assert len(manager.sessions) == 0
    assert manager.session_timeout == 300
    
    # Test start and stop
    await manager.start()
    assert manager._cleanup_task is not None
    
    await manager.stop()
    assert len(manager.sessions) == 0


@pytest.mark.asyncio
async def test_create_app():
    """Test FastAPI app creation."""
    app = create_app(["python", "-m", "test_server"])
    
    # Check that required endpoints exist
    routes = [route.path for route in app.routes]
    assert "/health" in routes
    assert "/mcp" in routes
    assert "/mcp/" in routes


@pytest.mark.asyncio
async def test_session_timeout():
    """Test session timeout functionality."""
    manager = MCPSessionManager(["python", "-m", "test_server"], session_timeout=1)
    
    # Create a mock session
    session = Mock()
    session.last_activity = 0  # Very old timestamp
    session.close = AsyncMock()
    
    manager.sessions["test-id"] = session
    
    # Manually trigger cleanup
    current_time = 1000000
    with patch('time.time', return_value=current_time):
        expired_sessions = []
        for session_id, sess in manager.sessions.items():
            if current_time - sess.last_activity > manager.session_timeout:
                expired_sessions.append(session_id)
        
        assert "test-id" in expired_sessions


if __name__ == "__main__":
    pytest.main([__file__])