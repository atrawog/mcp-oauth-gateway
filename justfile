set dotenv-load := true  # FIRST LINE - ALWAYS!

# The Sacred justfile for MCP OAuth Gateway
# Following the divine commandments of CLAUDE.md

# Universal commands mandated by the commandments

# Run tests with pytest (no mocking allowed!)
test:
    @pixi run pytest tests/ -v

# Run all tests including integration
test-all:
    @pixi run pytest tests/ -v --tb=short

# Run tests with verbose output
test-verbose:
    @pixi run pytest tests/ -v -s

# Run tests with sidecar coverage pattern
test-sidecar-coverage:
    @docker-compose -f docker-compose.yml -f docker-compose.coverage.yml up -d
    @pixi run pytest tests/ -v
    @docker-compose down

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

# Start all services
up: network-create volumes-create
    @docker-compose up -d

# Stop all services
down:
    @docker-compose down

# Rebuild specific service
rebuild service:
    @docker-compose -f {{service}}/docker-compose.yml build --no-cache
    @docker-compose up -d {{service}}

# View service logs
logs:
    @docker-compose logs -f

# Project-specific commands

# Generate JWT secret
generate-jwt-secret:
    @python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate GitHub OAuth token
generate-github-token:
    @pixi run python scripts/generate_oauth_token.py

# OAuth-specific testing
test-oauth-flow:
    @pixi run pytest tests/test_oauth_flow.py -v -s

test-mcp-protocol:
    @pixi run pytest tests/test_mcp_protocol.py -v -s

test-claude-integration:
    @pixi run pytest tests/test_claude_integration.py -v -s

# Service-specific rebuilds
rebuild-auth:
    @docker-compose -f auth/docker-compose.yml build --no-cache
    @docker-compose up -d auth

rebuild-mcp-fetch:
    @docker-compose -f mcp-fetch/docker-compose.yml build --no-cache
    @docker-compose up -d mcp-fetch

rebuild-traefik:
    @docker-compose -f traefik/docker-compose.yml up -d traefik

# Analysis commands
analyze-oauth-logs:
    @mkdir -p reports
    @pixi run python scripts/analyze_oauth_logs.py > reports/oauth-analysis-$(date +%Y%m%d-%H%M%S).md

# Health check commands
check-health:
    @echo "Checking service health..."
    @curl -f http://localhost/health || echo "Traefik not healthy"
    @curl -f http://auth.localhost:8000/health || echo "Auth service not healthy"
    @curl -f http://mcp-fetch.localhost:3000/health || echo "MCP-fetch not healthy"

# Setup commands
setup: network-create volumes-create
    @echo "Setting up MCP OAuth Gateway..."
    @pixi install
    @echo "Setup complete! Run 'just up' to start services."