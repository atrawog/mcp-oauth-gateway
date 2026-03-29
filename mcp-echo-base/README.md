# MCP Echo Server Base

Base class for MCP Echo Server implementations (stateful and stateless).

## Overview

This package provides the `MCPEchoServerBase` abstract base class that contains common functionality shared between stateful and stateless MCP echo servers. It implements the template method pattern to eliminate code duplication while allowing subclasses to customize specific behaviors.

## Features

- **100% Identical Methods**: Fully implemented common functionality
  - POST request handling with validation
  - Header validation (Content-Type, Accept)
  - JSON-RPC error responses
  - SSE streaming responses
  - Server startup and configuration

- **Template Methods**: Common structure with customizable hooks
  - Main request handler with subclass hooks
  - Traefik header extraction
  - Request data building
  - OPTIONS and GET request handling

- **Abstract Methods**: Subclass customization points
  - Server type identifier ("stateless" or "stateful")
  - Supported protocol versions
  - Additional headers to track
  - Additional request data fields
  - Initialize request handling
  - Logging format

## Usage

Subclasses must implement all abstract methods:

```python
from mcp_echo_base import MCPEchoServerBase

class MCPEchoServerStateless(MCPEchoServerBase):
    def get_server_type(self) -> str:
        return "stateless"

    def get_supported_versions(self) -> list[str]:
        return ["2025-06-18", "2024-11-05"]

    def get_additional_headers(self) -> dict[str, str]:
        return {}

    def get_additional_request_data(self, traefik_headers: dict[str, Any]) -> dict[str, Any]:
        return {}

    def _log_request(self, request: Request, traefik_headers: dict[str, Any]):
        logger.info("MCP-ECHO STATELESS REQUEST - ...")

    async def handle_initialize(self, arguments: dict[str, Any], request_id: Any) -> dict[str, Any]:
        # Implementation
        pass
```

## Dependencies

- starlette >= 0.27.0
- uvicorn >= 0.23.0

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Version

1.0.0
