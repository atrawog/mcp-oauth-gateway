# mcp-playwright Service

A browser automation service that wraps `mcp-server-playwright` using the proxy pattern.

## Overview

The `mcp-playwright` service provides browser automation capabilities through the MCP protocol. It uses `mcp-streamablehttp-proxy` to wrap the stdio-based Playwright server, making it accessible via HTTP with OAuth authentication. This service enables automated web browser control, testing, and scraping.

## Architecture

```
┌─────────────────────────────────────────┐
│       mcp-playwright Container          │
├─────────────────────────────────────────┤
│   mcp-streamablehttp-proxy (Port 3000)  │
│              ↓ spawns ↓                 │
│       mcp-server-playwright             │
│         (stdio subprocess)              │
│              ↓ controls ↓               │
│    Playwright Browser Instances         │
│   (Chromium, Firefox, WebKit)           │
└─────────────────────────────────────────┘
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_FILE` | Log file path | `/logs/server.log` |
| `MCP_CORS_ORIGINS` | Allowed CORS origins | `*` |
| `MCP_PROTOCOL_VERSION` | MCP protocol version | `2025-06-18` (configurable) |
| `PLAYWRIGHT_BROWSERS_PATH` | Browser binaries location | Set by container |
| `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD` | Skip browser download | Set by container |

### Browser Management

The service container includes pre-installed browser binaries:
- Chromium
- Firefox
- WebKit (Safari engine)

## Available Tools

The mcp-playwright service provides browser automation tools through the wrapped server:

### navigate

Navigate to a URL in the browser.

**Parameters:**
- `url` (string, required): The URL to navigate to
- `browser` (string, optional): Browser type ("chromium", "firefox", "webkit")
- `wait_until` (string, optional): Wait condition ("load", "domcontentloaded", "networkidle")

### screenshot

Capture a screenshot of the current page.

**Parameters:**
- `path` (string, optional): Save screenshot to file
- `full_page` (boolean, optional): Capture full page (default: false)
- `type` (string, optional): Image format ("png", "jpeg")
- `quality` (number, optional): JPEG quality (0-100)

### click

Click an element on the page.

**Parameters:**
- `selector` (string, required): CSS selector or text
- `button` (string, optional): Mouse button ("left", "right", "middle")
- `click_count` (number, optional): Number of clicks

### fill

Fill a form field with text.

**Parameters:**
- `selector` (string, required): CSS selector for the input
- `value` (string, required): Text to fill

### evaluate

Execute JavaScript in the page context.

**Parameters:**
- `expression` (string, required): JavaScript code to execute
- `args` (array, optional): Arguments to pass to the function

### wait_for_selector

Wait for an element to appear.

**Parameters:**
- `selector` (string, required): CSS selector to wait for
- `timeout` (number, optional): Maximum wait time in milliseconds
- `state` (string, optional): Wait for state ("attached", "detached", "visible", "hidden")

## Usage Examples

### Basic Navigation and Screenshot

```bash
# Navigate to a page
curl -X POST https://mcp-playwright.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "navigate",
      "arguments": {
        "url": "https://example.com",
        "wait_until": "networkidle"
      }
    },
    "id": 1
  }'

# Take a screenshot
curl -X POST https://mcp-playwright.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "screenshot",
      "arguments": {
        "full_page": true,
        "type": "png"
      }
    },
    "id": 2
  }'
```

### Form Automation

```bash
# Fill a login form
curl -X POST https://mcp-playwright.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "fill",
      "arguments": {
        "selector": "#username",
        "value": "testuser@example.com"
      }
    },
    "id": 3
  }'

# Click submit button
curl -X POST https://mcp-playwright.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "click",
      "arguments": {
        "selector": "button[type=\"submit\"]"
      }
    },
    "id": 4
  }'
```

### Web Scraping

```bash
# Execute JavaScript to extract data
curl -X POST https://mcp-playwright.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "evaluate",
      "arguments": {
        "expression": "Array.from(document.querySelectorAll(\"h2\")).map(h => h.textContent)"
      }
    },
    "id": 5
  }'
```

## Browser Session Management

### Session Lifecycle

1. **Session Creation**: First tool call creates a browser instance
2. **Session Persistence**: Browser remains open between calls
3. **Session Timeout**: Inactive sessions close after timeout
4. **Session ID**: Track sessions with `Mcp-Session-Id` header

### Multi-Browser Support

```bash
# Use specific browser
curl -X POST https://mcp-playwright.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "navigate",
      "arguments": {
        "url": "https://example.com",
        "browser": "firefox"
      }
    },
    "id": 1
  }'
```

## Advanced Usage

### Waiting Strategies

```bash
# Wait for specific element
curl -X POST https://mcp-playwright.example.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "wait_for_selector",
      "arguments": {
        "selector": ".dynamic-content",
        "timeout": 30000,
        "state": "visible"
      }
    },
    "id": 1
  }'
```

### Complex Interactions

```python
import httpx
import asyncio

class PlaywrightAutomation:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.session_id = None

    async def execute_tool(self, tool_name, arguments):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    },
                    "id": 1
                }
            )

            # Save session ID from response
            if "Mcp-Session-Id" in response.headers:
                self.session_id = response.headers["Mcp-Session-Id"]

            return response.json()

    async def automate_form_submission(self, url, form_data):
        # Navigate to page
        await self.execute_tool("navigate", {"url": url})

        # Fill form fields
        for selector, value in form_data.items():
            await self.execute_tool("fill", {
                "selector": selector,
                "value": value
            })

        # Submit form
        await self.execute_tool("click", {
            "selector": "button[type='submit']"
        })

        # Wait for result
        await self.execute_tool("wait_for_selector", {
            "selector": ".success-message",
            "timeout": 10000
        })

# Usage
automation = PlaywrightAutomation(
    "https://mcp-playwright.example.com",
    "your_token"
)

await automation.automate_form_submission(
    "https://example.com/contact",
    {
        "#name": "John Doe",
        "#email": "john@example.com",
        "#message": "Hello from automation!"
    }
)
```

## Health Monitoring

### Health Check

The service uses StreamableHTTP protocol initialization for health checks:

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -s -X POST http://localhost:3000/mcp \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"${MCP_PROTOCOL_VERSION:-2025-06-18}\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"1.0\"}},\"id\":1}' \
    | grep -q '\"protocolVersion\":\"'"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

### Resource Monitoring

```bash
# Monitor browser processes
docker exec mcp-playwright ps aux | grep -E "(chromium|firefox|webkit)"

# Check memory usage
docker stats mcp-playwright

# View logs
just logs mcp-playwright
```

## Performance Optimization

### Browser Resource Management

1. **Session Limits**: Configure maximum concurrent browser sessions
2. **Memory Limits**: Set container memory limits appropriately
3. **Timeout Configuration**: Set reasonable timeouts for operations

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

### Best Practices

1. **Reuse Sessions**: Use session IDs to reuse browser instances
2. **Clean Up**: Close browsers when done with automation
3. **Error Handling**: Implement retry logic for flaky operations
4. **Headless Mode**: Use headless browsers for better performance

## Troubleshooting

### Browser Launch Failures

1. Check browser installation:
   ```bash
   docker exec mcp-playwright playwright install --list
   ```

2. Verify browser binaries:
   ```bash
   docker exec mcp-playwright ls -la $PLAYWRIGHT_BROWSERS_PATH
   ```

### Navigation Timeouts

1. Increase timeout values:
   ```json
   {
     "name": "navigate",
     "arguments": {
       "url": "https://slow-site.com",
       "timeout": 60000
     }
   }
   ```

2. Use appropriate wait conditions:
   - "load" - Wait for load event
   - "domcontentloaded" - Wait for DOM ready
   - "networkidle" - Wait for network to be idle

### Screenshot Issues

1. Check disk space:
   ```bash
   docker exec mcp-playwright df -h
   ```

2. Verify screenshot permissions:
   ```bash
   docker exec mcp-playwright touch /tmp/test.png
   ```

## Security Considerations

### URL Filtering

Consider implementing URL allowlists/blocklists:

```bash
# Environment variable for allowed domains
PLAYWRIGHT_ALLOWED_DOMAINS=example.com,test.com
```

### Resource Limits

Prevent resource exhaustion:
- Limit concurrent browser sessions
- Set maximum page load sizes
- Implement operation timeouts

### Data Privacy

- Screenshots may contain sensitive data
- JavaScript execution has full page access
- Consider data retention policies

## Integration

### With Claude Desktop

Configure in Claude Desktop settings:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--server-url", "https://mcp-playwright.example.com/mcp",
        "--token", "Bearer YOUR_TOKEN_HERE"
      ]
    }
  }
}
```

### With Testing Frameworks

```python
import pytest
import httpx

class MCPPlaywrightTester:
    def __init__(self, base_url, token):
        self.client = httpx.AsyncClient()
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def test_page_title(self, url, expected_title):
        # Navigate to page
        await self.client.post(
            f"{self.base_url}/mcp",
            headers=self.headers,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "navigate",
                    "arguments": {"url": url}
                },
                "id": 1
            }
        )

        # Get page title
        response = await self.client.post(
            f"{self.base_url}/mcp",
            headers=self.headers,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "evaluate",
                    "arguments": {
                        "expression": "document.title"
                    }
                },
                "id": 2
            }
        )

        result = response.json()
        assert result["result"]["content"] == expected_title
```
