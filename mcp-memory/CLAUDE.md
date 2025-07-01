# MCP Memory Service - The Divine Knowledge Graph Repository

**🧠 Behold! The sacred knowledge graph server wrapped in OAuth glory! ⚡**

## Sacred Architecture Truth

**🔱 This service follows the holy Proxy Pattern - wrapping the official MCP server! ⚡**

- **Official Server**: `@modelcontextprotocol/server-memory` from npm
- **Divine Wrapper**: `mcp-streamablehttp-proxy` bridges stdio to HTTP
- **Protocol Version**: `2024-11-05` - The blessed version of memory protocol
- **Sacred Port**: 3000 - Where knowledge flows through HTTP
- **Data Sanctuary**: `/data/memory.json` - Persistent knowledge storage

## The Nine Sacred Tools of Knowledge

**⚡ These are the actual implemented tools, tested and verified! ⚡**

### 1. create_entities - The Divine Entity Creation
- **Purpose**: Birth new entities into the knowledge graph
- **Schema**: `entities[]` with `name`, `entityType`, `observations[]`
- **Returns**: Array of created entities with divine IDs
- **Status**: ✅ FULLY WORKING

### 2. create_relations - The Sacred Relationship Forge
- **Purpose**: Bind entities together with typed relationships
- **Schema**: `relations[]` with `from`, `to`, `relationType`
- **Returns**: Array of created relations
- **Status**: ✅ FULLY WORKING

### 3. add_observations - The Wisdom Augmentation
- **Purpose**: Enhance entities with new observations
- **Schema**: `observations[]` with `entityName`, `contents[]`
- **Returns**: Confirmation of added observations
- **Status**: ✅ FULLY WORKING

### 4. read_graph - The Complete Knowledge Revelation
- **Purpose**: Retrieve the entire knowledge graph state
- **Schema**: No parameters needed
- **Returns**: Full graph with `entities[]` and `relations[]`
- **Status**: ✅ FULLY WORKING

### 5. search_nodes - The Divine Query Engine
- **Purpose**: Search entities by query string
- **Schema**: `query` string parameter
- **Returns**: Matching entities and relations
- **Status**: ⚠️ PARTIAL - API works but has implementation quirks

### 6. open_nodes - The Entity Inspector
- **Purpose**: Get detailed information about specific entities
- **Schema**: `names[]` array of entity names
- **Returns**: Detailed entity data with all observations
- **Status**: ✅ FULLY WORKING

### 7. delete_entities - The Entity Destroyer
- **Purpose**: Remove entities from existence
- **Schema**: `entityNames[]` to delete
- **Returns**: Deletion confirmation
- **Status**: ✅ FULLY WORKING

### 8. delete_relations - The Relationship Severer
- **Purpose**: Remove relationships between entities
- **Schema**: `relationIds[]` to delete
- **Returns**: Deletion confirmation
- **Status**: ✅ WORKING (ID format implementation specific)

### 9. delete_observations - The Wisdom Eraser
- **Purpose**: Remove observations from entities
- **Schema**: `observationIds[]` to delete
- **Returns**: Deletion confirmation
- **Status**: ✅ WORKING (ID format implementation specific)

## Sacred Configuration

**⚙️ Environment variables that control the divine knowledge! ⚡**

```bash
# Protocol Configuration
MCP_PROTOCOL_VERSION=2024-11-05      # The blessed memory protocol version
MCP_CORS_ORIGINS=*                   # CORS permissions for divine access
MEMORY_FILE_PATH=/data/memory.json   # Where knowledge persists eternally

# Logging Configuration
LOG_FILE=/logs/server.log            # Where wisdom is recorded
```

## Divine Docker Architecture

**🐳 The container configuration follows the sacred patterns! ⚡**

```yaml
# Health Check - Protocol Verification
healthcheck:
  test: MCP initialize request with protocol handshake
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s

# Volume Mounts - Data Persistence
volumes:
  - mcp-memory-data:/data    # Knowledge graph storage
  - ../logs/mcp-memory:/logs # Sacred logging temple
```

## The Sacred Traefik Routing

**🚦 Four divine routing priorities guide the traffic! ⚡**

1. **Priority 10** - OAuth Discovery (`/.well-known/oauth-authorization-server`)
2. **Priority 6** - CORS Preflight (OPTIONS method)
3. **Priority 2** - MCP Route with Auth (`/mcp` endpoint)
4. **Priority 1** - Catch-all with Auth (all other paths)

**⚡ All routes except discovery require Bearer token authentication! ⚡**

## Testing Commandments

**🧪 All functionality tested with real protocol - no mocks! ⚡**

```bash
# Run comprehensive tests
just test -k mcp_memory

# Verify all 9 tools
just test -k test_mcp_memory_comprehensive

# Check functionality summary
just test -k test_mcp_memory_functionality_summary
```

**Test Coverage**: 11 tests, 100% pass rate, all tools verified!

## Common Usage Patterns

**💡 Divine examples of knowledge graph operations! ⚡**

### Creating a Knowledge Network
```python
# Create entities
entities = [
    {"name": "Project X", "entityType": "project", "observations": ["Started in 2024"]},
    {"name": "Alice", "entityType": "person", "observations": ["Lead developer"]}
]

# Create relationships
relations = [
    {"from": "Alice", "to": "Project X", "relationType": "works_on"}
]
```

### Querying the Graph
```python
# Read entire graph
full_graph = read_graph()

# Search for specific nodes
results = search_nodes(query="Project")

# Get detailed node info
details = open_nodes(names=["Alice", "Project X"])
```

## Divine Warnings

**⚠️ Heed these warnings or face data chaos! ⚡**

- **Session State**: Each connection maintains separate session state
- **Data Persistence**: All data saved to `/data/memory.json` volume
- **ID Formats**: Relation/observation IDs are implementation specific
- **Search Quirks**: Search has known implementation limitations
- **No Direct Auth**: Service knows nothing of OAuth - Traefik handles all

## Sacred Integration Points

**🔌 How this service connects to the divine gateway! ⚡**

- **URL**: `https://memory.${BASE_DOMAIN}/mcp`
- **Auth**: Bearer token via Authorization header
- **Protocol**: Streamable HTTP with MCP 2024-11-05
- **Client**: Use `mcp-streamablehttp-client` for divine communication

**⚡ This is a wrapped official MCP server - behavior matches upstream! ⚡**
