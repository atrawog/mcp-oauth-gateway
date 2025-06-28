"""Test utilities for speeding up fetch tests by using local services.

This module provides utilities to use local MCP services (like echo) instead of
fetching external URLs, which significantly speeds up test execution.
"""

import os

from .test_constants import AUTH_BASE_URL
from .test_constants import MCP_TESTING_URL


def get_local_test_url() -> str:
    """Get a local MCP service URL for testing instead of external URLs.

    Returns the first available URL in this order:
    1. MCP_TESTING_URL (if set)
    2. AUTH_BASE_URL (our auth service home page)

    The auth service returns an HTML error page with "MCP OAuth Gateway"
    when accessed without proper auth headers.
    """
    if MCP_TESTING_URL:
        return MCP_TESTING_URL

    # Use the auth service base URL - it returns an HTML error page
    # with "MCP OAuth Gateway" when accessed without auth
    return AUTH_BASE_URL


def get_mcp_gateway_test_content() -> dict:
    """Get test content that simulates a successful MCP fetch response.

    This returns a response that includes 'MCP OAuth Gateway' to verify
    we're hitting our services, not external ones.
    """
    return {
        "content": [
            {
                "type": "text",
                "text": """<html>
<head><title>MCP OAuth Gateway Test Response</title></head>
<body>
<h1>MCP OAuth Gateway - Test Content</h1>
<p>This is a test response from the MCP OAuth Gateway system.</p>
<p>If you see this, the authentication and routing are working correctly!</p>
</body>
</html>""",
            },
        ],
        "mimeType": "text/html",
        "url": get_local_test_url(),
    }


def convert_fetch_url_to_local(url: str) -> str:
    """Convert external fetch URLs to local test URLs.

    This helps speed up tests by avoiding external network calls.
    Common conversions:
    - https://example.com -> local test URL
    - http://example.com -> local test URL
    - Any external URL -> local test URL
    """
    # List of external domains we want to replace
    external_domains = ["example.com", "httpbin.org", "google.com", "github.com"]

    # Check if URL contains any external domain
    for domain in external_domains:
        if domain in url:
            return get_local_test_url()

    # If it's already a local URL (contains our BASE_DOMAIN), keep it
    base_domain = os.getenv("BASE_DOMAIN", "")
    if base_domain and base_domain in url:
        return url

    # For any other external URL, use local test URL
    if url.startswith(("http://", "https://")):
        # Assume it's external if we don't recognize it
        return get_local_test_url()

    return url


def create_echo_test_request(
    message: str = "Test from MCP OAuth Gateway - Verifying authentication and routing",
) -> dict:
    """Create an echo service test request that will return quickly.

    The echo service just echoes back what we send, making it perfect
    for fast testing without external dependencies. The default message
    includes "MCP OAuth Gateway" for easy verification.
    """
    return {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": "echo", "arguments": {"message": message}},
        "id": "echo-test-1",
    }


def create_local_fetch_request(url: str | None = None) -> dict:
    """Create a fetch request that uses local services instead of external URLs.

    This is a drop-in replacement for fetch requests that would normally
    hit external services like example.com.
    """
    local_url = url if url else get_local_test_url()

    # Convert any external URL to local
    local_url = convert_fetch_url_to_local(local_url)

    return {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": "fetch", "arguments": {"url": local_url}},
        "id": "fetch-local-1",
    }


def verify_mcp_gateway_response(response_text: str) -> bool:
    """Verify that the response came from our MCP OAuth Gateway.

    This checks for known strings that indicate we're hitting our
    own services, not external ones.
    """
    mcp_indicators = [
        "MCP OAuth Gateway",
        "Model Context Protocol",
        "OAuth Gateway",
        "mcp-oauth",
        "auth.atratest.org",  # Our auth service domain
        "echo-stateless.atratest.org",  # Our echo service domain
        "authorization_endpoint",  # OAuth metadata
        "token_endpoint",  # OAuth metadata
        "registration_endpoint",  # OAuth metadata
        "traefik",  # Our reverse proxy
        "forwardauth",  # Our auth middleware
        "invalid_request",  # OAuth error from our services
        "Missing Authorization header",  # Error from our auth middleware
        "robots.txt",  # Fetch service checking robots.txt on our domain
    ]

    response_lower = response_text.lower()
    return any(indicator.lower() in response_lower for indicator in mcp_indicators)
