# Testing Approach

The MCP OAuth Gateway follows a strict **no mocking** policy. All tests use real services and actual integrations to ensure production reliability.

## Core Testing Principles

### No Mocking Policy

**Absolutely forbidden:**
- Mock objects
- Stub services  
- Fake implementations
- In-memory databases

**Required instead:**
- Real Docker containers
- Actual service deployments
- True network calls
- Production-like environments

### Why No Mocks?

1. **Production Parity** - Tests match real-world behavior
2. **Integration Confidence** - Catch actual integration issues
3. **Network Reality** - Test real latency and failures
4. **Configuration Truth** - Validate actual configurations
5. **No False Positives** - If it passes, it works

## Test Structure

### Test Organization

```
tests/
├── conftest.py          # Shared fixtures
├── helpers/             # Test utilities
│   ├── __init__.py
│   ├── docker.py        # Docker helpers
│   ├── oauth.py         # OAuth flow helpers
│   └── mcp.py          # MCP protocol helpers
├── integration/         # Integration tests
│   ├── test_oauth_flow.py
│   ├── test_mcp_services.py
│   └── test_security.py
├── e2e/                # End-to-end tests
│   ├── test_full_flow.py
│   └── test_claude_integration.py
└── performance/        # Performance tests
    ├── test_load.py
    └── test_latency.py
```

### Test Categories

1. **Unit Tests** - Component-level with real dependencies
2. **Integration Tests** - Service interaction testing
3. **End-to-End Tests** - Complete user flows
4. **Performance Tests** - Load and latency testing
5. **Security Tests** - Vulnerability testing

## Writing Tests

### Test Fixtures

```python
# conftest.py
import pytest
import docker
from helpers.docker import wait_for_service

@pytest.fixture(scope="session")
def docker_services():
    """Start real Docker services for testing."""
    client = docker.from_env()
    
    # Start services
    subprocess.run(["just", "up", "-d"], check=True)
    
    # Wait for health
    wait_for_service("auth", "http://localhost:8000/health")
    wait_for_service("redis", "redis://localhost:6379")
    
    yield
    
    # Cleanup
    subprocess.run(["just", "down"], check=True)

@pytest.fixture
def auth_client(docker_services):
    """Real HTTP client for auth service."""
    return httpx.Client(base_url="http://localhost:8000")

@pytest.fixture
def redis_client(docker_services):
    """Real Redis connection."""
    return redis.Redis(host="localhost", port=6379)
```

### Integration Test Example

```python
# test_oauth_flow.py
import pytest
import httpx
from urllib.parse import urlparse, parse_qs

async def test_full_oauth_flow(auth_client, redis_client):
    """Test complete OAuth flow with real services."""
    
    # 1. Register client (real HTTP call)
    response = auth_client.post("/register", json={
        "client_name": "Test Client",
        "redirect_uris": ["http://localhost:9000/callback"],
        "grant_types": ["authorization_code"]
    })
    assert response.status_code == 201
    client_data = response.json()
    
    # 2. Verify in Redis (real Redis)
    client_key = f"oauth:client:{client_data['client_id']}"
    assert redis_client.exists(client_key)
    
    # 3. Start authorization (real flow)
    auth_response = auth_client.get("/authorize", params={
        "client_id": client_data["client_id"],
        "redirect_uri": "http://localhost:9000/callback",
        "response_type": "code",
        "state": "test-state"
    })
    assert auth_response.status_code == 302
    
    # 4. Extract code from redirect
    redirect_url = urlparse(auth_response.headers["Location"])
    code = parse_qs(redirect_url.query)["code"][0]
    
    # 5. Exchange code for token (real exchange)
    token_response = auth_client.post("/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:9000/callback",
        "client_id": client_data["client_id"],
        "client_secret": client_data["client_secret"]
    })
    assert token_response.status_code == 200
    token_data = token_response.json()
    
    # 6. Verify token in Redis
    token_key = f"oauth:token:{token_data['jti']}"
    assert redis_client.exists(token_key)
```

### End-to-End Test Example

```python
# test_full_flow.py
async def test_claude_to_mcp_flow(docker_services):
    """Test Claude.ai connecting to MCP service."""
    
    # 1. Simulate Claude registration
    claude_client = await register_claude_client()
    
    # 2. Perform OAuth flow
    access_token = await perform_oauth_flow(claude_client)
    
    # 3. Initialize MCP session
    mcp_client = MCPClient(
        "http://mcp-fetch:3000",
        token=access_token
    )
    await mcp_client.initialize()
    
    # 4. Call MCP method
    result = await mcp_client.request("fetch", {
        "url": "https://example.com"
    })
    
    # 5. Verify result
    assert result["status"] == 200
    assert "content" in result
```

## Running Tests

### Test Commands

```bash
# Run all tests
just test

# Run specific category
just test integration/

# Run single test
just test tests/integration/test_oauth_flow.py::test_full_oauth_flow

# Run with coverage
just test-coverage

# Run with debugging
just test --pdb

# Run performance tests
just test-performance
```

### Test Environment

Tests run against real services:

```bash
# Start test environment
just test-env up

# Run tests
just test

# Cleanup
just test-env down
```

## Coverage Testing

### Sidecar Coverage

Production coverage without instrumentation:

```python
# coverage-spy/sitecustomize.py
import coverage
import os

if os.environ.get("COVERAGE_PROCESS_START"):
    coverage.process_startup()
```

```bash
# Run with coverage
just test-sidecar-coverage

# Generate report
just coverage-report
```

### Coverage Requirements

- Minimum 80% line coverage
- 100% coverage for security code
- All error paths tested
- Integration points covered

## Performance Testing

### Load Testing

```python
# test_load.py
import asyncio
import httpx

async def test_high_load(docker_services):
    """Test system under load."""
    
    async def make_request(client, token):
        response = await client.post("/mcp", 
            headers={"Authorization": f"Bearer {token}"},
            json={"method": "ping", "id": 1}
        )
        return response.elapsed.total_seconds()
    
    # Create multiple clients
    clients = [httpx.AsyncClient() for _ in range(100)]
    
    # Make concurrent requests
    tasks = []
    for client in clients:
        tasks.extend([
            make_request(client, token) 
            for _ in range(10)
        ])
    
    # Measure performance
    latencies = await asyncio.gather(*tasks)
    
    # Assert performance requirements
    assert max(latencies) < 1.0  # Max 1 second
    assert sum(latencies) / len(latencies) < 0.1  # Avg 100ms
```

## Security Testing

### Vulnerability Tests

```python
# test_security.py
async def test_sql_injection(auth_client):
    """Test SQL injection protection."""
    
    # Attempt injection
    response = auth_client.post("/token", data={
        "grant_type": "'; DROP TABLE users; --",
        "code": "test"
    })
    
    # Should handle safely
    assert response.status_code == 400
    assert "invalid_grant" in response.json()["error"]
    
    # Verify database intact
    health = auth_client.get("/health")
    assert health.status_code == 200

async def test_path_traversal(mcp_filesystem):
    """Test path traversal protection."""
    
    # Attempt to escape root
    response = await mcp_filesystem.request("readFile", {
        "path": "../../etc/passwd"
    })
    
    # Should be blocked
    assert "error" in response
    assert response["error"]["code"] == -32602
```

## Test Best Practices

### 1. Test Independence

Each test must:
- Set up its own data
- Clean up after itself
- Not depend on test order
- Use unique identifiers

### 2. Real Data

Use realistic data:
- Actual URLs
- Valid OAuth flows
- Real file paths
- Production-like payloads

### 3. Error Testing

Test all error paths:
- Network failures
- Timeouts
- Invalid data
- Rate limits
- Service unavailable

### 4. Timing

Handle real-world timing:
- Network latency
- Service startup time
- Token expiration
- Cache invalidation

### 5. Cleanup

Always clean up:
- Remove test data
- Close connections
- Reset rate limits
- Clear caches

## Continuous Integration

### CI Pipeline

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start services
        run: just up -d
        
      - name: Wait for health
        run: just wait-healthy
        
      - name: Run tests
        run: just test-all
        
      - name: Coverage report
        run: just coverage-report
        
      - name: Cleanup
        run: just down -v
```

## Debugging Tests

### Debug Techniques

```bash
# Enable debug logging
export DEBUG=true
just test

# Use debugger
just test --pdb

# Verbose output
just test -vvv

# Keep services running
just test --keep-services
```

### Common Issues

1. **Service not ready**
   - Increase health check timeout
   - Add explicit waits
   - Check service logs

2. **Port conflicts**
   - Use dynamic ports
   - Clean up properly
   - Check for orphaned containers

3. **Flaky tests**
   - Add retries for network calls
   - Handle timing variations
   - Improve service stability

## Related Documentation

- [Development Guidelines](guidelines.md)
- [Project Structure](project-structure.md)
- [Testing Commands](../usage/testing.md)