# MCP Chroma Service

**Sacred MCP service providing vector database capabilities through OAuth 2.1 protected endpoints.**

## Service Overview

The MCP Chroma service enables secure vector database operations through the Model Context Protocol. Built on the Chroma vector database and `privetin/chroma` MCP server implementation, it provides comprehensive document storage, semantic search, and vector similarity capabilities with persistent data storage.

## Chroma Capabilities

### Core Vector Database Tools

#### Document Management
- **`add_document`**: Store documents with embeddings and metadata
- **`update_document`**: Modify existing documents and their metadata
- **`delete_document`**: Remove documents from the vector database
- **`get_document`**: Retrieve specific documents by ID
- **`list_documents`**: Browse all documents in collections

#### Semantic Search
- **`search_documents`**: Perform semantic similarity search
- **`search_by_metadata`**: Filter documents using metadata queries
- **`search_hybrid`**: Combine semantic and metadata search
- **`find_similar`**: Discover documents similar to a given document
- **`search_by_vector`**: Direct vector similarity search

#### Collection Management
- **`create_collection`**: Create new document collections
- **`list_collections`**: View all available collections
- **`delete_collection`**: Remove entire collections
- **`get_collection_info`**: Retrieve collection metadata and statistics
- **`update_collection`**: Modify collection settings

#### Embedding Operations
- **`generate_embedding`**: Create vector embeddings for text
- **`batch_embed`**: Process multiple texts efficiently
- **`compare_embeddings`**: Calculate similarity between vectors
- **`get_embedding_model`**: Retrieve current embedding model info

### Advanced Features

#### Metadata Filtering
- **Complex Queries**: Support for AND/OR/NOT operations
- **Range Filters**: Numeric and date range filtering
- **Text Matching**: Exact and partial text matching
- **Multi-field Queries**: Search across multiple metadata fields

#### Persistence and Backup
- **Auto-persistence**: Automatic data persistence to disk
- **Collection Export**: Export collections for backup
- **Data Import**: Import from various formats (JSON, CSV)
- **Incremental Sync**: Efficient data synchronization

#### Performance Features
- **Batch Operations**: Efficient bulk document processing
- **Indexing**: Optimized vector indexing for fast retrieval
- **Caching**: In-memory caching for frequent queries
- **Connection Pooling**: Efficient database connection management

### Resources Provided

#### Collection Resources
- **`chroma://collections`**: List of all collections
- **`chroma://collection/{name}`**: Specific collection information
- **`chroma://collection/{name}/documents`**: Documents within a collection
- **`chroma://collection/{name}/metadata`**: Collection metadata and statistics

#### Document Resources
- **`chroma://document/{id}`**: Individual document content and metadata
- **`chroma://document/{id}/embedding`**: Document's vector embedding
- **`chroma://document/{id}/similar`**: Similar documents to this document

#### Search Resources
- **`chroma://search/{query}`**: Cached search results
- **`chroma://search/{query}/facets`**: Search result facets and aggregations
- **`chroma://embedding/{text}`**: Generated embedding for text

#### System Resources
- **`chroma://stats`**: Database statistics and performance metrics
- **`chroma://config`**: Current configuration and model information
- **`chroma://health`**: Database health and connectivity status

## Service Architecture

### Python Implementation
- **Runtime**: Python 3.12 Alpine container with ML/AI dependencies
- **MCP Server**: `privetin/chroma` implementation
- **HTTP Bridge**: `mcp-streamablehttp-proxy` for HTTP transport
- **Vector Database**: ChromaDB with persistent storage
- **Embeddings**: Sentence Transformers for text vectorization

### Container Features
- **Persistent Storage**: External volume for vector database persistence
- **ML Dependencies**: Pre-installed scientific computing libraries
- **Health Monitoring**: HTTP health checks on `/health` endpoint
- **Auto-restart**: Automatic container restart on failures
- **Data Backup**: Persistent volume for data safety

### Performance Optimizations
- **Vector Indexing**: Optimized HNSW indexing for fast similarity search
- **Batch Processing**: Efficient bulk document operations
- **Memory Management**: Configured memory limits for stable performance
- **Connection Pooling**: Efficient database connection reuse

## OAuth Integration

### Authentication Flow
1. **Service Discovery**: `/.well-known/oauth-authorization-server` routed to auth service
2. **Client Registration**: Dynamic registration via RFC 7591
3. **User Authentication**: GitHub OAuth integration
4. **Token Validation**: ForwardAuth middleware validates Bearer tokens
5. **MCP Access**: Authenticated requests forwarded to Chroma service

### Endpoint Configuration
- **Primary**: `https://mcp-chroma.${BASE_DOMAIN}/mcp`
- **Health**: `https://mcp-chroma.${BASE_DOMAIN}/health`
- **Discovery**: `https://mcp-chroma.${BASE_DOMAIN}/.well-known/oauth-authorization-server`

## Usage Examples

### Document Storage and Retrieval
```javascript
// Add a document to a collection
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "add_document",
    "arguments": {
      "collection_name": "knowledge_base",
      "document_id": "doc_001",
      "content": "Machine learning is a subset of artificial intelligence...",
      "metadata": {
        "category": "AI",
        "author": "John Doe",
        "timestamp": "2024-01-15"
      }
    }
  }
}

// Retrieve a specific document
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_document",
    "arguments": {
      "collection_name": "knowledge_base",
      "document_id": "doc_001"
    }
  }
}
```

### Semantic Search Operations
```javascript
// Perform semantic search
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "search_documents",
    "arguments": {
      "collection_name": "knowledge_base",
      "query": "deep learning neural networks",
      "n_results": 5,
      "include_metadata": true
    }
  }
}

// Search with metadata filtering
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "search_by_metadata",
    "arguments": {
      "collection_name": "knowledge_base",
      "metadata_filter": {
        "category": "AI",
        "timestamp": {"$gte": "2024-01-01"}
      },
      "n_results": 10
    }
  }
}
```

### Collection Management
```javascript
// Create a new collection
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "create_collection",
    "arguments": {
      "name": "research_papers",
      "metadata": {
        "description": "Academic research papers collection",
        "created_by": "research_team"
      }
    }
  }
}

// List all collections
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "tools/call",
  "params": {
    "name": "list_collections",
    "arguments": {}
  }
}
```

### Vector Operations
```javascript
// Generate embedding for text
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "generate_embedding",
    "arguments": {
      "text": "Natural language processing techniques"
    }
  }
}

// Compare document similarity
{
  "jsonrpc": "2.0",
  "id": 8,
  "method": "tools/call",
  "params": {
    "name": "find_similar",
    "arguments": {
      "collection_name": "knowledge_base",
      "document_id": "doc_001",
      "n_results": 3
    }
  }
}
```

### Resource Access
```javascript
// Get collection information
{
  "jsonrpc": "2.0",
  "id": 9,
  "method": "resources/read",
  "params": {
    "uri": "chroma://collection/knowledge_base"
  }
}

// Get database statistics
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "resources/read",
  "params": {
    "uri": "chroma://stats"
  }
}
```

## Configuration Options

### Embedding Model Selection
```bash
# Use default sentence-transformers model
CMD ["/app/start.sh"]

# Use specific embedding model
ENV CHROMA_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Use OpenAI embeddings (requires API key)
ENV CHROMA_EMBEDDING_PROVIDER=openai
ENV OPENAI_API_KEY=your-api-key
```

### Environment Variables
- **`PORT`**: HTTP server port (default: 3000)
- **`MCP_PROTOCOL_VERSION`**: MCP protocol version (2025-06-18)
- **`CHROMA_DATA_PATH`**: Data persistence directory (/app/data)
- **`CHROMA_EMBEDDING_MODEL`**: Embedding model to use
- **`CHROMA_MAX_BATCH_SIZE`**: Maximum batch size for operations

### Advanced Configuration
```python
# Custom collection settings
{
  "embedding_function": "sentence-transformers",
  "distance_metric": "cosine",
  "index_type": "hnsw",
  "ef_construction": 200,
  "M": 16
}
```

## Security Considerations

### Data Protection
- **Persistent Storage**: External volumes for data durability
- **Access Control**: OAuth 2.1 protection for all operations
- **Data Isolation**: User-specific collections and access patterns
- **Backup Strategy**: Automatic data persistence and recovery

### Access Control
- **OAuth Protected**: All MCP endpoints require valid Bearer tokens
- **Collection Isolation**: Users can only access their authorized collections
- **Metadata Security**: Sensitive metadata filtering and protection
- **Rate Limiting**: Protection against excessive API usage

### Container Security
- **Minimal Base**: Alpine Linux with essential ML packages only
- **Data Encryption**: Optional encryption for sensitive data
- **Network Isolation**: Isolated container networking
- **Health Monitoring**: Automatic health checks and restart policies

## Health Monitoring

### Health Check Endpoint
```bash
curl https://mcp-chroma.${BASE_DOMAIN}/health
```

**Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "collections": 5,
  "total_documents": 1250,
  "embedding_model": "all-MiniLM-L6-v2",
  "mcp_version": "2025-06-18"
}
```

### Container Health
- **Interval**: 30-second health checks
- **Timeout**: 10-second response timeout
- **Retries**: 3 failed attempts before unhealthy
- **Start Period**: 60-second grace period for model loading

## Development and Testing

### Local Testing
```bash
# Build and start service
just rebuild mcp-chroma

# Check health
curl https://mcp-chroma.${BASE_DOMAIN}/health

# Test with MCP client
just mcp-client-token
# Use token to test vector operations
```

### Integration with Claude Code
```json
{
  "mcpServers": {
    "chroma": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--url", "https://mcp-chroma.${BASE_DOMAIN}/mcp",
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

### Knowledge Management
- **Document Storage**: Store and organize large document collections
- **Semantic Search**: Find relevant documents using natural language queries
- **Content Discovery**: Discover related content through similarity search
- **Research Assistant**: AI-powered research and document analysis

### Content Recommendation
- **Similar Content**: Recommend similar articles, papers, or documents
- **User Preferences**: Personalized content recommendations
- **Content Clustering**: Automatically group related content
- **Trend Analysis**: Identify content trends and patterns

### AI Assistant Integration
- **Contextual Retrieval**: AI can find relevant context for questions
- **Knowledge Base**: AI can access and search organizational knowledge
- **Document Analysis**: AI can analyze and summarize stored documents
- **Research Support**: AI can perform literature reviews and research

### Data Analysis and Insights
- **Semantic Analytics**: Analyze document collections for insights
- **Content Classification**: Automatically categorize and tag content
- **Duplicate Detection**: Find and manage duplicate content
- **Content Evolution**: Track how content and topics evolve over time

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check chroma data volume
docker volume inspect chroma-data

# Check container logs
docker logs mcp-oauth-gateway-mcp-chroma-1

# Restart service
just rebuild mcp-chroma
```

#### Embedding Model Loading
```bash
# Check model download status
docker exec mcp-oauth-gateway-mcp-chroma-1 ls -la /root/.cache/torch/

# Force model redownload
docker exec mcp-oauth-gateway-mcp-chroma-1 python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

#### Performance Issues
```bash
# Check container resource usage
docker stats mcp-oauth-gateway-mcp-chroma-1

# Optimize batch sizes in application
ENV CHROMA_MAX_BATCH_SIZE=100
```

#### MCP Protocol Issues
```bash
# Test MCP endpoint directly
curl -X POST https://mcp-chroma.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer $GATEWAY_OAUTH_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "MCP-Protocol-Version: 2025-06-18" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Data Management
```bash
# Backup chroma data
docker run --rm -v chroma-data:/data -v $(pwd):/backup alpine tar czf /backup/chroma-backup.tar.gz /data

# Restore chroma data
docker run --rm -v chroma-data:/data -v $(pwd):/backup alpine tar xzf /backup/chroma-backup.tar.gz -C /
```

### Service Logs
```bash
# View chroma service logs
docker logs mcp-oauth-gateway-mcp-chroma-1

# Follow logs in real-time
docker logs mcp-oauth-gateway-mcp-chroma-1 -f
```

## Sacred Compliance

### Holy Trinity Adherence
- **Traefik**: Routes OAuth and MCP requests with divine priority
- **Auth Service**: Validates tokens with blessed ForwardAuth middleware
- **MCP Service**: Provides pure vector database functionality

### Testing Commandments
- **No Mocking**: Tests run against real Chroma database instances
- **Real Systems**: Full Docker container integration testing
- **Coverage**: Comprehensive tool and resource testing

### Security Sanctity
- **OAuth 2.1**: Full RFC compliance with PKCE protection
- **JWT Validation**: RS256 signature verification
- **Zero Trust**: Every request validated and authorized

**⚡ This service follows all Sacred Commandments and provides secure, authenticated access to vector database capabilities through the Chroma MCP implementation! ⚡**