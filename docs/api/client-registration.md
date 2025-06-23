# Client Registration

The MCP OAuth Gateway implements RFC 7591 (Dynamic Client Registration) and RFC 7592 (Client Management) for secure client registration and lifecycle management.

## Overview

Dynamic client registration allows MCP clients (like Claude.ai) to register themselves with the gateway without manual configuration. This provides:

- Automatic client onboarding
- Secure credential generation
- Client lifecycle management
- Metadata storage

## Registration Flow

### 1. Initial Registration (RFC 7591)

```http
POST /register
Content-Type: application/json

{
  "redirect_uris": ["https://claude.ai/oauth/callback"],
  "client_name": "Claude Desktop",
  "client_uri": "https://claude.ai",
  "grant_types": ["authorization_code"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "none",
  "software_id": "claude-desktop-1.0",
  "software_version": "1.0.0"
}
```

### 2. Registration Response

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "client_id": "s6BhdRkqt3",
  "client_secret": "7Fjfp0ZBr1KtDRbnfVdmIw",
  "client_secret_expires_at": 1735689600,
  "registration_access_token": "this-is-a-bearer-token",
  "registration_client_uri": "https://auth.gateway.com/register/s6BhdRkqt3",
  "client_name": "Claude Desktop",
  "redirect_uris": ["https://claude.ai/oauth/callback"],
  "grant_types": ["authorization_code"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "none"
}
```

## Client Management (RFC 7592)

### Read Registration

```http
GET /register/{client_id}
Authorization: Bearer {registration_access_token}
```

### Update Registration

```http
PUT /register/{client_id}
Authorization: Bearer {registration_access_token}
Content-Type: application/json

{
  "client_name": "Claude Desktop Updated",
  "redirect_uris": ["https://claude.ai/oauth/callback", "https://claude.ai/oauth/callback2"]
}
```

### Delete Registration

```http
DELETE /register/{client_id}
Authorization: Bearer {registration_access_token}
```

## Registration Parameters

### Required Parameters

- **redirect_uris** - Array of redirect URIs for OAuth callbacks
- **grant_types** - OAuth grant types (must include "authorization_code")

### Optional Parameters

- **client_name** - Human-readable client name
- **client_uri** - Client homepage URL
- **logo_uri** - Client logo URL
- **contacts** - Array of contact emails
- **tos_uri** - Terms of service URL
- **policy_uri** - Privacy policy URL
- **software_id** - Unique software identifier
- **software_version** - Software version string

### MCP-Specific Parameters

- **mcp_version** - Supported MCP protocol version
- **mcp_capabilities** - Array of MCP capabilities

## Client Credentials

### Public Clients

For browser-based or mobile clients:

```json
{
  "token_endpoint_auth_method": "none",
  "grant_types": ["authorization_code"],
  "response_types": ["code"]
}
```

### Confidential Clients

For server-side applications:

```json
{
  "token_endpoint_auth_method": "client_secret_basic",
  "grant_types": ["authorization_code", "client_credentials"],
  "response_types": ["code"]
}
```

## Client Lifetime

### Default Behavior

- Clients expire after 90 days
- Configurable via `CLIENT_LIFETIME` environment variable
- Expiry time in `client_secret_expires_at` field

### Eternal Clients

Set `CLIENT_LIFETIME=0` for non-expiring clients:

```bash
# In .env
CLIENT_LIFETIME=0  # Clients never expire
```

## Security Considerations

### Registration Access Token

- **Purpose**: Manages specific client registration
- **Scope**: Limited to single client
- **Storage**: Keep secure, not recoverable if lost
- **Usage**: Required for all management operations

### Client Authentication

Public clients (no secret):
- Must use PKCE for authorization
- Cannot use client_credentials grant

Confidential clients:
- Authenticate with client_secret
- Support multiple grant types

### Validation Rules

1. **Redirect URI Validation**
   - Must be absolute URIs
   - HTTPS required (except localhost)
   - No wildcards in production

2. **Client Metadata**
   - Client name limited to 255 characters
   - URIs must be valid and accessible
   - Software ID should be unique

## Examples

### Claude.ai Registration

```python
import requests

# Register Claude as a client
response = requests.post(
    "https://auth.gateway.com/register",
    json={
        "client_name": "Claude Desktop",
        "redirect_uris": ["https://claude.ai/oauth/callback"],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
        "software_id": "claude-desktop",
        "software_version": "2024.1"
    }
)

registration = response.json()
client_id = registration["client_id"]
access_token = registration["registration_access_token"]
```

### Client Update

```python
# Update client registration
response = requests.put(
    f"https://auth.gateway.com/register/{client_id}",
    headers={"Authorization": f"Bearer {access_token}"},
    json={
        "client_name": "Claude Desktop Pro",
        "redirect_uris": [
            "https://claude.ai/oauth/callback",
            "claude://oauth/callback"
        ]
    }
)
```

### Client Deletion

```python
# Delete client registration
response = requests.delete(
    f"https://auth.gateway.com/register/{client_id}",
    headers={"Authorization": f"Bearer {access_token}"}
)
```

## Error Responses

### Invalid Client Metadata

```json
{
  "error": "invalid_client_metadata",
  "error_description": "The redirect_uri is not valid"
}
```

### Unauthorized Access

```json
{
  "error": "unauthorized",
  "error_description": "Invalid registration access token"
}
```

### Client Not Found

```json
{
  "error": "not_found",
  "error_description": "Client does not exist"
}
```

## Best Practices

1. **Store Registration Token** - Keep `registration_access_token` secure
2. **Monitor Expiration** - Track `client_secret_expires_at`
3. **Use HTTPS** - All redirect URIs must use HTTPS
4. **Validate Metadata** - Ensure all URIs are valid
5. **Implement Rotation** - Plan for client credential rotation
6. **Log Registration** - Audit all registration events

## Related Topics

- [OAuth Endpoints](oauth-endpoints.md) - OAuth flow details
- [Error Codes](error-codes.md) - Complete error reference
- [Security Architecture](../architecture/security.md) - Security details