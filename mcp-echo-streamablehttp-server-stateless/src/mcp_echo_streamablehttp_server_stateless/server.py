"""Stateless MCP Echo Server with StreamableHTTP transport."""

import os
import logging
from typing import Any, Dict, Optional, Sequence
import uvicorn
from mcp.server import Server, StreamableHTTPServer
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ErrorData,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)
import json

# Configure logging
logger = logging.getLogger(__name__)


class EchoServer:
    """Stateless MCP Echo Server implementation."""
    
    def __init__(self, debug: bool = False):
        """Initialize the echo server.
        
        Args:
            debug: Enable debug logging for message tracing
        """
        self.debug = debug
        if debug:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # Create MCP server
        self.mcp_server = Server("mcp-echo-streamablehttp-server-stateless")
        
        # Set up tools
        self._setup_tools()
        
        # Create HTTP transport
        self.http_server = StreamableHTTPServer(self.mcp_server)
    
    def _setup_tools(self):
        """Set up the echo and printEnv tools."""
        
        @self.mcp_server.list_tools()
        async def list_tools(request: ListToolsRequest) -> ListToolsResult:
            """List available tools."""
            if self.debug:
                logger.debug(f"list_tools request: {request}")
            
            tools = [
                Tool(
                    name="echo",
                    description="Echo back the provided message",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The message to echo back"
                            }
                        },
                        "required": ["message"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="printEnv",
                    description="Print the value of an environment variable",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The name of the environment variable"
                            }
                        },
                        "required": ["name"],
                        "additionalProperties": False
                    }
                )
            ]
            
            result = ListToolsResult(tools=tools)
            if self.debug:
                logger.debug(f"list_tools response: {result}")
            return result
        
        @self.mcp_server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls."""
            if self.debug:
                logger.debug(f"call_tool request: {request}")
            
            tool_name = request.params.name
            arguments = request.params.arguments
            
            try:
                if tool_name == "echo":
                    # Echo tool implementation
                    message = arguments.get("message")
                    if not isinstance(message, str):
                        raise ValueError("message must be a string")
                    
                    result = CallToolResult(
                        content=[TextContent(type="text", text=message)]
                    )
                    
                elif tool_name == "printEnv":
                    # PrintEnv tool implementation
                    env_name = arguments.get("name")
                    if not isinstance(env_name, str):
                        raise ValueError("name must be a string")
                    
                    env_value = os.environ.get(env_name)
                    if env_value is None:
                        text = f"Environment variable '{env_name}' not found"
                    else:
                        text = f"{env_name}={env_value}"
                    
                    result = CallToolResult(
                        content=[TextContent(type="text", text=text)]
                    )
                    
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                
                if self.debug:
                    logger.debug(f"call_tool response: {result}")
                return result
                
            except Exception as e:
                error_msg = f"Tool execution error: {str(e)}"
                if self.debug:
                    logger.error(error_msg, exc_info=True)
                raise
    
    def run(self, host: str = "0.0.0.0", port: int = 3000):
        """Run the HTTP server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        if self.debug:
            logger.info(f"Starting MCP Echo Server on {host}:{port}")
        
        uvicorn.run(
            self.http_server.app,
            host=host,
            port=port,
            log_level="debug" if self.debug else "info"
        )