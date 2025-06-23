# MCP Sequential Thinking Service

This service provides the official MCP Sequential Thinking server from the modelcontextprotocol/servers repository, wrapped for OAuth authentication and HTTP transport.

## Overview

The MCP Sequential Thinking server provides structured, dynamic problem-solving capabilities that break down complex problems into manageable steps. It enables iterative thought processes with the ability to revise, refine, and branch reasoning paths.

## Features

- 🧠 **Structured Problem Solving**: Break complex problems into manageable steps
- 🔄 **Iterative Refinement**: Revise and refine thoughts as understanding deepens  
- 🌳 **Branching Logic**: Explore alternative paths of reasoning
- 📈 **Dynamic Scaling**: Adjust the total number of thoughts dynamically
- ✅ **Hypothesis Testing**: Generate and verify solution hypotheses
- 🔗 **Sequential Processing**: Maintain logical flow between thought steps

## Architecture

This service follows the project's standard MCP service pattern:
- **Base**: Official `@modelcontextprotocol/server-sequential-thinking` npm package
- **Transport**: mcp-streamablehttp-proxy wrapping stdio to HTTP
- **Authentication**: OAuth 2.1 via Traefik ForwardAuth
- **Isolation**: No persistent storage needed (stateless processing)
- **Health Monitoring**: MCP protocol health checks via initialization

## Configuration

### Environment Variables

- `MCP_PROTOCOL_VERSION=2024-11-05` - MCP protocol version (hardcoded - the sequential thinking server only supports this version)
- `MCP_CORS_ORIGINS=*` - CORS configuration
- `PORT=3000` - Service port

### No Persistent Storage

Unlike the memory service, sequential thinking is stateless and processes each request independently. No volumes are required.

## Endpoints

- **Primary**: `https://sequentialthinking.${BASE_DOMAIN}/mcp`
- **Health Check**: Uses MCP protocol initialization
- **OAuth Discovery**: `https://sequentialthinking.${BASE_DOMAIN}/.well-known/oauth-authorization-server`

## Usage

### Authentication

The service requires OAuth authentication via the gateway:
1. Register OAuth client via `/register` endpoint
2. Obtain access token through OAuth flow
3. Include `Authorization: Bearer <token>` header in requests

### MCP Operations

The sequential thinking server provides tools for structured reasoning:
- **Problem decomposition** - Break complex problems into steps
- **Thought progression** - Build logical sequences of reasoning
- **Alternative exploration** - Branch into different solution paths
- **Hypothesis generation** - Create and test solution approaches
- **Iterative refinement** - Improve understanding through revision

### Example Usage

```bash
# Using mcp-streamablehttp-client
mcp-streamablehttp-client --server-url https://sequentialthinking.yourdomain.com/mcp --command "think 'How can I optimize database performance?'"

# Raw protocol
mcp-streamablehttp-client --raw '{"method": "tools/call", "params": {"name": "sequential_thinking", "arguments": {"problem": "Complex software architecture decision"}}}'
```

## Testing

The service is tested via the comprehensive MCP test suite:
- Protocol compliance tests
- Tool execution tests  
- Authentication flow tests
- Error handling validation

Use the standard project testing commands:
```bash
just test  # Run all tests including mcp-sequentialthinking
```

## Sequential Thinking Capabilities

The service provides structured thinking tools for:

### Problem Analysis
- **Decomposition**: Break complex problems into smaller, manageable components
- **Pattern Recognition**: Identify recurring themes and structures
- **Constraint Identification**: Recognize limitations and boundaries

### Solution Development
- **Hypothesis Formation**: Generate potential solution approaches
- **Step-by-Step Planning**: Create detailed implementation sequences
- **Alternative Evaluation**: Compare different solution paths

### Iterative Improvement
- **Thought Revision**: Refine understanding based on new insights
- **Path Correction**: Adjust reasoning when assumptions prove incorrect
- **Depth Adjustment**: Scale analysis complexity based on problem needs

### Logical Flow
- **Sequential Dependencies**: Maintain logical connections between steps
- **Branch Management**: Handle multiple concurrent reasoning paths
- **Synthesis**: Combine insights from different reasoning branches

## Integration Benefits

- **AI Enhancement**: Improve AI reasoning with structured thought processes
- **Problem Solving**: Systematic approach to complex challenges
- **Decision Making**: Comprehensive analysis before conclusions
- **Documentation**: Clear trail of reasoning for audit and review
- **Collaboration**: Shareable thought processes for team analysis

## Troubleshooting

### Common Issues

1. **Thinking process not starting**: Check tool parameters and format
2. **Authentication failures**: Verify OAuth token validity  
3. **Service not responding**: Check container logs and health status

### Debugging

```bash
# Check service status
just logs mcp-sequentialthinking

# Test authentication
mcp-streamablehttp-client --server-url https://sequentialthinking.yourdomain.com/mcp --test-auth

# Health check
curl -X POST https://sequentialthinking.yourdomain.com/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"'"$MCP_PROTOCOL_VERSION"'","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'
```

## Use Cases

The sequential thinking service excels at:

### Software Development
- Architecture design decisions
- Algorithm optimization strategies
- Debugging complex issues
- Code review processes

### Business Analysis
- Strategic planning breakdown
- Process improvement analysis
- Risk assessment workflows
- Decision tree construction

### Research & Analysis
- Literature review structuring
- Hypothesis development
- Experimental design
- Data interpretation strategies

### Education & Training
- Curriculum development
- Learning objective decomposition
- Assessment strategy design
- Knowledge transfer planning

## Integration

The service integrates with:
- **Auth Service**: OAuth token validation
- **Traefik**: Reverse proxy and routing
- **Let's Encrypt**: Automatic HTTPS certificates
- **Other MCP Services**: Can be combined with memory, fetch, and other tools

## Performance Characteristics

- **Stateless Operation**: No persistent state between requests
- **Fast Processing**: Lightweight reasoning operations
- **Scalable**: Can handle multiple concurrent thinking sessions
- **Resource Efficient**: Minimal memory and storage requirements

The sequential thinking service provides a powerful tool for structured problem-solving and analysis, seamlessly integrated into the MCP OAuth gateway architecture.