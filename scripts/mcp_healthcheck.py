#!/usr/bin/env python3
"""Standardized MCP Health Check Script.

Performs a divine MCP protocol health check for any MCP service
"""

import os
import sys

import requests


def perform_mcp_healthcheck(
    host: str = "localhost", port: int = 3000, protocol_version: str | None = None, timeout: int = 5
) -> bool:
    """Perform an MCP health check by sending an initialize request.

    Args:
        host: The MCP service host
        port: The MCP service port
        protocol_version: The expected MCP protocol version
        timeout: Request timeout in seconds

    Returns:
        True if health check passes, False otherwise
    """
    if not protocol_version:
        raise ValueError("MCP_PROTOCOL_VERSION must be provided")

    url = f"http://{host}:{port}/mcp"

    # Build the initialization request
    payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": protocol_version,
            "capabilities": {},
            "clientInfo": {"name": "healthcheck", "version": "1.0"},
        },
        "id": 1,
    }

    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response_text = response.text

        # Check for protocol version in response
        # The response might be SSE format, so we check for the version anywhere in the response
        if (
            f'"protocolVersion":"{protocol_version}"' in response_text
            or f'"protocolVersion": "{protocol_version}"' in response_text
        ):
            print(f"Health check passed: MCP service is responding with protocol version {protocol_version}")
            return True
        print("Health check failed: MCP service did not respond with expected protocol version")
        print(f"Response: {response_text[:500]}...")  # First 500 chars
        return False

    except requests.exceptions.RequestException as e:
        print(f"Health check failed: Connection error - {e!s}")
        return False
    except Exception as e:
        print(f"Health check failed: Unexpected error - {e!s}")
        return False


def main():
    """Main entry point for the health check script."""
    # Get configuration from environment variables
    host = os.environ.get("MCP_HOST", "localhost")
    port = int(os.environ.get("MCP_PORT", "3000"))
    protocol_version = os.environ.get("MCP_PROTOCOL_VERSION")

    # Check if protocol version is set
    if not protocol_version:
        print("ERROR: MCP_PROTOCOL_VERSION environment variable is not set!")
        print("Each service must define its own protocol version in docker-compose.yml")
        sys.exit(1)

    try:
        # Perform the health check
        success = perform_mcp_healthcheck(host, port, protocol_version)
        # Exit with appropriate code
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Health check failed with error: {e!s}")
        sys.exit(1)


if __name__ == "__main__":
    main()
