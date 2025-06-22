# Python Packages

The MCP OAuth Gateway project includes several specialized Python packages that provide the core functionality for OAuth authentication, MCP protocol handling, and service integration.

## Package Overview

All packages follow Python best practices with comprehensive testing, type hints, and production-ready code quality.

```{mermaid}
graph TB
    subgraph "Client Packages"
        A[mcp-oauth-dynamicclient] --> B[OAuth Client Library]
        C[mcp-streamablehttp-client] --> D[Testing & Integration]
    end
    
    subgraph "Server Packages"
        E[mcp-streamablehttp-proxy] --> F[Protocol Bridge]
        G[mcp-fetch-streamablehttp-server] --> H[Direct HTTP Server]
    end
    
    subgraph "Applications"
        I[MCP Services] --> E
        J[Auth Service] --> A
        K[Testing Tools] --> C
        L[Fetch Service] --> G
    end
```

## Available Packages

```{grid} 2
:gutter: 3

```{grid-item-card} 🔐 OAuth Dynamic Client
:link: mcp-oauth-dynamicclient
:link-type: doc

**RFC 7591/7592 compliant OAuth client library**

Complete OAuth 2.1 client implementation with dynamic registration, PKCE support, and token management.

**Features:** RFC compliance, PKCE S256, JWT handling, token refresh
```

```{grid-item-card} 🌉 Streamable HTTP Proxy
:link: mcp-streamablehttp-proxy  
:link-type: doc

**stdio ↔ HTTP protocol bridge for MCP servers**

Wraps stdio-based MCP servers to provide HTTP endpoints with session management and health checks.

**Features:** Protocol bridging, session handling, health monitoring
```

```{grid-item-card} 🧪 Streamable HTTP Client
:link: mcp-streamablehttp-client
:link-type: doc

**Testing and integration client for MCP services**

Comprehensive client for testing MCP services with OAuth integration and protocol validation.

**Features:** OAuth integration, protocol testing, command-line interface
```

```{grid-item-card} 🌐 Fetch HTTP Server
:link: mcp-fetch-streamablehttp-server
:link-type: doc

**Direct HTTP implementation of MCP Fetch**

Native HTTP server implementation of the MCP Fetch protocol without stdio bridging.

**Features:** Direct HTTP, content fetching, built-in validation
```
```

## Package Relationships

### Core Dependencies

```{mermaid}
graph LR
    subgraph "OAuth Layer"
        A[mcp-oauth-dynamicclient] --> B[RFC 7591/7592]
        A --> C[PKCE Support]
        A --> D[JWT Tokens]
    end
    
    subgraph "Protocol Layer"  
        E[mcp-streamablehttp-proxy] --> F[stdio Bridge]
        G[mcp-streamablehttp-client] --> H[Testing]
        I[mcp-fetch-streamablehttp-server] --> J[Direct HTTP]
    end
    
    A --> G
    E --> K[MCP Services]
    G --> L[Integration Tests]
```

### Installation Dependencies

Each package manages its own dependencies through `pyproject.toml`:

```toml
# Common dependency pattern
[project]
dependencies = [
    "fastapi>=0.100.0",
    "httpx>=0.24.0", 
    "pydantic>=2.0.0",
    "uvicorn>=0.23.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0"
]
```

## Development Patterns

### Package Structure

All packages follow the standardized structure:

```
package-name/
├── pyproject.toml          # Package configuration
├── README.md              # Package documentation  
├── CHANGELOG.md           # Version history
├── src/
│   └── package_name/      # Source code
│       ├── __init__.py    # Package exports
│       ├── cli.py         # Command-line interface
│       ├── client.py      # Client implementation
│       └── server.py      # Server implementation
├── tests/                 # Test suite
│   ├── test_*.py         # Unit tests
│   └── conftest.py       # Test configuration
└── examples/             # Usage examples
    └── *.py              # Example scripts
```

### Code Quality Standards

All packages maintain high code quality:

- **Type Hints** - Full typing coverage with mypy
- **Documentation** - Comprehensive docstrings and examples
- **Testing** - 100% test coverage with pytest
- **Linting** - Code formatting with black and ruff
- **Security** - Security scanning and validation

### Version Management

Packages use semantic versioning:

```
MAJOR.MINOR.PATCH
  │     │     │
  │     │     └── Bug fixes
  │     └── New features (backward compatible)
  └── Breaking changes
```

## Installation Methods

### Development Installation

For development and testing:

```bash
# Clone repository
git clone https://github.com/atrawog/mcp-oauth-gateway.git
cd mcp-oauth-gateway

# Install with pixi (recommended)
pixi install

# Install individual package for development
cd mcp-oauth-dynamicclient
pip install -e ".[dev]"
```

### Production Installation

For production use:

```bash
# Install from PyPI (when published)
pip install mcp-oauth-dynamicclient
pip install mcp-streamablehttp-proxy
pip install mcp-streamablehttp-client

# Install from source
pip install git+https://github.com/atrawog/mcp-oauth-gateway.git#subdirectory=mcp-oauth-dynamicclient
```

### Docker Installation

Packages are included in service containers:

```dockerfile
# Copy package source
COPY ../mcp-streamablehttp-proxy /tmp/proxy

# Install package
RUN pip install /tmp/proxy

# Use in application
CMD mcp-streamablehttp-proxy python -m mcp_server
```

## Usage Patterns

### OAuth Client Library

```python
from mcp_oauth_dynamicclient import OAuth2Client

# Initialize client
client = OAuth2Client(
    auth_server="https://auth.yourdomain.com",
    client_name="My MCP Client"
)

# Register dynamically
registration = await client.register()

# Perform OAuth flow
token = await client.authenticate()

# Use token for requests
response = await client.request(
    "GET", 
    "https://mcp-service.yourdomain.com/mcp",
    headers={"Authorization": f"Bearer {token}"}
)
```

### Protocol Bridge

```python
from mcp_streamablehttp_proxy import MCPProxy

# Start proxy server
proxy = MCPProxy(
    command=["python", "-m", "mcp_server"],
    port=3000
)

await proxy.start()
```

### Testing Client

```python
from mcp_streamablehttp_client import MCPClient

# Initialize client with OAuth
client = MCPClient(
    server_url="https://mcp-service.yourdomain.com/mcp",
    oauth_config={
        "auth_server": "https://auth.yourdomain.com",
        "client_name": "Test Client"
    }
)

# Call MCP tools
result = await client.call_tool("fetch", {
    "url": "https://example.com"
})
```

## Testing Framework

### Package Testing

Each package includes comprehensive tests:

```bash
# Run package tests
cd mcp-oauth-dynamicclient
pytest tests/ -v --cov=src/

# Run integration tests
pytest tests/test_integration.py -v

# Run all package tests
just test-packages
```

### Test Categories

1. **Unit Tests** - Individual component testing
2. **Integration Tests** - Cross-component testing  
3. **Protocol Tests** - MCP compliance testing
4. **OAuth Tests** - Authentication flow testing
5. **Error Handling** - Exception and error testing
6. **Performance Tests** - Load and stress testing

### Quality Metrics

- **Test Coverage** - 100% line and branch coverage
- **Type Coverage** - 100% type annotation coverage
- **Documentation** - All public APIs documented
- **Security** - Security scan validation
- **Performance** - Benchmark validation

## Documentation

### API Reference

Each package provides complete API documentation:

- **Public APIs** - All public functions and classes
- **Type Signatures** - Complete type information
- **Examples** - Practical usage examples
- **Error Handling** - Exception documentation

### Development Guides

- **Contributing** - How to contribute to packages
- **Architecture** - Package design and structure
- **Testing** - How to test package changes
- **Deployment** - How to publish packages

## Publishing and Distribution

### PyPI Publishing

Packages can be published to PyPI:

```bash
# Build package
python -m build

# Publish to PyPI
python -m twine upload dist/*
```

### GitHub Releases

Automated releases through GitHub Actions:

```yaml
# .github/workflows/release.yml
name: Release Package
on:
  push:
    tags: ['v*']
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and publish
        run: |
          pip install build twine
          python -m build
          python -m twine upload dist/*
```

## Maintenance and Updates

### Dependency Management

Regular dependency updates:

```bash
# Check for updates
pip-audit scan

# Update dependencies
pip install --upgrade -r requirements.txt

# Security scanning
safety check
```

### Version Updates

Coordinated version management:

1. **Feature Development** - Develop in feature branches
2. **Testing** - Comprehensive testing before release
3. **Version Bump** - Update version numbers consistently
4. **Documentation** - Update documentation and changelog
5. **Release** - Tag and publish new versions

---

**Next Steps:**
- Explore individual package documentation for detailed APIs
- Check {doc}`../development/setup` for development environment
- Review {doc}`../integration/index` for integration patterns