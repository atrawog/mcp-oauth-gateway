# Integration Guide

How to integrate with the MCP OAuth Gateway from various platforms and clients, implementing OAuth 2.1 with RFC 7591/7592 compliance.

## Claude.ai Integration

### The Nine Sacred Steps of Connection

Claude.ai follows a standardized integration pattern for MCP servers with OAuth authentication:

```{mermaid}
sequenceDiagram
    participant Claude as Claude.ai
    participant Gateway as MCP Gateway
    participant Auth as Auth Service
    participant GitHub as GitHub OAuth
    participant MCP as MCP Service
    
    Note over Claude,MCP: Step 1-3: Discovery & Registration
    Claude->>Gateway: POST /mcp (no auth)
    Gateway->>Claude: 401 + WWW-Authenticate: Bearer
    Claude->>Gateway: GET /.well-known/oauth-authorization-server
    Gateway->>Claude: OAuth server metadata
    
    Note over Claude,MCP: Step 4-5: Client Registration
    Claude->>Gateway: POST /register (client metadata)
    Gateway->>Claude: 201 + client_id + registration_access_token
    
    Note over Claude,MCP: Step 6-8: User Authentication
    Claude->>Gateway: GET /authorize?client_id=...&code_challenge=...
    Gateway->>GitHub: Redirect to GitHub OAuth
    GitHub->>Gateway: Authorization code
    Gateway->>Claude: Authorization code
    
    Note over Claude,MCP: Step 9: Token Exchange & Access
    Claude->>Gateway: POST /token (code + PKCE verifier)
    Gateway->>Claude: Access token (JWT)
    Claude->>Gateway: POST /mcp (Bearer token)
    Gateway->>MCP: Authenticated request
    MCP->>Claude: MCP response
```

### Configuration Requirements

Claude.ai requires specific OAuth server metadata to be available:

```json
{
  "issuer": "https://auth.yourdomain.com",
  "authorization_endpoint": "https://auth.yourdomain.com/authorize",
  "token_endpoint": "https://auth.yourdomain.com/token", 
  "registration_endpoint": "https://auth.yourdomain.com/register",
  "revocation_endpoint": "https://auth.yourdomain.com/revoke",
  "introspection_endpoint": "https://auth.yourdomain.com/introspect",
  "code_challenge_methods_supported": ["S256"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "response_types_supported": ["code"],
  "scopes_supported": ["mcp.fetch", "mcp.memory", "mcp.time"],
  "token_endpoint_auth_methods_supported": ["none", "client_secret_post"]
}
```

### MCP Server Configuration

Add your MCP server to Claude.ai configuration:

```json
{
  "mcpServers": {
    "your-service": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--url", "https://mcp-service.yourdomain.com/mcp",
        "--oauth2"
      ],
      "env": {
        "MCP_PROTOCOL_VERSION": "2025-06-18"
      }
    }
  }
}
```

## Custom MCP Clients

### Using mcp-streamablehttp-client

The recommended client for connecting to MCP OAuth Gateway:

#### Installation
```bash
# Install via pixi (recommended)
pixi add mcp-streamablehttp-client

# Or via pip
pip install mcp-streamablehttp-client
```

#### Basic Usage
```bash
# Interactive mode with OAuth
mcp-streamablehttp-client \
  --url https://mcp-service.yourdomain.com/mcp \
  --oauth2

# With pre-existing token
mcp-streamablehttp-client \
  --url https://mcp-service.yourdomain.com/mcp \
  --token your-access-token
```

#### Programmatic Usage
```python
from mcp_streamablehttp_client import MCPClient
import asyncio

async def main():
    client = MCPClient(
        url="https://mcp-service.yourdomain.com/mcp",
        oauth2=True  # Enables OAuth flow
    )
    
    # Initialize connection (triggers OAuth if needed)
    await client.initialize()
    
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {[tool.name for tool in tools.tools]}")
    
    # Call a tool
    result = await client.call_tool("get_current_time", {"timezone": "UTC"})
    print(f"Current time: {result.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Client Implementation

#### OAuth 2.1 Flow Implementation

```python
import requests
import secrets
import hashlib
import base64
from urllib.parse import urlencode, parse_qs
import webbrowser

class MCPOAuthClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client_id = None
        self.registration_token = None
        self.access_token = None
    
    def register_client(self):
        """Register new OAuth client via RFC 7591."""
        registration_data = {
            "redirect_uris": ["http://localhost:8080/callback"],
            "client_name": "Custom MCP Client",
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none"  # PKCE public client
        }
        
        response = requests.post(
            f"{self.base_url}/register",
            json=registration_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            data = response.json()
            self.client_id = data["client_id"]
            self.registration_token = data["registration_access_token"]
            return data
        else:
            raise Exception(f"Registration failed: {response.text}")
    
    def generate_pkce_challenge(self):
        """Generate PKCE code verifier and challenge."""
        # Generate code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        
        # Generate code challenge (S256)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def authorize(self):
        """Start OAuth authorization flow."""
        if not self.client_id:
            self.register_client()
        
        # Generate PKCE parameters
        code_verifier, code_challenge = self.generate_pkce_challenge()
        
        # Build authorization URL
        auth_params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": "http://localhost:8080/callback",
            "scope": "mcp.fetch mcp.memory mcp.time",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": secrets.token_urlsafe(32)
        }
        
        auth_url = f"{self.base_url}/authorize?{urlencode(auth_params)}"
        
        # Open browser for user authentication
        webbrowser.open(auth_url)
        
        # Wait for callback (simplified - use proper HTTP server)
        authorization_code = input("Enter authorization code from callback: ")
        
        return self.exchange_code(authorization_code, code_verifier)
    
    def exchange_code(self, code: str, code_verifier: str):
        """Exchange authorization code for access token."""
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://localhost:8080/callback",
            "client_id": self.client_id,
            "code_verifier": code_verifier
        }
        
        response = requests.post(
            f"{self.base_url}/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_info = response.json()
            self.access_token = token_info["access_token"]
            return token_info
        else:
            raise Exception(f"Token exchange failed: {response.text}")
    
    def call_mcp(self, service_url: str, method: str, params: dict = None):
        """Call MCP endpoint with authentication."""
        if not self.access_token:
            self.authorize()
        
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        response = requests.post(
            service_url,
            json=mcp_request,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )
        
        return response.json()

# Usage example
client = MCPOAuthClient("https://auth.yourdomain.com")
result = client.call_mcp(
    "https://mcp-time.yourdomain.com/mcp",
    "tools/call",
    {"name": "get_current_time", "arguments": {"timezone": "UTC"}}
)
print(result)
```

## OAuth Flow Implementation

### Server Discovery

Every MCP service must expose OAuth server metadata:

```python
import requests

def discover_oauth_server(mcp_service_url: str):
    """Discover OAuth authorization server for MCP service."""
    # Extract base domain from MCP service URL
    from urllib.parse import urlparse
    parsed = urlparse(mcp_service_url)
    base_domain = parsed.netloc
    
    # Try service-specific discovery first
    discovery_url = f"https://{base_domain}/.well-known/oauth-authorization-server"
    
    try:
        response = requests.get(discovery_url)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    # Fallback to auth service
    auth_domain = base_domain.replace('mcp-', 'auth.')
    discovery_url = f"https://{auth_domain}/.well-known/oauth-authorization-server"
    
    response = requests.get(discovery_url)
    return response.json()
```

### Dynamic Client Registration (RFC 7591)

```python
def register_oauth_client(auth_server_url: str, client_metadata: dict):
    """Register OAuth client dynamically."""
    response = requests.post(
        f"{auth_server_url}/register",
        json=client_metadata,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 201:
        return response.json()
    elif response.status_code == 400:
        error = response.json()
        raise ValueError(f"Registration error: {error['error_description']}")
    else:
        raise Exception(f"Registration failed: {response.status_code}")

# Example registration
client_info = register_oauth_client(
    "https://auth.yourdomain.com",
    {
        "redirect_uris": ["https://myapp.com/callback"],
        "client_name": "My MCP Application",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
        "scope": "mcp.fetch mcp.memory mcp.time"
    }
)
```

### Client Management (RFC 7592)

```python
def manage_client(auth_server_url: str, client_id: str, registration_token: str):
    """Manage OAuth client registration."""
    headers = {
        "Authorization": f"Bearer {registration_token}",
        "Content-Type": "application/json"
    }
    
    # Read client metadata
    response = requests.get(
        f"{auth_server_url}/register/{client_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Client read failed: {response.status_code}")

def update_client(auth_server_url: str, client_id: str, 
                  registration_token: str, updates: dict):
    """Update client registration."""
    headers = {
        "Authorization": f"Bearer {registration_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.put(
        f"{auth_server_url}/register/{client_id}",
        json=updates,
        headers=headers
    )
    
    return response.json() if response.status_code == 200 else None

def delete_client(auth_server_url: str, client_id: str, registration_token: str):
    """Delete client registration."""
    headers = {"Authorization": f"Bearer {registration_token}"}
    
    response = requests.delete(
        f"{auth_server_url}/register/{client_id}",
        headers=headers
    )
    
    return response.status_code == 204
```

## Testing Integration

### Integration Test Framework

```python
import pytest
import requests
from typing import Dict, Any

class MCPIntegrationTest:
    def __init__(self, base_domain: str):
        self.base_domain = base_domain
        self.auth_url = f"https://auth.{base_domain}"
        self.client_id = None
        self.access_token = None
    
    @pytest.fixture(scope="class")
    def oauth_client(self):
        """Setup OAuth client for testing."""
        client = MCPIntegrationTest(self.base_domain)
        client.register_test_client()
        client.authenticate()
        return client
    
    def register_test_client(self):
        """Register test client for integration tests."""
        client_data = {
            "redirect_uris": ["http://localhost:8080/callback"],
            "client_name": "Integration Test Client",
            "grant_types": ["authorization_code"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none"
        }
        
        response = requests.post(
            f"{self.auth_url}/register",
            json=client_data
        )
        
        assert response.status_code == 201
        data = response.json()
        self.client_id = data["client_id"]
        return data
    
    def authenticate(self):
        """Authenticate using test credentials."""
        # This would use test OAuth credentials
        # In real tests, use pre-configured test tokens
        self.access_token = "test_access_token"
    
    def test_service_discovery(self, service_name: str):
        """Test OAuth server discovery for service."""
        discovery_url = f"https://{service_name}.{self.base_domain}/.well-known/oauth-authorization-server"
        
        response = requests.get(discovery_url)
        assert response.status_code == 200
        
        metadata = response.json()
        assert "authorization_endpoint" in metadata
        assert "token_endpoint" in metadata
        assert "registration_endpoint" in metadata
    
    def test_mcp_endpoint(self, service_name: str, method: str, params: Dict[str, Any] = None):
        """Test MCP endpoint with authentication."""
        service_url = f"https://{service_name}.{self.base_domain}/mcp"
        
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        response = requests.post(
            service_url,
            json=mcp_request,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": "2025-06-18"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "result" in result or "error" in result
        return result

# Usage in tests
class TestMCPTimeService:
    def test_time_service_integration(self, oauth_client):
        """Test complete time service integration."""
        # Test service discovery
        oauth_client.test_service_discovery("mcp-time")
        
        # Test MCP initialization
        result = oauth_client.test_mcp_endpoint(
            "mcp-time", 
            "initialize",
            {"protocolVersion": "2025-06-18"}
        )
        assert result["result"]["protocolVersion"] == "2025-06-18"
        
        # Test tool calling
        result = oauth_client.test_mcp_endpoint(
            "mcp-time",
            "tools/call", 
            {"name": "get_current_time", "arguments": {"timezone": "UTC"}}
        )
        assert "result" in result
```

### Load Testing

```python
import asyncio
import aiohttp
import time
from typing import List

async def load_test_mcp_service(
    service_url: str,
    access_token: str,
    concurrent_requests: int = 100,
    duration_seconds: int = 60
):
    """Load test MCP service with OAuth authentication."""
    
    async def make_request(session: aiohttp.ClientSession):
        """Make single MCP request."""
        mcp_request = {
            "jsonrpc": "2.0", 
            "id": 1,
            "method": "tools/list"
        }
        
        try:
            async with session.post(
                service_url,
                json=mcp_request,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "MCP-Protocol-Version": "2025-06-18"
                }
            ) as response:
                return response.status, await response.json()
        except Exception as e:
            return 500, {"error": str(e)}
    
    # Run load test
    start_time = time.time()
    results = []
    
    async with aiohttp.ClientSession() as session:
        while time.time() - start_time < duration_seconds:
            # Launch concurrent requests
            tasks = [
                make_request(session) 
                for _ in range(concurrent_requests)
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Brief pause between batches
            await asyncio.sleep(0.1)
    
    # Analyze results
    successful_requests = sum(1 for status, _ in results if status == 200)
    total_requests = len(results)
    
    print(f"Load test results:")
    print(f"  Total requests: {total_requests}")
    print(f"  Successful: {successful_requests}")
    print(f"  Success rate: {successful_requests/total_requests*100:.1f}%")
    print(f"  Requests/second: {total_requests/duration_seconds:.1f}")

# Run load test
asyncio.run(load_test_mcp_service(
    "https://mcp-time.yourdomain.com/mcp",
    "your_access_token",
    concurrent_requests=50,
    duration_seconds=30
))
```

This integration guide provides comprehensive coverage for connecting to the MCP OAuth Gateway from various client types, implementing proper OAuth 2.1 flows, and testing integration thoroughly.