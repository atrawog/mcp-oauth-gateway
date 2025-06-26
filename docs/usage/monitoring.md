# Monitoring & Troubleshooting

This guide covers monitoring the MCP OAuth Gateway and troubleshooting common issues using actual available commands.

## Monitoring Overview

The gateway provides several tools for monitoring:

1. **Health Checks** - Service readiness verification
2. **Logs** - Real-time and historical logs
3. **OAuth Analysis** - Token and registration analysis
4. **SSL Monitoring** - Certificate status

## Health Monitoring

### Health Checks

```bash
# Comprehensive health check of all services
just check-health

# Quick health check
just health-quick

# Ensure all services are ready
just ensure-services-ready
```

### SSL Certificate Monitoring

```bash
# Check SSL certificates and ACME status
just check-ssl
```

## Log Monitoring

### View Logs

```bash
# View all logs
just logs

# Service-specific logs
just logs auth
just logs mcp-fetch
just logs traefik

# Follow logs in real-time
just logs -f
just logs -f auth

# Last N lines
just logs --tail=100
just logs --tail=50 traefik
```

### Log Management

```bash
# Purge all container logs (restarts services)
just logs-purge
```

### Log Analysis

```bash
# Analyze OAuth logs
just analyze-oauth-logs

# Filter logs with grep
just logs auth | grep ERROR
just logs | grep "rate limit"
```

## OAuth Monitoring

### Token and Registration Analysis

```bash
# Show all OAuth data
just oauth-show-all

# List active registrations
just oauth-list-registrations

# List active tokens
just oauth-list-tokens

# OAuth statistics
just oauth-stats

# Check for expired tokens (dry run)
just oauth-purge-expired-dry

# Actually purge expired tokens
just oauth-purge-expired
```

### Token Validation

```bash
# Validate current tokens
just validate-tokens

# Check token expiration
just check-token-expiry
```

## Troubleshooting Guide

### Service Won't Start

#### Check Service Status

```bash
# Use docker compose directly (for debugging only)
docker compose ps

# View service logs
just logs auth
just logs mcp-fetch

# Ensure dependencies are ready
just ensure-services-ready
```

#### Common Causes

1. **Missing environment variables**
   ```bash
   # Check .env file
   cat .env | grep GITHUB_CLIENT_ID
   ```

2. **Port conflicts**
   ```bash
   # Check if ports are in use
   sudo lsof -i :8000
   sudo lsof -i :3000
   ```

3. **Redis connection issues**
   ```bash
   # Check Redis logs
   just logs redis

   # Test Redis connection
   just exec redis redis-cli ping
   ```

### Authentication Issues

#### User Can't Authenticate

1. **Check allowed users**
   ```bash
   grep ALLOWED_GITHUB_USERS .env
   ```

2. **Verify OAuth flow**
   ```bash
   # Run OAuth flow tests
   just test-oauth-flow

   # Check auth logs
   just logs auth | grep "GitHub OAuth"
   ```

3. **Check JWT configuration**
   ```bash
   # Verify JWT secret exists
   grep GATEWAY_JWT_SECRET .env
   ```

#### Token Issues

1. **Expired tokens**
   ```bash
   # List and check token expiration
   just oauth-list-tokens

   # Purge expired tokens
   just oauth-purge-expired
   ```

2. **Invalid registrations**
   ```bash
   # Show test registrations
   just test-cleanup-show

   # Clean test data
   just test-cleanup
   ```

### Performance Issues

#### High Resource Usage

```bash
# Check container resource usage
docker stats

# View service logs for errors
just logs -f

# Rebuild services if needed
just rebuild auth mcp-fetch
```

#### Redis Memory Issues

```bash
# Check Redis memory usage
just exec redis redis-cli INFO memory

# List all keys (be careful in production)
just exec redis redis-cli --scan

# Purge expired OAuth data
just oauth-purge-expired
```

### SSL/Certificate Issues

```bash
# Check certificate status
just check-ssl

# View Traefik logs for ACME issues
just logs traefik | grep -i "acme"
just logs traefik | grep -i "certificate"

# Verify DNS resolution
nslookup auth.${BASE_DOMAIN}
nslookup mcp-fetch.${BASE_DOMAIN}
```

## Common Issues Reference

### Issue: 502 Bad Gateway

**Diagnosis**:
```bash
# Check if service is running
docker compose ps

# Check service logs
just logs auth
just logs mcp-fetch

# Ensure services are healthy
just ensure-services-ready
```

**Solution**:
```bash
# Rebuild and restart service
just rebuild auth
```

### Issue: 401 Unauthorized

**Diagnosis**:
```bash
# Check token validity
just validate-tokens

# View auth logs
just logs auth | grep "401"
```

**Solution**:
```bash
# Generate new token
just generate-github-token

# For MCP client token
just mcp-client-token
```

### Issue: Connection Refused

**Diagnosis**:
```bash
# Check network exists
docker network ls | grep public

# Test service connectivity
just exec auth curl http://redis:6379
```

**Solution**:
```bash
# Create network and restart
just network-create
just down
just up
```

## Maintenance Tasks

### Regular Cleanup

```bash
# Clean test registrations
just test-cleanup

# Purge expired tokens
just oauth-purge-expired

# Backup OAuth data
just oauth-backup
```

### Service Updates

```bash
# Rebuild services with fresh images
just rebuild

# Rebuild specific service
just rebuild mcp-fetch

# Fresh start with new build
just up-fresh
```

## Debug Techniques

### Enable Debug Logging

1. Edit `.env` file:
```bash
DEBUG=true
LOG_LEVEL=debug
```

2. Rebuild and monitor:
```bash
just rebuild auth
just logs -f auth
```

### Diagnose Test Failures

```bash
# Run diagnostic script
just diagnose-tests

# Run specific test with verbose output
just test tests/test_oauth_flow.py -v -s
```

### Access Service Shell

```bash
# Interactive shell access
just exec auth bash
just exec mcp-fetch sh

# Check environment variables
just exec auth env | grep GATEWAY
just exec mcp-fetch env | grep MCP
```

## Getting Help

When reporting issues:

1. **Collect logs**:
   ```bash
   just logs > gateway-logs.txt
   ```

2. **Show configuration** (remove secrets):
   ```bash
   cat .env | grep -v SECRET | grep -v TOKEN
   ```

3. **Check service status**:
   ```bash
   docker compose ps
   just check-health
   ```

## Related Documentation

- [Service Management](service-management.md)
- [Commands Reference](commands.md)
- [Token Management](token-management.md)
