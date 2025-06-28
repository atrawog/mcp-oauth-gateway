"""Entry point for the MCP Echo StreamableHTTP Server."""

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from .server import MCPEchoServer


# Set up logger
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="MCP Echo Server - Stateless StreamableHTTP Implementation",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("MCP_ECHO_HOST", "127.0.0.1"),
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_ECHO_PORT", "3000")),
        help="Port to bind to (default: 3000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=os.getenv("MCP_ECHO_DEBUG", "").lower() in ("true", "1", "yes"),
        help="Enable debug logging for message tracing",
    )

    args = parser.parse_args()

    # Get supported protocol versions from environment
    supported_versions_str = os.getenv("MCP_PROTOCOL_VERSIONS_SUPPORTED", "2025-06-18")
    supported_versions = [v.strip() for v in supported_versions_str.split(",") if v.strip()]

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    handlers = [logging.StreamHandler(sys.stdout)]

    # Add file handler if LOG_FILE is set
    log_file = os.environ.get("LOG_FILE")
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

    logging.basicConfig(level=log_level, format=log_format, handlers=handlers)

    if args.debug:
        logger.debug(f"Supported protocol versions: {', '.join(supported_versions)}")

    # Create and run server
    server = MCPEchoServer(debug=args.debug, supported_versions=supported_versions)

    try:
        server.run(host=args.host, port=args.port, log_file=log_file)
    except KeyboardInterrupt:
        if args.debug:
            logger.info("\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
