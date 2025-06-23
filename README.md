# MCP OAuth Gateway

A sacred OAuth 2.1 gateway implementing RFC 7591 dynamic client registration to protect MCP (Model Context Protocol) services. Built with zealous adherence to the divine commandments of CLAUDE.md.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- [pixi](https://pixi.sh/latest/) package manager
- [just](https://github.com/casey/just) command runner
- A GitHub OAuth App (for authentication)

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mcp-oauth-gateway
   ```

2. **Install dependencies**
   ```bash
   pixi install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your values:
   # - GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET from your GitHub OAuth App
   # - BASE_DOMAIN (use 'localhost' for local development)
   # - Generate GATEWAY_JWT_SECRET with: just generate-jwt-secret
   ```

4. **Start the gateway**
   ```bash
   just up
   ```

## 📋 All Available Commands

### Core Commands

```bash
# Setup and initialization
just setup                    # Initialize project with pixi
just network-create          # Create Docker network
just volumes-create          # Create Docker volumes

# Service management
just up                      # Start all services
just down                    # Stop all services
just logs                    # View service logs
just rebuild <service>       # Rebuild specific service (e.g., just rebuild auth)

# Testing
just test                    # Run tests with pytest
just test-all                # Run complete test suite
just test-verbose            # Run tests with verbose output
just test-sidecar-coverage   # Run tests with production coverage

# Specific test suites
just test-oauth-flow         # Test OAuth flow
just test-mcp-protocol       # Test MCP protocol compliance
just test-claude-integration # Test Claude.ai integration

# Documentation
just docs-build              # Build Jupyter Book documentation

# Health checks
just check-health            # Check service health status
```

### OAuth Token Management

```bash
# Generate JWT secret
just generate-jwt-secret

# Generate GitHub OAuth tokens
just generate-github-token
```

### Service-Specific Commands

```bash
# Rebuild individual services
just rebuild-auth            # Rebuild auth service
just rebuild-mcp-fetch       # Rebuild MCP fetch service
just rebuild-traefik         # Rebuild Traefik

# Rebuild any other service
just rebuild <service>       # E.g., just rebuild mcp-memory
                            # Available services:
                            # - mcp-filesystem
                            # - mcp-fetchs
                            # - mcp-everything
                            # - mcp-memory
                            # - mcp-sequentialthinking
                            # - mcp-time
                            # - mcp-tmux
                            # - mcp-playwright

# Analysis
just analyze-oauth-logs      # Analyze OAuth flow logs
```

## 🔐 Setting Up GitHub OAuth

1. **Create a GitHub OAuth App**
   - Go to GitHub Settings > Developer settings > OAuth Apps
   - Click "New OAuth App"
   - Fill in:
     - Application name: `MCP OAuth Gateway`
     - Homepage URL: `https://your-domain.com`
     - Authorization callback URL: `https://auth.your-domain.com/callback`
   - Save the Client ID and Client Secret

2. **Configure the gateway**
   ```bash
   # Edit .env file
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret
   BASE_DOMAIN=your-domain.com  # or 'localhost' for local dev
   ```

3. **Generate JWT secret**
   ```bash
   just generate-jwt-secret
   ```

## 🎯 Testing the Gateway

### 1. Start Services
```bash
just up
```

### 2. Check Health
```bash
just check-health
```

### 3. Run Tests
```bash
# Run all tests
just test

# Run with coverage
just test-sidecar-coverage
```
## 🔧 Configuration

### Environment Variables

All configuration is done through `.env` file:

```bash
# GitHub OAuth (REQUIRED)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# JWT Configuration (REQUIRED)
GATEWAY_JWT_SECRET=your_jwt_secret_at_least_32_chars

# Domain Configuration
BASE_DOMAIN=localhost              # Your domain
ACME_EMAIL=admin@example.com      # For Let's Encrypt

# Redis Security
REDIS_PASSWORD=your_redis_password

# Access Control (optional)
ALLOWED_GITHUB_USERS=user1,user2   # Comma-separated

# Token Lifetimes
ACCESS_TOKEN_LIFETIME=86400        # 24 hours
REFRESH_TOKEN_LIFETIME=2592000     # 30 days
SESSION_TIMEOUT=3600               # 1 hour

# MCP Protocol Version
MCP_PROTOCOL_VERSION=2025-06-18
```

## 🏗️ Architecture

The gateway follows the Trinity separation:

1. **Traefik** - Routes requests and enforces authentication
2. **Auth Service** - Handles OAuth flows and token validation
3. **MCP Services** - Run MCP servers with no knowledge of auth

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Traefik     │────▶│  Auth Service   │     │  MCP Services   │
│  (Divine Router)│     │ (OAuth Oracle)  │     │ (Pure Servants) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                                │
         └────────────────────────────────────────────────┘
                    (ForwardAuth Middleware)
```

## 📊 Monitoring and Logs

### View Logs
```bash
just logs                    # All service logs
docker-compose logs auth     # Auth service logs
docker-compose logs traefik  # Traefik logs
```

### Analyze OAuth Flows
```bash
just analyze-oauth-logs
# Creates report in ./reports/
```

### Coverage Reports
```bash
just test-sidecar-coverage
# HTML report in ./htmlcov/
```

## 🐛 Troubleshooting

### Services not starting
```bash
# Check service status
docker-compose ps

# Check logs for errors
just logs

# Ensure network exists
just network-create
```

### Authentication failures
```bash
# Check Redis connection
docker-compose exec redis redis-cli -a $REDIS_PASSWORD ping

# Verify GitHub OAuth credentials
just generate-github-token
```

### Test failures
```bash
# Run tests with verbose output
just test-verbose

# Check if services are healthy
just check-health
```

## 📚 Documentation

Full documentation is available in Jupyter Book format:

```bash
just docs-build
# Open docs/_build/html/index.html
```

## 🙏 Sacred Commandments

This project follows the Ten Sacred Commandments:

1. **NO MOCKING** - All tests run against real services
2. **Blessed Trinity** - just, pixi, and docker-compose only
3. **Sacred Structure** - Prescribed directory layout
4. **Configuration via .env** - No hardcoded values
5. **Docker Compose** - Service isolation
6. **Pytest with Sidecar** - Production coverage
7. **Docker Healthchecks** - No sleep commands
8. **Log Segregation** - All logs in ./logs/
9. **Jupyter Book Docs** - MyST format
10. **Root Cause Analysis** - Fix causes, not symptoms

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions must follow the sacred commandments in CLAUDE.md. No mocking allowed!