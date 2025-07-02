# PyPI Package Management Commands

Complete PyPI package lifecycle management for publishing Python packages to PyPI and TestPyPI.

## Overview

The justfile provides comprehensive PyPI package management commands for:
- Building Python packages
- Running package tests
- Checking package quality
- Publishing to TestPyPI (testing)
- Publishing to PyPI (production)
- Package cleanup and information

## Supported Packages

The following packages are managed:
- `mcp-streamablehttp-proxy`
- `mcp-oauth-dynamicclient`
- `mcp-streamablehttp-client`
- `mcp-fetch-streamablehttp-server`
- `mcp-echo-streamablehttp-server-stateless`
- `mcp-echo-streamablehttp-server-stateful`

## Building Packages

### `pypi-build` - Build Distribution Files

```bash
# Build all packages
just pypi-build

# Build specific package
just pypi-build mcp-oauth-dynamicclient

# Alias
just pb mcp-streamablehttp-proxy
```

Creates wheel and source distributions in each package's `dist/` directory.

## Testing Packages

### `pypi-test` - Run Package Tests

```bash
# Test all packages
just pypi-test

# Test specific package
just pypi-test mcp-streamablehttp-client

# Alias
just pt mcp-fetch-streamablehttp-server
```

Runs pytest on package test suites if they exist.

## Quality Checks

### `pypi-check` - Validate Packages

```bash
# Check all built packages
just pypi-check

# Check specific package
just pypi-check mcp-oauth-dynamicclient

# Alias
just pc all
```

Uses `twine check` to validate:
- Package metadata
- README rendering
- Distribution file integrity

## Publishing to TestPyPI

### `pypi-upload-test` - Upload to Test Index

```bash
# Upload all packages to TestPyPI
just pypi-upload-test

# Upload specific package
just pypi-upload-test mcp-streamablehttp-proxy

# Alias
just pu mcp-oauth-dynamicclient
```

Requirements:
- `TWINE_USERNAME` and `TWINE_PASSWORD` in `.env`
- Built packages in `dist/` directory
- Unique version numbers

Common solutions for upload failures:
- Version already exists: Increment version in `pyproject.toml`
- Rebuild with new version: `just pypi-build <package>`
- Check existing versions at https://test.pypi.org/project/<package>

### `pypi-publish-test` - Complete Test Workflow

```bash
# Full workflow: build, test, check, upload to TestPyPI
just pypi-publish-test mcp-oauth-dynamicclient

# All packages
just pypi-publish-test

# Alias
just ppt all
```

## Publishing to PyPI (Production)

### `pypi-upload` - Upload to Production

```bash
# Upload all packages to PyPI
just pypi-upload

# Upload specific package
just pypi-upload mcp-streamablehttp-proxy
```

🚨 **WARNING**: This uploads to PRODUCTION PyPI and cannot be undone!

Requirements:
- `TWINE_USERNAME` and `TWINE_PASSWORD` for PyPI (not TestPyPI)
- Thoroughly tested packages
- Unique version numbers

### `pypi-publish` - Complete Production Workflow

```bash
# Full workflow: build, test, check, upload to PyPI
just pypi-publish mcp-oauth-dynamicclient

# All packages
just pypi-publish

# Alias
just pp mcp-streamablehttp-client
```

## Package Information

### `pypi-info` - Show Package Details

```bash
# Show info for all packages
just pypi-info

# Show info for specific package
just pypi-info mcp-oauth-dynamicclient
```

Displays:
- Current version
- Description
- Python requirements
- Built distributions

## Cleanup

### `pypi-clean` - Remove Build Artifacts

```bash
# Clean all packages
just pypi-clean

# Clean specific package
just pypi-clean mcp-streamablehttp-proxy
```

Removes:
- `dist/` directories
- `build/` directories
- `*.egg-info/` directories
- `__pycache__/` directories
- `*.pyc` and `*.pyo` files

## Environment Setup

### Required Environment Variables

Add to `.env` for TestPyPI:
```bash
TWINE_USERNAME=__token__
TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmc...  # Your TestPyPI token
```

For production PyPI:
```bash
TWINE_USERNAME=__token__
TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmc...  # Your PyPI token
```

### Getting API Tokens

1. **TestPyPI**: https://test.pypi.org/manage/account/token/
2. **PyPI**: https://pypi.org/manage/account/token/

## Package Configuration

Each package has a `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mcp-oauth-dynamicclient"
version = "0.1.0"
description = "OAuth 2.1 Dynamic Client Registration"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "httpx",
    "pydantic>=2.0",
]

[project.scripts]
mcp-oauth-client = "mcp_oauth_dynamicclient.cli:main"
```

## Best Practices

1. **Test on TestPyPI First**
   ```bash
   # Always test before production
   just pypi-publish-test mcp-oauth-dynamicclient
   pip install -i https://test.pypi.org/simple/ mcp-oauth-dynamicclient
   ```

2. **Version Management**
   - Use semantic versioning (x.y.z)
   - Increment version for each release
   - Never reuse version numbers

3. **Pre-release Checklist**
   ```bash
   # 1. Update version in pyproject.toml
   # 2. Update changelog
   # 3. Run tests
   just pypi-test mcp-oauth-dynamicclient
   # 4. Build and check
   just pypi-build mcp-oauth-dynamicclient
   just pypi-check mcp-oauth-dynamicclient
   ```

4. **Release Workflow**
   ```bash
   # TestPyPI first
   just pypi-publish-test mcp-oauth-dynamicclient

   # Test installation
   pip install -i https://test.pypi.org/simple/ mcp-oauth-dynamicclient==0.1.0

   # If all good, release to PyPI
   just pypi-publish mcp-oauth-dynamicclient
   ```

## Troubleshooting

### Version Already Exists

```bash
# Check current version
just pypi-info mcp-oauth-dynamicclient

# Update version in pyproject.toml
# Then rebuild
just pypi-build mcp-oauth-dynamicclient
```

### Authentication Issues

```bash
# Verify environment variables
echo $TWINE_USERNAME
echo ${#TWINE_PASSWORD}  # Should show token length

# Test authentication
pixi run twine upload --repository testpypi --dry-run dist/*
```

### Package Not Found After Upload

```bash
# TestPyPI needs --index-url
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ package-name

# PyPI should work directly
pip install package-name
```

## Aliases Reference

For convenience, these aliases are available:

| Alias | Full Command |
|-------|--------------|
| `pb` | `pypi-build` |
| `pt` | `pypi-test` |
| `pc` | `pypi-check` |
| `pu` | `pypi-upload` |
| `ppt` | `pypi-publish-test` |
| `pp` | `pypi-publish` |

Example:
```bash
# These are equivalent
just pypi-build mcp-oauth-dynamicclient
just pb mcp-oauth-dynamicclient
```

Remember: **Always test on TestPyPI before production releases!**
