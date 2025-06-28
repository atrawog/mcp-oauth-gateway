"""Command-line interface for the MCP stdio-to-streamable-HTTP proxy."""

import argparse
import logging
import os
import sys

from .server import run_server

logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCP stdio-to-streamable-HTTP proxy - Bridge any MCP stdio server to streamable HTTP endpoints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with a Python MCP server module
  mcp-streamablehttp-proxy python -m mcp_server_fetch

  # Run with a custom command
  mcp-streamablehttp-proxy /path/to/mcp-server --arg1 --arg2

  # Run on a different port
  mcp-streamablehttp-proxy --port 8080 python -m mcp_server_fetch

  # Run with custom session timeout
  mcp-streamablehttp-proxy --timeout 600 python -m mcp_server_fetch
""",
    )

    parser.add_argument("server_command", nargs="+", help="Command to run the MCP stdio server")

    parser.add_argument(
        "--host",
        default=os.getenv("MCP_BIND_HOST", "127.0.0.1"),
        help="Host to bind to (default: 127.0.0.1, or MCP_BIND_HOST env var, use 0.0.0.0 for external access)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "3000")),
        help="Port to bind to (default: 3000, or MCP_PORT env var)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Session timeout in seconds (default: 300)",
    )

    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Logging level (default: info)",
    )

    # Use parse_known_args to handle server commands with options like -m
    args, unknown = parser.parse_known_args()

    # Combine the server_command with any unknown args (like -m)
    full_server_command = args.server_command
    if unknown:
        # Insert unknown args after the first command (e.g., python)
        if len(full_server_command) > 0:
            full_server_command = [full_server_command[0]] + unknown + full_server_command[1:]
        else:
            full_server_command = unknown

    try:
        run_server(
            server_command=full_server_command,
            host=args.host,
            port=args.port,
            session_timeout=args.timeout,
            log_level=args.log_level,
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
