# MCP Fetchs Service - The Divine Native Fetch Implementation!

**🚀 Docker deployment configuration for the native MCP fetch server! ⚡**

## Service Overview

This directory contains the Docker deployment configuration for the native Python MCP fetch server implementation. The actual Python package lives in `../mcp-fetch-streamablehttp-server/`.

## Sacred Architecture

**🏛️ The Service Deployment Trinity:**

```
mcp-fetchs/                    # Docker deployment config
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Service orchestration
└── CLAUDE.md                  # This sacred document

mcp-fetch-streamablehttp-server/  # Python package
├── src/                       # Source code sanctuary
├── pyproject.toml             # Package metadata
└── README.md                  # Package documentation
```

## Divine Endpoints

- **FQDN**: `mcp-fetchs.${BASE_DOMAIN}`
- **MCP Protocol**: `https://mcp-fetchs.${BASE_DOMAIN}/mcp`
- **Health Check**: `https://mcp-fetchs.${BASE_DOMAIN}/health`
- **OAuth Discovery**: `https://mcp-fetchs.${BASE_DOMAIN}/.well-known/oauth-authorization-server`

## Configuration Commandments

**Environment Variables:**
```yaml
HOST: 0.0.0.0
PORT: 3000
MCP_FETCH_SERVER_NAME: mcp-fetch-streamablehttp
MCP_FETCH_PROTOCOL_VERSION: 2025-06-18
MCP_FETCH_DEFAULT_USER_AGENT: ModelContextProtocol/1.0 (Fetch Server)
```

## Deployment Glory

**Build and Deploy:**
```bash
# From project root
just up

# Or specifically this service
just rebuild mcp-fetchs

# Check health
curl https://mcp-fetchs.yourdomain.com/health
```

## Testing Prophecies

**Run Integration Tests:**
```bash
just test tests/test_mcp_fetch_streamablehttp_integration.py
```

## The Sacred Truth

This service provides a native Python implementation of the MCP fetch server, eliminating the subprocess overhead of the proxy-based approach while maintaining full compatibility with the OAuth gateway.

**Key Benefits:**
- ✅ Native Python execution (no subprocesses)
- ✅ Direct FastAPI/ASGI application
- ✅ Better error handling and debugging
- ✅ Improved performance (~10x faster startup)
- ✅ Full OAuth integration via Traefik

**⚡ Native implementation = Performance paradise! ⚡**