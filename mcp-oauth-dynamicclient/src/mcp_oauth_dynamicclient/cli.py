"""
CLI interface for MCP OAuth Dynamic Client
"""

import argparse

import uvicorn

from .config import Settings
from .server import create_app


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="MCP OAuth Dynamic Client Registration Server")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind the server to (default: 8000)"
    )
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()

    # Create app
    settings = Settings()
    app = create_app(settings)

    # Run server
    if args.reload:
        # For reload, use the module path
        uvicorn.run(
            "mcp_oauth_dynamicclient.server:create_app",
            host=args.host,
            port=args.port,
            reload=True,
            factory=True,
        )
    else:
        # For production, use the app instance
        uvicorn.run(app, host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
