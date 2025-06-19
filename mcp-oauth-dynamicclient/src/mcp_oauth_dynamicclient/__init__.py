"""
MCP OAuth Dynamic Client Registration Package
Following OAuth 2.1 and RFC 7591 divine specifications
"""

__version__ = "0.1.0"

from .server import create_app
from .config import Settings
from .models import (
    ClientRegistration,
    TokenResponse,
    ErrorResponse
)

__all__ = [
    "create_app",
    "Settings",
    "ClientRegistration",
    "TokenResponse",
    "ErrorResponse"
]