# MCP Tmux Service

The MCP Tmux service provides programmatic control over terminal multiplexer sessions through the Model Context Protocol.

## Overview

MCP Tmux wraps the official `@modelcontextprotocol/server-tmux` implementation, exposing tmux functionality via HTTP endpoints secured with OAuth 2.1 authentication.

## Features

### 🖥️ Session Management
- **Create Sessions** - Start new tmux sessions programmatically
- **List Sessions** - Enumerate active sessions
- **Kill Sessions** - Terminate sessions cleanly
- **Attach/Detach** - Control session attachment

### 🪟 Window Operations
- **Create Windows** - Add new windows to sessions
- **Switch Windows** - Navigate between windows
- **Rename Windows** - Set descriptive names
- **Close Windows** - Remove windows cleanly

### 📐 Pane Control
- **Split Panes** - Horizontal and vertical splits
- **Navigate Panes** - Move between panes
- **Resize Panes** - Adjust pane dimensions
- **Send Commands** - Execute commands in specific panes

### 📝 Command Execution
- **Send Keys** - Type text into panes
- **Run Commands** - Execute shell commands
- **Capture Output** - Read pane contents
- **Clear Panes** - Reset pane content

## Authentication

All requests require OAuth 2.1 Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     https://mcp-tmux.yourdomain.com/mcp
```

## Endpoints

### Primary Endpoints
- **`/mcp`** - Main MCP protocol endpoint
- **`/mcp`** - Main MCP protocol endpoint (health checks via protocol initialization)
- **`/.well-known/oauth-authorization-server`** - OAuth discovery

## Usage Examples

### Create a New Session

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "create_session",
    "arguments": {
      "session_name": "dev-environment",
      "window_name": "editor"
    }
  },
  "id": 1
}
```

### Split Window into Panes

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "split_window",
    "arguments": {
      "session_name": "dev-environment",
      "direction": "horizontal",
      "percentage": 50
    }
  },
  "id": 2
}
```

### Send Command to Pane

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "send_keys",
    "arguments": {
      "session_name": "dev-environment",
      "pane_index": 0,
      "keys": "npm run dev",
      "enter": true
    }
  },
  "id": 3
}
```

## Available Tools

### Session Management
- `create_session` - Create a new tmux session
- `list_sessions` - List all active sessions
- `kill_session` - Terminate a session
- `rename_session` - Change session name

### Window Management
- `create_window` - Add a new window
- `list_windows` - List windows in a session
- `select_window` - Switch to a window
- `rename_window` - Change window name
- `kill_window` - Close a window

### Pane Operations
- `split_window` - Split into panes
- `select_pane` - Focus on a pane
- `resize_pane` - Adjust pane size
- `kill_pane` - Close a pane
- `list_panes` - Enumerate panes

### Command Execution
- `send_keys` - Send keystrokes to pane
- `capture_pane` - Read pane contents
- `clear_pane` - Clear pane content
- `run_command` - Execute shell command

## Configuration

### Environment Variables

```bash
# From .env file
MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION:-2025-06-18}
BASE_DOMAIN=yourdomain.com
```

### Docker Labels

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.mcp-tmux.rule=Host(`mcp-tmux.${BASE_DOMAIN}`)"
  - "traefik.http.routers.mcp-tmux.middlewares=mcp-auth@docker"
```

## Testing

### Integration Test
```bash
just test-file tests/test_mcp_tmux_integration.py
```

### Comprehensive Test
```bash
just test-file tests/test_mcp_tmux_comprehensive.py
```

### Manual Testing
```bash
# List sessions
mcp-streamablehttp-client query https://mcp-tmux.yourdomain.com/mcp \
  --token YOUR_TOKEN \
  '{"method": "tools/list"}'

# Create session
mcp-streamablehttp-client query https://mcp-tmux.yourdomain.com/mcp \
  --token YOUR_TOKEN \
  '{"method": "tools/call", "params": {"name": "create_session", "arguments": {"session_name": "test"}}}'
```

## Error Handling

### Common Errors

1. **Session Not Found**
   ```json
   {
     "error": {
       "code": -32602,
       "message": "Session 'nonexistent' not found"
     }
   }
   ```

2. **Invalid Pane Index**
   ```json
   {
     "error": {
       "code": -32602,
       "message": "Pane index out of range"
     }
   }
   ```

3. **Tmux Not Available**
   ```json
   {
     "error": {
       "code": -32603,
       "message": "tmux command not found"
     }
   }
   ```

## Best Practices

### Session Naming
- Use descriptive session names
- Avoid special characters
- Keep names unique and meaningful

### Resource Management
- Clean up unused sessions
- Limit concurrent sessions
- Monitor resource usage

### Security
- Never expose tmux directly
- Use OAuth authentication
- Validate all inputs
- Restrict command execution

## Troubleshooting

### Service Not Responding
```bash
# Check container status
docker ps | grep mcp-tmux

# View logs
docker logs mcp-tmux

# Protocol health check via MCP initialization
curl -X POST https://mcp-tmux.yourdomain.com/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"'"${MCP_PROTOCOL_VERSION:-2025-06-18}"'","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'
```

### Authentication Issues
```bash
# Verify token
mcp-streamablehttp-client test-auth \
  --url https://mcp-tmux.yourdomain.com/mcp \
  --token YOUR_TOKEN
```

### Tmux Issues
```bash
# Check tmux installation
docker exec mcp-tmux which tmux

# List tmux sessions in container
docker exec mcp-tmux tmux list-sessions
```

## Performance Considerations

- **Session Limits** - Monitor number of active sessions
- **Command Rate** - Avoid rapid command flooding
- **Output Capture** - Be mindful of large outputs
- **Resource Usage** - Monitor CPU/memory consumption

## Related Documentation

- {doc}`../integration/index` - Integration guides
- {doc}`../architecture/mcp-protocol` - Protocol details
- {doc}`../development/adding-services` - Development guide