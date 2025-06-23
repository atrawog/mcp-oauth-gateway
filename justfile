set dotenv-load := true  # FIRST LINE - ALWAYS!
set export := true       # Export all variables to recipes

# Enable Compose Bake for better performance
export COMPOSE_BAKE := "true"

# The Sacred justfile for MCP OAuth Gateway
# Following the divine commandments of CLAUDE.md

# Show all available commands (default)
default:
    @just --list

# Universal commands mandated by the commandments

# Ensure all services are ready before tests
ensure-services-ready:
    @pixi run python scripts/check_services_ready.py || (echo "❌ Services not ready! See above for details." && exit 1)

# Run tests with pytest (no mocking allowed!) and cleanup after
test:
    @pixi run pytest tests/ -v
    @echo "\n🧹 Cleaning up test registrations..."

# Run all tests including integration and cleanup after
test-all:
    @pixi run pytest tests/ -v --tb=short
    @echo "\n🧹 Cleaning up test registrations..."

# Run a single test file and cleanup after
test-file file:
    @pixi run pytest {{ file }} -v
    @echo "\n🧹 Cleaning up test registrations..."

# Run tests with verbose output and cleanup after
test-verbose:
    @pixi run pytest tests/ -v -s
    @echo "\n🧹 Cleaning up test registrations..."
 
# Run tests with sidecar coverage pattern
test-sidecar-coverage:
    @docker compose down --remove-orphans
    @docker compose -f docker-compose.yml -f docker-compose.coverage.yml up -d
    @echo "Waiting for services to be ready..."
    @pixi run python scripts/check_services_ready.py || (echo "❌ Services not ready!" && exit 1)
    @pixi run pytest tests/ -v
    @echo "Triggering graceful shutdown to collect coverage data..."
    @docker compose -f docker-compose.yml -f docker-compose.coverage.yml stop auth
    @echo "Waiting for coverage harvester to complete..."
    @sleep 10
    @echo ""
    @echo "📊 Coverage Report from Container:"
    @echo "=================================="
    @docker logs coverage-harvester 2>&1 | grep -A50 "Name" | grep -B50 "TOTAL" || echo "Coverage report not found in logs"
    @echo ""
    @echo "Copying coverage data locally..."
    @docker cp coverage-harvester:/coverage-data/.coverage . 2>/dev/null || echo "No coverage file to copy"
    @docker compose -f docker-compose.includes.yml -f docker-compose.coverage.yml down
    @echo "Attempting local report generation..."
    @pixi run python scripts/generate_coverage_report.py || echo "Local report generation had issues"

# Debug coverage setup
debug-coverage: ensure-services-ready
    @docker compose down --remove-orphans
    @docker compose -f docker-compose.yml -f docker-compose.coverage.yml up -d
    @echo "Waiting for services..."
    @pixi run python scripts/check_services_ready.py || (echo "❌ Services not ready!" && exit 1)
    @echo "=== Debugging coverage setup in auth container ==="
    @docker compose -f docker-compose.yml -f docker-compose.coverage.yml exec auth python /scripts/debug_coverage.py || echo "Debug script failed"
    @echo "=== Auth container environment ==="
    @docker compose -f docker-compose.yml -f docker-compose.coverage.yml exec auth env | grep -E "PYTHON|COVERAGE" || echo "No coverage env vars"
    @docker compose -f docker-compose.includes.yml -f docker-compose.coverage.yml down

# Build documentation with Jupyter Book
docs-build:
    @pixi run jupyter-book build docs/

# Lint and format code
lint:
    @pixi run ruff check .
    @pixi run ruff format .


# Docker operations

# Create the sacred shared network
network-create:
    @docker network create public || true

# Create required volumes
volumes-create:
    @docker volume create traefik-certificates || true
    @docker volume create redis-data || true
    @docker volume create coverage-data || true
    @docker volume create auth-keys || true
    @docker volume create mcp-memory-data || true

# Generate docker-compose includes based on enabled services
generate-includes:
    @pixi run python scripts/generate_compose_includes.py

# Build all services
build-all: network-create volumes-create generate-includes
    @echo "Building all services..."
    @docker compose -f docker-compose.includes.yml build
    @echo "✅ All services built successfully"

# Start all services
up: network-create volumes-create generate-includes
    @docker compose -f docker-compose.includes.yml up -d
    @echo "Waiting for services to be healthy..."
    @pixi run python scripts/check_services_ready.py || echo "⚠️  Some services may not be ready yet"

# Start all services with fresh build
up-fresh: network-create volumes-create build-all
    @docker compose up -d --force-recreate
    @echo "Waiting for services to be healthy..."
    @pixi run python scripts/check_services_ready.py || echo "⚠️  Some services may not be ready yet"

# Stop all services
down:
    @docker compose down

# Rebuild all services with no cache
rebuild-all: down
    @echo "Rebuilding all services from scratch..."
    @docker compose build --no-cache
    @echo "✅ All services rebuilt successfully"
    @docker compose up -d
    @echo "Waiting for services to be healthy..."
    @pixi run python scripts/check_services_ready.py || echo "⚠️  Some services may not be ready yet"

# Rebuild specific service
rebuild service:
    @echo "Rebuilding service: {{service}}"
    @docker compose build --no-cache {{service}}
    @docker compose up -d {{service}}
    @echo "✅ Service {{service}} rebuilt and started"

# View service logs (last 200 entries)
logs:
    @docker compose logs --tail=200

# Follow service logs in real-time
logs-follow:
    @docker compose logs -f

# Purge all container logs
logs-purge:
    @echo "🧹 Purging all container logs..."
    @docker compose down
    @docker compose up -d
    @echo "✅ All container logs purged (services restarted)"

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
    @echo "🔑 Generating RSA keys for RS256 JWT signing..."
    @pixi run python scripts/generate_rsa_keys_to_env.py

# Generate GitHub OAuth token
generate-github-token:
    @pixi run python scripts/generate_oauth_token.py

# Refresh OAuth tokens before tests
refresh-tokens:
    @echo "🔄 Refreshing OAuth tokens..."
    @pixi run python scripts/refresh_tokens.py

# Validate all OAuth tokens
validate-tokens:
    @echo "🔍 Validating OAuth tokens..."
    @pixi run python scripts/validate_tokens.py

# Check token expiration and refresh if needed
check-token-expiry:
    @echo "⏰ Checking token expiration..."
    @pixi run python scripts/check_token_expiry.py

# Diagnose test failures and find root causes
diagnose-tests:
    @echo "🔍 Diagnosing test failures..."
    @pixi run python scripts/diagnose_test_failures.py

# Create MCP configuration for Claude Code with bearer token
create-mcp-config:
    @pixi run python scripts/create_mcp_config.py

# Add MCP servers to Claude Code using claude mcp add
mcp-add:
    @echo "Adding MCP servers to Claude Code..."
    @if [ -z "${GATEWAY_OAUTH_ACCESS_TOKEN:-}" ]; then \
        echo "❌ GATEWAY_OAUTH_ACCESS_TOKEN not found in .env file"; \
        echo "Please run 'just generate-github-token' first"; \
        exit 1; \
    fi
    @claude mcp add mcp-fetch https://mcp-fetch.${BASE_DOMAIN}/mcp \
        --transport http \
        --header "Authorization: Bearer ${GATEWAY_OAUTH_ACCESS_TOKEN}" \
        || echo "Failed to add mcp-fetch server"
    @echo "✅ MCP servers added to Claude Code!"

# Complete setup: generate token and create config
setup-claude-code: generate-github-token create-mcp-config
    @echo "✅ Claude Code setup complete!"
    @echo "📝 MCP config saved to ~/.config/claude/mcp-config.json"

# Execute command in auth container
exec-auth *args:
    @docker exec auth {{args}}

# OAuth-specific testing
test-oauth-flow: ensure-services-ready
    @pixi run pytest tests/test_oauth_flow.py -v -s
    @echo "\n🧹 Cleaning up test registrations..."
    @pixi run python scripts/cleanup_test_data.py --execute

test-mcp-protocol: ensure-services-ready
    @pixi run pytest tests/test_mcp_protocol.py -v -s
    @echo "\n🧹 Cleaning up test registrations..."
    @pixi run python scripts/cleanup_test_data.py --execute

test-claude-integration: ensure-services-ready
    @pixi run pytest tests/test_claude_integration.py -v -s
    @echo "\n🧹 Cleaning up test registrations..."
    @pixi run python scripts/cleanup_test_data.py --execute

# MCP AI hostnames tests
test-mcp-hostnames: ensure-services-ready
    @pixi run pytest tests/test_mcp_ai_hostnames.py -v -s
    @echo "\n🧹 Cleaning up test registrations..."
    @pixi run python scripts/cleanup_test_data.py --execute


# Quick hostname connectivity check
check-mcp-hostnames:
    @pixi run python scripts/test_mcp_hostnames.py

# Service-specific rebuilds
rebuild-auth:
    @just rebuild auth

rebuild-mcp-fetch:
    @just rebuild mcp-fetch

rebuild-traefik:
    @just rebuild traefik

# Analysis commands
analyze-oauth-logs:
    @mkdir -p reports
    @pixi run python scripts/analyze_oauth_logs.py > reports/oauth-analysis-$(date +%Y%m%d-%H%M%S).md

# Health check commands
check-health:
    @pixi run python scripts/check_services_ready.py

# Quick health check (simple version)
health-quick:
    @echo "Checking service health..."
    @curl -f https://auth.${BASE_DOMAIN}/.well-known/oauth-authorization-server || echo "Auth service not healthy"
    @curl -f https://mcp-fetch.${BASE_DOMAIN}/.well-known/oauth-authorization-server || echo "MCP-fetch OAuth discovery not accessible"

# Check SSL certificates
check-ssl:
    @echo "Checking SSL certificates..."
    @echo "Auth service:"
    @curl -I https://auth.${BASE_DOMAIN}/.well-known/oauth-authorization-server 2>&1 | grep -E "HTTP|SSL|certificate" || echo "Auth SSL check failed"
    @echo ""
    @echo "MCP-fetch service:"
    @curl -I https://mcp-fetch.${BASE_DOMAIN}/sse 2>&1 | grep -E "HTTP|SSL|certificate" || echo "MCP-fetch SSL check failed"
    @echo ""
    @echo "Certificates in ACME storage:"
    @docker exec traefik cat /certificates/acme.json | jq -r '.letsencrypt.Certificates[].domain' || echo "No certificates found"

# Generate MCP client token using mcp-streamablehttp-client
mcp-client-token:
    @echo "🔐 Generating MCP client token using mcp-streamablehttp-client..."
    @pixi run install-mcp-client || true
    export MCP_SERVER_URL="https://mcp-fetch.${BASE_DOMAIN}/mcp" && \
    pixi run python -m mcp_streamablehttp_client.cli --token --server-url "$MCP_SERVER_URL"

# Complete MCP client token flow with auth code
mcp-client-token-complete auth_code:
    @echo "🔐 Completing MCP client token flow with authorization code..."
    @export MCP_SERVER_URL="https://mcp-fetch.${BASE_DOMAIN}/mcp" && \
    export MCP_AUTH_CODE="{{ auth_code }}" && \
    pixi run python scripts/complete_mcp_oauth.py


# OAuth Management Commands

# Show all OAuth client registrations
oauth-list-registrations:
    @echo "📋 Listing all OAuth client registrations..."
    @pixi run python scripts/manage_oauth_data.py list-registrations

# Show all active OAuth tokens
oauth-list-tokens:
    @echo "🔑 Listing all active OAuth tokens..."
    @pixi run python scripts/manage_oauth_data.py list-tokens

# Delete a specific client registration
oauth-delete-registration client_id:
    @echo "🗑️  Deleting client registration: {{client_id}}"
    @pixi run python scripts/manage_oauth_data.py delete-registration {{client_id}}

# Delete a client registration and ALL associated tokens
oauth-delete-client-complete client_id:
    @echo "🗑️  Deleting client registration and ALL associated data: {{client_id}}"
    @pixi run python scripts/manage_oauth_data.py delete-registration {{client_id}}

# Delete a specific token by JTI
oauth-delete-token jti:
    @echo "🗑️  Deleting token: {{jti}}"
    @pixi run python scripts/manage_oauth_data.py delete-token {{jti}}

# Delete ALL client registrations (dangerous!)
oauth-delete-all-registrations:
    @echo "⚠️  WARNING: This will delete ALL client registrations!"
    @pixi run python scripts/manage_oauth_data.py delete-all-registrations

# Delete ALL OAuth data - tokens, states, codes (dangerous!)
oauth-delete-all-tokens:
    @echo "⚠️  WARNING: This will delete ALL OAuth data (tokens, states, codes)!"
    @pixi run python scripts/manage_oauth_data.py delete-all-tokens

# Show OAuth statistics
oauth-stats:
    @echo "📊 OAuth Statistics:"
    @pixi run python scripts/manage_oauth_data.py stats

# Show all OAuth data (registrations + tokens + stats)
oauth-show-all: oauth-stats oauth-list-registrations oauth-list-tokens
    @echo "✅ Complete OAuth data displayed"

# Purge expired tokens (dry run - shows what would be deleted)
oauth-purge-expired-dry:
    @echo "🔍 Checking for expired tokens (DRY RUN)..."
    @pixi run python scripts/purge_expired_tokens.py --dry-run

# Purge expired tokens (actually delete them)
oauth-purge-expired:
    @echo "🧹 Purging expired tokens..."
    @pixi run python scripts/purge_expired_tokens.py

# Test cleanup commands - Sacred pattern: "TEST testname"
# Show all test registrations (dry run)
test-cleanup-show:
    @echo "🔍 Showing test registrations (client_name starting with 'TEST ')..."
    @pixi run python scripts/cleanup_test_data.py --show

# Cleanup test data
test-cleanup:
    @echo "🧹 Cleaning up test registrations..."
    @pixi run python scripts/cleanup_test_data.py --execute

# Setup commands
setup: network-create volumes-create
    @echo "Setting up MCP OAuth Gateway..."
    @pixi install
    @echo "Setup complete! Run 'just up' to start services."

# OAuth Backup and Restore Commands

# Backup all OAuth registrations and tokens
oauth-backup:
    @echo "🔐 Backing up OAuth registrations and tokens..."
    @pixi run python scripts/backup_oauth_data.py

# List available OAuth backups
oauth-backup-list:
    @echo "📋 Available OAuth backups:"
    @pixi run python scripts/restore_oauth_data.py --list

# Restore OAuth data from latest backup
oauth-restore:
    @echo "🔄 Restoring OAuth data from latest backup..."
    @pixi run python scripts/restore_oauth_data.py --latest

# Restore OAuth data from specific backup file
oauth-restore-file filename:
    @echo "🔄 Restoring OAuth data from {{filename}}..."
    @pixi run python scripts/restore_oauth_data.py --file {{filename}}

# Restore OAuth data from latest backup (clear existing data first)
oauth-restore-clear:
    @echo "🔄 Restoring OAuth data from latest backup (clearing existing data)..."
    @pixi run python scripts/restore_oauth_data.py --latest --clear

# Dry run - show what would be restored without making changes
oauth-restore-dry:
    @echo "🔍 Dry run - showing what would be restored..."
    @pixi run python scripts/restore_oauth_data.py --latest --dry-run

# View contents of latest backup
oauth-backup-view:
    @echo "📋 Viewing latest backup contents..."
    @ls -t backups/oauth-backup-*.json 2>/dev/null | head -1 | xargs pixi run python scripts/view_oauth_backup.py || echo "No backups found"

# View contents of specific backup file
oauth-backup-view-file filename:
    @echo "📋 Viewing backup: {{filename}}..."
    @pixi run python scripts/view_oauth_backup.py backups/{{filename}}