# MCP Everything Service

The MCP Everything service provides a unified interface to multiple MCP capabilities through a single endpoint.

## Overview

MCP Everything wraps the official `@modelcontextprotocol/server-everything` implementation, combining functionality from multiple MCP services into one comprehensive service. It's secured with OAuth 2.1 authentication and provides a convenient all-in-one solution.

## Features

### 🎯 Unified Interface
- **Single Endpoint** - Access all tools through one service
- **Consistent API** - Uniform interface across capabilities
- **Tool Discovery** - List all available tools
- **Simplified Integration** - One service to configure

### 🛠️ Combined Capabilities
- **Web Operations** - HTTP requests and content fetching
- **File Management** - File system operations
- **Time Functions** - Timezone and temporal operations
- **Data Processing** - JSON, XML, text manipulation
- **System Information** - Environment and configuration

### 📊 Tool Categories

#### Web & Network
- HTTP requests (GET, POST, PUT, DELETE)
- URL parsing and validation
- Content extraction
- API interactions

#### File System
- Read/write files
- Directory operations
- File search
- Metadata queries

#### Time & Date
- Current time
- Timezone conversions
- Date calculations
- Scheduling helpers

#### Data Processing
- JSON operations
- Text manipulation
- Encoding/decoding
- Format conversions

#### Utilities
- Random generation
- Hash calculations
- Environment info
- System queries

## Authentication

All requests require OAuth 2.1 Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     https://mcp-everything.yourdomain.com/mcp
```

## Endpoints

### Primary Endpoints
- **`/mcp`** - Main MCP protocol endpoint
- **`/mcp`** - Main MCP protocol endpoint (health checks via protocol initialization)
- **`/.well-known/oauth-authorization-server`** - OAuth discovery

## Usage Examples

### List All Available Tools

```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

### Web Request

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetch_url",
    "arguments": {
      "url": "https://api.example.com/data",
      "method": "GET"
    }
  },
  "id": 2
}
```

### File Operation

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {
      "path": "data/config.json"
    }
  },
  "id": 3
}
```

### Time Operation

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_current_time",
    "arguments": {
      "timezone": "America/New_York",
      "format": "ISO8601"
    }
  },
  "id": 4
}
```

## Available Tools

### Web Operations
- `fetch_url` - HTTP requests
- `parse_url` - URL parsing
- `extract_links` - Link extraction
- `download_file` - File downloads
- `check_url` - URL validation

### File Operations
- `read_file` - Read file contents
- `write_file` - Write to file
- `list_files` - Directory listing
- `file_info` - File metadata
- `search_files` - Find files

### Time Operations
- `get_current_time` - Current time
- `convert_timezone` - Timezone conversion
- `format_date` - Date formatting
- `date_diff` - Calculate differences
- `add_time` - Date arithmetic

### Data Processing
- `parse_json` - JSON parsing
- `stringify_json` - JSON encoding
- `encode_base64` - Base64 encoding
- `decode_base64` - Base64 decoding
- `hash_text` - Generate hashes

### Text Operations
- `uppercase` - Convert to uppercase
- `lowercase` - Convert to lowercase
- `trim` - Remove whitespace
- `split` - Split text
- `join` - Join text

### Utility Operations
- `random_string` - Generate random text
- `random_number` - Generate random numbers
- `uuid` - Generate UUIDs
- `environment_info` - System information
- `echo` - Echo input

## Configuration

### Environment Variables

```bash
# From .env file
MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION:-2025-06-18}
BASE_DOMAIN=yourdomain.com

# Everything specific
EVERYTHING_ENABLE_ALL=true
EVERYTHING_FILE_WORKSPACE=/workspace
EVERYTHING_REQUEST_TIMEOUT=30000
```

### Docker Labels

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.mcp-everything.rule=Host(`mcp-everything.${BASE_DOMAIN}`)"
  - "traefik.http.routers.mcp-everything.middlewares=mcp-auth@docker"
```

## Testing

### Integration Test
```bash
just test-file tests/test_mcp_everything_integration.py
```

### Comprehensive Test
```bash
just test-file tests/test_mcp_everything_comprehensive.py
```

### Tool-Specific Tests
```bash
just test-file tests/test_mcp_everything_tools.py
just test-file tests/test_mcp_everything_client_full.py
```

### Manual Testing
```bash
# List all tools
mcp-streamablehttp-client query https://mcp-everything.yourdomain.com/mcp \
  --token YOUR_TOKEN \
  '{"method": "tools/list"}'

# Count available tools
mcp-streamablehttp-client query https://mcp-everything.yourdomain.com/mcp \
  --token YOUR_TOKEN \
  '{"method": "tools/list"}' | jq '.result.tools | length'
```

## Tool Discovery

### List Tools by Category
```json
{
  "method": "tools/list",
  "params": {
    "category": "web"
  }
}
```

### Get Tool Details
```json
{
  "method": "tools/info",
  "params": {
    "name": "fetch_url"
  }
}
```

## Error Handling

### Common Errors

1. **Tool Not Found**
   ```json
   {
     "error": {
       "code": -32602,
       "message": "Unknown tool: invalid_tool"
     }
   }
   ```

2. **Invalid Arguments**
   ```json
   {
     "error": {
       "code": -32602,
       "message": "Missing required argument: url"
     }
   }
   ```

3. **Operation Failed**
   ```json
   {
     "error": {
       "code": -32603,
       "message": "Failed to fetch URL: connection timeout"
     }
   }
   ```

## Best Practices

### Tool Selection
- Use specific tools for clarity
- Check tool availability first
- Understand tool limitations
- Handle errors gracefully

### Performance
- Batch operations when possible
- Use appropriate timeouts
- Cache results when applicable
- Monitor resource usage

### Security
- Validate all inputs
- Use secure connections
- Respect rate limits
- Audit tool usage

## Advanced Usage

### Chained Operations
```json
{
  "method": "tools/call",
  "params": {
    "name": "chain",
    "arguments": {
      "operations": [
        {
          "tool": "fetch_url",
          "args": {"url": "https://api.example.com/data"}
        },
        {
          "tool": "parse_json",
          "args": {"use_previous_result": true}
        },
        {
          "tool": "write_file",
          "args": {"path": "data.json", "use_previous_result": true}
        }
      ]
    }
  }
}
```

### Conditional Operations
```json
{
  "method": "tools/call",
  "params": {
    "name": "conditional",
    "arguments": {
      "condition": {
        "tool": "file_exists",
        "args": {"path": "config.json"}
      },
      "if_true": {
        "tool": "read_file",
        "args": {"path": "config.json"}
      },
      "if_false": {
        "tool": "write_file",
        "args": {"path": "config.json", "content": "{}"}
      }
    }
  }
}
```

## Use Cases

### Data Pipeline
1. Fetch data from API
2. Parse and transform
3. Save to file
4. Generate report

### Web Monitoring
1. Check URL status
2. Extract content
3. Compare with previous
4. Alert on changes

### File Processing
1. List files in directory
2. Read each file
3. Process content
4. Write results

### Time-Based Tasks
1. Get current time
2. Calculate next run
3. Schedule operation
4. Log execution

## Troubleshooting

### Service Issues
```bash
# Check container status
docker ps | grep mcp-everything

# View logs
docker logs mcp-everything

# Protocol health check via MCP initialization
curl -X POST https://mcp-everything.yourdomain.com/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"'"${MCP_PROTOCOL_VERSION:-2025-06-18}"'","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'
```

### Tool Problems
```bash
# List available tools
curl -X POST https://mcp-everything.yourdomain.com/mcp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"method": "tools/list"}' | jq '.result.tools[].name'

# Test specific tool
curl -X POST https://mcp-everything.yourdomain.com/mcp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"method": "tools/call", "params": {"name": "echo", "arguments": {"message": "test"}}}'
```

## Performance Considerations

- **Tool Loading** - All tools loaded at startup
- **Memory Usage** - ~100MB base memory
- **Request Handling** - Synchronous processing
- **Timeout Settings** - 30s default timeout
- **Concurrent Requests** - Thread-safe operations

## Comparison with Individual Services

### Advantages
- Single endpoint to manage
- Unified authentication
- Simplified deployment
- Consistent interface
- Reduced complexity

### Trade-offs
- Larger memory footprint
- All tools loaded regardless of use
- Single point of failure
- Less granular scaling
- Potential feature lag

## Related Documentation

- {doc}`mcp-fetch` - Dedicated fetch service
- {doc}`mcp-filesystem` - Dedicated filesystem service
- {doc}`mcp-time` - Dedicated time service
- {doc}`../integration/index` - Integration guides
- {doc}`../architecture/mcp-protocol` - Protocol details