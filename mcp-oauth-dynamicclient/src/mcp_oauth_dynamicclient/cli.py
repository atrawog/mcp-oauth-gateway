"""CLI interface for MCP OAuth Dynamic Client"""

import argparse

import uvicorn

from .config import Settings
from .server import create_app


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="MCP OAuth Dynamic Client Registration Server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind the server to (default: 127.0.0.1, use 0.0.0.0 for external access)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()

    # Create app
    settings = Settings()
    app = create_app(settings)

    # Configure uvicorn logging to use our handlers
    import os

    # Get the log file from environment
    log_file = os.environ.get("LOG_FILE")
    log_config = None

    if log_file:
        # Create custom log config that includes file handler
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                },
                "file": {
                    "formatter": "default",
                    "class": "logging.FileHandler",
                    "filename": log_file,
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default", "file"],
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["default", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["default", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["default", "file"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }

    # Run server
    if args.reload:
        # For reload, use the module path
        uvicorn.run(
            "mcp_oauth_dynamicclient.server:create_app",
            host=args.host,
            port=args.port,
            reload=True,
            factory=True,
            log_config=log_config,
        )
    else:
        # For production, use the app instance
        uvicorn.run(app, host=args.host, port=args.port, reload=False, log_config=log_config)


if __name__ == "__main__":
    main()
