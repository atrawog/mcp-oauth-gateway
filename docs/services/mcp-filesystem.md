# MCP Filesystem Service

The MCP Filesystem service provides secure file system operations through the Model Context Protocol.

## Overview

MCP Filesystem wraps the official `@modelcontextprotocol/server-filesystem` implementation, enabling controlled file and directory operations via HTTP endpoints secured with OAuth 2.1 authentication. All operations are sandboxed within a workspace directory for security.

## Features

### 📁 File Operations
- **Read Files** - Get file contents
- **Write Files** - Create or update files
- **Delete Files** - Remove files
- **Move/Rename** - Relocate or rename files
- **Copy Files** - Duplicate files

### 📂 Directory Management
- **List Contents** - Browse directories
- **Create Directories** - Make new folders
- **Delete Directories** - Remove folders
- **Directory Tree** - View structure
- **Path Navigation** - Change working directory

### 🔍 Search & Query
- **Find Files** - Search by name or pattern
- **File Stats** - Get metadata
- **Size Calculations** - Directory sizes
- **Recent Files** - Sort by modification

### 🛡️ Security Features
- **Workspace Isolation** - Sandboxed operations
- **Path Validation** - Prevent traversal
- **Permission Checks** - Access control
- **Operation Logging** - Audit trail

## Authentication

All requests require OAuth 2.1 Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     https://mcp-filesystem.yourdomain.com/mcp
```

## Endpoints

### Primary Endpoints
- **`/mcp`** - Main MCP protocol endpoint
- **`/mcp`** - Main MCP protocol endpoint (health checks via protocol initialization)
- **`/.well-known/oauth-authorization-server`** - OAuth discovery

## Usage Examples

### Read File

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {
      "path": "documents/report.txt"
    }
  },
  "id": 1
}
```

### Write File

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "write_file",
    "arguments": {
      "path": "documents/new-file.txt",
      "content": "Hello, World!\nThis is a new file."
    }
  },
  "id": 2
}
```

### List Directory

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "list_directory",
    "arguments": {
      "path": "documents",
      "include_hidden": false,
      "recursive": false
    }
  },
  "id": 3
}
```

## Available Tools

### File Operations
- `read_file` - Read file contents
- `write_file` - Write to file
- `append_file` - Append to file
- `delete_file` - Remove file
- `move_file` - Move/rename file
- `copy_file` - Copy file

### Directory Operations
- `list_directory` - List contents
- `create_directory` - Make directory
- `delete_directory` - Remove directory
- `directory_tree` - Show tree structure
- `get_working_directory` - Current directory
- `change_directory` - Change directory

### File Information
- `file_exists` - Check existence
- `file_stats` - Get metadata
- `file_size` - Get size
- `is_directory` - Check if directory
- `is_file` - Check if file

### Search Operations
- `find_files` - Search by pattern
- `search_content` - Search in files
- `recent_files` - Recent modifications
- `largest_files` - Size sorting

### Utility Operations
- `calculate_checksum` - File hash
- `compress_file` - Create archive
- `extract_archive` - Extract files
- `compare_files` - Diff files

## Configuration

### Environment Variables

```bash
# From .env file
MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION:-2025-06-18}
BASE_DOMAIN=yourdomain.com

# Filesystem specific
FILESYSTEM_WORKSPACE=/workspace
FILESYSTEM_MAX_FILE_SIZE=10485760  # 10MB
FILESYSTEM_ALLOWED_EXTENSIONS=*
```

### Docker Labels

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.mcp-filesystem.rule=Host(`mcp-filesystem.${BASE_DOMAIN}`)"
  - "traefik.http.routers.mcp-filesystem.middlewares=mcp-auth@docker"
```

### Volume Mapping

```yaml
volumes:
  - ./mcp-filesystem/workspace:/workspace
```

## Testing

### Integration Test
```bash
just test-file tests/test_mcp_filesystem_integration.py
```

### Manual Testing
```bash
# List workspace root
mcp-streamablehttp-client query https://mcp-filesystem.yourdomain.com/mcp \
  --token YOUR_TOKEN \
  '{"method": "tools/call", "params": {"name": "list_directory", "arguments": {"path": "/"}}}'

# Create a file
mcp-streamablehttp-client query https://mcp-filesystem.yourdomain.com/mcp \
  --token YOUR_TOKEN \
  '{"method": "tools/call", "params": {"name": "write_file", "arguments": {"path": "test.txt", "content": "Hello MCP!"}}}'
```

## Error Handling

### Common Errors

1. **File Not Found**
   ```json
   {
     "error": {
       "code": -32602,
       "message": "File not found: documents/missing.txt"
     }
   }
   ```

2. **Permission Denied**
   ```json
   {
     "error": {
       "code": -32603,
       "message": "Permission denied: cannot write to system directories"
     }
   }
   ```

3. **Path Traversal Attempt**
   ```json
   {
     "error": {
       "code": -32602,
       "message": "Invalid path: path traversal detected"
     }
   }
   ```

4. **File Too Large**
   ```json
   {
     "error": {
       "code": -32603,
       "message": "File exceeds maximum size limit (10MB)"
     }
   }
   ```

## Best Practices

### Security
- Always validate paths
- Use relative paths within workspace
- Never expose system paths
- Implement access controls

### Performance
- Stream large files
- Use pagination for listings
- Cache frequently accessed files
- Limit recursive operations

### Organization
- Use clear directory structure
- Follow naming conventions
- Regular cleanup of temp files
- Document file purposes

### Error Handling
- Check file existence first
- Handle encoding issues
- Validate file sizes
- Implement proper cleanup

## Advanced Usage

### Batch Operations
```json
{
  "method": "tools/call",
  "params": {
    "name": "batch_operation",
    "arguments": {
      "operations": [
        {"action": "create_directory", "path": "backup"},
        {"action": "copy_file", "source": "data.json", "destination": "backup/data.json"},
        {"action": "delete_file", "path": "temp.txt"}
      ]
    }
  }
}
```

### File Search
```json
{
  "method": "tools/call",
  "params": {
    "name": "find_files",
    "arguments": {
      "pattern": "*.log",
      "modified_after": "2024-01-01",
      "size_greater_than": 1024,
      "recursive": true
    }
  }
}
```

### Content Search
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_content",
    "arguments": {
      "pattern": "TODO",
      "file_pattern": "*.py",
      "case_sensitive": false
    }
  }
}
```

## Workspace Structure

The service operates within a sandboxed workspace:

```
/workspace/
├── documents/       # User documents
├── data/           # Data files
├── temp/           # Temporary files
├── uploads/        # Uploaded content
└── exports/        # Generated files
```

## Troubleshooting

### Service Issues
```bash
# Check container status
docker ps | grep mcp-filesystem

# View logs
docker logs mcp-filesystem

# Protocol health check via MCP initialization
curl -X POST https://mcp-filesystem.yourdomain.com/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"'"${MCP_PROTOCOL_VERSION:-2025-06-18}"'","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'
```

### Workspace Problems
```bash
# Check workspace permissions
docker exec mcp-filesystem ls -la /workspace

# Verify workspace size
docker exec mcp-filesystem df -h /workspace

# List workspace contents
docker exec mcp-filesystem find /workspace -type f | head -20
```

### File Access Issues
```bash
# Test file creation
docker exec mcp-filesystem touch /workspace/test.txt

# Check file permissions
docker exec mcp-filesystem ls -la /workspace/test.txt

# Verify file operations
curl -X POST https://mcp-filesystem.yourdomain.com/mcp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"method": "tools/call", "params": {"name": "file_exists", "arguments": {"path": "test.txt"}}}'
```

## Performance Considerations

- **File Size Limits** - 10MB default per file
- **Directory Limits** - 10,000 files per directory
- **Operation Timeout** - 30 seconds per operation
- **Memory Usage** - Files loaded into memory
- **Concurrent Operations** - Thread-safe operations

## Security Considerations

- **Path Sanitization** - All paths validated
- **Workspace Isolation** - No access outside workspace
- **File Type Restrictions** - Optional extension filtering
- **Size Limits** - Prevent resource exhaustion
- **Operation Logging** - Audit trail maintained

## Related Documentation

- {doc}`../integration/index` - Integration guides
- {doc}`../architecture/mcp-protocol` - Protocol details
- {doc}`../development/adding-services` - Development guide