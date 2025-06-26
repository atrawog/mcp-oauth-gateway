# Development Guidelines

This document outlines the development principles and practices for the MCP OAuth Gateway project. All contributors must follow these guidelines to maintain code quality and consistency.

```{warning}
These guidelines are based on the "Sacred Commandments" in CLAUDE.md and must be followed without exception.
```

## Core Principles

### 1. No Mocking Policy

**The Divine Law**: Test against real systems only. No mocks, stubs, or fakes.

```python
# ❌ FORBIDDEN - Mock testing
@patch('requests.get')
def test_fetch(mock_get):
    mock_get.return_value.json.return_value = {'data': 'fake'}

# ✅ BLESSED - Real integration testing
def test_fetch():
    response = requests.get('http://mcp-fetch:3000/mcp')
    assert response.status_code == 200
```

**Why**: Mocks lie. Production will expose those lies. Test against real Docker containers.

### 2. The Holy Trinity of Tools

**Always use these three blessed tools**:

1. **`just`** - All commands flow through just
2. **`pixi`** - All Python packages through pixi
3. **`docker-compose`** - All services through compose

```bash
# ❌ HERESY
pytest tests/test_auth.py
pip install requests
docker run auth-service

# ✅ RIGHTEOUSNESS
just test tests/test_auth.py
pixi add requests
just up auth
```

### 3. Sacred Project Structure

```
project/
├── service-name/         # One service, one directory
│   ├── Dockerfile       # Container definition
│   └── src/            # Service source code
├── tests/              # All tests here, not in services
│   ├── conftest.py     # Shared fixtures
│   └── test_*.py       # Test files
├── scripts/            # Python automation scripts
├── docs/               # Jupyter Book documentation
├── justfile            # Command definitions
├── pixi.toml           # Python dependencies
└── .env                # Configuration (git-ignored)
```

## Development Workflow

### Setting Up Development Environment

```bash
# 1. Clone repository
git clone https://github.com/atrawog/mcp-oauth-gateway.git
cd mcp-oauth-gateway

# 2. Install dependencies
pixi install

# 3. Setup environment
just setup
cp .env.example .env
# Edit .env with your configuration

# 4. Generate secrets
just generate-jwt-secret
just generate-rsa-keys

# 5. Start services
just network-create
just up
```

### Making Changes

#### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

#### 2. Implement Changes

Follow these patterns:

**Service Implementation**:
```python
# auth/main.py
from fastapi import FastAPI, Depends
from authlib.oauth2 import ResourceProtector

app = FastAPI()

# Configuration through environment only
GITHUB_CLIENT_ID = os.environ["GITHUB_CLIENT_ID"]  # Required
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]      # Required

# No defaults in code - explicit > implicit
```

**Error Handling**:
```python
# Always return proper OAuth errors
@app.post("/token")
async def token_endpoint():
    try:
        # Token logic
    except InvalidClient:
        return JSONResponse(
            status_code=401,
            content={"error": "invalid_client"},
            headers={"WWW-Authenticate": 'Bearer error="invalid_client"'}
        )
```

#### 3. Write Tests

**Test Structure**:
```python
# tests/test_feature.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_real_oauth_flow():
    """Test against real deployed services."""
    # 1. Register client
    async with AsyncClient() as client:
        response = await client.post(
            "https://auth.localhost/register",
            json={"client_name": "test"}
        )
        assert response.status_code == 201

    # 2. Test actual OAuth flow
    # No mocking allowed!
```

#### 4. Run Tests

```bash
# Run all tests
just test

# Run specific test
just test tests/test_your_feature.py -v

# Run with coverage
just test-coverage
```

### Code Quality Standards

#### Python Code Style

- Use **Black** for formatting (via `just format`)
- Follow **PEP 8** conventions
- Use **type hints** for all functions
- Document with **docstrings**

```python
from typing import Dict, Optional

async def validate_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate JWT token and return claims.

    Args:
        token: JWT token string

    Returns:
        Token claims dict or None if invalid
    """
    # Implementation
```

#### Error Messages

Provide clear, actionable error messages:

```python
# ❌ Bad
raise ValueError("Invalid input")

# ✅ Good
raise ValueError(
    f"Invalid redirect_uri '{uri}': HTTPS required for non-localhost URIs. "
    f"See RFC 6749 Section 3.1.2"
)
```

### Documentation

#### Code Documentation

- All public functions need docstrings
- Complex logic needs inline comments
- README for each service directory

#### API Documentation

Use OpenAPI/Swagger annotations:

```python
@app.post(
    "/register",
    response_model=ClientRegistrationResponse,
    status_code=201,
    summary="Register OAuth Client",
    description="Dynamic client registration per RFC 7591"
)
async def register_client(request: ClientRegistrationRequest):
    """Register a new OAuth client."""
    # Implementation
```

### Security Practices

#### Never Hardcode Secrets

```python
# ❌ FORBIDDEN
JWT_SECRET = "super-secret-key"

# ✅ REQUIRED
JWT_SECRET = os.environ["GATEWAY_JWT_SECRET"]
if not JWT_SECRET:
    raise ValueError("GATEWAY_JWT_SECRET must be set")
```

#### Input Validation

Always validate inputs:

```python
from pydantic import BaseModel, HttpUrl, validator

class ClientRegistration(BaseModel):
    client_name: str
    redirect_uris: List[HttpUrl]

    @validator('redirect_uris', each_item=True)
    def validate_redirect_uri(cls, uri):
        if uri.host == 'localhost':
            return uri
        if uri.scheme != 'https':
            raise ValueError("HTTPS required for non-localhost")
        return uri
```

### Testing Requirements

#### Integration Tests Required

Every feature needs integration tests:

```python
# tests/test_integration_feature.py
async def test_feature_end_to_end():
    """Test complete flow with real services."""
    # 1. Setup
    await register_test_client()

    # 2. Execute
    token = await get_oauth_token()
    response = await call_mcp_service(token)

    # 3. Verify
    assert response.status_code == 200

    # 4. Cleanup
    await cleanup_test_data()
```

#### Health Check Tests

Every service needs health checks:

```python
async def test_service_health():
    """Verify service health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Docker Best Practices

#### Dockerfile Structure

```dockerfile
FROM python:3.11-slim

# Install system dependencies first (cached layer)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (cached if unchanged)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (invalidates cache on changes)
COPY . /app
WORKDIR /app

# Non-root user
RUN useradd -m appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Commit Guidelines

#### Commit Messages

Follow conventional commits:

```bash
feat: Add PKCE support to OAuth flow
fix: Correct token expiration calculation
docs: Update API documentation
test: Add integration tests for refresh token
refactor: Extract token validation logic
```

#### Pre-commit Checks

Before committing:

```bash
# 1. Format code
just format

# 2. Run linting
just lint

# 3. Run tests
just test

# 4. Check coverage
just test-coverage
```

### Pull Request Process

1. **Create PR** with clear description
2. **Ensure tests pass** - All CI checks must be green
3. **Update documentation** if needed
4. **Request review** from maintainers
5. **Address feedback** promptly

### Debugging Tips

#### Service Logs

```bash
# View specific service logs
just logs auth -f

# Search logs
just logs | grep -i error

# Analyze OAuth flows
just analyze-oauth-logs
```

#### Interactive Debugging

```bash
# Shell into service
just exec auth bash

# Python debugging
just exec auth python
>>> import redis
>>> r = redis.Redis(host='redis', password=os.environ['REDIS_PASSWORD'])
>>> r.keys('oauth:*')
```

#### Test Debugging

```python
# Use pytest debugging
just test tests/test_auth.py --pdb

# Add breakpoints
import pdb; pdb.set_trace()
```

## Common Pitfalls

### 1. Using Mocks

**Problem**: Tests pass but production fails
**Solution**: Always test against real services

### 2. Hardcoded Values

**Problem**: Works locally, fails in production
**Solution**: All config through environment variables

### 3. Missing Health Checks

**Problem**: Services appear running but are broken
**Solution**: Implement proper health endpoints

### 4. Ignoring CORS

**Problem**: Browser clients can't connect
**Solution**: Configure CORS properly for your domain

### 5. Weak Error Messages

**Problem**: Users can't debug issues
**Solution**: Provide clear, actionable error messages

## Getting Help

- Review existing code for patterns
- Check test files for examples
- Consult CLAUDE.md for commandments
- Open an issue for questions

## Next Steps

- [Testing Approach](testing-approach.md) - Testing philosophy
- [Project Structure](project-structure.md) - Directory layout
- [Adding Services](adding-services.md) - Add new MCP services
