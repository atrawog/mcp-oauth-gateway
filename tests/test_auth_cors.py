"""Test Auth service CORS configuration.

CRITICAL: Auth service MUST have proper CORS headers for web clients!
"""

import os

import httpx
import pytest

from .test_constants import HTTP_OK


class TestAuthCORS:
    """Test that Auth service has proper CORS configuration."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.base_domain = os.getenv("BASE_DOMAIN")
        if not self.base_domain:
            pytest.fail("BASE_DOMAIN environment variable not set")

        self.cors_origins = os.getenv("MCP_CORS_ORIGINS", "").split(",")
        self.cors_origins = [
            origin.strip() for origin in self.cors_origins if origin.strip()
        ]

    def test_cors_origins_configured(self):
        """Test that MCP_CORS_ORIGINS is configured."""
        assert os.getenv("MCP_CORS_ORIGINS"), "MCP_CORS_ORIGINS MUST be configured!"
        assert len(self.cors_origins) > 0, (
            "MCP_CORS_ORIGINS must contain at least one origin"
        )

    def test_auth_preflight_cors_headers(self):
        """Test that Auth endpoints respond correctly to CORS preflight requests."""
        # Test key auth endpoints
        endpoints = [
            f"https://auth.{self.base_domain}/register",
            f"https://auth.{self.base_domain}/token",
            f"https://auth.{self.base_domain}/authorize",
            f"https://auth.{self.base_domain}/.well-known/oauth-authorization-server",
        ]

        # If CORS is set to wildcard, test with a sample origin
        test_origins = ["https://example.com"] if self.cors_origins == ["*"] else self.cors_origins

        # Test OPTIONS request (CORS preflight) for each endpoint and origin
        with httpx.Client(verify=True, timeout=10.0) as client:
            for endpoint in endpoints:
                for test_origin in test_origins:
                    response = client.options(
                        endpoint,
                        headers={
                            "Origin": test_origin,
                            "Access-Control-Request-Method": "POST",
                            "Access-Control-Request-Headers": "content-type,authorization",
                        },
                    )

                    # CORS preflight should return 200 OK
                    assert response.status_code == HTTP_OK, (
                        f"CORS preflight failed for {endpoint} with origin {test_origin}"  # TODO: Break long line
                    )

                    # Check CORS headers
                    assert "access-control-allow-origin" in response.headers, (
                        f"Missing Access-Control-Allow-Origin header for {endpoint}"
                    )

                    # When wildcard is configured, FastAPI returns the specific origin, not "*"
                    if self.cors_origins == ["*"]:
                        assert (
                            response.headers["access-control-allow-origin"]
                            == test_origin
                        ), f"CORS origin mismatch for {endpoint}"
                    else:
                        assert (
                            response.headers["access-control-allow-origin"]
                            == test_origin
                        ), f"CORS origin mismatch for {endpoint}"

                    assert "access-control-allow-methods" in response.headers, (
                        f"Missing Access-Control-Allow-Methods header for {endpoint}"
                    )
                    allowed_methods = response.headers[
                        "access-control-allow-methods"
                    ].upper()
                    assert "POST" in allowed_methods or "GET" in allowed_methods, (
                        f"Required methods not allowed in CORS for {endpoint}"
                    )

                    assert "access-control-allow-headers" in response.headers, (
                        f"Missing Access-Control-Allow-Headers header for {endpoint}"
                    )
                    assert "access-control-allow-credentials" in response.headers, (
                        f"Missing Access-Control-Allow-Credentials header for {endpoint}"  # TODO: Break long line
                    )
                    assert (
                        response.headers["access-control-allow-credentials"].lower()
                        == "true"
                    ), f"CORS credentials not allowed for {endpoint}"

    def test_auth_actual_request_cors_headers(self):
        """Test that actual Auth requests include proper CORS headers."""
        # Test metadata endpoint which doesn't require auth
        metadata_url = (
            f"https://auth.{self.base_domain}/.well-known/oauth-authorization-server"
        )

        # If CORS is set to wildcard, use a test origin
        test_origin = "https://example.com" if self.cors_origins == ["*"] else self.cors_origins[0]

        with httpx.Client(verify=True, timeout=10.0) as client:
            response = client.get(metadata_url, headers={"Origin": test_origin})

            assert response.status_code == HTTP_OK, (
                f"Metadata request failed: {response.status_code}"
            )

            # Check CORS headers in response
            assert "access-control-allow-origin" in response.headers, (
                "Missing Access-Control-Allow-Origin in response"
            )

            # When wildcard is configured, the response may be "*" instead of the specific origin
            allowed_origin = response.headers["access-control-allow-origin"]
            if self.cors_origins == ["*"]:
                assert allowed_origin in ["*", test_origin], (
                    f"CORS origin should be '*' or '{test_origin}', got '{allowed_origin}'"  # TODO: Break long line
                )
            else:
                assert allowed_origin == test_origin, (
                    f"CORS origin mismatch, expected '{test_origin}', got '{allowed_origin}'"  # TODO: Break long line
                )

            # Check exposed headers
            if "access-control-expose-headers" in response.headers:
                exposed_headers = response.headers[
                    "access-control-expose-headers"
                ].lower()
                # Auth service exposes these headers
                assert any(
                    h in exposed_headers
                    for h in ["x-user-id", "x-user-name", "x-auth-token"]
                ), "Auth headers not exposed in CORS"

    def test_auth_health_endpoint_cors(self):
        """Test that OAuth discovery endpoint also has CORS headers."""
        health_url = (
            f"https://auth.{self.base_domain}/.well-known/oauth-authorization-server"
        )

        # If CORS is set to wildcard, use a test origin
        test_origin = "https://example.com" if self.cors_origins == ["*"] else self.cors_origins[0]

        with httpx.Client(verify=True, timeout=10.0) as client:
            response = client.get(health_url, headers={"Origin": test_origin})

            assert response.status_code == HTTP_OK, "OAuth discovery check failed"

            # OAuth discovery endpoint should also have CORS headers
            assert "access-control-allow-origin" in response.headers, (
                "OAuth discovery endpoint missing CORS headers"
            )

            # When wildcard is configured, the response may be "*" instead of the specific origin
            allowed_origin = response.headers["access-control-allow-origin"]
            if self.cors_origins == ["*"]:
                assert allowed_origin in ["*", test_origin], (
                    f"CORS origin should be '*' or '{test_origin}', got '{allowed_origin}'"  # TODO: Break long line
                )

    def test_cors_headers_without_origin(self):
        """Test that requests without Origin header still work."""
        metadata_url = (
            f"https://auth.{self.base_domain}/.well-known/oauth-authorization-server"
        )

        with httpx.Client(verify=True, timeout=10.0) as client:
            response = client.get(metadata_url)

            # Should still work without Origin header
            assert response.status_code == HTTP_OK, (
                f"Request failed without Origin header: {response.status_code}"
            )

    def test_cors_blocks_unauthorized_origins(self):
        """Test that CORS blocks requests from unauthorized origins."""
        # Skip this test if CORS is set to wildcard
        if "*" in self.cors_origins:
            pytest.skip("CORS wildcard (*) allows all origins")

        metadata_url = (
            f"https://auth.{self.base_domain}/.well-known/oauth-authorization-server"
        )

        # Create an origin that is NOT in the configured list
        test_unauthorized_origin = "https://definitely-not-authorized-origin-12345.com"

        # Make sure it's not accidentally in the allowed list
        if test_unauthorized_origin in self.cors_origins:
            pytest.skip("Test origin is actually authorized")

        with httpx.Client(verify=True, timeout=10.0) as client:
            # Preflight should not include this origin in the response
            response = client.options(
                metadata_url,
                headers={
                    "Origin": test_unauthorized_origin,
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "content-type",
                },
            )

            # Should either not have CORS headers or have different origin
            if "access-control-allow-origin" in response.headers:
                allowed_origin = response.headers["access-control-allow-origin"]
                assert allowed_origin != test_unauthorized_origin, (
                    "CORS allowed unauthorized origin!"
                )
