set dotenv-load := true          # FIRST LINE - ALWAYS! Load .env automatically!
set dotenv-required              # DIE if .env is missing! No mercy for the unprepared!
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
    pixi run python scripts/check_services_ready.py || (echo "❌ Services not ready! See above for details." && exit 1)

# Universal test runner with flexible arguments (replaces test, test-all, test-file, test-verbose)
test *args:
    pixi run pytest {{args}}
    echo "\n🧹 Cleaning up test registrations..."

# Alias for backwards compatibility
alias t := test

# Run tests in parallel using all CPU cores
test-parallel *args:
    pixi run pytest -n auto {{args}}

# Run tests in parallel with specific worker count
test-n count *args:
    pixi run pytest -n {{count}} {{args}}

# Run tests in parallel with optimal distribution strategy
test-fast *args:
    pixi run pytest -n auto --dist worksteal {{args}}

# Run tests by module (keeps tests in same file together)
test-by-module *args:
    pixi run pytest -n auto --dist loadfile {{args}}

# Run tests by class (keeps tests in same class together)
test-by-class *args:
    pixi run pytest -n auto --dist loadscope {{args}}

# Run only serial tests (those marked with @pytest.mark.serial)
test-serial:
    pixi run pytest -m serial

# Run parallel tests excluding serial ones
test-parallel-safe:
    pixi run pytest -n auto -m "not serial" --dist worksteal

# Run tests with sidecar coverage pattern
test-sidecar-coverage:
    docker compose down --remove-orphans
    docker compose -f docker-compose.yml -f docker-compose.coverage.yml up -d
    echo "Waiting for services to be ready..."
    pixi run python scripts/check_services_ready.py || (echo "❌ Services not ready!" && exit 1)
    pixi run pytest tests/ -v
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
    pixi run python scripts/generate_coverage_report.py || echo "Local report generation had issues"

# Debug coverage setup
debug-coverage: ensure-services-ready
    docker compose down --remove-orphans
    docker compose -f docker-compose.yml -f docker-compose.coverage.yml up -d
    echo "Waiting for services..."
    pixi run python scripts/check_services_ready.py || (echo "❌ Services not ready!" && exit 1)
    echo "=== Debugging coverage setup in auth container ==="
    docker compose -f docker-compose.yml -f docker-compose.coverage.yml exec auth python /scripts/debug_coverage.py || echo "Debug script failed"
    echo "=== Auth container environment ==="
    docker compose -f docker-compose.yml -f docker-compose.coverage.yml exec auth env | grep -E "PYTHON|COVERAGE" || echo "No coverage env vars"
    docker compose -f docker-compose.includes.yml -f docker-compose.coverage.yml down

# Build documentation with Jupyter Book
docs-build:
    pixi run jupyter-book build docs/

# Lint and format code - The Divine Code Quality Commandments!
# This runs ALL quality checks: linting, formatting, pre-commit hooks, and deprecation hunting
lint:
    @echo "🔥 Running Divine Code Quality Checks ⚡"
    @echo "========================================"
    @echo ""
    @echo "1️⃣ Ruff Linting..."
    pixi run pre-commit run ruff --all-files
    @echo "✅ Ruff linting passed!"
    @echo ""
    @echo "2️⃣ Code Formatting Check..."
    pixi run pre-commit run ruff-format --all-files
    @echo "✅ Code formatting check passed!"
    @echo ""
    @echo "3️⃣ Pre-commit Hooks..."
    pixi run pre-commit run --all-files || true
    @echo "✅ Pre-commit hooks completed!"
    @echo ""
    @echo "4️⃣ Pydantic Deprecation Hunt..."
    pixi run python scripts/lint_pydantic_compliance.py
    @echo ""
    @echo "🏆 ALL QUALITY CHECKS COMPLETED! Divine compliance achieved! ⚡"

# Quick lint - just run ruff check (for fast feedback)
lint-quick:
    pixi run pre-commit run ruff --all-files

# Fix linting issues automatically
lint-fix:
    pixi run pre-commit run ruff --all-files

# Format code with divine standards
format:
    pixi run pre-commit run ruff-format --all-files

# Check code formatting without making changes
format-check:
    pixi run pre-commit run ruff-format --all-files

# Hunt for Pydantic deprecations
lint-pydantic:
    pixi run python scripts/lint_pydantic_compliance.py

# Complete linting with deprecation hunting
lint-all:
    pixi run pre-commit run ruff --all-files
    pixi run python scripts/lint_pydantic_compliance.py

# Comprehensive linting: fix, format, and hunt deprecations
lint-comprehensive:
    pixi run pre-commit run ruff --all-files
    pixi run pre-commit run ruff-format --all-files
    pixi run python scripts/lint_pydantic_compliance.py


# Docker operations

# Create the sacred shared network
network-create:
    docker network create public || true

# Create required volumes
volumes-create:
    docker volume create traefik-certificates || true
    docker volume create redis-data || true
    docker volume create coverage-data || true
    docker volume create auth-keys || true
    docker volume create mcp-memory-data || true

# Generate docker-compose includes based on enabled services
generate-includes:
    pixi run python scripts/generate_compose_includes.py

# Generate Traefik middlewares from template with environment variables
generate-middlewares:
    pixi run python scripts/generate_middlewares.py

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
    pixi run python scripts/check_services_ready.py || echo "⚠️  Some services may not be ready yet"

# Start all services with fresh build
up-fresh: network-create volumes-create generate-includes generate-middlewares
    just build
    docker compose -f docker-compose.includes.yml up -d --force-recreate
    echo "Waiting for services to be healthy..."
    pixi run python scripts/check_services_ready.py || echo "⚠️  Some services may not be ready yet"

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
        docker compose -f docker-compose.includes.yml build --no-cache
        docker compose -f docker-compose.includes.yml up -d
    else
        echo "Rebuilding: {{services}}"
        docker compose -f docker-compose.includes.yml build --no-cache {{services}}
        docker compose -f docker-compose.includes.yml up -d {{services}}
    fi
    echo "✅ Rebuild completed"
    pixi run python scripts/check_services_ready.py || echo "⚠️  Some services may not be ready yet"

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

# Project-specific commands

# Generate JWT secret and save to .env
generate-jwt-secret:
    #!/usr/bin/env bash
    NEW_JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "🔐 Generated new JWT secret: ${NEW_JWT_SECRET}"

    # Check if .env exists
    if [ ! -f .env ]; then
        echo "❌ .env file not found! Creating one..."
        echo "GATEWAY_JWT_SECRET=${NEW_JWT_SECRET}" > .env
        echo "✅ Created .env with GATEWAY_JWT_SECRET"
    else
        # Check if GATEWAY_JWT_SECRET already exists in .env
        if grep -q "^GATEWAY_JWT_SECRET=" .env; then
            # Update existing GATEWAY_JWT_SECRET
            sed -i.bak "s/^GATEWAY_JWT_SECRET=.*/GATEWAY_JWT_SECRET=${NEW_JWT_SECRET}/" .env
            echo "✅ Updated GATEWAY_JWT_SECRET in .env file"
        else
            # Add GATEWAY_JWT_SECRET to .env
            echo "GATEWAY_JWT_SECRET=${NEW_JWT_SECRET}" >> .env
            echo "✅ Added GATEWAY_JWT_SECRET to .env file"
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
    pixi run python scripts/{{script}}.py {{args}}

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
    pixi run python scripts/test_mcp_hostnames.py

# Service-specific rebuilds are now: just rebuild auth, just rebuild mcp-fetch, etc.

# Analysis commands
analyze-oauth-logs:
    mkdir -p reports
    pixi run python scripts/analyze_oauth_logs.py > reports/oauth-analysis-$(date +%Y%m%d-%H%M%S).md

# Health check commands - checks both environment tokens and services
check-health:
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo "🏥 MCP OAuth Gateway Health Check"
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    @echo ""
    @echo "Step 1/3: Checking environment tokens..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    pixi run python scripts/check_env_tokens.py
    @echo ""
    @echo "Step 2/3: Checking Docker services..."
    @echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    pixi run python scripts/check_services_ready.py
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
    pixi run python scripts/check_env_tokens.py

# Check only services
check-services:
    pixi run python scripts/check_services_ready.py

# Quick health check (simple version)
@health-quick:
    echo "Checking service health..."
    curl -f https://auth.${BASE_DOMAIN}/.well-known/oauth-authorization-server || echo "Auth service not healthy"
    curl -f https://mcp-fetch.${BASE_DOMAIN}/.well-known/oauth-authorization-server || echo "MCP-fetch OAuth discovery not accessible"

# Show service status with health information
status:
    @pixi run python scripts/show_service_status.py

# Check SSL certificates
check-ssl:
	#!/usr/bin/env bash
	set -euo pipefail

	echo "Checking SSL certificates..."
	echo ""
	echo "=== Auth Service ==="
	curl -I https://auth.${BASE_DOMAIN}/.well-known/oauth-authorization-server 2>&1 | grep -E "HTTP|SSL|certificate" || echo "Auth SSL check failed"
	echo ""
	echo "=== MCP Services (checking enabled services only) ==="
	echo ""

	# Check each MCP service if enabled
	if [ "${MCP_EVERYTHING_ENABLED}" = "true" ]; then
		echo "MCP Everything (${MCP_EVERYTHING_URLS}):"
		for url in $(echo ${MCP_EVERYTHING_URLS} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_FETCH_ENABLED}" = "true" ]; then
		echo "MCP Fetch (${MCP_FETCH_URLS}):"
		for url in $(echo ${MCP_FETCH_URLS} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_FETCHS_ENABLED}" = "true" ]; then
		echo "MCP Fetchs (${MCP_FETCHS_URLS}):"
		for url in $(echo ${MCP_FETCHS_URLS} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_FILESYSTEM_ENABLED}" = "true" ]; then
		echo "MCP Filesystem (${MCP_FILESYSTEM_URLS}):"
		for url in $(echo ${MCP_FILESYSTEM_URLS} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_MEMORY_ENABLED}" = "true" ]; then
		echo "MCP Memory (${MCP_MEMORY_URLS}):"
		for url in $(echo ${MCP_MEMORY_URLS} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_PLAYWRIGHT_ENABLED}" = "true" ]; then
		echo "MCP Playwright (${MCP_PLAYWRIGHT_URLS}):"
		for url in $(echo ${MCP_PLAYWRIGHT_URLS} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_SEQUENTIALTHINKING_ENABLED}" = "true" ]; then
		echo "MCP Sequential Thinking (${MCP_SEQUENTIALTHINKING_URLS}):"
		for url in $(echo ${MCP_SEQUENTIALTHINKING_URLS} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_TIME_ENABLED}" = "true" ]; then
		echo "MCP Time (${MCP_TIME_URLS}):"
		for url in $(echo ${MCP_TIME_URLS} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	if [ "${MCP_TMUX_ENABLED}" = "true" ]; then
		echo "MCP Tmux (${MCP_TMUX_URLS}):"
		for url in $(echo ${MCP_TMUX_URLS} | tr ',' ' '); do
			curl -I "$url" 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: $url"
		done
		echo ""
	fi

	# MCP Echo service (special handling as it's not in the standard pattern)
	if [ "${MCP_ECHO_ENABLED:-false}" = "true" ]; then
		echo "MCP Echo:"
		curl -I https://echo.${BASE_DOMAIN}/mcp 2>&1 | grep -E "HTTP|SSL|certificate" || echo "  Failed: echo service"
		echo ""
	fi

	echo ""
	echo "=== Certificates in ACME storage ==="
	docker exec traefik cat /certificates/acme.json 2>/dev/null | jq -r '.letsencrypt.Certificates[].domain' || echo "No certificates found or Traefik not running"

# Generate MCP client token using mcp-streamablehttp-client
mcp-client-token:
    echo "🔐 Generating MCP client token using mcp-streamablehttp-client..."
    pixi run install-mcp-client || true
    export MCP_SERVER_URL="https://mcp-fetch.${BASE_DOMAIN}/mcp" && \
    pixi run python -m mcp_streamablehttp_client.cli --token --server-url "$MCP_SERVER_URL"

# Complete MCP client token flow with auth code
mcp-client-token-complete auth_code:
    echo "🔐 Completing MCP client token flow with authorization code..."
    export MCP_SERVER_URL="https://mcp-fetch.${BASE_DOMAIN}/mcp" && \
    export MCP_AUTH_CODE="{{ auth_code }}" && \
    pixi run python scripts/complete_mcp_oauth.py


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
    pixi install
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
    ls -t backups/oauth-backup-*.json 2>/dev/null | head -1 | xargs pixi run python scripts/view_oauth_backup.py || echo "No backups found"

# View contents of specific backup file
oauth-backup-view-file filename:
    echo "📋 Viewing backup: {{filename}}..."
    just run view_oauth_backup backups/{{filename}}

# PyPI Package Management - The Sacred Publishing Commandments!

# Build a specific Python package (or all packages)
pypi-build package="all":
    #!/usr/bin/env bash
    packages=(mcp-streamablehttp-proxy mcp-oauth-dynamicclient mcp-streamablehttp-client mcp-fetch-streamablehttp-server mcp-echo-streamablehttp-server-stateless)

    if [ "{{package}}" = "all" ]; then
        echo "🏗️  Building all Python packages..."
        for pkg in "${packages[@]}"; do
            echo "Building $pkg..."
            cd "$pkg"
            rm -rf dist/ build/ *.egg-info/
            pixi run python -m build
            echo "✅ Built $pkg"
            cd ..
        done
    else
        echo "🏗️  Building {{package}}..."
        cd "{{package}}"
        rm -rf dist/ build/ *.egg-info/
        pixi run python -m build
        echo "✅ Built {{package}}"
        cd ..
    fi

# Test a specific Python package (or all packages)
pypi-test package="all":
    #!/usr/bin/env bash
    packages=(mcp-streamablehttp-proxy mcp-oauth-dynamicclient mcp-streamablehttp-client mcp-fetch-streamablehttp-server mcp-echo-streamablehttp-server-stateless)

    if [ "{{package}}" = "all" ]; then
        echo "🧪 Testing all Python packages..."
        for pkg in "${packages[@]}"; do
            echo "Testing $pkg..."
            cd "$pkg"
            if [ -f "pyproject.toml" ] && [ -d "tests" ]; then
                pixi run pytest tests/ -v || echo "⚠️  Tests failed for $pkg"
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
            pixi run pytest tests/ -v
        else
            echo "⚠️  No tests found for {{package}}"
        fi
        echo "✅ Tested {{package}}"
        cd ..
    fi

# Check package distribution (validate built packages)
pypi-check package="all":
    #!/usr/bin/env bash
    packages=(mcp-streamablehttp-proxy mcp-oauth-dynamicclient mcp-streamablehttp-client mcp-fetch-streamablehttp-server mcp-echo-streamablehttp-server-stateless)

    if [ "{{package}}" = "all" ]; then
        echo "🔍 Checking all Python packages..."
        for pkg in "${packages[@]}"; do
            echo "Checking $pkg..."
            cd "$pkg"
            if [ -d "dist" ]; then
                pixi run twine check dist/*
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
            pixi run twine check dist/*
            echo "✅ Checked {{package}}"
        else
            echo "⚠️  No dist/ directory found for {{package}} - run 'just pypi-build {{package}}' first"
        fi
        cd ..
    fi

# Upload to TestPyPI (for testing)
pypi-upload-test package="all":
    #!/usr/bin/env bash
    packages=(mcp-streamablehttp-proxy mcp-oauth-dynamicclient mcp-streamablehttp-client mcp-fetch-streamablehttp-server mcp-echo-streamablehttp-server-stateless)

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
                if pixi run twine upload --repository testpypi dist/* --skip-existing; then
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
            if pixi run twine upload --repository testpypi dist/* --skip-existing; then
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
    packages=(mcp-streamablehttp-proxy mcp-oauth-dynamicclient mcp-streamablehttp-client mcp-fetch-streamablehttp-server mcp-echo-streamablehttp-server-stateless)

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
                pixi run twine upload dist/*
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
            pixi run twine upload dist/*
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
    packages=(mcp-streamablehttp-proxy mcp-oauth-dynamicclient mcp-streamablehttp-client mcp-fetch-streamablehttp-server mcp-echo-streamablehttp-server-stateless)

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
    packages=(mcp-streamablehttp-proxy mcp-oauth-dynamicclient mcp-streamablehttp-client mcp-fetch-streamablehttp-server mcp-echo-streamablehttp-server-stateless)

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
