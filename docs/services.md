# MCP Services

The MCP OAuth Gateway provides secure access to various Model Context Protocol (MCP) services. Each service extends Claude's capabilities in specific domains.

## Available Services

```{toctree}
:maxdepth: 2

services/overview
services/fetch
services/filesystem
services/memory
services/time
services/sequential-thinking
services/others
```

## Service Categories

### Core Services

These services provide fundamental capabilities:

- **[Fetch Service](services/fetch.md)** - Web content retrieval and processing
- **[Filesystem Service](services/filesystem.md)** - File system operations
- **[Memory Service](services/memory.md)** - Persistent memory and context

### Utility Services

Additional services for specialized tasks:

- **[Time Service](services/time.md)** - Time and date operations
- **[Sequential Thinking](services/sequential-thinking.md)** - Structured reasoning
- **[Other Services](services/others.md)** - Additional MCP implementations

## Managing Services

Services can be managed using the `just` command interface:

```bash
# Start all services
just up

# Start specific service
just up mcp-fetch

# View service logs
just logs mcp-fetch

# Rebuild service
just rebuild mcp-fetch
```

## Adding New Services

To add your own MCP service to the gateway, see [Adding New Services](development/adding-services.md).