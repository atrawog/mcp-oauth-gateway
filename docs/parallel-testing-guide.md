# Parallel Test Execution Guide

## Overview

The test suite is now configured for parallel execution using `pytest-xdist`. This significantly reduces test execution time by running tests across multiple workers.

## Setup Completed

### 1. **pytest-xdist Installation**
- Added to `pixi.toml` dependencies
- Provides `-n` flag for parallel execution

### 2. **Unique Client ID Fixtures**
Added to `conftest.py`:
- `worker_id` - Returns the xdist worker ID (master, gw0, gw1, etc.)
- `unique_test_id` - Generates unique test identifier with format: `{worker_id}_{timestamp}_{uuid}_{test_name}`
- `unique_client_name` - Creates unique OAuth client names: `TEST {unique_test_id}`
- Updated `registered_client` fixture to use `unique_client_name`

### 3. **Parallel Test Commands**
Added to `justfile`:
- `just test-parallel` - Run with auto-detected CPU cores
- `just test-n <count>` - Run with specific worker count
- `just test-fast` - Run with worksteal distribution (optimal for uneven test times)
- `just test-by-module` - Keep tests from same file together
- `just test-by-class` - Keep tests from same class together
- `just test-serial` - Run only tests marked as serial
- `just test-parallel-safe` - Run all tests except serial ones

### 4. **Test Markers**
Added to `pytest.ini`:
- `serial` - Tests that must run sequentially
- `redis_isolated` - Tests needing isolated Redis access
- `heavy_resource` - Resource-intensive tests

## Running Parallel Tests

### Quick Start
```bash
# Use all CPU cores
just test-parallel

# Use 4 workers
just test-n 4

# Fast mode with work stealing
just test-fast

# Run specific test files in parallel
just test-n 4 tests/test_oauth_flow.py tests/test_claude_integration.py
```

### Distribution Strategies

1. **worksteal** (default for test-fast)
   - Dynamic work distribution
   - Best for tests with varying execution times
   - Example: `just test-n 4 --dist worksteal`

2. **loadscope**
   - Keeps tests from same class on same worker
   - Good for tests with class-level fixtures
   - Example: `just test-by-class`

3. **loadfile**
   - Keeps tests from same file on same worker
   - Good for tests with module-level dependencies
   - Example: `just test-by-module`

## Test Isolation Strategies

### 1. **Unique Client Names**
All OAuth client registrations now use unique names to prevent conflicts:
```python
def test_oauth_flow(registered_client):
    # Client name will be like: TEST gw0_1735274521123_a1b2c3d4_test_oauth_flow
    client = registered_client
    # ... test code
```

### 2. **Shared Redis State**
- Tests share the same Redis database (required for OAuth tokens)
- Each test should clean up its own data
- Use unique prefixes for test-specific keys

### 3. **Rate Limiting**
- Global rate limiter increased to 20 concurrent requests
- Each worker shares the global limit

## Best Practices

### 1. **Use Fixtures for Client Registration**
```python
# Good - uses unique client name automatically
def test_my_oauth_test(registered_client):
    client = registered_client
    # ... use client

# Also good - explicit unique name
def test_dynamic_registration(http_client, unique_client_name):
    response = await http_client.post("/register", json={
        "client_name": unique_client_name,
        "redirect_uris": ["https://example.com/callback"]
    })
```

### 2. **Mark Serial Tests**
```python
@pytest.mark.serial
def test_modifies_global_state():
    # This test will run alone, not in parallel
    pass
```

### 3. **Handle Transient Failures**
```python
# Retry on conflicts from parallel execution
for attempt in range(3):
    try:
        response = await http_client.post(...)
        if response.status_code != 409:  # Not a conflict
            break
    except Exception:
        if attempt == 2:
            raise
        await asyncio.sleep(0.1 * (attempt + 1))
```

## Performance Comparison

### Sequential Execution
```bash
just test  # ~5-6 minutes for full suite
```

### Parallel Execution
```bash
just test-n 4  # ~2-3 minutes (depends on CPU cores)
just test-n auto  # Uses all available cores
```

## Troubleshooting

### 1. **Client Name Conflicts**
- Symptom: 409 Conflict errors during registration
- Solution: Ensure tests use `unique_client_name` or `registered_client` fixture

### 2. **Redis State Conflicts**
- Symptom: Unexpected test data in Redis
- Solution: Use unique key prefixes, ensure proper cleanup

### 3. **Rate Limiting**
- Symptom: 429 Too Many Requests errors
- Solution: Reduce worker count or increase rate limits

### 4. **Token Validation Spam**
- Symptom: Multiple "PRE-TEST TOKEN VALIDATION" messages
- Note: This is normal - each worker validates tokens independently

## Next Steps

### Remaining Optimizations

1. **Update Hardcoded Client Names**
   - Run: `python scripts/ensure_unique_client_ids.py`
   - Found ~26 test files with hardcoded names
   - Can be updated incrementally as needed

2. **Add Test Categories**
   - Mark tests by type (unit, integration, e2e)
   - Run categories on different worker counts

3. **Monitor Flaky Tests**
   - Tests that fail only in parallel may have hidden dependencies
   - Use `--lf` (last failed) to rerun failures

4. **CI/CD Integration**
   - Update CI pipelines to use parallel execution
   - Consider different worker counts for different environments

## Summary

The test suite is now ready for parallel execution with:
- ✅ Unique client IDs preventing OAuth conflicts
- ✅ Worker-aware fixtures
- ✅ Multiple distribution strategies
- ✅ Convenient justfile commands
- ✅ Proper test isolation

Start with `just test-n 4` and adjust based on your system's capabilities!
