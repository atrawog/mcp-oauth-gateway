#!/usr/bin/env python3
"""
Generic MCP stdio-to-streamable-http Proxy with proper /mcp handling
Following CLAUDE.md - Universal Proxy for Any MCP Server!

This proxy runs the OFFICIAL MCP server as a subprocess and bridges
stdio communication to HTTP endpoints.
"""
import sys
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
import subprocess
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
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
        
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming MCP request"""
        if not self.session_initialized:
            raise RuntimeError("Session not initialized")
            
        # Forward the request to the server
        if "id" not in request_data:
            self.request_id_counter += 1
            request_data["id"] = self.request_id_counter
            
        return await self._send_request(request_data)
        
    async def close(self):
        """Close the server process"""
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except:
                pass
            self.process = None


# Create FastAPI app
app = FastAPI()

# Global proxy instance
proxy: Optional[MCPStdioProxy] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the proxy on startup"""
    global proxy
    if len(sys.argv) < 2:
        raise RuntimeError("No MCP server command provided")
    server_command = sys.argv[1:]
    proxy = MCPStdioProxy()
    await proxy.start_server(server_command)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global proxy
    if proxy:
        await proxy.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if proxy and proxy.session_initialized:
        return {"status": "healthy", "server_info": proxy.server_info}
    return JSONResponse(
        status_code=503,
        content={"status": "unhealthy", "error": "Proxy not initialized"}
    )

@app.post("/mcp")
async def handle_mcp(request: Request):
    """Handle MCP requests without trailing slash redirect"""
    if not proxy:
        raise HTTPException(status_code=503, detail="Proxy not initialized")
        
    try:
        request_data = await request.json()
        response = await proxy.handle_request(request_data)
        return response
    except Exception as e:
        logger.error(f"Error handling request: {e}")
        return JSONResponse(
            status_code=500,
            content={"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": None}
        )

@app.post("/mcp/")
async def handle_mcp_trailing(request: Request):
    """Handle MCP requests with trailing slash"""
    return await handle_mcp(request)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mcp_stdio_http_proxy_fixed.py <mcp_server_command> [args...]")
        print("Example: python mcp_stdio_http_proxy_fixed.py python -m mcp_server_fetch")
        sys.exit(1)
    
    logger.info(f"Starting MCP stdio-to-HTTP proxy for: {' '.join(sys.argv[1:])}")
    
    # Run server without automatic trailing slash redirects
    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")