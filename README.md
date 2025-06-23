# MCP OAuth Gateway

An OAuth 2.1 Authorization Server that adds authentication to any MCP (Model Context Protocol) server without code modification. The gateway acts as an OAuth Authorization Server while using GitHub as the Identity Provider (IdP) for user authentication.

## ⚠️ Important Notice

**This is a reference implementation and test platform for the MCP protocol.** 

- **Primary Purpose**: Reference implementation for MCP protocol development and testing
- **Experimental Nature**: Used as a test platform for future MCP protocol iterations
- **Security Disclaimer**: While this implementation strives for security best practices, this implementation likely contains bugs and security vulnerabilities
- **Production Warning**: NOT recommended for production use without thorough security review
- **Use at Your Own Risk**: This is experimental software intended for development and testing

## 🏗️ Architecture

### Overview

The MCP OAuth Gateway implements a complete OAuth 2.1 Authorization Server that protects MCP services without requiring any code modifications to the MCP servers themselves.

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│          Traefik (The Divine Router)                        │
│  • Routes OAuth paths → Auth Service                        │
│  • Routes MCP paths → MCP Services (after auth)             │
│  • Enforces authentication via ForwardAuth                  │
│  • Provides HTTPS with Let's Encrypt certificates           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│      Auth Service (OAuth Authorization Server)              │
│  • Handles all OAuth endpoints (/register, /token, etc.)    │
│  • Validates tokens via /verify for ForwardAuth             │
│  • Integrates with GitHub OAuth for user authentication     │
│  • Uses mcp-oauth-dynamicclient for RFC compliance          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│    MCP Services (Pure Protocol Implementations)             │
│  • Run official MCP servers from modelcontextprotocol       │
│  • Wrapped with mcp-streamablehttp-proxy when needed        │
│  • Know nothing about OAuth - pure protocol innocence       │
│  • Each service isolated in its own container               │
└─────────────────────────────────────────────────────────────┘
```

### OAuth Roles

1. **MCP OAuth Gateway** - OAuth Authorization Server
   - Implements OAuth 2.1 with RFC 7591 dynamic client registration
   - Issues and validates access tokens for MCP clients
   - Manages client registrations and credentials

2. **GitHub OAuth** - Identity Provider (IdP)
   - Authenticates end users through GitHub's OAuth flow
   - Provides user identity and profile information
   - No direct interaction with MCP clients

3. **MCP Servers** - Protected resources
   - Run unmodified official MCP servers
   - Protected by OAuth without any code changes
   - Support various protocol versions based on implementation

### Available MCP Services

| Service | Description | Protocol Version |
|---------|-------------|------------------|
| mcp-fetch | Web content fetching | 2025-03-26 |
| mcp-fetchs | Native Python fetch implementation | 2025-06-18 |
| mcp-filesystem | File system access (sandboxed) | 2025-03-26 |
| mcp-memory | Persistent memory/knowledge graph | 2024-11-05 |
| mcp-sequentialthinking | Structured problem solving | 2024-11-05 |
| mcp-time | Time and timezone operations | 2025-03-26 |
| mcp-tmux | Terminal multiplexer integration | 2025-06-18 |
| mcp-playwright | Browser automation | 2025-06-18 |
| mcp-everything | Test server with all features | 2025-06-18 |

### Extensions Beyond MCP Protocol

- **RFC 7592 Client Management**: Complete client lifecycle management including read, update, and delete operations (NOT part of MCP 2025-06-18 specification)
- **GitHub Integration**: User authentication through GitHub OAuth
- **Dynamic Configuration**: All services configurable through environment variables

## 📋 Requirements

### System Requirements

- **Docker** and **Docker Compose** (required for all services)
- **[pixi](https://pixi.sh/latest/)** - Modern Python package manager
- **[just](https://github.com/casey/just)** - Command runner (all commands go through just)
- **Python 3.11+** (managed automatically by pixi)

### Infrastructure Requirements

- **Public IP address and properly configured DNS** (MANDATORY - no exceptions!)
  - All subdomains must resolve to your server:
    - `auth.your-domain.com` - OAuth authorization server
    - `mcp-*.your-domain.com` - Each MCP service subdomain
  - Ports 80 and 443 must be accessible from the internet
  - Let's Encrypt certificate provisioning requires public access
  - **NO LOCALHOST DEPLOYMENTS** - The gateway requires real domains

### GitHub OAuth App

You'll need to create a GitHub OAuth App for user authentication:
1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Click "New OAuth App"
3. Configure with your domain (see setup instructions)

## 🚀 Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/atrawog/mcp-oauth-gateway.git
cd mcp-oauth-gateway

# Install dependencies with pixi
pixi install

# Run initial setup
just setup
```

### 2. Configure Environment

The gateway uses a `.env` file for all configuration. Follow these steps to set it up:

```bash
# 1. Copy the example configuration
cp .env.example .env

# 2. Generate required secrets
just generate-jwt-secret      # Generates JWT secret key
just generate-rsa-keys       # Generates RSA keys for RS256 JWT signing

# 3. Edit .env with your configuration
nano .env
```

#### Essential Configuration Steps

1. **Domain Setup** (REQUIRED - Must be real domains!)
   ```bash
   BASE_DOMAIN=your-domain.com              # Your actual domain
   ACME_EMAIL=admin@your-domain.com        # Email for Let's Encrypt
   ```

2. **GitHub OAuth App** (REQUIRED)
   ```bash
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret
   ```

3. **Security** (REQUIRED)
   ```bash
   # These are auto-generated by the commands above:
   GATEWAY_JWT_SECRET=<auto-generated>
   JWT_PRIVATE_KEY_B64=<auto-generated>
   JWT_ALGORITHM=RS256
   
   # Set a Redis password:
   REDIS_PASSWORD=your_secure_redis_password
   ```

4. **Access Control** (RECOMMENDED)
   ```bash
   # Option 1: Whitelist specific users
   ALLOWED_GITHUB_USERS=user1,user2,user3
   
   # Option 2: Allow any authenticated GitHub user
   ALLOWED_GITHUB_USERS=*
   ```

5. **Service Selection** (OPTIONAL)
   ```bash
   # Enable/disable individual MCP services
   MCP_FETCH_ENABLED=true
   MCP_FETCHS_ENABLED=true
   MCP_FILESYSTEM_ENABLED=true
   MCP_MEMORY_ENABLED=true
   MCP_PLAYWRIGHT_ENABLED=false  # Disable if not needed
   MCP_SEQUENTIALTHINKING_ENABLED=true
   MCP_TIME_ENABLED=true
   MCP_TMUX_ENABLED=true
   MCP_EVERYTHING_ENABLED=true
   ```

### 3. Create GitHub OAuth App

1. Go to [GitHub OAuth Apps](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in:
   - **Application name**: `MCP OAuth Gateway`
   - **Homepage URL**: `https://your-domain.com`
   - **Authorization callback URL**: `https://auth.your-domain.com/callback`
4. Save the Client ID and Client Secret to your `.env` file

### 4. Start the Gateway

```bash
# Start all services
just up

# Check service health
just check-health
```

## 🔧 Configuration

All configuration is managed through the `.env` file. The gateway uses dynamic service selection - you can enable or disable individual MCP services based on your needs.

### Configuration Categories

#### 1. Core Settings (REQUIRED)

```bash
# Domain Configuration - MUST be publicly accessible domains!
BASE_DOMAIN=your-domain.com
ACME_EMAIL=your-email@example.com

# GitHub OAuth App Credentials
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret

# Security Keys (generated by just commands)
GATEWAY_JWT_SECRET=<generated-by-just-generate-jwt-secret>
JWT_PRIVATE_KEY_B64=<generated-by-just-generate-rsa-keys>
JWT_ALGORITHM=RS256

# Redis Security
REDIS_PASSWORD=your_secure_redis_password
```

#### 2. Access Control

```bash
# User Whitelist Options:
ALLOWED_GITHUB_USERS=user1,user2,user3  # Specific users only
# OR
ALLOWED_GITHUB_USERS=*                  # Any GitHub user
```

#### 3. Token Configuration

```bash
# Token Lifetimes (in seconds)
CLIENT_LIFETIME=7776000        # Client registration: 90 days (0 = eternal)
ACCESS_TOKEN_LIFETIME=86400    # Access tokens: 24 hours
REFRESH_TOKEN_LIFETIME=2592000 # Refresh tokens: 30 days
SESSION_TIMEOUT=3600           # Session timeout: 1 hour
```

#### 4. MCP Service Management

The gateway allows you to enable/disable individual MCP services. All services default to `true` (enabled) if not specified.

```bash
# Core MCP Services
MCP_FETCH_ENABLED=true              # Web content fetching (stdio proxy)
MCP_FETCHS_ENABLED=true             # Native Python fetch implementation
MCP_FILESYSTEM_ENABLED=true         # File system access (sandboxed)
MCP_MEMORY_ENABLED=true             # Persistent memory/knowledge graph
MCP_TIME_ENABLED=true               # Time and timezone operations

# Advanced MCP Services
MCP_SEQUENTIALTHINKING_ENABLED=true # Structured problem solving
MCP_TMUX_ENABLED=true               # Terminal multiplexer integration
MCP_PLAYWRIGHT_ENABLED=false        # Browser automation (resource intensive)
MCP_EVERYTHING_ENABLED=true         # Test server with all features
```

#### 5. Protocol Configuration

```bash
# MCP Protocol Version (used by services that support it)
MCP_PROTOCOL_VERSION=2025-06-18

# Note: Some services only support specific versions:
# - mcp-memory: 2024-11-05
# - mcp-sequentialthinking: 2024-11-05
# - mcp-fetch, mcp-filesystem, mcp-time: 2025-03-26
# - Others: 2025-06-18
```

#### 6. Test Configuration

```bash
# Enable/disable tests for specific services
MCP_FETCH_TESTS_ENABLED=false
MCP_FETCHS_TESTS_ENABLED=false
MCP_FILESYSTEM_TESTS_ENABLED=false
MCP_MEMORY_TESTS_ENABLED=false
MCP_PLAYWRIGHT_TESTS_ENABLED=false
MCP_SEQUENTIALTHINKING_TESTS_ENABLED=false
MCP_TIME_TESTS_ENABLED=false
MCP_TMUX_TESTS_ENABLED=false
MCP_EVERYTHING_TESTS_ENABLED=false

# Test parameters
TEST_HTTP_TIMEOUT=30.0
TEST_MAX_RETRIES=3
TEST_RETRY_DELAY=1.0
```

### Managing Services

#### Check Which Services Are Enabled

When you run `just up`, the system will show which services are being started:

```bash
just up
# Output:
# Generated docker-compose.includes.yml
# ✅ mcp-fetch is ENABLED
# ✅ mcp-fetchs is ENABLED
# ❌ mcp-playwright is DISABLED
# ... etc
```

#### Disable Unnecessary Services

To improve performance and reduce resource usage, disable services you don't need:

```bash
# Example: Minimal setup with just fetch and filesystem
MCP_FETCH_ENABLED=true
MCP_FETCHS_ENABLED=false
MCP_FILESYSTEM_ENABLED=true
MCP_MEMORY_ENABLED=false
MCP_PLAYWRIGHT_ENABLED=false
MCP_SEQUENTIALTHINKING_ENABLED=false
MCP_TIME_ENABLED=false
MCP_TMUX_ENABLED=false
MCP_EVERYTHING_ENABLED=false
```

#### Apply Configuration Changes

After modifying `.env`:

```bash
# Regenerate service configuration
just down
just up
```

### Environment File Best Practices

1. **Never commit `.env`** - It contains secrets!
2. **Use strong passwords** - Especially for REDIS_PASSWORD
3. **Backup your `.env`** - Keep a secure copy of your configuration
4. **Validate settings** - Use `just check-health` after changes
5. **Start minimal** - Enable only services you need

## 📖 Usage

### Service Management

```bash
# Start all services
just up

# Stop all services  
just down

# Rebuild specific service
just rebuild auth
just rebuild mcp-fetch
just rebuild mcp-memory

# View logs
just logs              # All services
just logs auth         # Specific service
just logs -f traefik   # Follow mode
```

### OAuth Token Management

```bash
# Generate gateway OAuth tokens (for testing)
just generate-github-token

# Generate MCP client token (for mcp-streamablehttp-client)
just mcp-client-token

# View OAuth registrations and tokens
just oauth-show-all
just oauth-list-registrations
just oauth-list-tokens

# Cleanup expired tokens
just oauth-purge-expired
```

### Testing

```bash
# Run all tests
just test

# Run specific test file
just test tests/test_oauth_flow.py

# Run with verbose output
just test -v

# Run with coverage analysis
just test-sidecar-coverage

# Run specific test suites
just test-oauth-flow
just test-mcp-protocol
just test-claude-integration
```

### Health Monitoring

```bash
# Check all services health
just check-health

# Quick health check
just health-quick

# Check SSL certificates
just check-ssl
```

### OAuth Data Management

```bash
# Backup OAuth data
just oauth-backup

# List backups
just oauth-backup-list

# Restore from latest backup
just oauth-restore

# View backup contents
just oauth-backup-view

# Cleanup test registrations
just test-cleanup-show  # Preview what would be deleted
just test-cleanup       # Actually delete test data
```

## 🧪 Testing the Gateway

### 1. Verify Services Are Running

```bash
just check-health
```

### 2. Test OAuth Flow

```bash
# Run OAuth flow tests
just test tests/test_oauth_flow.py -v

# Test with a real browser
# Visit: https://auth.your-domain.com/.well-known/oauth-authorization-server
```

### 3. Test MCP Integration

```bash
# Test MCP protocol compliance
just test tests/test_mcp_protocol.py -v

# Test specific MCP service
just test tests/test_mcp_fetch_integration.py -v
```

### 4. Generate Coverage Report

```bash
# Run tests with production coverage
just test-sidecar-coverage

# View HTML coverage report
open htmlcov/index.html
```

## 🔍 Monitoring and Troubleshooting

### View Logs

```bash
# All services
just logs

# Specific service with follow
just logs -f auth
just logs -f traefik

# Analyze OAuth flows
just analyze-oauth-logs
```

### Common Issues

#### Services Not Starting

```bash
# Check Docker status
docker compose ps

# Ensure network exists
just network-create

# Check for port conflicts
sudo netstat -tlnp | grep -E ':80|:443'
```

#### SSL Certificate Issues

```bash
# Check certificate status
just check-ssl

# View Traefik logs for ACME errors
just logs traefik | grep -i acme
```

#### Authentication Failures

```bash
# Verify GitHub OAuth credentials
just generate-github-token

# Check Redis connectivity
just exec redis redis-cli -a $REDIS_PASSWORD ping

# Validate tokens
just validate-tokens
```

#### MCP Service Issues

```bash
# Check specific service health
docker inspect mcp-oauth-gateway-mcp-fetch-1 --format='{{json .State.Health}}'

# Test MCP endpoint directly
curl -X POST https://everything.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer $GATEWAY_OAUTH_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
```

## 📚 Additional Information

### Documentation

Full documentation is available in Jupyter Book format:

```bash
# Build documentation
just docs-build

# Open in browser
open docs/_build/html/index.html
```

### Development Guidelines

All development must follow the sacred commandments in `CLAUDE.md`:
- **No mocking** - Test against real services only
- **Use just commands** - Never run commands directly
- **Configuration through .env** - No hardcoded values
- **Real deployments only** - No localhost testing

### Project Structure

```
mcp-oauth-gateway/
├── auth/                    # OAuth authorization server
├── mcp-*/                   # Individual MCP services
├── traefik/                 # Reverse proxy configuration
├── tests/                   # Integration tests
├── scripts/                 # Utility scripts
├── docs/                    # Jupyter Book documentation
├── docker-compose.yml       # Main compose file
├── docker-compose.*.yml     # Additional compose configs
├── justfile                 # Command definitions
├── pixi.toml               # Package management
├── .env.example            # Example configuration
└── CLAUDE.md               # Development commandments
```

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please:
1. Follow the sacred commandments in CLAUDE.md
2. Test with real services (no mocking)
3. Use `just` for all commands
4. Update documentation as needed

For questions or issues, please open a GitHub issue.