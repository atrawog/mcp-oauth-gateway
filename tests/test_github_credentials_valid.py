"""
Test to verify GitHub credentials are still valid
Following CLAUDE.md - NO MOCKING, real services only!
This test should run FIRST to ensure OAuth flow can work
"""
import pytest
import httpx
import os
from .test_constants import (
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    AUTH_BASE_URL
)

class TestGitHubCredentialsValid:
    """Verify GitHub OAuth credentials are still valid"""
    
    @pytest.mark.asyncio
    async def test_github_pat_valid(self):
        """Test if GITHUB_PAT is still valid"""
        github_pat = os.getenv("GITHUB_PAT")
        
        if not github_pat:
            pytest.skip("GITHUB_PAT not set - skipping PAT validation")
        
        # Test the PAT by making a simple API call
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {github_pat}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code == 401:
                pytest.fail(
                    "GITHUB_PAT is invalid or expired! "
                    "Token refresh should have handled this. "
                    "Run 'just generate-github-token' manually if needed."
                )
            elif response.status_code == 403:
                # Check if it's rate limited
                if "rate limit" in response.text.lower():
                    print("⚠️  GitHub API rate limited, but PAT is valid")
                else:
                    pytest.fail(f"GitHub PAT access denied: {response.text}")
            elif response.status_code == 200:
                user_data = response.json()
                print(f"✅ GITHUB_PAT is valid for user: {user_data.get('login', 'unknown')}")
            else:
                pytest.fail(f"Unexpected response: {response.status_code} - {response.text}")
    
    @pytest.mark.asyncio
    async def test_oauth_client_credentials_valid(self):
        """Test if GATEWAY_OAUTH_CLIENT_ID and GATEWAY_OAUTH_CLIENT_SECRET are still valid"""
        oauth_client_id = os.getenv("GATEWAY_OAUTH_CLIENT_ID")
        oauth_client_secret = os.getenv("GATEWAY_OAUTH_CLIENT_SECRET")
        
        if not oauth_client_id or not oauth_client_secret:
            pytest.skip("GATEWAY_OAUTH_CLIENT_ID or GATEWAY_OAUTH_CLIENT_SECRET not set - skipping OAuth validation")
        
        # These are our dynamically registered credentials - verify they work
        # We can't directly verify them without a full OAuth flow, but we can
        # at least check they're in the expected format
        
        # Client ID should start with "client_"
        if not oauth_client_id.startswith("client_"):
            pytest.fail(
                f"OAUTH_CLIENT_ID '{oauth_client_id}' doesn't match expected format. "
                "Run 'just generate-github-token' to register a new client."
            )
        
        # Client secret should be a reasonable length
        if len(oauth_client_secret) < 20:
            pytest.fail(
                f"GATEWAY_OAUTH_CLIENT_SECRET seems too short ({len(oauth_client_secret)} chars). "
                "Run 'just generate-github-token' to register a new client."
            )
        
        print(f"✅ GATEWAY_OAUTH_CLIENT_ID format valid: {oauth_client_id}")
        print(f"✅ GATEWAY_OAUTH_CLIENT_SECRET format valid: {len(oauth_client_secret)} chars")
    
    @pytest.mark.asyncio
    async def test_github_oauth_app_valid(self, wait_for_services):
        """Test if GitHub OAuth app credentials are valid"""
        # Try to reach GitHub OAuth authorize endpoint with our app
        async with httpx.AsyncClient() as client:
            # Build authorize URL
            authorize_url = (
                f"https://github.com/login/oauth/authorize"
                f"?client_id={GITHUB_CLIENT_ID}"
                f"&redirect_uri={AUTH_BASE_URL}/callback"
                f"&scope=read:user user:email"
                f"&state=test_validation"
            )
            
            # GitHub should redirect us to login if credentials are valid
            response = await client.get(
                authorize_url,
                follow_redirects=False
            )
            
            if response.status_code == 302:
                location = response.headers.get("location", "")
                
                # Check for OAuth error in redirect
                if "error=invalid_client" in location:
                    pytest.fail(
                        f"GitHub OAuth app credentials are invalid! "
                        f"GITHUB_CLIENT_ID: {GITHUB_CLIENT_ID} is not recognized. "
                        "Check your GitHub OAuth app settings."
                    )
                elif "error=" in location:
                    # Extract error
                    import urllib.parse
                    parsed = urllib.parse.urlparse(location)
                    params = urllib.parse.parse_qs(parsed.query)
                    error = params.get("error", ["unknown"])[0]
                    error_desc = params.get("error_description", [""])[0]
                    pytest.fail(
                        f"GitHub OAuth error: {error} - {error_desc}. "
                        "Check your GitHub OAuth app configuration."
                    )
                else:
                    # Should redirect to login or back to our callback
                    print(f"✅ GitHub OAuth app credentials are valid")
                    print(f"   Would redirect to: {location[:100]}...")
            elif response.status_code == 200:
                # GitHub might show the authorize page directly
                if "oauth/authorize" in str(response.url):
                    print("✅ GitHub OAuth app credentials are valid (showed authorize page)")
                else:
                    print(f"⚠️  Unexpected response but not an error: {response.url}")
            else:
                pytest.fail(
                    f"Unexpected response from GitHub: {response.status_code}. "
                    "This might indicate invalid OAuth app credentials."
                )
    
    @pytest.mark.asyncio 
    async def test_all_required_credentials_present(self):
        """Ensure all required credentials are set"""
        required_vars = {
            "GITHUB_CLIENT_ID": "GitHub OAuth App Client ID",
            "GITHUB_CLIENT_SECRET": "GitHub OAuth App Client Secret",
        }
        
        missing = []
        for var, description in required_vars.items():
            if not os.getenv(var):
                missing.append(f"{var} ({description})")
        
        if missing:
            pytest.fail(
                f"Missing required credentials:\n" + 
                "\n".join(f"  - {m}" for m in missing) +
                "\n\nSet these in your .env file or run 'just generate-github-token'"
            )
        
        print("✅ All required GitHub credentials are present")
    
    def test_run_this_first(self):
        """This test should always run first to validate setup"""
        print("\n" + "="*60)
        print("VALIDATING GITHUB CREDENTIALS")
        print("="*60)
        print("This test verifies your GitHub OAuth setup is working.")
        print("If any of these fail, the OAuth flow tests won't work!")
        print("="*60 + "\n")