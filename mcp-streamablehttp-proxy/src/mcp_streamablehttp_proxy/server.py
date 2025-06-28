"""Server runner for the MCP stdio-to-HTTP proxy."""

import logging
from typing import List

import uvicorn

from .proxy import create_app

logger = logging.getLogger(__name__)


def run_server(
    server_command: List[str],
    host: str = "127.0.0.1",
    port: int = 3000,
    session_timeout: int = 300,
    log_level: str = "info",
):
    """Run the MCP stdio-to-HTTP proxy server.


    Args:
        server_command: Command to run the MCP stdio server
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 3000)
        session_timeout: Session timeout in seconds (default: 300)
        log_level: Logging level (default: info)

    """
    # Set up logging
    import os

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_handlers = []

    # Always log to console
    log_handlers.append(logging.StreamHandler())

    # Add file handler if LOG_FILE is specified
    log_file = os.environ.get("LOG_FILE")
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        log_handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=log_handlers,
    )

    logger.info(f"Starting MCP stdio-to-HTTP proxy for: {' '.join(server_command)}")

    # Create FastAPI app
    app = create_app(server_command, session_timeout)

    # Run server without automatic trailing slash redirects
    uvicorn.run(app, host=host, port=port, log_level=log_level)
