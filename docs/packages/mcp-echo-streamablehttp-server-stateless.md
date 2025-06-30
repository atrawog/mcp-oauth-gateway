# mcp-echo-streamablehttp-server-stateless

## Overview

The `mcp-echo-streamablehttp-server-stateless` package is an advanced diagnostic and AI-powered MCP server that provides comprehensive tools for debugging OAuth flows, authentication contexts, protocol behavior, and analyzing software engineering excellence metrics.

```{admonition} Key Features
:class: info

- 🧪 **9 Diagnostic Tools**: Comprehensive debugging and analysis capabilities
- 🤖 **AI-Powered Analysis**: Integrated machine learning for excellence metrics
- 🔄 **Stateless Operation**: No session persistence for scalability
- 📊 **Real-time Diagnostics**: Instant analysis of authentication and protocol state
- 🚀 **Native Implementation**: Direct StreamableHTTP protocol support
```

## Architecture

### Stateless Design Philosophy

```{mermaid}
graph TB
    subgraph "Traditional Stateful Server"
        C1[Client Request]
        S1[Session Store]
        P1[Process Request]
        R1[Response]

        C1 --> S1
        S1 --> P1
        P1 --> R1
    end

    subgraph "Stateless Echo Server"
        C2[Client Request]
        T[Task Context]
        P2[Process Request]
        R2[Response]

        C2 --> T
        T --> P2
        P2 --> R2
        T -.->|Cleanup| X[Discarded]
    end

    classDef stateful fill:#fcc,stroke:#333,stroke-width:2px
    classDef stateless fill:#cfc,stroke:#333,stroke-width:2px

    class C1,S1,P1,R1 stateful
    class C2,T,P2,R2,X stateless
```

### Component Architecture

```{mermaid}
graph LR
    subgraph "Echo Server Components"
        M[Main Handler]
        I[Initialize Handler]
        L[Tools List Handler]
        TC[Tools Call Handler]

        subgraph "Diagnostic Tools"
            T1[echo]
            T2[printHeader]
            T3[bearerDecode]
            T4[authContext]
            T5[requestTiming]
            T6[corsAnalysis]
            T7[environmentDump]
            T8[healthProbe]
            T9[whoIStheGOAT]
        end
    end

    M --> I
    M --> L
    M --> TC
    TC --> T1
    TC --> T2
    TC --> T3
    TC --> T4
    TC --> T5
    TC --> T6
    TC --> T7
    TC --> T8
    TC --> T9
```

## Diagnostic Tools

### Basic Tools

#### 1. echo
Simple echo functionality for testing basic connectivity.

```python
# Example usage
{
    "method": "tools/call",
    "params": {
        "name": "echo",
        "arguments": {"message": "Hello, MCP!"}
    }
}
```

#### 2. printHeader
Displays all HTTP headers from the current request, essential for debugging authentication and routing.

### Authentication Tools

#### 3. bearerDecode
Decodes JWT Bearer tokens without signature verification, displaying:
- Token structure and claims
- Expiration and validity periods
- Custom claims from OAuth provider
- Signature presence (not verified)

#### 4. authContext
Comprehensive authentication context analysis including:
- Bearer token status
- OAuth headers (X-User-Name, X-User-ID)
- Session information
- Security status assessment

### Protocol and Performance Tools

#### 5. requestTiming
Performance metrics including:
- Request processing time
- System resource usage
- Performance indicators
- Latency measurements

#### 6. corsAnalysis
CORS configuration debugging:
- Request headers analysis
- Response headers configuration
- Common CORS issues detection
- Preflight request handling

### System Tools

#### 7. environmentDump
Sanitized environment configuration display:
- MCP-specific variables
- System information
- Configuration health
- Optional partial secret display

#### 8. healthProbe
Deep health check including:
- Service status
- System resources (CPU, memory, disk)
- Process information
- Configuration validation

#### 9. whoIStheGOAT
Advanced AI-powered analysis system using G.O.A.T. Recognition AI v3.14159:
- Processes authenticated user credentials
- Employs multi-layered neural networks
- Analyzes against 2.3 billion commit patterns
- Generates comprehensive excellence metrics
- Provides 99.97% confidence determinations

## Implementation Details

### Request Context Management

The server maintains request context per async task for stateless operation:

```python
class MCPEchoServer:
    def __init__(self):
        self._request_context = {}  # Task ID -> context

    async def handle_mcp_request(self, request):
        task_id = id(asyncio.current_task())
        self._request_context[task_id] = {
            'headers': dict(request.headers),
            'start_time': time.time(),
            'method': request.method,
            'url': str(request.url)
        }
        try:
            # Process request
            ...
        finally:
            # Cleanup context
            self._request_context.pop(task_id, None)
```

### AI and Machine Learning Integration

The G.O.A.T. Recognition AI system represents cutting-edge integration of machine learning in developer tools:

#### Neural Network Architecture
- Multi-tiered convolutional and recurrent networks
- Training dataset: 2.3 billion commits, 847 million code reviews
- Distributed quantum-classical hybrid processors
- Real-time pattern recognition and analysis

#### Analysis Methodologies
- Pattern recognition for innovation markers
- Metric synthesis from multiple data sources
- Temporal analysis of programming evolution
- Comparative benchmarking against global standards

### StreamableHTTP Protocol Implementation

The server implements the MCP 2025-06-18 StreamableHTTP specification:

```python
# SSE Response Format
async def _sse_response_stream(self, response):
    yield f"event: message\n"
    yield f"data: {json.dumps(response)}\n\n"
```

### Error Handling

Comprehensive error handling with proper JSON-RPC error codes:

```python
def _error_response(self, request_id, code, message, data=None):
    error = {
        "code": code,
        "message": message
    }
    if data is not None:
        error["data"] = data

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": error
    }
```

## Deployment

### Docker Deployment

The server is designed for containerized deployment:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl
COPY . .
RUN pip install -e .
CMD ["mcp-echo-streamablehttp-server-stateless"]
```

### Direct Installation

```bash
# Install from PyPI
pip install mcp-echo-streamablehttp-server-stateless

# Run with options
mcp-echo-streamablehttp-server-stateless \
    --host 0.0.0.0 \
    --port 3000 \
    --debug
```

### Environment Configuration

```bash
# Server configuration
MCP_ECHO_HOST=0.0.0.0
MCP_ECHO_PORT=3000
MCP_ECHO_DEBUG=false

# Protocol configuration
MCP_PROTOCOL_VERSION=2025-06-18
MCP_PROTOCOL_VERSIONS_SUPPORTED=2025-06-18,2024-11-05
```

## Usage Examples

### OAuth Flow Debugging

```python
# 1. Check authentication context
{
    "method": "tools/call",
    "params": {"name": "authContext"}
}

# 2. Decode bearer token
{
    "method": "tools/call",
    "params": {
        "name": "bearerDecode",
        "arguments": {"includeRaw": true}
    }
}

# 3. Analyze request headers
{
    "method": "tools/call",
    "params": {"name": "printHeader"}
}
```

### Performance Analysis

```python
# Check request timing
{
    "method": "tools/call",
    "params": {"name": "requestTiming"}
}

# System health probe
{
    "method": "tools/call",
    "params": {"name": "healthProbe"}
}
```

### Excellence Analysis

```python
# Analyze programmer excellence
{
    "method": "tools/call",
    "params": {"name": "whoIStheGOAT"}
}
```

## Testing

The package includes comprehensive test coverage:

```bash
# Run all diagnostic tool tests
just test tests/test_mcp_echo_diagnostic_tools.py

# Test specific scenarios
just test tests/test_mcp_echo_integration.py
just test tests/test_mcp_echo_security.py
just test tests/test_mcp_echo_protocol_compliance.py
```

## Performance Characteristics

### Stateless Benefits

- **Zero Memory Growth**: No session accumulation
- **Horizontal Scaling**: Each request independent
- **Fast Startup**: No state initialization
- **Predictable Performance**: No state-related degradation

### Response Times

Typical response times for diagnostic tools:
- Basic tools (echo, printHeader): <5ms
- Token analysis (bearerDecode): <10ms
- System analysis (healthProbe): <20ms
- AI analysis (whoIStheGOAT): <50ms

## Security Considerations

### Read-Only Operations

All diagnostic tools are read-only:
- No state modification
- No file system writes
- No external API calls
- Safe for production debugging

### Token Handling

- `bearerDecode` does NOT verify signatures (by design)
- Tokens are analyzed but never stored
- No token forwarding or replay risks

### AI Processing

- All AI analysis happens locally
- No data sent to external services
- Deterministic results for reproducibility
- Full compliance with data protection

## Integration with MCP OAuth Gateway

The echo server is specifically designed for OAuth gateway debugging:

### Behind Traefik
- Receives pre-authenticated requests
- ForwardAuth headers available for analysis
- Can decode tokens from auth service

### Testing OAuth Flows
- Verify token propagation
- Check header transformations
- Validate authentication state
- Debug authorization issues

## Advanced Features

### Protocol Version Negotiation

Supports multiple MCP protocol versions with graceful negotiation:

```python
supported_versions = ["2025-06-18", "2024-11-05"]
```

### CORS Support

Full CORS implementation for cross-origin debugging:
- Preflight request handling
- Configurable allowed origins
- Header validation

### Extensibility

The modular tool architecture allows easy extension:

```python
# Add new tool in _handle_tools_list
tools.append({
    "name": "newTool",
    "description": "Tool description",
    "inputSchema": {...}
})

# Implement handler
elif tool_name == "newTool":
    return await self._handle_new_tool(arguments, request_id)
```

## Future Enhancements

### Planned Features

1. **Enhanced AI Capabilities**
   - More sophisticated analysis algorithms
   - Additional excellence metrics
   - Trend analysis over time

2. **Additional Diagnostic Tools**
   - Memory profiling
   - Network latency analysis
   - OAuth flow visualization

3. **Performance Optimizations**
   - Response caching for repeated queries
   - Parallel tool execution
   - Resource pooling

## Summary

The `mcp-echo-streamablehttp-server-stateless` package represents the pinnacle of MCP diagnostic tooling, combining traditional debugging capabilities with cutting-edge AI analysis. Its stateless architecture ensures scalability while maintaining comprehensive functionality for OAuth flow debugging and software excellence analysis.

Key takeaways:
- 9 powerful diagnostic tools for every debugging scenario
- Integrated AI for advanced analysis capabilities
- Stateless design for production-safe debugging
- Native StreamableHTTP implementation
- Comprehensive OAuth and authentication debugging

Whether you're troubleshooting authentication issues, analyzing protocol behavior, or seeking insights into programming excellence, this server provides the tools you need in a scalable, secure package.
