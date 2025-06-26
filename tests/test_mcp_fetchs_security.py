from .test_constants import HTTP_OK
from .test_constants import HTTP_UNAUTHORIZED


"""Security-focused tests for mcp-fetchs native implementation."""

import httpx
import pytest

from tests.test_constants import BASE_DOMAIN
from tests.test_constants import GATEWAY_OAUTH_ACCESS_TOKEN


@pytest.fixture
def base_domain():
    """Base domain for tests."""
    return BASE_DOMAIN


@pytest.fixture
def valid_token():
    """Valid OAuth token for testing."""
    return GATEWAY_OAUTH_ACCESS_TOKEN


class TestMCPFetchsSecurity:
    """Security validation tests for mcp-fetchs."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_auth_schemes(
        self, mcp_fetchs_url, valid_token, wait_for_services
    ):
        """Test various authentication schemes are properly rejected/accepted."""
        test_cases = [
            # (auth_header, expected_status, description)
            (None, 401, "No auth header"),
            ("", 401, "Empty auth header"),
            ("Basic dXNlcjpwYXNz", 401, "Basic auth rejected"),
            ("Token abc123", 401, "Wrong scheme rejected"),
            (f"Bearer {valid_token}", 200, "Valid Bearer accepted"),
            ("Bearer invalid-token-format", 401, "Invalid token format"),
            ("Bearer", 401, "Bearer without token"),
            (f"bearer {valid_token}", 401, "Lowercase bearer rejected"),
        ]

        async with httpx.AsyncClient(verify=True) as client:
            for auth_header, expected_status, description in test_cases:
                headers = {"Content-Type": "application/json"}
                if auth_header is not None:
                    headers["Authorization"] = auth_header

                response = await client.post(
                    f"{mcp_fetchs_url}",
                    json={
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {"protocolVersion": "2025-06-18"},
                        "id": 1,
                    },
                    headers=headers,
                )

                assert response.status_code == expected_status, f"Failed: {description}"
                if expected_status == 401:
                    # WWW-Authenticate header should start with "Bearer"
                    www_auth = response.headers.get("WWW-Authenticate", "")
                    assert www_auth.startswith("Bearer"), (
                        f"WWW-Authenticate should start with Bearer, got: {www_auth}"
                    )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_token_validation(self, mcp_fetchs_url, wait_for_services):
        """Test token validation with various invalid formats."""
        invalid_tokens = [
            "not-a-jwt",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",  # Incomplete JWT
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJub25lIn0.eyJzdWIiOiJ0ZXN0In0.",  # alg: none
        ]

        async with httpx.AsyncClient(verify=True) as client:
            for token in invalid_tokens:
                response = await client.post(
                    f"{mcp_fetchs_url}",
                    json={"jsonrpc": "2.0", "method": "initialize", "id": 1},
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {token}",
                    },
                )

                assert response.status_code == HTTP_UNAUTHORIZED
                # WWW-Authenticate header should start with Bearer
                www_auth = response.headers.get("WWW-Authenticate", "")
                assert www_auth.startswith("Bearer"), (
                    f"WWW-Authenticate should start with Bearer, got: {www_auth}"
                )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_endpoint_auth_requirements(
        self, mcp_fetchs_url, valid_token, wait_for_services
    ):
        """Test which endpoints require authentication."""
        endpoints_auth_required = [
            ("/mcp", "POST", True),
            ("/mcp", "GET", True),
            ("/mcp", "OPTIONS", False),  # CORS preflight
            ("/", "GET", True),
            ("/unknown", "GET", True),
        ]

        async with httpx.AsyncClient(verify=True) as client:
            for path, method, auth_required in endpoints_auth_required:
                # Test without auth
                response = await client.request(
                    method,
                    f"{mcp_fetchs_url}{path}",
                    headers={"Content-Type": "application/json"}
                    if method == "POST"
                    else {},
                    json={"jsonrpc": "2.0", "method": "test", "id": 1}
                    if method == "POST"
                    else None,
                )

                if auth_required:
                    assert response.status_code in [401, 404], (
                        f"{method} {path} should require auth"
                    )
                    if response.status_code == HTTP_UNAUTHORIZED:
                        assert response.headers.get("WWW-Authenticate") == "Bearer"
                else:
                    assert response.status_code != 401, (
                        f"{method} {path} should not require auth"
                    )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_prevents_ssrf(
        self, mcp_fetchs_url, valid_token, wait_for_services
    ):
        """Test Server-Side Request Forgery prevention."""
        dangerous_urls = [
            "http://localhost/admin",
            "http://127.0.0.1:8080",
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "file:///etc/passwd",
            "ftp://internal.server/files",
            "gopher://example.com",
        ]

        async with httpx.AsyncClient(verify=True) as client:
            for url in dangerous_urls:
                response = await client.post(
                    f"{mcp_fetchs_url}",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "fetch",
                            "arguments": {"url": url, "method": "GET"},
                        },
                        "id": 1,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {valid_token}",
                    },
                )

                assert response.status_code == HTTP_OK
                data = response.json()
                # MCP 2025-06-18 returns tool errors with isError: true
                assert "result" in data
                assert data["result"]["isError"] is True
                assert len(data["result"]["content"]) > 0
                assert "Tool execution failed" in data["result"]["content"][0]["text"]

    # REMOVED: This test used httpbin.org which violates our testing principles.
    # Per CLAUDE.md: Test against real deployed services (our own), not external ones.
    #
    # @pytest.mark.integration
    # @pytest.mark.asyncio
    # async def test_fetchs_header_injection_prevention(
    #     self, mcp_fetchs_url, valid_token, wait_for_services
    # ):
    #     """Test prevention of header injection attacks."""
    #     malicious_headers = {
    #         "X-Injected\r\nX-Evil": "value",
    #         "X-Test": "value\r\nX-Injected: evil",
    #         "Authorization": "Bearer fake-token",  # Should not override
    #     }
    #
    #     async with httpx.AsyncClient(verify=True) as client:
    #         response = await client.post(
    #             f"{mcp_fetchs_url}",
    #             json={
    #                 "jsonrpc": "2.0",
    #                 "method": "tools/call",
    #                 "params": {
    #                     "name": "fetch",
    #                     "arguments": {
    #                         "url": "https://httpbin.org/headers",
    #                         "method": "GET",
    #                         "headers": malicious_headers,
    #                     },
    #                 },
    #                 "id": 1,
    #             },
    #             headers={
    #                 "Content-Type": "application/json",
    #                 "Authorization": f"Bearer {valid_token}",
    #             },
    #         )
    #
    #         # Should either sanitize or reject malicious headers
    #         assert response.status_code == HTTP_OK
    #         data = response.json()
    #         if "result" in data:
    #             content = data["result"]["content"][0]["text"]
    #             # Check that CRLF injection didn't work
    #             assert "X-Evil" not in content or "\\r\\n" in content
    #
    # @pytest.mark.integration
    # @pytest.mark.asyncio
    async def test_fetchs_rate_limiting_behavior(
        self, mcp_fetchs_url, valid_token, wait_for_services
    ):
        """Test service behavior under rapid requests."""
        async with httpx.AsyncClient(verify=True) as client:
            # Make 10 rapid requests
            responses = []
            for i in range(10):
                response = await client.post(
                    f"{mcp_fetchs_url}",
                    json={"jsonrpc": "2.0", "method": "tools/list", "id": i},
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {valid_token}",
                    },
                )
                responses.append(response.status_code)

            # All should succeed (no built-in rate limiting)
            assert all(status == 200 for status in responses)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetchs_oauth_discovery_security(
        self, base_domain, wait_for_services
    ):
        """Test OAuth discovery endpoint security."""
        from tests.test_constants import MCP_FETCHS_TESTS_ENABLED
        
        if not MCP_FETCHS_TESTS_ENABLED:
            pytest.skip("MCP Fetchs tests are disabled. Set MCP_FETCHS_TESTS_ENABLED=true to enable.")
        
        # Use base domain for OAuth discovery, not the /mcp endpoint
        oauth_discovery_url = (
            f"https://fetchs.{base_domain}/.well-known/oauth-authorization-server"
        )

        async with httpx.AsyncClient(verify=True) as client:
            # Discovery should be publicly accessible
            response = await client.get(oauth_discovery_url)

            assert response.status_code == HTTP_OK
            data = response.json()

            # Should contain proper OAuth metadata
            assert "issuer" in data
            assert "authorization_endpoint" in data
            assert "token_endpoint" in data
            assert "registration_endpoint" in data

            # Should use HTTPS URLs
            for key in ["issuer", "authorization_endpoint", "token_endpoint"]:
                assert data[key].startswith("https://"), f"{key} should use HTTPS"
