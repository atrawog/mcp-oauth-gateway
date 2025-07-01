# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the MCP OAuth Gateway. Remember the sacred debugging commandment: **Root cause analysis or eternal debugging hell!** ⚡

```{admonition} The Five Whys of Divine Debugging
:class: important
🔥 **Always ask five whys to find the root cause:**
1. Why did it fail? → Surface symptom
2. Why did that condition exist? → Enabling circumstance
3. Why was it allowed? → Systemic failure
4. Why wasn't it caught? → Testing blindness
5. Why will it never happen again? → Divine fix
```

## Quick Diagnostic Commands

Before diving deep, run these blessed diagnostics:

```bash
# Overall health check
just health-check

# Service status
just ps

# Recent logs
just logs --since 10m

# Check configuration
just validate-config

# Network connectivity
just check-network

# Port availability
just check-ports
```

## Common Issues

### Services Not Starting

#### Symptoms
```
✗ Container mcp-oauth-auth-1     Exited (1)
✗ Container mcp-oauth-traefik-1  Restarting
```

#### Diagnosis
```bash
# Check specific service logs
just logs auth -n 100

# Check for port conflicts
sudo lsof -i :80
sudo lsof -i :443
sudo lsof -i :8000

# Verify environment variables
just check-env
```

#### Common Causes & Solutions

**1. Missing Environment Variables**
```bash
# Error: KeyError: 'GITHUB_CLIENT_ID'
# Solution: Ensure all required vars in .env
cp .env.example .env
nano .env  # Fill in required values
```

**2. Port Already in Use**
```bash
# Error: bind: address already in use
# Solution: Stop conflicting service
sudo systemctl stop nginx  # or apache2
# Or change ports in .env
```

**3. Invalid Configuration**
```bash
# Error: yaml: line 23: found character '\t'
# Solution: Fix YAML formatting (spaces only!)
just validate-compose
```

### OAuth Authentication Failures

#### Cannot Register Client

**Symptom**: POST to `/register` returns 400 or 500

```bash
# Diagnose
curl -v -X POST http://localhost/register \
  -H "Content-Type: application/json" \
  -d '{"client_name":"test"}'

# Check auth logs
just logs auth | grep -E "register|error"
```

**Common Fixes**:
1. Ensure Redis is running: `just exec auth redis-cli PING`
2. Check required fields in registration
3. Verify CORS if from browser

#### GitHub OAuth Errors

**Symptom**: Redirect to GitHub fails or returns error

```bash
# Test GitHub connectivity
just exec auth curl -I https://api.github.com

# Verify OAuth credentials
just exec auth env | grep GITHUB

# Check callback URL matches GitHub app
echo "Callback should be: https://auth.${DOMAIN}/callback"
```

**Common Fixes**:
1. Update GitHub OAuth app callback URL
2. Ensure GITHUB_CLIENT_ID and SECRET are correct
3. Check ALLOWED_GITHUB_USERS restrictions

#### Token Validation Failures

**Symptom**: 401 Unauthorized on MCP endpoints

```bash
# Test token validation
TOKEN="your-jwt-token"
curl -H "Authorization: Bearer $TOKEN" \
  http://auth.localhost/verify

# Decode JWT to check claims
echo $TOKEN | cut -d. -f2 | base64 -d | jq .
```

**Common Fixes**:
1. Token expired - request new token
2. Wrong JWT secret - check GATEWAY_JWT_SECRET
3. Invalid issuer/audience claims

### MCP Service Issues

#### MCP Service Not Responding

**Symptom**: 502 Bad Gateway or timeouts

```bash
# Check service health
curl http://mcp-fetch.localhost/health

# Check if subprocess is running (for proxy pattern)
just exec mcp-fetch ps aux

# View service logs
just logs mcp-fetch -f
```

**Common Fixes**:
1. Service crashed - restart: `just restart mcp-fetch`
2. Subprocess died - check mcp-server installation
3. Memory limit hit - increase limits

#### Protocol Version Mismatch

**Symptom**: MCP initialization fails

```bash
# Check protocol version
just exec mcp-fetch env | grep MCP_PROTOCOL_VERSION

# Test with curl
curl -X POST http://mcp-fetch.localhost/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18"},"id":1}'
```

**Common Fixes**:
1. Update MCP_PROTOCOL_VERSION in .env
2. Ensure client and server support same version
3. Check service supports claimed version

### Network and Routing Issues

#### Cannot Access Services

**Symptom**: Connection refused or timeout

```bash
# Test internal connectivity
just exec traefik ping auth
just exec traefik wget -O- http://auth:8000/health

# Check Traefik routing
curl -H "Host: auth.localhost" http://localhost/health

# Verify DNS resolution
nslookup auth.localhost
```

**Common Fixes**:
1. Add entries to /etc/hosts for localhost
2. Check Traefik labels on services
3. Verify network connectivity between containers

#### SSL Certificate Issues

**Symptom**: SSL errors or certificate warnings

```bash
# Check certificate status
just exec traefik cat /letsencrypt/acme.json | jq '.letsencrypt.Certificates'

# Test SSL
openssl s_client -connect mcp.yourdomain.com:443 -servername mcp.yourdomain.com

# Check ACME logs
just logs traefik | grep -i acme
```

**Common Fixes**:
1. Ensure port 80 is accessible for ACME
2. Verify DNS points to correct IP
3. Check rate limits not exceeded
4. Use staging server for testing

### Performance Issues

#### High Memory Usage

**Symptom**: Services consuming excessive memory

```bash
# Monitor memory usage
just stats

# Check for memory leaks
just exec auth ps aux --sort=-%mem | head

# View memory limits
docker inspect mcp-oauth-auth-1 | jq '.[0].HostConfig.Memory'
```

**Common Fixes**:
1. Set memory limits in docker-compose
2. Enable Redis memory limits
3. Restart services periodically
4. Check for infinite loops in logs

#### Slow Response Times

**Symptom**: Requests taking > 1s

```bash
# Measure response times
time curl -H "Authorization: Bearer $TOKEN" \
  http://mcp-fetch.localhost/mcp

# Check service load
just exec auth top

# Monitor Redis performance
just exec redis redis-cli --latency
```

**Common Fixes**:
1. Scale services horizontally
2. Optimize Redis queries
3. Enable caching where appropriate
4. Check network latency

### Redis Issues

#### Connection Failures

**Symptom**: Redis connection refused

```bash
# Test Redis connectivity
just exec redis redis-cli PING

# Check Redis logs
just logs redis

# Verify password
just exec auth redis-cli -a $REDIS_PASSWORD PING
```

**Common Fixes**:
1. Ensure Redis is running
2. Check REDIS_PASSWORD matches
3. Verify Redis port not blocked
4. Check Redis memory/disk full

#### Data Persistence Issues

**Symptom**: Data lost after restart

```bash
# Check persistence config
just exec redis redis-cli CONFIG GET save
just exec redis redis-cli CONFIG GET appendonly

# Verify data directory
just exec redis ls -la /data
```

**Common Fixes**:
1. Enable Redis persistence in config
2. Ensure volume is mounted correctly
3. Check disk space for Redis data
4. Verify file permissions

## Advanced Debugging

### Enable Debug Logging

```bash
# Temporarily enable debug logs
LOG_LEVEL=DEBUG just up auth

# Or modify .env
echo "LOG_LEVEL=DEBUG" >> .env
just restart auth
```

### Interactive Debugging

```bash
# Enter service container
just shell auth

# Inside container:
python
>>> import redis
>>> r = redis.from_url("redis://:password@redis:6379")
>>> r.ping()

# Test OAuth flow manually
curl -v http://localhost:8000/health
```

### Network Debugging

```bash
# Inspect networks
docker network ls
docker network inspect mcp-oauth_public

# Test connectivity between containers
just exec auth ping redis
just exec auth nc -zv redis 6379

# Trace routing
just exec traefik wget -S -O- http://auth:8000/health
```

### Trace Requests

```bash
# Enable Traefik debug logs
TRAEFIK_LOG_LEVEL=DEBUG just restart traefik

# Follow request flow
just logs -f traefik | grep -E "auth|mcp-fetch"

# Use correlation IDs
curl -H "X-Request-ID: test-123" http://auth.localhost/health
just logs | grep test-123
```

## Recovery Procedures

### Service Recovery

```bash
# Restart individual service
just restart auth

# Restart all services
just down && just up

# Force recreate
just down
just up --force-recreate
```

### Data Recovery

```bash
# Backup Redis before recovery
just exec redis redis-cli BGSAVE

# Restore from backup
docker cp backup/dump.rdb mcp-oauth-redis-1:/data/dump.rdb
just restart redis
```

### Complete Reset

```bash
# Warning: Deletes all data!
just clean-all

# Start fresh
just init
just up
```

## Preventive Measures

### Health Monitoring

```bash
# Set up automated health checks
crontab -e
# Add: */5 * * * * /opt/mcp-oauth-gateway/scripts/health-check.sh

# Monitor logs for errors
just logs -f | grep -E "ERROR|CRITICAL|FATAL"
```

### Regular Maintenance

```bash
# Weekly: Update containers
just pull
just up -d

# Monthly: Clean unused resources
docker system prune -af

# Quarterly: Review and rotate secrets
just rotate-secrets
```

## Getting Help

### Collect Diagnostics

```bash
# Generate diagnostic bundle
just diagnostic-bundle

# Includes:
# - Service logs
# - Configuration (sanitized)
# - Health check results
# - Resource usage
```

### Reporting Issues

When reporting issues, include:
1. Output of `just version`
2. Diagnostic bundle
3. Steps to reproduce
4. Expected vs actual behavior
5. Any error messages

### Support Channels

- GitHub Issues: For bugs and features
- Documentation: This guide and others
- Community: Discord/Slack channels

---

*Remember: Every problem has a root cause. Find it with the five whys, fix it properly, and document the solution. This is the path to operational excellence!* 🔧⚡
