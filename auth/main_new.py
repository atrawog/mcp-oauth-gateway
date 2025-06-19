"""
Auth service using mcp-oauth-dynamicclient package
"""
import sys
import os

# Add the package to Python path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-oauth-dynamicclient', 'src'))

from mcp_oauth_dynamicclient import create_app, Settings

# Create settings from environment
settings = Settings()

# Create the FastAPI app
app = create_app(settings)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)