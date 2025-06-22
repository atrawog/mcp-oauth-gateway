# MCP OAuth Dynamic Client

A production-ready Python library implementing OAuth 2.1 with RFC 7591 dynamic client registration and RFC 7592 client management, specifically designed for MCP (Model Context Protocol) applications.

```{image} https://img.shields.io/badge/RFC-7591%20%7C%207592-orange
:alt: RFC Compliant
```
```{image} https://img.shields.io/badge/OAuth-2.1-green
:alt: OAuth 2.1 Compliant
```
```{image} https://img.shields.io/badge/PKCE-S256-blue
:alt: PKCE S256 Support
```

## Overview

The MCP OAuth Dynamic Client provides a complete OAuth 2.1 implementation with emphasis on security, standards compliance, and ease of use. It handles the complex OAuth flows while providing a simple, intuitive API for MCP client applications.

## 🚀 Key Features

### OAuth 2.1 Compliance
- **RFC 6749** - OAuth 2.0 Authorization Framework
- **OAuth 2.1** - Modern security enhancements
- **PKCE S256** - Proof Key for Code Exchange (required)
- **JWT Tokens** - JSON Web Token support with validation

### Dynamic Client Management  
- **RFC 7591** - OAuth 2.0 Dynamic Client Registration
- **RFC 7592** - OAuth 2.0 Dynamic Client Registration Management
- **Automatic Registration** - Self-service client onboarding
- **Lifecycle Management** - Complete client lifecycle support

### Security Features
- **Token Security** - Secure token storage and refresh
- **State Validation** - CSRF protection with state parameters
- **Nonce Support** - Replay attack prevention
- **Secure Redirect** - Redirect URI validation

### Production Ready
- **Error Handling** - Comprehensive error handling and recovery
- **Retry Logic** - Automatic retry with exponential backoff
- **Rate Limiting** - Client-side rate limiting support
- **Logging** - Structured logging for debugging and monitoring

## 🛠️ Installation

### From PyPI (when published)

```bash
pip install mcp-oauth-dynamicclient
```

### From Source

```bash
# Clone repository
git clone https://github.com/atrawog/mcp-oauth-gateway.git
cd mcp-oauth-gateway/mcp-oauth-dynamicclient

# Install in development mode
pip install -e ".[dev]"
```

### With Optional Dependencies

```bash
# Install with all features
pip install "mcp-oauth-dynamicclient[cli,redis,jwt]"

# Development installation
pip install "mcp-oauth-dynamicclient[dev]"
```

## 📚 Quick Start

### Basic OAuth Flow

```python
from mcp_oauth_dynamicclient import OAuth2Client
import asyncio

async def main():
    # Initialize client
    client = OAuth2Client(
        auth_server="https://auth.yourdomain.com",
        client_name="My MCP Application",
        redirect_uris=["http://localhost:8080/callback"]
    )
    
    # Dynamic client registration
    registration = await client.register()
    print(f"Client ID: {registration.client_id}")
    
    # Start OAuth flow
    auth_url = await client.get_authorization_url(
        scope="mcp:read mcp:write"
    )
    print(f"Visit: {auth_url}")
    
    # Exchange authorization code for token
    # (authorization_code obtained from callback)
    token = await client.exchange_code(authorization_code)
    
    # Use token for authenticated requests
    response = await client.authenticated_request(
        "GET",
        "https://mcp-service.yourdomain.com/mcp",
        token=token
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### Token Management

```python
from mcp_oauth_dynamicclient import TokenManager

# Initialize token manager with storage
token_manager = TokenManager(
    storage_type="file",  # or "redis", "memory"
    storage_config={"path": "./tokens.json"}
)

# Store token
await token_manager.store_token("client_id", {
    "access_token": "...",
    "refresh_token": "...",
    "expires_at": 1640995200
})

# Retrieve and refresh if needed
token = await token_manager.get_valid_token("client_id")

# Automatic refresh
if token_manager.is_expired(token):
    refreshed = await token_manager.refresh_token("client_id")
```

### Client Configuration

```python
from mcp_oauth_dynamicclient import OAuth2Config

# Create configuration
config = OAuth2Config(
    auth_server="https://auth.yourdomain.com",
    client_name="My Application",
    client_uri="https://myapp.com",
    tos_uri="https://myapp.com/terms",
    policy_uri="https://myapp.com/privacy",
    redirect_uris=["https://myapp.com/callback"],
    scope="mcp:read mcp:write",
    
    # PKCE configuration
    use_pkce=True,
    code_challenge_method="S256",
    
    # Token configuration
    token_endpoint_auth_method="client_secret_basic",
    
    # Client lifetime (0 = eternal)
    client_lifetime=7776000  # 90 days
)

client = OAuth2Client(config=config)
```

## 🏗️ Architecture

### Component Architecture

```{mermaid}
graph TB
    subgraph "OAuth2Client"
        A[Registration Manager] --> B[Authorization Handler]
        B --> C[Token Manager]
        C --> D[Request Handler]
    end
    
    subgraph "Storage Layer"
        E[File Storage] 
        F[Redis Storage]
        G[Memory Storage]
    end
    
    subgraph "Security Layer"
        H[PKCE Generator]
        I[State Validator]
        J[JWT Validator]
    end
    
    C --> E
    C --> F  
    C --> G
    B --> H
    B --> I
    A --> J
```

### Flow Diagram

```{mermaid}
sequenceDiagram
    participant Client as OAuth2Client
    participant Auth as Auth Server
    participant Resource as MCP Service
    
    Client->>Auth: Dynamic Registration (RFC 7591)
    Auth-->>Client: Client Credentials
    
    Client->>Auth: Authorization Request + PKCE
    Auth-->>Client: Authorization Code
    
    Client->>Auth: Token Exchange + PKCE Verifier
    Auth-->>Client: Access Token + Refresh Token
    
    Client->>Resource: Authenticated Request
    Resource-->>Client: Protected Resource
    
    Note over Client,Auth: Token Refresh (when needed)
    Client->>Auth: Refresh Token
    Auth-->>Client: New Access Token
```

## 🔧 API Reference

### OAuth2Client Class

The main client class for OAuth operations.

#### Constructor

```python
OAuth2Client(
    auth_server: str = None,
    config: OAuth2Config = None,
    storage: TokenStorage = None,
    http_client: httpx.AsyncClient = None
)
```

**Parameters:**
- `auth_server` - Authorization server base URL
- `config` - OAuth2Config instance (alternative to individual params)
- `storage` - Custom token storage implementation
- `http_client` - Custom HTTP client instance

#### Registration Methods

##### register()
```python
async def register() -> ClientRegistration
```

Perform dynamic client registration per RFC 7591.

**Returns:** `ClientRegistration` with client_id, client_secret, and metadata

**Example:**
```python
registration = await client.register()
print(f"Registered client: {registration.client_id}")
```

##### get_client_info()
```python
async def get_client_info(client_id: str) -> dict
```

Retrieve client information per RFC 7592.

##### update_client()
```python
async def update_client(client_id: str, **updates) -> dict
```

Update client configuration per RFC 7592.

##### delete_client()
```python
async def delete_client(client_id: str) -> bool
```

Delete client registration per RFC 7592.

#### Authorization Methods

##### get_authorization_url()
```python
async def get_authorization_url(
    scope: str = None,
    state: str = None,
    **params
) -> str
```

Generate authorization URL with PKCE challenge.

**Parameters:**
- `scope` - Requested OAuth scopes
- `state` - CSRF protection state parameter
- `**params` - Additional authorization parameters

**Returns:** Authorization URL for user redirection

##### exchange_code()
```python
async def exchange_code(
    authorization_code: str,
    state: str = None
) -> TokenResponse
```

Exchange authorization code for access token.

**Parameters:**
- `authorization_code` - Code from authorization callback
- `state` - State parameter for validation

**Returns:** `TokenResponse` with tokens and metadata

#### Token Methods

##### refresh_token()
```python
async def refresh_token(refresh_token: str) -> TokenResponse
```

Refresh access token using refresh token.

##### revoke_token()
```python
async def revoke_token(token: str, token_type: str = "access_token") -> bool
```

Revoke access or refresh token.

##### validate_token()
```python
async def validate_token(token: str) -> dict
```

Validate token and return introspection data.

#### Request Methods

##### authenticated_request()
```python
async def authenticated_request(
    method: str,
    url: str,
    token: str = None,
    **kwargs
) -> httpx.Response
```

Make authenticated HTTP request with automatic token handling.

### Configuration Classes

#### OAuth2Config

Configuration container for OAuth parameters.

```python
@dataclass
class OAuth2Config:
    auth_server: str
    client_name: str
    client_uri: str = None
    redirect_uris: List[str] = None
    scope: str = "mcp:read"
    use_pkce: bool = True
    code_challenge_method: str = "S256"
    token_endpoint_auth_method: str = "client_secret_basic"
    client_lifetime: int = 7776000  # 90 days
```

#### ClientRegistration

Registration response data structure.

```python
@dataclass
class ClientRegistration:
    client_id: str
    client_secret: str
    client_secret_expires_at: int
    registration_access_token: str
    registration_client_uri: str
    redirect_uris: List[str]
    scope: str
    token_endpoint_auth_method: str
```

#### TokenResponse

Token response data structure.

```python
@dataclass
class TokenResponse:
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str = None
    scope: str = None
    id_token: str = None
```

### Storage Interface

#### TokenStorage

Abstract base class for token storage implementations.

```python
class TokenStorage:
    async def store_token(self, key: str, token: dict) -> None
    async def retrieve_token(self, key: str) -> dict
    async def delete_token(self, key: str) -> None
    async def list_tokens(self) -> List[str]
```

#### Built-in Storage Implementations

##### FileStorage
```python
from mcp_oauth_dynamicclient.storage import FileStorage

storage = FileStorage(path="./tokens.json")
```

##### RedisStorage
```python
from mcp_oauth_dynamicclient.storage import RedisStorage

storage = RedisStorage(
    host="localhost",
    port=6379,
    db=0,
    prefix="oauth_tokens:"
)
```

##### MemoryStorage
```python
from mcp_oauth_dynamicclient.storage import MemoryStorage

storage = MemoryStorage()  # In-memory only
```

## 🧪 Testing

### Test Suite

The package includes comprehensive tests covering all functionality:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/ --cov-report=html

# Run specific test categories
pytest tests/test_registration.py -v  # Registration tests
pytest tests/test_auth_flow.py -v     # Authorization tests
pytest tests/test_tokens.py -v        # Token management tests
pytest tests/test_storage.py -v       # Storage tests
```

### Test Categories

1. **Registration Tests** - RFC 7591/7592 compliance
2. **Authorization Tests** - OAuth 2.1 flow validation
3. **Token Tests** - Token lifecycle management
4. **PKCE Tests** - PKCE implementation validation
5. **Storage Tests** - Storage backend testing
6. **Integration Tests** - End-to-end flow testing
7. **Error Handling** - Exception and error scenarios
8. **Security Tests** - Security feature validation

### Mock vs Integration Testing

The package supports both mock and integration testing:

```python
# Mock testing for unit tests
from mcp_oauth_dynamicclient.testing import MockAuthServer

async def test_registration():
    mock_server = MockAuthServer()
    client = OAuth2Client(auth_server=mock_server.url)
    
    registration = await client.register()
    assert registration.client_id is not None

# Integration testing with real server
async def test_real_integration():
    client = OAuth2Client(auth_server="https://auth.example.com")
    # Test against real auth server
```

## 🔍 Monitoring and Logging

### Structured Logging

The package provides comprehensive logging:

```python
import logging
from mcp_oauth_dynamicclient import OAuth2Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_oauth_dynamicclient")

# Client automatically logs important events
client = OAuth2Client(auth_server="https://auth.example.com")
```

### Log Output Examples

```json
{
  "timestamp": "2025-06-21T23:38:12Z",
  "level": "INFO",
  "component": "OAuth2Client",
  "event": "client_registration",
  "client_id": "client_123",
  "auth_server": "https://auth.example.com"
}

{
  "timestamp": "2025-06-21T23:38:15Z", 
  "level": "INFO",
  "component": "TokenManager",
  "event": "token_refresh",
  "client_id": "client_123",
  "expires_in": 3600
}
```

### Metrics Collection

Optional metrics collection for monitoring:

```python
from mcp_oauth_dynamicclient.metrics import MetricsCollector

# Enable metrics
metrics = MetricsCollector()
client = OAuth2Client(
    auth_server="https://auth.example.com",
    metrics_collector=metrics
)

# Get metrics
stats = metrics.get_stats()
print(f"Total registrations: {stats['registrations']}")
print(f"Token refreshes: {stats['token_refreshes']}")
```

## 🚨 Error Handling

### Exception Hierarchy

```python
from mcp_oauth_dynamicclient.exceptions import (
    OAuth2Error,           # Base exception
    RegistrationError,     # Registration failures
    AuthorizationError,    # Authorization failures
    TokenError,           # Token operation failures
    ValidationError,      # Input validation errors
    NetworkError,         # Network/HTTP errors
    ConfigurationError    # Configuration errors
)
```

### Error Handling Examples

```python
try:
    registration = await client.register()
except RegistrationError as e:
    print(f"Registration failed: {e}")
    if e.error_code == "invalid_client_name":
        # Handle specific error
        pass

try:
    token = await client.exchange_code(code)
except AuthorizationError as e:
    if e.error_code == "invalid_grant":
        # Authorization code expired or invalid
        # Restart authorization flow
        pass

try:
    new_token = await client.refresh_token(refresh_token)
except TokenError as e:
    if e.error_code == "invalid_grant":
        # Refresh token expired, need re-authorization
        pass
```

### Retry Logic

Built-in retry logic for transient failures:

```python
from mcp_oauth_dynamicclient import OAuth2Client, RetryConfig

# Configure retry behavior
retry_config = RetryConfig(
    max_retries=3,
    backoff_factor=2.0,
    retry_on_status=[502, 503, 504],
    retry_on_exceptions=[NetworkError]
)

client = OAuth2Client(
    auth_server="https://auth.example.com",
    retry_config=retry_config
)
```

## 🎯 Advanced Usage

### Custom Storage Backend

Implement custom token storage:

```python
from mcp_oauth_dynamicclient.storage import TokenStorage

class DatabaseStorage(TokenStorage):
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def store_token(self, key: str, token: dict) -> None:
        await self.db.execute(
            "INSERT INTO tokens (key, data) VALUES (?, ?)",
            (key, json.dumps(token))
        )
    
    async def retrieve_token(self, key: str) -> dict:
        result = await self.db.fetch_one(
            "SELECT data FROM tokens WHERE key = ?", (key,)
        )
        return json.loads(result["data"]) if result else None

# Use custom storage
storage = DatabaseStorage(db_connection)
client = OAuth2Client(
    auth_server="https://auth.example.com",
    storage=storage
)
```

### Token Introspection

Advanced token validation:

```python
# Validate token and get metadata
token_info = await client.introspect_token(access_token)

if token_info["active"]:
    print(f"Token valid until: {token_info['exp']}")
    print(f"Scopes: {token_info['scope']}")
    print(f"Client: {token_info['client_id']}")
else:
    print("Token is invalid or expired")
```

### Device Authorization Flow

Support for RFC 8628 Device Authorization Grant:

```python
# Start device flow
device_auth = await client.start_device_authorization(scope="mcp:read")

print(f"Visit: {device_auth['verification_uri']}")
print(f"Code: {device_auth['user_code']}")

# Poll for completion
token = await client.poll_device_authorization(
    device_code=device_auth["device_code"]
)
```

## 🔗 Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, Depends, HTTPException
from mcp_oauth_dynamicclient import OAuth2Client

app = FastAPI()
oauth_client = OAuth2Client(auth_server="https://auth.example.com")

async def get_current_user(token: str = Depends(oauth_token)):
    try:
        user_info = await oauth_client.introspect_token(token)
        if not user_info["active"]:
            raise HTTPException(401, "Invalid token")
        return user_info
    except Exception:
        raise HTTPException(401, "Authentication failed")

@app.get("/protected")
async def protected_route(user=Depends(get_current_user)):
    return {"user": user["sub"], "scopes": user["scope"]}
```

### CLI Integration

```python
import click
from mcp_oauth_dynamicclient.cli import OAuth2CLI

@click.command()
@click.option("--auth-server", required=True)
@click.option("--client-name", required=True)
def login(auth_server, client_name):
    """Login via OAuth 2.1 flow"""
    cli = OAuth2CLI(auth_server=auth_server, client_name=client_name)
    token = cli.interactive_login()
    click.echo(f"Access token: {token['access_token']}")

if __name__ == "__main__":
    login()
```

### Async Context Manager

```python
from mcp_oauth_dynamicclient import OAuth2Client

async def main():
    async with OAuth2Client(auth_server="https://auth.example.com") as client:
        # Client automatically handles cleanup
        registration = await client.register()
        token = await client.get_token()
        
        # Make authenticated requests
        response = await client.authenticated_request(
            "GET", "https://api.example.com/data"
        )
    # Client and connections automatically closed
```

---

**Next Steps:**
- Explore {doc}`mcp-streamablehttp-proxy` for protocol bridging
- Check {doc}`../integration/oauth-flows` for OAuth integration patterns  
- Review {doc}`../api/oauth-endpoints` for server-side implementation