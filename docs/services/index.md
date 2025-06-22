# MCP Services

The MCP OAuth Gateway hosts multiple Model Context Protocol services, each providing specialized functionality while sharing a common authentication and routing infrastructure.

## Service Architecture

All MCP services follow the same architectural pattern:

```{mermaid}
graph LR
    subgraph "Service Container"
        A[Official MCP Server] --> B[mcp-streamablehttp-proxy]
        B --> C[HTTP Endpoint]
    end
    
    subgraph "Infrastructure"
        D[Traefik Router] --> E[OAuth Middleware]
        E --> C
        F[Health Checks] --> C
    end
    
    subgraph "Clients"
        G[Claude.ai] --> D
        H[MCP Clients] --> D
        I[Testing Tools] --> D
    end
```

## Common Features

All services share these capabilities:

### 🔐 Security
- **OAuth 2.1 Authentication** - Bearer token required
- **RFC 7591 Registration** - Dynamic client onboarding
- **HTTPS/TLS** - All communications encrypted
- **CORS Support** - Configurable origin policies

### 🏗️ Infrastructure
- **Docker Containers** - Isolated execution environments
- **Health Checks** - Automatic monitoring and recovery
- **Traefik Routing** - Intelligent request routing
- **Logging** - Centralized log aggregation

### 🧪 Testing
- **100% Real Testing** - No mocking, production validation
- **Protocol Compliance** - MCP 2025-06-18 verified
- **Integration Tests** - End-to-end functionality
- **Performance Tests** - Load and stress testing

## Available Services

```{grid} 2
:gutter: 3

```{grid-item-card} 🌐 MCP Fetch
:link: mcp-fetch
:link-type: doc

Web content retrieval and HTTP operations. Perfect for web scraping, API calls, and content analysis.

**Capabilities:** HTTP requests, content fetching, URL validation
```

```{grid-item-card} 🧠 MCP Memory
:link: mcp-memory
:link-type: doc

Knowledge graph storage and retrieval. Ideal for building AI memory systems and relationship mapping.

**Capabilities:** Entity management, relations, observations, graph queries
```

```{grid-item-card} 🕒 MCP Time
:link: mcp-time
:link-type: doc

Temporal operations and timezone handling. Essential for global applications and scheduling.

**Capabilities:** Current time, timezone conversions, DST handling
```

```{grid-item-card} 🧮 MCP Sequential Thinking
:link: mcp-sequentialthinking
:link-type: doc

Structured problem-solving and reasoning workflows. Perfect for complex analytical tasks.

**Capabilities:** Multi-step reasoning, hypothesis testing, branching logic
```

```{grid-item-card} 📁 MCP Filesystem
:link: mcp-filesystem
:link-type: doc

File system operations and management. Ideal for file processing and content management.

**Capabilities:** File read/write, directory management, workspace isolation
```

```{grid-item-card} 🎯 MCP Everything
:link: mcp-everything
:link-type: doc

Combined functionality from multiple services. One-stop solution for diverse needs.

**Capabilities:** All-in-one MCP operations, unified interface
```

```{grid-item-card} 🔧 MCP Fetchs
:link: mcp-fetchs
:link-type: doc

Alternative web fetching implementation with enhanced features. Extended HTTP capabilities.

**Capabilities:** Advanced HTTP operations, content processing, header management
```

```{grid-item-card} 💻 MCP Tmux
:link: mcp-tmux
:link-type: doc

Terminal multiplexer control and automation. Perfect for managing terminal sessions programmatically.

**Capabilities:** Session management, window control, pane operations, command execution
```

```{grid-item-card} 🎭 MCP Playwright
:link: mcp-playwright
:link-type: doc

Browser automation and web testing. Ideal for web scraping, testing, and browser interactions.

**Capabilities:** Browser control, page automation, screenshot capture, web testing
```
```

## Service URLs

Each service is accessible via its dedicated subdomain:

| Service | URL | Protocol |
|---------|-----|----------|
| MCP Fetch | `https://mcp-fetch.${BASE_DOMAIN}/mcp` | MCP 2025-06-18 |
| MCP Memory | `https://mcp-memory.${BASE_DOMAIN}/mcp` | MCP 2025-06-18 |
| MCP Time | `https://mcp-time.${BASE_DOMAIN}/mcp` | MCP 2025-06-18 |
| MCP Sequential Thinking | `https://mcp-sequentialthinking.${BASE_DOMAIN}/mcp` | MCP 2025-06-18 |
| MCP Filesystem | `https://mcp-filesystem.${BASE_DOMAIN}/mcp` | MCP 2025-06-18 |
| MCP Everything | `https://mcp-everything.${BASE_DOMAIN}/mcp` | MCP 2025-06-18 |
| MCP Fetchs | `https://mcp-fetchs.${BASE_DOMAIN}/mcp` | MCP 2025-06-18 |
| MCP Tmux | `https://mcp-tmux.${BASE_DOMAIN}/mcp` | MCP 2025-06-18 |
| MCP Playwright | `https://mcp-playwright.${BASE_DOMAIN}/mcp` | MCP 2025-06-18 |

## Common Endpoints

All services provide standard endpoints:

### Primary Endpoints
- **`/mcp`** - Main MCP protocol endpoint (requires authentication)
- **`/health`** - Health check endpoint (public)
- **`/.well-known/oauth-authorization-server`** - OAuth discovery (public)

### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2025-06-21T23:38:12Z",
  "service": "mcp-fetch",
  "version": "1.0.0"
}
```

## Authentication Flow

All services use the same OAuth 2.1 authentication flow:

1. **Client Registration** - Register via `/register` endpoint
2. **Authorization** - Obtain authorization code via `/authorize`
3. **Token Exchange** - Exchange code for access token via `/token`
4. **Service Access** - Use Bearer token to access MCP endpoints

## Development Patterns

### Adding a New Service

To add a new MCP service:

1. **Create Service Directory**
   ```bash
   mkdir mcp-newservice
   cd mcp-newservice
   ```

2. **Create Dockerfile**
   ```dockerfile
   FROM python:3.12-alpine
   # Install official MCP server
   RUN pip install mcp-server-newservice
   # Install proxy
   COPY ../mcp-streamablehttp-proxy /tmp/proxy
   RUN pip install /tmp/proxy
   # Wrap the server
   CMD mcp-streamablehttp-proxy python -m mcp_server_newservice
   ```

3. **Create docker-compose.yml**
   ```yaml
   services:
     mcp-newservice:
       build: .
       labels:
         - "traefik.http.routers.mcp-newservice.rule=Host(`mcp-newservice.${BASE_DOMAIN}`)"
         # ... routing configuration
   ```

4. **Add to Main Compose**
   ```yaml
   include:
     - mcp-newservice/docker-compose.yml
   ```

5. **Create Tests**
   ```python
   # tests/test_mcp_newservice_integration.py
   # tests/test_mcp_newservice_comprehensive.py
   ```

### Service Configuration

Standard environment variables for all services:

```bash
# Protocol configuration
MCP_PROTOCOL_VERSION=2025-06-18
MCP_CORS_ORIGINS=*
PORT=3000

# Domain configuration (from .env)
BASE_DOMAIN=yourdomain.com
```

## Monitoring and Observability

### Health Monitoring
- **Docker Health Checks** - Container-level monitoring
- **HTTP Health Endpoints** - Application-level monitoring
- **Traefik Dashboard** - Traffic and routing monitoring

### Logging
- **Centralized Logs** - All services log to `./logs/`
- **Structured Logging** - JSON format for parsing
- **Log Rotation** - Automatic cleanup and archival

### Metrics
- **Request Metrics** - Traefik provides request/response metrics
- **Service Metrics** - Custom metrics via health endpoints
- **Performance Monitoring** - Response time and throughput tracking

## Troubleshooting

### Common Issues

1. **Service Not Starting**
   ```bash
   # Check container logs
   docker logs mcp-servicename
   
   # Check health status
   curl https://mcp-servicename.yourdomain.com/health
   ```

2. **Authentication Failures**
   ```bash
   # Verify OAuth configuration
   curl https://mcp-servicename.yourdomain.com/.well-known/oauth-authorization-server
   
   # Test token validity
   mcp-streamablehttp-client --test-auth
   ```

3. **Protocol Issues**
   ```bash
   # Test protocol compliance
   mcp-streamablehttp-client --list-tools
   
   # Check protocol version
   just test-file tests/test_mcp_servicename_integration.py
   ```

### Debug Commands

```bash
# Service status
just logs mcp-servicename

# Full system health
just check-health

# Test specific service
just test-file tests/test_mcp_servicename_comprehensive.py

# Protocol compliance check
just test-protocol-compliance
```

## Performance Considerations

### Resource Usage
- **Memory** - Each service container: ~50-100MB
- **CPU** - Minimal unless processing large requests
- **Storage** - Logs and temporary files only (except mcp-memory)

### Scaling
- **Horizontal** - Multiple instances behind Traefik
- **Vertical** - Resource limits via Docker
- **Load Balancing** - Traefik automatic load balancing

### Optimization
- **Caching** - HTTP caching headers where appropriate
- **Connection Pooling** - Persistent connections for efficiency
- **Resource Limits** - Docker memory and CPU constraints

---

**Next Steps:**
- Explore individual service documentation for detailed capabilities
- Check the {doc}`../integration/index` guide for client integration
- Review {doc}`../development/adding-services` for development guidelines