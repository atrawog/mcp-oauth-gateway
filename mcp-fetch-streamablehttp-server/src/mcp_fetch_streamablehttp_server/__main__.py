"""Entry point for running the server directly."""

import logging
import os

import uvicorn

from .server import Settings
from .server import create_server


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def main():
    """Run the server."""
    # Load settings
    settings = Settings()

    # Create server
    server = create_server(settings)
    app = server.create_app()

    # Get host and port from environment
    host = os.getenv("HOST", "0.0.0.0")  # noqa: S104
    port = int(os.getenv("PORT", "3000"))

    # Log startup info
    logger.info(f"Starting {settings.server_name} v{settings.server_version}")
    logger.info(f"MCP Protocol: {settings.protocol_version}")
    logger.info(f"Listening on {host}:{port}")

    # Run with uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        use_colors=True,
        lifespan="on",
    )


if __name__ == "__main__":
    main()
