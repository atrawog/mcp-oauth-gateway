"""Basic example of running the MCP OAuth server"""

import asyncio
import os

from mcp_oauth_dynamicclient import Settings, create_app


async def main():
    # Create settings (will load from .env)
    settings = Settings()

    # Create the app
    app = create_app(settings)

    # Run with uvicorn
    import uvicorn

    # Use environment variable or default to localhost for security
    host = os.getenv("HOST", "127.0.0.1")  # Default to localhost only
    config = uvicorn.Config(app, host=host, port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
