"""Server runner for the MCP stdio-to-HTTP proxy."""
import logging
from typing import List, Optional
import uvicorn
from .proxy import create_app

logger = logging.getLogger(__name__)


def run_server(
    server_command: List[str],
    host: str = "0.0.0.0",
    port: int = 3000,
    session_timeout: int = 300,
    log_level: str = "info"
):
    """Run the MCP stdio-to-HTTP proxy server.
    
    Args:
        server_command: Command to run the MCP stdio server
        host: Host to bind to (default: 0.0.0.0)
        port: Port to bind to (default: 3000)
        session_timeout: Session timeout in seconds (default: 300)
        log_level: Logging level (default: info)
    """
    # Set up logging
    logging.basicConfig(level=getattr(logging, log_level.upper()))
    
    logger.info(f"Starting MCP stdio-to-HTTP proxy for: {' '.join(server_command)}")
    
    # Create FastAPI app
    app = create_app(server_command, session_timeout)
    
    # Run server without automatic trailing slash redirects
    uvicorn.run(app, host=host, port=port, log_level=log_level)