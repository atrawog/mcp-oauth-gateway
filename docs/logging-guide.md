# 📜 Logging Guide for MCP OAuth Gateway

## Overview

All services in the MCP OAuth Gateway are configured to write logs to the `./logs` directory, organized by service name. This provides persistent logging that survives container restarts and enables comprehensive monitoring and debugging.

## Log Directory Structure

```
logs/
├── traefik/
│   ├── traefik.log      # General Traefik logs (JSON format)
│   └── access.log       # HTTP access logs with full headers (JSON format)
├── auth/
│   └── auth.log         # Auth service application logs
├── mcp-fetch/
│   └── server.log       # MCP Fetch service logs
├── mcp-fetchs/
│   └── server.log       # MCP Fetchs service logs
├── mcp-filesystem/
│   └── server.log       # MCP Filesystem service logs
├── mcp-memory/
│   └── server.log       # MCP Memory service logs
└── [other-mcp-services]/
    └── server.log       # Service-specific logs
```

## Just Commands for Log Management

### Viewing Logs

```bash
# View Docker container logs (standard output)
just logs [service-name]
just logs-follow [service-name]

# View file-based logs from ./logs directory
just logs-files              # View all service logs
just logs-files traefik      # View specific service logs
just logs-files auth
```

### Log Statistics

```bash
# Show log file statistics
just logs-stats

# Example output:
# 📁 traefik: 2.3M (2 log files)
# 📁 auth: 156K (1 log files)
# 📁 mcp-fetch: 89K (1 log files)
# Total size: 2.5M
```

### Log Cleanup

```bash
# Remove ALL logs (default behavior - asks for confirmation)
just logs-clean

# Remove ALL logs without confirmation (for automation)
just logs-clean-force
# Or use environment variable:
FORCE_CLEAN=1 just logs-clean

# Keep last 7 days of logs (removes older logs)
just logs-clean 7

# Keep last 30 days of logs
just logs-clean 30

# Keep last 1 day of logs
just logs-clean 1
```

**Note**: The default `just logs-clean` will ask for confirmation before deleting all logs to prevent accidental data loss. Use `just logs-clean-force` or set `FORCE_CLEAN=1` for automation scenarios.

### Log Rotation

```bash
# Setup system-wide log rotation (requires sudo)
just logs-rotation-setup

# Manually rotate logs
just logs-rotate

# Purge Docker container logs (restarts services)
just logs-purge
```

### Testing

```bash
# Test logging configuration
just logs-test
```

## Log Rotation Configuration

The project includes a `logrotate.conf` file that configures:
- Daily rotation
- 7 days retention (by default)
- Compression of rotated logs
- Proper file permissions
- Signal to Traefik to reopen log files

## Traefik Access Logs

Traefik's access logs include comprehensive HTTP request information:
- Request method and path
- Response status code
- Request/response headers
- Client IP address
- Request duration
- Backend service information

Example access log entry (JSON format):
```json
{
  "time": "2025-06-27T10:30:45Z",
  "status": 200,
  "method": "POST",
  "path": "/mcp",
  "host": "fetch.example.com",
  "headers": {
    "Authorization": ["Bearer ***"],
    "Content-Type": ["application/json"]
  },
  "duration": 0.023
}
```

## Service Logs

All MCP services write logs to their respective directories with timestamp and log level:
```
2025-06-27 10:30:45 - mcp_streamablehttp_proxy - INFO - Starting MCP stdio-to-HTTP proxy
2025-06-27 10:30:46 - mcp_streamablehttp_proxy - INFO - MCP server process started
```

## Debugging Tips

1. **Check service health first**:
   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}"
   ```

2. **Follow multiple services**:
   ```bash
   just logs-files  # Shows all service logs in real-time
   ```

3. **Search logs for errors**:
   ```bash
   grep -r "ERROR" logs/
   grep -r "401" logs/traefik/access.log
   ```

4. **Monitor log growth**:
   ```bash
   watch -n 10 'just logs-stats'
   ```

## Environment Variables

Services support these logging-related environment variables:
- `LOG_FILE` - Path to log file (set automatically)
- `LOG_LEVEL` - Logging verbosity (INFO, DEBUG, ERROR)

## Best Practices

1. **Regular Cleanup**: Use `just logs-clean 7` to keep only recent logs
2. **Monitor Size**: Check `just logs-stats` regularly
3. **Setup Rotation**: Run `just logs-rotation-setup` on production servers
4. **Debug Mode**: Set `LOG_LEVEL=DEBUG` in `.env` for verbose logging
5. **Archive Important Logs**: Before running `just logs-clean`, archive any logs needed for auditing

## Troubleshooting

### No Logs Appearing
- Ensure services are running: `just ps`
- Check volume mounts: `docker compose config | grep logs`
- Verify permissions: `ls -la logs/`

### Logs Not Rotating
- Check logrotate installation: `which logrotate`
- Test configuration: `sudo logrotate -d /etc/logrotate.d/mcp-oauth-gateway`
- Force rotation: `just logs-rotate`

### Disk Space Issues
- Clean all logs: `just logs-clean`
- Keep only recent: `just logs-clean 3`
- Check sizes: `du -sh logs/*`
