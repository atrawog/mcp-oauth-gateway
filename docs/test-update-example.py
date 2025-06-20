"""
Example: How to update existing tests to use the cleanup pattern
"""

# BEFORE - Old test without cleanup pattern
async def test_oauth_client_flow(self):
    """Test complete OAuth client flow"""
    async with httpx.AsyncClient() as client:
        # Register client
        registration_data = {
            "client_name": "OAuth Test Client",  # Generic name
            "redirect_uris": ["http://localhost:8080/callback"],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"]
        }
        
        response = await client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data
        )
        # ... rest of test


# AFTER - Updated with cleanup pattern
async def test_oauth_client_flow(self):
    """Test complete OAuth client flow"""
    async with httpx.AsyncClient() as client:
        # Register client
        registration_data = {
            "client_name": "TEST test_oauth_client_flow",  # TEST + actual function name
            "redirect_uris": ["http://localhost:8080/callback"],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"]
        }
        
        response = await client.post(
            f"{AUTH_BASE_URL}/register",
            json=registration_data
        )
        # ... rest of test


# For class-based tests
class TestOAuthFlows:
    async def test_refresh_token_flow(self):
        """Test refresh token flow"""
        registration_data = {
            "client_name": "TEST test_refresh_token_flow",  # TEST + method name
            "redirect_uris": ["http://localhost:8080/callback"]
        }
        # ... rest of test
    
    async def test_pkce_flow(self):
        """Test PKCE flow"""
        registration_data = {
            "client_name": "TEST test_pkce_flow",  # TEST + method name
            "redirect_uris": ["http://localhost:8080/callback"]
        }
        # ... rest of test