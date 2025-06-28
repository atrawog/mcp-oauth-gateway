"""Main entry point for MCP Echo StreamableHTTP Server - Stateful version."""

import argparse
import logging
import os
import sys

from .server import MCPEchoServerStateful


def parse_supported_versions(versions_str: str) -> list[str]:
    """Parse comma-separated supported protocol versions."""
    if not versions_str:
        return []
    return [v.strip() for v in versions_str.split(",") if v.strip()]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Echo StreamableHTTP Server - Stateful version with session management",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("MCP_ECHO_HOST", "0.0.0.0"),  # noqa: S104 - Docker container needs to bind to all interfaces
        help="Host to bind to (default: 0.0.0.0, env: MCP_ECHO_HOST)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_ECHO_PORT", "3000")),
        help="Port to bind to (default: 3000, env: MCP_ECHO_PORT)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=os.getenv("MCP_ECHO_DEBUG", "").lower() in ("true", "1", "yes"),
        help="Enable debug mode (default: False, env: MCP_ECHO_DEBUG)",
    )
    parser.add_argument(
        "--protocol-versions",
        default=os.getenv("MCP_PROTOCOL_VERSIONS_SUPPORTED", "2025-06-18,2025-03-26,2024-11-05"),
        help="Comma-separated list of supported protocol versions (env: MCP_PROTOCOL_VERSIONS_SUPPORTED)",
    )
    parser.add_argument(
        "--session-timeout",
        type=int,
        default=int(os.getenv("MCP_SESSION_TIMEOUT", "3600")),
        help="Session timeout in seconds (default: 3600, env: MCP_SESSION_TIMEOUT)",
    )

    args = parser.parse_args()

    # Parse supported versions
    supported_versions = parse_supported_versions(args.protocol_versions)
    if not supported_versions:
        print("Error: No supported protocol versions specified", file=sys.stderr)
        sys.exit(1)

    if args.debug:
        print("Starting MCP Echo Server Stateful")
        print(f"Host: {args.host}")
        print(f"Port: {args.port}")
        print(f"Debug: {args.debug}")
        print(f"Supported protocol versions: {supported_versions}")
        print(f"Session timeout: {args.session_timeout} seconds")

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

    # Create and run server
    server = MCPEchoServerStateful(
        debug=args.debug,
        supported_versions=supported_versions,
        session_timeout=args.session_timeout,
    )

    try:
        server.run(host=args.host, port=args.port, log_file=log_file)
    except KeyboardInterrupt:
        if args.debug:
            print("\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
