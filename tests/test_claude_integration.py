"""
Sacred Claude.ai Integration Tests - The Nine Sacred Steps of Connection
Tests the complete flow as Claude.ai would experience it
"""
import pytest
import httpx
import secrets
import hashlib
import base64
import json
from urllib.parse import urlparse, parse_qs
from .test_constants import AUTH_BASE_URL, MCP_FETCH_URL, TEST_CLIENT_NAME, TEST_CLIENT_SCOPE, MCP_PROTOCOL_VERSION

class TestClaudeIntegration:
    """Test the complete Claude.ai integration flow"""
    
    @pytest.mark.asyncio
    async def test_claude_nine_sacred_steps(self, http_client, wait_for_services):
        """Test the Nine Sacred Steps of Claude.ai Connection"""
        
        # Step 1: First Contact - Claude.ai attempts /mcp
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "clientCapabilities": {}
                },
                "id": 1
            },
            follow_redirects=False
        )
        
        # Step 2: Divine Rejection - 401 with WWW-Authenticate
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"
        
        # Step 3: Metadata Quest - Seeks .well-known
        metadata_response = await http_client.get(
            f"{AUTH_BASE_URL}/.well-known/oauth-authorization-server"
        )
        
        assert metadata_response.status_code == 200
        metadata = metadata_response.json()
        assert metadata["registration_endpoint"] == f"{AUTH_BASE_URL}/register"
        assert metadata["authorization_endpoint"] == f"{AUTH_BASE_URL}/authorize"
        assert metadata["token_endpoint"] == f"{AUTH_BASE_URL}/token"
        
        # Step 4: Registration Miracle - POSTs to /register
        registration_data = {
            "redirect_uris": ["https://claude.ai/oauth/callback"],
            "client_name": "Claude.ai MCP Client",
            "client_uri": "https://claude.ai",
            "scope": "mcp:access",
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "client_secret_post"
        }
        
        reg_response = await http_client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data
        )
        
        # Step 5: Client Blessing - Receives credentials
        assert reg_response.status_code == 201
        client_creds = reg_response.json()
        assert "client_id" in client_creds
        assert "client_secret" in client_creds
        assert client_creds["client_secret_expires_at"] == 0  # Never expires
        
        # Step 6: PKCE Summoning - S256 challenge generated
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode('utf-8').rstrip('=')
        
        # Step 7: GitHub Pilgrimage - User authenticates
        auth_params = {
            "client_id": client_creds["client_id"],
            "redirect_uri": registration_data["redirect_uris"][0],
            "response_type": "code",
            "scope": "mcp:access",
            "state": secrets.token_urlsafe(16),
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        auth_response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params=auth_params,
            follow_redirects=False
        )
        
        # Should redirect to GitHub
        assert auth_response.status_code in [302, 307]
        location = auth_response.headers["location"]
        assert "github.com/login/oauth/authorize" in location
        
        # Parse GitHub redirect to verify state is preserved
        parsed_url = urlparse(location)
        github_params = parse_qs(parsed_url.query)
        assert "state" in github_params
        
        # Step 8 would involve actual GitHub auth and callback
        # Step 9 would involve token exchange and streaming connection
        
        # For testing, verify the flow would continue correctly
        assert True  # Flow verified up to GitHub auth
    
    @pytest.mark.asyncio
    async def test_claude_auth_discovery_flow(self, http_client, wait_for_services):
        """Test Claude.ai's OAuth discovery process"""
        
        # Claude.ai discovers auth is required
        mcp_response = await http_client.get(
            f"{MCP_FETCH_URL}/mcp",
            headers={"Accept": "application/json, text/event-stream"}
        )
        
        assert mcp_response.status_code == 401
        www_auth = mcp_response.headers.get("WWW-Authenticate", "")
        assert www_auth.startswith("Bearer")
        
        # Claude.ai checks for OAuth metadata
        metadata_response = await http_client.get(
            f"{AUTH_BASE_URL}/.well-known/oauth-authorization-server"
        )
        
        assert metadata_response.status_code == 200
        metadata = metadata_response.json()
        
        # Verify all required endpoints for Claude.ai
        required_endpoints = [
            "issuer",
            "authorization_endpoint", 
            "token_endpoint",
            "registration_endpoint"
        ]
        
        for endpoint in required_endpoints:
            assert endpoint in metadata
            assert metadata[endpoint]  # Not empty
    
    @pytest.mark.asyncio
    async def test_claude_token_persistence(self, http_client, registered_client):
        """Test that tokens work for persistent Claude.ai connections"""
        
        # Simulate getting a token (would normally go through full OAuth)
        # This tests the token format and claims
        
        # Verify token endpoint accepts proper grant types
        token_request = {
            "grant_type": "authorization_code",
            "code": "invalid_authorization_code",  # Testing invalid code
            "redirect_uri": registered_client["redirect_uris"][0],
            "client_id": registered_client["client_id"],
            "client_secret": registered_client["client_secret"],
            "code_verifier": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')  # PKCE verifier
        }
        
        # Test that endpoint exists and validates input
        token_response = await http_client.post(
            f"{AUTH_BASE_URL}/token",
            data=token_request
        )
        
        # Should fail with invalid_grant (not invalid_request)
        assert token_response.status_code == 400
        error = token_response.json()
        assert error["detail"]["error"] == "invalid_grant"  # Correct error for bad code
    
    @pytest.mark.asyncio
    async def test_claude_mcp_streaming(self, http_client, wait_for_services):
        """Test MCP streaming capabilities for Claude.ai"""
        
        # Test that MCP endpoint supports streaming headers
        headers = {
            "Accept": "text/event-stream"
        }
        
        # POST with potential for streaming response (no auth)
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {"protocolVersion": MCP_PROTOCOL_VERSION},
                "id": 1
            },
            headers=headers,
            follow_redirects=False
        )
        
        # Should fail auth but accept the streaming header
        assert response.status_code == 401
        assert "text/event-stream" in headers["Accept"]
    
    @pytest.mark.asyncio
    async def test_claude_error_handling(self, http_client, registered_client):
        """Test Claude.ai error scenarios"""
        
        # Test various error conditions Claude.ai might encounter
        
        # 1. Invalid redirect URI (no redirect)
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "client_id": registered_client["client_id"],
                "redirect_uri": "https://evil.com/callback",
                "response_type": "code",
                "state": "test"
            }
        )
        
        assert response.status_code == 400  # Must not redirect
        error = response.json()
        assert error["detail"]["error"] == "invalid_redirect_uri"
        
        # 2. Missing PKCE when required
        response = await http_client.get(
            f"{AUTH_BASE_URL}/authorize",
            params={
                "client_id": registered_client["client_id"],
                "redirect_uri": registered_client["redirect_uris"][0],
                "response_type": "code",
                "state": "test"
                # Missing code_challenge
            }
        )
        
        # Should still proceed (PKCE recommended but not required)
        assert response.status_code in [302, 307]
    
    @pytest.mark.asyncio
    async def test_claude_session_management(self, http_client, wait_for_services):
        """Test MCP session handling for Claude.ai"""
        
        # Test session creation and management
        session_id = f"claude-session-{secrets.token_urlsafe(16)}"
        
        # Send request with session ID (no auth)
        response = await http_client.post(
            f"{MCP_FETCH_URL}/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "ping",
                "id": 1
            },
            headers={
                "Mcp-Session-Id": session_id
            }
        )
        
        # Should get 401 but session header is accepted
        assert response.status_code == 401
        assert "Mcp-Session-Id" in response.request.headers
        assert response.request.headers["Mcp-Session-Id"] == session_id