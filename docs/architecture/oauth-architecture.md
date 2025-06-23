# OAuth Architecture Explained

This document clarifies the OAuth architecture of the MCP OAuth Gateway and how it adds authentication to any MCP server without code modification.

```{important}
**Reference Implementation Warning**

The MCP OAuth Gateway is a reference implementation and test platform for:
- Exploring MCP protocol authentication patterns
- Testing future MCP protocol iterations
- Demonstrating OAuth integration possibilities

While we implement security best practices, this codebase:
- Is experimental and likely contains security vulnerabilities
- Should undergo thorough security review before any production use
- May change significantly as the MCP protocol evolves
- Is intended primarily for development and testing purposes
```

## OAuth Terminology

Understanding the OAuth roles is crucial:

- **Resource Owner**: The end user who owns the data
- **Client**: The application requesting access (e.g., Claude.ai)
- **Authorization Server (AS)**: Issues tokens after authentication (MCP OAuth Gateway)
- **Resource Server (RS)**: The API holding protected data (MCP servers)
- **Identity Provider (IdP)**: Verifies user identity (GitHub OAuth)

## Architecture Overview

```{mermaid}
graph TB
    subgraph "OAuth Clients"
        C1[Claude.ai]
        C2[VS Code Extension]
        C3[Other MCP Clients]
    end
    
    subgraph "MCP OAuth Gateway (Authorization Server)"
        AS[Auth Service]
        T[Traefik Router]
        R[Redis Storage]
    end
    
    subgraph "Identity Provider"
        GH[GitHub OAuth]
    end
    
    subgraph "Protected Resources"
        MCP1[MCP Fetch Server]
        MCP2[MCP Time Server]
        MCP3[Any MCP Server]
    end
    
    C1 --> T
    C2 --> T
    C3 --> T
    T --> AS
    AS --> R
    AS --> GH
    T --> MCP1
    T --> MCP2
    T --> MCP3
```

## Key Architectural Decisions

### 1. Gateway as Authorization Server

The MCP OAuth Gateway **is** the Authorization Server, not just a proxy:

- **Issues its own tokens**: The gateway creates and signs JWT access tokens
- **Manages client registrations**: Implements RFC 7591 for dynamic registration (REQUIRED by MCP 2025-06-18)
- **RFC 7592 Extension**: Implements RFC 7592 client management (NOT part of MCP 2025-06-18 spec!)
- **Validates all requests**: Every MCP request goes through token validation
- **Controls access**: Determines which users can access which resources

### 2. GitHub as Identity Provider Only

GitHub OAuth serves a specific, limited role:

- **User authentication only**: GitHub verifies user identity
- **Not for client auth**: MCP clients never talk to GitHub directly
- **Identity claims**: Provides user profile (name, email, etc.)
- **Access control**: Gateway checks GitHub username against allowlist

### 3. Zero Code Modification for MCP Servers

The gateway protects MCP servers without any changes:

```yaml
# Before: Unprotected MCP server
mcp-server:
  command: npx @modelcontextprotocol/server-fetch

# After: OAuth-protected MCP server
mcp-server:
  image: atrawog/mcp-streamablehttp-proxy:latest
  environment:
    - SERVER_COMMAND=npx @modelcontextprotocol/server-fetch
  labels:
    - "traefik.http.middlewares.mcp-auth.forwardauth.address=http://auth:8000/verify"
```

## OAuth Flow Walkthrough

### Step 1: Client Registration (RFC 7591)

```http
POST /register HTTP/1.1
Host: auth.example.com
Content-Type: application/json

{
  "redirect_uris": ["https://claude.ai/oauth/callback"],
  "client_name": "Claude Desktop",
  "grant_types": ["authorization_code"],
  "response_types": ["code"]
}
```

Response:
```json
{
  "client_id": "7891011",
  "client_secret": "secret123",
  "registration_access_token": "reg.token.xyz",
  "registration_client_uri": "https://auth.example.com/register/7891011"
}
```

### Step 2: User Authorization

1. **Client redirects to gateway**:
   ```
   https://auth.example.com/authorize?
     client_id=7891011&
     redirect_uri=https://claude.ai/oauth/callback&
     response_type=code&
     code_challenge=challenge123&
     code_challenge_method=S256
   ```

2. **Gateway redirects to GitHub**:
   ```
   https://github.com/login/oauth/authorize?
     client_id=github_client_id&
     redirect_uri=https://auth.example.com/callback
   ```

3. **User authenticates with GitHub**

4. **GitHub redirects back with code**

5. **Gateway validates user and issues authorization code**

### Step 3: Token Exchange

```http
POST /token HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=auth_code_123&
client_id=7891011&
client_secret=secret123&
code_verifier=verifier123
```

Response:
```json
{
  "access_token": "eyJhbGc...",  // Gateway-issued JWT
  "token_type": "Bearer",
  "expires_in": 86400,
  "refresh_token": "refresh_xyz"
}
```

### Step 4: Accessing Protected Resources

```http
POST /mcp HTTP/1.1
Host: mcp-fetch.example.com
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "fetch",
  "params": {"url": "https://example.com"},
  "id": 1
}
```

## Token Lifecycle

### Access Token (Gateway-Issued JWT)

```json
{
  "sub": "user123",
  "aud": "mcp-gateway",
  "iss": "https://auth.example.com",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "unique-token-id",
  "github_username": "johndoe",
  "client_id": "7891011"
}
```

- **Issued by**: MCP OAuth Gateway
- **Validated by**: Auth Service on every request
- **Contains**: User identity from GitHub + client information
- **Lifetime**: Configurable (default 24 hours)

### Refresh Token

- **Purpose**: Get new access tokens without re-authentication
- **Storage**: Redis with configurable TTL
- **Security**: Bound to specific client + user combination

## Security Benefits

### 1. Complete OAuth Compliance
- RFC 6749 (OAuth 2.0) core
- RFC 7636 (PKCE) for public clients
- RFC 7591 (Dynamic Registration)
- RFC 7592 (Client Management)
- RFC 8414 (Authorization Server Metadata)

### 2. Defense in Depth
- **Layer 1**: Traefik routes and enforces auth
- **Layer 2**: Auth Service validates tokens
- **Layer 3**: MCP services run in isolation

### 3. Zero Trust Architecture
- Every request validated
- No implicit trust between services
- Tokens expire and must be refreshed

### 4. Flexible Access Control
- Per-user access via GitHub username allowlist
- Per-client access via registration
- Per-resource access via token claims

## Common Misconceptions

### ❌ "The gateway just proxies to GitHub OAuth"
**✅ Reality**: The gateway IS the OAuth server. It uses GitHub only for user identity verification.

### ❌ "MCP servers need OAuth support"
**✅ Reality**: MCP servers run completely unmodified. The proxy layer handles all HTTP/OAuth concerns.

### ❌ "Clients authenticate directly with GitHub"
**✅ Reality**: Clients only interact with the gateway's OAuth endpoints. GitHub is invisible to them.

### ❌ "It's just a reverse proxy with auth"
**✅ Reality**: It's a complete OAuth 2.1 Authorization Server with token issuance, client management, and session handling.

## Summary

The MCP OAuth Gateway is a complete OAuth 2.1 Authorization Server that:

1. **Acts as the Authorization Server** for MCP clients
2. **Uses GitHub as Identity Provider** for user authentication only
3. **Protects any MCP server** without code modifications
4. **Implements full OAuth standards** compliance
5. **Provides enterprise-grade security** for MCP deployments

This architecture allows organizations to add robust authentication to their MCP infrastructure without modifying any MCP server code, while leveraging GitHub's trusted identity system for user verification.