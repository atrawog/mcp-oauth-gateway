# OAuth Management Commands

Complete OAuth lifecycle management commands following RFC 7591/7592 standards.

## Overview

The justfile provides comprehensive OAuth management commands for:
- Client registration management
- Token lifecycle operations
- Backup and restore functionality
- Cleanup and maintenance

## Client Registration Management

### Listing Operations

```bash
# Show all registered OAuth clients
just oauth-list-registrations

# Show all active tokens
just oauth-list-tokens

# Show complete OAuth statistics
just oauth-stats

# Display everything (stats + registrations + tokens)
just oauth-show-all
```

### Client Deletion

```bash
# Delete a specific client registration
just oauth-delete-registration client_abc123

# Delete client and ALL associated data (tokens, etc.)
just oauth-delete-client-complete client_abc123

# Delete ALL registrations (dangerous!)
just oauth-delete-all-registrations
```

### Token Management

```bash
# Delete specific token by JTI
just oauth-delete-token jti_xyz789

# Delete ALL tokens (dangerous!)
just oauth-delete-all-tokens

# Purge expired tokens (dry run)
just oauth-purge-expired-dry

# Actually purge expired tokens
just oauth-purge-expired
```

## Backup and Restore

### Creating Backups

```bash
# Backup all OAuth registrations and tokens
just oauth-backup

# Creates timestamped backup in backups/ directory
# Format: oauth-backup-YYYYMMDD-HHMMSS.json
```

### Viewing Backups

```bash
# List available backups
just oauth-backup-list

# View contents of latest backup
just oauth-backup-view

# View specific backup file
just oauth-backup-view-file oauth-backup-20240101-120000.json
```

### Restoring Data

```bash
# Restore from latest backup
just oauth-restore

# Restore from specific file
just oauth-restore-file oauth-backup-20240101-120000.json

# Clear existing data before restore
just oauth-restore-clear

# Dry run - see what would be restored
just oauth-restore-dry
```

## Test Data Management

### Sacred Test Pattern

Test clients follow the naming convention: `TEST {test_name}`

```bash
# Show all test registrations
just test-cleanup-show

# Clean up test registrations
just test-cleanup
```

Example test client names:
- `TEST integration_suite`
- `TEST oauth_flow`
- `TEST claude_integration`

## Token Generation

### Gateway Tokens

```bash
# Generate new JWT secret
just generate-jwt-secret

# Generate RSA key pair for RS256
just generate-rsa-keys

# Generate GitHub OAuth token
just generate-github-token

# Refresh existing tokens
just refresh-tokens

# Validate all tokens
just validate-tokens

# Check token expiration
just check-token-expiry
```

### MCP Client Tokens

```bash
# Generate token for mcp-streamablehttp-client
just mcp-client-token

# Complete OAuth flow with auth code
just mcp-client-token-complete auth_code_here
```

## OAuth Statistics

The `oauth-stats` command provides:

```
📊 OAuth Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Client Registrations: 42
Active Tokens: 137
Expired Tokens: 23
User Count: 15
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Implementation Details

### Redis Key Patterns

All OAuth data stored in Redis with these patterns:

```
oauth:client:{client_id}     # Client registration
oauth:token:{jti}            # Access tokens
oauth:refresh:{token}        # Refresh tokens
oauth:state:{state}          # CSRF states
oauth:code:{code}            # Auth codes
oauth:user_tokens:{username} # User token index
```

### Management Scripts

Commands use Python scripts in `scripts/`:
- `manage_oauth_data.py` - Main OAuth management
- `backup_oauth_data.py` - Backup functionality
- `restore_oauth_data.py` - Restore functionality
- `cleanup_test_data.py` - Test cleanup
- `purge_expired_tokens.py` - Token cleanup

## Security Considerations

### Dangerous Operations

These commands require careful consideration:
- `oauth-delete-all-registrations` - Removes ALL clients
- `oauth-delete-all-tokens` - Invalidates ALL access
- `oauth-restore-clear` - Wipes existing data

### Safe Operations

These commands are non-destructive:
- All `list` and `show` commands
- `oauth-backup` operations
- Dry run commands (`-dry` suffix)

## Best Practices

1. **Regular Backups**
   ```bash
   # Add to cron for daily backups
   0 2 * * * cd /path/to/gateway && just oauth-backup
   ```

2. **Token Hygiene**
   ```bash
   # Weekly cleanup of expired tokens
   just oauth-purge-expired
   ```

3. **Test Cleanup**
   ```bash
   # After test runs
   just test-cleanup
   ```

4. **Pre-deployment Backup**
   ```bash
   # Before any major changes
   just oauth-backup
   just oauth-stats > oauth-stats-pre-deploy.txt
   ```

## Troubleshooting

### Client Not Found
```bash
# Verify client exists
just oauth-list-registrations | grep client_id
```

### Token Issues
```bash
# Check token status
just oauth-list-tokens | grep jti
```

### Restore Failures
```bash
# Check Redis connectivity
just exec redis redis-cli ping

# Verify backup file
just oauth-backup-view-file backup.json
```
