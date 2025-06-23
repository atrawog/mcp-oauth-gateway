# Frequently Asked Questions (FAQ)

Common questions and answers about the MCP OAuth Gateway.

## General Questions

### What is the MCP OAuth Gateway?

The MCP OAuth Gateway is a secure authentication and authorization system for Model Context Protocol (MCP) servers. It implements OAuth 2.1 with RFC 7591/7592 compliance to provide secure access to MCP services through GitHub authentication.

**Key Features**:
- OAuth 2.1 + PKCE authentication
- Dynamic client registration (RFC 7591)
- Client management (RFC 7592)
- MCP Protocol 2025-06-18 support
- GitHub OAuth integration
- Docker-based architecture

### Why use OAuth for MCP servers?

OAuth provides standardized, secure authentication that:
- Eliminates the need for API keys or hardcoded credentials
- Supports automatic token refresh
- Provides fine-grained access control
- Integrates with existing identity providers (GitHub)
- Follows industry security standards

### What's the "Holy Trinity" architecture?

The **Holy Trinity** refers to the three-layer separation:

1. **Traefik**: Routes requests and enforces authentication
2. **Auth Service**: Handles OAuth flows and token validation  
3. **MCP Services**: Run MCP servers with no auth knowledge

This separation ensures security, maintainability, and scalability.

## Setup and Configuration

### How do I get started?

```bash
# 1. Clone and setup
git clone <repository>
cd mcp-oauth-gateway
just setup

# 2. Configure environment
cp .env.example .env
# Edit .env with your domain and GitHub OAuth app details

# 3. Generate secrets
just generate-jwt-secret
just generate-github-token

# 4. Start services
just up-fresh

# 5. Test
just test
```

### What do I need to configure GitHub OAuth?

1. **Create GitHub OAuth App**:
   - Go to GitHub Settings → Developer settings → OAuth Apps
   - Create new OAuth App
   - Homepage URL: `https://your-domain.com`
   - Authorization callback URL: `https://auth.your-domain.com/callback`

2. **Environment Variables**:
   ```bash
   GITHUB_CLIENT_ID=your-github-client-id
   GITHUB_CLIENT_SECRET=your-github-client-secret
   ALLOWED_GITHUB_USERS=your-username,other-user
   ```

### Can I use a different domain provider?

Yes! The system works with any domain provider. You need:
- DNS control to create A records
- Domain pointing to your server's IP
- Let's Encrypt will handle SSL certificates automatically

### How do I use localhost for development?

For local development:
```bash
BASE_DOMAIN=localhost
```

Note: Some OAuth features may be limited with localhost. Use a real domain with ngrok or similar for full testing.

## Authentication and Security

### How does the OAuth flow work?

1. **Client Registration**: MCP client registers with `/register` endpoint
2. **User Authorization**: User authenticates via GitHub OAuth
3. **Token Exchange**: Authorization code exchanged for access token
4. **API Access**: Bearer token used for MCP endpoint access

See the [Integration Guide](../integration/index.md) for detailed flow diagrams.

### What's the difference between client auth and user auth?

**Two separate realms**:

- **Client Authentication** (RFC 7591/7592): Authenticates MCP clients to access the gateway
- **User Authentication** (OAuth 2.0): Authenticates human users via GitHub

Never mix these! Each has separate tokens and purposes.

### How long do tokens last?

- **Access Tokens**: 30 minutes
- **Refresh Tokens**: 1 year  
- **Authorization Codes**: 10 minutes
- **Client Registrations**: 90 days (configurable, can be eternal)

### How do I revoke access?

```bash
# Revoke specific client
just oauth-delete-registration <client_id>

# Revoke all tokens for cleanup
just oauth-delete-all-tokens

# Remove user from allowed list
# Edit ALLOWED_GITHUB_USERS in .env
```

### How can I allow any GitHub user to access my gateway?

You can configure the gateway to accept any authenticated GitHub user by setting the `ALLOWED_GITHUB_USERS` environment variable to `*`:

```bash
# In your .env file
ALLOWED_GITHUB_USERS=*
```

This wildcard configuration means:
- Any user with a valid GitHub account can authenticate
- They still need to complete the full OAuth flow
- All security measures remain in place
- Only authentication is allowed - authorization still applies

**Security Note**: Only use the wildcard if you intentionally want to allow any GitHub user. For production deployments, it's recommended to explicitly list allowed users.

### Is the system secure?

Yes! The system implements:
- **OAuth 2.1** with PKCE for secure flows
- **JWT tokens** with RS256 signing
- **HTTPS everywhere** with Let's Encrypt
- **Zero trust** architecture
- **Input validation** on all endpoints
- **Rate limiting** and monitoring

## MCP Protocol

### Which MCP protocol version is supported?

The gateway supports **MCP Protocol 2025-06-18**, the latest version with streamable HTTP transport.

### Can I use stdio MCP servers?

Yes! The system uses `mcp-streamablehttp-proxy` to wrap stdio MCP servers and expose them as HTTP endpoints. This allows official MCP servers to work with HTTP-based authentication.

### How do I add a new MCP service?

1. **Create service directory**:
   ```bash
   mkdir mcp-newservice
   cd mcp-newservice
   ```

2. **Create Dockerfile**:
   ```dockerfile
   FROM python:3.12-alpine
   RUN pip install mcp-server-newservice
   CMD mcp-streamablehttp-proxy python -m mcp_server_newservice
   ```

3. **Create docker-compose.yml** with Traefik labels

4. **Add to main docker-compose.yml**

5. **Test**: `just rebuild mcp-newservice`

### What MCP tools are available?

Current services provide:
- **mcp-fetch**: HTTP requests and web scraping
- **mcp-memory**: Persistent knowledge graph storage
- **mcp-time**: Time and timezone operations

See [Services Documentation](../services/index.md) for complete tool lists.

## Development and Testing

### Why "no mocking" in tests?

The **Sacred Commandment** of "No Mocks" ensures:
- Tests run against real Docker services
- Integration issues are caught early
- Production behavior is accurately tested
- No false confidence from fake responses

### How do I run tests?

```bash
# Standard test suite
just test

# Specific test categories
just test-oauth-flow
just test-mcp-protocol
just test-claude-integration

# With coverage
just test-sidecar-coverage
```

### What if tests fail?

```bash
# Diagnose issues
just diagnose-tests

# Check service health
just check-health

# Clean up test data
just test-cleanup

# View detailed output
just test-verbose
```

### How do I debug issues?

```bash
# View logs
just logs-follow

# Check specific service
docker logs mcp-oauth-gateway-auth-1

# Health checks
just check-health

# OAuth data analysis
just oauth-show-all
```

## Deployment and Operations

### Can I deploy to production?

Yes! The system is designed for production use:
- Automatic SSL certificates
- Health checks and monitoring
- Backup and restore capabilities
- Security best practices

### How do I backup data?

```bash
# Backup OAuth registrations and tokens
just oauth-backup

# List available backups
just oauth-backup-list

# Restore from backup
just oauth-restore
```

### How do I monitor the system?

```bash
# Health monitoring
just check-health

# SSL certificate status
just check-ssl

# OAuth statistics
just oauth-stats

# Log analysis
just analyze-oauth-logs
```

### How do I scale the system?

The architecture supports scaling:
- **Horizontal scaling**: Multiple MCP service instances
- **Load balancing**: Traefik handles distribution
- **Stateless services**: Redis provides shared state
- **Independent services**: Scale services individually

### What about high availability?

For HA deployment:
- Use Redis cluster for state storage
- Deploy multiple auth service instances
- Use external load balancer with health checks
- Monitor and alert on service failures

## Claude.ai Integration

### How do I connect Claude.ai?

```bash
# Generate access tokens
just generate-github-token

# Create MCP configuration
just create-mcp-config

# Add to Claude Code
just mcp-add
```

Or use the unified command:
```bash
just setup-claude-code
```

### What's the MCP configuration format?

```json
{
  "mcpServers": {
    "mcp-fetch": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--url", "https://mcp-fetch.your-domain.com/mcp",
        "--oauth2"
      ],
      "env": {
        "MCP_PROTOCOL_VERSION": "2025-06-18"
      }
    }
  }
}
```

### Can I use custom MCP clients?

Yes! Any MCP client can connect by:
1. Implementing OAuth 2.1 flow
2. Using the discovery endpoint: `/.well-known/oauth-authorization-server`
3. Following MCP Protocol 2025-06-18

See [Integration Guide](../integration/index.md) for implementation details.

## Troubleshooting

### Services won't start - what should I check?

```bash
# 1. Check environment variables
grep -E "GITHUB|GATEWAY|BASE_DOMAIN" .env

# 2. Generate missing secrets
just generate-jwt-secret

# 3. Check Docker resources
docker system df
docker system prune

# 4. Restart with fresh build
just up-fresh
```

### OAuth flow fails - how to fix?

```bash
# 1. Check GitHub OAuth app configuration
# Ensure callback URL is: https://auth.your-domain.com/callback

# 2. Verify tokens
just check-token-expiry

# 3. Clean up test data
just test-cleanup

# 4. Regenerate tokens
just generate-github-token
```

### SSL certificates not working?

```bash
# 1. Check DNS resolution
nslookup auth.your-domain.com

# 2. Verify domain points to server
curl -I http://auth.your-domain.com

# 3. Check ACME challenge
curl http://auth.your-domain.com/.well-known/acme-challenge/test

# 4. Force certificate renewal
docker volume rm traefik-certificates
just up-fresh
```

### MCP clients can't connect?

```bash
# 1. Test MCP endpoint
curl -X POST https://mcp-fetch.your-domain.com/mcp \
  -H "Authorization: Bearer $GATEWAY_OAUTH_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize"}'

# 2. Check service health
curl https://mcp-fetch.your-domain.com/health

# 3. Verify OAuth discovery
curl https://mcp-fetch.your-domain.com/.well-known/oauth-authorization-server
```

## Advanced Topics

### Can I customize the OAuth flows?

The system implements standard OAuth 2.1, but you can:
- Modify client registration metadata validation
- Add custom scopes
- Implement additional grant types
- Customize token claims

### How do I add custom authentication providers?

Currently supports GitHub OAuth, but the architecture allows:
- Additional OAuth providers (Google, Microsoft, etc.)
- SAML integration
- Custom authentication backends
- Multi-provider support

### Can I run without Docker?

While designed for Docker, you can run natively:
- Install Python dependencies via pixi
- Run services manually
- Configure networking manually
- Handle SSL certificates separately

**Not recommended** - Docker provides isolation, networking, and deployment benefits.

### How do I contribute?

1. **Fork the repository**
2. **Follow development guidelines** in [Development Guide](../development/index.md)
3. **Run tests**: `just test`
4. **Submit pull request**

Key requirements:
- No mocking in tests
- Follow Sacred Commandments
- Test against real services
- Document changes

## Getting Help

### Where can I get more help?

- **Documentation**: Complete docs in this Jupyter Book
- **Command Reference**: `just --list` and [Command Reference](command-reference.md)
- **Troubleshooting**: [Troubleshooting Guide](troubleshooting-guide.md)
- **Issues**: Create GitHub issues with diagnostic information

### How do I report bugs?

Include this information:
```bash
# System info
docker version
just --version

# Service health
just check-health

# Recent logs
just logs --tail=50

# Configuration (redacted)
env | grep -E "(BASE_DOMAIN|MCP_)" | sed 's/=.*/=***/'
```

### What about feature requests?

Feature requests are welcome! Consider:
- Use cases and benefits
- Compatibility with existing architecture
- Security implications
- Implementation complexity

The system is designed to be extensible while maintaining security and simplicity.

[Frequently Asked Questions - Common questions and comprehensive answers]