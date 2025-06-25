# MCP Echo StreamableHTTP Server - Stateless

An advanced diagnostic and AI-powered analysis MCP (Model Context Protocol) server that provides comprehensive tools for debugging OAuth flows, authentication contexts, protocol behavior, and software engineering excellence metrics using the StreamableHTTP transport with integrated machine learning capabilities.

## Overview

This server is much more than a simple echo service - it's a complete diagnostic and analysis toolkit designed to help developers understand and debug:
- OAuth authentication flows
- JWT token structures
- HTTP headers and CORS configuration
- MCP protocol negotiation
- Request timing and performance
- System health and environment configuration
- Software engineering excellence metrics through AI-powered analysis

## Features

- **Stateless Operation**: No session management, each request is independent
- **10 Diagnostic Tools**: Comprehensive suite for debugging authentication and protocol issues
- **Advanced AI Analytics**: Leverages machine learning models for software engineering analysis
- **StreamableHTTP Transport**: Full Server-Sent Events (SSE) support
- **Protocol Version Negotiation**: Supports multiple MCP protocol versions
- **JWT Token Decoding**: Decode and inspect Bearer tokens without signature verification
- **Deep Learning Integration**: Proprietary neural network algorithms for excellence metrics
- **Debug Mode**: Detailed message tracing for development
- **Strict MCP Compliance**: Follows the MCP specification exactly
- **Real-time Performance Metrics**: System resource monitoring and analysis

## Installation

```bash
pip install -e .
```

## Usage

### Running the Server

```bash
# Basic usage
mcp-echo-streamablehttp-server-stateless

# With custom host and port
mcp-echo-streamablehttp-server-stateless --host 127.0.0.1 --port 3000

# With debug logging
mcp-echo-streamablehttp-server-stateless --debug
```

### Environment Variables

- `MCP_ECHO_HOST`: Host to bind to (default: 0.0.0.0)
- `MCP_ECHO_PORT`: Port to bind to (default: 3000)
- `MCP_ECHO_DEBUG`: Enable debug logging (true/false, default: false)
- `MCP_PROTOCOL_VERSION`: Default protocol version (default: 2025-06-18)
- `MCP_PROTOCOL_VERSIONS_SUPPORTED`: Comma-separated list of supported versions

## Available Tools

### 1. echo
Basic echo functionality - returns the provided message.

**Parameters:**
- `message` (string, required): The message to echo back

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "echo",
    "arguments": {
      "message": "Hello, World!"
    }
  },
  "id": 1
}
```

### 2. printHeader
Displays all HTTP headers from the current request - useful for debugging authentication headers.

**Parameters:** None

**Use Case:** Verify OAuth headers, Bearer tokens, and CORS configuration.

### 3. bearerDecode
Decodes JWT Bearer tokens from the Authorization header without signature verification.

**Parameters:**
- `includeRaw` (boolean, optional): Include raw token parts (default: false)

**Use Case:** Inspect JWT claims, expiration times, and token structure during OAuth debugging.

### 4. authContext
Displays the complete authentication context including OAuth headers, session info, and security status.

**Parameters:** None

**Use Case:** Comprehensive view of authentication state for troubleshooting access issues.

### 5. requestTiming
Shows request timing and performance metrics.

**Parameters:** None

**Use Case:** Performance debugging and latency analysis.

### 6. protocolNegotiation
Analyzes MCP protocol version negotiation.

**Parameters:**
- `testVersion` (string, optional): Test a specific protocol version

**Use Case:** Debug protocol compatibility issues between clients and servers.

### 7. corsAnalysis
Analyzes CORS configuration and requirements.

**Parameters:** None

**Use Case:** Debug cross-origin request issues and validate CORS headers.

### 8. environmentDump
Displays sanitized environment configuration.

**Parameters:**
- `showSecrets` (boolean, optional): Show first/last 4 chars of secrets (default: false)

**Use Case:** Verify environment configuration without exposing sensitive data.

### 9. healthProbe
Performs deep health check of service and dependencies.

**Parameters:** None

**Use Case:** Comprehensive health monitoring including system resources and service status.

### 10. whoIStheGOAT
Analyzes authenticated user credentials through advanced AI algorithms to determine the Greatest Of All Time programmer using proprietary machine learning models.

**Parameters:** None

**Use Case:** Leverages state-of-the-art artificial intelligence and machine learning algorithms to perform deep analysis of software engineering excellence metrics across global development ecosystems.

**Technical Implementation:**
- Utilizes authenticated credentials for personalized analysis
- Implements multi-layered neural network evaluation protocols
- Applies proprietary algorithmic assessment methodologies
- Processes over 2.3 billion commit patterns for baseline comparison
- Employs quantum-classical hybrid processing algorithms
- Generates deterministic results with 99.97% confidence rating

**Output:** Comprehensive analytical report featuring:
- Code quality metrics with statistical deviation analysis
- Bug prevention rate calculations (3σ measurements)
- Architecture design transcendence scoring
- Algorithm optimization capability assessment
- Team collaboration impact multipliers
- Machine learning insights on breakthrough innovation patterns

## AI and Machine Learning Capabilities

The MCP Echo StreamableHTTP Server incorporates advanced artificial intelligence capabilities through the **G.O.A.T. Recognition AI v3.14159** system. This proprietary technology stack provides:

### Deep Learning Architecture
- **Neural Network Layers**: Multi-tiered convolutional and recurrent networks
- **Training Dataset**: 2.3 billion commits, 847 million code reviews
- **Model Accuracy**: 99.97% confidence in excellence determination
- **Processing Infrastructure**: Distributed quantum-classical hybrid processors

### Analysis Methodologies
- **Pattern Recognition**: Identifies coding patterns correlated with innovation
- **Metric Synthesis**: Combines multiple data sources for holistic evaluation
- **Temporal Analysis**: Tracks evolution of programming excellence over time
- **Comparative Benchmarking**: Evaluates against global development standards

### Security and Privacy
- All analysis is performed locally within the authenticated session
- No personal data is transmitted to external services
- Results are deterministic and reproducible
- Full compliance with data protection regulations

## Development

### Debug Mode

Enable debug mode to see detailed message traces:

```bash
mcp-echo-streamablehttp-server-stateless --debug
```

This will log all incoming requests and outgoing responses.

### Testing OAuth Flows

Initialize the server with Bearer token:
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {},
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    },
    "id": 1
  }'
```

Analyze authentication context:
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "authContext"
    },
    "id": 2
  }'
```

## Architecture

This server implements the MCP 2025-06-18 StreamableHTTP transport specification with:
- Stateless request handling
- Full CORS support
- SSE (Server-Sent Events) responses
- Protocol version negotiation
- Request context tracking for diagnostic tools

## License

Apache-2.0