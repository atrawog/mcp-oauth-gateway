set dotenv-load := true          # FIRST LINE - ALWAYS! Load .env automatically!
set dotenv-required := true      # Fail if .env is missing — no silent misconfigurations!
set positional-arguments := true # Enable blessed argument passing!
set allow-duplicate-recipes      # Allow recipe overloading with different arity!
set export := true               # Export all variables as environment variables!
set quiet                        # Silence the incantations! Show only results!

# Enable Compose Bake for better performance
export COMPOSE_BAKE := "true"

# The Sacred justfile for MCP OAuth Gateway
# Following the divine commandments of CLAUDE.md

# Show all available commands (default)
@default:
    just --list

# Universal commands mandated by the commandments

# Ensure all services are ready before tests
ensure-services-ready:
    uv run python scripts/check_services_ready.py || (echo "❌ Services not ready! See above for details." && exit 1)

# Universal test runner with flexible arguments (replaces test, test-all, test-file, test-verbose)
test *args:
    uv run pytest {{args}}
    echo "\n🧹 Cleaning up test registrations..."

# Alias for backwards compatibility
alias t := test

# Run tests in parallel using all CPU cores
test-parallel *args:
    uv run pytest -n auto {{args}}

# Run tests in parallel with specific worker count
test-n count *args:
    uv run pytest -n {{count}} {{args}}

# Run tests in parallel with optimal distribution strategy
test-fast *args:
    uv run pytest -n auto --dist worksteal {{args}}

# Run tests by module (keeps tests in same file together)
test-by-module *args:
    uv run pytest -n auto --dist loadfile {{args}}

# Run tests by class (keeps tests in same class together)
test-by-class *args:
    uv run pytest -n auto --dist loadscope {{args}}

# Run only serial tests (those marked with @pytest.mark.serial)
test-serial:
    uv run pytest -m serial

# Run parallel tests excluding serial ones
test-parallel-safe:
    uv run pytest -n auto -m "not serial" --dist worksteal

# Run tests with sidecar coverage pattern
test-sidecar-coverage:
    docker compose down --remove-orphans
    docker compose -f docker-compose.yml -f docker-compose.coverage.yml up -d
    echo "Waiting for services to be ready..."
    uv run python scripts/check_services_ready.py || (echo "❌ Services not ready!" && exit 1)
    uv run pytest tests/ -v
    echo "Triggering graceful shutdown to collect coverage data..."
    docker compose -f docker-compose.yml -f docker-compose.coverage.yml stop auth
    echo "Waiting for coverage harvester to complete..."
    sleep 10
    echo ""
    echo "📊 Coverage Report from Container:"
    echo "=================================="
    docker logs coverage-harvester 2>&1 | grep -A50 "Name" | grep -B50 "TOTAL" || echo "Coverage report not found in logs"
    echo ""
    echo "Copying coverage data locally..."
    docker cp coverage-harvester:/coverage-data/.coverage . 2>/dev/null || echo "No coverage file to copy"
    docker compose -f docker-compose.includes.yml -f docker-compose.coverage.yml down
    echo "Attempting local report generation..."
    uv run python scripts/generate_coverage_report.py || echo "Local report generation had issues"

# Debug coverage setup
debug-coverage: ensure-services-ready
    docker compose down --remove-orphans
    docker compose -f docker-compose.yml -f docker-compose.coverage.yml up -d
    echo "Waiting for services..."
    uv run python scripts/check_services_ready.py || (echo "❌ Services not ready!" && exit 1)
    echo "=== Debugging coverage setup in auth container ==="
    docker compose -f docker-compose.yml -f docker-compose.coverage.yml exec auth python /scripts/debug_coverage.py || echo "Debug script failed"
    echo "=== Auth container environment ==="
    docker compose -f docker-compose.yml -f docker-compose.coverage.yml exec auth env | grep -E "PYTHON|COVERAGE" || echo "No coverage env vars"
    docker compose -f docker-compose.includes.yml -f docker-compose.coverage.yml down

# Build documentation with Jupyter Book
docs-build:
    uv run jupyter-book build docs/

# Lint and format code - The Divine Code Quality Commandments!
# This runs ALL quality checks: linting, formatting, pre-commit hooks, and deprecation hunting
lint:
    @echo "🔥 Running Divine Code Quality Checks ⚡"
    @echo "========================================"
    @echo ""
    @echo "1️⃣ First Pass: Checking for ALL issues (including those that need manual fixes)..."
    -uv run ruff check . --exit-non-zero-on-fix
    @echo ""
    @echo "2️⃣ Second Pass: Applying automatic fixes..."
    uv run ruff check . --fix
    @echo ""
    @echo "3️⃣ Third Pass: Checking for remaining issues that need MANUAL fixes..."
    uv run ruff check . --no-fix || (echo "" && echo "⚠️  ⚠️  ⚠️  ATTENTION REQUIRED ⚠️  ⚠️  ⚠️" && echo "🔴 There are linting errors that need MANUAL fixes!" && echo "🔴 Please fix the errors shown above before proceeding." && echo "" && exit 1)
    @echo ""
    @echo "4️⃣ Running code formatter..."
    uv run ruff format .
    @echo ""
    @echo "5️⃣ Running ALL other pre-commit hooks..."
    uv run pre-commit run --all-files
    @echo ""
    @echo "6️⃣ Checking STAGED files (as git commit would)..."
    @if git diff --cached --quiet; then \
        echo "✅ No staged files to check"; \
    else \
        echo "🔍 Checking staged files for commit readiness..."; \
        uv run pre-commit run || (echo "" && echo "⚠️  STAGED FILES HAVE ISSUES! ⚠️" && echo "🔴 Fix the issues above and re-stage the files!" && echo "" && exit 1); \
    fi
    @echo ""
    @echo "🏆 ALL QUALITY CHECKS COMPLETED! Divine compliance achieved! ⚡"

# Quick lint - just run ruff check (for fast feedback)
lint-quick:
    uv run ruff check . --no-fix

# Show only issues that need MANUAL fixes (cannot be auto-fixed)
lint-manual:
    @echo "🔍 Checking for issues that need MANUAL fixes..."
    @echo "=================================================="
    @uv run ruff check . --fix --diff > /tmp/ruff-fixes.diff 2>&1 || true
    @if uv run ruff check . --no-fix 2>&1 | grep -E "^[^:]+:[0-9]+:[0-9]+:"; then \
        echo ""; \
        echo "⚠️  The above errors need MANUAL fixes!"; \
        echo "💡 Tip: Read the error messages carefully and fix them in your editor."; \
    else \
        echo "✅ No manual fixes needed!"; \
    fi

# Fix linting issues automatically (only auto-fixable ones)
lint-fix:
    @echo "🔧 Applying automatic fixes..."
    uv run ruff check . --fix
    uv run ruff format .
    @echo "✅ Auto-fixes applied! Run 'just lint' to check for remaining issues."

# Format code with divine standards
format:
    uv run pre-commit run ruff-format --all-files

# Show help for linting commands
lint-help:
    @echo "📚 Divine Linting Commands Guide ⚡"
    @echo "================================"
    @echo ""
    @echo "🔥 just lint         - Full divine quality check with clear error reporting"
    @echo "                     Shows ALL issues including those needing manual fixes"
    @echo "                     Auto-fixes what it can, then shows remaining issues"
    @echo "                     ⚠️  EXITS WITH ERROR if manual fixes are needed!"
    @echo ""
    @echo "🏃 just lint-quick   - Fast check without auto-fixing (read-only)"
    @echo ""
    @echo "🔍 just lint-manual  - Show ONLY issues that need manual fixes"
    @echo ""
    @echo "🔧 just lint-fix     - Apply all automatic fixes"
    @echo ""
    @echo "🎨 just format       - Format code with divine standards"
    @echo ""
    @echo "💡 Pro tip: Always use 'just lint' before committing!"

# Check code formatting without making changes
format-check:
    uv run ruff format . --check

# Hunt for Pydantic deprecations
lint-pydantic:
    uv run python scripts/lint_pydantic_compliance.py

# Complete linting with deprecation hunting
lint-all:
    uv run pre-commit run ruff --all-files
    uv run python scripts/lint_pydantic_compliance.py

# Comprehensive linting: fix, format, and hunt deprecations
lint-comprehensive:
    uv run pre-commit run ruff --all-files
    uv run pre-commit run ruff-format --all-files
    uv run python scripts/lint_pydantic_compliance.py

# Security scan with bandit
security-scan:
    @echo "🔥 Running Security Scan with Bandit ⚡"
    uv run python -m bandit -r . -x tests/ -f txt

# Security scan with JSON output
security-scan-json:
    uv run python -m bandit -r . -x tests/ -f json -o bandit-report.json


# Docker operations

# Create the sacred shared network
network-create:
    docker network create public || true

# Create required volumes
volumes-create:
    docker volume create redis-data || true
    docker volume create coverage-data || true
    docker volume create auth-keys || true
    docker volume create mcp-memory-data || true

# Generate docker-compose includes based on enabled services
generate-includes:
    uv run python scripts/generate_compose_includes.py

# Generate SWAG middlewares from template with environment variables
generate-middlewares:
    uv run python scripts/generate_middlewares.py

# Flexible build command with optional services
build *services: network-create volumes-create generate-includes generate-middlewares
    #!/usr/bin/env bash
    if [ -z "{{services}}" ]; then
        echo "Building all services..."
        docker compose -f docker-compose.includes.yml build
    else
        echo "Building services: {{services}}"
        docker compose -f docker-compose.includes.yml build {{services}}
    fi
    echo "✅ Build completed successfully"

# Flexible up command with options
up *args: network-create volumes-create generate-includes generate-middlewares
    docker compose -f docker-compose.includes.yml up -d {{args}}
    echo "Waiting for services to be healthy..."
    uv run python scripts/check_services_ready.py || echo "⚠️  Some services may not be ready yet"

# Start all services with fresh build
up-fresh: network-create volumes-create generate-includes generate-middlewares
    just build
    docker compose -f docker-compose.includes.yml up -d --force-recreate
    echo "Waiting for services to be healthy..."
    uv run python scripts/check_services_ready.py || echo "⚠️  Some services may not be ready yet"

# Stop all services (with optional remove volumes/orphans)
down *args:
    docker compose -f docker-compose.includes.yml down {{args}}

# Remove orphan containers
remove-orphans:
    docker compose -f docker-compose.includes.yml down --remove-orphans

# Flexible rebuild command with optional services and no-cache by default
rebuild *services: network-create volumes-create generate-includes generate-middlewares
    #!/usr/bin/env bash
    if [ -z "{{services}}" ]; then
        echo "Rebuilding all services from scratch..."
        echo "Stopping all services..."
        docker compose -f docker-compose.includes.yml down
        echo "Building all services with no cache..."
        docker compose -f docker-compose.includes.yml build --no-cache
        echo "Starting all services..."
        docker compose -f docker-compose.includes.yml up -d
    else
        echo "Rebuilding: {{services}}"
        echo "Stopping services: {{services}}"
        docker compose -f docker-compose.includes.yml stop {{services}}
        docker compose -f docker-compose.includes.yml rm -f {{services}}
        echo "Building services with no cache: {{services}}"
        docker compose -f docker-compose.includes.yml build --no-cache {{services}}
        echo "Starting services: {{services}}"
        docker compose -f docker-compose.includes.yml up -d {{services}}
    fi
    echo "✅ Rebuild completed"
    uv run python scripts/check_services_ready.py || echo "⚠️  Some services may not be ready yet"

# Alias for common operations
alias b := build
alias u := up
alias d := down
alias r := rebuild

# Flexible logs command - can specify service and options
logs *args:
    docker compose -f docker-compose.includes.yml logs {{args}}

# Follow logs (alias for convenience)
logs-follow *args:
    docker compose -f docker-compose.includes.yml logs -f {{args}}

# Purge all container logs
logs-purge:
    echo "🧹 Purging all container logs..."
    docker compose -f docker-compose.includes.yml down
    docker compose -f docker-compose.includes.yml up -d
    echo "✅ All container logs purged (services restarted)"

# View file-based logs
logs-files service="all":
    #!/usr/bin/env bash
    if [ "{{service}}" = "all" ]; then
        echo "📜 Viewing all service logs from ./logs directory..."
        tail -f logs/*/*.log 2>/dev/null || echo "No log files found yet. Services may still be starting."
    else
        echo "📜 Viewing logs for {{service}}..."
        tail -f logs/{{service}}/*.log 2>/dev/null || echo "No log files found for {{service}}"
    fi

# Setup log rotation (requires sudo)
logs-rotation-setup:
    echo "🔄 Setting up log rotation..."
    echo "⚠️  This requires sudo access to install system-wide logrotate config"
    sudo bash scripts/setup_log_rotation.sh

# Manually rotate logs
logs-rotate:
    echo "🔄 Manually rotating logs..."
    sudo logrotate -f /etc/logrotate.d/mcp-oauth-gateway || echo "⚠️  Log rotation not set up. Run: just logs-rotation-setup"

# Show log statistics
logs-stats:
    #!/usr/bin/env bash
    echo "📊 Log Statistics"
    echo "================"
    echo ""
    for dir in logs/*/; do
        if [ -d "$dir" ]; then
            service=$(basename "$dir")
            size=$(du -sh "$dir" 2>/dev/null | cut -f1)
            count=$(find "$dir" -name "*.log" -type f 2>/dev/null | wc -l)
            echo "📁 $service: $size ($count log files)"
        fi
    done
    echo ""
    echo "Total size: $(du -sh logs/ 2>/dev/null | cut -f1)"

# Clean logs - by default removes all logs, or keep last X days if specified
logs-clean days="0":
    #!/usr/bin/env bash
    if [ "{{days}}" = "0" ]; then
        # Check if running in CI or with FORCE_CLEAN env var
        if [ -z "$CI" ] && [ -z "$FORCE_CLEAN" ]; then
            echo "⚠️  WARNING: This will delete ALL log files!"
            echo -n "Are you sure? (y/N): "
            read -r response
            if [ "$response" != "y" ] && [ "$response" != "Y" ]; then
                echo "❌ Cancelled"
                exit 0
            fi
        fi
        echo "🧹 Cleaning ALL logs..."
        find logs -name "*.log" -delete 2>/dev/null || true
        find logs -name "*.log.gz" -delete 2>/dev/null || true
        find logs -name "*.log.*" -delete 2>/dev/null || true
        echo "✅ Removed all log files"
    else
        echo "🧹 Cleaning logs older than {{days}} days..."
        find logs -name "*.log" -mtime +{{days}} -delete 2>/dev/null || true
        find logs -name "*.log.gz" -mtime +{{days}} -delete 2>/dev/null || true
        find logs -name "*.log.*" -mtime +{{days}} -delete 2>/dev/null || true
        echo "✅ Removed logs older than {{days}} days"
    fi

    # Show remaining logs
    remaining=$(find logs -name "*.log*" 2>/dev/null | wc -l)
    if [ "$remaining" -gt 0 ]; then
        echo "📊 Remaining log files: $remaining"
        echo "📏 Total size: $(du -sh logs/ 2>/dev/null | cut -f1)"
    else
        echo "📭 No log files remaining"
    fi

# Force clean all logs without confirmation
logs-clean-force:
    FORCE_CLEAN=1 just logs-clean

# Project-specific commands

# Generate JWT secret and save to .env
generate-jwt-secret:
    #!/usr/bin/env bash
    NEW_JWT_SECRET=$(uv run python -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "🔐 Generated new JWT secret: ${NEW_JWT_SECRET}"

    # Check if .env exists
    if [ ! -f .env ]; then
        echo "❌ .env file not found! Creating one..."
        printf "OAUTH_JWT_SECRET=%s\nGATEWAY_JWT_SECRET=%s\n" "${NEW_JWT_SECRET}" "${NEW_JWT_SECRET}" > .env
        echo "✅ Created .env with OAUTH_JWT_SECRET and GATEWAY_JWT_SECRET"
    else
        if grep -q "^OAUTH_JWT_SECRET=" .env; then
            sed -i.bak "s/^OAUTH_JWT_SECRET=.*/OAUTH_JWT_SECRET=${NEW_JWT_SECRET}/" .env
        else
            echo "OAUTH_JWT_SECRET=${NEW_JWT_SECRET}" >> .env
        fi

        if grep -q "^GATEWAY_JWT_SECRET=" .env; then
            sed -i.bak "s/^GATEWAY_JWT_SECRET=.*/GATEWAY_JWT_SECRET=${NEW_JWT_SECRET}/" .env
            echo "✅ Updated JWT secret aliases in .env file"
        else
            echo "GATEWAY_JWT_SECRET=${NEW_JWT_SECRET}" >> .env
            echo "✅ Added JWT secret aliases to .env file"
        fi
    fi

    echo "🔥 SACRED JWT SECRET HAS BEEN BLESSED AND WRITTEN TO .ENV!"

# Generate RSA keys for RS256 JWT signing and save to .env
generate-rsa-keys:
    echo "🔑 Generating RSA keys for RS256 JWT signing..."
    just run generate_rsa_keys_to_env

# Generate secure Redis password and save to .env
generate-redis-password:
    #!/usr/bin/env bash
    NEW_REDIS_PASSWORD=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "🔐 Generated new Redis password: ${NEW_REDIS_PASSWORD}"

    # Check if .env exists
    if [ ! -f .env ]; then
        echo "📄 Creating .env file..."
        cp .env.example .env
    fi

    # Update or add REDIS_PASSWORD in .env
    if grep -q "^REDIS_PASSWORD=" .env; then
        echo "🔄 Updating REDIS_PASSWORD in .env..."
        sed -i.bak "s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=${NEW_REDIS_PASSWORD}|" .env
    else
        echo "➕ Adding REDIS_PASSWORD to .env..."
        echo "REDIS_PASSWORD=${NEW_REDIS_PASSWORD}" >> .env
    fi

    echo "✅ Redis password saved to .env successfully!"

# Generate all required secrets (JWT, RSA keys, Redis password)
generate-all-secrets:
    echo "🔐 Generating all required secrets..."
    just generate-jwt-secret
    just generate-rsa-keys
    just generate-redis-password
    echo "✅ All required secrets generated successfully!"

# Generate GitHub OAuth token
generate-github-token:
    just run generate_oauth_token

# Refresh OAuth tokens before tests
refresh-tokens:
    echo "🔄 Refreshing OAuth tokens..."
    just run refresh_tokens

# Validate all OAuth tokens
validate-tokens:
    echo "🔍 Validating OAuth tokens..."
    just run validate_tokens

# Check token expiration and refresh if needed
check-token-expiry:
    echo "⏰ Checking token expiration..."
    just run check_token_expiry

# Diagnose test failures and find root causes
diagnose-tests:
    echo "🔍 Diagnosing test failures..."
    just run diagnose_test_failures

# Create MCP configuration for Claude Code with bearer token
create-mcp-config:
    just run create_mcp_config

# Add MCP servers to Claude Code using claude mcp add
@mcp-add:
    echo "Adding MCP servers to Claude Code..."
    if [ -z "${GATEWAY_OAUTH_ACCESS_TOKEN:-}" ]; then \
        echo "❌ GATEWAY_OAUTH_ACCESS_TOKEN not found in .env file"; \
        echo "Please run 'just generate-github-token' first"; \
        exit 1; \
    fi
    claude mcp add mcp-fetch https://mcp-fetch.${BASE_DOMAIN}/mcp \
        --transport http \
        --header "Authorization: Bearer ${GATEWAY_OAUTH_ACCESS_TOKEN}" \
        || echo "Failed to add mcp-fetch server"
    echo "✅ MCP servers added to Claude Code!"

# Complete setup: generate token and create config
setup-claude-code: generate-github-token create-mcp-config
    echo "✅ Claude Code setup complete!"
    echo "📝 MCP config saved to ~/.config/claude/mcp-config.json"

# Flexible exec command for any service
exec service *args:
    docker compose -f docker-compose.includes.yml exec -T {{service}} {{args}}

# Universal script runner
run script *args:
    uv run python scripts/{{script}}.py {{args}}

# These specific test commands are kept for documentation/convenience
# But you should use: just test tests/test_oauth_flow.py -v -s
test-oauth-flow: ensure-services-ready
    just test tests/test_oauth_flow.py -v -s

test-mcp-protocol: ensure-services-ready
    just test tests/test_mcp_protocol.py -v -s

test-claude-integration: ensure-services-ready
    just test tests/test_claude_integration.py -v -s

# MCP AI hostnames tests
test-mcp-hostnames: ensure-services-ready
    just test tests/test_mcp_ai_hostnames.py -v -s


# Quick hostname connectivity check
check-mcp-hostnames:
    uv run python scripts/test_mcp_hostnames.py

# Service-specific rebuilds are now: just rebuild auth, just rebuild mcp-fetch, etc.

# Analysis commands
analyze-oauth-logs:
    mkdir -p reports
    uv run python scripts/analyze_oauth_logs.py > reports/oauth-analysis-$(date +%Y%m%d-%H%M%S).md

# Health check commands - checks both environment tokens and services
check-health:
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "🏥 MCP OAuth Gateway Health Check"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo ""
    @echo "Step 1/3: Checking environment tokens..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    uv run python scripts/check_env_tokens.py
    @echo ""
    @echo "Step 2/3: Checking Docker services..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    uv run python scripts/check_services_ready.py
    @echo ""
    @echo "Step 3/3: Checking service endpoints..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @just health-quick
    @echo ""
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "✅ Health check complete!"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check only environment tokens
check-tokens:
    uv run python scripts/check_env_tokens.py

# Check only services
check-services:
    uv run python scripts/check_services_ready.py --check-only

# Quick health check (simple version)
@health-quick:
    #!/usr/bin/env bash
    set -uo pipefail
    failed=0
    echo "Checking service health..."
    if ! curl -fsS https://mcp-auth.${BASE_DOMAIN}/.well-known/oauth-authorization-server >/dev/null; then
        echo "Auth service not healthy"
        failed=1
    fi
    if ! curl -fsS https://mcp-fetch.${BASE_DOMAIN}/.well-known/oauth-authorization-server >/dev/null; then
        echo "MCP-fetch OAuth discovery not accessible"
        failed=1
    fi
    exit "$failed"

# Show service status with health information
status:
    @uv run python scripts/show_service_status.py

# Check SSL certificates
check-ssl:
	#!/usr/bin/env bash
	set -euo pipefail

	echo "Checking SSL certificates..."
	echo ""
	echo "=== Auth Service ==="
	curl -I https://mcp-auth.${BASE_DOMAIN}/.well-known/oauth-authorization-server 2>&1 | grep -E "HTTP|SSL|certificate" || echo "Auth SSL check failed"
	echo ""
	echo "=== MCP Services (checking enabled services only) ==="
	echo ""

	# Check each MCP service if enabled
	if [ "${MCP_EVERYTHING_ENABLED:-false}" = "true" ]; then
		echo "MCP Everything (${MCP_EVERYTHING_URLS:-}):"
		for url in $(echo ${MCP_EVERYTHING_URLS:-} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_FETCH_ENABLED:-false}" = "true" ]; then
		echo "MCP Fetch (${MCP_FETCH_URLS:-}):"
		for url in $(echo ${MCP_FETCH_URLS:-} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_FETCHS_ENABLED:-false}" = "true" ]; then
		echo "MCP Fetchs (${MCP_FETCHS_URLS:-}):"
		for url in $(echo ${MCP_FETCHS_URLS:-} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_FILESYSTEM_ENABLED:-false}" = "true" ]; then
		echo "MCP Filesystem (${MCP_FILESYSTEM_URLS:-}):"
		for url in $(echo ${MCP_FILESYSTEM_URLS:-} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_MEMORY_ENABLED:-false}" = "true" ]; then
		echo "MCP Memory (${MCP_MEMORY_URLS:-}):"
		for url in $(echo ${MCP_MEMORY_URLS:-} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_PLAYWRIGHT_ENABLED:-false}" = "true" ]; then
		echo "MCP Playwright (${MCP_PLAYWRIGHT_URLS:-}):"
		for url in $(echo ${MCP_PLAYWRIGHT_URLS:-} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_SEQUENTIALTHINKING_ENABLED:-false}" = "true" ]; then
		echo "MCP Sequential Thinking (${MCP_SEQUENTIALTHINKING_URLS:-}):"
		for url in $(echo ${MCP_SEQUENTIALTHINKING_URLS:-} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_TIME_ENABLED:-false}" = "true" ]; then
		echo "MCP Time (${MCP_TIME_URLS:-}):"
		for url in $(echo ${MCP_TIME_URLS:-} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_TMUX_ENABLED:-false}" = "true" ]; then
		echo "MCP Tmux (${MCP_TMUX_URLS:-}):"
		for url in $(echo ${MCP_TMUX_URLS:-} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	# MCP Echo services (special handling as they're not in the standard pattern)
	if [ "${MCP_ECHO_STATEFUL_ENABLED:-false}" = "true" ]; then
		echo "MCP Echo Stateful:"
		curl -I https://echo-stateful.${BASE_DOMAIN}/mcp 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: echo-stateful service"
		echo ""
	fi

	if [ "${MCP_ECHO_STATELESS_ENABLED:-false}" = "true" ]; then
		echo "MCP Echo Stateless:"
		curl -I https://echo-stateless.${BASE_DOMAIN}/mcp 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: echo-stateless service"
		echo ""
	fi

	echo ""
	echo "=== Certificates in ACME storage ==="
	docker exec swag cat /config/etc/letsencrypt/live/${SWAG_URL:-$BASE_DOMAIN}/cert.pem 2>/dev/null || echo "No certificates found or SWAG not running"

# Generate MCP client token using mcp-streamablehttp-client
mcp-client-token:
    echo "🔐 Generating MCP client token using mcp-streamablehttp-client..."
    uv pip install -e mcp-streamablehttp-client 2>/dev/null || true
    export MCP_SERVER_URL="https://mcp-auth.${BASE_DOMAIN}" && \
    uv run python -m mcp_streamablehttp_client.cli --token --server-url "$MCP_SERVER_URL"

# Complete MCP client token flow with auth code
mcp-client-token-complete auth_code:
    echo "🔐 Completing MCP client token flow with authorization code..."
    export MCP_SERVER_URL="https://mcp-auth.${BASE_DOMAIN}" && \
    export MCP_AUTH_CODE="{{ auth_code }}" && \
    uv run python scripts/complete_mcp_oauth.py

# Inject existing MCP client OAuth credentials into Codex's file-backed store
codex-inject-mcp-credentials server_name:
    echo "🔐 Injecting MCP client OAuth credentials into Codex for {{ server_name }}..."
    uv run python @oauth-helpers/scripts/inject_codex_mcp_credentials.py "{{ server_name }}"

# Run the callback relay server for headless Codex OAuth flows
callback-relay:
    echo "🔁 Starting callback relay server..."
    uv run python @oauth-helpers/scripts/callback_relay_server.py

# Onboard the current machine into the callback relay using loopback target
relay-onboard-current-machine machine_id:
    uv run python @oauth-helpers/scripts/relay_onboard_machine.py current "{{ machine_id }}"

# Onboard a remote machine into the callback relay over SSH
relay-onboard-ssh-machine host machine_id="":
    if [ -n "{{ machine_id }}" ]; then \
        uv run python @oauth-helpers/scripts/relay_onboard_machine.py ssh "{{ host }}" --machine-id "{{ machine_id }}"; \
    else \
        uv run python @oauth-helpers/scripts/relay_onboard_machine.py ssh "{{ host }}"; \
    fi


# OAuth Management Commands - Using flexible script runner

# Show all OAuth client registrations
oauth-list-registrations:
    echo "📋 Listing all OAuth client registrations..."
    just run manage_oauth_data list-registrations

# Show all active OAuth tokens
oauth-list-tokens:
    echo "🔑 Listing all active OAuth tokens..."
    just run manage_oauth_data list-tokens

# Delete a specific client registration
oauth-delete-registration client_id:
    echo "🗑️  Deleting client registration: {{client_id}}"
    just run manage_oauth_data delete-registration {{client_id}}

# Delete a client registration and ALL associated tokens
oauth-delete-client-complete client_id:
    echo "🗑️  Deleting client registration and ALL associated data: {{client_id}}"
    just run manage_oauth_data delete-registration {{client_id}}

# Delete a specific token by JTI
oauth-delete-token jti:
    echo "🗑️  Deleting token: {{jti}}"
    just run manage_oauth_data delete-token {{jti}}

# Delete all test client registrations (safer than delete-all)
oauth-delete-test-registrations:
    echo "🧪 Deleting all test client registrations..."
    just run manage_oauth_data delete-test-registrations

# Delete ALL client registrations (dangerous!)
oauth-delete-all-registrations:
    echo "⚠️  WARNING: This will delete ALL client registrations!"
    just run manage_oauth_data delete-all-registrations

# Delete ALL OAuth data - tokens, states, codes (dangerous!)
oauth-delete-all-tokens:
    echo "⚠️  WARNING: This will delete ALL OAuth data (tokens, states, codes)!"
    just run manage_oauth_data delete-all-tokens

# Show OAuth statistics
oauth-stats:
    echo "📊 OAuth Statistics:"
    just run manage_oauth_data stats

# Show all OAuth data (registrations + tokens + stats)
oauth-show-all: oauth-stats oauth-list-registrations oauth-list-tokens
    echo "✅ Complete OAuth data displayed"

# Purge expired tokens (dry run - shows what would be deleted)
oauth-purge-expired-dry:
    echo "🔍 Checking for expired tokens (DRY RUN)..."
    just run purge_expired_tokens --dry-run

# Purge expired tokens (actually delete them)
oauth-purge-expired:
    echo "🧹 Purging expired tokens..."
    just run purge_expired_tokens

# Test cleanup commands - Sacred pattern: "TEST testname"
# Show all test registrations (dry run)
test-cleanup-show:
    echo "🔍 Showing test registrations (client_name starting with 'TEST ')..."
    just run cleanup_test_data --show

# Cleanup test data
test-cleanup:
    echo "🧹 Cleaning up test registrations..."
    just run cleanup_test_data --execute

# Setup commands
setup: network-create volumes-create
    echo "Setting up MCP OAuth Gateway..."
    uv sync
    echo "Setup complete! Run 'just up' to start services."

# OAuth Backup and Restore Commands

# Backup all OAuth registrations and tokens
oauth-backup:
    echo "🔐 Backing up OAuth registrations and tokens..."
    just run backup_oauth_data

# List available OAuth backups
oauth-backup-list:
    echo "📋 Available OAuth backups:"
    just run restore_oauth_data --list

# Restore OAuth data from latest backup
oauth-restore:
    echo "🔄 Restoring OAuth data from latest backup..."
    just run restore_oauth_data --latest

# Restore OAuth data from specific backup file
oauth-restore-file filename:
    echo "🔄 Restoring OAuth data from {{filename}}..."
    just run restore_oauth_data --file {{filename}}

# Restore OAuth data from latest backup (clear existing data first)
oauth-restore-clear:
    echo "🔄 Restoring OAuth data from latest backup (clearing existing data)..."
    just run restore_oauth_data --latest --clear

# Dry run - show what would be restored without making changes
oauth-restore-dry:
    echo "🔍 Dry run - showing what would be restored..."
    just run restore_oauth_data --latest --dry-run

# View contents of latest backup
oauth-backup-view:
    echo "📋 Viewing latest backup contents..."
    ls -t backups/oauth-backup-*.json 2>/dev/null | head -1 | xargs uv run python scripts/view_oauth_backup.py || echo "No backups found"

# View contents of specific backup file
oauth-backup-view-file filename:
    echo "📋 Viewing backup: {{filename}}..."
    just run view_oauth_backup backups/{{filename}}

# PyPI Package Management - The Sacred Publishing Commandments!

# Initialize git submodules
submodule-init:
    echo "🔄 Initializing git submodules..."
    git submodule update --init --recursive
    echo "✅ Submodules initialized"

# Build a specific Python package (or all packages)
pypi-build package="all":
    #!/usr/bin/env bash
    # Ensure submodules are initialized
    submodule_missing=false
    for pkg in mcp-streamablehttp-client mcp-oauth-dynamicclient mcp-streamablehttp-proxy; do
        if [ ! -f "$pkg/pyproject.toml" ]; then
            submodule_missing=true
            break
        fi
    done
    
    if [ "$submodule_missing" = true ]; then
        echo "🔄 Initializing submodules..."
        git submodule update --init --recursive
    fi
    
    packages=(mcp-streamablehttp-proxy mcp-oauth-dynamicclient mcp-streamablehttp-client)

    if [ "{{package}}" = "all" ]; then
        echo "🏗️  Building all Python packages..."
        for pkg in "${packages[@]}"; do
            echo "Building $pkg..."
            cd "$pkg"
            rm -rf dist/ build/ *.egg-info/
            uv run python -m build
            echo "✅ Built $pkg"
            cd ..
        done
    else
        echo "🏗️  Building {{package}}..."
        cd "{{package}}"
        rm -rf dist/ build/ *.egg-info/
        uv run python -m build
        echo "✅ Built {{package}}"
        cd ..
    fi

# Test a specific Python package (or all packages)
pypi-test package="all":
    #!/usr/bin/env bash
    # Ensure submodules are initialized
    submodule_missing=false
    for pkg in mcp-streamablehttp-client mcp-oauth-dynamicclient mcp-streamablehttp-proxy; do
        if [ ! -f "$pkg/pyproject.toml" ]; then
            submodule_missing=true
            break
        fi
    done
    
    if [ "$submodule_missing" = true ]; then
        echo "🔄 Initializing submodules..."
        git submodule update --init --recursive
    fi
    
    packages=(mcp-streamablehttp-proxy mcp-oauth-dynamicclient mcp-streamablehttp-client)

    if [ "{{package}}" = "all" ]; then
        echo "🧪 Testing all Python packages..."
        for pkg in "${packages[@]}"; do
            echo "Testing $pkg..."
            cd "$pkg"
            if [ -f "pyproject.toml" ] && [ -d "tests" ]; then
                uv run pytest tests/ -v || echo "⚠️  Tests failed for $pkg"
            else
                echo "⚠️  No tests found for $pkg"
            fi
            echo "✅ Tested $pkg"
            cd ..
        done
    else
        echo "🧪 Testing {{package}}..."
        cd "{{package}}"
        if [ -f "pyproject.toml" ] && [ -d "tests" ]; then
            uv run pytest tests/ -v
        else
            echo "⚠️  No tests found for {{package}}"
        fi
        echo "✅ Tested {{package}}"
        cd ..
    fi

# Check package distribution (validate built packages)
pypi-check package="all":
    #!/usr/bin/env bash
    packages=(mcp-streamablehttp-proxy mcp-oauth-dynamicclient mcp-streamablehttp-client)

    if [ "{{package}}" = "all" ]; then
        echo "🔍 Checking all Python packages..."
        for pkg in "${packages[@]}"; do
            echo "Checking $pkg..."
            cd "$pkg"
            if [ -d "dist" ]; then
                uv run twine check dist/*
                echo "✅ Checked $pkg"
            else
                echo "⚠️  No dist/ directory found for $pkg - run 'just pypi-build $pkg' first"
            fi
            cd ..
        done
    else
        echo "🔍 Checking {{package}}..."
        cd "{{package}}"
        if [ -d "dist" ]; then
            uv run twine check dist/*
            echo "✅ Checked {{package}}"
        else
            echo "⚠️  No dist/ directory found for {{package}} - run 'just pypi-build {{package}}' first"
        fi
        cd ..
    fi

# Upload to TestPyPI (for testing)
pypi-upload-test package="all":
    #!/usr/bin/env bash
    packages=(mcp-streamablehttp-proxy mcp-oauth-dynamicclient mcp-streamablehttp-client)

    echo "⚠️  WARNING: This will upload to TestPyPI!"

    # Check if required environment variables are set
    if [ -z "${TWINE_USERNAME:-}" ] || [ -z "${TWINE_PASSWORD:-}" ]; then
        echo "❌ ERROR: TWINE_USERNAME and TWINE_PASSWORD must be set for TestPyPI"
        echo "TWINE_USERNAME: '${TWINE_USERNAME:-}'"
        echo "TWINE_PASSWORD length: ${#TWINE_PASSWORD}"
        echo "Please add them to your .env file"
        exit 1
    fi

    echo "✅ TWINE_USERNAME: ${TWINE_USERNAME}"
    echo "✅ TWINE_PASSWORD length: ${#TWINE_PASSWORD}"
    echo "🤖 Proceeding automatically without prompts"

    if [ "{{package}}" = "all" ]; then
        echo "📤 Uploading all packages to TestPyPI..."
        for pkg in "${packages[@]}"; do
            echo "Uploading $pkg to TestPyPI..."
            cd "$pkg"
            if [ -d "dist" ]; then
                if uv run twine upload --repository testpypi dist/* --skip-existing; then
                    echo "✅ Uploaded $pkg to TestPyPI"
                else
                    echo "❌ Upload failed for $pkg"
                    echo "💡 Common solutions:"
                    echo "   - Version already exists: Increment version in pyproject.toml"
                    echo "   - Run: just pypi-build $pkg (to rebuild with new version)"
                    echo "   - Check https://test.pypi.org/project/$pkg for existing versions"
                fi
            else
                echo "⚠️  No dist/ directory found for $pkg - run 'just pypi-build $pkg' first"
            fi
            cd ..
        done
    else
        echo "📤 Uploading {{package}} to TestPyPI..."
        cd "{{package}}"
        if [ -d "dist" ]; then
            if uv run twine upload --repository testpypi dist/* --skip-existing; then
                echo "✅ Uploaded {{package}} to TestPyPI"
            else
                echo "❌ Upload failed for {{package}}"
                echo "💡 Common solutions:"
                echo "   - Version already exists: Increment version in pyproject.toml"
                echo "   - Run: just pypi-build {{package}} (to rebuild with new version)"
                echo "   - Check https://test.pypi.org/project/{{package}} for existing versions"
            fi
        else
            echo "⚠️  No dist/ directory found for {{package}} - run 'just pypi-build {{package}}' first"
        fi
        cd ..
    fi

# Upload to PyPI (PRODUCTION - BE CAREFUL!)
pypi-upload package="all":
    #!/usr/bin/env bash
    packages=(mcp-streamablehttp-proxy mcp-oauth-dynamicclient mcp-streamablehttp-client)

    echo "🚨 WARNING: This will upload to PRODUCTION PyPI!"

    # Check if required environment variables are set
    if [ -z "${TWINE_USERNAME:-}" ] || [ -z "${TWINE_PASSWORD:-}" ]; then
        echo "❌ ERROR: TWINE_USERNAME and TWINE_PASSWORD must be set for PyPI"
        echo "TWINE_USERNAME: '${TWINE_USERNAME:-}'"
        echo "TWINE_PASSWORD length: ${#TWINE_PASSWORD}"
        echo "Please add them to your .env file"
        exit 1
    fi

    echo "✅ TWINE_USERNAME: ${TWINE_USERNAME}"
    echo "✅ TWINE_PASSWORD length: ${#TWINE_PASSWORD}"
    echo "🚨 This action cannot be undone!"
    echo "🤖 Proceeding automatically without prompts"

    if [ "{{package}}" = "all" ]; then
        echo "📤 Uploading all packages to PyPI..."
        for pkg in "${packages[@]}"; do
            echo "Uploading $pkg to PyPI..."
            cd "$pkg"
            if [ -d "dist" ]; then
                uv run twine upload dist/*
                echo "✅ Uploaded $pkg to PyPI"
            else
                echo "⚠️  No dist/ directory found for $pkg - run 'just pypi-build $pkg' first"
            fi
            cd ..
        done
    else
        echo "📤 Uploading {{package}} to PyPI..."
        cd "{{package}}"
        if [ -d "dist" ]; then
            uv run twine upload dist/*
            echo "✅ Uploaded {{package}} to PyPI"
        else
            echo "⚠️  No dist/ directory found for {{package}} - run 'just pypi-build {{package}}' first"
        fi
        cd ..
    fi

# Complete build, test, check, and upload workflow for TestPyPI
pypi-publish-test package="all":
    echo "🚀 Complete TestPyPI publish workflow for {{package}}..."
    just pypi-build {{package}}
    just pypi-test {{package}}
    just pypi-check {{package}}
    just pypi-upload-test {{package}}
    echo "✅ {{package}} published to TestPyPI successfully!"

# Complete build, test, check, and upload workflow for PyPI
pypi-publish package="all":
    echo "🚀 Complete PyPI publish workflow for {{package}}..."
    just pypi-build {{package}}
    just pypi-test {{package}}
    just pypi-check {{package}}
    just pypi-upload {{package}}
    echo "✅ {{package}} published to PyPI successfully!"

# Clean all package build artifacts
pypi-clean package="all":
    #!/usr/bin/env bash
    packages=(mcp-streamablehttp-proxy mcp-oauth-dynamicclient mcp-streamablehttp-client)

    if [ "{{package}}" = "all" ]; then
        echo "🧹 Cleaning all Python package build artifacts..."
        for pkg in "${packages[@]}"; do
            echo "Cleaning $pkg..."
            cd "$pkg"
            rm -rf dist/ build/ *.egg-info/ __pycache__/ .pytest_cache/
            find . -name "*.pyc" -delete
            find . -name "*.pyo" -delete
            echo "✅ Cleaned $pkg"
            cd ..
        done
    else
        echo "🧹 Cleaning {{package}} build artifacts..."
        cd "{{package}}"
        rm -rf dist/ build/ *.egg-info/ __pycache__/ .pytest_cache/
        find . -name "*.pyc" -delete
        find . -name "*.pyo" -delete
        echo "✅ Cleaned {{package}}"
        cd ..
    fi

# Show package information and versions
pypi-info package="all":
    #!/usr/bin/env bash
    packages=(mcp-streamablehttp-proxy mcp-oauth-dynamicclient mcp-streamablehttp-client)

    if [ "{{package}}" = "all" ]; then
        echo "📋 Package Information for all packages:"
        for pkg in "${packages[@]}"; do
            echo ""
            echo "=== $pkg ==="
            cd "$pkg"
            if [ -f "pyproject.toml" ]; then
                echo "Version: $(grep -E '^version\s*=' pyproject.toml | cut -d'"' -f2)"
                echo "Description: $(grep -E '^description\s*=' pyproject.toml | cut -d'"' -f2)"
                echo "Python Requires: $(grep -E 'requires-python\s*=' pyproject.toml | cut -d'"' -f2 || echo 'Not specified')"
                if [ -d "dist" ]; then
                    echo "Built packages:"
                    ls -la dist/
                fi
            else
                echo "⚠️  No pyproject.toml found"
            fi
            cd ..
        done
    else
        echo "📋 Package Information for {{package}}:"
        cd "{{package}}"
        if [ -f "pyproject.toml" ]; then
            echo "Version: $(grep -E '^version\s*=' pyproject.toml | cut -d'"' -f2)"
            echo "Description: $(grep -E '^description\s*=' pyproject.toml | cut -d'"' -f2)"
            echo "Python Requires: $(grep -E 'requires-python\s*=' pyproject.toml | cut -d'"' -f2 || echo 'Not specified')"
            if [ -d "dist" ]; then
                echo "Built packages:"
                ls -la dist/
            fi
        else
            echo "⚠️  No pyproject.toml found"
        fi
        cd ..
    fi

# Aliases for convenience
alias pb := pypi-build
alias pt := pypi-test
alias pc := pypi-check
alias pu := pypi-upload
alias ppt := pypi-publish-test
alias pp := pypi-publish
