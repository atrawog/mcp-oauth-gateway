# Utility Commands

Essential utility commands for development, monitoring, and maintenance of the MCP OAuth Gateway.

## Overview

Utility commands provide:
- Health monitoring and status checks
- Script execution helpers
- Network and volume management
- Configuration generation
- Development tools

## Health Monitoring

### Comprehensive Health Check

```bash
# Full 3-step health check
just check-health

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏥 MCP OAuth Gateway Health Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1/3: Checking environment tokens...
Step 2/3: Checking Docker services...
Step 3/3: Checking service endpoints...
✅ Health check complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Individual Checks

```bash
# Check only environment tokens
just check-tokens

# Check only Docker services
just check-services

# Quick endpoint check
just health-quick

# SSL certificate check
just check-ssl

# MCP hostname connectivity
just check-mcp-hostnames
```

### Service Status

```bash
# Show detailed service status
just status

Service Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ traefik    - healthy (up 2 hours)
✅ auth       - healthy (up 2 hours)
✅ redis      - healthy (up 2 hours)
✅ mcp-fetch  - healthy (up 1 hour)
⚠️  mcp-filesystem - starting (10s)
```

## Script Execution

### Universal Script Runner

```bash
# Run any script from scripts/ directory
just run <script_name> [args...]

# Examples:
just run check_services_ready
just run analyze_oauth_logs --verbose
just run generate_coverage_report
just run manage_oauth_data list-registrations
```

Scripts available:
- `check_services_ready.py` - Service readiness check
- `check_env_tokens.py` - Token validation
- `generate_compose_includes.py` - Dynamic compose generation
- `generate_middlewares.py` - Traefik middleware generation
- `show_service_status.py` - Detailed status display

### Service Readiness

```bash
# Ensure services ready (called automatically)
just ensure-services-ready

# Used internally by test commands
# Fails fast if services not healthy
```

## Network Management

### Docker Network

```bash
# Create the sacred public network
just network-create

# Equivalent to:
docker network create public || true
```

The `public` network is used by all services for internal communication.

## Volume Management

### Create Volumes

```bash
# Create all required volumes
just volumes-create

# Creates:
# - traefik-certificates
# - redis-data
# - coverage-data
# - auth-keys
# - mcp-memory-data
```

Volumes are persistent and survive container restarts.

## Configuration Generation

### Compose Includes

```bash
# Generate docker-compose.includes.yml
just generate-includes

# Based on enabled services in .env:
# ENABLE_MCP_FETCH=true
# ENABLE_MCP_FILESYSTEM=false
# etc.
```

### Middleware Generation

```bash
# Generate Traefik middlewares
just generate-middlewares

# Creates middlewares from templates:
# - mcp-auth.yml (ForwardAuth)
# - secure-headers.yml
```

## Development Utilities

### Container Execution

```bash
# Execute command in any container
just exec <service> <command>

# Examples:
just exec redis redis-cli
just exec auth python manage.py shell
just exec traefik traefik version
```

### Quick Aliases

```bash
# Short aliases for common operations
just t    # alias for test
just b    # alias for build
just u    # alias for up
just d    # alias for down
just r    # alias for rebuild
```

## Claude Integration

### MCP Configuration

```bash
# Create MCP config for Claude Code
just create-mcp-config

# Generates ~/.config/claude/mcp-config.json
```

### Add to Claude

```bash
# Add MCP servers to Claude Code
just mcp-add

# Uses 'claude mcp add' command
# Requires GATEWAY_OAUTH_ACCESS_TOKEN
```

### Complete Setup

```bash
# Full Claude Code setup
just setup-claude-code

# Combines:
# 1. Token generation
# 2. Config creation
# 3. MCP registration
```

## Diagnostic Tools

### Test Diagnosis

```bash
# Diagnose test failures
just diagnose-tests

🔍 Diagnosing test failures...
- Checking service health...
- Analyzing recent logs...
- Identifying common issues...
- Suggesting fixes...
```

### Debug Coverage

```bash
# Debug coverage setup
just debug-coverage

=== Debugging coverage setup ===
- Coverage spy installed: ✅
- Environment variables: ✅
- Coverage collection: ✅
```

## Secret Management

### Generate All Secrets

```bash
# Generate all required secrets
just generate-all-secrets

# Generates:
# - JWT secret
# - RSA key pair
# - Redis password
```

### Individual Secret Generation

```bash
# JWT secret only
just generate-jwt-secret

# RSA keys only
just generate-rsa-keys

# Redis password only
just generate-redis-password
```

## PyPI Package Utilities

### Package Building

```bash
# Build specific package
just pypi-build mcp-oauth-dynamicclient

# Build all packages
just pypi-build all
```

### Package Testing

```bash
# Test specific package
just pypi-test mcp-streamablehttp-proxy

# Test all packages
just pypi-test all
```

## Initial Setup

### Project Setup

```bash
# Complete initial setup
just setup

# Performs:
# 1. Network creation
# 2. Volume creation
# 3. Pixi installation
# 4. Displays next steps
```

## Analysis Tools

### OAuth Analysis

```bash
# Analyze OAuth logs
just analyze-oauth-logs

# Creates timestamped report:
# reports/oauth-analysis-20240101-120000.md
```

## Best Practices

1. **Regular Health Checks**
   ```bash
   # Add to monitoring
   */5 * * * * just check-health
   ```

2. **Pre-deployment Checks**
   ```bash
   # Before deployment
   just check-health
   just check-ssl
   just status
   ```

3. **Script Organization**
   ```bash
   # Use the run command for scripts
   just run my_script --help
   ```

4. **Development Workflow**
   ```bash
   # Morning routine
   just check-health
   just status
   just logs -f
   ```

## Troubleshooting

### Health Check Failures

```bash
# Detailed service check
just check-services

# Manual endpoint test
curl https://auth.${BASE_DOMAIN}/health
```

### Script Execution Issues

```bash
# Check script exists
ls scripts/

# Run with Python directly
pixi run python scripts/check_services_ready.py
```

### Network Problems

```bash
# Verify network exists
docker network ls | grep public

# Inspect network
docker network inspect public
```
