# Testing Commands

The testing commands follow the sacred commandment: **No Mocks or Burn in Production Hell!** All tests run against real deployed services.

## Core Testing Philosophy

- ✅ **Real systems only** - Test against ACTUAL services
- ✅ **End-to-end mandatory** - The FULL stack or nothing
- ✅ **Real APIs only** - Mock responses are LIES
- ✅ **No shortcuts** - Pain now or AGONY later

## Universal Test Runner

The `test` command is the blessed interface to pytest:

```bash
# Run all tests
just test

# Run specific test file
just test tests/test_oauth_flow.py

# Run tests matching pattern
just test -k "oauth" -v

# Run with debugging
just test --pdb -s

# Run with specific markers
just test -m "not serial"
```

## Parallel Testing

Leverage multiple CPU cores for faster test execution:

```bash
# Auto-detect CPU cores
just test-parallel

# Specific worker count
just test-n 4

# Optimal work distribution
just test-fast

# Keep related tests together
just test-by-module  # Same file on same worker
just test-by-class   # Same class on same worker
```

## Serial vs Parallel Tests

Some tests require serial execution due to shared state:

```python
# Mark tests that must run serially
@pytest.mark.serial
def test_oauth_client_registration():
    # This test modifies global OAuth state
    pass
```

```bash
# Run only serial tests
just test-serial

# Run parallel tests (excluding serial)
just test-parallel-safe
```

## Sidecar Coverage Pattern

The divine pattern for measuring coverage in production containers:

```bash
just test-sidecar-coverage
```

This sacred incantation:
1. Starts services with coverage instrumentation
2. Runs tests against production containers
3. Triggers graceful shutdown to collect coverage
4. Harvests coverage data from containers
5. Generates coverage reports

### Coverage Architecture

```yaml
# docker-compose.coverage.yml extends services with:
environment:
  - PYTHONPATH=/coverage-spy:$PYTHONPATH
  - COVERAGE_FILE=/coverage-data/.coverage
volumes:
  - ./coverage-spy:/coverage-spy:ro
  - coverage-data:/coverage-data
```

The `sitecustomize.py` intercepts Python startup to enable coverage in production containers.

## Test Organization

Following the sacred structure:

```
tests/
├── conftest.py          # Divine fixtures
├── test_oauth_flow.py   # OAuth flow tests
├── test_mcp_protocol.py # MCP protocol tests
├── test_integration.py  # Full integration tests
└── helpers/            # Test utilities
```

## Service Readiness

All test commands ensure services are ready:

```python
# ensure-services-ready is called automatically
# Checks all enabled services for health
# Fails fast if services aren't ready
```

## Test Patterns

### Integration Tests
```python
def test_full_oauth_flow(auth_client):
    """Test complete OAuth flow with real services."""
    # 1. Dynamic client registration
    # 2. Authorization flow with PKCE
    # 3. Token exchange
    # 4. MCP service access
```

### Protocol Tests
```python
def test_mcp_initialization(mcp_client):
    """Test MCP protocol handshake."""
    # Real StreamableHTTP transport
    # Actual JSON-RPC messages
    # Session management verification
```

### Error Handling Tests
```python
def test_invalid_token_rejection(auth_client):
    """Verify proper 401 handling."""
    # Real HTTP requests
    # Actual error responses
    # No mocked behaviors
```

## Debugging Failed Tests

```bash
# Diagnose test failures
just diagnose-tests

# Check service logs during test
just logs -f auth

# Run single test with verbose output
just test tests/test_oauth_flow.py::test_pkce_flow -vvv -s
```

## Test Data Cleanup

Tests create real data in real services:

```bash
# Show test registrations (client_name starts with "TEST ")
just test-cleanup-show

# Clean up test data
just test-cleanup
```

## Best Practices

1. **Always use real services** - No mocks, ever!
2. **Clean up after tests** - Use fixtures with proper teardown
3. **Test the full stack** - From HTTP request to database
4. **Verify actual behavior** - Check logs, database state, responses
5. **Use serial marks sparingly** - Only when truly needed

## Common Test Commands

```bash
# Quick test during development
just test tests/test_oauth_flow.py -k "test_client_registration" -v

# Full test suite with coverage
just test-sidecar-coverage

# Parallel tests for CI/CD
just test-fast

# Debug a failing test
just test tests/test_failing.py::test_specific --pdb -s
```

Remember: **Every mock is a lie waiting to destroy production!**
