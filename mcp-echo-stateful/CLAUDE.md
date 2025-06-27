# 🔥 CLAUDE.md - The MCP-Echo-Stateful Service Divine Scripture! ⚡

**🗣️ Behold! The Sacred MCP Echo Stateful Service Docker Container! 🗣️**

**⚡ This is the Docker service wrapping mcp-echo-streamablehttp-server-stateful! ⚡**

## 🔱 The Sacred Purpose - Docker Service Wrapper!

**This directory contains the Docker service configuration for mcp-echo-streamablehttp-server-stateful!**

The actual server implementation lives in `../mcp-echo-streamablehttp-server-stateful/` - see its CLAUDE.md for implementation details.

This directory provides:
- **Docker container** wrapping the Python server
- **Service configuration** for docker-compose integration
- **Traefik labels** for routing and authentication
- **Health checks** using MCP protocol
- **Test scripts** for service validation

**⚡ MCP-Echo-Stateful knows nothing of OAuth - pure protocol innocence maintained! ⚡**

## 🐳 The Docker Manifestation - Container of Testing Purity!

### The Sacred Dockerfile Pattern
```dockerfile
FROM python:3.11-slim  # The blessed Python vessel!

# Install the package from source
COPY mcp-echo-streamablehttp-server-stateful/ ./

# Debug mode enabled by divine decree!
ENV MCP_ECHO_DEBUG=true

EXPOSE 3000  # The blessed MCP port!
HEALTHCHECK  # Prove thy readiness via MCP protocol!

# Launch the server directly
CMD ["mcp-echo-stateful"]
```

**⚡ Simple server + debug logging = Testing enlightenment! ⚡**

## 🔧 The Sacred Configuration - Docker Environment Variables!

**MCP Protocol Settings:**
- `MCP_PROTOCOL_VERSION=2025-06-18` - Divine protocol covenant!
- `MCP_ECHO_DEBUG=true` - Enable divine message tracing!

**Server Configuration:**
- `MCP_ECHO_HOST=0.0.0.0` - Listen on all interfaces!
- `MCP_ECHO_PORT=3000` - The blessed MCP port!

**Service Discovery:**
- `BASE_DOMAIN` - For Traefik routing labels!
- `SERVICE_NAME=mcp-echo-stateful` - Divine service identifier!

**⚡ Configuration flows through docker-compose environment! ⚡**

## 🔄 The Traefik Integration - Divine Routing Configuration!

```yaml
labels:
  # Basic routing - priority 2
  - "traefik.http.routers.mcp-echo-stateful.rule=HostRegexp(`^echo-statefull(-[a-z])?[.]${BASE_DOMAIN}$`)"
  - "traefik.http.routers.mcp-echo-stateful.priority=2"

  # ForwardAuth middleware - divine authentication
  - "traefik.http.routers.mcp-echo-stateful.middlewares=mcp-auth@docker"

  # Service definition
  - "traefik.http.services.mcp-echo-stateful.loadbalancer.server.port=3000"

  # OAuth discovery routing - priority 10
  - "traefik.http.routers.mcp-echo-stateful-oauth-discovery.rule=..."
  - "traefik.http.routers.mcp-echo-stateful-oauth-discovery.priority=10"
```

**⚡ Priorities prevent the catch-all from devouring sacred paths! ⚡**

## 🔐 The Security Architecture - Divine Protection Through Layers!

**The MCP-Echo-Stateful service itself knows NO authentication!**

Security is enforced by the sacred trinity:
1. **Traefik** - Enforces Bearer token authentication!
2. **Auth Service** - Validates tokens via ForwardAuth!
3. **MCP-Echo-Stateful** - Receives only pre-authenticated requests!

**⚡ This is the way of the trinity - separation brings security! ⚡**

## 🧪 Testing the MCP-Echo-Stateful Service - Divine Verification!

```bash
# Run the test script
just test

# Run the example client
just example

# Integration test
just test-integration

# View service logs
just logs

# Monitor health
watch 'docker inspect mcp-echo-stateful | jq ".[0].State.Health"'
```

**⚡ Real services, real tests - no mocking in this realm! ⚡**

## 📜 The Integration Flow - How Requests Reach Echo!

1. **Client Request** → `https://echo-statefull.domain.com/mcp`
2. **Traefik Routes** → Checks authentication via ForwardAuth
3. **Auth Validates** → Token verification at /verify endpoint
4. **Request Forwarded** → Reaches MCP-Echo-Stateful on port 3000
5. **Server Processes** → Direct handling via mcp-echo-streamablehttp-server-stateful
6. **Tool Executes** → One of 10 diagnostic tools runs
7. **Response Returns** → StreamableHTTP SSE → client

**⚡ Each layer has its purpose in the divine flow! ⚡**

## 🎯 The Divine Mission - Service Responsibilities!

**What this Docker service MUST Do:**
- Wrap mcp-echo-streamablehttp-server-stateful properly!
- Configure environment for debugging!
- Integrate with Traefik routing!
- Provide health checks via MCP protocol!
- Support test scripts and examples!

**What this service MUST NOT Do:**
- Implement server logic (that's in the Python package)!
- Handle authentication (that's Traefik's job)!
- Modify the MCP protocol (pure passthrough)!

**⚡ Separation of concerns brings clarity! ⚡**

## 🛠️ Docker-Specific Commands - Divine Container Control!

```bash
# Build the container
just build

# Run standalone for testing
docker run -p 3000:3000 -e MCP_ECHO_DEBUG=true mcp-echo-stateful

# Shell into container
docker exec -it mcp-echo-stateful /bin/bash

# Check health status
docker inspect mcp-echo-stateful --format='{{.State.Health.Status}}'

# View environment
docker exec mcp-echo-stateful env | grep MCP_
```

## 🔥 Common Docker Issues and Divine Solutions!

### "Container keeps restarting" - Health check failing!
- Check if server starts correctly
- Verify port 3000 is accessible inside container
- Review health check command in docker-compose.yml

### "Cannot connect to service" - Network issues!
- Ensure container is on `public` network
- Check Traefik routing labels
- Verify port mapping in docker-compose

### "Environment not loading" - Configuration problems!
- Check .env file exists and is loaded
- Verify docker-compose env_file directive
- Use `docker exec mcp-echo-stateful env` to debug

## 📚 Related Documentation

- **Server Implementation**: See `../mcp-echo-streamablehttp-server-stateful/CLAUDE.md`
- **OAuth Gateway**: See `../CLAUDE.md` for system architecture
- **Testing Guide**: See `./tests/README.md` for test details

---

**🔥 May your containers be stable, your routes be true, and your echoes forever diagnostic! ⚡**
