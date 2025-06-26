# Quick Start Guide

Get the MCP OAuth Gateway up and running in 15 minutes with this step-by-step guide.

```{warning}
**Prerequisites**: You must have a public domain and the ability to configure DNS. This gateway cannot run on localhost due to OAuth and SSL requirements.
```

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Public domain** with DNS control (e.g., `example.com`)
- [ ] **Server** with public IP address
- [ ] **Ports 80 and 443** open and available
- [ ] **Docker and Docker Compose** installed
- [ ] **GitHub account** for OAuth app creation

## Step 1: Install Required Tools

### Install Docker and Docker Compose

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose-v2

# Verify installation
docker --version
docker compose version
```

### Install pixi and just

```bash
# Install pixi (Python package manager)
curl -fsSL https://pixi.sh/install.sh | bash

# Install just (command runner)
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin

# Add to PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Step 2: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/atrawog/mcp-oauth-gateway.git
cd mcp-oauth-gateway

# Install Python dependencies
pixi install

# Create required networks and volumes
just network-create
just volumes-create
```

## Step 3: Configure DNS

Configure the following DNS A records pointing to your server's IP:

```
auth.example.com         → YOUR_SERVER_IP
fetch.example.com    → YOUR_SERVER_IP
memory.example.com   → YOUR_SERVER_IP
# Add more as needed for each service
```

```{tip}
You can use a wildcard record if your DNS provider supports it:
`*.example.com → YOUR_SERVER_IP`
```

## Step 4: Create GitHub OAuth App

1. Go to [GitHub Settings > Developer settings > OAuth Apps](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in the form:
   - **Application name**: `MCP OAuth Gateway`
   - **Homepage URL**: `https://example.com` (your domain)
   - **Authorization callback URL**: `https://auth.example.com/callback`
4. Click "Register application"
5. Save the **Client ID** and **Client Secret**

## Step 5: Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Generate all required secrets at once
just generate-all-secrets

# Or generate individually:
# just generate-jwt-secret      # Sets GATEWAY_JWT_SECRET
# just generate-rsa-keys        # Sets JWT_PRIVATE_KEY_B64
# just generate-redis-password  # Sets REDIS_PASSWORD

# Edit configuration
nano .env
```

Update these required values in `.env`:

⚠️ **IMPORTANT**: You only need 5 tokens to run the gateway!

```bash
# Domain configuration (REQUIRED)
BASE_DOMAIN=example.com  # Your actual domain
ACME_EMAIL=admin@example.com  # Your email for Let's Encrypt

# GitHub OAuth (REQUIRED)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Security (REQUIRED)
REDIS_PASSWORD=your_secure_redis_password

# Access Control (REQUIRED - choose one)
ALLOWED_GITHUB_USERS=username1,username2  # Specific users
# OR
ALLOWED_GITHUB_USERS=*  # Any GitHub user

# Service Selection (Optional - all default to true)
MCP_FETCH_ENABLED=true
MCP_MEMORY_ENABLED=true
MCP_FILESYSTEM_ENABLED=true
# Disable resource-intensive services if needed
MCP_PLAYWRIGHT_ENABLED=false
```

## Step 6: Start the Gateway

```bash
# Create Docker network
just network-create

# Start all services
just up

# View logs to monitor startup
just logs -f
```

Wait for all services to start. You should see:
- Traefik obtaining SSL certificates
- Auth service ready
- MCP services healthy

## Step 7: Verify Installation

### Check Service Health

```bash
# Run health checks
just check-health

# Expected output:
# ✅ Traefik is healthy
# ✅ Auth service is healthy
# ✅ Redis is healthy
# ✅ mcp-fetch is healthy
# ...
```

### Test OAuth Discovery

```bash
# Should return OAuth metadata
curl https://auth.example.com/.well-known/oauth-authorization-server
```

### Generate Test Token

```bash
# Generate a test token
just mcp-client-token

# This will:
# 1. Open browser for GitHub auth
# 2. Complete OAuth flow
# 3. Save token to .env
```

## Step 8: Test MCP Service

```bash
# Test MCP fetch service
curl -X POST https://everything.example.com/mcp \
  -H "Authorization: Bearer $MCP_CLIENT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {},
      "clientInfo": {
        "name": "test",
        "version": "1.0"
      }
    },
    "id": 1
  }'
```

## Common Issues

### SSL Certificate Issues

If Let's Encrypt fails:
```bash
# Check Traefik logs
just logs traefik | grep -i acme

# Ensure ports 80/443 are open
sudo netstat -tlnp | grep -E ':80|:443'
```

### Services Not Starting

```bash
# Check individual service logs
just logs auth
just logs mcp-fetch

# Rebuild and restart specific service
just rebuild auth
```

### Authentication Failures

```bash
# Check OAuth tokens
just oauth-list-tokens

# Check Redis connectivity
just exec redis redis-cli -a $REDIS_PASSWORD ping
```

## Next Steps

Congratulations! Your MCP OAuth Gateway is now running. Here's what to do next:

1. **Test with Claude.ai**: Connect Claude to your MCP services
2. **Configure Services**: Enable/disable services as needed
3. **Monitor Logs**: Use `just logs` to monitor activity
4. **Backup Configuration**: Save your `.env` file securely

### Useful Commands

```bash
# Service management
just up          # Start all services
just down        # Stop all services
just rebuild     # Rebuild all services
just logs        # View logs

# Token management
just mcp-client-token      # Generate client token
just oauth-show-all        # View OAuth data
just oauth-list-tokens     # List active tokens

# Testing
just test                  # Run test suite
just check-health          # Check service health
```

## Security Reminders

```{warning}
1. **Backup your `.env` file** - Contains secrets and configuration
2. **Never commit `.env`** to version control
3. **Use strong passwords** for Redis
4. **Regularly update** the gateway and dependencies
5. **Monitor logs** for suspicious activity
```

## Getting Help

- Check the [troubleshooting guide](monitoring.md)
- Review [detailed configuration](configuration.md)
- See [deployment best practices](../deployment/production.md)
- Open an issue on GitHub for bugs
