"""Test the replayLastEcho functionality of MCP Echo Stateful server."""

import uuid

import httpx
import pytest


class TestMCPEchoStatefulReplay:
    """Test the replayLastEcho tool in the stateful MCP Echo server."""

    @pytest.mark.asyncio
    async def test_replay_last_echo_basic(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateful_url: str,
        gateway_auth_headers: dict,
    ):
        """Test basic replayLastEcho functionality."""
        test_message = f"Test message {uuid.uuid4()}"

        # Initialize session
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test-replay", "version": "1.0"},
            },
            "id": 1,
        }

        # Initialize
        response = await http_client.post(mcp_echo_stateful_url, json=init_request, headers=gateway_auth_headers)
        assert response.status_code == 200
        session_id = response.headers.get("mcp-session-id")
        assert session_id is not None

        # Add session ID to headers for subsequent requests
        headers_with_session = {**gateway_auth_headers, "mcp-session-id": session_id}

        # Send echo request
        echo_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "echo", "arguments": {"message": test_message}},
            "id": 2,
        }

        response = await http_client.post(mcp_echo_stateful_url, json=echo_request, headers=headers_with_session)
        assert response.status_code == 200
        echo_result = response.json()
        assert "result" in echo_result
        assert test_message in echo_result["result"]["content"][0]["text"]

        # Test replay
        replay_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "replayLastEcho", "arguments": {}},
            "id": 3,
        }

        response = await http_client.post(mcp_echo_stateful_url, json=replay_request, headers=headers_with_session)
        assert response.status_code == 200
        replay_result = response.json()
        assert "result" in replay_result
        replay_text = replay_result["result"]["content"][0]["text"]
        assert "[REPLAY" in replay_text
        assert test_message in replay_text

    @pytest.mark.asyncio
    async def test_replay_without_prior_echo(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateful_url: str,
        gateway_auth_headers: dict,
    ):
        """Test replayLastEcho without calling echo first."""
        # Initialize session
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test-replay-no-echo", "version": "1.0"},
            },
            "id": 1,
        }

        # Initialize
        response = await http_client.post(mcp_echo_stateful_url, json=init_request, headers=gateway_auth_headers)
        assert response.status_code == 200
        session_id = response.headers.get("mcp-session-id")
        assert session_id is not None

        # Add session ID to headers
        headers_with_session = {**gateway_auth_headers, "mcp-session-id": session_id}

        # Try replay without echo
        replay_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "replayLastEcho", "arguments": {}},
            "id": 2,
        }

        response = await http_client.post(mcp_echo_stateful_url, json=replay_request, headers=headers_with_session)
        assert response.status_code == 200
        replay_result = response.json()
        assert "result" in replay_result
        replay_text = replay_result["result"]["content"][0]["text"]
        assert "No previous echo message found" in replay_text

    @pytest.mark.asyncio
    async def test_replay_without_session(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateful_url: str,
        gateway_auth_headers: dict,
    ):
        """Test replayLastEcho without a session ID."""
        # Try replay without session - should create a new session
        replay_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "replayLastEcho", "arguments": {}},
            "id": 1,
        }

        response = await http_client.post(mcp_echo_stateful_url, json=replay_request, headers=gateway_auth_headers)
        assert response.status_code == 200
        result = response.json()
        # Since no session was provided, replayLastEcho returns an error
        assert "error" in result
        assert "Session required for replay functionality" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_multiple_echo_replay(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateful_url: str,
        gateway_auth_headers: dict,
    ):
        """Test that replay always returns the last echo message."""
        messages = [f"Message {i} - {uuid.uuid4()}" for i in range(3)]

        # Initialize session
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test-multi-replay", "version": "1.0"},
            },
            "id": 1,
        }

        # Initialize
        response = await http_client.post(mcp_echo_stateful_url, json=init_request, headers=gateway_auth_headers)
        assert response.status_code == 200
        session_id = response.headers.get("mcp-session-id")
        assert session_id is not None

        # Add session ID to headers
        headers_with_session = {**gateway_auth_headers, "mcp-session-id": session_id}

        # Send multiple echo requests
        for i, message in enumerate(messages):
            echo_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "echo", "arguments": {"message": message}},
                "id": i + 2,
            }

            response = await http_client.post(mcp_echo_stateful_url, json=echo_request, headers=headers_with_session)
            assert response.status_code == 200

        # Replay should return the last message
        replay_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "replayLastEcho", "arguments": {}},
            "id": len(messages) + 2,
        }

        response = await http_client.post(mcp_echo_stateful_url, json=replay_request, headers=headers_with_session)
        assert response.status_code == 200
        replay_result = response.json()
        assert "result" in replay_result
        replay_text = replay_result["result"]["content"][0]["text"]
        assert "[REPLAY" in replay_text
        assert messages[-1] in replay_text  # Should contain the last message
        # Should not contain earlier messages
        for msg in messages[:-1]:
            assert msg not in replay_text

    @pytest.mark.asyncio
    async def test_replay_preserves_session_context(
        self,
        http_client: httpx.AsyncClient,
        mcp_echo_stateful_url: str,
        gateway_auth_headers: dict,
    ):
        """Test that replay includes session context information."""
        test_message = f"Context test {uuid.uuid4()}"
        client_name = "test-context-client"

        # Initialize session with specific client name
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": client_name, "version": "2.0"},
            },
            "id": 1,
        }

        # Initialize
        response = await http_client.post(mcp_echo_stateful_url, json=init_request, headers=gateway_auth_headers)
        assert response.status_code == 200
        session_id = response.headers.get("mcp-session-id")
        assert session_id is not None

        # Add session ID to headers
        headers_with_session = {**gateway_auth_headers, "mcp-session-id": session_id}

        # Send echo request
        echo_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "echo", "arguments": {"message": test_message}},
            "id": 2,
        }

        response = await http_client.post(mcp_echo_stateful_url, json=echo_request, headers=headers_with_session)
        assert response.status_code == 200

        # Test replay
        replay_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "replayLastEcho", "arguments": {}},
            "id": 3,
        }

        response = await http_client.post(mcp_echo_stateful_url, json=replay_request, headers=headers_with_session)
        assert response.status_code == 200
        replay_result = response.json()
        assert "result" in replay_result
        replay_text = replay_result["result"]["content"][0]["text"]

        # Check session context is preserved
        assert f"[REPLAY - Session {session_id[:8]}" in replay_text
        assert f"from {client_name}]" in replay_text
        assert test_message in replay_text
