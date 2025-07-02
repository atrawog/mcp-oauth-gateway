# mcp-sequentialthinking Service

A sequential thinking and reasoning service that wraps `mcp-server-sequential-thinking` using the proxy pattern.

## Overview

The `mcp-sequentialthinking` service provides structured thinking and step-by-step reasoning capabilities through the MCP protocol. It uses `mcp-streamablehttp-proxy` to wrap the stdio-based sequential thinking server, making it accessible via HTTP with OAuth authentication. This service helps break down complex problems into manageable steps.

## Architecture

```
┌─────────────────────────────────────────┐
│   mcp-sequentialthinking Container      │
├─────────────────────────────────────────┤
│   mcp-streamablehttp-proxy (Port 3000)  │
│              ↓ spawns ↓                 │
│   mcp-server-sequential-thinking        │
│         (stdio subprocess)              │
└─────────────────────────────────────────┘
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_FILE` | Log file path | `/logs/server.log` |
| `MCP_CORS_ORIGINS` | Allowed CORS origins | `*` |
| `MCP_PROTOCOL_VERSION` | MCP protocol version | `2024-11-05` |

**Note**: This service uses an older protocol version (2024-11-05) for compatibility with the sequential thinking server.

## Available Tools

The mcp-sequentialthinking service provides tools for structured problem-solving:

### think_sequentially

Break down a problem into sequential steps and solve methodically.

**Parameters:**
- `problem` (string, required): The problem or question to analyze
- `max_steps` (integer, optional): Maximum number of thinking steps
- `depth` (integer, optional): Depth of analysis for each step

### analyze_step

Analyze a specific step in detail.

**Parameters:**
- `step` (string, required): The step to analyze
- `context` (string, optional): Previous steps or context
- `criteria` (array, optional): Specific criteria to evaluate

### synthesize_steps

Combine multiple steps into a coherent solution.

**Parameters:**
- `steps` (array, required): Array of steps to synthesize
- `goal` (string, optional): The overall goal to achieve

## Usage Examples

### Problem Decomposition

```bash
# Break down a complex problem
curl -X POST https://mcp-sequentialthinking.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "think_sequentially",
      "arguments": {
        "problem": "How to design a scalable microservices architecture?",
        "max_steps": 10,
        "depth": 3
      }
    },
    "id": 1
  }'
```

### Step Analysis

```bash
# Analyze a specific step
curl -X POST https://mcp-sequentialthinking.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "analyze_step",
      "arguments": {
        "step": "Choose appropriate communication patterns",
        "context": "Designing microservices architecture",
        "criteria": ["scalability", "reliability", "complexity"]
      }
    },
    "id": 2
  }'
```

### Solution Synthesis

```bash
# Synthesize steps into solution
curl -X POST https://mcp-sequentialthinking.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "synthesize_steps",
      "arguments": {
        "steps": [
          "Identify service boundaries",
          "Define communication protocols",
          "Implement service discovery",
          "Add monitoring and logging",
          "Design failure handling"
        ],
        "goal": "Create resilient microservices system"
      }
    },
    "id": 3
  }'
```

## Common Use Cases

### Software Architecture Planning

```python
import httpx
import json

class ArchitecturePlanner:
    def __init__(self, mcp_url, token):
        self.mcp_url = mcp_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def plan_system(self, requirements):
        """Plan system architecture step by step"""
        async with httpx.AsyncClient() as client:
            # First, break down the problem
            response = await client.post(
                f"{self.mcp_url}/mcp",
                headers=self.headers,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "think_sequentially",
                        "arguments": {
                            "problem": f"Design system with requirements: {requirements}",
                            "max_steps": 15
                        }
                    },
                    "id": 1
                }
            )

            steps = response.json()["result"]["content"]

            # Analyze critical steps
            critical_analyses = []
            for step in steps["critical_steps"]:
                analysis = await client.post(
                    f"{self.mcp_url}/mcp",
                    headers=self.headers,
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "analyze_step",
                            "arguments": {
                                "step": step,
                                "criteria": ["feasibility", "risk", "cost"]
                            }
                        },
                        "id": 2
                    }
                )
                critical_analyses.append(analysis.json())

            return {
                "steps": steps,
                "analyses": critical_analyses
            }
```

### Decision Making Framework

```bash
# Complex decision analysis
curl -X POST https://mcp-sequentialthinking.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "think_sequentially",
      "arguments": {
        "problem": "Should we migrate from monolith to microservices?",
        "max_steps": 8,
        "depth": 4
      }
    },
    "id": 1
  }'
```

### Problem Solving Pipeline

```python
class ProblemSolver:
    def __init__(self, mcp_client):
        self.client = mcp_client

    async def solve_problem(self, problem_statement):
        # Step 1: Decompose problem
        decomposition = await self.client.think_sequentially(
            problem=problem_statement,
            max_steps=10
        )

        # Step 2: Analyze each component
        analyses = []
        for component in decomposition["components"]:
            analysis = await self.client.analyze_step(
                step=component,
                context=problem_statement
            )
            analyses.append(analysis)

        # Step 3: Synthesize solution
        solution = await self.client.synthesize_steps(
            steps=[a["recommendation"] for a in analyses],
            goal=f"Solve: {problem_statement}"
        )

        return {
            "problem": problem_statement,
            "decomposition": decomposition,
            "analyses": analyses,
            "solution": solution
        }
```

## Health Monitoring

### Health Check

The service uses StreamableHTTP protocol initialization for health checks:

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
    | grep -q '\"protocolVersion\":\"2024-11-05\"'"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

### Monitoring

```bash
# View logs
just logs mcp-sequentialthinking

# Monitor thinking operations
just logs -f mcp-sequentialthinking | grep -E "(think|analyze|synthesize)"

# Check response times
just logs mcp-sequentialthinking | grep "duration"
```

## Best Practices

### Problem Formulation

1. **Clear Problem Statements**: Provide specific, well-defined problems
2. **Context Inclusion**: Include relevant background information
3. **Constraint Specification**: Mention any limitations or requirements

### Step Configuration

1. **Appropriate Step Count**:
   - Simple problems: 3-5 steps
   - Medium complexity: 5-10 steps
   - Complex problems: 10-15 steps

2. **Depth Settings**:
   - Level 1: High-level overview
   - Level 2: Moderate detail
   - Level 3-4: Deep analysis

### Performance Optimization

1. **Caching Results**: Cache analysis for repeated problems
2. **Batch Processing**: Analyze multiple related problems together
3. **Progressive Refinement**: Start with shallow analysis, then deepen

## Common Patterns

### Iterative Refinement

```python
async def refine_solution(initial_problem, iterations=3):
    current_solution = None

    for i in range(iterations):
        # Think about the problem
        result = await think_sequentially(
            problem=initial_problem if i == 0 else f"Improve: {current_solution}",
            max_steps=5 + i  # Increase steps each iteration
        )

        # Extract and refine
        current_solution = result["solution"]

        # Analyze quality
        quality = await analyze_step(
            step=current_solution,
            criteria=["completeness", "feasibility", "efficiency"]
        )

        if quality["score"] > 0.9:
            break

    return current_solution
```

### Comparative Analysis

```bash
# Compare multiple approaches
curl -X POST https://mcp-sequentialthinking.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "think_sequentially",
      "arguments": {
        "problem": "Compare REST vs GraphQL vs gRPC for our API",
        "max_steps": 12,
        "depth": 3
      }
    },
    "id": 1
  }'
```

## Troubleshooting

### Timeout Issues

1. Increase timeout for complex problems:
   ```python
   client = httpx.AsyncClient(timeout=300)  # 5 minutes
   ```

2. Break down very complex problems:
   ```python
   # Instead of one large problem
   subproblems = split_problem(large_problem)
   results = [await think_sequentially(sub) for sub in subproblems]
   final = await synthesize_steps(results)
   ```

### Protocol Version Mismatch

This service uses protocol version 2024-11-05. Ensure compatibility:

```bash
# Check server protocol version
docker exec mcp-sequentialthinking \
  mcp-server-sequential-thinking --version
```

### Memory Issues

For very deep analysis:

1. Limit depth parameter
2. Reduce max_steps
3. Process in smaller chunks

## Integration

### With Claude Desktop

Configure in Claude Desktop settings:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--server-url", "https://mcp-sequentialthinking.example.com/mcp",
        "--token", "Bearer YOUR_TOKEN_HERE"
      ]
    }
  }
}
```

### With Decision Support Systems

```python
class DecisionEngine:
    def __init__(self, mcp_url, token):
        self.thinking_service = MCPSequentialThinking(mcp_url, token)

    async def make_decision(self, decision_context):
        # Analyze the decision
        analysis = await self.thinking_service.think_sequentially(
            problem=f"Decide: {decision_context['question']}",
            max_steps=10
        )

        # Evaluate options
        option_analyses = []
        for option in decision_context['options']:
            evaluation = await self.thinking_service.analyze_step(
                step=f"Choose {option}",
                context=decision_context['question'],
                criteria=decision_context.get('criteria', [])
            )
            option_analyses.append({
                'option': option,
                'evaluation': evaluation
            })

        # Synthesize recommendation
        recommendation = await self.thinking_service.synthesize_steps(
            steps=[a['evaluation']['summary'] for a in option_analyses],
            goal="Make optimal decision"
        )

        return {
            'analysis': analysis,
            'evaluations': option_analyses,
            'recommendation': recommendation
        }
```
