"""Pure Python client for MCP fetch server over Streamable HTTP transport."""

from .client import MCPFetchClient
from .exceptions import MCPError, MCPTransportError, MCPProtocolError

__version__ = "0.1.0"

__all__ = [
    "MCPFetchClient",
    "MCPError",
    "MCPTransportError",
    "MCPProtocolError",
]