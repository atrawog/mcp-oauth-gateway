#!/usr/bin/env python3
"""Strategy for parallel test execution without Redis database isolation.

Instead of separate databases, we'll use:
1. Unique test prefixes/namespaces
2. Proper test categorization
3. Smart worker distribution
4. Enhanced cleanup
"""


def create_parallel_test_fixture():
    """Create fixtures for parallel-safe test execution."""
    return '''
import uuid
from datetime import datetime

@pytest.fixture
def test_id():
    """Generate a unique test ID for parallel-safe operations."""
    # Combination of timestamp and UUID for uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"test_{timestamp}_{unique_id}"


@pytest.fixture
def unique_client_name(test_id, worker_id):
    """Generate unique client names for OAuth registration."""
    return f"client_{worker_id}_{test_id}"


@pytest.fixture
def unique_redis_prefix(test_id, worker_id):
    """Generate unique Redis key prefix for test isolation."""
    return f"test:{worker_id}:{test_id}"


# Enhanced cleanup fixture
@pytest.fixture(autouse=True)
async def enhanced_redis_cleanup(redis_client, request, unique_redis_prefix):
    """Enhanced cleanup that handles parallel test execution."""
    # Before test: record any test-specific keys
    test_keys = set()

    yield

    # After test: Clean up any keys created with our prefix
    if not request.node.get_closest_marker("skip_redis_cleanup"):
        # Clean up test-specific keys
        pattern = f"{unique_redis_prefix}:*"
        async for key in redis_client.scan_iter(match=pattern):
            test_keys.add(key)

        if test_keys:
            await redis_client.delete(*test_keys)
'''


def create_test_categorization():
    """Create test categorization for optimal parallel distribution."""
    return """
# Test categories for parallel execution
# Use pytest.mark to categorize tests

# Category 1: Stateless tests (highly parallel)
# - Unit tests
# - Simple API endpoint tests
# - Validation tests
pytest.mark.parallel_safe

# Category 2: OAuth flow tests (moderate parallelism)
# - Client registration tests
# - Token generation tests
# - Authorization flow tests
pytest.mark.oauth_flow

# Category 3: MCP service tests (grouped by service)
# - Each MCP service can run in parallel
# - Tests for same service stay on same worker
pytest.mark.mcp_service

# Category 4: Integration tests (limited parallelism)
# - Full end-to-end flows
# - Cross-service tests
pytest.mark.integration_heavy

# Category 5: Exclusive tests (serial execution)
# - Tests that modify global state
# - Performance/load tests
# - Tests that restart services
pytest.mark.serial
"""


def create_parallel_safe_patterns():
    """Common patterns for parallel-safe tests."""
    return '''
# Pattern 1: Unique client registration
async def test_oauth_registration(unique_client_name):
    """Each test uses a unique client name."""
    registration_data = {
        "client_name": unique_client_name,
        "redirect_uris": [f"https://example.com/callback/{unique_client_name}"]
    }
    # ... rest of test

# Pattern 2: Scoped Redis operations
async def test_redis_operations(redis_client, unique_redis_prefix):
    """Use prefixed keys for Redis operations."""
    key = f"{unique_redis_prefix}:mydata"
    await redis_client.set(key, "value")
    # ... rest of test

# Pattern 3: Isolated MCP sessions
async def test_mcp_session(test_id):
    """Each test creates its own MCP session."""
    session_id = f"session_{test_id}"
    # ... rest of test

# Pattern 4: Retry on conflicts
async def test_with_retry(http_client):
    """Retry on conflicts from parallel execution."""
    for attempt in range(3):
        try:
            response = await http_client.post(...)
            if response.status_code != 409:  # Not a conflict
                break
        except Exception:
            if attempt == 2:
                raise
            await asyncio.sleep(0.1 * (attempt + 1))
'''


def create_justfile_commands():
    """Justfile commands for parallel testing."""
    return """
# Test in parallel with automatic CPU detection
test-parallel *args:
    pixi run pytest -n auto {{args}}

# Test in parallel with specific worker count
test-parallel-n count *args:
    pixi run pytest -n {{count}} {{args}}

# Test by category with optimal distribution
test-parallel-stateless:
    pixi run pytest -n auto -m "parallel_safe" --dist worksteal

test-parallel-oauth:
    pixi run pytest -n 4 -m "oauth_flow" --dist loadscope

test-parallel-mcp:
    pixi run pytest -n auto -m "mcp_service" --dist loadfile

test-parallel-integration:
    pixi run pytest -n 2 -m "integration_heavy"

# Run serial tests separately
test-serial:
    pixi run pytest -m "serial"

# Full parallel test suite with categories
test-all-parallel:
    @echo "Running parallel-safe tests..."
    pixi run pytest -n auto -m "parallel_safe" --dist worksteal -q
    @echo "Running OAuth flow tests..."
    pixi run pytest -n 4 -m "oauth_flow" --dist loadscope -q
    @echo "Running MCP service tests..."
    pixi run pytest -n auto -m "mcp_service" --dist loadfile -q
    @echo "Running integration tests..."
    pixi run pytest -n 2 -m "integration_heavy" -q
    @echo "Running serial tests..."
    pixi run pytest -m "serial" -q

# Parallel test with statistics
test-parallel-stats:
    pixi run pytest -n auto --dist worksteal --durations=20
"""


def main():
    print("🚀 Parallel Test Strategy (Without Redis DB Isolation)")
    print("=" * 60)
    print("\n1. **Test Isolation Approaches:**")
    print("   - Unique test IDs and prefixes")
    print("   - Client name namespacing")
    print("   - Scoped Redis key patterns")
    print("   - Enhanced cleanup procedures")

    print("\n2. **Worker Distribution Strategies:**")
    print("   - `--dist worksteal`: Dynamic distribution (best for uneven tests)")
    print("   - `--dist loadscope`: Keep same-class tests together")
    print("   - `--dist loadfile`: Keep same-file tests together")
    print("   - `--dist loadgroup`: Group by xdist_group mark")

    print("\n3. **Test Categorization:**")
    print("   - parallel_safe: Stateless, highly parallel")
    print("   - oauth_flow: OAuth tests with moderate parallelism")
    print("   - mcp_service: Service tests grouped by service")
    print("   - integration_heavy: Limited parallelism")
    print("   - serial: Must run sequentially")

    print("\n4. **Recommended Approach:**")
    print("   a) Start with: `just test -n 4 --dist loadscope`")
    print("   b) Monitor for conflicts/failures")
    print("   c) Mark problematic tests with @pytest.mark.serial")
    print("   d) Use unique prefixes for shared resources")

    print("\n5. **Conflict Resolution:**")
    print("   - OAuth client conflicts: Use unique client names")
    print("   - Token conflicts: Use test-specific scopes")
    print("   - Redis conflicts: Use prefixed keys")
    print("   - Port conflicts: Tests already use shared services")

    print("\n✅ This approach maintains shared state while enabling parallelism!")


if __name__ == "__main__":
    main()
