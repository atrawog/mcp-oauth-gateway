# RFC 7592 Client Registration Management

The `mcp-streamablehttp-client` now supports full RFC 7592 (OAuth 2.0 Dynamic Client Registration Management Protocol) functionality, allowing clients to manage their registrations after initial creation.

## Overview

RFC 7592 extends RFC 7591 (Dynamic Client Registration) by providing endpoints for:
- **GET** - Read current client configuration
- **PUT** - Update client configuration
- **DELETE** - Remove client registration

These operations use a special `registration_access_token` that is provided during initial registration.

## New CLI Commands

### Get Client Information

View your current client registration details:

```bash
mcp-streamablehttp-client --get-client-info
```

This displays:
- Client ID and name
- Registered scopes and redirect URIs
- Grant types and response types
- Registration timestamps
- Expiration information

### Update Client Registration

Update specific fields of your registration:

```bash
# Update single field
mcp-streamablehttp-client --update-client "client_name=My Updated Client"

# Update multiple fields (comma-separated)
mcp-streamablehttp-client --update-client "client_name=New Name,scope=read write admin"

# Update array fields (semicolon-separated values)
mcp-streamablehttp-client --update-client "redirect_uris=https://app1.com/callback;https://app2.com/callback"
```

Allowed update fields:
- `client_name` - Human-readable client name
- `redirect_uris` - OAuth callback URLs (array)
- `scope` - Requested scopes
- `grant_types` - OAuth grant types (array)
- `response_types` - OAuth response types (array)
- `contacts` - Contact emails (array)
- `client_uri` - Client homepage URL
- `logo_uri` - Client logo URL
- `tos_uri` - Terms of service URL
- `policy_uri` - Privacy policy URL

### Delete Client Registration

Permanently delete your client registration:

```bash
mcp-streamablehttp-client --delete-client
```

⚠️ **Warning**: This is irreversible! You'll need to re-register to use the service again.

## Environment Variables

The client now stores and uses these RFC 7592 credentials:

```bash
# RFC 7592 Management Credentials (set automatically during registration)
MCP_CLIENT_REGISTRATION_TOKEN=<bearer-token>  # For authentication
MCP_CLIENT_REGISTRATION_URI=<management-uri>  # Endpoint for operations
```

These are automatically saved to `.env` when you register or refresh tokens.

## Security Model

### Bearer Token Authentication

All RFC 7592 operations require the `registration_access_token`:
- Provided only once during initial registration
- Must be stored securely (automatically saved to `.env`)
- Grants full control over the client registration
- Cannot be recovered if lost

### Error Handling

The client handles these RFC 7592 errors gracefully:
- **401 Unauthorized** - Invalid or missing token
- **403 Forbidden** - Token lacks permissions
- **404 Not Found** - Client registration doesn't exist (may have expired)

## Usage Examples

### Complete Lifecycle Example

```bash
# 1. Register new client (gets RFC 7592 credentials)
mcp-streamablehttp-client --token

# 2. Check current registration
mcp-streamablehttp-client --get-client-info

# 3. Update client name and scope
mcp-streamablehttp-client --update-client "client_name=Production Client,scope=read write"

# 4. Verify changes
mcp-streamablehttp-client --get-client-info

# 5. Delete when no longer needed
mcp-streamablehttp-client --delete-client
```

### Checking Registration Status

```bash
# View token and registration status
mcp-streamablehttp-client --token
```

This shows:
- OAuth endpoint configuration
- Client registration status
- RFC 7592 management capability
- Access token validity
- Refresh token availability

### Handling Expired Clients

If your client registration expires:

```bash
# Check if client still exists
mcp-streamablehttp-client --get-client-info

# If 404 error, re-register
mcp-streamablehttp-client --reset-auth
mcp-streamablehttp-client --token
```

## Integration with Existing Workflows

The RFC 7592 functionality integrates seamlessly:

1. **Automatic Credential Storage** - Management tokens saved to `.env` during registration
2. **Token Refresh Compatible** - Client updates don't affect OAuth tokens
3. **Error Recovery** - Clear error messages guide recovery actions
4. **Backward Compatible** - Works with clients registered before RFC 7592 support

## Best Practices

1. **Backup Management Tokens** - The `registration_access_token` cannot be recovered
2. **Regular Status Checks** - Use `--get-client-info` to verify registration health
3. **Update Carefully** - Some updates may require re-authentication
4. **Monitor Expiration** - Check `client_secret_expires_at` regularly

## Implementation Details

The implementation follows RFC 7592 specifications exactly:
- Bearer token authentication via `Authorization` header
- RESTful operations on `registration_client_uri`
- Proper HTTP status codes and error responses
- Atomic updates with full response echoing

For developers integrating this functionality, see the `OAuthClient` class methods:
- `get_client_configuration()`
- `update_client_configuration(updates: dict)`
- `delete_client_registration()`

All methods handle errors gracefully and update local state appropriately.