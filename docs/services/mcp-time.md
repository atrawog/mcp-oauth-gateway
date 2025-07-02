# mcp-time Service

A time and date service that wraps the official `mcp-server-time` using the proxy pattern.

## Overview

The `mcp-time` service provides time and date information capabilities through the MCP protocol. It uses `mcp-streamablehttp-proxy` to wrap the official Python-based time server, making it accessible via HTTP with OAuth authentication.

## Architecture

```
┌─────────────────────────────────────────┐
│          mcp-time Container             │
├─────────────────────────────────────────┤
│   mcp-streamablehttp-proxy (Port 3000)  │
│              ↓ spawns ↓                 │
│         mcp-server-time                 │
│         (stdio subprocess)              │
└─────────────────────────────────────────┘
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_FILE` | Log file path | `/logs/server.log` |
| `MCP_CORS_ORIGINS` | Allowed CORS origins | `*` |
| `MCP_PROTOCOL_VERSION` | MCP protocol version | `2025-03-26` |

## Available Tools

The mcp-time service provides time-related operations through the wrapped official server:

### get_current_time

Gets the current time in a specified timezone.

**Parameters:**
- `timezone` (string, optional): Timezone name (e.g., "America/New_York", "Europe/London", "Asia/Tokyo")

**Returns:**
- Current time in ISO 8601 format
- Timezone information
- UTC offset

### get_time_difference

Calculates the time difference between two timestamps or timezones.

**Parameters:**
- `time1` (string, required): First timestamp or timezone
- `time2` (string, required): Second timestamp or timezone

**Returns:**
- Time difference in various units (seconds, minutes, hours, days)

### convert_timezone

Converts a timestamp from one timezone to another.

**Parameters:**
- `timestamp` (string, required): The timestamp to convert
- `from_timezone` (string, required): Source timezone
- `to_timezone` (string, required): Target timezone

**Returns:**
- Converted timestamp in the target timezone

## Usage Examples

### Get Current Time

```bash
# Get current UTC time
curl -X POST https://mcp-time.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_current_time",
      "arguments": {}
    },
    "id": 1
  }'

# Get current time in specific timezone
curl -X POST https://mcp-time.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_current_time",
      "arguments": {
        "timezone": "America/New_York"
      }
    },
    "id": 2
  }'
```

### Calculate Time Difference

```bash
curl -X POST https://mcp-time.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_time_difference",
      "arguments": {
        "time1": "2024-01-15T10:00:00Z",
        "time2": "2024-01-15T15:30:00Z"
      }
    },
    "id": 3
  }'
```

### Convert Timezone

```bash
curl -X POST https://mcp-time.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "convert_timezone",
      "arguments": {
        "timestamp": "2024-01-15T10:00:00",
        "from_timezone": "America/New_York",
        "to_timezone": "Europe/London"
      }
    },
    "id": 4
  }'
```

## Common Timezone References

### Major Timezones

| Region | Timezone ID | UTC Offset |
|--------|-------------|------------|
| UTC | UTC | +00:00 |
| Eastern US | America/New_York | -05:00/-04:00 |
| Central US | America/Chicago | -06:00/-05:00 |
| Mountain US | America/Denver | -07:00/-06:00 |
| Pacific US | America/Los_Angeles | -08:00/-07:00 |
| UK | Europe/London | +00:00/+01:00 |
| Central Europe | Europe/Berlin | +01:00/+02:00 |
| Japan | Asia/Tokyo | +09:00 |
| Australia East | Australia/Sydney | +10:00/+11:00 |

### Timezone List

To get a complete list of supported timezones, you can query:

```bash
# This depends on the specific implementation of mcp-server-time
curl -X POST https://mcp-time.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "list_timezones",
      "arguments": {}
    },
    "id": 5
  }'
```

## Health Monitoring

### Health Check

The service uses StreamableHTTP protocol initialization for health checks:

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-03-26\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
    | grep -q '\"protocolVersion\":\"2025-03-26\"'"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

### Logs

```bash
# View logs
just logs mcp-time

# Follow logs
just logs -f mcp-time

# Check file logs
cat logs/mcp-time/server.log
```

## Integration Examples

### Scheduling Applications

```python
import httpx
from datetime import datetime

class TimeScheduler:
    def __init__(self, mcp_url, token):
        self.mcp_url = mcp_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def schedule_meeting(self, participants_timezones):
        """Find optimal meeting time across timezones"""
        async with httpx.AsyncClient() as client:
            times = {}

            # Get current time in each participant's timezone
            for tz in participants_timezones:
                response = await client.post(
                    f"{self.mcp_url}/mcp",
                    headers=self.headers,
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "get_current_time",
                            "arguments": {"timezone": tz}
                        },
                        "id": 1
                    }
                )
                times[tz] = response.json()

            return times
```

### Time-based Automation

```bash
#!/bin/bash
# Script to perform actions based on time

# Get current time in specific timezone
CURRENT_TIME=$(curl -s -X POST https://mcp-time.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_current_time",
      "arguments": {"timezone": "America/New_York"}
    },
    "id": 1
  }' | jq -r '.result.content')

# Parse hour from response
HOUR=$(echo $CURRENT_TIME | grep -oP '\d{2}(?=:\d{2}:\d{2})')

# Perform actions based on time
if [ $HOUR -ge 9 ] && [ $HOUR -lt 17 ]; then
    echo "Business hours - running production tasks"
else
    echo "After hours - running maintenance tasks"
fi
```

## Troubleshooting

### Timezone Not Found

1. Verify timezone ID is correct:
   ```bash
   # Common timezone format: Continent/City
   # Correct: America/New_York
   # Incorrect: EST, New York, US/Eastern
   ```

2. Use standard IANA timezone database names

### Time Conversion Errors

1. Ensure timestamp format is correct:
   ```bash
   # ISO 8601 format recommended
   # With timezone: 2024-01-15T10:00:00-05:00
   # UTC: 2024-01-15T15:00:00Z
   # Without timezone: 2024-01-15T10:00:00
   ```

2. Check for daylight saving time transitions

### Service Issues

1. Verify Python package is installed:
   ```bash
   docker exec mcp-time pip list | grep mcp-server-time
   ```

2. Check proxy logs:
   ```bash
   just logs mcp-time | grep ERROR
   ```

## Best Practices

### Timezone Handling

1. **Always use timezone-aware timestamps** when possible
2. **Store times in UTC** and convert for display
3. **Use IANA timezone names** (not abbreviations like EST/PST)
4. **Account for DST transitions** in scheduling logic

### Performance

1. **Cache timezone data** when making multiple conversions
2. **Batch time operations** when possible
3. **Use appropriate precision** (don't request microseconds if not needed)

## Integration

### With Claude Desktop

Configure in Claude Desktop settings:

```json
{
  "mcpServers": {
    "time": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--server-url", "https://mcp-time.example.com/mcp",
        "--token", "Bearer YOUR_TOKEN_HERE"
      ]
    }
  }
}
```

### With Python Clients

```python
import httpx
from datetime import datetime
import asyncio

class MCPTimeClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def get_current_time(self, timezone=None):
        async with httpx.AsyncClient() as client:
            args = {"timezone": timezone} if timezone else {}
            response = await client.post(
                f"{self.base_url}/mcp",
                headers=self.headers,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "get_current_time",
                        "arguments": args
                    },
                    "id": 1
                }
            )
            return response.json()

# Usage
async def main():
    client = MCPTimeClient("https://mcp-time.example.com", "your_token")

    # Get UTC time
    utc_time = await client.get_current_time()
    print(f"UTC: {utc_time}")

    # Get time in New York
    ny_time = await client.get_current_time("America/New_York")
    print(f"New York: {ny_time}")

asyncio.run(main())
```
