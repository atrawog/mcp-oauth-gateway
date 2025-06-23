# Filesystem Service

The MCP Filesystem service provides secure file system access capabilities, allowing Claude to read, write, and manage files through the OAuth-protected gateway.

## Overview

The Filesystem service enables:
- File reading and writing
- Directory listing and navigation
- File metadata access
- Path validation and security
- Configurable access restrictions

## Configuration

### Environment Variables

```bash
# Service-specific settings
MCP_FILESYSTEM_ROOT=/data              # Root directory for access
MCP_FILESYSTEM_ALLOW_HIDDEN=false      # Allow access to hidden files
MCP_FILESYSTEM_MAX_FILE_SIZE=10485760  # Max file size (10MB)
MCP_FILESYSTEM_FOLLOW_SYMLINKS=false   # Follow symbolic links
MCP_FILESYSTEM_ALLOWED_EXTENSIONS=*    # Allowed file extensions
```

### Docker Compose

The service runs as `mcp-filesystem` in the compose stack:

```yaml
mcp-filesystem:
  image: mcp-oauth-gateway/mcp-filesystem:latest
  volumes:
    - ./data:/data:ro  # Mount data directory (read-only by default)
  environment:
    - MCP_PROTOCOL_VERSION=${MCP_PROTOCOL_VERSION}
    - FILESYSTEM_ROOT=${MCP_FILESYSTEM_ROOT}
```

## Usage

### Starting the Service

```bash
# Start filesystem service only
just up mcp-filesystem

# View logs
just logs mcp-filesystem

# Rebuild after changes
just rebuild mcp-filesystem
```

### Available Methods

#### readFile

Read file contents:

```json
{
  "jsonrpc": "2.0",
  "method": "readFile",
  "params": {
    "path": "/documents/readme.txt",
    "encoding": "utf-8"
  },
  "id": "1"
}
```

#### writeFile

Write file contents:

```json
{
  "jsonrpc": "2.0",
  "method": "writeFile",
  "params": {
    "path": "/documents/output.txt",
    "content": "File contents here",
    "encoding": "utf-8"
  },
  "id": "2"
}
```

#### listDirectory

List directory contents:

```json
{
  "jsonrpc": "2.0",
  "method": "listDirectory",
  "params": {
    "path": "/documents",
    "recursive": false,
    "includeHidden": false
  },
  "id": "3"
}
```

#### getFileInfo

Get file metadata:

```json
{
  "jsonrpc": "2.0",
  "method": "getFileInfo",
  "params": {
    "path": "/documents/readme.txt"
  },
  "id": "4"
}
```

## Security Features

### Path Validation

- All paths resolved relative to configured root
- Path traversal attempts blocked
- Symlink following configurable
- Hidden file access controlled

### Access Control

- Read/write permissions configurable
- File extension filtering
- Size limits enforced
- Directory restrictions

### Audit Logging

All file operations logged with:
- User identity
- Operation type
- File path
- Timestamp
- Success/failure status

## Examples

### Reading a Text File

```python
import mcp_streamablehttp_client as mcp

client = mcp.Client(
    "https://mcp-filesystem.gateway.yourdomain.com",
    token=access_token
)

result = await client.request("readFile", {
    "path": "/documents/report.txt",
    "encoding": "utf-8"
})

print(result["content"])
```

### Writing a File

```python
result = await client.request("writeFile", {
    "path": "/output/results.json",
    "content": json.dumps(data),
    "encoding": "utf-8"
})
```

### Listing Directory

```python
result = await client.request("listDirectory", {
    "path": "/",
    "recursive": True,
    "includeHidden": False
})

for entry in result["entries"]:
    print(f"{entry['type']}: {entry['path']}")
```

## Limitations

1. **Size Limits** - Default 10MB per file
2. **Path Restrictions** - Confined to root directory
3. **Binary Files** - Limited support
4. **Permissions** - Host system permissions apply
5. **Concurrency** - File locking not implemented

## Troubleshooting

### Common Issues

#### Permission Denied

```json
{
  "error": {
    "code": -32005,
    "message": "Permission denied",
    "data": {
      "path": "/protected/file.txt"
    }
  }
}
```

**Solution**: Check file permissions and service configuration

#### Path Not Found

```json
{
  "error": {
    "code": -32004,
    "message": "Path not found",
    "data": {
      "path": "/nonexistent/file.txt"
    }
  }
}
```

**Solution**: Verify path exists and is within allowed root

#### File Too Large

```json
{
  "error": {
    "code": -32010,
    "message": "File size exceeds limit",
    "data": {
      "size": 15728640,
      "limit": 10485760
    }
  }
}
```

**Solution**: Increase `MCP_FILESYSTEM_MAX_FILE_SIZE` or split file

## Best Practices

1. **Use Relative Paths** - Always relative to configured root
2. **Handle Errors** - File operations can fail
3. **Check Permissions** - Verify access before operations
4. **Validate Input** - Sanitize file paths and content
5. **Monitor Usage** - Track file access patterns

## Security Considerations

- Never expose system files
- Validate all file paths
- Log all access attempts
- Use read-only mounts when possible
- Implement rate limiting
- Regular security audits

## Related Services

- [Fetch Service](fetch.md) - For web content retrieval
- [Memory Service](memory.md) - For temporary storage