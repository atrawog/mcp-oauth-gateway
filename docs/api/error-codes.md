# Error Codes

This reference documents all error codes returned by the MCP OAuth Gateway, including OAuth 2.1 errors and MCP-specific errors.

## OAuth 2.1 Error Codes

### Authorization Endpoint Errors

These errors are returned to the redirect_uri with error parameters:

| Error Code | Description | Example Scenario |
|------------|-------------|------------------|
| `invalid_request` | Request missing required parameters | Missing `response_type` parameter |
| `unauthorized_client` | Client not authorized for this grant type | Public client using `client_credentials` |
| `access_denied` | User denied authorization | User clicked "Deny" on consent |
| `unsupported_response_type` | Invalid response_type value | Using deprecated `token` type |
| `invalid_scope` | Requested scope invalid or unknown | Requesting non-existent scope |
| `server_error` | Server encountered unexpected error | Database connection failed |
| `temporarily_unavailable` | Server temporarily overloaded | Rate limit exceeded |

Example redirect:
```
https://client.example.com/callback?error=access_denied&error_description=User+denied+access
```

### Token Endpoint Errors

These errors are returned as JSON with HTTP 400/401:

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| `invalid_request` | Malformed request | 400 |
| `invalid_client` | Client authentication failed | 401 |
| `invalid_grant` | Invalid or expired authorization code | 400 |
| `unauthorized_client` | Client not authorized for grant type | 400 |
| `unsupported_grant_type` | Grant type not supported | 400 |
| `invalid_scope` | Requested scope exceeds granted scope | 400 |

Example response:
```json
{
  "error": "invalid_grant",
  "error_description": "Authorization code expired"
}
```

### Registration Endpoint Errors (RFC 7591)

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| `invalid_client_metadata` | Invalid registration parameters | 400 |
| `invalid_redirect_uri` | Redirect URI validation failed | 400 |
| `invalid_software_statement` | Software statement validation failed | 400 |

## MCP Protocol Error Codes

### JSON-RPC Standard Errors

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid Request | Not a valid JSON-RPC request |
| -32601 | Method not found | Method does not exist |
| -32602 | Invalid params | Invalid method parameters |
| -32603 | Internal error | Internal JSON-RPC error |

### MCP-Specific Errors

| Code | Message | Description |
|------|---------|-------------|
| -32001 | Not initialized | Session not initialized |
| -32002 | Session expired | Session has timed out |
| -32003 | Rate limit exceeded | Too many requests |
| -32004 | Resource not found | Requested resource missing |
| -32005 | Permission denied | Insufficient permissions |
| -32006 | Invalid session | Session ID invalid or not found |
| -32007 | Capability not supported | Service doesn't support capability |
| -32008 | Operation cancelled | Operation was cancelled |
| -32009 | Resource locked | Resource is locked by another operation |
| -32010 | Quota exceeded | Storage or operation quota exceeded |

Example MCP error:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "Not initialized",
    "data": {
      "detail": "Must call initialize before other methods"
    }
  },
  "id": "request-123"
}
```

## HTTP Status Codes

### Success Codes

| Status | Description | Usage |
|--------|-------------|-------|
| 200 OK | Request succeeded | Normal responses |
| 201 Created | Resource created | Client registration |
| 204 No Content | Success, no body | DELETE operations |

### Client Error Codes

| Status | Description | Common Causes |
|--------|-------------|---------------|
| 400 Bad Request | Invalid request syntax | Malformed JSON, missing params |
| 401 Unauthorized | Authentication required | Missing/invalid Bearer token |
| 403 Forbidden | Access denied | User not in whitelist |
| 404 Not Found | Resource not found | Invalid endpoint/client_id |
| 405 Method Not Allowed | HTTP method not supported | GET on POST-only endpoint |
| 409 Conflict | Request conflicts with state | Duplicate registration |
| 429 Too Many Requests | Rate limit exceeded | Too many requests |

### Server Error Codes

| Status | Description | Common Causes |
|--------|-------------|---------------|
| 500 Internal Server Error | Unexpected server error | Unhandled exception |
| 502 Bad Gateway | Invalid upstream response | Service unavailable |
| 503 Service Unavailable | Service temporarily down | Maintenance mode |
| 504 Gateway Timeout | Upstream timeout | MCP service timeout |

## Error Response Format

### OAuth Error Response

```json
{
  "error": "invalid_grant",
  "error_description": "The provided authorization code is invalid or has expired",
  "error_uri": "https://gateway.example.com/docs/errors#invalid_grant"
}
```

### MCP Error Response

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "param": "url",
      "reason": "URL must be absolute",
      "value": "example.com"
    }
  },
  "id": "request-id"
}
```

### HTTP Error Response

```json
{
  "error": {
    "type": "rate_limit_error",
    "message": "Rate limit exceeded",
    "code": "too_many_requests",
    "details": {
      "limit": 100,
      "remaining": 0,
      "reset": 1642444800
    }
  }
}
```

## Common Error Scenarios

### Authentication Errors

#### Expired Token
```json
{
  "error": "invalid_token",
  "error_description": "Access token expired",
  "www_authenticate": "Bearer error=\"invalid_token\""
}
```

#### Invalid Signature
```json
{
  "error": "invalid_token",
  "error_description": "Token signature verification failed"
}
```

### Authorization Errors

#### User Not Allowed
```json
{
  "error": "access_denied",
  "error_description": "User not in allowed users list"
}
```

#### Invalid Scope
```json
{
  "error": "insufficient_scope",
  "error_description": "Token does not have required scope"
}
```

### MCP Protocol Errors

#### Not Initialized
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "Not initialized",
    "data": {
      "hint": "Call initialize method first"
    }
  }
}
```

#### Method Not Found
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": {
      "method": "unknownMethod",
      "available": ["fetch", "search"]
    }
  }
}
```

## Error Handling Best Practices

### Client-Side Handling

```python
try:
    response = await client.post("/mcp", json=request)
    response.raise_for_status()
    result = response.json()

    if "error" in result:
        handle_mcp_error(result["error"])
    else:
        process_result(result["result"])

except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        # Refresh token and retry
        await refresh_token()
    elif e.response.status_code == 429:
        # Rate limited, wait and retry
        await asyncio.sleep(60)
    else:
        # Log and handle other errors
        logger.error(f"HTTP error: {e}")
```

### Retry Strategy

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(httpx.HTTPStatusError)
)
async def call_mcp_service(method, params):
    # Implementation with automatic retry
    pass
```

### Error Logging

```python
def log_error(error_response):
    logger.error(
        "MCP Error",
        extra={
            "error_code": error_response.get("code"),
            "error_message": error_response.get("message"),
            "request_id": error_response.get("id"),
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

## Troubleshooting Guide

### By Error Code

| If you see... | Check... | Try... |
|---------------|----------|--------|
| `invalid_client` | Client ID/secret | Verify credentials in .env |
| `invalid_grant` | Authorization code | Ensure code used within 1 minute |
| `unauthorized` | Bearer token | Check token not expired |
| `-32001` | Initialization | Call initialize first |
| `429` | Rate limits | Implement backoff |

### Debug Headers

Include these headers for debugging:

```http
X-Request-Id: unique-request-id
X-Debug-Mode: true
```

Response will include:

```http
X-Request-Id: unique-request-id
X-Error-Details: detailed-error-info
X-Rate-Limit-Remaining: 95
```

## Related Documentation

- [OAuth Endpoints](oauth-endpoints.md) - OAuth flow details
- [MCP Endpoints](mcp-endpoints.md) - MCP protocol details
- [Monitoring](../usage/monitoring.md) - Error tracking
