"""
Sacred Test Configuration - Following the divine commandment of NO MOCKING!
All tests run against real deployed services
NO HARDCODED VALUES - Everything from .env per Commandment 4!
"""
import pytest
import httpx
import asyncio
import os
import sys
import time
import json
import base64
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Tuple, Optional
from pathlib import Path
from dotenv import load_dotenv

# SACRED LAW: Load .env file BEFORE importing test_constants
# This ensures all environment variables are available!
# Use explicit path to ensure .env is found regardless of working directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Import all configuration from test_constants
from .test_constants import (
    AUTH_BASE_URL, 
    MCP_FETCH_URL,
    SESSION_TIMEOUT,
    TEST_HTTP_TIMEOUT,
    TEST_MAX_RETRIES,
    TEST_RETRY_DELAY,
    TEST_CALLBACK_URL,
    TEST_CLIENT_NAME,
    TEST_CLIENT_SCOPE,
    GATEWAY_OAUTH_ACCESS_TOKEN
)

# MCP Client tokens for external client testing
MCP_CLIENT_ACCESS_TOKEN = os.getenv("MCP_CLIENT_ACCESS_TOKEN")
MCP_CLIENT_ID = os.getenv("MCP_CLIENT_ID")
MCP_CLIENT_SECRET = os.getenv("MCP_CLIENT_SECRET")

# pytest-asyncio handles event loop automatically with asyncio_mode = auto


def check_token_expiry(token: str) -> Tuple[bool, int]:
    """Check if JWT token is expired. Returns (is_valid, seconds_until_expiry)"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return False, 0
        
        # Decode payload
        payload_part = parts[1]
        payload_part += '=' * (4 - len(payload_part) % 4)
        payload_json = base64.urlsafe_b64decode(payload_part)
        payload = json.loads(payload_json)
        
        exp = payload.get('exp', 0)
        now = int(time.time())
        
        if exp <= now:
            return False, 0
        else:
            return True, exp - now
    except Exception:
        return False, 0


def pytest_configure(config):
    """Run token validation BEFORE any test collection or execution"""
    import sys
    
    # Force output to be visible
    sys.stdout.flush()
    sys.stderr.flush()
    
    print("\n" + "=" * 60, file=sys.stderr)
    print("🔐 PRE-TEST TOKEN VALIDATION", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Check Gateway OAuth token exists
    gateway_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    if not gateway_token:
        print("❌ No GATEWAY_OAUTH_ACCESS_TOKEN found! Run: just generate-github-token", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        pytest.exit("Token validation failed", returncode=1)
    
    # Check JWT structure and expiry
    is_valid, ttl = check_token_expiry(gateway_token)
    if not is_valid:
        print("❌ Gateway token is expired! Run: just generate-github-token", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        pytest.exit("Token validation failed", returncode=1)
    
    # Verify token with auth service using synchronous request
    import requests
    import time
    
    # Try to verify token with retries (auth service might be starting up)
    max_retries = 3
    retry_delay = 2
    token_valid = False
    
    for attempt in range(max_retries):
        try:
            verify_response = requests.get(
                f"{AUTH_BASE_URL}/verify",
                headers={"Authorization": f"Bearer {gateway_token}"},
                timeout=10
            )
            
            if verify_response.status_code == 401:
                # Token is invalid - abort immediately
                print("❌ Gateway token is not recognized by auth service!", file=sys.stderr)
                print("   Run: just generate-github-token", file=sys.stderr)
                print("=" * 60, file=sys.stderr)
                pytest.exit("Token validation failed - invalid gateway token", returncode=1)
            elif verify_response.status_code != 200:
                print(f"❌ Failed to verify gateway token: {verify_response.status_code}", file=sys.stderr)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                print("=" * 60, file=sys.stderr)
                pytest.exit("Token validation failed", returncode=1)
            else:
                print(f"✅ Gateway token valid for {ttl/3600:.1f} hours and recognized by auth service", file=sys.stderr)
                token_valid = True
                break
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Cannot connect to auth service (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                time.sleep(retry_delay)
                continue
            else:
                print(f"❌ Cannot connect to auth service at {AUTH_BASE_URL}", file=sys.stderr)
                print("   Make sure services are running: just up", file=sys.stderr)
                print("=" * 60, file=sys.stderr)
                pytest.exit("Cannot connect to auth service", returncode=1)
        except requests.exceptions.Timeout as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Auth service timeout (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                time.sleep(retry_delay)
                continue
            else:
                print(f"❌ Auth service timeout - service may be overloaded", file=sys.stderr)
                print("=" * 60, file=sys.stderr)
                pytest.exit("Auth service timeout", returncode=1)
        except SystemExit:
            # Re-raise SystemExit from pytest.exit() calls
            raise
        except Exception as e:
            # Other exceptions (JSON decode errors, etc)
            print(f"❌ Unexpected error verifying token: {e}", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            pytest.exit(f"Token verification error: {e}", returncode=1)
    
    # Check GitHub PAT
    github_pat = os.getenv("GITHUB_PAT")
    if not github_pat or github_pat.strip() == "":
        print("❌ No GitHub PAT configured! GitHub PAT is REQUIRED!", file=sys.stderr)
        print("   Run: just generate-github-token", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        pytest.exit("Token validation failed", returncode=1)
    
    # Quick validation of other critical variables
    critical_vars = {
        "BASE_DOMAIN": "Base domain for services",
        "GITHUB_CLIENT_ID": "GitHub OAuth client ID",
        "GITHUB_CLIENT_SECRET": "GitHub OAuth client secret",
        "GATEWAY_JWT_SECRET": "JWT signing secret",
        "JWT_PRIVATE_KEY_B64": "RSA private key for RS256 JWT signing",
        "JWT_ALGORITHM": "JWT algorithm (should be RS256)"
    }
    
    missing = []
    for var, desc in critical_vars.items():
        if not os.getenv(var):
            missing.append(f"  - {var}: {desc}")
    
    if missing:
        print("❌ Critical environment variables missing:", file=sys.stderr)
        for m in missing:
            print(m, file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(1)  # Exit immediately with error code
    
    # Validate JWT_ALGORITHM is RS256
    jwt_algorithm = os.getenv("JWT_ALGORITHM")
    if jwt_algorithm != "RS256":
        print(f"❌ JWT_ALGORITHM must be RS256, but found: {jwt_algorithm}", file=sys.stderr)
        print("   Update .env file to set JWT_ALGORITHM=RS256", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(1)  # Exit immediately with error code
    
    # Validate JWT_PRIVATE_KEY_B64 is a valid base64-encoded RSA key
    jwt_private_key_b64 = os.getenv("JWT_PRIVATE_KEY_B64")
    if jwt_private_key_b64:
        try:
            import base64
            key_bytes = base64.b64decode(jwt_private_key_b64)
            if not key_bytes.startswith(b'-----BEGIN'):
                print("❌ JWT_PRIVATE_KEY_B64 does not appear to be a valid PEM-encoded key", file=sys.stderr)
                print("   Run: just generate-rsa-keys", file=sys.stderr)
                print("=" * 60, file=sys.stderr)
                pytest.exit("Token validation failed", returncode=1)
        except Exception as e:
            print(f"❌ JWT_PRIVATE_KEY_B64 is not valid base64: {e}", file=sys.stderr)
            print("   Run: just generate-rsa-keys", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            sys.exit(1)  # Exit immediately with error code
    
    # Summary of validation status
    if token_valid:
        print("✅ All critical tokens and configuration validated!", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
    else:
        # This should never be reached because we exit immediately on any token failure
        print("❌ CRITICAL ERROR: Token validation logic error!", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        pytest.exit("Token validation logic error", returncode=1)


def update_env_file(key: str, value: str):
    """Update a key in the .env file"""
    env_file = Path(".env")
    lines = []
    found = False
    
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
    
    if not found:
        lines.append(f"{key}={value}\n")
    
    with open(env_file, 'w') as f:
        f.writelines(lines)

@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provides an async HTTP client for tests"""
    # Use timeout from test_constants - already validated!
    async with httpx.AsyncClient(timeout=TEST_HTTP_TIMEOUT) as client:
        yield client

@pytest.fixture(scope="session", autouse=True)
async def ensure_services_ready():
    """Ensure all services are ready before ANY tests run - replaces scripts/check_services_ready.py"""
    print("\n" + "=" * 60)
    print("Pre-test Service Check")
    print("=" * 60)
    
    # Check Docker services
    import subprocess
    try:
        # Check if services are running
        result = subprocess.run(
            ["docker", "compose", "ps", "--services", "--filter", "status=running"],
            capture_output=True,
            text=True,
            check=True
        )
        running_services = set(result.stdout.strip().split('\n'))
        required_services = {"traefik", "auth", "redis", "mcp-fetch"}
        
        missing = required_services - running_services
        if missing:
            print(f"❌ Required services not running: {missing}", file=sys.stderr)
            print("Run: just up", file=sys.stderr)
            pytest.fail("Required services not running")
        
        print("✅ All required Docker services are running")
        
        # Wait for health checks
        max_wait = 60
        start_time = time.time()
        while time.time() - start_time < max_wait:
            result = subprocess.run(
                ["docker", "compose", "ps", "--format", "json"],
                capture_output=True,
                text=True
            )
            
            all_healthy = True
            for line in result.stdout.strip().split('\n'):
                if line:
                    service_info = json.loads(line)
                    if service_info.get("Health", "") not in ["", "healthy"]:
                        all_healthy = False
                        break
            
            if all_healthy:
                print("✅ All services are healthy")
                break
            
            await asyncio.sleep(2)
        else:
            pytest.fail(f"❌ Services did not become healthy within {max_wait} seconds")
            
    except subprocess.CalledProcessError as e:
        pytest.fail(f"❌ Failed to check Docker services: {e}")
    except Exception as e:
        pytest.fail(f"❌ Unexpected error checking services: {e}")


@pytest.fixture(scope="session", autouse=True)
async def refresh_and_validate_tokens(ensure_services_ready):
    """Refresh and validate all tokens before tests - replaces scripts/refresh_tokens.py and validate_tokens.py"""
    print("\n" + "=" * 60)
    print("🔐 TOKEN REFRESH AND VALIDATION")
    print("=" * 60)
    
    # Check and refresh Gateway OAuth token
    gateway_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
    if not gateway_token:
        pytest.fail("❌ No GATEWAY_OAUTH_ACCESS_TOKEN found! Run: just generate-github-token")
    
    # First check JWT expiry
    is_valid, ttl = check_token_expiry(gateway_token)
    if not is_valid:
        pytest.fail("❌ Gateway token is expired! Run: just generate-github-token")
    
    # Then verify token is actually valid in the auth service
    token_needs_refresh = False
    async with httpx.AsyncClient(timeout=10.0) as client:
        verify_response = await client.get(
            f"{AUTH_BASE_URL}/verify",
            headers={"Authorization": f"Bearer {gateway_token}"}
        )
        
        if verify_response.status_code == 401:
            print("⚠️  Gateway token is not recognized by auth service - will attempt refresh")
            token_needs_refresh = True
        elif verify_response.status_code != 200:
            pytest.fail(f"❌ Failed to verify gateway token: {verify_response.status_code}")
    
    if ttl < 3600 or token_needs_refresh:  # Less than 1 hour OR token invalid
        # Try to refresh
        refresh_token = os.getenv("GATEWAY_OAUTH_REFRESH_TOKEN")
        if not refresh_token or refresh_token == "None":
            print("⚠️  No valid refresh token available - cannot auto-refresh")
            if token_needs_refresh:
                pytest.fail("❌ Gateway token is invalid and no refresh token available! Run: just generate-github-token")
            else:
                pytest.fail("❌ Gateway token expires soon and no refresh token! Run: just generate-github-token")
        
        # Refresh the token
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{AUTH_BASE_URL}/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": os.getenv("GATEWAY_OAUTH_CLIENT_ID"),
                    "client_secret": os.getenv("GATEWAY_OAUTH_CLIENT_SECRET")
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                new_token = data["access_token"]
                update_env_file("GATEWAY_OAUTH_ACCESS_TOKEN", new_token)
                os.environ["GATEWAY_OAUTH_ACCESS_TOKEN"] = new_token
                
                if "refresh_token" in data:
                    update_env_file("GATEWAY_OAUTH_REFRESH_TOKEN", data["refresh_token"])
                    os.environ["GATEWAY_OAUTH_REFRESH_TOKEN"] = data["refresh_token"]
                    
                print("✅ Gateway token refreshed successfully")
            else:
                error_detail = response.text
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", {}).get("error_description", error_detail)
                except:
                    pass
                pytest.fail(f"❌ Failed to refresh gateway token: {response.status_code} - {error_detail}")
    else:
        print(f"✅ Gateway token valid for {ttl/3600:.1f} hours")
    
    # Check GitHub PAT
    github_pat = os.getenv("GITHUB_PAT")
    if not github_pat or github_pat.strip() == "":
        pytest.fail("❌ No GitHub PAT configured! GitHub PAT is REQUIRED! Run: just generate-github-token")
    
    # Validate GitHub PAT
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {github_pat}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ GitHub PAT is valid for user: {user_data.get('login')}")
    elif response.status_code == 401:
        pytest.fail("❌ GitHub PAT is invalid or expired! Run: just generate-github-token")
    else:
        pytest.fail(f"❌ GitHub API returned unexpected status: {response.status_code}")
    
    # Ensure MCP client token
    mcp_token = os.getenv("MCP_CLIENT_ACCESS_TOKEN")
    if mcp_token:
        is_valid, ttl = check_token_expiry(mcp_token)
        if is_valid and ttl > 300:
            # Verify token is actually valid in the auth service
            async with httpx.AsyncClient(timeout=10.0) as client:
                verify_response = await client.get(
                    f"{AUTH_BASE_URL}/verify",
                    headers={"Authorization": f"Bearer {mcp_token}"}
                )
                
                if verify_response.status_code == 200:
                    print(f"✅ MCP client token valid for {ttl/3600:.1f} hours")
                else:
                    # Token not valid in auth service, use gateway token
                    gateway_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
                    update_env_file("MCP_CLIENT_ACCESS_TOKEN", gateway_token)
                    os.environ["MCP_CLIENT_ACCESS_TOKEN"] = gateway_token
                    print("✅ Updated MCP client token from gateway token (previous token not recognized by auth service)")
        else:
            # Use gateway token as MCP client token
            gateway_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
            update_env_file("MCP_CLIENT_ACCESS_TOKEN", gateway_token)
            os.environ["MCP_CLIENT_ACCESS_TOKEN"] = gateway_token
            print("✅ Updated MCP client token from gateway token")
    else:
        # Set MCP client token from gateway token
        gateway_token = os.getenv("GATEWAY_OAUTH_ACCESS_TOKEN")
        update_env_file("MCP_CLIENT_ACCESS_TOKEN", gateway_token)
        os.environ["MCP_CLIENT_ACCESS_TOKEN"] = gateway_token
        print("✅ Set MCP client token from gateway token")
    
    # Validate all required environment variables
    required_vars = {
        "GATEWAY_OAUTH_ACCESS_TOKEN": "Gateway OAuth access token",
        "MCP_CLIENT_ACCESS_TOKEN": "MCP client access token",
        "GITHUB_PAT": "GitHub Personal Access Token",
        "BASE_DOMAIN": "Base domain",
        "GITHUB_CLIENT_ID": "GitHub OAuth client ID",
        "GITHUB_CLIENT_SECRET": "GitHub OAuth client secret",
        "GATEWAY_JWT_SECRET": "JWT signing secret",
        "JWT_PRIVATE_KEY_B64": "RSA private key for RS256 JWT signing",
        "JWT_ALGORITHM": "JWT algorithm (should be RS256)",
        "GATEWAY_OAUTH_CLIENT_ID": "Gateway OAuth client ID",
        "GATEWAY_OAUTH_CLIENT_SECRET": "Gateway OAuth client secret"
    }
    
    all_valid = True
    for key, desc in required_vars.items():
        if not os.getenv(key):
            print(f"❌ Missing: {desc} ({key})")
            all_valid = False
    
    if not all_valid:
        pytest.fail("❌ Required environment variables are missing!")
    
    print("\n" + "=" * 60)
    print("✅ ALL TOKENS VALIDATED AND READY FOR TESTING!")
    print("=" * 60)


@pytest.fixture
async def wait_for_services(http_client: httpx.AsyncClient):
    """Wait for all services to be healthy before running tests"""
    services = [
        (AUTH_BASE_URL, "/health", 200),
        (MCP_FETCH_URL, "/mcp", 401)  # MCP endpoint returns 401 when auth is required
    ]
    
    # Use retry configuration from test_constants - already validated!
    
    for base_url, health_path, expected_status in services:
        url = f"{base_url}{health_path}"
        for attempt in range(TEST_MAX_RETRIES):
            try:
                response = await http_client.get(url)
                if response.status_code == expected_status:
                    print(f"✓ Service {base_url} is responding correctly (status: {expected_status})")
                    break
            except Exception as e:
                if attempt == TEST_MAX_RETRIES - 1:
                    pytest.fail(f"Service {base_url} failed to become healthy: {e}")
                await asyncio.sleep(TEST_RETRY_DELAY)

@pytest.fixture
async def registered_client(http_client: httpx.AsyncClient, wait_for_services) -> dict:
    """Register a test OAuth client dynamically - no hardcoded values!
    
    This fixture properly cleans up the registration using RFC 7592 DELETE endpoint.
    """
    # MUST have OAuth access token - test FAILS if not available
    assert GATEWAY_OAUTH_ACCESS_TOKEN, "GATEWAY_OAUTH_ACCESS_TOKEN not available - run: just generate-github-token"
    
    # Use test configuration from test_constants - already validated!
    
    registration_data = {
        "redirect_uris": [TEST_CALLBACK_URL],
        "client_name": TEST_CLIENT_NAME,
        "scope": TEST_CLIENT_SCOPE
    }
    
    response = await http_client.post(
        f"{AUTH_BASE_URL}/register",
        json=registration_data,
        headers={"Authorization": f"Bearer {GATEWAY_OAUTH_ACCESS_TOKEN}"}
    )
    
    assert response.status_code == 201, f"Client registration failed: {response.text}"
    client_data = response.json()
    
    # Yield the client data for the test to use
    yield client_data
    
    # Cleanup: Delete the client registration using RFC 7592
    if "registration_access_token" in client_data and "client_id" in client_data:
        try:
            delete_response = await http_client.delete(
                f"{AUTH_BASE_URL}/register/{client_data['client_id']}",
                headers={"Authorization": f"Bearer {client_data['registration_access_token']}"}
            )
            # 204 No Content is success, 404 is okay if already deleted
            if delete_response.status_code not in (204, 404):
                print(f"Warning: Failed to delete client {client_data['client_id']}: {delete_response.status_code}")
        except Exception as e:
            print(f"Warning: Error during client cleanup: {e}")

@pytest.fixture
def mcp_client_token():
    """Provides MCP client access token for external client testing"""
    if not MCP_CLIENT_ACCESS_TOKEN:
        pytest.fail("No MCP_CLIENT_ACCESS_TOKEN available - token refresh should have set this!")
    return MCP_CLIENT_ACCESS_TOKEN

@pytest.fixture
def mcp_client_credentials():
    """Provides MCP client credentials for external client testing"""
    if not MCP_CLIENT_ID or not MCP_CLIENT_SECRET:
        pytest.fail("No MCP client credentials available - token refresh should have set these!")
    return {
        "client_id": MCP_CLIENT_ID,
        "client_secret": MCP_CLIENT_SECRET,
        "access_token": MCP_CLIENT_ACCESS_TOKEN
    }

@pytest.fixture
async def mcp_authenticated_client(http_client: httpx.AsyncClient, mcp_client_token: str) -> httpx.AsyncClient:
    """Provides an HTTP client with MCP authentication headers pre-configured"""
    # Create a new client with auth headers
    http_client.headers["Authorization"] = f"Bearer {mcp_client_token}"
    return http_client

@pytest.fixture
def mcp_fetch_url():
    """Base URL for mcp-fetch service, with test skip logic."""
    from .test_constants import MCP_FETCH_TESTS_ENABLED, MCP_FETCH_URLS
    
    if not MCP_FETCH_TESTS_ENABLED:
        pytest.skip("MCP Fetch tests are disabled. Set MCP_FETCH_TESTS_ENABLED=true to enable.")
    if not MCP_FETCH_URLS:
        pytest.skip("MCP_FETCH_URLS environment variable not set")
    
    # Return first URL from the list
    return MCP_FETCH_URLS[0].replace('/mcp', '')  # Remove /mcp path if present

@pytest.fixture
def mcp_fetchs_url():
    """Base URL for mcp-fetchs service, with test skip logic."""
    from .test_constants import MCP_FETCHS_TESTS_ENABLED, MCP_FETCHS_URLS
    
    if not MCP_FETCHS_TESTS_ENABLED:
        pytest.skip("MCP Fetchs tests are disabled. Set MCP_FETCHS_TESTS_ENABLED=true to enable.")
    if not MCP_FETCHS_URLS:
        pytest.skip("MCP_FETCHS_URLS environment variable not set")
    
    # Return first URL from the list
    return MCP_FETCHS_URLS[0].replace('/mcp', '')  # Remove /mcp path if present

@pytest.fixture
def mcp_filesystem_url():
    """Base URL for mcp-filesystem service, with test skip logic."""
    from .test_constants import MCP_FILESYSTEM_TESTS_ENABLED, MCP_FILESYSTEM_URLS
    
    if not MCP_FILESYSTEM_TESTS_ENABLED:
        pytest.skip("MCP Filesystem tests are disabled. Set MCP_FILESYSTEM_TESTS_ENABLED=true to enable.")
    if not MCP_FILESYSTEM_URLS:
        pytest.skip("MCP_FILESYSTEM_URLS environment variable not set")
    
    # Return first URL from the list
    return MCP_FILESYSTEM_URLS[0].replace('/mcp', '')  # Remove /mcp path if present

@pytest.fixture
def mcp_memory_url():
    """Base URL for mcp-memory service, with test skip logic."""
    from .test_constants import MCP_MEMORY_TESTS_ENABLED, MCP_MEMORY_URLS
    
    if not MCP_MEMORY_TESTS_ENABLED:
        pytest.skip("MCP Memory tests are disabled. Set MCP_MEMORY_TESTS_ENABLED=true to enable.")
    if not MCP_MEMORY_URLS:
        pytest.skip("MCP_MEMORY_URLS environment variable not set")
    
    # Return first URL from the list
    return MCP_MEMORY_URLS[0].replace('/mcp', '')  # Remove /mcp path if present