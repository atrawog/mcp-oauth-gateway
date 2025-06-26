# MCP Playwright Service

**Sacred MCP service providing browser automation capabilities through OAuth 2.1 protected endpoints.**

## Service Overview

The MCP Playwright service enables secure browser automation through the Model Context Protocol. Built on Microsoft's `@playwright/mcp` package, it provides comprehensive web browser interaction capabilities including page navigation, element interaction, screenshot capture, and automated testing workflows.

## Playwright Capabilities

### Core Browser Tools

#### Page Navigation
- **`navigate`**: Navigate to specified URLs with full page loading
- **`reload`**: Refresh current page content
- **`go_back`**: Navigate to previous page in history
- **`go_forward`**: Navigate to next page in history
- **`wait_for_selector`**: Wait for specific elements to appear
- **`wait_for_navigation`**: Wait for page navigation events

#### Element Interaction
- **`click`**: Click on elements using selectors or coordinates
- **`type`**: Type text into input fields and text areas
- **`fill`**: Fill form fields with specified values
- **`check`**: Check checkboxes and radio buttons
- **`uncheck`**: Uncheck checkboxes
- **`select_option`**: Select options from dropdown menus
- **`hover`**: Hover over elements to trigger hover states

#### Content Extraction
- **`get_text`**: Extract text content from elements
- **`get_attribute`**: Get attribute values from elements
- **`get_property`**: Get JavaScript property values
- **`evaluate`**: Execute JavaScript in the page context
- **`get_page_content`**: Get complete HTML content
- **`get_page_title`**: Extract page title

#### Media Capture
- **`screenshot`**: Capture full page or element screenshots
- **`pdf`**: Generate PDF documents from pages
- **`record_video`**: Record browser interactions as video

#### File Operations
- **`upload_file`**: Upload files through file input elements
- **`download`**: Handle file downloads and capture content

### Browser Configuration

#### Supported Browsers
- **Chromium**: Default headless browser for fast automation
- **Firefox**: Alternative browser for cross-browser testing
- **WebKit**: Safari-like browser for compatibility testing
- **Microsoft Edge**: Chromium-based browser with Edge features

#### Execution Modes
- **Headless Mode**: Background browser execution (default)
- **Headed Mode**: Visible browser for debugging and development
- **Snapshot Mode**: Accessibility-focused interaction using page snapshots
- **Vision Mode**: Screenshot-based visual interaction

#### Profile Management
- **Persistent Profiles**: Maintain browser state across sessions
- **Isolated Profiles**: Clean browser state for each session
- **Custom User Data**: Configure browser with specific settings

### Resources Provided

#### Page Resources
- **`browser://page/{pageId}`**: Current page state and metadata
- **`browser://page/{pageId}/screenshot`**: Live page screenshots
- **`browser://page/{pageId}/content`**: HTML content and DOM structure
- **`browser://page/{pageId}/console`**: Browser console messages
- **`browser://page/{pageId}/network`**: Network requests and responses

#### Element Resources
- **`browser://element/{selector}`**: Element properties and state
- **`browser://element/{selector}/screenshot`**: Element-specific screenshots
- **`browser://form/{formId}`**: Form data and validation state

#### Session Resources
- **`browser://session/{sessionId}`**: Browser session information
- **`browser://session/{sessionId}/cookies`**: Session cookies and storage
- **`browser://session/{sessionId}/history`**: Navigation history

## Service Architecture

### Node.js Implementation
- **Runtime**: Node.js 18+ Alpine container with browser dependencies
- **MCP Server**: `@playwright/mcp` npm package
- **HTTP Bridge**: `mcp-streamablehttp-proxy` for HTTP transport
- **Browsers**: Pre-installed Chromium, Firefox, and WebKit

### Container Features
- **Browser Installation**: Pre-configured Playwright browsers
- **Shared Memory**: 2GB shared memory for browser processes
- **Health Monitoring**: MCP protocol health checks via initialization
- **Process Management**: Automatic browser cleanup and resource management
- **Font Support**: Liberation fonts and emoji support for rendering

### Performance Optimizations
- **Browser Caching**: Persistent browser binaries
- **Parallel Execution**: Multiple browser contexts for concurrent operations
- **Resource Limits**: Configured memory and CPU limits for stability
- **Connection Pooling**: Efficient browser instance management

## OAuth Integration

### Authentication Flow
1. **Service Discovery**: `/.well-known/oauth-authorization-server` routed to auth service
2. **Client Registration**: Dynamic registration via RFC 7591
3. **User Authentication**: GitHub OAuth integration
4. **Token Validation**: ForwardAuth middleware validates Bearer tokens
5. **MCP Access**: Authenticated requests forwarded to Playwright service

### Endpoint Configuration
- **Primary**: `https://mcp-playwright.${BASE_DOMAIN}/mcp`
- **Health**: Uses MCP protocol initialization
- **Discovery**: `https://mcp-playwright.${BASE_DOMAIN}/.well-known/oauth-authorization-server`

## Usage Examples

### Page Navigation and Interaction
```javascript
// Navigate to a webpage
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "navigate",
    "arguments": {
      "url": "https://example.com"
    }
  }
}

// Click on an element
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "click",
    "arguments": {
      "selector": "button[type='submit']"
    }
  }
}

// Fill a form field
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "fill",
    "arguments": {
      "selector": "input[name='email']",
      "value": "user@example.com"
    }
  }
}
```

### Content Extraction
```javascript
// Get page title
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "get_page_title",
    "arguments": {}
  }
}

// Extract text content
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "get_text",
    "arguments": {
      "selector": "h1.main-title"
    }
  }
}

// Execute JavaScript
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "tools/call",
  "params": {
    "name": "evaluate",
    "arguments": {
      "expression": "document.querySelector('input[name=\"search\"]').value"
    }
  }
}
```

### Screenshot and Media Capture
```javascript
// Take a full page screenshot
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "screenshot",
    "arguments": {
      "fullPage": true,
      "path": "screenshot.png"
    }
  }
}

// Generate PDF
{
  "jsonrpc": "2.0",
  "id": 8,
  "method": "tools/call",
  "params": {
    "name": "pdf",
    "arguments": {
      "path": "page.pdf",
      "format": "A4"
    }
  }
}
```

### Resource Access
```javascript
// Get page resource
{
  "jsonrpc": "2.0",
  "id": 9,
  "method": "resources/read",
  "params": {
    "uri": "browser://page/current"
  }
}

// Get element screenshot
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "resources/read",
  "params": {
    "uri": "browser://element/button[type='submit']/screenshot"
  }
}
```

## Configuration Options

### Browser Selection
```bash
# Use Chromium (default)
CMD ["/app/start.sh"]

# Use Firefox
CMD ["/app/start.sh", "--browser", "firefox"]

# Use WebKit
CMD ["/app/start.sh", "--browser", "webkit"]

# Enable headed mode for debugging
CMD ["/app/start.sh", "--headed"]
```

### Environment Variables
- **`PORT`**: HTTP server port (default: 3000)
- **`MCP_PROTOCOL_VERSION`**: MCP protocol version (defaults to 2025-06-18 if not set)
- **`PLAYWRIGHT_BROWSERS_PATH`**: Browser installation path
- **`PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD`**: Skip browser downloads if already installed

### Advanced Configuration
```javascript
// Browser context options
{
  "viewport": { "width": 1920, "height": 1080 },
  "userAgent": "Mozilla/5.0 (custom user agent)",
  "locale": "en-US",
  "timezoneId": "America/New_York",
  "permissions": ["geolocation", "notifications"]
}
```

## Security Considerations

### Browser Isolation
- **Sandboxed Execution**: Browsers run in isolated container environment
- **Network Restrictions**: Limited network access and URL filtering
- **File System Isolation**: Restricted file system access
- **Resource Limits**: Memory and CPU limits prevent resource exhaustion

### Access Control
- **OAuth Protected**: All MCP endpoints require valid Bearer tokens
- **Session Isolation**: Each authenticated user gets isolated browser contexts
- **Content Security**: Automatic sanitization of malicious content
- **Download Restrictions**: Controlled file download capabilities

### Container Security
- **Minimal Base**: Alpine Linux with essential packages only
- **Non-Root User**: Browsers run with limited privileges
- **Network Isolation**: Isolated container networking
- **Health Monitoring**: Automatic health checks and restart policies

## Health Monitoring

### Health Check Endpoint
```bash
curl -X POST https://mcp-playwright.${BASE_DOMAIN}/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"'"$MCP_PROTOCOL_VERSION"'","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'
```

**Response**:
```
event: message
data: {"result":{"protocolVersion":"${MCP_PROTOCOL_VERSION}","capabilities":{...},"serverInfo":{...}},"jsonrpc":"2.0","id":1}
```

### Container Health
- **Interval**: 30-second health checks
- **Timeout**: 10-second response timeout
- **Retries**: 3 failed attempts before unhealthy
- **Start Period**: 60-second grace period for browser initialization

## Development and Testing

### Local Testing
```bash
# Build and start service
just rebuild mcp-playwright

# Check health
curl -X POST https://mcp-playwright.${BASE_DOMAIN}/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"'"$MCP_PROTOCOL_VERSION"'","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'

# Test with MCP client
just mcp-client-token
# Use token to test browser automation
```

### Integration with Claude Code
```json
{
  "mcpServers": {
    "playwright": {
      "command": "mcp-streamablehttp-client",
      "args": [
        "--url", "https://mcp-playwright.${BASE_DOMAIN}/mcp",
        "--oauth2"
      ],
      "env": {
        "MCP_PROTOCOL_VERSION": "${MCP_PROTOCOL_VERSION:-2025-06-18}"
      }
    }
  }
}
```

## Common Use Cases

### Web Scraping and Data Extraction
- **Content Mining**: Extract structured data from web pages
- **Price Monitoring**: Track product prices and availability
- **News Aggregation**: Collect articles and content from news sites
- **Social Media Monitoring**: Track social media posts and engagement

### Automated Testing
- **UI Testing**: Automated user interface testing workflows
- **Cross-Browser Testing**: Test across different browser engines
- **Performance Testing**: Measure page load times and performance
- **Visual Regression Testing**: Compare screenshots for visual changes

### AI Assistant Integration
- **Web Research**: AI can browse and extract information from websites
- **Form Automation**: AI can fill forms and submit data
- **Screenshot Analysis**: AI can analyze visual content of web pages
- **User Interface Testing**: AI can test web applications automatically

### Monitoring and Alerts
- **Website Monitoring**: Check website availability and functionality
- **Content Change Detection**: Monitor for changes in web content
- **Performance Monitoring**: Track website performance metrics
- **Error Detection**: Identify and report website errors

## Troubleshooting

### Common Issues

#### Browser Initialization Failures
```bash
# Check browser availability in container
docker exec mcp-oauth-gateway-mcp-playwright-1 npx playwright --version

# Reinstall browsers
docker exec mcp-oauth-gateway-mcp-playwright-1 npx playwright install
```

#### Memory Issues
```bash
# Check container memory usage
docker stats mcp-oauth-gateway-mcp-playwright-1

# Increase shared memory size in docker-compose.yml
shm_size: '4gb'
```

#### MCP Protocol Issues
```bash
# Test MCP endpoint directly
curl -X POST https://mcp-playwright.${BASE_DOMAIN}/mcp \
  -H "Authorization: Bearer $GATEWAY_OAUTH_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "MCP-Protocol-Version: ${MCP_PROTOCOL_VERSION:-2025-06-18}" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Browser Debugging
```bash
# Enable headed mode for visual debugging
# Modify docker-compose.yml environment:
- PLAYWRIGHT_HEADED=true

# View browser console logs
docker logs mcp-oauth-gateway-mcp-playwright-1
```

### Service Logs
```bash
# View Playwright service logs
docker logs mcp-oauth-gateway-mcp-playwright-1

# Follow logs in real-time
docker logs mcp-oauth-gateway-mcp-playwright-1 -f
```

## Sacred Compliance

### Holy Trinity Adherence
- **Traefik**: Routes OAuth and MCP requests with divine priority
- **Auth Service**: Validates tokens with blessed ForwardAuth middleware
- **MCP Service**: Provides pure browser automation functionality

### Testing Commandments
- **No Mocking**: Tests run against real browser instances
- **Real Systems**: Full Docker container integration testing
- **Coverage**: Comprehensive tool and resource testing

### Security Sanctity
- **OAuth 2.1**: Full RFC compliance with PKCE protection
- **JWT Validation**: RS256 signature verification
- **Zero Trust**: Every request validated and authorized

**⚡ This service follows all Sacred Commandments and provides secure, authenticated access to browser automation capabilities through Microsoft Playwright! ⚡**
