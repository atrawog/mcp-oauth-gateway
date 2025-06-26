# RFC 7592 Implementation Details

This document provides a comprehensive overview of how RFC 7592 (OAuth 2.0 Dynamic Client Registration Management Protocol) is implemented in the MCP OAuth Gateway.

## Overview

The gateway implements RFC 7592 with complete separation between registration access tokens and OAuth access tokens, ensuring proper security boundaries and preventing token confusion attacks.

## Implementation Architecture

### Token Generation

Registration access tokens are generated during client registration:

```python
# In routes.py, line 167
registration_access_token = f"reg-{secrets.token_urlsafe(32)}"
```

**Key characteristics:**
- Format: `reg-{32-byte-random-value}`
- Entropy: 32 bytes (256 bits) of cryptographic randomness
- Generation: Uses Python's `secrets.token_urlsafe()` for secure random generation
- Uniqueness: Each client receives a unique token at registration

### Token Storage

Registration tokens are stored as part of the client data in Redis:

```python
# Redis key pattern
oauth:client:{client_id}

# Stored data includes:
{
    "client_id": "...",
    "client_secret": "...",
    "registration_access_token": "reg-xxx...",  # The RFC 7592 token
    "redirect_uris": [...],
    # ... other client metadata
}
```

**Storage characteristics:**
- Location: Within client data object
- Key: `oauth:client:{client_id}`
- Lifetime: Matches client lifetime (90 days default, eternal if CLIENT_LIFETIME=0)
- No separate token storage - integrated with client data

### Authentication Mechanism

The `DynamicClientConfigurationEndpoint` class handles RFC 7592 authentication:

```python
# In rfc7592.py, lines 40-64
def authenticate_client(self, request: HTTPConnection, client_id: str) -> Optional[Dict[str, Any]]:
    """Authenticate a client using registration access token from RFC 7592."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]  # Remove "Bearer " prefix

    # Retrieve client from storage
    client_data = self.storage.get_client(client_id)
    if not client_data:
        raise ValueError(f"Client {client_id} not found")

    # Verify registration access token
    stored_token = client_data.get("registration_access_token")
    if not stored_token or not secrets.compare_digest(token, stored_token):
        return None

    return client_data
```

**Security features:**
- Uses `secrets.compare_digest()` for constant-time comparison
- Returns `None` for authentication failure (403 response)
- Raises `ValueError` for missing clients (404 response)
- No JWT validation - direct string comparison only

### Endpoint Implementation

#### GET /register/{client_id}

View client registration details:

```python
# Routes.py, lines 710-744
@router.get("/register/{client_id}")
async def get_client_configuration(client_id: str, request: Request):
    # Authenticate using registration access token
    client_data = config_endpoint.authenticate_client(request, client_id)

    # Return 404 if client not found
    # Return 401 if no auth header
    # Return 403 if invalid token
    # Return 200 with client data if successful
```

#### PUT /register/{client_id}

Update client registration:

```python
# Routes.py, lines 746-830
@router.put("/register/{client_id}")
async def update_client_configuration(client_id: str, request: Request):
    # Same authentication pattern
    # Allows updating: client_name, redirect_uris, etc.
    # Validates redirect URIs if changed
    # Returns updated client data
```

#### DELETE /register/{client_id}

Delete client registration:

```python
# Routes.py, lines 831-867
@router.delete("/register/{client_id}")
async def delete_client_configuration(client_id: str, request: Request):
    # Same authentication pattern
    # Removes client from Redis
    # Returns 204 No Content on success
```

## Security Enforcement

### Token Type Separation

The implementation enforces complete separation between token types:

1. **Registration Access Tokens**
   - Only accepted on `/register/{client_id}` endpoints
   - Validated by `DynamicClientConfigurationEndpoint`
   - Direct string comparison, no JWT processing

2. **OAuth Access Tokens**
   - Only accepted on resource endpoints
   - Validated by `verify_bearer_token` dependency
   - JWT signature and claims verification

### Test Coverage

The `test_rfc7592_security.py` file verifies this separation:

```python
def test_oauth_token_rejected_for_client_management():
    """Test that OAuth JWT tokens cannot access RFC 7592 endpoints."""
    # Attempts to use OAuth token on management endpoint
    # Expects 403 Forbidden response
    # Confirms token separation is enforced
```

## Common Misconceptions

### Misconception 1: OAuth tokens can manage clients

**Reality**: OAuth access tokens are explicitly rejected with 403 Forbidden when used on RFC 7592 endpoints.

### Misconception 2: Registration tokens are JWTs

**Reality**: Registration tokens are opaque strings with no internal structure, validated through direct comparison.

### Misconception 3: Registration tokens expire separately

**Reality**: Registration token lifetime is tied to client lifetime - they don't have independent expiration.

### Misconception 4: Lost tokens can be recovered

**Reality**: There is no token recovery mechanism. Lost registration tokens mean the client becomes permanently unmanageable.

## Best Practices

1. **Store tokens securely**: Registration access tokens should be stored with the same security as client secrets.

2. **Don't share tokens**: Each client's registration token should only be known to that specific client.

3. **Handle 403 correctly**: When receiving 403 on management endpoints, don't retry with the same token.

4. **Plan for token loss**: Implement a re-registration flow for cases where tokens are lost.

5. **Use correct headers**: Always use `Authorization: Bearer {registration_access_token}` format.

## Compliance Status

The implementation fully complies with RFC 7592:

- ✅ Separate authentication realm for client management
- ✅ Bearer token authentication scheme
- ✅ Proper HTTP status codes (401, 403, 404)
- ✅ Support for GET, PUT, DELETE operations
- ✅ Client metadata validation
- ✅ Registration token included in initial response

## References

- [RFC 7592](https://tools.ietf.org/html/rfc7592) - OAuth 2.0 Dynamic Client Registration Management Protocol
- [RFC 7591](https://tools.ietf.org/html/rfc7591) - OAuth 2.0 Dynamic Client Registration Protocol
- [Implementation](https://github.com/atrawog/mcp-oauth-gateway) - Source code
