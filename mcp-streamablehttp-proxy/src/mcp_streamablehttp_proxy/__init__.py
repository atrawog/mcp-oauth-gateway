"""MCP stdio-to-streamable-HTTP proxy - Bridge any MCP stdio server to streamable HTTP endpoints."""

__version__ = "0.1.0"

from .proxy import MCPSession, MCPSessionManager, create_app
from .server import run_server

__all__ = [
    "MCPSession",
    "MCPSessionManager",
    "__version__",
    "create_app",
    "run_server",
]
