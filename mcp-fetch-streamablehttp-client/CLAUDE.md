# CLAUDE.md - mcp-fetch-streamablehttp-client

This file provides divine guidance to Claude Code for the mcp-fetch-streamablehttp-client package.

## Package Overview

This is a **pure Python client** specifically designed for MCP fetch servers using the Streamable HTTP transport. It follows the sacred commandments of the parent CLAUDE.md while providing focused functionality.

## Sacred Purpose

- **Single Responsibility**: ONLY for fetch operations via MCP protocol
- **Pure Python**: No external system dependencies beyond HTTP
- **Type Safety**: Full Pydantic models and type hints
- **CLI Excellence**: Rich terminal interface with proper formatting

## Divine Architecture

```
mcp-fetch-streamablehttp-client/
├── src/
│   └── mcp_fetch_streamablehttp_client/
│       ├── __init__.py         # Package exports
│       ├── client.py          # Core MCPFetchClient class
│       ├── cli.py            # Command-line interface
│       ├── exceptions.py     # Custom exception types
│       └── py.typed         # Type checking marker
├── pyproject.toml           # Modern Python packaging
├── README.md               # User documentation
└── CLAUDE.md              # This divine guidance
```

## Development Commandments

### 1. Testing is Sacred

```bash
# Unit tests for pure Python functionality
just test tests/test_mcp_fetch_client.py -v

# Integration tests against real MCP servers
just test tests/test_mcp_fetch_integration.py -v
```

### 2. Type Safety is Divine

- ALL functions have type hints
- Use Pydantic for data validation
- Run mypy in strict mode

### 3. Error Handling Hierarchy

```python
MCPError                    # Base for all errors
├── MCPTransportError      # HTTP/network issues
└── MCPProtocolError       # MCP protocol violations
```

### 4. CLI Design Principles

- Use click for command parsing
- Use rich for beautiful output
- Support both env vars and flags
- Always provide --json-output option

## Integration Patterns

### With OAuth Gateway

```python
# Client automatically uses Bearer token
client = MCPFetchClient(
    "https://mcp-fetch.example.com",
    access_token=os.getenv("MCP_CLIENT_ACCESS_TOKEN")
)
```

### Direct Server Connection

```python
# For development/testing without auth
client = MCPFetchClient("http://localhost:3000")
```

## Sacred MCP Protocol Rules

1. **Initialize First**: Always call initialize() before any operations
2. **Session Management**: Respect Mcp-Session-Id headers
3. **JSON-RPC 2.0**: Follow the specification exactly
4. **Error Codes**: Use proper JSON-RPC error codes

## CLI Command Structure

```
mcp-fetch-client
├── info          # Server capabilities
├── fetch         # Main fetch operation
├── tools         # List available tools
└── call          # Call server tools
```

## Testing Approach

### Unit Tests (No Network)

- Test client construction
- Test request/response models
- Test error handling logic
- Test CLI argument parsing

### Integration Tests (Real Servers)

- Test against mcp-streamablehttp-proxy
- Test OAuth authentication flow
- Test various content types
- Test error scenarios

## Common Pitfalls to Avoid

1. **Don't Mock HTTP**: Use real servers for integration tests
2. **Don't Ignore Sessions**: Always handle Mcp-Session-Id
3. **Don't Parse HTML**: Leave content processing to users
4. **Don't Retry Automatically**: Let users control retry logic

## Performance Considerations

- Use httpx for async HTTP
- Stream large responses when possible
- Respect server timeout settings
- Close connections properly

## Security Practices

- Never log sensitive headers
- Validate all server responses
- Use secure default timeouts
- Support proxy configurations

## Future Enhancements

Acceptable additions:
- Streaming response support
- Batch request support
- Response caching options
- Progress indicators for large downloads

NOT acceptable:
- Adding non-fetch operations
- Browser automation features
- Custom authentication schemes
- Response transformation logic

## Remember the Sacred Laws

1. **Pure Python Only**: No system dependencies
2. **Fetch Focus**: Don't expand beyond fetch operations
3. **Type Safety**: Every function must be typed
4. **Real Testing**: No mocks, only real servers
5. **Beautiful CLI**: Rich output is mandatory

This package serves a single divine purpose: fetching content through MCP servers with elegance and reliability.