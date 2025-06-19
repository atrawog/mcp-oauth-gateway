"""
Sacred Auth Service - Using mcp-oauth-dynamicclient package
Following OAuth 2.1 and RFC 7591 divine specifications
"""
import sys
import os

# For development: Add the package to Python path if not installed
# In Docker, the package is properly installed so this won't be needed
try:
    from mcp_oauth_dynamicclient import create_app, Settings
except ImportError:
    # Development mode: add package to path
    package_path = os.path.join(os.path.dirname(__file__), '..', 'mcp-oauth-dynamicclient', 'src')
    if package_path not in sys.path:
        sys.path.insert(0, package_path)
    from mcp_oauth_dynamicclient import create_app, Settings

# Create settings from environment
settings = Settings()

# Create the FastAPI app using our package
app = create_app(settings)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)