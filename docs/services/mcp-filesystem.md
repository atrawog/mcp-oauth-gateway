# mcp-filesystem Service

A filesystem access service that wraps the official `mcp-server-filesystem` using the proxy pattern.

## Overview

The `mcp-filesystem` service provides secure filesystem access capabilities through the MCP protocol. It uses `mcp-streamablehttp-proxy` to wrap the official stdio-based filesystem server, making it accessible via HTTP with OAuth authentication.

## Architecture

```
┌─────────────────────────────────────────┐
│        mcp-filesystem Container         │
├─────────────────────────────────────────┤
│   mcp-streamablehttp-proxy (Port 3000)  │
│              ↓ spawns ↓                 │
│       mcp-server-filesystem             │
│         (stdio subprocess)              │
└─────────────────────────────────────────┘
            ↓ accesses ↓
┌─────────────────────────────────────────┐
│        ./workspace Directory            │
│      (mounted as /workspace)            │
└─────────────────────────────────────────┘
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_FILE` | Log file path | `/logs/server.log` |
| `MCP_CORS_ORIGINS` | Allowed CORS origins | From `.env` file |
| `MCP_PROTOCOL_VERSION` | MCP protocol version | `2025-03-26` |

### Volume Mounts

```yaml
volumes:
  - ../workspace:/workspace:rw  # Read/write access to workspace
  - ../logs/mcp-filesystem:/logs  # Service logs
```

## Available Tools

The mcp-filesystem service provides filesystem operations through the wrapped official server:

### read_file

Reads the contents of a file.

**Parameters:**
- `path` (string, required): Path to the file to read

### write_file

Writes content to a file.

**Parameters:**
- `path` (string, required): Path to the file to write
- `content` (string, required): Content to write to the file

### list_directory

Lists the contents of a directory.

**Parameters:**
- `path` (string, required): Path to the directory to list

### create_directory

Creates a new directory.

**Parameters:**
- `path` (string, required): Path of the directory to create

### delete

Deletes a file or directory.

**Parameters:**
- `path` (string, required): Path to delete

### move

Moves or renames a file or directory.

**Parameters:**
- `source` (string, required): Source path
- `destination` (string, required): Destination path

## Security Features

### Path Restrictions

The service is restricted to the `/workspace` directory:
- All paths are relative to `/workspace`
- Cannot access files outside the workspace
- Prevents directory traversal attacks

### Access Control

- OAuth authentication required via Traefik
- Per-user access control based on JWT claims
- File operations logged for audit trail

## Usage Examples

### Read a File

```bash
curl -X POST https://mcp-filesystem.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "read_file",
      "arguments": {
        "path": "config.json"
      }
    },
    "id": 1
  }'
```

### Write a File

```bash
curl -X POST https://mcp-filesystem.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "write_file",
      "arguments": {
        "path": "output.txt",
        "content": "Hello, World!"
      }
    },
    "id": 2
  }'
```

### List Directory

```bash
curl -X POST https://mcp-filesystem.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "list_directory",
      "arguments": {
        "path": "/"
      }
    },
    "id": 3
  }'
```

## Health Monitoring

### Health Check

The service uses StreamableHTTP protocol initialization for health checks:

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-03-26\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
    | grep -q '\"protocolVersion\":\"2025-03-26\"'"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

### Logs

```bash
# View logs
just logs mcp-filesystem

# Follow logs
just logs -f mcp-filesystem

# Check file logs
cat logs/mcp-filesystem/server.log
```

## Workspace Management

### Setting Up Workspace

The workspace directory is mounted at `./workspace` relative to the project root:

```bash
# Create workspace if it doesn't exist
mkdir -p workspace

# Set appropriate permissions
chmod 755 workspace

# Create subdirectories
mkdir -p workspace/{documents,images,data}
```

### Backup Strategy

Regular backups of the workspace are recommended:

```bash
# Backup workspace
tar -czf workspace-backup-$(date +%Y%m%d).tar.gz workspace/

# Restore workspace
tar -xzf workspace-backup-20240115.tar.gz
```

## Troubleshooting

### Permission Denied Errors

1. Check workspace permissions:
   ```bash
   ls -la workspace/
   ```

2. Fix permissions if needed:
   ```bash
   chmod -R 755 workspace/
   ```

### Path Not Found Errors

1. Verify the file exists in workspace:
   ```bash
   ls -la workspace/path/to/file
   ```

2. Remember all paths are relative to `/workspace`

### Service Won't Start

1. Check if workspace directory exists:
   ```bash
   ls -la | grep workspace
   ```

2. Check proxy logs:
   ```bash
   just logs mcp-filesystem | grep ERROR
   ```

## Integration

### With Claude Desktop

Configure in Claude Desktop settings:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--server-url", "https://mcp-filesystem.example.com/mcp",
        "--token", "Bearer YOUR_TOKEN_HERE"
      ]
    }
  }
}
```

### With Python Clients

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://mcp-filesystem.example.com/mcp",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "read_file",
                "arguments": {"path": "config.json"}
            },
            "id": 1
        }
    )
```
