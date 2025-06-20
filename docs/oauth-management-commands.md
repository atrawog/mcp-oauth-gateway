# OAuth Management Commands

This document describes the `just` commands for managing OAuth registrations and tokens in the MCP OAuth Gateway.

## Overview

The gateway stores OAuth data in Redis:
- **Client Registrations**: OAuth clients registered via dynamic registration (RFC 7591)
- **Access Tokens**: Active JWT tokens with user sessions
- **Refresh Tokens**: Long-lived tokens for renewing access

## Commands

### Viewing OAuth Data

#### Show OAuth Statistics
```bash
just oauth-stats
```
Displays a summary of all OAuth data including counts of registrations, tokens, and active users.

#### List All Client Registrations
```bash
just oauth-list-registrations
```
Shows all registered OAuth clients with their IDs, names, scopes, and redirect URIs.

#### List All Active Tokens
```bash
just oauth-list-tokens
```
Displays all active access tokens with user information, client IDs, and expiration times.

#### Show Complete OAuth Data
```bash
just oauth-show-all
```
Runs all viewing commands in sequence (stats, registrations, tokens).

### Deleting OAuth Data

#### Delete Specific Client Registration
```bash
just oauth-delete-registration <client_id>
```
Removes a specific client registration and all associated tokens.

Example:
```bash
just oauth-delete-registration client_ABC123
```

#### Delete Client Complete (Registration + ALL Tokens)
```bash
just oauth-delete-client-complete <client_id>
```
Explicitly deletes a client registration and ALL associated data including:
- The client registration itself
- All access tokens issued to this client
- All authorization codes for this client
- Shows a detailed deletion summary

Example:
```bash
just oauth-delete-client-complete client_ACr2wy6hSDlOmntyNNJicg
```

Output:
```
✅ Deleted client registration:
   Client ID: client_ACr2wy6hSDlOmntyNNJicg
   Name: mcp-http-stdio
   Scope: read write

📊 Deletion Summary:
   Access tokens deleted: 1
   Auth codes deleted: 1

✅ Client 'client_ACr2wy6hSDlOmntyNNJicg' and all associated data has been removed.
```

#### Delete Specific Token
```bash
just oauth-delete-token <jti>
```
Deletes a specific token by its JTI (JWT ID). Supports partial matching.

Example:
```bash
just oauth-delete-token dS4MClJT
```

#### Delete ALL Client Registrations (Dangerous!)
```bash
just oauth-delete-all-registrations
```
**WARNING**: Removes ALL client registrations and their associated tokens. Requires confirmation.

#### Delete ALL Tokens (Dangerous!)
```bash
just oauth-delete-all-tokens
```
**WARNING**: Removes ALL access and refresh tokens. Requires confirmation.

### Purging Expired Tokens

#### Check for Expired Tokens (Dry Run)
```bash
just oauth-purge-expired-dry
```
Shows what tokens would be deleted without actually deleting them. Use this to preview the cleanup operation.

#### Purge Expired Tokens
```bash
just oauth-purge-expired
```
Actually deletes all expired tokens, including:
- Access tokens past their expiration time
- Refresh tokens with expired TTL
- Auth codes with expired TTL
- Auth states with expired TTL
- Orphaned user token indexes

## Token Expiration Strategy

The system uses Redis TTL (Time To Live) for automatic expiration:
- **Access tokens**: Set via `setex` with `ACCESS_TOKEN_LIFETIME` (default: 24 hours)
- **Refresh tokens**: Set with `REFRESH_TOKEN_LIFETIME` (default: 30 days)
- **Auth codes**: Short-lived (typically 10 minutes)
- **Auth states**: Very short-lived (5 minutes)

Redis automatically removes keys when their TTL expires, but the purge command helps clean up:
- Tokens stored without TTL (from older versions)
- Orphaned user token indexes
- Any inconsistent data

### Recommended Usage

1. **Regular Maintenance**: Run monthly or weekly depending on traffic
   ```bash
   # Check what would be cleaned
   just oauth-purge-expired-dry
   
   # If looks good, actually purge
   just oauth-purge-expired
   ```

2. **After Heavy Testing**: Clean up test tokens
   ```bash
   just oauth-purge-expired
   ```

3. **Before Backups**: Ensure you're not backing up expired data
   ```bash
   just oauth-purge-expired
   just oauth-stats  # Verify counts
   ```

4. **Automation Options**:
   - Add to crontab: `0 3 * * 0 cd /path/to/project && just oauth-purge-expired`
   - Add to CI/CD maintenance jobs
   - Run before deployments

## Usage Examples

### Clean Up Test Data
After running tests, you may accumulate many test registrations:
```bash
# Check current state
just oauth-stats

# If too many test registrations, clean them up
just oauth-delete-all-registrations
```

### Debug Token Issues
```bash
# See all active tokens
just oauth-list-tokens

# Delete expired or problematic token
just oauth-delete-token <partial-jti>
```

### Monitor Active Users
```bash
# Quick overview
just oauth-stats

# Detailed token information
just oauth-list-tokens
```

## Data Storage Details

The commands interact with Redis keys following these patterns:
- `oauth:client:{client_id}` - Client registration data
- `oauth:token:{jti}` - Access token data
- `oauth:refresh:{token}` - Refresh tokens
- `oauth:user_tokens:{username}` - User token index

All commands work with real production data - there's no mocking or simulation, following the sacred commandments of CLAUDE.md.