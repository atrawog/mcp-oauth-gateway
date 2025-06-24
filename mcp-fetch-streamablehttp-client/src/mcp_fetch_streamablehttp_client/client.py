"""Pure Python client for MCP fetch server over Streamable HTTP transport."""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import httpx
from pydantic import BaseModel, Field

from .exceptions import MCPError, MCPProtocolError, MCPTransportError

logger = logging.getLogger(__name__)


class MCPRequest(BaseModel):
    """JSON-RPC 2.0 request."""
    
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Union[str, int] = Field(default_factory=lambda: str(uuid4()))


class MCPResponse(BaseModel):
    """JSON-RPC 2.0 response."""
    
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Union[str, int, None] = None


class FetchResult(BaseModel):
    """Result from a fetch operation."""
    
    text: Optional[str] = None
    mimeType: Optional[str] = None
    blob: Optional[str] = None  # Base64 encoded
    status: int = 200
    headers: Dict[str, str] = Field(default_factory=dict)


class MCPFetchClient:
    """Pure Python client for MCP fetch server over Streamable HTTP transport."""
    
    def __init__(
        self,
        base_url: str,
        access_token: Optional[str] = None,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize the MCP fetch client.
        
        Args:
            base_url: Base URL of the MCP server (e.g., http://localhost:3000)
            access_token: Optional Bearer token for authentication
            timeout: Request timeout in seconds
            headers: Additional headers to include in requests
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session_id: Optional[str] = None
        
        # Set up default headers
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        
        if headers:
            self._headers.update(headers)
            
        if access_token:
            self._headers["Authorization"] = f"Bearer {access_token}"
            
        # Create HTTP client
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers=self._headers,
        )
        
        # Track initialization state
        self._initialized = False
        self._capabilities: Dict[str, Any] = {}
        self._server_info: Dict[str, Any] = {}
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def _make_request(self, request: MCPRequest) -> MCPResponse:
        """Make a JSON-RPC request to the server.
        
        Args:
            request: The JSON-RPC request to send
            
        Returns:
            The JSON-RPC response
            
        Raises:
            MCPTransportError: For HTTP-level errors
            MCPProtocolError: For JSON-RPC errors
        """
        headers = {}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        try:
            response = await self._client.post(
                f"{self.base_url}/mcp",
                json=request.model_dump(exclude_none=True),
                headers=headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise MCPTransportError(f"HTTP error: {e}") from e
        
        # Extract session ID from response headers
        if "Mcp-Session-Id" in response.headers:
            self.session_id = response.headers["Mcp-Session-Id"]
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise MCPProtocolError(f"Invalid JSON response: {e}") from e
        
        mcp_response = MCPResponse(**data)
        
        # Check for JSON-RPC errors
        if mcp_response.error:
            raise MCPProtocolError(
                mcp_response.error.get("message", "Unknown error"),
                code=mcp_response.error.get("code"),
                data=mcp_response.error.get("data"),
            )
        
        return mcp_response
    
    async def initialize(
        self,
        client_name: str = "mcp-fetch-client",
        client_version: str = "0.1.0",
        protocol_version: str = "2025-06-18",
    ) -> Dict[str, Any]:
        """Initialize the MCP session.
        
        Args:
            client_name: Name of the client
            client_version: Version of the client
            protocol_version: MCP protocol version to use
            
        Returns:
            Server initialization response with capabilities
            
        Raises:
            MCPError: If already initialized or initialization fails
        """
        if self._initialized:
            raise MCPError("Client already initialized")
        
        request = MCPRequest(
            method="initialize",
            params={
                "protocolVersion": protocol_version,
                "capabilities": {},
                "clientInfo": {
                    "name": client_name,
                    "version": client_version,
                },
            },
        )
        
        response = await self._make_request(request)
        
        if not response.result:
            raise MCPProtocolError("Initialize returned no result")
        
        self._capabilities = response.result.get("capabilities", {})
        self._server_info = response.result.get("serverInfo", {})
        self._initialized = True
        
        # Send initialized notification
        await self._make_request(MCPRequest(method="initialized"))
        
        return response.result
    
    async def fetch(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
    ) -> FetchResult:
        """Fetch a URL using the MCP server.
        
        Args:
            url: URL to fetch
            method: HTTP method (GET, POST, etc.)
            headers: HTTP headers to include
            body: Request body for POST/PUT requests
            
        Returns:
            FetchResult containing the response
            
        Raises:
            MCPError: If not initialized
            MCPProtocolError: For protocol errors
        """
        if not self._initialized:
            raise MCPError("Client not initialized. Call initialize() first.")
        
        # Check if fetch capability is available
        if "resources" not in self._capabilities:
            raise MCPError("Server does not support resources/fetch capability")
        
        params = {
            "url": url,
            "method": method,
        }
        
        if headers:
            params["headers"] = headers
            
        if body:
            params["body"] = body
        
        request = MCPRequest(
            method="resources/fetch",
            params=params,
        )
        
        response = await self._make_request(request)
        
        if not response.result:
            raise MCPProtocolError("Fetch returned no result")
        
        return FetchResult(**response.result)
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the server.
        
        Returns:
            List of tool definitions
            
        Raises:
            MCPError: If not initialized
        """
        if not self._initialized:
            raise MCPError("Client not initialized. Call initialize() first.")
        
        request = MCPRequest(method="tools/list")
        response = await self._make_request(request)
        
        return response.result.get("tools", []) if response.result else []
    
    async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """Call a tool on the server.
        
        Args:
            name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            MCPError: If not initialized or tool not found
        """
        if not self._initialized:
            raise MCPError("Client not initialized. Call initialize() first.")
        
        request = MCPRequest(
            method="tools/call",
            params={
                "name": name,
                "arguments": arguments or {},
            },
        )
        
        response = await self._make_request(request)
        return response.result
    
    @property
    def capabilities(self) -> Dict[str, Any]:
        """Get server capabilities."""
        return self._capabilities.copy()
    
    @property
    def server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return self._server_info.copy()