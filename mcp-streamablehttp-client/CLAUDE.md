# CLAUDE.md - MCP Streamable HTTP Client Development Guide

This file provides guidance to Claude Code when working with the mcp-streamablehttp-client codebase.

## Overview

The mcp-streamablehttp-client is a bridge tool that enables stdio-based MCP clients (like Claude Desktop) to connect to streamable HTTP-based MCP servers that require OAuth authentication. It handles the complete OAuth flow and provides several testing and debugging capabilities.

## Key Features Added (2025-06-22)

### 1. Raw Protocol Mode (`--raw`)
- Allows sending raw JSON-RPC requests directly to the MCP server
- Automatically handles initialization and session management
- Returns the full JSON-RPC response for analysis
- Essential for protocol compliance testing

Example usage:
```bash
mcp-streamablehttp-client --raw '{"method": "tools/list", "params": {}}'
```

### 2. Listing Commands
- `--list-tools`: Lists all available MCP tools with their schemas
- `--list-resources`: Lists all available MCP resources
- `--list-prompts`: Lists all available MCP prompts with arguments

These commands:
- Automatically handle initialization
- Format output in both human-readable and JSON formats
- Show parameter requirements and descriptions

### 3. Enhanced Command Parsing
The `parse_tool_arguments()` function in `cli.py` now supports:
- Special handling for the `echo` tool (uses "message" parameter)
- JSON argument parsing: `--command 'tool {"key": "value"}'`
- Key=value parsing: `--command "tool key1=value1 key2=value2"`
- Smart defaults based on tool name patterns

## Architecture

### Core Components

1. **cli.py**: Command-line interface and argument parsing
   - `main()`: Entry point with all CLI options
   - `async_main()`: Async orchestrator for different modes
   - `execute_mcp_command()`: Handles tool execution via --command
   - `execute_raw_protocol()`: Handles raw JSON-RPC requests
   - `execute_list_command()`: Handles listing tools/resources/prompts
   - `parse_tool_arguments()`: Smart argument parsing for tools

2. **proxy.py**: The core proxy that bridges stdio ↔ streamable HTTP
   - `StreamableHttpToStdioProxy`: Main proxy class
   - `_handle_request()`: Processes JSON-RPC requests
   - Handles session management with `Mcp-Session-Id` headers
   - Automatically sends `notifications/initialized` after initialization
   - Parses both JSON and SSE (text/event-stream) responses

3. **oauth.py**: OAuth authentication handling
   - Device flow authentication
   - Token refresh logic
   - Dynamic client registration (RFC 7591)
   - Client management (RFC 7592)

4. **config.py**: Configuration management via pydantic settings

## Testing Integration

The client is extensively tested with the mcp-everything server using:
- `test_mcp_everything_client_full.py`: Uses raw protocol mode for comprehensive testing
- `test_mcp_everything_comprehensive.py`: Tests tool execution with --command
- `test_mcp_everything_client_simple.py`: Basic connectivity tests

### Test Patterns

1. **Raw Protocol Testing**:
   ```python
   cmd = ["pixi", "run", "mcp-streamablehttp-client", "--raw", json.dumps(request)]
   ```

2. **Tool Command Testing**:
   ```python
   cmd = ["pixi", "run", "mcp-streamablehttp-client", "--command", "echo Hello"]
   ```

3. **Listing Testing**:
   ```python
   cmd = ["pixi", "run", "mcp-streamablehttp-client", "--list-tools"]
   ```

## Important Implementation Details

### Session Management
- Session ID comes from response headers (`Mcp-Session-Id`), not JSON body
- Session ID must be included in all subsequent requests after initialization
- Don't include session ID in the initialize request itself

### Response Parsing
- Responses can be multi-line JSON or SSE format
- SSE responses have format: `data: {json}\n\n`
- The response parser in tests looks for all JSON objects and returns the last JSON-RPC response

### Protocol Compliance
- Always send `notifications/initialized` after successful initialization
- The server returns 202 Accepted for notifications (not 200 OK)
- Accept header must include `application/json, text/event-stream`

### Error Handling
- 406 Not Acceptable: Missing or incorrect Accept header
- 401 Unauthorized: Token expired or invalid
- 400 Bad Request: Malformed request or missing required fields

## Development Workflow

1. **Making Changes**:
   - Always reinstall after changes: `pixi run pip install -e ./mcp-streamablehttp-client`
   - Test with simple commands first: `--list-tools`, `--command "echo test"`
   - Use `--raw` for protocol-level debugging

2. **Adding New Features**:
   - Add CLI options in `main()` function
   - Update function signatures in `async_main()`
   - Implement handlers before command processing
   - Update tests to use new features

3. **Testing**:
   - Unit tests: Focus on argument parsing and response handling
   - Integration tests: Use real mcp-everything server
   - Always test both success and error cases

## Common Issues and Solutions

1. **"Initialize is automatic" error**: The command parser is receiving quoted strings incorrectly. Use single words or JSON format.

2. **Session ID issues**: Ensure session ID is extracted from headers, not JSON response body.

3. **JSON parsing errors**: The client output includes logging. Parse from the end of output backwards to find JSON responses.

4. **Authentication failures**: Check MCP_CLIENT_ACCESS_TOKEN in .env is valid and not expired.

## Future Enhancements

Potential improvements to consider:
- WebSocket support for real-time updates
- Batch request support
- Progress indicators for long-running operations
- Response streaming for large payloads
- Built-in response validation against schemas
