"""MCP OAuth Dynamic Client Registration Package
Following OAuth 2.1 and RFC 7591 divine specifications
"""

__version__ = "0.1.0"

from .config import Settings
from .models import ClientRegistration, ErrorResponse, TokenResponse


# Import create_app lazily to avoid circular imports
def __getattr__(name):
    if name == "create_app":
        from .server import create_app

        return create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ClientRegistration", "ErrorResponse", "Settings", "TokenResponse", "create_app"]
