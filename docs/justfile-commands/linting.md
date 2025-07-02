# Linting and Code Quality Commands

Divine code quality enforcement following the sacred commandments of CLAUDE.md!

## Overview

The justfile provides comprehensive linting and code quality commands for:
- Code linting with automatic fixes
- Code formatting enforcement
- Pydantic deprecation hunting
- Security vulnerability scanning
- Pre-commit hook execution

## Core Linting Command

### `lint` - The Divine Code Quality Check

```bash
# Full divine quality check with clear error reporting
just lint
```

This sacred incantation performs:
1. **First Pass**: Checking for ALL issues (including manual fixes needed)
2. **Second Pass**: Applying automatic fixes
3. **Third Pass**: Checking for remaining issues needing MANUAL fixes
4. **Fourth Pass**: Running code formatter
5. **Fifth Pass**: Running ALL pre-commit hooks

⚠️ **EXITS WITH ERROR if manual fixes are needed!**

## Quick Linting

### `lint-quick` - Fast Feedback

```bash
# Quick check without auto-fixing (read-only)
just lint-quick
```

Just runs ruff check without modifications - perfect for CI/CD or quick checks.

## Manual Fix Detection

### `lint-manual` - Show Only Manual Fixes

```bash
# Show ONLY issues that need manual fixes
just lint-manual
```

This command:
- Runs ruff with fixes to see what CAN be auto-fixed
- Shows only the errors that CANNOT be auto-fixed
- Provides helpful tips for fixing

## Auto-Fix Command

### `lint-fix` - Apply Automatic Fixes

```bash
# Apply all automatic fixes
just lint-fix
```

Automatically:
- Applies ruff fixes
- Formats code with ruff format
- Does NOT run other pre-commit hooks

## Code Formatting

### `format` - Divine Code Formatting

```bash
# Format code with divine standards
just format
```

Runs the ruff-format pre-commit hook on all files.

### `format-check` - Check Formatting

```bash
# Check formatting without changes
just format-check
```

Verifies formatting compliance without making changes.

## Pydantic Compliance

### `lint-pydantic` - Hunt Deprecations

```bash
# Hunt for Pydantic deprecations
just lint-pydantic
```

Runs `scripts/lint_pydantic_compliance.py` to find:
- Deprecated Pydantic v1 patterns
- Migration opportunities to v2
- Best practice violations

## Comprehensive Linting

### `lint-all` - Complete Linting

```bash
# Complete linting with deprecation hunting
just lint-all
```

Runs:
1. Pre-commit ruff checks
2. Pydantic deprecation hunting

### `lint-comprehensive` - Full Code Quality

```bash
# Fix, format, and hunt deprecations
just lint-comprehensive
```

The most thorough check:
1. Ruff linting
2. Code formatting
3. Pydantic deprecation hunting

## Security Scanning

### `security-scan` - Bandit Security Analysis

```bash
# Run security scan with text output
just security-scan
```

Uses Bandit to find:
- Hard-coded passwords
- SQL injection risks
- Insecure random generators
- Shell injection vulnerabilities
- And more security issues

### `security-scan-json` - JSON Security Report

```bash
# Generate JSON security report
just security-scan-json
```

Creates `bandit-report.json` with detailed findings for CI/CD integration.

## Help Command

### `lint-help` - Command Guide

```bash
# Show linting command guide
just lint-help
```

Displays a helpful guide explaining all linting commands and their purposes.

## Pre-commit Integration

All linting commands integrate with pre-commit hooks defined in `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

## Ruff Configuration

Linting rules are configured in `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "DTZ",  # flake8-datetimez
    "S",    # flake8-bandit
    "SIM",  # flake8-simplify
    "RUF",  # Ruff-specific rules
]
```

## Best Practices

1. **Always use `just lint` before committing**
   - Catches all issues
   - Auto-fixes what it can
   - Shows manual fixes needed

2. **Use `lint-quick` in CI/CD**
   - Fast, read-only check
   - No file modifications

3. **Run security scans regularly**
   ```bash
   # Add to CI/CD pipeline
   just security-scan-json
   ```

4. **Fix manual issues immediately**
   - Don't let them accumulate
   - Use `lint-manual` to focus

## Common Linting Patterns

### Import Organization
```python
# Ruff automatically organizes imports:
# 1. Standard library
# 2. Third-party packages
# 3. Local imports
```

### Code Simplification
```python
# Before (flagged by SIM rules)
if x == True:
    pass

# After (auto-fixed)
if x:
    pass
```

### Security Issues
```python
# Flagged by S rules
password = "hardcoded"  # S105: Hardcoded password

# Fix: Use environment variables
password = os.getenv("PASSWORD")
```

## Troubleshooting

### Lint Errors That Can't Auto-Fix

```bash
# See exactly what needs manual fixing
just lint-manual

# Common manual fixes:
# - Undefined variables
# - Syntax errors
# - Some security issues
# - Complex refactoring
```

### Pre-commit Hook Failures

```bash
# Update pre-commit hooks
pixi run pre-commit autoupdate

# Run specific hook
pixi run pre-commit run ruff --all-files
```

### Conflicting Fixes

If ruff and formatter conflict:
1. Run `just lint-fix` first
2. Then run `just format`
3. Finally run `just lint` to verify

Remember: **Divine code quality brings production salvation!**
