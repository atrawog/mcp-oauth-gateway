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

# Stop all services  
just down

# Restart all services
just restart

# Restart specific service
just restart auth
just restart mcp-fetch
```

### Building and Rebuilding

```bash
# Build all services
just build

# Build without cache
just build-no-cache

# Rebuild specific service
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

# Last N lines
just logs --tail=100
```

## Health Monitoring

### Health Checks

```bash
# Comprehensive health check
just check-health

# Quick health check
just health-quick

# Check SSL certificates
just check-ssl

# OAuth discovery endpoint check
just check-oauth-discovery
```

### Service Status

```bash
# Docker compose status
just ps

# Detailed service info
just exec auth curl http://localhost:8000/health
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
```

### Token Operations

```bash
# Validate current tokens
just validate-tokens

# Show all OAuth data
just oauth-show-all

# List active registrations
just oauth-list-registrations

# List active tokens
just oauth-list-tokens

# Count OAuth entities
just oauth-count

# Purge expired tokens
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
just oauth-restore backups/oauth_backup_20240101_120000.json

# View backup contents
just oauth-backup-view
just oauth-backup-view backups/oauth_backup_20240101_120000.json
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
just test-verbose

# Run with debugging
just test --pdb
```

### Test Categories

```bash
# OAuth flow tests
just test-oauth-flow

# MCP protocol tests
just test-mcp-protocol

# Claude.ai integration tests
just test-claude-integration

# Security tests
just test-security

# CORS tests
just test-cors
```

### Coverage Analysis

```bash
# Run tests with coverage
just test-coverage

# Production coverage with sidecar
just test-sidecar-coverage

# Generate HTML coverage report
just coverage-html

# View coverage report
open htmlcov/index.html
```

### Test Cleanup

```bash
# Show test data that would be cleaned
just test-cleanup-show

# Actually clean test data
just test-cleanup

# Clean test data older than N hours
just test-cleanup-old 24
```

## Development Tools

### Code Quality

```bash
# Run linting
just lint

# Format code
just format

# Type checking
just typecheck

# Run all quality checks
just quality
```

### Documentation

```bash
# Build documentation
just docs-build

# Clean documentation build
just docs-clean

# Serve documentation locally
just docs-serve
```

### Analysis Tools

```bash
# Analyze OAuth logs
just analyze-oauth-logs

# Analyze specific timeframe
just analyze-oauth-logs-timeframe "2024-01-01 00:00:00" "2024-01-01 23:59:59"

# Session analysis
just analyze-sessions

# Performance analysis
just analyze-performance
```

## Utility Commands

### Docker Operations

```bash
# Create Docker network
just network-create

# Execute command in container
just exec redis redis-cli
just exec auth bash

# Clean Docker resources
just docker-clean

# Show Docker disk usage
just docker-usage
```

### Configuration

```bash
# Validate .env file
just validate-env

# Show current configuration
just show-config

# Generate example .env
just generate-env-example
```

### Database Operations

```bash
# Redis CLI access
just redis-cli

# Redis backup
just redis-backup

# Redis restore
just redis-restore backup.rdb

# Clear Redis (DANGEROUS!)
just redis-clear
```

## Advanced Commands

### Debugging

```bash
# Enable debug mode
just debug-on

# Disable debug mode
just debug-off

# Show debug status
just debug-status

# Trace specific request
just trace-request <request-id>
```

### Performance

```bash
# Run performance tests
just perf-test

# Memory profiling
just profile-memory

# CPU profiling
just profile-cpu
```

### Security

```bash
# Security audit
just security-audit

# Update dependencies
just update-deps

# Check for vulnerabilities
just check-vulnerabilities
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
just network-create
just up
just check-health
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
just test tests/test_mcp_fetch_integration.py
just logs mcp-fetch
```

### Troubleshooting

```bash
# Service issues
just logs -f problematic-service
just restart problematic-service
just exec problematic-service bash

# OAuth issues
just oauth-show-all
just analyze-oauth-logs
just validate-tokens
```

## Getting Help

```bash
# List all commands
just --list

# Show command definition
just --show <command>

# Command help
just help
```

## Next Steps

- [Service Management](service-management.md) - Managing services
- [Token Management](token-management.md) - OAuth token operations
- [Testing Guide](testing.md) - Running tests
- [Monitoring](monitoring.md) - Troubleshooting guide