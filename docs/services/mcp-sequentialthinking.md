# MCP Sequential Thinking Service

The MCP Sequential Thinking service provides structured problem-solving and reasoning workflows through the Model Context Protocol.

## Overview

MCP Sequential Thinking wraps the official `@modelcontextprotocol/server-sequential-thinking` implementation, enabling AI models to perform complex multi-step reasoning tasks via HTTP endpoints secured with OAuth 2.1 authentication.

## Features

### 🧠 Reasoning Workflows
- **Step-by-Step Analysis** - Break down complex problems
- **Hypothesis Testing** - Validate assumptions
- **Decision Trees** - Explore branching logic
- **Causal Reasoning** - Understand cause and effect

### 📊 Problem Structuring
- **Problem Decomposition** - Divide into sub-problems
- **Constraint Analysis** - Identify limitations
- **Goal Setting** - Define clear objectives
- **Solution Synthesis** - Combine partial solutions

### 🔄 Iterative Thinking
- **Refinement Loops** - Improve solutions iteratively
- **Backtracking** - Revise earlier decisions
- **Alternative Paths** - Explore multiple approaches
- **Convergence Testing** - Verify solution quality

### 📝 Documentation
- **Reasoning Traces** - Record thinking process
- **Decision Rationale** - Explain choices
- **Assumption Tracking** - Document premises
- **Conclusion Summary** - Synthesize findings

## Authentication

All requests require OAuth 2.1 Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     https://mcp-sequentialthinking.yourdomain.com/mcp
```

## Endpoints

### Primary Endpoints
- **`/mcp`** - Main MCP protocol endpoint
- **`/health`** - Health check endpoint (public)
- **`/.well-known/oauth-authorization-server`** - OAuth discovery

## Usage Examples

### Start a Reasoning Session

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "start_reasoning",
    "arguments": {
      "problem": "Design a distributed caching system",
      "constraints": [
        "Must handle 1M requests/second",
        "Sub-millisecond latency",
        "Fault tolerant"
      ],
      "approach": "systematic"
    }
  },
  "id": 1
}
```

### Add Reasoning Step

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "add_step",
    "arguments": {
      "session_id": "session-123",
      "step_type": "analysis",
      "content": "First, let's analyze the performance requirements...",
      "conclusions": [
        "Need distributed architecture",
        "Require in-memory storage"
      ]
    }
  },
  "id": 2
}
```

### Explore Alternative

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "explore_alternative",
    "arguments": {
      "session_id": "session-123",
      "branch_point": "step-3",
      "alternative": "Use write-through cache instead of write-back",
      "rationale": "Better consistency guarantees"
    }
  },
  "id": 3
}
```

## Available Tools

### Session Management
- `start_reasoning` - Begin reasoning session
- `resume_session` - Continue existing session
- `list_sessions` - Show active sessions
- `end_session` - Complete reasoning

### Reasoning Steps
- `add_step` - Add reasoning step
- `insert_step` - Insert between steps
- `revise_step` - Modify existing step
- `delete_step` - Remove step

### Problem Analysis
- `decompose_problem` - Break into parts
- `identify_constraints` - List limitations
- `define_goals` - Set objectives
- `analyze_dependencies` - Map relationships

### Solution Development
- `propose_solution` - Suggest approach
- `evaluate_solution` - Assess quality
- `compare_solutions` - Contrast options
- `refine_solution` - Improve approach

### Branching & Alternatives
- `create_branch` - Fork reasoning path
- `explore_alternative` - Try different approach
- `merge_branches` - Combine insights
- `select_branch` - Choose best path

### Documentation
- `summarize_reasoning` - Create summary
- `export_trace` - Export full trace
- `get_conclusions` - List findings
- `generate_report` - Create report

## Configuration

### Environment Variables

```bash
# From .env file
MCP_PROTOCOL_VERSION=2025-06-18
BASE_DOMAIN=yourdomain.com

# Sequential thinking specific
THINKING_MAX_DEPTH=10
THINKING_TIMEOUT=300000
```

### Docker Labels

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.mcp-sequentialthinking.rule=Host(`mcp-sequentialthinking.${BASE_DOMAIN}`)"
  - "traefik.http.routers.mcp-sequentialthinking.middlewares=mcp-auth@docker"
```

## Testing

### Integration Test
```bash
just test-file tests/test_mcp_sequentialthinking_integration.py
```

### Comprehensive Test
```bash
just test-file tests/test_mcp_sequentialthinking_comprehensive.py
```

### Functionality Test
```bash
just test-file tests/test_mcp_sequentialthinking_functionality_summary.py
```

### Manual Testing
```bash
# List available tools
mcp-streamablehttp-client query https://mcp-sequentialthinking.yourdomain.com/mcp \
  --token YOUR_TOKEN \
  '{"method": "tools/list"}'

# Start reasoning
mcp-streamablehttp-client query https://mcp-sequentialthinking.yourdomain.com/mcp \
  --token YOUR_TOKEN \
  '{"method": "tools/call", "params": {"name": "start_reasoning", "arguments": {"problem": "How to optimize database queries?"}}}'
```

## Error Handling

### Common Errors

1. **Session Not Found**
   ```json
   {
     "error": {
       "code": -32602,
       "message": "Session 'invalid-id' not found"
     }
   }
   ```

2. **Circular Reasoning**
   ```json
   {
     "error": {
       "code": -32603,
       "message": "Circular dependency detected in reasoning chain"
     }
   }
   ```

3. **Depth Limit Exceeded**
   ```json
   {
     "error": {
       "code": -32603,
       "message": "Maximum reasoning depth (10) exceeded"
     }
   }
   ```

## Best Practices

### Problem Definition
- Start with clear problem statements
- Identify all constraints upfront
- Define measurable success criteria
- Break complex problems into parts

### Reasoning Process
- Document assumptions explicitly
- Test hypotheses systematically
- Consider multiple alternatives
- Validate conclusions

### Session Management
- Use meaningful session IDs
- Save progress regularly
- Clean up completed sessions
- Export important traces

### Quality Control
- Review reasoning chains
- Check for logical consistency
- Validate against constraints
- Seek convergence

## Advanced Usage

### Multi-Phase Reasoning
```json
{
  "method": "tools/call",
  "params": {
    "name": "start_reasoning",
    "arguments": {
      "problem": "Design a recommendation system",
      "phases": [
        "requirements_analysis",
        "architecture_design",
        "algorithm_selection",
        "implementation_planning"
      ]
    }
  }
}
```

### Constraint Satisfaction
```json
{
  "method": "tools/call",
  "params": {
    "name": "add_step",
    "arguments": {
      "step_type": "constraint_check",
      "constraints": {
        "performance": "< 100ms response time",
        "accuracy": "> 95% precision",
        "scalability": "10M users"
      }
    }
  }
}
```

### Decision Matrix
```json
{
  "method": "tools/call",
  "params": {
    "name": "evaluate_solution",
    "arguments": {
      "criteria": {
        "performance": {"weight": 0.3, "score": 8},
        "cost": {"weight": 0.2, "score": 6},
        "complexity": {"weight": 0.2, "score": 7},
        "maintainability": {"weight": 0.3, "score": 9}
      }
    }
  }
}
```

## Use Cases

### Software Architecture
- System design decisions
- Technology selection
- Performance optimization
- Scalability planning

### Problem Solving
- Root cause analysis
- Debugging complex issues
- Algorithm development
- Process improvement

### Decision Making
- Trade-off analysis
- Risk assessment
- Option evaluation
- Strategy formulation

### Research & Analysis
- Literature review synthesis
- Hypothesis formulation
- Experimental design
- Results interpretation

## Troubleshooting

### Service Issues
```bash
# Check container status
docker ps | grep mcp-sequentialthinking

# View logs
docker logs mcp-sequentialthinking

# Test health endpoint
curl https://mcp-sequentialthinking.yourdomain.com/health
```

### Session Problems
```bash
# List active sessions
curl -X POST https://mcp-sequentialthinking.yourdomain.com/mcp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"method": "tools/call", "params": {"name": "list_sessions"}}'

# Export session trace
curl -X POST https://mcp-sequentialthinking.yourdomain.com/mcp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"method": "tools/call", "params": {"name": "export_trace", "arguments": {"session_id": "session-123"}}}'
```

## Performance Considerations

- **Session Limits** - Maximum 100 concurrent sessions
- **Step Depth** - Default limit of 10 levels
- **Memory Usage** - ~10MB per active session
- **Processing Time** - Complex reasoning may take minutes
- **Storage** - Session data persisted for 24 hours

## Related Documentation

- {doc}`../integration/index` - Integration guides
- {doc}`../architecture/mcp-protocol` - Protocol details
- {doc}`../development/adding-services` - Development guide