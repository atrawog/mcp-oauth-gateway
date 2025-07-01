# Logging Commands

Centralized logging management following the divine commandment: "Scattered logs = lost wisdom!"

## Overview

The justfile provides comprehensive logging commands for:
- Container log viewing and following
- File-based log management
- Log rotation and cleanup
- Statistics and analysis

## Container Logs

### Basic Log Viewing

```bash
# View logs for all services
just logs

# View logs for specific service
just logs auth

# Follow logs in real-time
just logs -f

# Follow specific service logs
just logs -f mcp-fetch

# View last N lines
just logs --tail 100

# Multiple services
just logs auth redis traefik
```

### Log Following Alias

```bash
# Convenience alias for following
just logs-follow auth

# Equivalent to
just logs -f auth
```

## File-Based Logs

All services write logs to `./logs/{service-name}/`:

```
logs/
├── traefik/
│   ├── access.log
│   └── traefik.log
├── auth/
│   └── app.log
├── redis/
│   └── redis.log
└── mcp-fetch/
    ├── proxy.log
    └── server.log
```

### Viewing File Logs

```bash
# View all service logs
just logs-files

# View specific service logs
just logs-files auth

# Real-time following
tail -f logs/auth/*.log
```

## Log Management

### Log Statistics

```bash
# Show log statistics
just logs-stats

Output:
📊 Log Statistics
================
📁 auth: 156MB (3 log files)
📁 traefik: 89MB (2 log files)
📁 redis: 12MB (1 log files)
📁 mcp-fetch: 45MB (2 log files)

Total size: 302MB
```

### Log Cleanup

```bash
# Clean all logs (with confirmation)
just logs-clean

# Keep logs from last 7 days
just logs-clean 7

# Force clean without confirmation
just logs-clean-force

# CI/CD friendly
FORCE_CLEAN=1 just logs-clean
```

### Log Purging

```bash
# Purge container logs (restart services)
just logs-purge

# This stops and restarts all services
# Effectively clearing container logs
```

## Log Rotation

### Setup Rotation

```bash
# Setup system-wide log rotation (requires sudo)
just logs-rotation-setup

# Creates /etc/logrotate.d/mcp-oauth-gateway
```

Rotation configuration:
```
/path/to/logs/*/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 user group
}
```

### Manual Rotation

```bash
# Manually trigger rotation
just logs-rotate

# Uses logrotate -f to force rotation
```

## Log Testing

### Test Configuration

```bash
# Test logging configuration
just logs-test

# Verifies:
# - Log directories exist
# - Write permissions
# - Rotation configuration
# - Service logging
```

## Log Analysis

### OAuth Log Analysis

```bash
# Analyze OAuth logs
just analyze-oauth-logs

# Generates report in reports/
# reports/oauth-analysis-20240101-120000.md
```

Report includes:
- Authentication success/failure rates
- Token generation statistics
- Client registration patterns
- Error analysis

### Common Patterns

```bash
# Find errors across all logs
grep -r ERROR logs/

# Authentication failures
grep "auth_failure" logs/auth/*.log

# Trace specific request
grep "request_id_xyz" logs/*/*.log
```

## Structured Logging

Services use structured JSON logging:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "service": "auth",
  "event": "token_generated",
  "client_id": "client_abc123",
  "user_id": "github|username",
  "request_id": "req_xyz789"
}
```

### Parsing Structured Logs

```bash
# Extract specific fields
cat logs/auth/app.log | jq '.event'

# Filter by level
cat logs/auth/app.log | jq 'select(.level == "ERROR")'

# Count events
cat logs/auth/app.log | jq '.event' | sort | uniq -c
```

## Log Levels

Configure via environment:

```bash
# Service-specific
AUTH_LOG_LEVEL=DEBUG
TRAEFIK_LOG_LEVEL=INFO
MCP_LOG_LEVEL=WARN

# Global fallback
LOG_LEVEL=INFO
```

Levels (in order):
- `DEBUG` - Detailed debugging
- `INFO` - General information
- `WARN` - Warning conditions
- `ERROR` - Error conditions
- `FATAL` - Critical failures

## Monitoring Integration

### Real-time Monitoring

```bash
# Watch for errors
watch 'grep -c ERROR logs/*/*.log'

# Monitor log growth
watch 'du -sh logs/*'

# Track request rate
tail -f logs/traefik/access.log | grep -c "POST /mcp"
```

### Alerting Patterns

```bash
# Alert on high error rate
ERROR_COUNT=$(grep -c ERROR logs/auth/app.log)
if [ $ERROR_COUNT -gt 100 ]; then
    echo "High error rate detected!"
fi
```

## Best Practices

1. **Regular Cleanup**
   ```bash
   # Weekly cleanup keeping 7 days
   0 3 * * 0 just logs-clean 7
   ```

2. **Rotation Setup**
   ```bash
   # One-time setup
   just logs-rotation-setup
   ```

3. **Monitoring**
   ```bash
   # Follow logs during development
   just logs -f

   # Check errors after deployment
   grep ERROR logs/*/*.log
   ```

4. **Analysis**
   ```bash
   # Regular OAuth analysis
   just analyze-oauth-logs
   ```

## Troubleshooting

### No Logs Appearing

```bash
# Check service is running
docker compose ps

# Check log directory permissions
ls -la logs/

# Check service log configuration
docker compose exec auth env | grep LOG
```

### Log Rotation Not Working

```bash
# Check logrotate configuration
cat /etc/logrotate.d/mcp-oauth-gateway

# Test rotation
sudo logrotate -d /etc/logrotate.d/mcp-oauth-gateway
```

### Disk Space Issues

```bash
# Check log sizes
just logs-stats

# Clean old logs
just logs-clean 1

# Emergency cleanup
just logs-clean-force
```
