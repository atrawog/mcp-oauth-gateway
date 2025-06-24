"""Exception types for MCP client."""


class MCPError(Exception):
    """Base exception for all MCP-related errors."""
    pass


class MCPTransportError(MCPError):
    """Raised when there's an error in the transport layer (HTTP)."""
    pass


class MCPProtocolError(MCPError):
    """Raised when there's an error in the MCP protocol layer."""
    
    def __init__(self, message: str, code: int = None, data: dict = None):
        super().__init__(message)
        self.code = code
        self.data = data