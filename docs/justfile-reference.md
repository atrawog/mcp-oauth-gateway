# Justfile Reference

The justfile is the divine command center for the MCP OAuth Gateway project, following the sacred commandments of CLAUDE.md. All commands flow through `just` as decreed by the Holy Trinity of Tools.

## Justfile Configuration

The justfile uses these sacred settings:

```justfile
set dotenv-load := true          # Load .env automatically
set dotenv-required              # Die if .env is missing
set positional-arguments := true # Enable blessed argument passing
set allow-duplicate-recipes      # Allow recipe overloading
set export := true               # Export all variables as environment
set quiet                        # Silence the incantations
```

## Command Categories

### 🧪 Testing Commands

All testing follows the divine commandment: **No Mocks or Burn in Production Hell!**

| Command | Description | Example |
|---------|-------------|---------|
| `test` | Universal test runner with flexible arguments | `just test -k auth -v` |
| `test-parallel` | Run tests in parallel using all CPU cores | `just test-parallel` |
| `test-n` | Run tests with specific worker count | `just test-n 4` |
| `test-fast` | Parallel tests with worksteal distribution | `just test-fast` |
| `test-by-module` | Keep tests in same file together | `just test-by-module` |
| `test-by-class` | Keep tests in same class together | `just test-by-class` |
| `test-serial` | Run only serial tests (marked with @pytest.mark.serial) | `just test-serial` |
| `test-parallel-safe` | Run parallel tests excluding serial ones | `just test-parallel-safe` |
| `test-sidecar-coverage` | Production container coverage testing | `just test-sidecar-coverage` |

### 🐳 Docker Operations

Service orchestration through docker-compose as mandated by the commandments.

| Command | Description | Example |
|---------|-------------|---------|
| `build` | Build services (all or specific) | `just build auth mcp-fetch` |
| `up` | Start services with health checks | `just up` |
| `up-fresh` | Fresh build and start | `just up-fresh` |
| `down` | Stop services | `just down --volumes` |
| `rebuild` | Rebuild from scratch (no-cache) | `just rebuild auth` |
| `remove-orphans` | Remove orphan containers | `just remove-orphans` |
| `logs` | View logs flexibly | `just logs -f auth` |
| `exec` | Execute commands in containers | `just exec redis redis-cli` |

### 📊 Logging Management

Centralized logging as decreed: **Scattered logs = lost wisdom!**

| Command | Description | Example |
|---------|-------------|---------|
| `logs-files` | View file-based logs | `just logs-files auth` |
| `logs-stats` | Show log statistics | `just logs-stats` |
| `logs-clean` | Clean logs (with safety prompt) | `just logs-clean 7` |
| `logs-clean-force` | Force clean without prompt | `just logs-clean-force` |
| `logs-rotate` | Manually rotate logs | `just logs-rotate` |
| `logs-rotation-setup` | Setup log rotation (requires sudo) | `just logs-rotation-setup` |
| `logs-purge` | Purge all container logs | `just logs-purge` |
| `logs-test` | Test logging configuration | `just logs-test` |

### 🔐 OAuth Management

Complete OAuth lifecycle management following RFC 7591/7592.

| Command | Description | Example |
|---------|-------------|---------|
| `oauth-list-registrations` | Show all client registrations | `just oauth-list-registrations` |
| `oauth-list-tokens` | Show all active tokens | `just oauth-list-tokens` |
| `oauth-delete-registration` | Delete specific client | `just oauth-delete-registration client_123` |
| `oauth-delete-client-complete` | Delete client and all data | `just oauth-delete-client-complete client_123` |
| `oauth-stats` | Show OAuth statistics | `just oauth-stats` |
| `oauth-show-all` | Display all OAuth data | `just oauth-show-all` |
| `oauth-purge-expired` | Remove expired tokens | `just oauth-purge-expired` |
| `oauth-backup` | Backup OAuth data | `just oauth-backup` |
| `oauth-restore` | Restore from latest backup | `just oauth-restore` |

### 🔑 Token & Secret Generation

Sacred token generation following divine security practices.

| Command | Description | Example |
|---------|-------------|---------|
| `generate-jwt-secret` | Generate JWT secret to .env | `just generate-jwt-secret` |
| `generate-rsa-keys` | Generate RS256 signing keys | `just generate-rsa-keys` |
| `generate-redis-password` | Generate Redis password | `just generate-redis-password` |
| `generate-all-secrets` | Generate all required secrets | `just generate-all-secrets` |
| `generate-github-token` | OAuth flow for GitHub token | `just generate-github-token` |
| `mcp-client-token` | Generate MCP client token | `just mcp-client-token` |
| `refresh-tokens` | Refresh OAuth tokens | `just refresh-tokens` |
| `validate-tokens` | Validate all tokens | `just validate-tokens` |

### 🧹 Code Quality

Following the divine linting commandments.

| Command | Description | Example |
|---------|-------------|---------|
| `lint` | Run all quality checks | `just lint` |
| `lint-quick` | Quick ruff check only | `just lint-quick` |
| `lint-fix` | Auto-fix linting issues | `just lint-fix` |
| `format` | Format code | `just format` |
| `format-check` | Check formatting | `just format-check` |
| `lint-pydantic` | Hunt Pydantic deprecations | `just lint-pydantic` |
| `lint-comprehensive` | Full lint, format, deprecations | `just lint-comprehensive` |

### 🏥 Health & Monitoring

Real health checks following: **sleep = random production failures!**

| Command | Description | Example |
|---------|-------------|---------|
| `check-health` | Complete health check (3 steps) | `just check-health` |
| `check-tokens` | Check environment tokens | `just check-tokens` |
| `check-services` | Check Docker services | `just check-services` |
| `health-quick` | Quick endpoint check | `just health-quick` |
| `status` | Show service status | `just status` |
| `check-ssl` | Verify SSL certificates | `just check-ssl` |
| `check-mcp-hostnames` | Test MCP hostname connectivity | `just check-mcp-hostnames` |

### 📚 Documentation

Documentation with Jupyter Book as commanded.

| Command | Description | Example |
|---------|-------------|---------|
| `docs-build` | Build Jupyter Book docs | `just docs-build` |

### 🛠️ Utility Commands

Essential utilities for development workflow.

| Command | Description | Example |
|---------|-------------|---------|
| `run` | Universal script runner | `just run analyze_logs --verbose` |
| `ensure-services-ready` | Verify services before operations | Called automatically |
| `network-create` | Create docker network | Called by build/up |
| `volumes-create` | Create required volumes | Called by build/up |
| `generate-includes` | Generate compose includes | Called by build/up |
| `generate-middlewares` | Generate Traefik config | Called by build/up |
| `setup` | Initial project setup | `just setup` |

### 🧪 Test Utilities

Specialized testing and debugging commands.

| Command | Description | Example |
|---------|-------------|---------|
| `test-cleanup-show` | Show test registrations | `just test-cleanup-show` |
| `test-cleanup` | Clean test data | `just test-cleanup` |
| `diagnose-tests` | Diagnose test failures | `just diagnose-tests` |
| `debug-coverage` | Debug coverage setup | `just debug-coverage` |

### 📦 PyPI Package Management

Commands for managing Python packages.

| Command | Description | Example |
|---------|-------------|---------|
| `pypi-build` | Build Python packages | `just pypi-build mcp-oauth-dynamicclient` |
| `pypi-test` | Test Python packages | `just pypi-test all` |

## Command Aliases

Quick shortcuts for common operations:

| Alias | Full Command |
|-------|--------------|
| `t` | `test` |
| `b` | `build` |
| `u` | `up` |
| `d` | `down` |
| `r` | `rebuild` |

## Sacred Patterns

### Flexible Arguments with Positional Parameters

```bash
# Test with any pytest arguments
just test -k "oauth" -v -s --pdb

# Build specific services
just build auth mcp-fetch

# Follow logs for specific service
just logs -f auth
```

### Universal Script Runner

```bash
# Run any script from scripts/ directory
just run analyze_oauth_logs
just run check_services_ready
just run generate_coverage_report
```

### Service Operations

```bash
# Execute commands in containers
just exec redis redis-cli
just exec auth python manage.py shell

# Rebuild specific services
just rebuild auth mcp-fetch
```

## Environment Requirements

The justfile requires:
1. `.env` file present (enforced by `set dotenv-required`)
2. Pixi installed and configured
3. Docker and docker-compose available
4. Python environment via pixi

## The Divine Flow

A typical development workflow:

```bash
# Initial setup
just setup
just generate-all-secrets

# Development cycle
just up
just test
just logs -f auth

# OAuth management
just oauth-stats
just generate-github-token

# Cleanup
just down
just test-cleanup
```

Remember: **If you're not typing "just", you're typing BLASPHEMY!**
