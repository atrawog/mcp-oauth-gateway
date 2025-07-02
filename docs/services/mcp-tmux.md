# mcp-tmux Service

A terminal multiplexer control service that wraps `mcp-server-tmux` using the proxy pattern.

## Overview

The `mcp-tmux` service provides terminal multiplexer control capabilities through the MCP protocol. It uses `mcp-streamablehttp-proxy` to wrap the stdio-based tmux server, making it accessible via HTTP with OAuth authentication. This service enables remote terminal session management, window control, and command execution.

## Architecture

```
┌─────────────────────────────────────────┐
│         mcp-tmux Container              │
├─────────────────────────────────────────┤
│   mcp-streamablehttp-proxy (Port 3000)  │
│              ↓ spawns ↓                 │
│         mcp-server-tmux                 │
│         (stdio subprocess)              │
│              ↓ controls ↓               │
│         tmux sessions                   │
│      (terminal multiplexer)             │
└─────────────────────────────────────────┘
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_FILE` | Log file path | `/logs/server.log` |
| `MCP_CORS_ORIGINS` | Allowed CORS origins | `*` |
| `MCP_PROTOCOL_VERSION` | MCP protocol version | `2025-06-18` (configurable) |

## Available Tools

The mcp-tmux service provides terminal session management through the wrapped server:

### create_session

Create a new tmux session.

**Parameters:**
- `name` (string, required): Session name
- `window_name` (string, optional): Initial window name
- `start_directory` (string, optional): Starting directory

### list_sessions

List all active tmux sessions.

**Parameters:** None

**Returns:**
- Array of session objects with names, windows, and creation times

### attach_session

Attach to an existing tmux session.

**Parameters:**
- `name` (string, required): Session name to attach to

### send_keys

Send keystrokes to a tmux pane.

**Parameters:**
- `session` (string, required): Target session name
- `window` (string, optional): Target window name/index
- `pane` (string, optional): Target pane index
- `keys` (string, required): Keys to send

### run_command

Execute a command in a tmux pane.

**Parameters:**
- `session` (string, required): Target session name
- `window` (string, optional): Target window name/index
- `pane` (string, optional): Target pane index
- `command` (string, required): Command to execute

### capture_pane

Capture the contents of a tmux pane.

**Parameters:**
- `session` (string, required): Target session name
- `window` (string, optional): Target window name/index
- `pane` (string, optional): Target pane index
- `history` (boolean, optional): Include scrollback history

### kill_session

Terminate a tmux session.

**Parameters:**
- `name` (string, required): Session name to kill

## Usage Examples

### Session Management

```bash
# Create a new session
curl -X POST https://mcp-tmux.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "create_session",
      "arguments": {
        "name": "dev-session",
        "window_name": "editor",
        "start_directory": "/workspace"
      }
    },
    "id": 1
  }'

# List all sessions
curl -X POST https://mcp-tmux.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "list_sessions",
      "arguments": {}
    },
    "id": 2
  }'
```

### Command Execution

```bash
# Run a command
curl -X POST https://mcp-tmux.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "run_command",
      "arguments": {
        "session": "dev-session",
        "window": "editor",
        "command": "npm test"
      }
    },
    "id": 3
  }'

# Send keys (like Ctrl+C)
curl -X POST https://mcp-tmux.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "send_keys",
      "arguments": {
        "session": "dev-session",
        "window": "editor",
        "keys": "C-c"
      }
    },
    "id": 4
  }'
```

### Output Capture

```bash
# Capture pane contents
curl -X POST https://mcp-tmux.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "capture_pane",
      "arguments": {
        "session": "dev-session",
        "window": "editor",
        "history": true
      }
    },
    "id": 5
  }'
```

## Window and Pane Management

### Window Operations

```python
import httpx

class TmuxWindowManager:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def create_dev_environment(self, session_name):
        """Create a development environment with multiple windows"""
        async with httpx.AsyncClient() as client:
            # Create session with editor window
            await client.post(
                f"{self.base_url}/mcp",
                headers=self.headers,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "create_session",
                        "arguments": {
                            "name": session_name,
                            "window_name": "editor"
                        }
                    },
                    "id": 1
                }
            )

            # Add terminal window
            await client.post(
                f"{self.base_url}/mcp",
                headers=self.headers,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "run_command",
                        "arguments": {
                            "session": session_name,
                            "command": "tmux new-window -n terminal"
                        }
                    },
                    "id": 2
                }
            )

            # Add logs window
            await client.post(
                f"{self.base_url}/mcp",
                headers=self.headers,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "run_command",
                        "arguments": {
                            "session": session_name,
                            "command": "tmux new-window -n logs"
                        }
                    },
                    "id": 3
                }
            )
```

### Pane Layouts

```bash
# Split window horizontally
curl -X POST https://mcp-tmux.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "run_command",
      "arguments": {
        "session": "dev-session",
        "window": "editor",
        "command": "tmux split-window -h"
      }
    },
    "id": 1
  }'

# Set layout
curl -X POST https://mcp-tmux.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "run_command",
      "arguments": {
        "session": "dev-session",
        "window": "editor",
        "command": "tmux select-layout even-horizontal"
      }
    },
    "id": 2
  }'
```

## Advanced Usage

### Automated Testing

```python
class TmuxTestRunner:
    def __init__(self, tmux_client):
        self.tmux = tmux_client

    async def run_test_suite(self, session_name, test_commands):
        """Run tests in separate tmux panes and collect results"""
        results = []

        # Create test session
        await self.tmux.create_session(
            name=session_name,
            window_name="tests"
        )

        for i, test_cmd in enumerate(test_commands):
            # Create new pane for each test
            if i > 0:
                await self.tmux.run_command(
                    session=session_name,
                    window="tests",
                    command="tmux split-window -v"
                )

            # Run test
            await self.tmux.run_command(
                session=session_name,
                window="tests",
                pane=str(i),
                command=test_cmd
            )

            # Wait for completion
            await asyncio.sleep(5)

            # Capture output
            output = await self.tmux.capture_pane(
                session=session_name,
                window="tests",
                pane=str(i),
                history=True
            )

            results.append({
                "command": test_cmd,
                "output": output
            })

        # Clean up
        await self.tmux.kill_session(name=session_name)

        return results
```

### Session Monitoring

```bash
#!/bin/bash
# Monitor tmux session activity

SESSION="monitoring"

# Create monitoring session
curl -X POST https://mcp-tmux.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"method\": \"tools/call\",
    \"params\": {
      \"name\": \"create_session\",
      \"arguments\": {
        \"name\": \"$SESSION\"
      }
    },
    \"id\": 1
  }"

# Monitor system resources
curl -X POST https://mcp-tmux.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"method\": \"tools/call\",
    \"params\": {
      \"name\": \"run_command\",
      \"arguments\": {
        \"session\": \"$SESSION\",
        \"command\": \"htop\"
      }
    },
    \"id\": 2
  }"
```

## Health Monitoring

### Health Check

The service uses StreamableHTTP protocol initialization for health checks:

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"${MCP_PROTOCOL_VERSION:-2025-06-18}\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
    | grep -q '\"protocolVersion\":\"'"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

### Session Monitoring

```bash
# Check active sessions
docker exec mcp-tmux tmux list-sessions

# Monitor tmux server
docker exec mcp-tmux tmux info

# View logs
just logs mcp-tmux
```

## Security Considerations

### Command Execution

1. **Input Validation**: Sanitize commands to prevent injection
2. **Path Restrictions**: Limit accessible directories
3. **Command Allowlist**: Consider restricting allowed commands

### Session Isolation

1. **User Sessions**: Separate sessions per user
2. **Access Control**: Validate session ownership
3. **Timeout Policy**: Auto-kill idle sessions

### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

## Troubleshooting

### Session Not Found

1. List existing sessions:
   ```bash
   docker exec mcp-tmux tmux list-sessions
   ```

2. Check session name:
   ```bash
   # Session names are case-sensitive
   # No spaces allowed in names
   ```

### Command Execution Failures

1. Check tmux server:
   ```bash
   docker exec mcp-tmux tmux info | grep pid
   ```

2. Verify pane exists:
   ```bash
   docker exec mcp-tmux tmux list-panes -t session:window
   ```

### Permission Issues

1. Check user permissions:
   ```bash
   docker exec mcp-tmux whoami
   ```

2. Verify tmux socket:
   ```bash
   docker exec mcp-tmux ls -la /tmp/tmux-*
   ```

## Best Practices

### Session Naming

1. Use descriptive names: `project-dev`, `monitoring-prod`
2. Include timestamps: `backup-20240115-1430`
3. Avoid special characters

### Resource Management

1. **Limit Sessions**: Set maximum sessions per user
2. **Auto Cleanup**: Kill orphaned sessions
3. **Monitor Usage**: Track session creation/destruction

### Error Handling

```python
async def safe_command_execution(tmux_client, session, command):
    try:
        # Check session exists
        sessions = await tmux_client.list_sessions()
        if not any(s['name'] == session for s in sessions):
            await tmux_client.create_session(name=session)

        # Execute command
        result = await tmux_client.run_command(
            session=session,
            command=command
        )

        # Capture output
        output = await tmux_client.capture_pane(
            session=session,
            history=True
        )

        return {"success": True, "output": output}

    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Integration

### With Claude Desktop

Configure in Claude Desktop settings:

```json
{
  "mcpServers": {
    "tmux": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--server-url", "https://mcp-tmux.example.com/mcp",
        "--token", "Bearer YOUR_TOKEN_HERE"
      ]
    }
  }
}
```

### With CI/CD Systems

```python
class TmuxCIRunner:
    def __init__(self, mcp_url, token):
        self.client = TmuxClient(mcp_url, token)

    async def run_ci_pipeline(self, pipeline_config):
        session_name = f"ci-{pipeline_config['id']}"

        # Create CI session
        await self.client.create_session(
            name=session_name,
            window_name="build"
        )

        stages = ["build", "test", "deploy"]

        for stage in stages:
            # Create window for stage
            if stage != "build":
                await self.client.run_command(
                    session=session_name,
                    command=f"tmux new-window -n {stage}"
                )

            # Run stage commands
            for cmd in pipeline_config[stage]["commands"]:
                await self.client.run_command(
                    session=session_name,
                    window=stage,
                    command=cmd
                )

                # Check for failures
                output = await self.client.capture_pane(
                    session=session_name,
                    window=stage
                )

                if "error" in output.lower() or "failed" in output.lower():
                    raise Exception(f"Stage {stage} failed")

        # Cleanup
        await self.client.kill_session(name=session_name)
```
