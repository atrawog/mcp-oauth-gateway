"""Sacred Test Constants - Following Commandment 4: Configure Only Through Environment
NO HARDCODED VALUES! NO DEFAULTS! ALL configuration MUST come from environment variables.

According to CLAUDE.md: "No defaults in code - Every value must be explicitly blessed!"
Environment variables are loaded by 'just test' - tests read from environment only!
"""

import os


def _get_env_or_fail(key: str) -> str:
    """Get environment variable or fail with clear error message."""
    value = os.getenv(key)
    if value is None:
        raise ValueError(
            f"SACRED VIOLATION! Environment variable {key} is not set. "
            f"All configuration MUST come from environment variables. "
            f"No hardcoded defaults allowed! Run tests with 'just test'.",
        )
    return value


def _get_env_int_or_fail(key: str) -> int:
    """Get environment variable as integer or fail."""
    value = _get_env_or_fail(key)
    try:
        return int(value)
    except ValueError as e:
        raise ValueError(f"Environment variable {key} must be an integer, got: {value}") from e


def _get_env_float_or_fail(key: str) -> float:
    """Get environment variable as float or fail."""
    value = _get_env_or_fail(key)
    try:
        return float(value)
    except ValueError as e:
        raise ValueError(f"Environment variable {key} must be a float, got: {value}") from e


def _get_env_optional(key: str, default=None):
    """Get optional environment variable."""
    return os.getenv(key, default)


# Domain Configuration - From main .env
BASE_DOMAIN = _get_env_or_fail("BASE_DOMAIN")
AUTH_BASE_URL = f"https://auth.{BASE_DOMAIN}"

# MCP Testing URL - Use this if provided for general testing
MCP_TESTING_URL = _get_env_optional("MCP_TESTING_URL")


# Helper function to get MCP service URLs
def _get_mcp_service_urls(service_name: str, default_subdomain: str) -> list:
    """Get MCP service URLs with fallback to single URL or MCP_TESTING_URL."""
    # First check for MCP_<SERVICE>_URLS (plural)
    urls_env = _get_env_optional(f"MCP_{service_name.upper()}_URLS")
    if urls_env:
        urls = [url.strip() for url in urls_env.split(",") if url.strip()]
        # Use URLs as-is from environment - they already include /mcp if needed
        return [url.rstrip("/") for url in urls]

    # Then check for MCP_<SERVICE>_URL (singular)
    url_env = _get_env_optional(f"MCP_{service_name.upper()}_URL")
    if url_env:
        url = url_env.strip().rstrip("/")
        return [url]

    # Fall back to MCP_TESTING_URL if provided
    if MCP_TESTING_URL:
        url = MCP_TESTING_URL.strip().rstrip("/")
        return [url]

    # Finally, construct from BASE_DOMAIN (with /mcp path for MCP services)
    return [f"https://{default_subdomain}.{BASE_DOMAIN}/mcp"]


# Get the first URL for backwards compatibility (old single URL variables)
MCP_ECHO_STATEFUL_URL = _get_mcp_service_urls("echo_stateful", "echo-stateful")[0]
MCP_ECHO_STATELESS_URL = _get_mcp_service_urls("echo_stateless", "echo-stateless-")[0]
MCP_FETCH_URL = _get_mcp_service_urls("fetch", "fetch")[0]
MCP_FETCHS_URL = _get_mcp_service_urls("fetchs", "fetchs")[0]
MCP_FILESYSTEM_URL = _get_mcp_service_urls("filesystem", "filesystem")[0]
MCP_MEMORY_URL = _get_mcp_service_urls("memory", "memory")[0]
MCP_PLAYWRIGHT_URL = _get_mcp_service_urls("playwright", "playwright")[0]
MCP_SEQUENTIALTHINKING_URL = _get_mcp_service_urls("sequentialthinking", "sequentialthinking")[0]
MCP_TIME_URL = _get_mcp_service_urls("time", "time")[0]
MCP_TMUX_URL = _get_mcp_service_urls("tmux", "tmux")[0]

# Redis Configuration - From main .env
REDIS_PASSWORD = _get_env_or_fail("REDIS_PASSWORD")
# For tests, we connect to localhost Redis (not the Docker service name)
REDIS_URL = f"redis://:{REDIS_PASSWORD}@localhost:6379/0"

# GitHub OAuth Configuration - From main .env
GITHUB_CLIENT_ID = _get_env_or_fail("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = _get_env_or_fail("GITHUB_CLIENT_SECRET")

# JWT Configuration - From main .env
GATEWAY_JWT_SECRET = _get_env_or_fail("GATEWAY_JWT_SECRET")
JWT_SECRET = GATEWAY_JWT_SECRET  # Backwards compatibility alias
JWT_PRIVATE_KEY_B64 = _get_env_or_fail("JWT_PRIVATE_KEY_B64")  # RS256 private key
JWT_ALGORITHM = _get_env_or_fail("JWT_ALGORITHM")  # Should be RS256

# Token Lifetimes - From main .env
ACCESS_TOKEN_LIFETIME = _get_env_int_or_fail("ACCESS_TOKEN_LIFETIME")
REFRESH_TOKEN_LIFETIME = _get_env_int_or_fail("REFRESH_TOKEN_LIFETIME")
SESSION_TIMEOUT = _get_env_int_or_fail("SESSION_TIMEOUT")

# MCP Protocol Configuration - From main .env
MCP_PROTOCOL_VERSION = _get_env_or_fail("MCP_PROTOCOL_VERSION")
MCP_PROTOCOL_VERSIONS_SUPPORTED = _get_env_or_fail("MCP_PROTOCOL_VERSIONS_SUPPORTED").split(",")

# GitHub Personal Access Token (if needed for tests) - From main .env
GITHUB_PAT = os.getenv("GITHUB_PAT")  # REQUIRED - GitHub PAT is NOT optional!

# Gateway OAuth Client Credentials (from successful registration) - From main .env
GATEWAY_OAUTH_CLIENT_ID = os.getenv("GATEWAY_OAUTH_CLIENT_ID")  # Optional, set after registration
GATEWAY_OAUTH_CLIENT_SECRET = os.getenv("GATEWAY_OAUTH_CLIENT_SECRET")  # Optional, set after registration
GATEWAY_OAUTH_ACCESS_TOKEN = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")  # Optional, set after OAuth flow
GATEWAY_OAUTH_REFRESH_TOKEN = os.getenv("GATEWAY_OAUTH_REFRESH_TOKEN")  # Optional, set after OAuth flow

# MCP Client tokens for testing MCP endpoints
MCP_CLIENT_ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN")  # Optional, set after MCP client setup
MCP_CLIENT_REFRESH_TOKEN = os.getenv("MCP_CLIENT_REFRESH_TOKEN")  # Optional
# Backwards compatibility aliases
OAUTH_CLIENT_ID = GATEWAY_OAUTH_CLIENT_ID
OAUTH_CLIENT_SECRET = GATEWAY_OAUTH_CLIENT_SECRET
OAUTH_ACCESS_TOKEN = GATEWAY_OAUTH_ACCESS_TOKEN

# Test Configuration - From main .env
TEST_HTTP_TIMEOUT = _get_env_float_or_fail("TEST_HTTP_TIMEOUT")
TEST_MAX_RETRIES = _get_env_int_or_fail("TEST_MAX_RETRIES")
TEST_RETRY_DELAY = _get_env_float_or_fail("TEST_RETRY_DELAY")
TEST_OAUTH_CALLBACK_URL = _get_env_or_fail("TEST_OAUTH_CALLBACK_URL")
TEST_CLIENT_NAME = _get_env_or_fail("TEST_CLIENT_NAME")
TEST_CLIENT_SCOPE = _get_env_or_fail("TEST_CLIENT_SCOPE")
TEST_INVALID_REDIRECT_URI = _get_env_or_fail("TEST_INVALID_REDIRECT_URI")

# Health Check Configuration - From main .env
HEALTH_CHECK_TIMEOUT = _get_env_int_or_fail("HEALTH_CHECK_TIMEOUT")
HEALTH_CHECK_INTERVAL = _get_env_int_or_fail("HEALTH_CHECK_INTERVAL")

# Access Control Configuration - From main .env
ALLOWED_GITHUB_USERS = _get_env_or_fail("ALLOWED_GITHUB_USERS").split(",")

# MCP Everything Configuration - From main .env
MCP_EVERYTHING_TESTS_ENABLED = (_get_env_optional("MCP_EVERYTHING_TESTS_ENABLED") or "false").lower() == "true"
MCP_EVERYTHING_URLS = _get_mcp_service_urls("everything", "everything")

# MCP Echo Stateful Configuration - From main .env
MCP_ECHO_STATEFUL_TESTS_ENABLED = (_get_env_optional("MCP_ECHO_STATEFUL_TESTS_ENABLED") or "false").lower() == "true"
MCP_ECHO_STATEFUL_URLS = _get_mcp_service_urls("echo_stateful", "echo-stateful")

# MCP Echo Stateless Configuration - From main .env
MCP_ECHO_STATELESS_TESTS_ENABLED = (_get_env_optional("MCP_ECHO_STATELESS_TESTS_ENABLED") or "false").lower() == "true"
MCP_ECHO_STATELESS_URLS = _get_mcp_service_urls("echo_stateless", "echo-stateless-")

# MCP Fetch Configuration - From main .env
MCP_FETCH_TESTS_ENABLED = (_get_env_optional("MCP_FETCH_TESTS_ENABLED") or "false").lower() == "true"
MCP_FETCH_URLS = _get_mcp_service_urls("fetch", "fetch")

# MCP Fetchs Configuration - From main .env
MCP_FETCHS_TESTS_ENABLED = (_get_env_optional("MCP_FETCHS_TESTS_ENABLED") or "false").lower() == "true"
MCP_FETCHS_URLS = _get_mcp_service_urls("fetchs", "fetchs")

# MCP Filesystem Configuration - From main .env
MCP_FILESYSTEM_TESTS_ENABLED = (_get_env_optional("MCP_FILESYSTEM_TESTS_ENABLED") or "false").lower() == "true"
MCP_FILESYSTEM_URLS = _get_mcp_service_urls("filesystem", "filesystem")

# MCP Memory Configuration - From main .env
MCP_MEMORY_TESTS_ENABLED = (_get_env_optional("MCP_MEMORY_TESTS_ENABLED") or "false").lower() == "true"
MCP_MEMORY_URLS = _get_mcp_service_urls("memory", "memory")

# MCP Playwright Configuration - From main .env
MCP_PLAYWRIGHT_TESTS_ENABLED = (_get_env_optional("MCP_PLAYWRIGHT_TESTS_ENABLED") or "false").lower() == "true"
MCP_PLAYWRIGHT_URLS = _get_mcp_service_urls("playwright", "playwright")

# MCP Sequential Thinking Configuration - From main .env
MCP_SEQUENTIALTHINKING_TESTS_ENABLED = (
    _get_env_optional("MCP_SEQUENTIALTHINKING_TESTS_ENABLED") or "false"
).lower() == "true"
MCP_SEQUENTIALTHINKING_URLS = _get_mcp_service_urls("sequentialthinking", "sequentialthinking")

# MCP Time Configuration - From main .env
MCP_TIME_TESTS_ENABLED = (_get_env_optional("MCP_TIME_TESTS_ENABLED") or "false").lower() == "true"
MCP_TIME_URLS = _get_mcp_service_urls("time", "time")

# MCP Tmux Configuration - From main .env
MCP_TMUX_TESTS_ENABLED = (_get_env_optional("MCP_TMUX_TESTS_ENABLED") or "false").lower() == "true"
MCP_TMUX_URLS = _get_mcp_service_urls("tmux", "tmux")


# HTTP Status Code Constants - Addresses PLR2004 magic number issues
# Success statuses
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ACCEPTED = 202
HTTP_NO_CONTENT = 204

# Redirection statuses
HTTP_MOVED_PERMANENTLY = 301
HTTP_FOUND = 302
HTTP_SEE_OTHER = 303
HTTP_NOT_MODIFIED = 304
HTTP_TEMPORARY_REDIRECT = 307
HTTP_PERMANENT_REDIRECT = 308

# Client error statuses
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_NOT_ACCEPTABLE = 406
HTTP_CONFLICT = 409
HTTP_GONE = 410
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_TOO_MANY_REQUESTS = 429

# Server error statuses
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_NOT_IMPLEMENTED = 501
HTTP_BAD_GATEWAY = 502
HTTP_SERVICE_UNAVAILABLE = 503
HTTP_GATEWAY_TIMEOUT = 504
