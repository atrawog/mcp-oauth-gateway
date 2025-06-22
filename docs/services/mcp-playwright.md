# MCP Playwright Service

The MCP Playwright service provides browser automation and web testing capabilities through the Model Context Protocol.

## Overview

MCP Playwright wraps the official `@modelcontextprotocol/server-playwright` implementation, enabling programmatic control of web browsers via HTTP endpoints secured with OAuth 2.1 authentication.

## Features

### 🌐 Browser Control
- **Launch Browsers** - Start Chrome, Firefox, Safari, or WebKit
- **Headless Mode** - Run browsers without UI
- **Multiple Contexts** - Isolated browser sessions
- **Device Emulation** - Mobile and tablet simulation

### 📄 Page Management
- **Navigate URLs** - Load web pages
- **Wait Strategies** - Smart waiting for elements
- **Page Events** - Monitor page lifecycle
- **Multiple Pages** - Handle tabs and windows

### 🎯 Element Interaction
- **Click Elements** - Buttons, links, inputs
- **Type Text** - Fill forms and inputs
- **Select Options** - Dropdowns and checkboxes
- **Hover & Focus** - Mouse interactions

### 📸 Content Capture
- **Screenshots** - Full page or element
- **PDF Generation** - Save pages as PDF
- **HTML Content** - Extract page source
- **Text Extraction** - Get visible text

### 🧪 Testing Features
- **Assertions** - Verify page state
- **Network Interception** - Mock API responses
- **Console Monitoring** - Capture console logs
- **Error Handling** - Catch page errors

## Authentication

All requests require OAuth 2.1 Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     https://mcp-playwright.yourdomain.com/mcp
```

## Endpoints

### Primary Endpoints
- **`/mcp`** - Main MCP protocol endpoint
- **`/health`** - Health check endpoint (public)
- **`/.well-known/oauth-authorization-server`** - OAuth discovery

## Usage Examples

### Launch Browser and Navigate

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "launch_browser",
    "arguments": {
      "browser": "chromium",
      "headless": true
    }
  },
  "id": 1
}
```

### Take Screenshot

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "screenshot",
    "arguments": {
      "url": "https://example.com",
      "full_page": true,
      "path": "screenshot.png"
    }
  },
  "id": 2
}
```

### Fill and Submit Form

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fill_form",
    "arguments": {
      "url": "https://example.com/login",
      "selectors": {
        "username": "#username",
        "password": "#password"
      },
      "values": {
        "username": "user@example.com",
        "password": "secure_password"
      },
      "submit": "#submit-button"
    }
  },
  "id": 3
}
```

## Available Tools

### Browser Management
- `launch_browser` - Start a browser instance
- `close_browser` - Terminate browser
- `list_browsers` - Show active browsers
- `new_context` - Create isolated context

### Navigation
- `navigate` - Go to URL
- `go_back` - Navigate back
- `go_forward` - Navigate forward
- `reload` - Refresh page
- `wait_for_navigation` - Wait for page load

### Element Interaction
- `click` - Click element
- `type` - Type text
- `fill` - Fill input field
- `select` - Choose option
- `check` - Check checkbox
- `uncheck` - Uncheck checkbox
- `hover` - Hover over element
- `focus` - Focus element

### Content Operations
- `screenshot` - Capture screenshot
- `pdf` - Generate PDF
- `get_content` - Get HTML content
- `get_text` - Extract text
- `get_attribute` - Get element attribute
- `get_url` - Get current URL
- `get_title` - Get page title

### Waiting & Assertions
- `wait_for_selector` - Wait for element
- `wait_for_load_state` - Wait for page state
- `assert_visible` - Check visibility
- `assert_text` - Verify text content
- `assert_url` - Check URL

### Advanced Features
- `evaluate` - Run JavaScript
- `add_script_tag` - Inject script
- `intercept_network` - Mock requests
- `get_console_logs` - Capture console
- `emulate_device` - Mobile emulation

## Configuration

### Environment Variables

```bash
# From .env file
MCP_PROTOCOL_VERSION=2025-06-18
BASE_DOMAIN=yourdomain.com

# Playwright specific
PLAYWRIGHT_BROWSERS_PATH=/browsers
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0
```

### Docker Labels

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.mcp-playwright.rule=Host(`mcp-playwright.${BASE_DOMAIN}`)"
  - "traefik.http.routers.mcp-playwright.middlewares=mcp-auth@docker"
```

## Testing

### Integration Test
```bash
just test-file tests/test_mcp_playwright_integration.py
```

### Manual Testing
```bash
# List available tools
mcp-streamablehttp-client query https://mcp-playwright.yourdomain.com/mcp \
  --token YOUR_TOKEN \
  '{"method": "tools/list"}'

# Take screenshot
mcp-streamablehttp-client query https://mcp-playwright.yourdomain.com/mcp \
  --token YOUR_TOKEN \
  '{"method": "tools/call", "params": {"name": "screenshot", "arguments": {"url": "https://example.com"}}}'
```

## Error Handling

### Common Errors

1. **Element Not Found**
   ```json
   {
     "error": {
       "code": -32602,
       "message": "No element matches selector '#missing'"
     }
   }
   ```

2. **Navigation Timeout**
   ```json
   {
     "error": {
       "code": -32603,
       "message": "Navigation timeout of 30000ms exceeded"
     }
   }
   ```

3. **Browser Launch Failed**
   ```json
   {
     "error": {
       "code": -32603,
       "message": "Failed to launch browser: executable not found"
     }
   }
   ```

## Best Practices

### Resource Management
- Close browsers when done
- Limit concurrent browsers
- Use contexts for isolation
- Set appropriate timeouts

### Performance
- Use headless mode for speed
- Disable images when not needed
- Reuse browser contexts
- Batch operations when possible

### Reliability
- Use explicit waits
- Handle navigation errors
- Implement retry logic
- Clean up resources

### Security
- Never store credentials in code
- Validate URLs before navigation
- Use secure contexts
- Limit JavaScript execution

## Troubleshooting

### Service Not Starting
```bash
# Check container status
docker ps | grep mcp-playwright

# View logs
docker logs mcp-playwright

# Test health endpoint
curl https://mcp-playwright.yourdomain.com/health
```

### Browser Issues
```bash
# Check browser installation
docker exec mcp-playwright npx playwright install-deps

# List installed browsers
docker exec mcp-playwright npx playwright --version
```

### Screenshot/PDF Issues
```bash
# Check file permissions
docker exec mcp-playwright ls -la /tmp

# Test with simple page
curl -X POST https://mcp-playwright.yourdomain.com/mcp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"method": "tools/call", "params": {"name": "screenshot", "arguments": {"url": "about:blank"}}}'
```

## Performance Considerations

- **Browser Instances** - Limit to 3-5 concurrent browsers
- **Page Contexts** - Use contexts instead of new browsers
- **Timeouts** - Set reasonable timeouts (30s default)
- **Memory Usage** - Monitor container memory
- **Network Traffic** - Consider bandwidth usage

## Advanced Usage

### Device Emulation
```json
{
  "method": "tools/call",
  "params": {
    "name": "emulate_device",
    "arguments": {
      "device": "iPhone 12",
      "user_agent": "custom-agent"
    }
  }
}
```

### Network Interception
```json
{
  "method": "tools/call",
  "params": {
    "name": "intercept_network",
    "arguments": {
      "url_pattern": "**/api/*",
      "response": {
        "status": 200,
        "body": {"mocked": true}
      }
    }
  }
}
```

### JavaScript Execution
```json
{
  "method": "tools/call",
  "params": {
    "name": "evaluate",
    "arguments": {
      "expression": "document.querySelector('h1').textContent"
    }
  }
}
```

## Related Documentation

- {doc}`../integration/index` - Integration guides
- {doc}`../architecture/mcp-protocol` - Protocol details
- {doc}`../development/adding-services` - Development guide