# Command Reference

Complete reference for all `just` commands available in the MCP OAuth Gateway project. The project follows the **Sacred Commandments** with `just` as the divine task runner.

## Usage

All commands are executed using the `just` command runner:

```bash
# Show all available commands
just

# Execute a specific command
just <command> [arguments]

# Show this help
just --list
```

## Command Categories

### 🏗️ Project Setup Commands

#### `just setup`
**Purpose**: Initialize the MCP OAuth Gateway project with all dependencies and infrastructure.

```bash
just setup
```

**What it does**:
- Creates required Docker networks (`public`)
- Creates required Docker volumes (certificates, redis-data, etc.)
- Installs Python dependencies via pixi
- Prepares the environment for first run

**When to use**: First time setting up the project or after a clean checkout.

#### `just network-create`
**Purpose**: Create the sacred shared Docker network for service communication.

```bash
just network-create
```

**Details**:
- Creates the `public` Docker network if it doesn't exist
- Used by all services for inter-service communication
- Traefik uses this network for routing

#### `just volumes-create`
**Purpose**: Create all required Docker volumes for persistent data.

```bash
just volumes-create
```

**Creates volumes**:
- `traefik-certificates`: Let's Encrypt SSL certificates
- `redis-data`: Redis persistence
- `coverage-data`: Test coverage data
- `auth-keys`: JWT signing keys
- `mcp-memory-data`: Memory service persistence

---

### 🐳 Docker Service Management

#### `just up`
**Purpose**: Start all services in development mode.

```bash
just up
```

**What it does**:
- Ensures networks and volumes exist
- Starts all services via docker-compose
- Waits for services to become healthy
- Shows service readiness status

#### `just up-fresh`
**Purpose**: Start all services with fresh builds and recreation.

```bash
just up-fresh
```

**What it does**:
- Builds all services from scratch
- Forces recreation of containers (`--force-recreate`)
- Starts all services
- Waits for health checks to pass

**When to use**: After significant code changes or when containers need rebuilding.

#### `just down`
**Purpose**: Stop all services gracefully.

```bash
just down
```

**What it does**:
- Stops all running containers
- Removes containers but preserves volumes
- Preserves networks for next startup

#### `just build-all`
**Purpose**: Build all service images without starting them.

```bash
just build-all
```

**What it does**:
- Ensures infrastructure exists (networks, volumes)
- Builds all Docker images
- Does not start containers

#### `just rebuild-all`
**Purpose**: Completely rebuild all services from scratch.

```bash
just rebuild-all
```

**What it does**:
- Stops all services
- Rebuilds all images with `--no-cache`
- Starts all services
- Waits for health checks

**When to use**: When you need to ensure completely fresh builds.

#### `just rebuild <service>`
**Purpose**: Rebuild a specific service only.

```bash
just rebuild auth
just rebuild mcp-fetch
just rebuild traefik
```

**What it does**:
- Rebuilds the specified service with `--no-cache`
- Restarts only that service
- Other services continue running

**Examples**:
```bash
just rebuild auth          # Rebuild auth service
just rebuild mcp-fetch     # Rebuild MCP fetch service
just rebuild traefik       # Rebuild Traefik proxy
```

#### Service-Specific Rebuild Shortcuts

```bash
just rebuild-auth         # Shortcut for 'just rebuild auth'
just rebuild-mcp-fetch    # Shortcut for 'just rebuild mcp-fetch'
just rebuild-traefik      # Shortcut for 'just rebuild traefik'
```

---

### 🧪 Testing Commands

#### `just test`
**Purpose**: Run the standard test suite with automatic cleanup.

```bash
just test
```

**What it does**:
- Runs pytest with verbose output
- Tests against real Docker services (no mocking!)
- Automatically cleans up test registrations after completion
- Returns exit code 0 on success, non-zero on failure

#### `just test-all`
**Purpose**: Run comprehensive test suite including integration tests.

```bash
just test-all
```

**What it does**:
- Runs all tests with short traceback format
- Includes integration and end-to-end tests
- Automatic test cleanup
- More comprehensive than `just test`

#### `just test-file <file>`
**Purpose**: Run a specific test file.

```bash
just test-file tests/test_oauth_flow.py
just test-file tests/test_mcp_protocol.py
```

**What it does**:
- Runs only the specified test file
- Includes verbose output
- Automatic cleanup after test

#### `just test-verbose`
**Purpose**: Run tests with maximum verbosity and output.

```bash
just test-verbose
```

**What it does**:
- Runs tests with `-v -s` flags
- Shows all print statements and output
- Useful for debugging test failures

#### `just test-sidecar-coverage`
**Purpose**: Run tests with production-grade coverage measurement.

```bash
just test-sidecar-coverage
```

**What it does**:
- Starts services with coverage instrumentation
- Measures code coverage without modifying production containers
- Runs full test suite
- Generates coverage reports
- Uses sidecar pattern for non-invasive coverage

**Sacred principle**: This measures production containers without contamination!

#### Specialized Test Commands

```bash
just test-oauth-flow         # Test OAuth 2.1 flows specifically
just test-mcp-protocol       # Test MCP protocol compliance
just test-claude-integration # Test Claude.ai integration
just test-mcp-hostnames      # Test MCP service hostname resolution
```

#### Test Utilities

```bash
just ensure-services-ready   # Wait for all services to be healthy
just diagnose-tests         # Analyze test failures and find root causes
just test-cleanup           # Clean up test registrations manually
just test-cleanup-show      # Show what test data would be cleaned
```

---

### 📊 Coverage and Quality

#### `just debug-coverage`
**Purpose**: Debug coverage measurement setup in containers.

```bash
just debug-coverage
```

**What it does**:
- Starts services with coverage configuration
- Runs debug scripts inside auth container
- Shows coverage environment variables
- Helps troubleshoot coverage issues

#### `just lint`
**Purpose**: Run code quality checks and formatting.

```bash
just lint
```

**What it does**:
- Runs `ruff check` for linting
- Runs `ruff format` for code formatting
- Applies fixes automatically where possible

---

### 📚 Documentation Commands

#### `just docs-build`
**Purpose**: Build Jupyter Book documentation.

```bash
just docs-build
```

**What it does**:
- Builds complete HTML documentation using Jupyter Book
- Processes MyST Markdown files
- Generates navigation and search index
- Outputs to `docs/_build/html/`

**Output location**: `docs/_build/html/index.html`

---

### 🔐 Security and OAuth Management

#### JWT and Keys Management

```bash
just generate-jwt-secret     # Generate and save JWT secret to .env
just generate-rsa-keys       # Generate RSA keys for RS256 JWT signing
just generate-github-token   # Generate GitHub OAuth token (interactive)
```

#### Token Management

```bash
just refresh-tokens          # Refresh OAuth tokens before tests
just validate-tokens         # Validate all OAuth tokens
just check-token-expiry      # Check token expiration status
```

#### OAuth Client Registration Management

```bash
just oauth-list-registrations    # Show all OAuth client registrations
just oauth-delete-registration <client_id>  # Delete specific registration
just oauth-delete-all-registrations  # Delete ALL registrations (dangerous!)
```

#### OAuth Token Management

```bash
just oauth-list-tokens              # Show all active OAuth tokens
just oauth-delete-token <jti>       # Delete specific token by JTI
just oauth-delete-all-tokens        # Delete ALL tokens (dangerous!)
```

#### OAuth Statistics and Analysis

```bash
just oauth-stats            # Show OAuth usage statistics
just oauth-show-all         # Show complete OAuth data overview
```

#### Token Cleanup

```bash
just oauth-purge-expired-dry    # Show expired tokens (dry run)
just oauth-purge-expired        # Actually delete expired tokens
```

---

### 💾 Backup and Restore

#### OAuth Data Backup

```bash
just oauth-backup           # Backup all OAuth registrations and tokens
just oauth-backup-list      # List available backup files
just oauth-backup-view      # View latest backup contents
just oauth-backup-view-file <filename>  # View specific backup
```

#### OAuth Data Restore

```bash
just oauth-restore          # Restore from latest backup
just oauth-restore-file <filename>  # Restore from specific backup
just oauth-restore-clear    # Restore and clear existing data first
just oauth-restore-dry      # Show what would be restored (dry run)
```

---

### 🔧 MCP Client Integration

#### MCP Client Token Generation

```bash
just mcp-client-token       # Generate MCP client token interactively
just mcp-client-token-complete <auth_code>  # Complete OAuth flow with code
```

#### Claude Code Integration

```bash
just create-mcp-config      # Create MCP configuration for Claude Code
just mcp-add               # Add MCP servers to Claude Code
just setup-claude-code     # Complete Claude Code setup
```

**Example workflow**:
```bash
# 1. Generate OAuth tokens
just generate-github-token

# 2. Create MCP configuration
just create-mcp-config

# 3. Add servers to Claude Code
just mcp-add

# Or do all at once:
just setup-claude-code
```

---

### 📊 Monitoring and Health Checks

#### Service Health

```bash
just check-health           # Comprehensive service health check
just health-quick          # Quick service health check
just ensure-services-ready  # Wait for services to be ready
```

#### SSL Certificate Management

```bash
just check-ssl             # Check SSL certificate status
```

**What it shows**:
- SSL certificate status for each service
- Certificate validation
- ACME certificate storage contents

#### Log Management

```bash
just logs                  # View last 200 log entries from all services
just logs-follow           # Follow logs in real-time
just logs-purge            # Purge all container logs (restart services)
```

---

### 🔍 Analysis and Debugging

#### OAuth Analysis

```bash
just analyze-oauth-logs     # Analyze OAuth logs and generate report
```

**Output**: Creates timestamped report in `reports/` directory.

#### Service Debugging

```bash
just exec-auth <command>    # Execute command in auth container
```

**Examples**:
```bash
just exec-auth ps aux                    # Show processes in auth container
just exec-auth cat /app/logs/auth.log   # View auth service logs
just exec-auth env                      # Show environment variables
```

#### Hostname Testing

```bash
just check-mcp-hostnames    # Quick hostname connectivity check
```

---

### ⚠️ Dangerous Commands

These commands can delete data and should be used with caution:

```bash
# Delete ALL OAuth registrations
just oauth-delete-all-registrations

# Delete ALL OAuth tokens, states, and codes
just oauth-delete-all-tokens

# Purge all container logs (restarts services)
just logs-purge
```

---

## Command Patterns and Best Practices

### Sacred Development Workflow

```bash
# 1. Initial setup
just setup

# 2. Start services
just up-fresh

# 3. Run tests
just test

# 4. Make changes, then rebuild specific service
just rebuild auth

# 5. Test specific functionality
just test-oauth-flow

# 6. Check health
just check-health

# 7. Build documentation
just docs-build
```

### Testing Workflow

```bash
# Standard test run
just test

# Debug test failures
just test-verbose
just diagnose-tests

# Test specific areas
just test-oauth-flow
just test-mcp-protocol

# Clean up after tests
just test-cleanup

# Coverage analysis
just test-sidecar-coverage
```

### OAuth Management Workflow

```bash
# View current state
just oauth-show-all

# Backup before changes
just oauth-backup

# Make changes, then check
just oauth-stats

# Clean up test data
just test-cleanup

# Restore if needed
just oauth-restore
```

### Production Maintenance

```bash
# Health monitoring
just check-health
just check-ssl

# Log analysis
just logs
just analyze-oauth-logs

# Token maintenance
just oauth-purge-expired
just validate-tokens

# Backup management
just oauth-backup
just oauth-backup-list
```

## Environment Variables

Many commands use environment variables from `.env`:

- `BASE_DOMAIN`: Your domain for services (e.g., `example.com`)
- `GATEWAY_JWT_SECRET`: JWT signing secret
- `GATEWAY_OAUTH_ACCESS_TOKEN`: OAuth access token
- `GITHUB_CLIENT_ID/SECRET`: GitHub OAuth application credentials

## Error Handling

All commands include error handling and informative output:

- ✅ Success indicators for completed operations
- ❌ Error messages with troubleshooting hints
- ⚠️ Warnings for potentially dangerous operations
- 🔍 Diagnostic information for debugging

## Integration with Sacred Commandments

These commands follow the **Ten Sacred Commandments**:

1. **No Mocks**: All tests use real services
2. **Holy Trinity**: Uses `just`, `pixi`, and `docker-compose`
3. **Real Systems**: Tests against actual Docker containers
4. **Configuration via .env**: All config through environment
5. **Centralized Logging**: Logs flow to `./logs/`

Run `just --list` to see all available commands with brief descriptions.