# MCP Tmux Service

**Sacred MCP service providing tmux session interaction capabilities through OAuth 2.1 protected endpoints.**

## Service Overview

The MCP Tmux service enables secure interaction with tmux terminal sessions through the Model Context Protocol. Built on the `tmux-mcp` Node.js package, it provides comprehensive tmux management capabilities including session listing, pane content capture, command execution, and window management.

## Tmux Capabilities

### Core Tools Available

#### Session Management
- **`list-sessions`**: List all available tmux sessions
- **`find-session`**: Search for specific tmux sessions by name or pattern
- **`new-session`**: Create new tmux sessions with specified names
- **`kill-session`**: Terminate tmux sessions

#### Window Operations  
- **`list-windows`**: List all windows within a session
- **`new-window`**: Create new windows in existing sessions
- **`select-window`**: Switch to specific windows
- **`rename-window`**: Rename existing windows

#### Pane Interaction
- **`capture-pane`**: Capture terminal content from specific panes
- **`list-panes`**: List all panes within a window
- **`split-window`**: Create new panes by splitting existing ones
- **`select-pane`**: Switch focus to specific panes

#### Command Execution
- **`execute-command`**: Execute shell commands in tmux panes
- **`send-keys`**: Send keystrokes to tmux panes
- **`run-shell`**: Run shell commands and capture output

### Resources Provided

#### Session Resources
- **`tmux://sessions`**: Complete list of all tmux sessions
- **`tmux://session/{sessionId}`**: Detailed information about specific sessions
- **`tmux://session/{sessionId}/windows`**: Windows within a session

#### Pane Resources
- **`tmux://pane/{paneId}`**: Real-time pane content and status
- **`tmux://pane/{paneId}/history`**: Complete terminal history for a pane
- **`tmux://window/{windowId}/panes`**: All panes within a window

#### Command Resources
- **`tmux://command/{commandId}/result`**: Execution results and output
- **`tmux://command/{commandId}/status`**: Command execution status

## Service Architecture

### Node.js Implementation
- **Runtime**: Node.js 22 Alpine container
- **MCP Server**: `tmux-mcp` npm package via npx
- **HTTP Bridge**: `mcp-streamablehttp-proxy` for HTTP transport
- **Dependencies**: tmux, bash, curl for health checks

### Container Features
- **Tmux Installation**: Pre-installed tmux with default session management
- **Health Monitoring**: HTTP health checks on `/health` endpoint
- **Process Management**: Automatic tmux session creation and management
- **Shell Support**: Configurable shell types (bash, fish, zsh)

## OAuth Integration

### Authentication Flow
1. **Service Discovery**: `/.well-known/oauth-authorization-server` routed to auth service
2. **Client Registration**: Dynamic registration via RFC 7591
3. **User Authentication**: GitHub OAuth integration
4. **Token Validation**: ForwardAuth middleware validates Bearer tokens
5. **MCP Access**: Authenticated requests forwarded to tmux service

### Endpoint Configuration
- **Primary**: `https://mcp-tmux.${BASE_DOMAIN}/mcp`
- **Health**: `https://mcp-tmux.${BASE_DOMAIN}/health`
- **Discovery**: `https://mcp-tmux.${BASE_DOMAIN}/.well-known/oauth-authorization-server`

## Usage Examples

### Session Management
```javascript
// List all tmux sessions
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "list-sessions",
    "arguments": {}
  }
}

// Create new session
{
  "jsonrpc": "2.0", 
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "new-session",
    "arguments": {
      "sessionName": "development",
      "detached": true
    }
  }
}
```

### Pane Content Capture
```javascript
// Capture pane content
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call", 
  "params": {
    "name": "capture-pane",
    "arguments": {
      "paneId": "%1",
      "startLine": 0,
      "endLine": -1
    }
  }
}
```

### Command Execution
```javascript
// Execute command in pane
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "execute-command",
    "arguments": {
      "paneId": "%1", 
      "command": "ls -la",
      "waitForCompletion": true
    }
  }
}
```

### Resource Access
```javascript
// Get session list resource
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "resources/read",
  "params": {
    "uri": "tmux://sessions"
  }
}

// Get specific pane content
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "resources/read", 
  "params": {
    "uri": "tmux://pane/%1"
  }
}
```

## Configuration Options

### Shell Type Configuration
The service supports different shell types:
```bash
# Default bash
CMD ["/app/start.sh"]

# Fish shell
CMD ["/app/start.sh", "--shell-type=fish"]

# Zsh shell  
CMD ["/app/start.sh", "--shell-type=zsh"]
```

### Environment Variables
- **`PORT`**: HTTP server port (default: 3000)
- **`MCP_PROTOCOL_VERSION`**: MCP protocol version (2025-06-18)
- **`TMUX_SESSION_PREFIX`**: Prefix for auto-created sessions

## Security Considerations

### Access Control
- **OAuth Protected**: All MCP endpoints require valid Bearer tokens
- **Session Isolation**: Each authenticated user gets isolated tmux access
- **Command Validation**: Input validation on all tmux commands
- **Resource Limiting**: Prevents resource exhaustion attacks

### Container Security
- **Minimal Base**: Alpine Linux with minimal packages
- **Non-Root User**: Runs with limited privileges where possible
- **Network Isolation**: Isolated container networking
- **Health Monitoring**: Automatic health checks and restart policies

## Health Monitoring

### Health Check Endpoint
```bash
curl https://mcp-tmux.${BASE_DOMAIN}/health
```

**Response**:
```json
{
  "status": "healthy",
  "tmux": "available",
  "sessions": 3,
  "mcp_version": "2025-06-18"
}
```

### Container Health
- **Interval**: 30-second health checks
- **Timeout**: 10-second response timeout
- **Retries**: 3 failed attempts before unhealthy
- **Start Period**: 40-second grace period for startup

## Development and Testing

### Local Testing
```bash
# Build and start service
just rebuild mcp-tmux

# Check health
curl https://mcp-tmux.${BASE_DOMAIN}/health

# Test with MCP client
just mcp-client-token
# Use token to test endpoints
```

### Integration with Claude Code
```json
{
  "mcpServers": {
    "tmux": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--url", "https://mcp-tmux.${BASE_DOMAIN}/mcp",
        "--oauth2"
      ],
      "env": {
        "MCP_PROTOCOL_VERSION": "2025-06-18"
      }
    }
  }
}
```

## Common Use Cases

### Development Workflow
- **Session Management**: Create and manage development sessions
- **Multi-Pane Setup**: Split terminals for different tasks
- **Command Execution**: Run build commands and scripts
- **Log Monitoring**: Capture and analyze application logs

### System Administration
- **Server Monitoring**: Watch system processes and logs
- **Remote Management**: Execute administrative commands
- **Session Persistence**: Maintain long-running processes
- **Multi-User Coordination**: Share terminal sessions securely

### AI Assistant Integration
- **Terminal Awareness**: AI can see current terminal state
- **Command Assistance**: AI can suggest and execute commands
- **Process Monitoring**: AI can track running processes
- **Error Diagnosis**: AI can analyze terminal output for issues

## Troubleshooting

### Common Issues

#### Tmux Not Available
```bash
# Check tmux installation in container
docker exec mcp-oauth-gateway-mcp-tmux-1 tmux -V

# Restart service
just rebuild mcp-tmux
```

#### Session Creation Failures
```bash
# Check tmux server status
docker exec mcp-oauth-gateway-mcp-tmux-1 tmux list-sessions

# Create default session manually
docker exec mcp-oauth-gateway-mcp-tmux-1 tmux new-session -d -s default
```

#### MCP Protocol Issues
```bash
# Test MCP endpoint directly
curl -X POST https://mcp-tmux.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer $GATEWAY_OAUTH_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "MCP-Protocol-Version: 2025-06-18" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Service Logs
```bash
# View tmux service logs
docker logs mcp-oauth-gateway-mcp-tmux-1

# Follow logs in real-time
docker logs mcp-oauth-gateway-mcp-tmux-1 -f
```

## Sacred Compliance

### Holy Trinity Adherence
- **Traefik**: Routes OAuth and MCP requests with divine priority
- **Auth Service**: Validates tokens with blessed ForwardAuth middleware  
- **MCP Service**: Provides pure tmux protocol functionality

### Testing Commandments
- **No Mocking**: Tests run against real tmux sessions
- **Real Systems**: Full Docker container integration testing
- **Coverage**: Comprehensive tool and resource testing

### Security Sanctity
- **OAuth 2.1**: Full RFC compliance with PKCE protection
- **JWT Validation**: RS256 signature verification
- **Zero Trust**: Every request validated and authorized

**⚡ This service follows all Sacred Commandments and provides secure, authenticated access to tmux terminal management capabilities! ⚡**