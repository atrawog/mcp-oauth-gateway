"""
Sacred Test Constants - Following Commandment 4: Configure Only Through .env Files
NO HARDCODED VALUES! NO DEFAULTS! ALL configuration MUST come from environment variables.

According to CLAUDE.md: "No defaults in code - Every value must be explicitly blessed!"
Tests should use the SAME .env file as the application!
"""
import os

def _get_env_or_fail(key: str) -> str:
    """Get environment variable or fail with clear error message"""
    value = os.getenv(key)
    if value is None:
        raise ValueError(
            f"SACRED VIOLATION! Environment variable {key} is not set. "
            f"All configuration MUST come from .env files. "
            f"No hardcoded defaults allowed! Add {key} to your .env file."
        )
    return value

def _get_env_int_or_fail(key: str) -> int:
    """Get environment variable as integer or fail"""
    value = _get_env_or_fail(key)
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Environment variable {key} must be an integer, got: {value}")

def _get_env_float_or_fail(key: str) -> float:
    """Get environment variable as float or fail"""
    value = _get_env_or_fail(key)
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Environment variable {key} must be a float, got: {value}")

# Domain Configuration - From main .env
BASE_DOMAIN = _get_env_or_fail("BASE_DOMAIN")
AUTH_BASE_URL = f"https://auth.{BASE_DOMAIN}"
MCP_FETCH_URL = f"https://fetch.{BASE_DOMAIN}"
MCP_FETCHS_URL = f"https://fetchs.{BASE_DOMAIN}"
MCP_FILESYSTEM_URL = f"https://filesystem.{BASE_DOMAIN}"
MCP_MEMORY_URL = f"https://memory.{BASE_DOMAIN}"

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
TEST_CALLBACK_URL = _get_env_or_fail("TEST_CALLBACK_URL")
TEST_CLIENT_NAME = _get_env_or_fail("TEST_CLIENT_NAME")
TEST_CLIENT_SCOPE = _get_env_or_fail("TEST_CLIENT_SCOPE")
TEST_REDIRECT_URI = _get_env_or_fail("TEST_REDIRECT_URI")
TEST_INVALID_REDIRECT_URI = _get_env_or_fail("TEST_INVALID_REDIRECT_URI")

# Health Check Configuration - From main .env
HEALTH_CHECK_TIMEOUT = _get_env_int_or_fail("HEALTH_CHECK_TIMEOUT")
HEALTH_CHECK_INTERVAL = _get_env_int_or_fail("HEALTH_CHECK_INTERVAL")

# Access Control Configuration - From main .env
ALLOWED_GITHUB_USERS = _get_env_or_fail("ALLOWED_GITHUB_USERS").split(",")

# MCP Everything Configuration - From main .env
MCP_EVERYTHING_TESTS_ENABLED = os.getenv("MCP_EVERYTHING_TESTS_ENABLED", "false").lower() == "true"
MCP_EVERYTHING_URLS = os.getenv("MCP_EVERYTHING_URLS", "").split(",") if os.getenv("MCP_EVERYTHING_URLS") else []

# MCP Fetch Configuration - From main .env
MCP_FETCH_TESTS_ENABLED = os.getenv("MCP_FETCH_TESTS_ENABLED", "false").lower() == "true"
MCP_FETCH_URLS = os.getenv("MCP_FETCH_URLS", "").split(",") if os.getenv("MCP_FETCH_URLS") else []

# MCP Fetchs Configuration - From main .env
MCP_FETCHS_TESTS_ENABLED = os.getenv("MCP_FETCHS_TESTS_ENABLED", "false").lower() == "true"
MCP_FETCHS_URLS = os.getenv("MCP_FETCHS_URLS", "").split(",") if os.getenv("MCP_FETCHS_URLS") else []

# MCP Filesystem Configuration - From main .env
MCP_FILESYSTEM_TESTS_ENABLED = os.getenv("MCP_FILESYSTEM_TESTS_ENABLED", "false").lower() == "true"
MCP_FILESYSTEM_URLS = os.getenv("MCP_FILESYSTEM_URLS", "").split(",") if os.getenv("MCP_FILESYSTEM_URLS") else []

# MCP Memory Configuration - From main .env
MCP_MEMORY_TESTS_ENABLED = os.getenv("MCP_MEMORY_TESTS_ENABLED", "false").lower() == "true"
MCP_MEMORY_URLS = os.getenv("MCP_MEMORY_URLS", "").split(",") if os.getenv("MCP_MEMORY_URLS") else []