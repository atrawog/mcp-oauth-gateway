"""Command-line interface for the MCP stdio-to-HTTP proxy."""
import sys
import argparse
import logging
from .server import run_server

logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCP stdio-to-HTTP proxy - Bridge any MCP stdio server to HTTP endpoints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with a Python MCP server module
  mcp-stdio-http python -m mcp_server_fetch
  
  # Run with a custom command
  mcp-stdio-http /path/to/mcp-server --arg1 --arg2
  
  # Run on a different port
  mcp-stdio-http --port 8080 python -m mcp_server_fetch
  
  # Run with custom session timeout
  mcp-stdio-http --timeout 600 python -m mcp_server_fetch
"""
    )
    
    parser.add_argument(
        "server_command",
        nargs="+",
        help="Command to run the MCP stdio server"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to bind to (default: 3000)"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Session timeout in seconds (default: 300)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Logging level (default: info)"
    )
    
    args = parser.parse_args()
    
    try:
        run_server(
            server_command=args.server_command,
            host=args.host,
            port=args.port,
            session_timeout=args.timeout,
            log_level=args.log_level
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()