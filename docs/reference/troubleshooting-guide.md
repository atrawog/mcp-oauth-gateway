# Troubleshooting Guide

Comprehensive troubleshooting guide for common issues in the MCP OAuth Gateway.

## Quick Diagnostic Commands

### Health Check Workflow
```bash
# 1. Check overall service health
just check-health

# 2. Verify SSL certificates
just check-ssl

# 3. Check OAuth token status
just check-token-expiry

# 4. View service logs
just logs

# 5. Check OAuth data integrity
just oauth-show-all
```

### Emergency Recovery
```bash
# Quick restart with fresh build
just up-fresh

# Clean up test data
just test-cleanup

# Regenerate tokens if expired
just generate-github-token
```

## Common Issues and Solutions

### 🔴 Service Startup Issues

#### Problem: Services Won't Start
**Symptoms**:
- Containers exit immediately
- Health checks fail
- `just up` command fails

**Diagnostic Steps**:
```bash
# Check service status
docker ps -a

# View startup logs
just logs

# Check individual service
docker logs mcp-oauth-gateway-auth-1
```

**Common Causes & Solutions**:

1. **Missing Environment Variables**
   ```bash
   # Check for required variables
   grep -E "GITHUB|GATEWAY|BASE_DOMAIN" .env
   
   # Generate missing JWT secret
   just generate-jwt-secret
   
   # Generate GitHub tokens
   just generate-github-token
   ```

2. **Network Issues**
   ```bash
   # Recreate network
   docker network rm public
   just network-create
   ```

3. **Volume Permission Issues**
   ```bash
   # Recreate volumes
   docker volume prune
   just volumes-create
   ```

#### Problem: Health Checks Failing
**Symptoms**:
- Services show as "unhealthy" 
- `just check-health` reports failures

**Solutions**:
```bash
# Check specific service health endpoint
curl -f https://auth.${BASE_DOMAIN}/health

# Check internal health (bypass Traefik)
docker exec mcp-oauth-gateway-auth-1 curl -f http://localhost:8000/health

# Rebuild problematic service
just rebuild auth
```

### 🔴 Authentication Issues

#### Problem: OAuth Flow Fails
**Symptoms**:
- 401 Unauthorized responses
- "Invalid client" errors
- GitHub OAuth redirects fail

**Diagnostic Steps**:
```bash
# Check OAuth client registrations
just oauth-list-registrations

# Verify GitHub OAuth configuration
curl https://auth.${BASE_DOMAIN}/.well-known/oauth-authorization-server

# Test OAuth discovery
curl https://mcp-fetch.${BASE_DOMAIN}/.well-known/oauth-authorization-server
```

**Solutions**:

1. **Invalid Client Registration**
   ```bash
   # Clean up invalid registrations
   just test-cleanup
   
   # Re-register client manually
   curl -X POST https://auth.${BASE_DOMAIN}/register \
     -H "Content-Type: application/json" \
     -d '{"redirect_uris": ["http://localhost:8080/callback"], "client_name": "Test Client"}'
   ```

2. **Expired Tokens**
   ```bash
   # Check token expiration
   just check-token-expiry
   
   # Regenerate expired tokens
   just generate-github-token
   ```

3. **GitHub OAuth Configuration**
   ```bash
   # Verify GitHub app settings
   echo "Check GitHub OAuth app configuration:"
   echo "- Homepage URL: https://${BASE_DOMAIN}"
   echo "- Callback URL: https://auth.${BASE_DOMAIN}/callback"
   ```

#### Problem: JWT Token Issues
**Symptoms**:
- "Invalid token signature" errors
- Token validation failures
- 401 responses from MCP endpoints

**Solutions**:
```bash
# Regenerate JWT secret
just generate-jwt-secret

# Regenerate RSA keys
just generate-rsa-keys

# Validate current tokens
just validate-tokens

# Check token format
echo $GATEWAY_OAUTH_ACCESS_TOKEN | cut -d. -f2 | base64 -d | jq
```

### 🔴 SSL/TLS Issues

#### Problem: SSL Certificate Errors
**Symptoms**:
- "Certificate not valid" errors
- HTTPS connections fail
- Browser security warnings

**Diagnostic Steps**:
```bash
# Check SSL status
just check-ssl

# View certificate details
openssl s_client -connect auth.${BASE_DOMAIN}:443 -servername auth.${BASE_DOMAIN}

# Check ACME certificates
docker exec traefik cat /certificates/acme.json | jq -r '.letsencrypt.Certificates[].domain'
```

**Solutions**:

1. **Let's Encrypt Issues**
   ```bash
   # Check ACME challenge
   curl http://auth.${BASE_DOMAIN}/.well-known/acme-challenge/test
   
   # Clear old certificates
   docker volume rm traefik-certificates
   just volumes-create
   just up-fresh
   ```

2. **Domain Resolution**
   ```bash
   # Test DNS resolution
   nslookup auth.${BASE_DOMAIN}
   
   # Check if domain points to your server
   curl -I http://auth.${BASE_DOMAIN}
   ```

### 🔴 MCP Protocol Issues

#### Problem: MCP Connection Failures
**Symptoms**:
- "Protocol version mismatch" errors
- MCP clients can't connect
- Invalid JSON-RPC responses

**Diagnostic Steps**:
```bash
# Test MCP endpoint directly
curl -X POST https://mcp-fetch.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer ${GATEWAY_OAUTH_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "MCP-Protocol-Version: 2025-06-18" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}'

# Check MCP service health
curl https://mcp-fetch.${BASE_DOMAIN}/health
```

**Solutions**:

1. **Protocol Version Issues**
   ```bash
   # Verify protocol version
   echo $MCP_PROTOCOL_VERSION
   
   # Update if needed
   echo "MCP_PROTOCOL_VERSION=2025-06-18" >> .env
   just rebuild mcp-fetch
   ```

2. **MCP Server Issues**
   ```bash
   # Check MCP server logs
   docker logs mcp-oauth-gateway-mcp-fetch-1
   
   # Restart MCP service
   just rebuild mcp-fetch
   ```

### 🔴 Network and Connectivity Issues

#### Problem: Service Communication Failures
**Symptoms**:
- Services can't reach each other
- Traefik routing errors
- Database connection failures

**Diagnostic Steps**:
```bash
# Check network connectivity
docker network ls
docker network inspect public

# Test inter-service communication
docker exec mcp-oauth-gateway-auth-1 curl http://redis:6379
docker exec mcp-oauth-gateway-traefik-1 curl http://auth:8000/health
```

**Solutions**:

1. **Network Issues**
   ```bash
   # Recreate network
   docker compose down
   docker network rm public
   just network-create
   just up
   ```

2. **DNS Resolution**
   ```bash
   # Check internal DNS
   docker exec mcp-oauth-gateway-auth-1 nslookup redis
   docker exec mcp-oauth-gateway-auth-1 nslookup auth
   ```

#### Problem: Redis Connection Issues
**Symptoms**:
- "Connection refused" to Redis
- OAuth data not persisting
- Session storage failures

**Solutions**:
```bash
# Check Redis status
docker exec mcp-oauth-gateway-redis-1 redis-cli ping

# View Redis logs
docker logs mcp-oauth-gateway-redis-1

# Test Redis connectivity from auth service
docker exec mcp-oauth-gateway-auth-1 redis-cli -h redis ping

# Restart Redis
just rebuild redis
```

### 🔴 Test Failures

#### Problem: Tests Failing Consistently
**Symptoms**:
- pytest failures
- OAuth flow tests fail
- Integration tests timeout

**Diagnostic Steps**:
```bash
# Run diagnostic script
just diagnose-tests

# Check service readiness
just ensure-services-ready

# Run single failing test
just test-file tests/test_oauth_flow.py
```

**Solutions**:

1. **Service Not Ready**
   ```bash
   # Wait for services
   just ensure-services-ready
   
   # Check what's not ready
   just check-health
   ```

2. **Test Data Conflicts**
   ```bash
   # Clean up test data
   just test-cleanup
   
   # View test registrations
   just test-cleanup-show
   
   # Full OAuth cleanup
   just oauth-delete-all-registrations
   ```

3. **Token Issues in Tests**
   ```bash
   # Regenerate test tokens
   just generate-github-token
   
   # Validate tokens
   just validate-tokens
   ```

#### Problem: Coverage Collection Fails
**Symptoms**:
- Coverage reports empty
- Sidecar coverage errors
- Coverage data not collected

**Solutions**:
```bash
# Debug coverage setup
just debug-coverage

# Check coverage configuration
docker exec coverage-harvester ls -la /coverage-data/

# Manual coverage run
just test-sidecar-coverage
```

## Service-Specific Troubleshooting

### Auth Service Issues

#### Logs Analysis
```bash
# View auth service logs
docker logs mcp-oauth-gateway-auth-1 --tail=100

# Follow auth logs in real-time
docker logs mcp-oauth-gateway-auth-1 -f

# Search for specific errors
docker logs mcp-oauth-gateway-auth-1 2>&1 | grep -i error
```

#### Common Auth Issues

1. **JWT Key Issues**
   ```bash
   # Check JWT key volume
   docker volume inspect auth-keys
   
   # Regenerate keys
   just generate-rsa-keys
   ```

2. **GitHub API Issues**
   ```bash
   # Test GitHub connectivity from container
   docker exec mcp-oauth-gateway-auth-1 curl -I https://api.github.com
   
   # Check GitHub rate limits
   curl -H "Authorization: token ${GITHUB_TOKEN}" https://api.github.com/rate_limit
   ```

### Traefik Issues

#### Routing Problems
```bash
# Check Traefik dashboard
open http://localhost:8080

# View Traefik logs
docker logs mcp-oauth-gateway-traefik-1

# Check routing rules
docker exec mcp-oauth-gateway-traefik-1 cat /etc/traefik/traefik.yml
```

#### Certificate Issues
```bash
# Check ACME status
docker exec traefik cat /certificates/acme.json | jq '.letsencrypt'

# Force certificate renewal
docker exec traefik rm /certificates/acme.json
just up-fresh
```

### MCP Service Issues

#### mcp-streamablehttp-proxy Problems
```bash
# Check proxy status
docker exec mcp-oauth-gateway-mcp-fetch-1 ps aux

# Test MCP server directly
docker exec mcp-oauth-gateway-mcp-fetch-1 python -m mcp_server_fetch --help

# Check proxy logs
docker logs mcp-oauth-gateway-mcp-fetch-1
```

## Performance Issues

### High Resource Usage

#### Memory Issues
```bash
# Check container memory usage
docker stats

# Check Redis memory usage
docker exec mcp-oauth-gateway-redis-1 redis-cli info memory

# Clean up old data
just oauth-purge-expired
```

#### CPU Issues
```bash
# Check container CPU usage
docker stats --no-stream

# Profile auth service
docker exec mcp-oauth-gateway-auth-1 top

# Check for high-frequency requests
just analyze-oauth-logs
```

### Slow Response Times

#### Database Performance
```bash
# Check Redis latency
docker exec mcp-oauth-gateway-redis-1 redis-cli --latency

# Monitor Redis commands
docker exec mcp-oauth-gateway-redis-1 redis-cli monitor
```

#### Network Latency
```bash
# Test internal latency
docker exec mcp-oauth-gateway-auth-1 ping redis
docker exec mcp-oauth-gateway-traefik-1 ping auth

# Test external latency
curl -w "@curl-format.txt" -o /dev/null -s https://auth.${BASE_DOMAIN}/health
```

## Recovery Procedures

### Complete System Recovery

#### Level 1: Service Restart
```bash
# Restart all services
just down
just up
```

#### Level 2: Fresh Build
```bash
# Rebuild all services
just up-fresh
```

#### Level 3: Complete Reset
```bash
# Stop everything
just down

# Clean up containers and networks
docker system prune -f

# Recreate infrastructure
just setup

# Fresh start
just up-fresh
```

### Data Recovery

#### OAuth Data Recovery
```bash
# Backup current state
just oauth-backup

# Restore from backup if needed
just oauth-restore

# Clean slate if corrupted
just oauth-delete-all-tokens
just oauth-delete-all-registrations
```

#### Configuration Recovery
```bash
# Restore from .env.example
cp .env.example .env

# Regenerate all secrets
just generate-jwt-secret
just generate-rsa-keys
just generate-github-token
```

## Monitoring and Prevention

### Proactive Monitoring

#### Health Monitoring
```bash
# Set up health check monitoring
while true; do
  just check-health || echo "Health check failed at $(date)"
  sleep 300
done
```

#### Log Monitoring
```bash
# Monitor for errors
just logs-follow | grep -i error

# Analyze patterns
just analyze-oauth-logs
```

### Preventive Maintenance

#### Regular Tasks
```bash
# Weekly: Clean up expired tokens
just oauth-purge-expired

# Daily: Check health
just check-health

# Monthly: Backup OAuth data
just oauth-backup
```

#### Security Audits
```bash
# Check token expiration
just check-token-expiry

# Review OAuth registrations
just oauth-list-registrations

# Validate SSL certificates
just check-ssl
```

## Getting Help

### Debugging Information Collection

When reporting issues, collect this information:

```bash
# System information
docker version
docker compose version
just --version

# Service status
just check-health

# Configuration (redacted)
env | grep -E "(BASE_DOMAIN|MCP_|CLIENT_)" | sed 's/=.*/=***/'

# Recent logs
just logs --tail=50

# OAuth statistics
just oauth-stats
```

### Log Files

Important log locations:
- **Container logs**: `docker logs <container-name>`
- **Application logs**: `./logs/` directory
- **Analysis reports**: `./reports/` directory

### Support Resources

- **CLAUDE.md**: Project-specific guidance
- **Docker logs**: Detailed service information
- **Health endpoints**: Real-time status
- **OAuth introspection**: Token validation

[Troubleshooting guide - comprehensive issue resolution procedures]