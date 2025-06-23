# Monitoring & Troubleshooting

This guide covers monitoring the MCP OAuth Gateway and troubleshooting common issues.

## Monitoring Overview

### Key Metrics

Monitor these critical metrics:

1. **Service Health**
   - Container status
   - Health check results
   - Restart counts

2. **Performance Metrics**
   - Request latency
   - Throughput (req/sec)
   - Error rates

3. **Resource Usage**
   - CPU utilization
   - Memory consumption
   - Disk I/O

4. **Application Metrics**
   - Active tokens
   - Authentication failures
   - API usage by client

## Built-in Monitoring

### Health Checks

All services expose health endpoints:

```bash
# Check all services
just health-check

# Individual service health
curl https://auth.gateway.yourdomain.com/health
curl https://mcp-fetch.gateway.yourdomain.com/health
```

### Logs

Access logs through Docker:

```bash
# View all logs
just logs

# Service-specific logs
just logs auth
just logs mcp-fetch
just logs traefik

# Follow logs
just logs -f

# Filter logs
just logs auth | grep ERROR
```

### Metrics Endpoint

Prometheus-compatible metrics:

```bash
# Auth service metrics
curl https://auth.gateway.yourdomain.com/metrics

# Traefik metrics
curl https://traefik.gateway.yourdomain.com/metrics
```

## Log Analysis

### Log Format

Structured JSON logging:

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "INFO",
  "service": "auth",
  "message": "Token validated successfully",
  "user": "alice",
  "client_id": "client_123",
  "duration_ms": 15
}
```

### Common Log Patterns

```bash
# Authentication failures
just logs auth | jq 'select(.level=="ERROR" and .message | contains("auth"))'

# Slow requests
just logs | jq 'select(.duration_ms > 1000)'

# Rate limit hits
just logs | jq 'select(.message | contains("rate limit"))'
```

## Troubleshooting Guide

### Service Won't Start

#### Symptoms
- Container exits immediately
- Health checks failing
- Service unreachable

#### Diagnosis
```bash
# Check container status
docker ps -a

# View startup logs
just logs <service> --tail 100

# Check configuration
just validate-env
```

#### Common Causes
1. **Missing environment variables**
   ```bash
   ERROR: Required variable GITHUB_CLIENT_ID not set
   ```
   Solution: Check .env file

2. **Port conflicts**
   ```bash
   ERROR: bind: address already in use
   ```
   Solution: Change port or stop conflicting service

3. **Redis connection failure**
   ```bash
   ERROR: Could not connect to Redis
   ```
   Solution: Ensure Redis is running

### Authentication Issues

#### User Can't Authenticate

1. **Check allowed users**
   ```bash
   grep ALLOWED_GITHUB_USERS .env
   ```

2. **Verify GitHub OAuth**
   ```bash
   just logs auth | grep "GitHub OAuth"
   ```

3. **Test OAuth flow**
   ```bash
   just test-oauth-flow
   ```

#### Token Validation Failures

1. **Check JWT secret**
   ```bash
   # Ensure secret matches across services
   just show-config | grep JWT_SECRET
   ```

2. **Verify token expiry**
   ```bash
   just decode-token <token>
   ```

3. **Check Redis connectivity**
   ```bash
   just redis-cli ping
   ```

### Performance Issues

#### High Latency

1. **Check resource usage**
   ```bash
   just stats
   ```

2. **Analyze slow endpoints**
   ```bash
   just logs | jq 'select(.duration_ms > 500) | {path, duration_ms}'
   ```

3. **Review rate limits**
   ```bash
   grep RATE_LIMIT .env
   ```

#### Memory Issues

1. **Check memory usage**
   ```bash
   docker stats
   ```

2. **Review Redis memory**
   ```bash
   just redis-cli INFO memory
   ```

3. **Clear old tokens**
   ```bash
   just cleanup-tokens
   ```

### SSL/Certificate Issues

#### Certificate Not Renewing

1. **Check Let's Encrypt logs**
   ```bash
   just logs traefik | grep -i "acme"
   ```

2. **Verify DNS**
   ```bash
   nslookup gateway.yourdomain.com
   ```

3. **Force renewal**
   ```bash
   just renew-certs
   ```

## Monitoring Tools

### Prometheus Setup

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'mcp-gateway'
    static_configs:
      - targets:
        - 'auth:8000'
        - 'traefik:8080'
```

### Grafana Dashboards

Import provided dashboards:

```bash
# Import dashboards
just import-dashboards

# Access Grafana
https://grafana.gateway.yourdomain.com
```

### Alert Rules

```yaml
# alerts.yml
groups:
  - name: mcp-gateway
    rules:
      - alert: ServiceDown
        expr: up{job="mcp-gateway"} == 0
        for: 5m
        
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        
      - alert: SlowRequests
        expr: http_request_duration_seconds{quantile="0.99"} > 2
        for: 10m
```

## Debug Mode

### Enable Debug Logging

```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart services
just restart
```

### Debug Endpoints

```bash
# Service debug info
curl https://auth.gateway.yourdomain.com/debug

# Token debug
curl https://auth.gateway.yourdomain.com/debug/token/<jti>
```

## Common Issues Reference

### Issue: 502 Bad Gateway

**Causes**:
- Service not running
- Health check failing
- Network connectivity

**Solution**:
```bash
just restart <service>
just logs <service>
```

### Issue: 401 Unauthorized

**Causes**:
- Expired token
- Invalid token
- User not allowed

**Solution**:
```bash
just generate-token
just validate-token <token>
```

### Issue: Rate Limit Exceeded

**Causes**:
- Too many requests
- Misconfigured limits

**Solution**:
```bash
# Adjust limits in .env
RATE_LIMIT_MCP=200/minute
just restart
```

## Maintenance Commands

### Regular Maintenance

```bash
# Clean up old tokens
just cleanup-tokens

# Vacuum Redis
just redis-vacuum

# Rotate logs
just rotate-logs

# Update services
just update-all
```

### Emergency Procedures

```bash
# Stop all services
just down

# Emergency restart
just emergency-restart

# Backup before changes
just backup-all

# Restore from backup
just restore <backup-file>
```

## Getting Help

### Diagnostic Bundle

Generate a diagnostic bundle:

```bash
just diagnostic-bundle
```

This creates a zip file with:
- Configuration (sanitized)
- Recent logs
- Health check results
- Performance metrics

### Support Channels

1. Check documentation first
2. Review [GitHub issues](https://github.com/your-org/mcp-oauth-gateway/issues)
3. Contact support with diagnostic bundle