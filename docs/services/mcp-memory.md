# MCP Memory Service

The MCP Memory service provides a sophisticated knowledge graph storage system, enabling AI systems to build, maintain, and query persistent memory through entities, relations, and observations.

```{image} https://img.shields.io/badge/Status-Production%20Ready-green
:alt: Production Ready
```
```{image} https://img.shields.io/badge/Protocol-MCP%202025--06--18-blue
:alt: MCP Protocol Version
```

## Overview

MCP Memory transforms how AI systems handle knowledge persistence. Instead of losing context between conversations, AI systems can build comprehensive knowledge graphs that persist across sessions, enabling true memory and learning capabilities.

## 🧠 Capabilities

### Knowledge Graph Management
- **Entity Storage** - Create and manage knowledge entities
- **Relationship Mapping** - Define connections between entities
- **Observation Tracking** - Record events and interactions
- **Graph Querying** - Search and retrieve knowledge

### Persistence Features
- **Session Persistence** - Knowledge survives container restarts
- **Graph Integrity** - Consistent relationships and references
- **Query Optimization** - Efficient graph traversal
- **Backup Support** - Data export and import capabilities

### AI Memory Functions
- **Context Building** - Accumulate conversational context
- **Learning Tracking** - Record learning and insights
- **Relationship Discovery** - Find connections in data
- **Memory Recall** - Retrieve relevant historical information

## 🛠️ Tools

The MCP Memory service provides 9 comprehensive tools for knowledge management:

### Core Entity Management

#### create_entities
Create new entities in the knowledge graph.

```json
{
  "method": "tools/call",
  "params": {
    "name": "create_entities",
    "arguments": {
      "entities": [
        {
          "name": "John Doe",
          "entityType": "Person",
          "observations": ["Software engineer at TechCorp"]
        }
      ]
    }
  }
}
```

#### delete_entities
Remove entities and their associated relationships.

```json
{
  "method": "tools/call",
  "params": {
    "name": "delete_entities",
    "arguments": {
      "entityNames": ["John Doe"]
    }
  }
}
```

### Relationship Management

#### create_relations
Establish relationships between entities.

```json
{
  "method": "tools/call",
  "params": {
    "name": "create_relations",
    "arguments": {
      "relations": [
        {
          "from": "John Doe",
          "to": "TechCorp",
          "relationType": "works_at"
        }
      ]
    }
  }
}
```

#### delete_relations
Remove specific relationships.

```json
{
  "method": "tools/call",
  "params": {
    "name": "delete_relations",
    "arguments": {
      "relations": [
        {
          "from": "John Doe",
          "to": "TechCorp",
          "relationType": "works_at"
        }
      ]
    }
  }
}
```

### Observation Management

#### add_observations
Add observations to existing entities.

```json
{
  "method": "tools/call",
  "params": {
    "name": "add_observations",
    "arguments": {
      "entityName": "John Doe",
      "observations": [
        "Promoted to Senior Engineer in 2024",
        "Specializes in Python and AI systems"
      ]
    }
  }
}
```

#### delete_observations
Remove specific observations.

```json
{
  "method": "tools/call",
  "params": {
    "name": "delete_observations",
    "arguments": {
      "entityName": "John Doe",
      "observations": ["Old observation to remove"]
    }
  }
}
```

### Query and Retrieval

#### read_graph
Retrieve the complete knowledge graph or specific entities.

```json
{
  "method": "tools/call",
  "params": {
    "name": "read_graph",
    "arguments": {}
  }
}
```

#### search_nodes
Search for entities by name or type.

```json
{
  "method": "tools/call",
  "params": {
    "name": "search_nodes",
    "arguments": {
      "query": "John"
    }
  }
}
```

#### open_nodes
Open and explore specific entities with their relationships.

```json
{
  "method": "tools/call",
  "params": {
    "name": "open_nodes",
    "arguments": {
      "entityNames": ["John Doe"]
    }
  }
}
```

## 📊 Knowledge Graph Structure

### Entity Format
```json
{
  "name": "John Doe",
  "entityType": "Person",
  "observations": [
    "Software engineer at TechCorp",
    "Promoted to Senior Engineer in 2024"
  ]
}
```

### Relationship Format
```json
{
  "from": "John Doe",
  "to": "TechCorp", 
  "relationType": "works_at"
}
```

### Graph Response
```json
{
  "entities": [
    {
      "name": "John Doe",
      "entityType": "Person",
      "observations": ["Software engineer at TechCorp"]
    }
  ],
  "relations": [
    {
      "from": "John Doe",
      "to": "TechCorp",
      "relationType": "works_at"
    }
  ]
}
```

## 🏗️ Architecture

### Storage Architecture

```{mermaid}
graph TB
    subgraph "MCP Memory Container"
        A[Memory Server] --> B[Graph Engine]
        B --> C[JSON Storage]
        C --> D[Persistence Volume]
    end
    
    subgraph "Data Flow"
        E[Entity Creation] --> B
        F[Relationship Mapping] --> B
        G[Observation Tracking] --> B
        H[Graph Queries] --> B
    end
    
    subgraph "Persistence"
        D --> I[mcp-memory-data Volume]
        I --> J[/data/memory.json]
    end
```

### Memory Persistence

The service uses a persistent Docker volume to maintain knowledge across restarts:

```yaml
volumes:
  mcp-memory-data:
    external: true
```

Data is stored in `/data/memory.json` within the container, ensuring knowledge survives:
- Container restarts
- Service updates
- System reboots

## 💡 Usage Patterns

### AI Conversation Memory

Build persistent conversation context:

```python
# Create user entity
await create_entities([{
    "name": "User",
    "entityType": "Person", 
    "observations": ["Interested in AI and Python"]
}])

# Add conversation context
await add_observations("User", [
    "Asked about MCP protocol implementation",
    "Prefers detailed technical explanations"
])

# Create topic relationships
await create_relations([{
    "from": "User",
    "to": "MCP Protocol",
    "relationType": "interested_in"
}])
```

### Project Knowledge Base

Track project information:

```python
# Create project entity
await create_entities([{
    "name": "OAuth Gateway Project",
    "entityType": "Project",
    "observations": ["MCP authentication system"]
}])

# Track team members
await create_relations([{
    "from": "John Doe",
    "to": "OAuth Gateway Project", 
    "relationType": "contributes_to"
}])

# Add progress observations
await add_observations("OAuth Gateway Project", [
    "Completed authentication implementation",
    "Added comprehensive testing suite"
])
```

### Learning and Insights

Capture learning and discoveries:

```python
# Create concept entities
await create_entities([{
    "name": "OAuth 2.1",
    "entityType": "Concept",
    "observations": ["Modern authentication protocol"]
}])

# Link related concepts  
await create_relations([{
    "from": "OAuth 2.1",
    "to": "PKCE",
    "relationType": "includes"
}])

# Record insights
await add_observations("OAuth 2.1", [
    "Requires PKCE for public clients",
    "Deprecates implicit grant flow"
])
```

## ⚙️ Configuration

### Environment Variables

```bash
# Protocol configuration
MCP_PROTOCOL_VERSION=2025-06-18
MCP_CORS_ORIGINS=*
PORT=3000

# Storage configuration  
MEMORY_FILE_PATH=/data/memory.json
AUTO_SAVE_INTERVAL=30  # seconds

# Graph limits
MAX_ENTITIES=10000
MAX_OBSERVATIONS_PER_ENTITY=1000
MAX_RELATIONS=50000
```

### Docker Configuration

```yaml
services:
  mcp-memory:
    build:
      context: ../
      dockerfile: mcp-memory/Dockerfile
    volumes:
      - mcp-memory-data:/data
    environment:
      - MCP_PROTOCOL_VERSION=2025-06-18
      - MEMORY_FILE_PATH=/data/memory.json
    labels:
      - "traefik.http.routers.mcp-memory.rule=Host(`mcp-memory.${BASE_DOMAIN}`)"
      - "traefik.http.routers.mcp-memory.middlewares=mcp-auth"

volumes:
  mcp-memory-data:
    external: true
```

## 🧪 Testing

### Comprehensive Test Suite

The MCP Memory service includes extensive testing coverage:

#### Test Categories

1. **Entity Management** - Create, read, update, delete operations
2. **Relationship Handling** - Complex relationship scenarios
3. **Observation Tracking** - Dynamic content management
4. **Graph Queries** - Search and retrieval functionality
5. **Persistence** - Data survival across restarts
6. **Performance** - Large graph handling
7. **Error Handling** - Invalid operations and edge cases

#### Test Results

✅ **All 11 Tools Tested** - 100% functionality coverage  
✅ **Persistence Verified** - Data survives container restarts  
✅ **Complex Workflows** - Multi-step knowledge building  
✅ **Graph Integrity** - Relationship consistency maintained  
✅ **Search Functionality** - Entity discovery working  
✅ **Error Handling** - Graceful failure management  

### Running Tests

```bash
# All memory tests
just test-file tests/test_mcp_memory_*

# Integration tests
pytest tests/test_mcp_memory_integration.py -v

# Comprehensive functionality tests
pytest tests/test_mcp_memory_comprehensive.py -v

# Performance tests
pytest tests/test_mcp_memory_performance.py -v
```

## 🔍 Monitoring

### Health Checks

```bash
# Service health
curl https://mcp-memory.yourdomain.com/health

# Response format
{
  "status": "healthy",
  "timestamp": "2025-06-21T23:38:12Z",
  "service": "mcp-memory",
  "version": "1.0.0",
  "graph_stats": {
    "entities": 150,
    "relations": 320,
    "observations": 1250
  }
}
```

### Memory Metrics

Track knowledge graph growth:

```json
{
  "entity_count": 150,
  "relation_count": 320,
  "observation_count": 1250,
  "entity_types": ["Person", "Project", "Concept", "Organization"],
  "relation_types": ["works_at", "contributes_to", "includes", "relates_to"],
  "storage_size_bytes": 2048576,
  "last_modified": "2025-06-21T23:38:12Z"
}
```

## 🚨 Error Handling

### Common Errors

1. **Entity Not Found**
   ```json
   {
     "error": "Entity 'Unknown Person' not found",
     "code": "ENTITY_NOT_FOUND"
   }
   ```

2. **Duplicate Entity**
   ```json
   {
     "error": "Entity 'John Doe' already exists", 
     "code": "ENTITY_EXISTS"
   }
   ```

3. **Invalid Relationship**
   ```json
   {
     "error": "Cannot create relation: source entity not found",
     "code": "INVALID_RELATION"
   }
   ```

### Recovery Strategies

1. **Data Corruption**
   ```bash
   # Backup current data
   docker cp mcp-memory:/data/memory.json ./backup-memory.json
   
   # Restore from backup
   docker cp ./backup-memory.json mcp-memory:/data/memory.json
   ```

2. **Performance Issues**
   ```bash
   # Check graph size
   curl https://mcp-memory.yourdomain.com/health
   
   # Consider graph cleanup or partitioning
   ```

## 🎯 Use Cases

### AI Assistant Memory
- **User Preferences** - Remember user preferences and context
- **Conversation History** - Maintain conversation threads
- **Learning Tracking** - Record what the AI has learned
- **Relationship Mapping** - Map user relationships and connections

### Knowledge Management
- **Research Notes** - Organize research findings and sources
- **Project Documentation** - Track project progress and insights
- **Team Knowledge** - Share institutional knowledge
- **Decision History** - Record decisions and rationale

### Business Intelligence
- **Customer Relationships** - Map customer interactions
- **Product Knowledge** - Track product features and feedback
- **Market Intelligence** - Organize competitive intelligence
- **Process Documentation** - Map business processes

## 🔧 Troubleshooting

### Common Issues

1. **Data Not Persisting**
   ```bash
   # Check volume mount
   docker inspect mcp-memory | grep Mounts
   
   # Verify volume exists
   docker volume ls | grep mcp-memory-data
   ```

2. **Graph Performance Issues**
   ```bash
   # Check graph size
   curl https://mcp-memory.yourdomain.com/health
   
   # Monitor memory usage
   docker stats mcp-memory
   ```

3. **Search Not Working**
   ```bash
   # Test search functionality
   mcp-streamablehttp-client \\
     --command "search_nodes query='test'"
   ```

### Debug Commands

```bash
# Service logs
docker logs mcp-memory

# Graph statistics
mcp-streamablehttp-client --command "read_graph"

# Test entity creation
mcp-streamablehttp-client \\
  --command "create_entities entities='[{\"name\":\"Test\",\"entityType\":\"Test\"}]'"
```

## 📈 Performance Optimization

### Graph Size Management

1. **Entity Limits** - Configure maximum entities per type
2. **Observation Pruning** - Remove old observations periodically
3. **Relationship Cleanup** - Remove orphaned relationships
4. **Data Archival** - Archive old data to reduce active graph size

### Query Optimization

1. **Indexed Search** - Use entity name indexing
2. **Type Filtering** - Filter by entity type for faster queries
3. **Relationship Caching** - Cache frequently accessed relationships
4. **Batch Operations** - Use batch creates for better performance

---

**Next Steps:**
- Explore {doc}`mcp-time` for temporal operations
- Check {doc}`../integration/claude-ai` for AI memory integration
- Review {doc}`../development/adding-services` for extending memory capabilities