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
lint:
    pixi run ruff check .

# Fix linting issues automatically
lint-fix:
    pixi run ruff check . --fix

# Format code with divine standards
format:
    pixi run ruff format .

# Hunt for Pydantic deprecations
lint-pydantic:
    pixi run python scripts/lint_pydantic_compliance.py

# Complete linting with deprecation hunting
lint-all:
    pixi run ruff check .
    pixi run python scripts/lint_pydantic_compliance.py

# Comprehensive linting: fix, format, and hunt deprecations
lint-comprehensive:
    pixi run ruff check . --fix
    pixi run ruff format .
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

# Flexible build command with optional services
build *services: network-create volumes-create generate-includes
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
up *args: network-create volumes-create generate-includes
    docker compose -f docker-compose.includes.yml up -d {{args}}
    echo "Waiting for services to be healthy..."
    pixi run python scripts/check_services_ready.py || echo "⚠️  Some services may not be ready yet"

# Start all services with fresh build
up-fresh: network-create volumes-create
    just build
    docker compose up -d --force-recreate
    echo "Waiting for services to be healthy..."
    pixi run python scripts/check_services_ready.py || echo "⚠️  Some services may not be ready yet"

# Stop all services (with optional remove volumes/orphans)
down *args:
    docker compose down {{args}}

# Flexible rebuild command with optional services and no-cache by default
rebuild *services:
    #!/usr/bin/env bash
    if [ -z "{{services}}" ]; then
        echo "Rebuilding all services from scratch..."
        docker compose build --no-cache
        docker compose up -d
    else
        echo "Rebuilding: {{services}}"
        docker compose build --no-cache {{services}}
        docker compose up -d {{services}}
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
    docker compose logs {{args}}

# Follow logs (alias for convenience)
logs-follow *args:
    docker compose logs -f {{args}}

# Purge all container logs
logs-purge:
    echo "🧹 Purging all container logs..."
    docker compose down
    docker compose up -d
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
    docker compose exec -T {{service}} {{args}}

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

# Health check commands
check-health:
    pixi run python scripts/check_services_ready.py

# Quick health check (simple version)
@health-quick:
    echo "Checking service health..."
    curl -f https://auth.${BASE_DOMAIN}/.well-known/oauth-authorization-server || echo "Auth service not healthy"
    curl -f https://mcp-fetch.${BASE_DOMAIN}/.well-known/oauth-authorization-server || echo "MCP-fetch OAuth discovery not accessible"

# Check SSL certificates - @ prefix to show commands for debugging
@check-ssl:
    echo "Checking SSL certificates..."
    echo "Auth service:"
    curl -I https://auth.${BASE_DOMAIN}/.well-known/oauth-authorization-server 2>&1 | grep -E "HTTP|SSL|certificate" || echo "Auth SSL check failed"
    echo ""
    echo "MCP-fetch service:"
    curl -I https://mcp-fetch.${BASE_DOMAIN}/sse 2>&1 | grep -E "HTTP|SSL|certificate" || echo "MCP-fetch SSL check failed"
    echo ""
    echo "Certificates in ACME storage:"
    docker exec traefik cat /certificates/acme.json | jq -r '.letsencrypt.Certificates[].domain' || echo "No certificates found"

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