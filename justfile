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

# Run tests with pytest (no mocking allowed!)
test: ensure-services-ready validate-tokens
    @pixi run python scripts/check_test_requirements.py || (echo "❌ Test requirements not met! See above for details." && exit 1)
    @pixi run pytest tests/ -v

# Run all tests including integration
test-all: ensure-services-ready validate-tokens
    @pixi run python scripts/check_test_requirements.py || (echo "❌ Test requirements not met! See above for details." && exit 1)
    @pixi run pytest tests/ -v --tb=short

# Run tests with verbose output
test-verbose: ensure-services-ready validate-tokens
    @pixi run python scripts/check_test_requirements.py || (echo "❌ Test requirements not met! See above for details." && exit 1)
    @pixi run pytest tests/ -v -s

# Run tests with sidecar coverage pattern
test-sidecar-coverage: ensure-services-ready validate-tokens
    @docker compose down --remove-orphans
    @docker compose -f docker-compose.yml -f docker-compose.coverage.yml up -d
    @echo "Waiting for services to be ready..."
    @pixi run python scripts/check_services_ready.py || (echo "❌ Services not ready!" && exit 1)
    @pixi run pytest tests/ -v
    @echo "Triggering graceful shutdown to collect coverage data..."
    @docker compose -f docker-compose.yml -f docker-compose.coverage.yml stop auth
    @echo "Waiting for coverage harvester to complete..."
    @sleep 5
    @docker compose -f docker-compose.yml -f docker-compose.coverage.yml logs coverage-harvester
    @echo "Coverage collection complete"
    @docker compose -f docker-compose.yml -f docker-compose.coverage.yml down

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
    @docker compose -f docker-compose.yml -f docker-compose.coverage.yml down

# Build documentation with Jupyter Book
docs-build:
    @pixi run jupyter-book build docs/

# Lint and format code
lint:
    @pixi run ruff check .
    @pixi run ruff format .

# Development commands

# Start development environment
dev:
    @just up

# Docker operations

# Create the sacred shared network
network-create:
    @docker network create public || true

# Create required volumes
volumes-create:
    @docker volume create traefik-certificates || true
    @docker volume create redis-data || true
    @docker volume create coverage-data || true

# Build all services
build-all: network-create volumes-create
    @echo "Building all services..."
    @docker compose build
    @echo "✅ All services built successfully"

# Start all services
up: network-create volumes-create
    @docker compose up -d
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
    @docker compose -f {{service}}/docker-compose.yml build --no-cache
    @docker compose up -d {{service}}

# View service logs
logs:
    @docker compose logs -f

# Project-specific commands

# Generate JWT secret and save to .env
generate-jwt-secret:
    #!/usr/bin/env bash
    NEW_JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "🔐 Generated new JWT secret: ${NEW_JWT_SECRET}"
    
    # Check if .env exists
    if [ ! -f .env ]; then
        echo "❌ .env file not found! Creating one..."
        echo "JWT_SECRET=${NEW_JWT_SECRET}" > .env
        echo "✅ Created .env with JWT_SECRET"
    else
        # Check if JWT_SECRET already exists in .env
        if grep -q "^JWT_SECRET=" .env; then
            # Update existing JWT_SECRET
            sed -i.bak "s/^JWT_SECRET=.*/JWT_SECRET=${NEW_JWT_SECRET}/" .env
            echo "✅ Updated JWT_SECRET in .env file"
        else
            # Add JWT_SECRET to .env
            echo "JWT_SECRET=${NEW_JWT_SECRET}" >> .env
            echo "✅ Added JWT_SECRET to .env file"
        fi
    fi
    
    echo "🔥 SACRED JWT SECRET HAS BEEN BLESSED AND WRITTEN TO .ENV!"

# Generate GitHub OAuth token
generate-github-token:
    @pixi run python scripts/generate_oauth_token.py

# Validate all OAuth tokens
validate-tokens:
    @echo "🔍 Validating OAuth tokens..."
    @pixi run python scripts/validate_tokens.py

# Check token expiration and refresh if needed
check-token-expiry:
    @echo "⏰ Checking token expiration..."
    @pixi run python scripts/check_token_expiry.py

# Refresh OAuth tokens if expired
refresh-tokens:
    @echo "🔄 Refreshing OAuth tokens..."
    @pixi run python scripts/refresh_oauth_tokens.py

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
    @if [ -z "${OAUTH_ACCESS_TOKEN:-}" ]; then \
        echo "❌ OAUTH_ACCESS_TOKEN not found in .env file"; \
        echo "Please run 'just generate-github-token' first"; \
        exit 1; \
    fi
    @claude mcp add mcp-fetch https://mcp-fetch.${BASE_DOMAIN}/mcp \
        --transport http \
        --header "Authorization: Bearer ${OAUTH_ACCESS_TOKEN}" \
        || echo "Failed to add mcp-fetch server"
    @echo "✅ MCP servers added to Claude Code!"

# Complete setup: generate token and create config
setup-claude-code: generate-github-token create-mcp-config
    @echo "✅ Claude Code setup complete!"
    @echo "📝 MCP config saved to ~/.config/claude/mcp-config.json"

# OAuth-specific testing
test-oauth-flow: ensure-services-ready
    @pixi run pytest tests/test_oauth_flow.py -v -s

test-mcp-protocol: ensure-services-ready
    @pixi run pytest tests/test_mcp_protocol.py -v -s

test-claude-integration: ensure-services-ready
    @pixi run pytest tests/test_claude_integration.py -v -s

# Service-specific rebuilds
rebuild-auth:
    @docker compose build auth
    @docker compose up -d auth --force-recreate

rebuild-mcp-fetch:
    @docker compose build mcp-fetch
    @docker compose up -d mcp-fetch --force-recreate

rebuild-traefik:
    @docker compose -f traefik/docker-compose.yml up -d traefik

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
    @curl -f https://auth.${BASE_DOMAIN}/health || echo "Auth service not healthy"
    @curl -f https://mcp-fetch.${BASE_DOMAIN}/health || echo "MCP-fetch not healthy"

# Check SSL certificates
check-ssl:
    @echo "Checking SSL certificates..."
    @echo "Auth service:"
    @curl -I https://auth.${BASE_DOMAIN}/health 2>&1 | grep -E "HTTP|SSL|certificate" || echo "Auth SSL check failed"
    @echo ""
    @echo "MCP-fetch service:"
    @curl -I https://mcp-fetch.${BASE_DOMAIN}/sse 2>&1 | grep -E "HTTP|SSL|certificate" || echo "MCP-fetch SSL check failed"
    @echo ""
    @echo "Certificates in ACME storage:"
    @docker exec traefik cat /certificates/acme.json | jq -r '.letsencrypt.Certificates[].domain' || echo "No certificates found"

# Setup commands
setup: network-create volumes-create
    @echo "Setting up MCP OAuth Gateway..."
    @pixi install
    @echo "Setup complete! Run 'just up' to start services."