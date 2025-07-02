# Quick Install

**🚀 Deploy MCP OAuth Gateway with minimal configuration - production-ready in 5 minutes!**

This guide provides the bare minimum steps to deploy a functional MCP OAuth Gateway. Every deployment is production-grade - there is no "test" or "development" mode.

## Prerequisites

- Docker and Docker Compose installed
- A registered domain name with DNS configured
- A GitHub OAuth App (for user authentication)
- Port 80/443 available for Traefik

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-org/mcp-oauth-gateway.git
cd mcp-oauth-gateway

# Run initial setup
just setup
```

## Step 2: Configure Environment

Create your `.env` file with minimal required settings:

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` with these essential production values:

```bash
# Domain Configuration (MUST be a real domain for Let's Encrypt)
BASE_DOMAIN=your-domain.com
ACME_EMAIL=your-email@example.com

# GitHub OAuth App (create at https://github.com/settings/applications/new)
# Callback URL: https://auth.your-domain.com/callback
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Access Control (comma-separated GitHub usernames or *)
ALLOWED_GITHUB_USERS=your-github-username,other-allowed-user

# Enable minimal MCP services (add more as needed)
MCP_FETCH_ENABLED=true
MCP_FILESYSTEM_ENABLED=true
# Other MCP_*_ENABLED remain false by default
```

## Step 3: Generate Security Secrets

```bash
# Generate all required secrets automatically
just generate-all-secrets
```

This creates production-grade:
- JWT signing secret (256-bit)
- RSA key pairs (4096-bit)
- Redis password (secure random)
- Session keys

## Step 4: Deploy Production Services

```bash
# Start all services in production
just up

# Verify health status
just check-health
```

## Step 5: Verify Production Deployment

```bash
# Check service status
just status

# Verify SSL certificates
just check-ssl

# Check OAuth endpoint
curl https://auth.${BASE_DOMAIN}/.well-known/oauth-authorization-server
```

## MCP Access

Your MCP services are now available at:
- `https://mcp-fetch.your-domain.com/mcp`
- `https://mcp-filesystem.your-domain.com/mcp`

Use the `MCP_CLIENT_ACCESS_TOKEN` from your `.env` file to authenticate.

## Management

```bash
# View production logs
just logs -f

# Check OAuth statistics
just oauth-stats

# List active registrations
just oauth-list-registrations
```

## Next Steps

- To verify your deployment with the full test suite, see [Production with Tests](production-test-install.md)
- For backup procedures, see [Production Deployment](deployment/production.md)

## Production Notes

**⚡ This IS production! There is no "development mode"!**

- All services run with production configurations
- SSL certificates are real (Let's Encrypt)
- OAuth tokens are production tokens
- Data is persisted in Redis

The only difference between this and a "tested" install is whether you run the verification suite.
