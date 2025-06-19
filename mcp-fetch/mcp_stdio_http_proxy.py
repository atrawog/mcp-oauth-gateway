#!/usr/bin/env python3
"""
Generic MCP stdio-to-streamable-http Proxy
Following CLAUDE.md - Universal Proxy for Any MCP Server!

This proxy runs the OFFICIAL MCP server as a subprocess and bridges
stdio communication to HTTP endpoints using FastMCP.
"""
import sys
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
import subprocess
from fastmcp import FastMCP
from uuid import uuid4

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPStdioProxy:
    """Proxy that bridges stdio MCP servers to streamable HTTP"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.session_initialized = False
        self.request_id_counter = 0
        self.pending_responses: Dict[int, asyncio.Future] = {}
        self.server_capabilities: Dict[str, Any] = {}
        self.server_info: Dict[str, Any] = {}
        self.available_tools: List[Dict[str, Any]] = []
        
    async def start_server(self, server_command: List[str]):
        """Start the underlying MCP server process"""
        logger.info(f"Starting MCP server: {' '.join(server_command)}")
        
        self.process = await asyncio.create_subprocess_exec(
            *server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Start reading responses from the server
        asyncio.create_task(self._read_responses())
        
        # Initialize the session
        await self._initialize_session()
        
    async def _read_responses(self):
        """Read responses from the server stdout"""
        while self.process and self.process.stdout:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    break
                    
                line = line.decode().strip()
                if not line:
                    continue
                    
                try:
                    response = json.loads(line)
                    await self._handle_response(response)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from server: {line}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error reading from server: {e}")
                break
                
    async def _handle_response(self, response: Dict[str, Any]):
        """Handle a response from the server"""
        request_id = response.get("id")
        
        if request_id is not None and request_id in self.pending_responses:
            # This is a response to one of our requests
            future = self.pending_responses.pop(request_id)
            if not future.cancelled():
                future.set_result(response)
        else:
            # This might be a notification or unsolicited message
            logger.debug(f"Received unsolicited message: {response}")
            
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the server and wait for response"""
        if not self.process or not self.process.stdin:
            raise RuntimeError("Server process not available")
            
        request_id = request.get("id")
        if request_id is not None:
            # Create future for response
            future = asyncio.Future()
            self.pending_responses[request_id] = future
            
        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        if request_id is not None:
            # Wait for response
            try:
                response = await asyncio.wait_for(future, timeout=30.0)
                return response
            except asyncio.TimeoutError:
                self.pending_responses.pop(request_id, None)
                raise RuntimeError("Request timeout")
        
        return {}
        
    async def _initialize_session(self):
        """Initialize the MCP session"""
        self.request_id_counter += 1
        
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "mcp-stdio-http-proxy",
                    "version": "1.0.0"
                }
            },
            "id": self.request_id_counter
        }
        
        response = await self._send_request(init_request)
        
        if "error" in response:
            raise RuntimeError(f"Initialization failed: {response['error']}")
            
        result = response.get("result", {})
        self.server_capabilities = result.get("capabilities", {})
        self.server_info = result.get("serverInfo", {})
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        await self._send_request(initialized_notification)
        
        # Get available tools
        await self._list_tools()
        
        self.session_initialized = True
        logger.info(f"Session initialized with server: {self.server_info}")
        
    async def _list_tools(self):
        """Get list of available tools from the server"""
        self.request_id_counter += 1
        
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": self.request_id_counter
        }
        
        response = await self._send_request(request)
        
        if "error" in response:
            logger.error(f"Failed to list tools: {response['error']}")
            return
            
        result = response.get("result", {})
        self.available_tools = result.get("tools", [])
        logger.info(f"Available tools: {[t.get('name') for t in self.available_tools]}")
        
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the underlying server"""
        if not self.session_initialized:
            raise RuntimeError("Session not initialized")
            
        self.request_id_counter += 1
        
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            },
            "id": self.request_id_counter
        }
        
        response = await self._send_request(request)
        
        if "error" in response:
            error = response["error"]
            raise RuntimeError(f"Tool call failed: {error.get('message', str(error))}")
            
        result = response.get("result", {})
        
        # Extract content from the result
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                # Join all text content
                texts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        texts.append(item.get("text", ""))
                return "\n".join(texts)
                
        return str(result)
        
    async def close(self):
        """Close the server process"""
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except:
                pass
            self.process = None


# Global proxy instance
proxy: Optional[MCPStdioProxy] = None

# Create FastMCP server
mcp = FastMCP("MCP Fetch Server (via stdio proxy)")

async def ensure_proxy():
    """Ensure the proxy is started"""
    global proxy
    if proxy is None:
        if len(sys.argv) < 2:
            raise RuntimeError("No MCP server command provided")
        server_command = sys.argv[1:]
        proxy = MCPStdioProxy()
        await proxy.start_server(server_command)
    return proxy

@mcp.tool()
async def fetch(url: str, max_size: Optional[int] = None, user_agent: Optional[str] = None) -> str:
    """
    Fetch a URL and optionally extract its contents as markdown.
    
    This is the OFFICIAL fetch tool from modelcontextprotocol/servers.
    
    Args:
        url: The URL to fetch
        max_size: Maximum download size in bytes (default 5MB)
        user_agent: Custom user agent string
        
    Returns:
        The fetched content as text or markdown
    """
    proxy_instance = await ensure_proxy()
    
    # Build arguments for the official server
    args = {"url": url}
    if max_size is not None:
        args["max_size"] = max_size
    if user_agent is not None:
        args["user_agent"] = user_agent
        
    return await proxy_instance.call_tool("fetch", args)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mcp_stdio_http_proxy.py <mcp_server_command> [args...]")
        print("Example: python mcp_stdio_http_proxy.py python -m mcp_server_fetch")
        sys.exit(1)
    
    logger.info(f"Starting MCP stdio-to-HTTP proxy for: {' '.join(sys.argv[1:])}")
    
    # Run as streamable HTTP server
    try:
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0", 
            port=3000,
            path="/mcp"
        )
    finally:
        # Cleanup
        if proxy:
            asyncio.run(proxy.close())