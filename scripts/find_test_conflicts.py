#!/usr/bin/env python3
"""Find potential test conflicts when running in parallel."""


def find_potential_conflicts(log_file):
    """Find tests that might conflict when run in parallel."""
    # Track Redis key usage
    redis_patterns = [
        r"oauth:client:",
        r"oauth:state:",
        r"oauth:code:",
        r"oauth:token:",
        r"oauth:refresh:",
        r"oauth:user_tokens:",
        r"redis:session:",
    ]

    # Track test patterns that might conflict

    print("=== Potential Test Conflicts Analysis ===\n")

    # Common conflict sources
    print("1. **OAuth Client Registration Conflicts:**")
    print("   Tests that register clients might conflict if they:")
    print("   - Use the same redirect URIs")
    print("   - Register with the same client names")
    print("   - Don't clean up after themselves\n")

    print("2. **Redis Key Conflicts:**")
    print("   Tests using Redis might conflict on:")
    for pattern in redis_patterns:
        print(f"   - {pattern}* keys")
    print()

    print("3. **Resource Contention:**")
    print("   - MCP service session management")
    print("   - Tmux session conflicts")
    print("   - Playwright browser instances")
    print("   - File system operations in shared directories\n")

    print("4. **Timing Issues:**")
    print("   - Tests with sleep() or time-based assertions")
    print("   - SSE streaming tests expecting specific timing")
    print("   - Token expiration tests\n")

    # Recommendations
    print("=== Recommendations to Fix Conflicts ===\n")

    print("1. **Use Unique Test Data:**")
    print("   ```python")
    print("   @pytest.fixture")
    print("   def unique_client_id():")
    print("       return f'test_client_{uuid.uuid4()}'")
    print("   ```\n")

    print("2. **Proper Cleanup:**")
    print("   ```python")
    print("   @pytest.fixture(autouse=True)")
    print("   def cleanup_test_data(test_redis):")
    print("       yield")
    print("       # Clean up any test data")
    print("       pattern = f'oauth:test:*'")
    print("       for key in test_redis.scan_iter(match=pattern):")
    print("           test_redis.delete(key)")
    print("   ```\n")

    print("3. **Test Isolation:**")
    print("   - Use separate Redis databases for parallel workers")
    print("   - Use unique tmux session names per test")
    print("   - Isolate file operations to temp directories\n")

    print("4. **Group Related Tests:**")
    print("   ```bash")
    print("   # Run tests grouped by class to reduce conflicts")
    print("   just test-n 4 --dist loadscope")
    print("   ```\n")

    print("5. **Mark Slow Tests:**")
    print("   ```python")
    print("   @pytest.mark.slow")
    print("   def test_long_running_operation():")
    print("       # Run these separately")
    print("   ```\n")

    print("6. **Use Fixtures for Shared Setup:**")
    print("   - Create registered_client fixture for OAuth tests")
    print("   - Create authenticated_session fixture for MCP tests")
    print("   - Reuse expensive operations across tests")


if __name__ == "__main__":
    find_potential_conflicts("test-parallel-output.log")
