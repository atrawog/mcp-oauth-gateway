# First Setup

This guide walks you through the complete setup process for the MCP OAuth Gateway from scratch.

```{warning}
**Reference Implementation Notice**

This is a reference implementation for testing MCP protocol features. It likely contains security vulnerabilities and should not be used in production without thorough security review.
```

## Prerequisites

Before starting, ensure you have:

- **Docker** and **Docker Compose** installed
- **[pixi](https://pixi.sh)** package manager installed
- **[just](https://github.com/casey/just)** command runner installed
- A **GitHub account** for OAuth integration
- A **domain name** (or use `localhost` for local development)

## Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/atrawog/mcp-oauth-gateway.git
cd mcp-oauth-gateway

# Install dependencies
pixi install
```

## Step 2: Create GitHub OAuth App

1. Go to [GitHub OAuth Apps](https://github.com/settings/applications/new)

2. Fill in the application details:
   - **Application name**: `MCP OAuth Gateway` (or your preferred name)
   - **Homepage URL**: `https://your-domain.com` (or `http://localhost` for local dev)
   - **Authorization callback URL**: `https://auth.your-domain.com/callback` (or `http://auth.localhost/callback`)

3. Click **"Register application"**

4. Save the **Client ID** and **Client Secret** - you'll need these next

## Step 3: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

### Required Configuration

Update these values in your `.env` file:

```bash
# GitHub OAuth (from Step 2)
GITHUB_CLIENT_ID=Iv1.your_actual_client_id_here
GITHUB_CLIENT_SECRET=your_actual_client_secret_here

# Domain Configuration
BASE_DOMAIN=your-domain.com  # or 'localhost' for local development
ACME_EMAIL=admin@your-domain.com  # your email for Let's Encrypt

# Redis Security
REDIS_PASSWORD=choose_a_strong_password_here

# Access Control (optional but recommended)
ALLOWED_GITHUB_USERS=your_github_username,other_allowed_users
```

### Generate Required Secrets

```bash
# Generate JWT signing secret
just generate-jwt-secret

# Generate RSA keys for token signing
just generate-rsa-keys
```

These commands automatically update your `.env` file with:
- `GATEWAY_JWT_SECRET`
- `JWT_PRIVATE_KEY_B64`

## Step 4: Start Services

```bash
# Create required Docker networks and volumes
just network-create
just volumes-create

# Start all services
just up

# Wait for services to be ready
just ensure-services-ready
```

## Step 5: Generate OAuth Tokens

The gateway needs its own OAuth tokens to operate:

```bash
# This will open your browser for GitHub authentication
just generate-github-token
```

This interactive process:
1. Opens your browser to authenticate with GitHub
2. Registers the gateway as an OAuth client
3. Saves tokens to your `.env` file

## Step 6: Verify Installation

```bash
# Check all services are healthy
just check-health

# Run basic tests
just test

# View service logs
just logs
```

## Step 7: First API Call

### Get OAuth Server Metadata

```bash
# Test OAuth discovery endpoint (should work without auth)
curl https://auth.${BASE_DOMAIN}/.well-known/oauth-authorization-server
```

### Test MCP Service (Requires Authentication)

First, generate a client token:

```bash
# Generate MCP client access token
just mcp-client-token
```

Then test an MCP service:

```bash
# Test MCP Time service
curl -X POST https://time.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer ${MCP_CLIENT_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0"
      }
    },
    "id": 1
  }'
```

## Configuration Details

### Service URLs

With `BASE_DOMAIN=example.com`, your services will be available at:

| Service | URL |
|---------|-----|
| Auth Service | `https://auth.example.com` |
| MCP Fetch | `https://fetch.example.com/mcp` |
| MCP Memory | `https://memory.example.com/mcp` |
| MCP Time | `https://time.example.com/mcp` |
| MCP Filesystem | `https://filesystem.example.com/mcp` |
| MCP Sequential Thinking | `https://sequentialthinking.example.com/mcp` |
| MCP Everything | `https://everything.example.com/mcp` |
| MCP Fetchs | `https://fetchs.example.com/mcp` |
| MCP Tmux | `https://tmux.example.com/mcp` |
| MCP Playwright | `https://playwright.example.com/mcp` |

### Local Development

For local development with `BASE_DOMAIN=localhost`:

1. Services will be available at `http://service.localhost`
2. No HTTPS/TLS certificates needed
3. Use `http://` instead of `https://` in all URLs

### Production Deployment

For production with a real domain:

1. Ensure DNS is configured for all subdomains
2. Let's Encrypt will automatically provision certificates
3. Set `ALLOWED_GITHUB_USERS` to restrict access
4. Use strong passwords for all secrets
5. Consider using a secrets management system

## Troubleshooting

### Services Not Starting

```bash
# Check Docker status
docker-compose ps

# View detailed logs
just logs auth  # or any service name

# Check for missing environment variables
grep -E "^(GITHUB_CLIENT_ID|GITHUB_CLIENT_SECRET|GATEWAY_JWT_SECRET)=" .env
```

### Authentication Failures

```bash
# Verify GitHub OAuth credentials
curl https://api.github.com/user -H "Authorization: token ${GITHUB_PAT}"

# Check token validity
just validate-tokens

# Regenerate tokens if needed
just generate-github-token
```

### SSL/TLS Issues (Production)

```bash
# Check Let's Encrypt logs
docker-compose logs traefik | grep -i acme

# Verify DNS resolution
dig auth.${BASE_DOMAIN}
dig fetch.${BASE_DOMAIN}
```

### Health Check Failures

```bash
# Test service health directly
docker exec mcp-fetch curl -s -X POST http://localhost:3000/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'

# Check service logs for errors
just logs mcp-fetch
```

## Next Steps

Now that your gateway is running:

1. **Integrate with Claude.ai** - See {doc}`../integration/claude-ai`
2. **Explore MCP Services** - See {doc}`../services/index`
3. **Run Full Test Suite** - `just test-all`
4. **Add Custom Services** - See {doc}`../development/adding-services`

## Security Reminders

```{caution}
For production use:
- Enable `ALLOWED_GITHUB_USERS` to restrict access
- Use strong, unique passwords for all secrets
- Regularly rotate OAuth tokens
- Monitor logs for suspicious activity
- Keep services updated
```