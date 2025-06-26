#!/usr/bin/env python3
"""Add parallel test execution support to conftest.py.

This script updates the Redis client fixture to use separate databases per worker.
"""

import re


def update_conftest():
    """Update conftest.py to support parallel test execution."""
    conftest_path = "tests/conftest.py"

    # Read the current conftest.py
    with open(conftest_path) as f:
        content = f.read()

    # Add worker_id fixture if not present
    worker_id_fixture = '''
def pytest_configure(config):
    """Configure pytest with worker information for parallel execution."""
    # Existing pytest_configure code...
    worker_id = os.environ.get('PYTEST_XDIST_WORKER', 'master')
    config.worker_id = worker_id


@pytest.fixture(scope="session")
def worker_id(request):
    """Return the current pytest-xdist worker ID.
    Returns 'master' if not running in parallel mode.
    Returns 'gw0', 'gw1', etc. when running with pytest-xdist.
    """
    return getattr(request.config, 'worker_id', 'master')


@pytest.fixture(scope="session")
def redis_db_number(worker_id):
    """Assign a unique Redis database number for each worker.
    - master: db 0 (default, non-parallel execution)
    - gw0: db 1
    - gw1: db 2
    - etc.
    """
    if worker_id == 'master':
        return 0
    # Extract number from worker_id (e.g., 'gw0' -> 0, 'gw1' -> 1)
    worker_num = int(worker_id.replace('gw', ''))
    # Use databases 1-15 for workers (Redis supports 0-15 by default)
    return min(worker_num + 1, 15)
'''

    # Find where to insert the worker_id fixture (after imports)
    import_section_end = content.find("\n\n# pytest-asyncio")
    if import_section_end == -1:
        import_section_end = content.find("\n\n@pytest.fixture")

    # Update Redis client creation to use worker-specific database
    redis_update = '''async def redis_client(redis_db_number):
    """Create a Redis client for testing with worker-specific database."""
    import redis.asyncio as redis

    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    # Use worker-specific database for test isolation
    client = await redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db_number,  # Worker-specific database
        decode_responses=True,
    )

    try:
        await client.ping()
        yield client
    finally:
        await client.close()'''

    # Find and replace the redis_client fixture
    redis_pattern = r"@pytest\.fixture[^\n]*\nasync def redis_client\([^)]*\):[^}]+finally:\s*await client\.close\(\)"

    # Check if redis_client exists
    if re.search(redis_pattern, content, re.DOTALL):
        # Replace existing redis_client
        content = re.sub(redis_pattern, f"@pytest.fixture\n{redis_update}", content, flags=re.DOTALL)
    else:
        print("Warning: Could not find redis_client fixture to update")

    # Add worker_id fixtures if not already present
    if "def worker_id(" not in content:
        # Insert after the existing pytest_configure
        configure_end = content.find('pytest.exit("Token validation failed", returncode=1)')
        if configure_end != -1:
            # Find the end of the function
            func_end = content.find("\n\n\n", configure_end)
            if func_end == -1:
                func_end = content.find("\n\n@", configure_end)

            # Insert worker configuration
            content = (
                content[:func_end]
                + """

    # Configure worker ID for parallel execution
    worker_id = os.environ.get('PYTEST_XDIST_WORKER', 'master')
    config.worker_id = worker_id"""
                + worker_id_fixture
                + content[func_end:]
            )

    # Write the updated content
    with open(conftest_path, "w") as f:
        f.write(content)

    print("✅ Updated conftest.py with parallel test support")
    print("📝 Added fixtures: worker_id, redis_db_number")
    print("🔧 Updated redis_client to use worker-specific databases")

    # Also update the rate limiter to be worker-aware
    update_rate_limiter()


def update_rate_limiter():
    """Update rate limiter to be worker-aware."""
    conftest_path = "tests/conftest.py"

    with open(conftest_path) as f:
        content = f.read()

    # Update the global rate limiter to use more permits for parallel execution
    content = content.replace(
        "_RATE_LIMITER = Semaphore(10)",
        "# Increase rate limit for parallel execution\n"
        "# Each worker gets its own allocation, so total = workers * limit\n"
        "_RATE_LIMITER = Semaphore(20)",
    )

    with open(conftest_path, "w") as f:
        f.write(content)

    print("🚀 Updated rate limiter for parallel execution")


if __name__ == "__main__":
    update_conftest()
    print("\n✨ Parallel test support has been added!")
    print("\nYou can now run tests in parallel with:")
    print("  just test -n auto     # Use all CPU cores")
    print("  just test -n 4        # Use 4 workers")
    print("  just test -n 4 --dist loadscope  # Keep same-module tests together")
