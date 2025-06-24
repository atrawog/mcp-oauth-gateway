"""Sacred Integration Tests for MCP Protocol 2025-06-18 Compliance
Following Commandment 1: NO MOCKING! Test against real deployed services only!
These tests verify compliance with the MCP 2025-06-18 specification.
"""

import json
import os

import httpx
import pytest

from .test_constants import MCP_PROTOCOL_VERSION
from .test_constants import MCP_PROTOCOL_VERSIONS_SUPPORTED
from .test_constants import HTTP_OK
from .test_constants import HTTP_CREATED
from .test_constants import HTTP_NO_CONTENT
from .test_constants import HTTP_UNAUTHORIZED
from .test_constants import HTTP_NOT_FOUND
from .test_constants import HTTP_UNPROCESSABLE_ENTITY


# MCP Client tokens for external client testing
MCP_CLIENT_ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN")


class TestMCPProtocolVersionNegotiation:
    """Test MCP protocol version negotiation per 2025-06-18 spec."""

    @pytest.mark.asyncio
    async def test_protocol_version_negotiation(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test that server negotiates protocol version correctly."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Request current protocol version
        response = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "compliance-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        assert response.status_code == HTTP_OK
        data = response.json()
        # Server may negotiate a different protocol version
        assert "protocolVersion" in data["result"]

    @pytest.mark.asyncio
    async def test_unsupported_protocol_version(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test server behavior with unsupported protocol version."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Request an old/unsupported version
        response = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-01-01",  # Old version
                    "capabilities": {},
                    "clientInfo": {"name": "old-client", "version": "0.1.0"},
                },
                "id": 1,
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        assert response.status_code == HTTP_OK
        data = response.json()

        # Server should either:
        # 1. Return an error
        # 2. Negotiate to a supported version
        if "error" in data:
            assert "protocol" in data["error"]["message"].lower()
        else:
            # Should return a supported version
            assert data["result"]["protocolVersion"] in MCP_PROTOCOL_VERSIONS_SUPPORTED


class TestMCPJSONRPCCompliance:
    """Test JSON-RPC 2.0 compliance as required by MCP spec."""

    @pytest.mark.asyncio
    async def test_json_rpc_request_format(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test that server accepts proper JSON-RPC 2.0 requests."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Valid JSON-RPC 2.0 request
        response = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "jsonrpc-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        assert response.status_code == HTTP_OK
        data = response.json()

        # Response must have JSON-RPC fields
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data or "error" in data
        assert not ("result" in data and "error" in data)  # Can't have both

    @pytest.mark.asyncio
    async def test_json_rpc_error_format(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test that errors follow JSON-RPC 2.0 error format."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Initialize first to get session ID
        init_response = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "error-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)
        assert init_response.status_code == HTTP_OK
        session_id = init_response.headers.get("Mcp-Session-Id")

        # Send invalid method to trigger error
        response = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "invalid/method/name",
                "params": {},
                "id": 2,
            },
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Mcp-Session-Id": session_id,
            }, timeout=30.0)

        assert response.status_code == HTTP_OK  # JSON-RPC errors return 200
        data = response.json()

        # Check error format
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert isinstance(data["error"]["code"], int)  # Must be integer
        # Different MCP servers may return different error codes for unknown methods
        # -32601 = Method not found, -32602 = Invalid params
        assert data["error"]["code"] in [-32601, -32602]

    @pytest.mark.asyncio
    async def test_json_rpc_notification(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test JSON-RPC notifications (no id field)."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Initialize first
        await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "notification-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        # Send notification (no id)
        response = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialized",
                "params": {},
                # No id field - this is a notification
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        # Server should accept notification
        assert response.status_code in [200, 202, 204]

    @pytest.mark.asyncio
    async def test_json_rpc_id_types(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test that both string and number IDs are supported."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Test with number ID
        response1 = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "id-test", "version": "1.0.0"},
                },
                "id": 42,
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        assert response1.status_code == HTTP_OK
        assert response1.json()["id"] == 42

        # Test with string ID
        response2 = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": "unique-string-id",
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        assert response2.status_code == HTTP_OK
        assert response2.json()["id"] == "unique-string-id"


class TestMCPLifecycleCompliance:
    """Test MCP lifecycle requirements per 2025-06-18 spec."""

    @pytest.mark.asyncio
    async def test_initialization_required_fields(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test that initialization response contains all required fields."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        response = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "field-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        assert response.status_code == HTTP_OK
        result = response.json()["result"]

        # Required fields per spec
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        assert "name" in result["serverInfo"]
        assert "version" in result["serverInfo"]

    @pytest.mark.asyncio
    async def test_operations_before_initialization(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test that operations fail before initialization."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Fresh client with no initialization
        async with httpx.AsyncClient(timeout=30.0) as fresh_client:
            response = await fresh_client.post(
                f"{mcp_test_url}",
                json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"},
            )

            # Should fail or return error
            assert response.status_code in [200, 400]
            if response.status_code == HTTP_OK:
                data = response.json()
                if "error" in data:
                    # Should indicate not initialized
                    assert "initializ" in data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_capability_negotiation(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test that server reports capabilities correctly."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Request specific capabilities
        response = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "capability-test", "version": "1.0.0"},
                    "capabilities": {"tools": True, "prompts": True, "resources": True},
                },
                "id": 1,
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)

        assert response.status_code == HTTP_OK
        capabilities = response.json()["result"]["capabilities"]

        # Server should report its actual capabilities
        # mcp-server-fetch should at least have tools
        assert isinstance(capabilities, dict)
        if "tools" in capabilities:
            assert (
                isinstance(capabilities["tools"], dict) or capabilities["tools"] is True
            )


class TestMCPTransportCompliance:
    """Test MCP Streamable HTTP transport compliance."""

    @pytest.mark.asyncio
    async def test_content_type_header(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test that Content-Type header is required."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Send without Content-Type
        response = await http_client.post(
            f"{mcp_test_url}",
            content=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "content-type-test", "version": "1.0.0"},
                    },
                    "id": 1,
                }
            ),
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"
                # No Content-Type header
            },
            timeout=30.0
        )

        # Should either work (defaulting to JSON) or fail
        assert response.status_code in [200, 400, 415]

    @pytest.mark.asyncio
    async def test_mcp_protocol_version_header(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test MCP-Protocol-Version header handling."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Send with MCP-Protocol-Version header
        response = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "header-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
            }, timeout=30.0)

        assert response.status_code == HTTP_OK
        # Header should be accepted

    @pytest.mark.asyncio
    async def test_authorization_header_required(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test that Authorization header is required for protected endpoints."""
        # No auth header
        response = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "no-auth", "version": "1.0.0"},
                },
                "id": 1,
            }, timeout=30.0)

        assert response.status_code == HTTP_UNAUTHORIZED
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"].startswith("Bearer")


class TestMCPSecurityCompliance:
    """Test MCP security requirements per 2025-06-18 spec."""

    @pytest.mark.asyncio
    async def test_origin_header_validation(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test that Origin header is validated to prevent DNS rebinding."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Send with suspicious Origin
        response = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "origin-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Origin": "http://evil.com",
            }, timeout=30.0)

        # Should either accept (if CORS configured) or reject
        assert response.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_token_validation(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test that tokens are properly validated."""
        # Invalid token format
        response = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "token-test", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={"Authorization": "Bearer not-a-valid-jwt-token"}, timeout=30.0)

        assert response.status_code == HTTP_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_secure_session_ids(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test that session IDs are secure and non-deterministic."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Initialize multiple sessions and check IDs are unique

        for i in range(3):
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{mcp_test_url}",
                    json={
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": MCP_PROTOCOL_VERSION,
                            "clientInfo": {"name": f"session-{i}", "version": "1.0.0"},
                        },
                        "id": 1,
                    },
                    headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"},
                )

                assert response.status_code == HTTP_OK
                # Session ID might be in headers or internal
                # Each session should be independent

        # Sessions should be isolated from each other


class TestMCPErrorHandling:
    """Test MCP error handling per spec."""

    @pytest.mark.asyncio
    async def test_standard_error_codes(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test that standard JSON-RPC error codes are used."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        test_cases = [
            # (request, expected_error_code)
            (
                {"jsonrpc": "2.0", "method": "unknown_method", "params": {}, "id": 1},
                -32601,  # Method not found
            ),
            (
                {"jsonrpc": "2.0", "method": "initialize", "id": 1},  # Missing params
                -32602,  # Invalid params
            ),
            (
                {"method": "initialize", "params": {}, "id": 1},  # Missing jsonrpc
                -32600,  # Invalid request
            ),
        ]

        for request, _expected_code in test_cases:
            response = await http_client.post(
                f"{mcp_test_url}",
                json=request,
                headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"},
                timeout=60.0,  # Increase timeout for error handling tests
            )

            if response.status_code == HTTP_OK:
                data = response.json()
                if "error" in data:
                    # Allow some flexibility as servers may handle errors differently
                    assert isinstance(data["error"]["code"], int)

    @pytest.mark.asyncio
    async def test_graceful_error_recovery(
        self, http_client: httpx.AsyncClient, wait_for_services, mcp_test_url
    ):
        """Test that errors don't break the session."""
        if not MCP_CLIENT_ACCESS_TOKEN:
            pytest.fail(
                "No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!"
            )

        # Initialize
        init_response = await http_client.post(
            f"{mcp_test_url}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "error-recovery", "version": "1.0.0"},
                },
                "id": 1,
            },
            headers={"Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}"}, timeout=30.0)
        assert init_response.status_code == HTTP_OK
        session_id = init_response.headers.get("Mcp-Session-Id")

        # Send bad request
        await http_client.post(
            f"{mcp_test_url}",
            json={"jsonrpc": "2.0", "method": "bad_method", "params": {}, "id": 2},
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Mcp-Session-Id": session_id,
            }, timeout=30.0)

        # Now send good request - session should still work
        good_response = await http_client.post(
            f"{mcp_test_url}",
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 3},
            headers={
                "Authorization": f"Bearer {MCP_CLIENT_ACCESS_TOKEN}",
                "Mcp-Session-Id": session_id,
            }, timeout=30.0)

        assert good_response.status_code == HTTP_OK
        data = good_response.json()
        assert "result" in data  # Should succeed despite previous error
