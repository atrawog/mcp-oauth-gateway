# MCP Echo StreamableHTTP Server - Stateless

A stateless MCP (Model Context Protocol) server that implements echo and printEnv tools using the StreamableHTTP transport.

## Features

- **Stateless Operation**: No session management, each request is independent
- **Echo Tool**: Returns the provided message
- **PrintEnv Tool**: Prints environment variable values
- **Debug Mode**: Detailed message tracing for development
- **Strict MCP Compliance**: Follows the MCP specification exactly

## Installation

```bash
pip install -e .
```

## Usage

### Running the Server

```bash
# Basic usage
mcp-echo-streamablehttp-server-stateless

# With custom host and port
mcp-echo-streamablehttp-server-stateless --host 127.0.0.1 --port 3000

# With debug logging
mcp-echo-streamablehttp-server-stateless --debug
```

### Environment Variables

- `MCP_ECHO_HOST`: Host to bind to (default: 0.0.0.0)
- `MCP_ECHO_PORT`: Port to bind to (default: 3000)
- `MCP_ECHO_DEBUG`: Enable debug logging (true/false, default: false)

### Available Tools

#### echo
Echoes back the provided message.

**Parameters:**
- `message` (string, required): The message to echo back

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "echo",
    "arguments": {
      "message": "Hello, World!"
    }
  },
  "id": 1
}
```

#### printEnv
Prints the value of an environment variable.

**Parameters:**
- `name` (string, required): The name of the environment variable

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "printEnv",
    "arguments": {
      "name": "PATH"
    }
  },
  "id": 2
}
```

## Development

### Debug Mode

Enable debug mode to see detailed message traces:

```bash
mcp-echo-streamablehttp-server-stateless --debug
```

This will log all incoming requests and outgoing responses.

### Testing with curl

Initialize the server:
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    },
    "id": 1
  }'
```

Call the echo tool:
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {
        "message": "Hello from MCP!"
      }
    },
    "id": 2
  }'
```

## License

MIT