# Token Management Examples

## Check Token Status

The `--token` / `-t` option provides comprehensive token status and management:

```bash
$ mcp-streamablehttp-client --token
```

### Example Output

```
OAuth Token Status Check
========================================

✓ OAuth endpoints configured
  Authorization: https://auth.example.com/authorize
  Token: https://auth.example.com/token
  Device: https://auth.example.com/device/code
  Registration: https://auth.example.com/register

Client Registration:
✓ Client registered: client_abc123
  Secret: secret_x...

Access Token:
✓ Token exists: eyJhbGciOiJIUzI1NiI...
✓ Valid until: 2025-06-19T15:30:00Z
  Time left: 2.5 hours

Refresh Token:
✓ Refresh token available: refresh_def456...

Testing token with server...
✓ Token accepted by server!
  Server: mcp-fetch v1.0.0

🎉 All token checks passed!

Credentials stored in: /home/user/.mcp/credentials.json
Permissions: 600
```

## Automatic Token Refresh

When tokens are expired or expiring soon:

```bash
$ mcp-streamablehttp-client --token
```

```
OAuth Token Status Check
========================================

✓ OAuth endpoints configured
✓ Client registered: client_abc123

Access Token:
✓ Token exists: eyJhbGciOiJIUzI1NiI...
⚠️  Expires soon: 2025-06-19T12:05:00Z
  Time left: 240 seconds

Refresh Token:
✓ Refresh token available: refresh_def456...

Refreshing access token...
✓ Token refreshed successfully!
  New token: eyJhbGciOiJIUzI1NiJ...
  New expiry: 2025-06-19T16:05:00Z

Testing token with server...
✓ Token accepted by server!

🎉 All token checks passed!
```

## Common Scenarios

### First Time Setup
```bash
$ mcp-streamablehttp-client --token

OAuth Token Status Check
========================================

⚠️  OAuth endpoints not discovered yet

Discovering OAuth configuration...
✓ OAuth endpoints discovered

Client Registration:
⚠️  No client credentials found

Authentication required
Registering OAuth client...

Please visit:
https://auth.example.com/device

And enter code:
ABCD-1234

✓ Authentication completed successfully!
✓ All token checks passed!
```

### Expired Tokens with Valid Refresh Token
```bash
$ mcp-streamablehttp-client --token

Access Token:
✗ Token expired: 2025-06-19T11:00:00Z
  Expired 3600 seconds ago

Refresh Token:
✓ Refresh token available: refresh_def456...

Refreshing access token...
✓ Token refreshed successfully!
```

### Completely Invalid Credentials
```bash
$ mcp-streamablehttp-client --token

Access Token:
✗ Token expired: 2025-06-19T11:00:00Z

Refresh Token:
⚠️  No refresh token available

Authentication required
# ... full OAuth flow starts
```

## Integration with Other Commands

The token check is automatically integrated:

```bash
# These commands will automatically refresh tokens if needed
mcp-streamablehttp-client --command "fetch https://example.com"
mcp-streamablehttp-client --test-auth
```

But `--token` gives you explicit control and detailed status information.

## Troubleshooting Token Issues

1. **Check status first**:
   ```bash
   mcp-streamablehttp-client --token
   ```

2. **If refresh fails**:
   ```bash
   mcp-streamablehttp-client --reset-auth
   ```

3. **Debug token issues**:
   ```bash
   mcp-streamablehttp-client --token --log-level DEBUG
   ```

4. **Manual server test after token refresh**:
   ```bash
   mcp-streamablehttp-client --token && mcp-streamablehttp-client --test-auth
   ```