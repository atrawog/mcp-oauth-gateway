"""Entry point for the MCP Echo StreamableHTTP Server."""

import argparse
import os
import sys
from dotenv import load_dotenv
from .server import MCPEchoServer


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="MCP Echo Server - Stateless StreamableHTTP Implementation"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("MCP_ECHO_HOST", "0.0.0.0"),
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_ECHO_PORT", "3000")),
        help="Port to bind to (default: 3000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=os.getenv("MCP_ECHO_DEBUG", "").lower() in ("true", "1", "yes"),
        help="Enable debug logging for message tracing"
    )
    
    args = parser.parse_args()
    
    # Get supported protocol versions from environment
    supported_versions_str = os.getenv("MCP_PROTOCOL_VERSIONS_SUPPORTED", "2025-06-18")
    supported_versions = [v.strip() for v in supported_versions_str.split(",") if v.strip()]
    
    if args.debug:
        print(f"Supported protocol versions: {', '.join(supported_versions)}")
    
    # Create and run server
    server = MCPEchoServer(debug=args.debug, supported_versions=supported_versions)
    
    try:
        server.run(host=args.host, port=args.port)
    except KeyboardInterrupt:
        if args.debug:
            print("\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()