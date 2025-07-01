# System Components Architecture

Detailed architecture of the three sacred layers that compose the MCP OAuth Gateway.

## Component Hierarchy

```{mermaid}
graph TB
    subgraph "Layer 1: Divine Router"
        T[Traefik v3.0]
        T1[Entrypoints<br/>:80 :443]
        T2[Routers<br/>Priority-based]
        T3[Middlewares<br/>ForwardAuth]
        T4[Services<br/>Load Balancers]

        T --> T1
        T --> T2
        T --> T3
        T --> T4
    end

    subgraph "Layer 2: OAuth Oracle"
        A[Auth Service]
        A1[OAuth Server<br/>Authlib]
        A2[Dynamic Registration<br/>RFC 7591]
        A3[JWT Service<br/>RS256]
        A4[GitHub Integration]

        R[Redis Storage]
        R1[Client Registry]
        R2[Token Store]
        R3[Session Cache]

        A --> A1
        A --> A2
        A --> A3
        A --> A4
        A --> R
        R --> R1
        R --> R2
        R --> R3
    end

    subgraph "Layer 3: MCP Services"
        P[Proxy Services]
        P1[mcp-streamablehttp-proxy]
        P2[stdio subprocess]

        N[Native Services]
        N1[FastAPI Server]
        N2[Direct MCP Protocol]

        P --> P1
        P1 --> P2
        N --> N1
        N --> N2
    end
```

## Layer 1: Traefik (Divine Router)

### Core Responsibilities

Traefik serves as the single entry point for all external traffic:

- **SSL Termination**: Automatic HTTPS via Let's Encrypt
- **Request Routing**: Path and host-based routing with priorities
- **Authentication Enforcement**: ForwardAuth middleware
- **Load Balancing**: Distribute requests across service instances
- **Service Discovery**: Automatic via Docker labels

### Configuration Components

#### Entrypoints
```yaml
entrypoints:
  web:
    address: ":80"
    http:
      redirections:
        entrypoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"
```

#### Routers
```yaml
# Priority-based routing
routers:
  auth-oauth:
    rule: "PathPrefix(`/register`)"
    priority: 4  # Highest
  mcp-service:
    rule: "Host(`service.domain`)"
    priority: 2
    middlewares:
      - mcp-auth@file
```

#### Middlewares
```yaml
middlewares:
  mcp-auth:
    forwardAuth:
      address: "http://auth:8000/verify"
      authResponseHeaders:
        - X-User-Id
        - X-User-Name
```

### Scaling Considerations

- Stateless design enables horizontal scaling
- Shared certificate storage via volume
- Configuration via Docker labels
- Health monitoring built-in

## Layer 2: Auth Service (OAuth Oracle)

### Core Components

#### OAuth Server (Authlib)
- OAuth 2.1 implementation
- PKCE enforcement
- Token introspection
- Token revocation

#### Dynamic Registration (RFC 7591)
```python
# Public registration endpoint
@app.post("/register")
async def register_client(request: ClientRegistration):
    client_id = generate_client_id()
    client_secret = generate_client_secret()
    registration_token = generate_registration_token()
    # Store in Redis
    return ClientRegistrationResponse(...)
```

#### JWT Service
```python
# Token generation with RS256
def generate_token(user_id: str, client_id: str):
    payload = {
        "iss": f"https://auth.{BASE_DOMAIN}",
        "sub": f"github|{user_id}",
        "aud": client_id,
        "exp": time() + ACCESS_TOKEN_LIFETIME,
        "jti": generate_jti()
    }
    return jwt.encode(payload, private_key, algorithm="RS256")
```

#### GitHub Integration
- OAuth application for user authentication
- User allowlist enforcement
- Profile data extraction

### Redis Storage Architecture

#### Data Models

```python
# Client Registration
oauth:client:{client_id} = {
    "client_id": str,
    "client_secret": str,
    "client_name": str,
    "redirect_uris": List[str],
    "registration_access_token": str,
    "created_at": datetime,
    "expires_at": datetime
}

# Access Token
oauth:token:{jti} = {
    "client_id": str,
    "user_id": str,
    "scope": str,
    "issued_at": datetime,
    "expires_at": datetime
}

# User Token Index
oauth:user_tokens:{username} = Set[jti]
```

#### TTL Management
- State tokens: 5 minutes
- Authorization codes: 10 minutes (or 1 year for long-lived)
- Access tokens: 30 days
- Refresh tokens: 1 year
- Client registrations: 90 days (or eternal)

## Layer 3: MCP Services

### Proxy Pattern Architecture

#### Components
```
┌─────────────────────────────────────┐
│      mcp-streamablehttp-proxy       │
├─────────────────────────────────────┤
│  HTTP Server (FastAPI)              │
│  Session Manager                    │
│  Process Manager                    │
│  Message Router                     │
├─────────────────────────────────────┤
│      stdio subprocess               │
│  (Official MCP Server)              │
└─────────────────────────────────────┘
```

#### Session Management
```python
sessions = {
    "session-id": {
        "process": subprocess.Popen(...),
        "created_at": datetime,
        "last_activity": datetime,
        "message_queue": Queue()
    }
}
```

#### Message Flow
1. HTTP request received
2. Session lookup/creation
3. Forward to subprocess stdin
4. Read from subprocess stdout
5. Return as SSE stream

### Native Pattern Architecture

#### Components
```
┌─────────────────────────────────────┐
│    Native StreamableHTTP Server     │
├─────────────────────────────────────┤
│  FastAPI Application                │
│  MCP Protocol Handler               │
│  Tool Implementations               │
│  Direct HTTP Responses              │
└─────────────────────────────────────┘
```

#### Protocol Implementation
```python
@app.post("/mcp")
async def handle_mcp(request: Request):
    body = await request.json()

    if body["method"] == "initialize":
        return handle_initialize(body)
    elif body["method"] == "tools/call":
        return handle_tool_call(body)
    # ... other methods
```

## Inter-Component Communication

### Network Architecture

All components communicate via Docker network:

```yaml
networks:
  public:
    driver: bridge
    internal: false
```

### Service Discovery

Services discover each other by name:
- `http://auth:8000`
- `http://redis:6379`
- `http://mcp-service:3000`

### Security Boundaries

```
External → Traefik (HTTPS required)
         ↓
Traefik → Auth (Internal HTTP)
         ↓
Auth → Redis (Internal Redis protocol)
         ↓
Traefik → MCP Services (Internal HTTP)
```

## Component Lifecycle

### Startup Sequence

1. **Redis** starts first (no dependencies)
2. **Auth** waits for Redis health
3. **Traefik** starts (no hard dependencies)
4. **MCP Services** start in parallel

### Health Checks

Each component implements health checks:

```yaml
# Redis
test: ["CMD", "redis-cli", "ping"]

# Auth
test: ["CMD", "curl", "-f", "http://localhost:8000/health"]

# Traefik
test: ["CMD", "traefik", "healthcheck"]

# MCP Services
test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
```

### Graceful Shutdown

Components handle SIGTERM:
1. Stop accepting new requests
2. Complete in-flight requests
3. Close connections cleanly
4. Exit with status 0

## Resource Management

### CPU Allocation

```yaml
# High priority services
traefik:
  cpus: '2'
auth:
  cpus: '1'

# Standard services
mcp-service:
  cpus: '0.5'
```

### Memory Limits

```yaml
# Infrastructure
redis:
  memory: 1G
auth:
  memory: 512M

# MCP Services
mcp-service:
  memory: 256M
```

### Storage Volumes

```yaml
volumes:
  traefik-certificates:  # Persistent
  redis-data:           # Persistent
  auth-keys:           # Persistent
  logs:                # Rotated
```

## Monitoring Integration

### Metrics Collection

Each component exposes metrics:
- Request count
- Response time
- Error rate
- Resource usage

### Log Aggregation

Centralized logging structure:
```
logs/
├── traefik/
│   ├── access.log
│   └── traefik.log
├── auth/
│   └── app.log
└── {service}/
    └── service.log
```

### Alerting Points

Critical monitoring points:
- SSL certificate expiry
- Redis memory usage
- Auth service errors
- Service health failures
