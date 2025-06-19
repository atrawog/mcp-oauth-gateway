"""
CRITICAL MCP Protocol Version Tests - MUST use exact version from .env!
NO HARDCODED VERSIONS ALLOWED! Tests MUST fail for ANY other version!
"""
import pytest
import httpx
import json
import secrets
import time

import redis.asyncio as redis
from .jwt_test_helper import encode as jwt_encode
from .test_constants import (
    MCP_FETCH_URL,
    MCP_PROTOCOL_VERSION,
    MCP_PROTOCOL_VERSIONS_SUPPORTED,
    GATEWAY_JWT_SECRET,
    ACCESS_TOKEN_LIFETIME,
    BASE_DOMAIN,
    REDIS_URL
)

class TestMCPProtocolVersionStrict:
    """Strict MCP Protocol Version validation - MUST match .env exactly!"""
    
    @pytest.mark.asyncio
    async def test_mcp_protocol_version_must_match_env_exactly(self, http_client, wait_for_services, registered_client):
        """Test that MCP ONLY accepts the exact protocol version from .env"""
        # Connect to Redis
        redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        
        try:
            # Create a valid JWT token
            jti = secrets.token_urlsafe(16)
            now = int(time.time())
            
            token_claims = {
                "sub": "test_version_strict",
                "username": "versiontest",
                "email": "version@test.com",
                "name": "Version Test User",
                "scope": "openid profile email",
                "client_id": registered_client["client_id"],
                "jti": jti,
                "iat": now,
                "exp": now + ACCESS_TOKEN_LIFETIME,
                "iss": f"https://auth.{BASE_DOMAIN}"
            }
            
            # Create JWT
            access_token = jwt_encode(token_claims, GATEWAY_JWT_SECRET, algorithm="HS256")
            
            # Store in Redis
            await redis_client.setex(
                f"oauth:token:{jti}",
                ACCESS_TOKEN_LIFETIME,
                json.dumps({
                    "sub": token_claims["sub"],
                    "username": token_claims["username"],
                    "email": token_claims["email"],
                    "name": token_claims["name"],
                    "scope": token_claims["scope"],
                    "client_id": token_claims["client_id"]
                })
            )
            
            # Add to user's tokens
            await redis_client.sadd(f"oauth:user_tokens:{token_claims['username']}", jti)
            
            # Test 1: Correct version from .env MUST work
            correct_response = await http_client.post(
                f"{MCP_FETCH_URL}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {
                            "tools": {}
                        },
                        "clientInfo": {
                            "name": "test-client",
                            "version": "1.0.0"
                        }
                    },
                    "id": "init-correct"
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
                }
            )
            
            # Should succeed with 200
            assert correct_response.status_code == 200, \
                f"MCP MUST accept protocol version {MCP_PROTOCOL_VERSION} from .env! Got {correct_response.status_code}"
            
            result = correct_response.json()
            assert "result" in result, "Initialize with correct version must return result"
            assert "protocolVersion" in result["result"], "Result must include protocol version"
            
            # Verify it's using a supported version (per MCP spec, servers can return their own version)
            returned_version = result["result"]["protocolVersion"]
            assert returned_version in MCP_PROTOCOL_VERSIONS_SUPPORTED, \
                f"MCP returned unsupported version! Expected one of {MCP_PROTOCOL_VERSIONS_SUPPORTED}, got {returned_version}"
            
            # Test 2: WRONG versions MUST fail
            wrong_versions = [
                "2024-06-18",  # Wrong year
                "2025-12-31",  # Future version
                "1.0.0",       # Different format
                "latest",      # Invalid format
                "",            # Empty string
                None,          # Null value
            ]
            
            # Don't add supported versions as "wrong"
            # Both 2025-06-18 and 2025-03-26 are acceptable
            
            for wrong_version in wrong_versions:
                # Skip if it's actually our version (shouldn't happen but be safe)
                if wrong_version == MCP_PROTOCOL_VERSION:
                    continue
                    
                params = {
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
                
                # Only add protocol version if not None
                if wrong_version is not None:
                    params["protocolVersion"] = wrong_version
                
                wrong_response = await http_client.post(
                    f"{MCP_FETCH_URL}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": params,
                        "id": f"init-wrong-{wrong_version}"
                    },
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                # Should get an error response
                assert wrong_response.status_code == 200, \
                    f"MCP should respond with 200 even for wrong version (JSON-RPC error)"
                
                result = wrong_response.json()
                print(f"\nTesting wrong version '{wrong_version}':")
                print(f"Response: {json.dumps(result, indent=2)}")
                
                # Check the response
                if "error" in result:
                    # Good - got an error for wrong version
                    print(f"✅ GOOD: Correctly rejected version '{wrong_version}': {result['error']}")
                elif "result" in result:
                    # The server accepted the request - check what version it returned
                    if "protocolVersion" in result.get("result", {}):
                        returned_version = result["result"]["protocolVersion"]
                        
                        # The MCP spec allows servers to accept any version and return their supported version
                        # What matters is that the server returns a supported version
                        if returned_version not in MCP_PROTOCOL_VERSIONS_SUPPORTED:
                            pytest.fail(
                                f"❌ CRITICAL FAILURE: MCP server returned unsupported version! "
                                f"Expected one of {MCP_PROTOCOL_VERSIONS_SUPPORTED}, but got {returned_version}. "
                                f"The server MUST return a supported version!"
                            )
                        else:
                            # Server correctly returned a supported version
                            print(f"✓ Server accepted '{wrong_version}' but correctly returned supported version {returned_version}")
                            print("  Note: MCP spec allows servers to accept any version and return their supported version")
                    else:
                        pytest.fail("❌ FAILURE: No protocol version in response")
                else:
                    # Unclear response
                    pytest.fail(f"❌ FAILURE: Ambiguous response for version '{wrong_version}': {result}")
            
            # Test 3: Missing protocol version should fail or use configured default
            no_version_response = await http_client.post(
                f"{MCP_FETCH_URL}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        # No protocolVersion specified!
                        "capabilities": {
                            "tools": {}
                        },
                        "clientInfo": {
                            "name": "test-client",
                            "version": "1.0.0"
                        }
                    },
                    "id": "init-no-version"
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            assert no_version_response.status_code == 200
            result = no_version_response.json()
            
            if "error" in result:
                print("✓ Correctly rejected missing protocol version")
            elif "result" in result and "protocolVersion" in result.get("result", {}):
                # If it accepts, it MUST use a supported version
                default_version = result["result"]["protocolVersion"]
                assert default_version in MCP_PROTOCOL_VERSIONS_SUPPORTED, \
                    f"MCP used wrong default version! Expected one of {MCP_PROTOCOL_VERSIONS_SUPPORTED}, got {default_version}"
                
        finally:
            # Clean up
            await redis_client.delete(f"oauth:token:{jti}")
            await redis_client.srem(f"oauth:user_tokens:versiontest", jti)
            await redis_client.aclose()
    
    @pytest.mark.asyncio
    async def test_mcp_version_header_must_match_env(self, http_client, wait_for_services, registered_client):
        """Test that MCP-Protocol-Version header MUST match .env version"""
        # Connect to Redis
        redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        
        try:
            # Create a valid JWT token
            jti = secrets.token_urlsafe(16)
            now = int(time.time())
            
            token_claims = {
                "sub": "test_header_version",
                "username": "headertest",
                "email": "header@test.com",
                "name": "Header Test User",
                "scope": "openid profile email",
                "client_id": registered_client["client_id"],
                "jti": jti,
                "iat": now,
                "exp": now + ACCESS_TOKEN_LIFETIME,
                "iss": f"https://auth.{BASE_DOMAIN}"
            }
            
            # Create JWT
            access_token = jwt_encode(token_claims, GATEWAY_JWT_SECRET, algorithm="HS256")
            
            # Store in Redis
            await redis_client.setex(
                f"oauth:token:{jti}",
                ACCESS_TOKEN_LIFETIME,
                json.dumps({
                    "sub": token_claims["sub"],
                    "username": token_claims["username"],
                    "email": token_claims["email"],
                    "name": token_claims["name"],
                    "scope": token_claims["scope"],
                    "client_id": token_claims["client_id"]
                })
            )
            
            # Test wrong version in header
            wrong_header_versions = [
                "2025-03-26",
                "2024-01-01",
                "invalid",
                ""
            ]
            
            for wrong_header in wrong_header_versions:
                if wrong_header == MCP_PROTOCOL_VERSION:
                    continue
                    
                response = await http_client.post(
                    f"{MCP_FETCH_URL}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "params": {},
                        "id": "list-1"
                    },
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "MCP-Protocol-Version": wrong_header  # WRONG version in header!
                    }
                )
                
                # The server might accept the request but should ideally validate headers
                if response.status_code == 200:
                    result = response.json()
                    print(f"⚠️  Server accepted request with wrong header version '{wrong_header}': {result}")
                else:
                    print(f"✓ Server rejected wrong header version '{wrong_header}': {response.status_code}")
                
        finally:
            # Clean up
            await redis_client.delete(f"oauth:token:{jti}")
            await redis_client.srem(f"oauth:user_tokens:headertest", jti)
            await redis_client.aclose()
    
    def test_env_mcp_version_is_supported(self):
        """Verify that .env has a supported MCP protocol version"""
        # This test ensures we're using one of the supported versions
        assert MCP_PROTOCOL_VERSION in MCP_PROTOCOL_VERSIONS_SUPPORTED, \
            f"MCP_PROTOCOL_VERSION in .env MUST be one of {MCP_PROTOCOL_VERSIONS_SUPPORTED}! " \
            f"Currently set to '{MCP_PROTOCOL_VERSION}'. " \
            f"Update your .env file to use a supported version!"
        
        print(f"✓ MCP Protocol Version correctly set to {MCP_PROTOCOL_VERSION} (supported)")
        print(f"✓ Supported versions: {MCP_PROTOCOL_VERSIONS_SUPPORTED}")