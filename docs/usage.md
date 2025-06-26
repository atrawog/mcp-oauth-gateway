# Usage Guide

This guide covers the day-to-day usage of the MCP OAuth Gateway, from basic commands to advanced management tasks.

## Topics

```{toctree}
:maxdepth: 2

usage/commands
usage/service-management
usage/token-management
usage/testing
usage/monitoring
```

## Quick Reference

### Essential Commands

```bash
# Start the gateway
just up

# View logs
just logs

# Run tests
just test

# Generate tokens
just generate-jwt-secret
just generate-github-token
just mcp-client-token
```

### Common Tasks

1. **Starting Services** - Use `just up` to start all services
2. **Checking Status** - Monitor with `just logs` and health endpoints
3. **Managing Tokens** - Generate and rotate authentication tokens
4. **Running Tests** - Verify configuration with `just test`

## Workflow Examples

### Daily Operations

1. Check service health: `just logs`
2. Monitor performance: View metrics at `/metrics`
3. Rotate tokens as needed
4. Backup Redis data regularly

### Troubleshooting

When issues arise:

1. Check logs: `just logs -f <service>`
2. Run diagnostics: `just test-verbose`
3. Review configuration: `just show-config`
4. See [Monitoring & Troubleshooting](usage/monitoring.md)

## Best Practices

- Always use `just` commands instead of direct Docker commands
- Monitor logs regularly for security events
- Keep tokens secure and rotate them periodically
- Test configuration changes before applying to production
