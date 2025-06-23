# MCP Memory Service

This service provides the official MCP Memory server from the modelcontextprotocol/servers repository, wrapped for OAuth authentication and HTTP transport.

## Overview

The MCP Memory server is a knowledge graph-based persistent memory system that allows AI agents to build a durable model of the world they interact with. It tracks user identity, behaviors, preferences, goals, and relationships.

## Features

- 🧠 **Persistent Memory**: Knowledge graph storage in JSON format
- 👤 **User Identity Tracking**: Maintains user profiles and behaviors
- 🎯 **Goal Management**: Tracks user objectives and preferences
- 🔗 **Relationship Mapping**: Models connections between entities
- 📊 **Behavioral Analysis**: Records and analyzes user patterns
- 🔄 **Context Preservation**: Maintains conversation continuity across sessions

## Architecture

This service follows the project's standard MCP service pattern:
- **Base**: Official `@modelcontextprotocol/server-memory` npm package
- **Transport**: Direct streamableHttp mode (no proxy needed)
- **Authentication**: OAuth 2.1 via Traefik ForwardAuth
- **Storage**: Persistent volume for memory.json file
- **Health Monitoring**: MCP protocol health checks via initialization

## Configuration

### Environment Variables

- `MCP_PROTOCOL_VERSION=2024-11-05` - MCP protocol version (hardcoded - the memory server only supports this version)
- `MCP_CORS_ORIGINS=*` - CORS configuration
- `MEMORY_FILE_PATH=/data/memory.json` - Memory storage location
- `PORT=3000` - Service port

### Storage

The service uses a Docker volume `mcp-memory-data` to persist memory data:
- Mount point: `/data`
- Memory file: `/data/memory.json`
- Automatically created on first run

## Endpoints

- **Primary**: `https://mcp-memory.${BASE_DOMAIN}/mcp`
- **Health Check**: Uses MCP protocol initialization
- **OAuth Discovery**: `https://mcp-memory.${BASE_DOMAIN}/.well-known/oauth-authorization-server`

## Usage

### Authentication

The service requires OAuth authentication via the gateway:
1. Register OAuth client via `/register` endpoint
2. Obtain access token through OAuth flow
3. Include `Authorization: Bearer <token>` header in requests

### MCP Operations

The memory server provides these MCP tools:
- `create_memory` - Store new memories
- `search_memories` - Query existing memories
- `update_memory` - Modify existing memories
- `delete_memory` - Remove memories

And these resources:
- `memory://entities` - List all tracked entities
- `memory://relations` - List all relationships
- `memory://observations` - List all observations

### Example Usage

```bash
# Using mcp-streamablehttp-client
mcp-streamablehttp-client --server-url https://memory.yourdomain.com/mcp --command "create_memory content='User prefers morning meetings'"

# Raw protocol
mcp-streamablehttp-client --raw '{"method": "tools/call", "params": {"name": "search_memories", "arguments": {"query": "meetings"}}}'
```

## Testing

The service is tested via the comprehensive MCP test suite:
- Protocol compliance tests
- Tool execution tests
- Resource access tests
- Authentication flow tests

Use the standard project testing commands:
```bash
just test  # Run all tests including mcp-memory
```

## Memory Structure

The memory system organizes information into:

### Entities
- **Users**: People interacting with the system
- **Concepts**: Abstract ideas and topics
- **Objects**: Physical or digital items
- **Locations**: Places and venues

### Relations
- **Preferences**: User likes/dislikes
- **Associations**: Conceptual connections
- **Interactions**: Historical behaviors
- **Goals**: Objectives and intentions

### Observations
- **Behavioral Patterns**: Recurring actions
- **Context Clues**: Environmental factors
- **Temporal Patterns**: Time-based behaviors
- **Emotional States**: Mood and sentiment

## Privacy and Security

- **Data Isolation**: Each authenticated user has separate memory space
- **Access Control**: OAuth authentication required for all operations
- **Data Persistence**: Memories stored locally in container volume
- **No External Sharing**: Memory data never leaves the service

## Troubleshooting

### Common Issues

1. **Memory not persisting**: Check volume mount and permissions
2. **Authentication failures**: Verify OAuth token validity
3. **Service not starting**: Check container logs for npm package issues

### Debugging

```bash
# Check service status
just logs mcp-memory

# Test authentication
mcp-streamablehttp-client --server-url https://memory.yourdomain.com/mcp --test-auth

# Health check
curl -X POST https://memory.yourdomain.com/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"'"$MCP_PROTOCOL_VERSION"'","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'
```

## Integration

The service integrates with:
- **Auth Service**: OAuth token validation
- **Traefik**: Reverse proxy and routing
- **Redis**: Session management (via auth service)
- **Let's Encrypt**: Automatic HTTPS certificates

## Memory Persistence

Memory data is stored in JSON format with this structure:
```json
{
  "entities": [...],
  "relations": [...],
  "observations": [...]
}
```

The file is automatically created and maintained by the memory server, with atomic writes ensuring data consistency.