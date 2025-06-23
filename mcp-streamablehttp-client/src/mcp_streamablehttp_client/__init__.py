"""MCP Streamable HTTP to stdio proxy client with OAuth support."""

from .config import Settings
from .oauth import OAuthClient
from .proxy import StreamableHttpToStdioProxy


__version__ = "0.1.0"
__all__ = ["OAuthClient", "Settings", "StreamableHttpToStdioProxy"]
