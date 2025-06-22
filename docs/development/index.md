# Development Guide

Complete guide for developing with and contributing to the MCP OAuth Gateway following the **Ten Sacred Commandments of Divine Python Development**.

## Development Environment

### Prerequisites
- **Docker & Docker Compose**: Container orchestration
- **pixi**: Python package management (replaces pip/conda)
- **just**: Task runner (replaces make/npm scripts)
- **Git**: Version control

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd mcp-oauth-gateway

# Setup development environment
just setup

# Start all services
just up-fresh
```

### Sacred Development Tools Trinity

The development environment follows the **Holy Trinity** pattern:

1. **just** - The divine task runner
2. **pixi** - The blessed package manager  
3. **docker-compose** - The sacred orchestrator

#### Essential Commands

```bash
# Development lifecycle
just setup                    # Initialize project dependencies
just dev                     # Start development environment
just test                    # Run test suite
just lint                    # Code quality checks

# Service management
just up                      # Start all services
just up-fresh               # Fresh build with --force-recreate
just down                   # Stop all services
just rebuild <service>      # Rebuild specific service
just rebuild-all           # Rebuild all services

# Monitoring and debugging
just logs                   # View last 200 log entries
just logs-follow           # Follow all container logs
just check-health          # Verify service health
just logs-purge           # Clear all container logs
```

### Environment Configuration

All configuration flows through `.env` files:

```bash
# Copy example configuration
cp .env.example .env

# Generate required secrets
just generate-jwt-secret
just generate-github-token    # Manual intervention required
just mcp-client-token        # For external client testing
```

## Contributing Guidelines

### Code Standards

#### The Sacred Commandments
1. **No Mocks**: All tests use real services and deployments
2. **Real Systems Only**: Test against actual Docker containers
3. **pixi for Dependencies**: Never use pip/conda directly
4. **just for Tasks**: All commands through justfile
5. **Configuration via .env**: No hardcoded values

#### Project Structure

```
mcp-oauth-gateway/
├── service-name/           # Each service in its own directory
│   ├── Dockerfile         # Container definition
│   ├── docker-compose.yml # Service orchestration
│   └── CLAUDE.md          # Service documentation
├── package-name/          # Python packages
│   ├── src/package_name/  # Source code
│   └── pyproject.toml     # Package metadata
├── tests/                 # All pytest tests
├── scripts/               # Python automation scripts
├── docs/                  # Jupyter Book documentation
├── logs/                  # Centralized logging
├── reports/               # Analysis outputs (git-ignored)
└── htmlcov/              # Coverage reports (git-ignored)
```

### Git Workflow

#### Branch Strategy
- **main**: Production-ready code
- **feature/name**: Feature development branches
- **fix/name**: Bug fix branches
- **docs/name**: Documentation updates

#### Commit Standards
- **Conventional Commits**: Use conventional commit format
- **Atomic Commits**: One logical change per commit
- **Descriptive Messages**: Clear what and why

```bash
# Commit message format
type(scope): description

# Examples
feat(auth): add RFC 7592 client management endpoints
fix(mcp-time): resolve timezone conversion edge case
docs(architecture): update security model documentation
test(integration): add comprehensive MCP protocol tests
```

### Pull Request Process

1. **Branch Creation**: Create feature branch from main
2. **Development**: Follow coding standards and test requirements
3. **Testing**: Ensure all tests pass with `just test`
4. **Documentation**: Update relevant documentation
5. **Quality Checks**: Run `just lint` and fix issues
6. **Pull Request**: Create PR with descriptive title and body
7. **Code Review**: Address reviewer feedback
8. **CI/CD**: Ensure all checks pass
9. **Merge**: Squash and merge to main

## Testing Strategy

### Real Systems Testing Philosophy

**⚡ No mocks! No stubs! No fakes! ⚡**

All tests run against real Docker containers to ensure production compatibility.

#### Test Categories

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Service-to-service communication
3. **End-to-End Tests**: Complete workflow validation
4. **Load Tests**: Performance and scalability
5. **Security Tests**: Authentication and authorization

#### Test Environment

```bash
# Start test environment
just up-fresh

# Wait for services to be ready
just ensure-services-ready

# Run comprehensive test suite
just test-all

# Run with coverage measurement
just test-sidecar-coverage
```

#### Test Structure

```python
# tests/test_mcp_service_integration.py
import pytest
from helpers.mcp_client import MCPClient

class TestMCPServiceIntegration:
    @pytest.fixture(scope="class")
    def service_url(self, base_domain):
        return f"https://mcp-service.{base_domain}"
    
    @pytest.fixture(scope="class")
    def client_token(self, oauth_client):
        return oauth_client.get_access_token()
    
    def test_service_health(self, service_url):
        """Test service health endpoint."""
        response = requests.get(f"{service_url}/health")
        assert response.status_code == 200
    
    def test_mcp_protocol(self, service_url, client_token):
        """Test MCP protocol compliance."""
        client = MCPClient(service_url, client_token)
        response = client.initialize()
        assert response["result"]["protocolVersion"] == "2025-06-18"
```

### Coverage Requirements

- **Minimum Coverage**: 90% for new code
- **Critical Paths**: 100% coverage for auth and security code
- **Sidecar Coverage**: Measure production containers without modification

```bash
# Generate coverage report
just test-sidecar-coverage

# View coverage report
open htmlcov/index.html
```

## Code Quality Standards

### Python Code Standards

#### Code Style
- **Black**: Automatic code formatting
- **isort**: Import sorting
- **flake8**: Linting and style checking
- **mypy**: Type checking

```bash
# Run all quality checks
just lint

# Individual tools
pixi run black .
pixi run isort .
pixi run flake8 .
pixi run mypy .
```

#### Type Hints
- **Required**: All function signatures must have type hints
- **Comprehensive**: Include return types and complex types
- **Modern Syntax**: Use Python 3.9+ type syntax

```python
from typing import Dict, List, Optional
from datetime import datetime

def process_oauth_token(
    token: str,
    client_id: str,
    expires_at: Optional[datetime] = None
) -> Dict[str, Any]:
    """Process OAuth token with validation."""
    ...
```

### Documentation Standards

#### Docstring Format
- **Google Style**: Use Google-style docstrings
- **Comprehensive**: Document all parameters and return values
- **Examples**: Include usage examples where helpful

```python
def validate_jwt_token(token: str, audience: str) -> Dict[str, Any]:
    """Validate JWT token signature and claims.
    
    Args:
        token: The JWT token to validate
        audience: Expected audience claim
        
    Returns:
        Dictionary containing validated claims
        
    Raises:
        TokenValidationError: If token is invalid
        
    Example:
        >>> claims = validate_jwt_token(token, "mcp-services")
        >>> print(claims["sub"])
        github_user_123
    """
```

#### API Documentation
- **OpenAPI Specs**: Document all REST endpoints
- **Request/Response Examples**: Show actual usage patterns
- **Error Codes**: Document all possible error responses

### Security Standards

#### Secrets Management
- **Environment Variables**: All secrets via .env files
- **No Hardcoding**: Never commit secrets to repository
- **Rotation**: Support for secret rotation

#### Input Validation
- **Validate Everything**: All inputs must be validated
- **Sanitize Outputs**: Prevent injection attacks
- **Error Handling**: Secure error messages

```python
from pydantic import BaseModel, validator

class ClientRegistrationRequest(BaseModel):
    redirect_uris: List[str]
    client_name: Optional[str] = None
    
    @validator('redirect_uris')
    def validate_redirect_uris(cls, v):
        for uri in v:
            if not uri.startswith(('https://', 'http://localhost')):
                raise ValueError('Invalid redirect URI')
        return v
```

### Performance Standards

#### Response Times
- **API Endpoints**: < 100ms for simple operations
- **OAuth Flows**: < 2s for complete authorization
- **Health Checks**: < 50ms response time

#### Resource Usage
- **Memory**: < 512MB per service container
- **CPU**: < 50% sustained usage under load
- **Storage**: Efficient Redis key usage

### Error Handling Standards

#### Error Response Format
```json
{
  "error": "invalid_request",
  "error_description": "The request is missing a required parameter",
  "error_uri": "https://docs.example.com/oauth-errors#invalid_request"
}
```

#### Logging Standards
- **Structured Logging**: JSON format for parsing
- **Context Information**: Include request IDs and user context
- **Security Events**: Comprehensive audit trail

```python
import structlog

logger = structlog.get_logger()

def handle_oauth_request(request: Request) -> Response:
    logger.info(
        "oauth_request_received",
        client_id=request.client_id,
        grant_type=request.grant_type,
        request_id=request.headers.get("x-request-id")
    )
```

## Debugging and Troubleshooting

### Common Issues

#### Service Startup Problems
```bash
# Check service health
just check-health

# View service logs
just logs-follow

# Rebuild specific service
just rebuild auth
```

#### Authentication Issues
```bash
# Check OAuth configuration
just generate-github-token

# Verify client registration
curl -X GET https://auth.${BASE_DOMAIN}/register/${CLIENT_ID} \
  -H "Authorization: Bearer ${REGISTRATION_TOKEN}"
```

#### Test Failures
```bash
# Run single test with verbose output
pixi run pytest tests/test_specific.py -v -s

# Debug with pdb
pixi run pytest tests/test_specific.py --pdb
```

### Development Tools

#### Docker Debugging
```bash
# Enter running container
docker exec -it mcp-oauth-gateway-auth-1 /bin/sh

# View container logs
docker logs mcp-oauth-gateway-auth-1 --follow

# Inspect container
docker inspect mcp-oauth-gateway-auth-1
```

#### Redis Debugging
```bash
# Connect to Redis
docker exec -it mcp-oauth-gateway-redis-1 redis-cli

# List all keys
KEYS *

# Get specific key
GET oauth:token:abcd1234
```