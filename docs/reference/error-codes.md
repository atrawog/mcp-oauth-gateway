# Error Codes Reference

Complete reference for error codes returned by the MCP OAuth Gateway services.

## OAuth 2.1 Error Codes (RFC 6749)

### Authorization Endpoint Errors

#### `invalid_request`
**HTTP Status**: 400 Bad Request  
**Description**: The request is missing a required parameter, includes an invalid parameter value, includes a parameter more than once, or is otherwise malformed.

**Common Causes**:
- Missing `client_id` parameter
- Missing `response_type` parameter
- Invalid redirect URI format

**Example Response**:
```json
{
  "error": "invalid_request",
  "error_description": "Missing required parameter: client_id",
  "error_uri": "https://docs.oauth.com/errors#invalid_request"
}
```

#### `unauthorized_client`
**HTTP Status**: 400 Bad Request  
**Description**: The client is not authorized to request an authorization code using this method.

**Common Causes**:
- Client ID not found in registrations
- Client not allowed for authorization code flow
- Expired client registration

#### `access_denied`
**HTTP Status**: 400 Bad Request  
**Description**: The resource owner or authorization server denied the request.

**Common Causes**:
- User not in `ALLOWED_GITHUB_USERS` list
- GitHub OAuth was cancelled
- User denied permission

#### `unsupported_response_type`
**HTTP Status**: 400 Bad Request  
**Description**: The authorization server does not support obtaining an authorization code using this method.

**Common Causes**:
- Using unsupported response type (only `code` supported)
- Malformed response_type parameter

#### `invalid_scope`
**HTTP Status**: 400 Bad Request  
**Description**: The requested scope is invalid, unknown, or malformed.

**Common Causes**:
- Requesting unsupported scopes
- Malformed scope parameter

#### `server_error`
**HTTP Status**: 500 Internal Server Error  
**Description**: The authorization server encountered an unexpected condition.

### Token Endpoint Errors

#### `invalid_request`
**HTTP Status**: 400 Bad Request  
**Description**: The request is missing a required parameter, includes an unsupported parameter value, includes a parameter more than once, or is otherwise malformed.

**Common Causes**:
- Missing authorization code
- Missing PKCE code verifier
- Invalid grant type

#### `invalid_client`
**HTTP Status**: 401 Unauthorized  
**Description**: Client authentication failed.

**Headers**: `WWW-Authenticate: Bearer`

**Common Causes**:
- Invalid client ID
- Client secret mismatch (for confidential clients)
- Expired client registration

#### `invalid_grant`
**HTTP Status**: 400 Bad Request  
**Description**: The provided authorization grant is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client.

**Common Causes**:
- Expired authorization code
- Code already used (replay attack)
- PKCE verification failure
- Mismatched redirect URI

#### `unauthorized_client`
**HTTP Status**: 400 Bad Request  
**Description**: The authenticated client is not authorized to use this authorization grant type.

#### `unsupported_grant_type`
**HTTP Status**: 400 Bad Request  
**Description**: The authorization grant type is not supported by the authorization server.

**Common Causes**:
- Using unsupported grant type
- Requesting refresh token flow when not supported

#### `invalid_scope`
**HTTP Status**: 400 Bad Request  
**Description**: The requested scope is invalid, unknown, malformed, or exceeds the scope granted by the resource owner.

## RFC 7591 Client Registration Errors

### Registration Endpoint Errors

#### `invalid_redirect_uri`
**HTTP Status**: 400 Bad Request  
**Description**: The redirect_uri in the client metadata is invalid.

**Common Causes**:
- Non-HTTPS redirect URI (except localhost)
- Invalid URI format
- Forbidden redirect URI patterns

#### `invalid_client_metadata`
**HTTP Status**: 400 Bad Request  
**Description**: The client metadata is invalid or malformed.

**Common Causes**:
- Invalid JSON in request body
- Unsupported grant types
- Invalid client name

#### `invalid_software_statement`
**HTTP Status**: 400 Bad Request  
**Description**: The software statement is invalid (if supported).

#### `unapproved_software_statement`
**HTTP Status**: 400 Bad Request  
**Description**: The software statement is not approved (if software statements are supported).

## RFC 7592 Client Management Errors

### Client Configuration Endpoint Errors

#### `invalid_client_id`
**HTTP Status**: 404 Not Found  
**Description**: The client identifier is invalid or not found.

#### `invalid_token`
**HTTP Status**: 401 Unauthorized  
**Description**: The registration access token is invalid, expired, or malformed.

**Headers**: `WWW-Authenticate: Bearer`

**Common Causes**:
- Expired registration access token
- Malformed Bearer token
- Token not found in storage

#### `insufficient_scope`
**HTTP Status**: 403 Forbidden  
**Description**: The registration access token doesn't have sufficient scope for the requested operation.

## MCP Protocol Errors (2025-06-18)

### Protocol-Level Errors

#### `method_not_found`
**JSON-RPC Error Code**: -32601  
**Description**: The requested MCP method is not supported by the server.

**Example Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": {
      "method": "unsupported/method"
    }
  }
}
```

#### `invalid_params`
**JSON-RPC Error Code**: -32602  
**Description**: Invalid method parameters provided.

#### `internal_error`
**JSON-RPC Error Code**: -32603  
**Description**: Internal server error in MCP server.

#### `parse_error`
**JSON-RPC Error Code**: -32700  
**Description**: Invalid JSON was received by the server.

#### `invalid_request`
**JSON-RPC Error Code**: -32600  
**Description**: The JSON sent is not a valid Request object.

### MCP-Specific Errors

#### `protocol_version_mismatch`
**JSON-RPC Error Code**: -32000  
**Description**: Client and server protocol versions are incompatible.

**Example Response**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32000,
    "message": "Protocol version mismatch",
    "data": {
      "client_version": "2025-01-01",
      "server_version": "2025-06-18"
    }
  }
}
```

#### `session_not_found`
**JSON-RPC Error Code**: -32001  
**Description**: The session ID is invalid or expired.

#### `initialization_required`
**JSON-RPC Error Code**: -32002  
**Description**: Client must send initialize request before other operations.

#### `tool_not_found`
**JSON-RPC Error Code**: -32003  
**Description**: The requested tool is not available.

#### `resource_not_found`
**JSON-RPC Error Code**: -32004  
**Description**: The requested resource is not available.

## HTTP Status Codes

### Success Codes

| Code | Status | Usage |
|------|--------|-------|
| 200 | OK | Successful GET, POST (non-creation) |
| 201 | Created | Successful client registration |
| 204 | No Content | Successful DELETE operations |

### Client Error Codes

| Code | Status | Usage |
|------|--------|-------|
| 400 | Bad Request | Malformed requests, validation errors |
| 401 | Unauthorized | Authentication required/failed |
| 403 | Forbidden | Valid auth but insufficient permissions |
| 404 | Not Found | Resource not found |
| 405 | Method Not Allowed | HTTP method not supported |
| 429 | Too Many Requests | Rate limiting |

### Server Error Codes

| Code | Status | Usage |
|------|--------|-------|
| 500 | Internal Server Error | Unexpected server errors |
| 502 | Bad Gateway | Upstream service errors |
| 503 | Service Unavailable | Service temporarily down |
| 504 | Gateway Timeout | Upstream timeout |

## Authentication Errors

### Bearer Token Errors

#### Missing Authorization Header
**HTTP Status**: 401 Unauthorized  
**Headers**: `WWW-Authenticate: Bearer`

```json
{
  "error": "missing_authorization",
  "error_description": "Authorization header is required"
}
```

#### Invalid Bearer Token Format
**HTTP Status**: 401 Unauthorized  
**Headers**: `WWW-Authenticate: Bearer`

```json
{
  "error": "invalid_token_format",
  "error_description": "Authorization header must be in format 'Bearer <token>'"
}
```

#### Expired Access Token
**HTTP Status**: 401 Unauthorized  
**Headers**: `WWW-Authenticate: Bearer`

```json
{
  "error": "token_expired",
  "error_description": "The access token has expired",
  "error_uri": "https://auth.yourdomain.com/token"
}
```

#### Invalid Token Signature
**HTTP Status**: 401 Unauthorized  
**Headers**: `WWW-Authenticate: Bearer`

```json
{
  "error": "invalid_token",
  "error_description": "Token signature verification failed"
}
```

### ForwardAuth Errors

#### Auth Service Unreachable
**HTTP Status**: 502 Bad Gateway

```json
{
  "error": "auth_service_error",
  "error_description": "Authentication service is temporarily unavailable"
}
```

#### Auth Service Timeout
**HTTP Status**: 504 Gateway Timeout

```json
{
  "error": "auth_timeout", 
  "error_description": "Authentication verification timed out"
}
```

## Service-Specific Errors

### Redis Connection Errors

#### Redis Unavailable
**HTTP Status**: 503 Service Unavailable

```json
{
  "error": "storage_unavailable",
  "error_description": "Token storage service is temporarily unavailable"
}
```

### GitHub OAuth Errors

#### GitHub Service Error
**HTTP Status**: 502 Bad Gateway

```json
{
  "error": "github_error",
  "error_description": "GitHub OAuth service returned an error",
  "error_details": "GitHub error message"
}
```

#### Invalid GitHub Code
**HTTP Status**: 400 Bad Request

```json
{
  "error": "invalid_authorization_code",
  "error_description": "The authorization code from GitHub is invalid or expired"
}
```

## Error Response Format

### OAuth 2.1 Error Response
```json
{
  "error": "error_code",
  "error_description": "Human-readable description",
  "error_uri": "https://docs.example.com/oauth-errors#error_code",
  "state": "client_state_value"
}
```

### MCP JSON-RPC Error Response
```json
{
  "jsonrpc": "2.0",
  "id": "request_id",
  "error": {
    "code": -32000,
    "message": "Error message",
    "data": {
      "additional": "context"
    }
  }
}
```

### HTTP API Error Response
```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable message",
    "details": {
      "field": "Additional context"
    }
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "req_123456"
}
```

## Debugging Error Responses

### Enable Debug Mode
```bash
# View detailed error logs
just logs-follow

# Check specific service logs
docker logs mcp-oauth-gateway-auth-1

# Analyze OAuth error patterns
just analyze-oauth-logs
```

### Common Debugging Steps

1. **Check Service Health**:
   ```bash
   just check-health
   ```

2. **Verify Configuration**:
   ```bash
   just validate-tokens
   ```

3. **Check Token Expiry**:
   ```bash
   just check-token-expiry
   ```

4. **View OAuth Data**:
   ```bash
   just oauth-show-all
   ```

### Error Recovery

#### Token Issues
```bash
# Regenerate expired tokens
just generate-github-token

# Clean up invalid tokens
just oauth-purge-expired
```

#### Client Registration Issues
```bash
# List problematic registrations
just oauth-list-registrations

# Clean up test registrations
just test-cleanup
```

#### Service Issues
```bash
# Restart specific service
just rebuild auth

# Full restart
just up-fresh
```

[Error codes reference - complete list with descriptions and troubleshooting]