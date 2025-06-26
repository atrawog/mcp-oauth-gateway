# GitHub OAuth Setup

This guide walks you through setting up GitHub OAuth for the MCP OAuth Gateway.

## Prerequisites

- GitHub account
- Administrative access to create OAuth Apps
- Your gateway domain configured

## Step 1: Create GitHub OAuth App

### Navigate to GitHub Settings

1. Log in to GitHub
2. Go to Settings → Developer settings → OAuth Apps
3. Click "New OAuth App"

### Configure OAuth App

Fill in the application details:

- **Application name**: `MCP OAuth Gateway` (or your preferred name)
- **Homepage URL**: `https://gateway.yourdomain.com`
- **Authorization callback URL**: `https://auth.yourdomain.com/callback`
- **Application description**: Optional description

### Important URLs

Ensure these URLs are correct:
- Homepage URL should be your main gateway domain
- Callback URL must include the `auth` subdomain
- Both URLs must use HTTPS in production

## Step 2: Obtain Credentials

After creating the app:

1. Copy the **Client ID**
2. Click "Generate a new client secret"
3. Copy the **Client Secret** immediately (shown only once)

## Step 3: Configure Environment

Add credentials to your `.env` file:

```bash
# GitHub OAuth Configuration
GITHUB_CLIENT_ID=Iv1.a1b2c3d4e5f6g7h8
GITHUB_CLIENT_SECRET=1234567890abcdef1234567890abcdef12345678
```

## Step 4: User Access Control

### Configure Allowed Users

Specify which GitHub users can access your gateway:

```bash
# Individual users (comma-separated)
ALLOWED_GITHUB_USERS=alice,bob,charlie

# Organization members
ALLOWED_GITHUB_USERS=org:mycompany

# Teams (requires organization app)
ALLOWED_GITHUB_USERS=org:mycompany/team:developers

# Combined
ALLOWED_GITHUB_USERS=alice,bob,org:mycompany/team:admins
```

### Organization Apps

For organization-level control:

1. Go to Organization Settings → Developer settings → OAuth Apps
2. Create app with same settings
3. Enable organization access restrictions

## Step 5: Test Authentication

### Understanding the Two OAuth Flows

The gateway uses **two different GitHub OAuth flows** for different purposes:

#### 1. Browser-Based OAuth Flow (End Users)

For end users accessing MCP services through a browser:

1. Start the gateway: `just up`
2. Navigate to: `https://gateway.yourdomain.com/authorize`
3. You will be **redirected to GitHub** in your browser
4. Log in and authorize the application
5. GitHub redirects back to the gateway
6. Gateway issues JWT tokens for MCP access

#### 2. Device Flow (Gateway & CLI Tools)

For command-line authentication without browser:

```bash
# Generate GitHub PAT for the gateway itself
just generate-github-token

# This will:
# 1. Show: "Visit https://github.com/login/device"
# 2. Display a code like: "ABCD-1234"
# 3. You manually enter this code on GitHub
# 4. Gateway polls until you authorize
# 5. Stores GITHUB_PAT in .env
```

### When Each Flow is Used

| Scenario | Flow Type | Initiated By | User Action |
|----------|-----------|--------------|-------------|
| End user accessing MCP service | Browser OAuth | User clicks link/visits URL | Redirected to GitHub automatically |
| Gateway needs GitHub token | Device Flow | `just generate-github-token` | Manually enter code at github.com/login/device |
| MCP client needs token | Device Flow | `just mcp-client-token` | Manually enter code at github.com/login/device |

## Advanced Configuration

### Scopes

The gateway requests minimal scopes:
- `read:user` - Read user profile
- `user:email` - Access email (optional)

### Enterprise GitHub

For GitHub Enterprise:

```bash
# In .env
GITHUB_ENTERPRISE_URL=https://github.company.com
GITHUB_API_URL=https://github.company.com/api/v3
```

### Multiple OAuth Apps

For different environments:

```bash
# Development
GITHUB_CLIENT_ID_DEV=Iv1.dev123456789
GITHUB_CLIENT_SECRET_DEV=devsecret123...

# Production
GITHUB_CLIENT_ID_PROD=Iv1.prod987654321
GITHUB_CLIENT_SECRET_PROD=prodsecret456...
```

## Troubleshooting

### Common Issues

#### Invalid Callback URL

**Error**: "The redirect_uri MUST match the registered callback URL"

**Solution**:
- Ensure callback URL in GitHub matches exactly
- Include `https://` protocol
- Check for trailing slashes

#### Authorization Failed

**Error**: "User not in allowed list"

**Solution**:
- Check `ALLOWED_GITHUB_USERS` configuration
- Ensure username is correct (case-sensitive)
- For orgs, verify membership

#### Token Generation Failed

**Error**: "Could not exchange authorization code"

**Solution**:
- Verify client ID and secret
- Check network connectivity
- Ensure Redis is running

### Debug Mode

Enable debug logging:

```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG
```

Check auth service logs:
```bash
just logs auth
```

## Security Best Practices

1. **Rotate Secrets** - Change client secret periodically
2. **Limit Scope** - Request minimal permissions
3. **IP Allowlist** - Restrict OAuth app to specific IPs
4. **Audit Logs** - Monitor authorization events
5. **Token Expiry** - Set appropriate token lifetimes

## Webhook Configuration (Optional)

For real-time updates:

1. Go to OAuth App settings
2. Add webhook URL: `https://auth.yourdomain.com/webhook`
3. Select events:
   - User authorization revoked
   - App suspended
   - App unsuspended

## Next Steps

1. Test authentication flow
2. Configure [user permissions](../usage/token-management.md)
3. Set up [monitoring](../usage/monitoring.md)
4. Review [security best practices](../architecture/security.md)
