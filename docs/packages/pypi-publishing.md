# PyPI Publishing Guide

This guide covers building, testing, and publishing the MCP OAuth Gateway Python packages to PyPI using the integrated just commands.

## Overview

The MCP OAuth Gateway contains four Python packages that can be published to PyPI:

- **mcp-oauth-dynamicclient** - OAuth 2.1 Authorization Server Library
- **mcp-streamablehttp-proxy** - Universal stdio-to-HTTP Bridge  
- **mcp-streamablehttp-client** - Client Bridge with OAuth Support
- **mcp-fetch-streamablehttp-server** - Native MCP Server Implementation

## Prerequisites

### Environment Setup

1. **Install Dependencies**:
   ```bash
   pixi install
   ```

2. **PyPI Account Setup**:
   - Create accounts on [PyPI](https://pypi.org) and [TestPyPI](https://test.pypi.org)
   - Generate API tokens for both accounts
   - Configure authentication (see [Authentication Setup](#authentication-setup))

3. **Verify just Commands**:
   ```bash
   just --list | grep pypi
   ```

### Authentication Setup

#### Option 1: Environment Variables (Recommended)

Set these environment variables or add to your `.env` file:

```bash
# For PyPI
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmcC...  # Your PyPI API token

# For TestPyPI
export TWINE_TEST_USERNAME=__token__
export TWINE_TEST_PASSWORD=pypi-AgEIcHlwaS5vcmcC...  # Your TestPyPI API token
```

#### Option 2: .pypirc Configuration

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...
```

## Command Reference

### Individual Operations

| Command | Purpose | Alias |
|---------|---------|-------|
| `just pypi-build [package]` | Build wheel and source distributions | `pb` |
| `just pypi-test [package]` | Run package tests | `pt` |
| `just pypi-check [package]` | Validate distributions with twine | `pc` |
| `just pypi-upload-test [package]` | Upload to TestPyPI | - |
| `just pypi-upload [package]` | Upload to PyPI | `pu` |

### Complete Workflows

| Command | Purpose | Alias |
|---------|---------|-------|
| `just pypi-publish-test [package]` | Complete TestPyPI workflow | `ppt` |
| `just pypi-publish [package]` | Complete PyPI workflow | `pp` |

### Utilities

| Command | Purpose |
|---------|---------|
| `just pypi-clean [package]` | Clean build artifacts |
| `just pypi-info [package]` | Show package information |

### Package Selection

- **`all` (default)**: Operates on all four packages
- **Specific package**: Use exact directory name (e.g., `mcp-oauth-dynamicclient`)

## Publishing Workflows

### Testing Workflow (TestPyPI)

Always test on TestPyPI before publishing to production PyPI:

```bash
# Test complete workflow for all packages
just pypi-publish-test

# Test specific package
just pypi-publish-test mcp-oauth-dynamicclient

# Manual step-by-step testing
just pypi-build mcp-oauth-dynamicclient
just pypi-test mcp-oauth-dynamicclient
just pypi-check mcp-oauth-dynamicclient
just pypi-upload-test mcp-oauth-dynamicclient
```

### Production Workflow (PyPI)

```bash
# Publish all packages to PyPI
just pypi-publish

# Publish specific package
just pypi-publish mcp-streamablehttp-proxy

# Manual step-by-step production
just pypi-build
just pypi-test
just pypi-check
just pypi-upload  # Requires double confirmation
```

## Package-Specific Considerations

### mcp-oauth-dynamicclient

**Key Features:**
- OAuth 2.1 and RFC 7591/7592 compliance
- Redis integration for token storage
- FastAPI-based async implementation

**Publishing Notes:**
- Requires Python ≥3.9
- Has comprehensive test suite
- Critical for gateway authentication

**Pre-publication Checklist:**
```bash
# Verify OAuth compliance tests pass
just pypi-test mcp-oauth-dynamicclient

# Check Redis connectivity in tests
just test tests/test_oauth_flow.py -v
```

### mcp-streamablehttp-proxy

**Key Features:**
- Universal stdio-to-HTTP bridge
- Process management for MCP servers
- Health monitoring integration

**Publishing Notes:**
- Broad Python compatibility (≥3.8)
- Lightweight with minimal dependencies
- Core infrastructure component

**Pre-publication Checklist:**
```bash
# Verify proxy functionality
just pypi-test mcp-streamablehttp-proxy

# Test with actual MCP server
just test-mcp-protocol -v
```

### mcp-streamablehttp-client

**Key Features:**
- OAuth device flow implementation
- Token refresh capabilities
- CLI tools for MCP interaction

**Publishing Notes:**
- Requires Python ≥3.10
- Rich CLI interface with Click
- Client-side OAuth handling

**Pre-publication Checklist:**
```bash
# Test OAuth flows
just pypi-test mcp-streamablehttp-client

# Verify token generation
just mcp-client-token
```

### mcp-fetch-streamablehttp-server

**Key Features:**
- Native streamable HTTP implementation
- Web scraping with robots.txt compliance
- Reference server implementation

**Publishing Notes:**
- Requires Python ≥3.11 (latest features)
- Specialized dependencies (robotspy, BeautifulSoup4)
- Performance optimized with uvloop

**Pre-publication Checklist:**
```bash
# Test native implementation
just pypi-test mcp-fetch-streamablehttp-server

# Verify fetch functionality
just test tests/test_mcp_hostnames.py -v
```

## Version Management

### Semantic Versioning

All packages follow [semantic versioning](https://semver.org/):

- **Major (x.0.0)**: Breaking API changes
- **Minor (0.x.0)**: New features, backward compatible
- **Patch (0.0.x)**: Bug fixes and improvements

### Version Updates

1. **Update pyproject.toml**:
   ```toml
   [project]
   version = "1.2.3"
   ```

2. **Verify Version**:
   ```bash
   just pypi-info package-name
   ```

3. **Tag Release** (optional):
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```

## Quality Assurance

### Pre-Publication Testing

```bash
# Complete testing workflow
just lint-comprehensive      # Fix code formatting
just test-all               # Run full test suite
just pypi-build all         # Build all packages
just pypi-check all         # Validate distributions
```

### Distribution Validation

The `pypi-check` command uses `twine check` to validate:
- Package metadata completeness
- README rendering on PyPI
- File structure correctness
- Security vulnerabilities

### Test Installation

After TestPyPI upload, verify installation:

```bash
# Install from TestPyPI
pip install -i https://test.pypi.org/simple/ mcp-oauth-dynamicclient

# Test basic import
python -c "import mcp_oauth_dynamicclient; print('Import successful')"
```

## Troubleshooting

### Common Issues

#### Build Failures

```bash
# Clean and rebuild
just pypi-clean package-name
just pypi-build package-name
```

#### Test Failures

```bash
# Run verbose tests
just pypi-test package-name
just test tests/ -v -s --tb=long
```

#### Upload Failures

```bash
# Check authentication
pixi run twine --version
echo $TWINE_USERNAME
echo $TWINE_PASSWORD

# Verify package format
just pypi-check package-name
```

#### Version Conflicts

```bash
# Check existing versions on PyPI
pixi run pip index versions package-name

# Update version in pyproject.toml
# Rebuild and upload
```

### Authentication Issues

#### Token Problems

1. Verify token format (should start with `pypi-`)
2. Check token scope and permissions
3. Regenerate tokens if necessary

#### Permission Errors

1. Verify PyPI project ownership
2. Check collaborator permissions
3. Use project-scoped tokens

### Package-Specific Issues

#### mcp-oauth-dynamicclient

- **Redis Connection**: Ensure Redis is running for tests
- **OAuth Secrets**: Check GitHub OAuth configuration
- **JWT Validation**: Verify secret generation

#### mcp-streamablehttp-proxy

- **Process Management**: Check subprocess handling
- **Port Conflicts**: Verify available ports
- **Health Checks**: Ensure MCP protocol compliance

#### mcp-streamablehttp-client

- **OAuth Flow**: Test device flow manually
- **Token Storage**: Check credential persistence
- **CLI Interface**: Verify Click command structure

#### mcp-fetch-streamablehttp-server

- **Python Version**: Requires Python ≥3.11
- **Dependencies**: Check robotspy availability
- **Performance**: Verify uvloop installation

## Security Considerations

### Token Management

- **Never commit tokens** to version control
- **Use API tokens** instead of passwords
- **Scope tokens** to specific projects when possible
- **Rotate tokens** regularly

### Package Security

- **Scan dependencies** for vulnerabilities
- **Review package contents** before upload
- **Use signed commits** for releases
- **Monitor package** for unauthorized changes

### Distribution Security

```bash
# Verify package integrity
just pypi-check package-name

# Check for security vulnerabilities
pixi run pip-audit dist/*.whl
```

## Automation

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Publish to PyPI
on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Pixi
        uses: prefix-dev/setup-pixi@v0.4.1
      - name: Build packages
        run: pixi run just pypi-build
      - name: Test packages
        run: pixi run just pypi-test
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: pixi run just pypi-upload
```

### Automated Testing

```bash
# Set up automated testing workflow
just pypi-clean
just pypi-build
just pypi-test
just pypi-check
just pypi-upload-test  # Test on TestPyPI first
```

## Best Practices

### Release Preparation

1. **Update Documentation**: Ensure README and docs are current
2. **Review Changelog**: Document all changes since last release
3. **Test Thoroughly**: Run complete test suite
4. **Version Bump**: Update version appropriately
5. **Clean Build**: Remove old artifacts

### Publishing Strategy

1. **TestPyPI First**: Always test on TestPyPI
2. **Staged Rollout**: Consider publishing packages individually
3. **Dependency Order**: Publish dependencies before dependents
4. **Monitor**: Watch for issues after publication

### Post-Publication

1. **Verify Installation**: Test installation from PyPI
2. **Update Documentation**: Link to PyPI packages
3. **Tag Release**: Create git tags for releases
4. **Announce**: Notify users of new releases

## Examples

### Publishing Single Package

```bash
# Complete workflow for OAuth client
just pypi-publish-test mcp-oauth-dynamicclient
# Review TestPyPI, test installation
just pypi-publish mcp-oauth-dynamicclient
```

### Publishing All Packages

```bash
# Test all packages
just pypi-publish-test

# If testing successful, publish all
just pypi-publish
```

### Development Cycle

```bash
# Development workflow
just lint-comprehensive
just test-all
just pypi-clean
just pypi-build
just pypi-test
just pypi-upload-test
# Review, then:
just pypi-upload
```

This guide ensures reliable, secure publication of all MCP OAuth Gateway packages to PyPI while maintaining quality standards and following best practices.