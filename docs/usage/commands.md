# Command Reference

All commands in the MCP OAuth Gateway are executed through `just`, following the project's "blessed trinity" approach. This reference covers all available commands.

```{tip}
Run `just --list` to see all available commands with descriptions.
```

## Service Management

### Starting and Stopping Services

```bash
# Start all services
just up

# Start services with options
just up --force-recreate

# Start all services with fresh build
just up-fresh

# Stop all services  
just down

# Stop with options (remove volumes/orphans)
just down --volumes --remove-orphans
```

### Building and Rebuilding

```bash
# Build all services
just build

# Build specific service(s)
just build auth
just build auth mcp-fetch  # Multiple services

# Rebuild specific service (with no-cache by default)
just rebuild auth
just rebuild mcp-fetch mcp-memory  # Multiple services
```

### Service Logs

```bash
# View all logs
just logs

# View specific service logs
just logs auth
just logs traefik

# Follow logs (real-time)
just logs -f
just logs -f mcp-fetch

# Follow specific service logs (alternate)
just logs-follow auth

# Last N lines
just logs --tail=100

# Purge all container logs
just logs-purge
```

## Health Monitoring

### Health Checks

```bash
# Ensure all services are ready (used before tests)
just ensure-services-ready

# Comprehensive health check
just check-health

# Quick health check
just health-quick

# Check SSL certificates
just check-ssl
```

### Service Status

```bash
# Execute commands in containers
just exec auth curl http://localhost:8000/health
just exec redis redis-cli ping
```

## OAuth Token Management

### Token Generation

```bash
# Generate JWT secret (one-time setup)
just generate-jwt-secret

# Generate RSA keys for JWT signing
just generate-rsa-keys

# Generate GitHub OAuth token (interactive)
just generate-github-token

# Generate MCP client token
just mcp-client-token

# Complete MCP client token flow with auth code
just mcp-client-token-complete <auth_code>
```

### Token Operations

```bash
# Validate current tokens
just validate-tokens

# Show all OAuth data
just oauth-show-all

# Show OAuth statistics
just oauth-stats

# List active registrations
just oauth-list-registrations

# List active tokens
just oauth-list-tokens

# Purge expired tokens (dry run)
just oauth-purge-expired-dry

# Purge expired tokens (execute)
just oauth-purge-expired
```

### OAuth Data Management

```bash
# Backup OAuth data
just oauth-backup

# List backups
just oauth-backup-list

# Restore from latest backup
just oauth-restore

# Restore from specific backup
just oauth-restore-file oauth-backup-20240101-120000.json

# View backup contents
just oauth-backup-view
just oauth-backup-view-file oauth-backup-20240101-120000.json

# Restore with clear (removes existing data first)
just oauth-restore-clear

# Dry run restore
just oauth-restore-dry
```

## Testing

### Running Tests

```bash
# Run all tests
just test

# Run specific test file
just test tests/test_oauth_flow.py

# Run tests matching pattern
just test -k oauth

# Run with verbose output
just test -v

# Run with debugging
just test --pdb

# Multiple options
just test tests/test_oauth_flow.py -v -s
```

### Test Categories

```bash
# OAuth flow tests
just test-oauth-flow

# MCP protocol tests
just test-mcp-protocol

# Claude.ai integration tests
just test-claude-integration

# MCP hostname tests
just test-mcp-hostnames
```

### Coverage Analysis

```bash
# Production coverage with sidecar
just test-sidecar-coverage

# Debug coverage setup
just debug-coverage

# View coverage report
open htmlcov/index.html
```

### Test Cleanup

```bash
# Show test data that would be cleaned
just test-cleanup-show

# Actually clean test data
just test-cleanup
```

## Development Tools

### Code Quality

```bash
# Run linting
just lint

# Fix linting issues automatically
just lint-fix

# Format code
just format

# Hunt for Pydantic deprecations
just lint-pydantic

# Complete linting with deprecation hunting
just lint-all

# Comprehensive linting: fix, format, and hunt deprecations
just lint-comprehensive
```

### Documentation

```bash
# Build documentation
just docs-build
```

### Analysis Tools

```bash
# Analyze OAuth logs
just analyze-oauth-logs

# Check MCP hostnames
just check-mcp-hostnames

# Diagnose test failures
just diagnose-tests
```

## Utility Commands

### Docker Operations

```bash
# Create Docker network
just network-create

# Create required volumes
just volumes-create

# Execute command in container
just exec redis redis-cli
just exec auth bash

# Generate docker-compose includes
just generate-includes
```

### Configuration

```bash
# Claude Code setup
just setup-claude-code

# Create MCP config for Claude Code
just create-mcp-config

# Add MCP servers to Claude Code
just mcp-add
```

### Token Management

```bash
# Check token expiration
just check-token-expiry

# Refresh OAuth tokens
just refresh-tokens

# Validate all tokens
just validate-tokens

# Delete specific client registration
just oauth-delete-registration <client_id>

# Delete client registration and ALL associated tokens
just oauth-delete-client-complete <client_id>

# Delete specific token
just oauth-delete-token <jti>

# Delete all registrations (DANGEROUS!)
just oauth-delete-all-registrations

# Delete all tokens (DANGEROUS!)
just oauth-delete-all-tokens
```

## Script Runner

### Universal Script Runner

The project includes a universal script runner for executing Python scripts:

```bash
# Run any script from the scripts/ directory
just run <script_name> [args...]

# Examples:
just run generate_oauth_token
just run refresh_tokens
just run check_token_expiry
just run manage_oauth_data list-registrations
just run analyze_oauth_logs
```

## Command Patterns

### Using Arguments

Many commands accept arguments:

```bash
# Single argument
just rebuild auth

# Multiple arguments
just rebuild auth mcp-fetch mcp-memory

# With options
just test -v -k oauth

# Aliases for common commands
just t  # alias for test
just b  # alias for build
just u  # alias for up
just d  # alias for down
just r  # alias for rebuild
```

### Environment Variables

Commands respect environment variables:

```bash
# Override timeout
TEST_TIMEOUT=60 just test

# Custom domain
BASE_DOMAIN=test.com just up
```

### Chaining Commands

```bash
# Stop, rebuild, and start
just down && just rebuild auth && just up

# Run tests and generate report
just test && just coverage-html
```

## Common Workflows

### Initial Setup

```bash
just setup
just generate-jwt-secret
just generate-rsa-keys
just up
just check-health
just generate-github-token
```

### Daily Operations

```bash
# Morning startup
just up
just check-health
just logs -f

# Evening shutdown
just oauth-backup
just down
```

### Development Cycle

```bash
# Make changes
just rebuild mcp-fetch
just test tests/test_mcp_protocol.py -v
just logs -f mcp-fetch
```

### Troubleshooting

```bash
# Service issues
just logs -f problematic-service
just rebuild problematic-service
just exec problematic-service bash

# OAuth issues
just oauth-show-all
just analyze-oauth-logs
just validate-tokens
just diagnose-tests
```

## Getting Help

```bash
# List all commands
just --list

# Show command definition
just --show <command>
```

## Next Steps

- [Service Management](service-management.md) - Managing services
- [Token Management](token-management.md) - OAuth token operations
- [Testing Guide](testing.md) - Running tests
- [Monitoring](monitoring.md) - Troubleshooting guide