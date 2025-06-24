# mcp-fetch-streamablehttp-client

Pure Python client for MCP fetch servers using the Streamable HTTP transport.

## Overview

This package provides a lightweight, pure Python client specifically designed for interacting with MCP fetch servers over the Streamable HTTP transport protocol. It implements the MCP 2025-06-18 specification and provides both a programmatic API and command-line interface.

## Features

- 🐍 **Pure Python**: No external dependencies beyond standard HTTP libraries
- 🌐 **Streamable HTTP Transport**: Full support for MCP protocol over HTTP
- 🔑 **OAuth Support**: Built-in Bearer token authentication
- 🛠️ **CLI Tool**: Rich command-line interface for quick interactions
- 📊 **Type Safety**: Full type hints and Pydantic models
- 🎨 **Rich Output**: Beautiful formatted output with syntax highlighting

## Installation

### Using pixi (Recommended)

```bash
pixi add mcp-fetch-streamablehttp-client
```

### Using pip

```bash
pip install mcp-fetch-streamablehttp-client
```

## Quick Start

### Command Line

```bash
# Get server info
mcp-fetch-client info --server-url http://localhost:3000

# Fetch a URL
mcp-fetch-client fetch https://example.com

# Fetch with authentication
export MCP_ACCESS_TOKEN=your-bearer-token
mcp-fetch-client fetch https://api.example.com/data

# Fetch with custom headers
mcp-fetch-client fetch https://api.example.com \
  -H "User-Agent: MyApp/1.0" \
  -H "Accept: application/json"

# POST request with data
mcp-fetch-client fetch https://api.example.com/users \
  -m POST \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe"}'
```

### Python API

```python
import asyncio
from mcp_fetch_streamablehttp_client import MCPFetchClient

async def main():
    # Create client
    async with MCPFetchClient("http://localhost:3000") as client:
        # Initialize session
        info = await client.initialize()
        print(f"Connected to: {info['serverInfo']['name']}")
        
        # Fetch a URL
        result = await client.fetch("https://example.com")
        print(f"Status: {result.status}")
        print(f"Content: {result.text[:200]}...")
        
        # Fetch with headers
        result = await client.fetch(
            "https://api.github.com/user",
            headers={"Authorization": "token ghp_xxxx"}
        )

asyncio.run(main())
```

### With OAuth Authentication

```python
async with MCPFetchClient(
    "http://localhost:3000",
    access_token="your-bearer-token"
) as client:
    await client.initialize()
    result = await client.fetch("https://api.example.com/protected")
```

## CLI Commands

### info

Get server information and capabilities:

```bash
mcp-fetch-client info [OPTIONS]

Options:
  --server-url TEXT  MCP server URL [env: MCP_SERVER_URL]
  --token TEXT       Bearer token [env: MCP_ACCESS_TOKEN]
```

### fetch

Fetch a URL through the MCP server:

```bash
mcp-fetch-client fetch URL [OPTIONS]

Options:
  --server-url TEXT     MCP server URL [env: MCP_SERVER_URL]
  --token TEXT          Bearer token [env: MCP_ACCESS_TOKEN]
  -m, --method TEXT     HTTP method (GET, POST, etc.)
  -H, --header TEXT     HTTP headers (multiple allowed)
  -d, --data TEXT       Request body data
  --json-output         Output raw JSON response
```

### tools

List available tools on the server:

```bash
mcp-fetch-client tools [OPTIONS]

Options:
  --server-url TEXT  MCP server URL [env: MCP_SERVER_URL]
  --token TEXT       Bearer token [env: MCP_ACCESS_TOKEN]
```

### call

Call a tool on the server:

```bash
mcp-fetch-client call TOOL_NAME [OPTIONS]

Options:
  --server-url TEXT     MCP server URL [env: MCP_SERVER_URL]
  --token TEXT          Bearer token [env: MCP_ACCESS_TOKEN]
  -a, --arg TEXT        Tool arguments as key=value
  --json-args TEXT      Tool arguments as JSON string
```

## Environment Variables

- `MCP_SERVER_URL`: Default MCP server URL (default: http://localhost:3000)
- `MCP_ACCESS_TOKEN`: Bearer token for authentication

## API Reference

### MCPFetchClient

Main client class for interacting with MCP fetch servers.

#### Constructor

```python
MCPFetchClient(
    base_url: str,
    access_token: Optional[str] = None,
    timeout: float = 30.0,
    headers: Optional[Dict[str, str]] = None
)
```

#### Methods

- `async initialize()`: Initialize MCP session
- `async fetch(url, method="GET", headers=None, body=None)`: Fetch a URL
- `async list_tools()`: List available tools
- `async call_tool(name, arguments=None)`: Call a server tool
- `async close()`: Close the client connection

#### Properties

- `capabilities`: Server capabilities dictionary
- `server_info`: Server information dictionary

### Exceptions

- `MCPError`: Base exception for all MCP errors
- `MCPTransportError`: HTTP transport errors
- `MCPProtocolError`: MCP protocol errors

## Examples

### Fetch JSON Data

```python
async with MCPFetchClient("http://localhost:3000") as client:
    await client.initialize()
    
    # Fetch JSON API
    result = await client.fetch(
        "https://api.github.com/repos/modelcontextprotocol/servers",
        headers={"Accept": "application/vnd.github.v3+json"}
    )
    
    if result.mimeType == "application/json":
        import json
        data = json.loads(result.text)
        print(f"Stars: {data['stargazers_count']}")
```

### Post Data

```python
async with MCPFetchClient("http://localhost:3000") as client:
    await client.initialize()
    
    # POST JSON data
    result = await client.fetch(
        "https://httpbin.org/post",
        method="POST",
        headers={"Content-Type": "application/json"},
        body='{"key": "value"}'
    )
    
    print(f"Response status: {result.status}")
```

### Error Handling

```python
from mcp_fetch_streamablehttp_client import MCPFetchClient, MCPError

try:
    async with MCPFetchClient("http://localhost:3000") as client:
        await client.initialize()
        result = await client.fetch("https://invalid-url")
except MCPError as e:
    print(f"MCP Error: {e}")
```

## Development

### Running Tests

```bash
# Install dev dependencies
pixi install --with dev

# Run tests
pixi run pytest

# Run with coverage
pixi run pytest --cov=mcp_fetch_streamablehttp_client
```

### Type Checking

```bash
pixi run mypy src/
```

### Linting

```bash
pixi run ruff check src/
pixi run black src/
```

## License

Apache License 2.0

## See Also

- [MCP Protocol Specification](https://github.com/modelcontextprotocol/specification)
- [mcp-streamablehttp-proxy](../mcp-streamablehttp-proxy) - Server-side proxy
- [mcp-streamablehttp-client](../mcp-streamablehttp-client) - General purpose client