"""Fetch tool implementation for MCP server."""

import base64
import logging
from typing import Any, Dict, List, Optional, Union

import httpx
from bs4 import BeautifulSoup
from mcp import Tool
from mcp.types import TextContent, ImageContent
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

try:
    from robotspy import Robots
    HAS_ROBOTSPY = True
except ImportError:
    logger.warning("robotspy not available, robots.txt checking disabled")
    HAS_ROBOTSPY = False


class FetchArguments(BaseModel):
    """Arguments for the fetch tool."""
    url: str = Field(description="URL to fetch")
    method: str = Field(default="GET", description="HTTP method (GET or POST)")
    headers: Optional[Dict[str, str]] = Field(default=None, description="HTTP headers")
    body: Optional[str] = Field(default=None, description="Request body for POST")
    max_length: int = Field(default=100000, description="Maximum response length")
    user_agent: str = Field(
        default="ModelContextProtocol/1.0",
        description="User agent string"
    )


class FetchHandler:
    """Handler for fetch tool operations."""
    
    def __init__(self, allowed_schemes: List[str] = None, max_redirects: int = 5):
        self.allowed_schemes = allowed_schemes or ["http", "https"]
        self.max_redirects = max_redirects
        self._robots_cache: Dict[str, Robots] = {}
        
    def get_tools(self) -> List[Tool]:
        """Return list of available tools."""
        return [
            Tool(
                name="fetch",
                description="Fetch a URL and return its contents",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to fetch"
                        },
                        "method": {
                            "type": "string",
                            "enum": ["GET", "POST"],
                            "default": "GET",
                            "description": "HTTP method"
                        },
                        "headers": {
                            "type": "object",
                            "description": "HTTP headers",
                            "additionalProperties": {"type": "string"}
                        },
                        "body": {
                            "type": "string",
                            "description": "Request body for POST"
                        },
                        "max_length": {
                            "type": "integer",
                            "default": 100000,
                            "description": "Maximum response length"
                        },
                        "user_agent": {
                            "type": "string",
                            "default": "ModelContextProtocol/1.0",
                            "description": "User agent string"
                        }
                    },
                    "required": ["url"]
                }
            )
        ]
        
    async def handle_fetch(self, arguments: Dict[str, Any]) -> List[Union[TextContent, ImageContent]]:
        """Handle fetch tool call."""
        
        # Parse arguments
        args = FetchArguments(**arguments)
        
        # Validate URL scheme
        parsed = httpx.URL(args.url)
        if parsed.scheme not in self.allowed_schemes:
            raise ValueError(f"URL scheme {parsed.scheme} not allowed")
        
        # Prevent SSRF attacks to internal IPs
        if parsed.host:
            host_lower = parsed.host.lower()
            # Block localhost and common internal addresses
            blocked_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"]
            if host_lower in blocked_hosts:
                raise ValueError(f"Access to {parsed.host} is not allowed")
            
            # Block AWS metadata service
            if host_lower == "169.254.169.254":
                raise ValueError(f"Access to AWS metadata service is not allowed")
            
            # Block private IP ranges (simplified check)
            if host_lower.startswith("10.") or host_lower.startswith("172.") or host_lower.startswith("192.168."):
                raise ValueError(f"Access to private IP addresses is not allowed")
            
        # Check robots.txt if available
        if HAS_ROBOTSPY:
            if not await self._check_robots(parsed, args.user_agent):
                raise ValueError(f"Fetching {args.url} is disallowed by robots.txt")
            
        # Prepare headers
        headers = args.headers or {}
        headers["User-Agent"] = args.user_agent
        
        # Create HTTP client
        async with httpx.AsyncClient(follow_redirects=True, max_redirects=self.max_redirects) as client:
            try:
                # Make request
                if args.method == "POST":
                    response = await client.post(
                        args.url,
                        headers=headers,
                        content=args.body,
                        timeout=30.0
                    )
                else:
                    response = await client.get(
                        args.url,
                        headers=headers,
                        timeout=30.0
                    )
                    
                response.raise_for_status()
                
            except httpx.HTTPStatusError as e:
                raise ValueError(f"HTTP {e.response.status_code}: {e.response.text}")
            except httpx.RequestError as e:
                raise ValueError(f"Request failed: {str(e)}")
                
        # Process response based on content type
        content_type = response.headers.get("content-type", "").lower()
        
        if content_type.startswith("image/"):
            # Handle image content
            image_data = response.content
            if len(image_data) > args.max_length:
                raise ValueError(f"Image too large: {len(image_data)} bytes")
                
            # Convert to base64
            base64_data = base64.b64encode(image_data).decode("utf-8")
            mime_type = content_type.split(";")[0].strip()
            
            return [ImageContent(
                type="image",
                data=base64_data,
                mimeType=mime_type
            )]
            
        else:
            # Handle text content
            try:
                text = response.text
            except UnicodeDecodeError:
                # Fallback to bytes representation
                text = repr(response.content)
                
            # Truncate if needed
            if len(text) > args.max_length:
                text = text[:args.max_length] + "... (truncated)"
                
            # Extract title if HTML
            title = None
            if content_type.startswith("text/html"):
                try:
                    soup = BeautifulSoup(text, "html.parser")
                    if soup.title:
                        title = soup.title.string
                except Exception:
                    pass
                    
            return [TextContent(
                type="text",
                text=text,
                title=title
            )]
            
    async def _check_robots(self, url: httpx.URL, user_agent: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        if not HAS_ROBOTSPY:
            return True  # Allow all if robotspy not available
        
        # Construct robots.txt URL
        robots_url = f"{url.scheme}://{url.host}"
        if url.port:
            robots_url += f":{url.port}"
        robots_url += "/robots.txt"
        
        # Check cache
        cache_key = f"{url.host}:{url.port or 'default'}"
        if cache_key not in self._robots_cache:
            try:
                # Fetch robots.txt
                async with httpx.AsyncClient() as client:
                    response = await client.get(robots_url, timeout=5.0)
                    if response.status_code == 200:
                        self._robots_cache[cache_key] = Robots.parse(
                            robots_url,
                            response.text
                        )
                    else:
                        # No robots.txt means everything is allowed
                        self._robots_cache[cache_key] = None
            except Exception:
                # Error fetching robots.txt means we allow access
                self._robots_cache[cache_key] = None
                
        # Check if allowed
        robots = self._robots_cache.get(cache_key)
        if robots is None:
            return True
            
        return robots.can_fetch(user_agent, str(url))