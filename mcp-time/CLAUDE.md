# MCP Time Service

This service provides the official MCP Time server from the modelcontextprotocol/servers repository, wrapped for OAuth authentication and HTTP transport.

## Overview

The MCP Time server provides essential time-related functionality for AI systems and applications. It enables accurate time queries, timezone conversions, and temporal calculations across global timezones using IANA timezone standards.

## Features

- 🕒 **Current Time Queries**: Get current time in any timezone with IANA timezone support
- 🌍 **Timezone Conversion**: Convert times between different global timezones
- 🔍 **Automatic Detection**: System timezone detection for local time operations
- ⏰ **Daylight Saving**: Automatic DST handling and status reporting
- 📅 **24-Hour Format**: Precise time handling in standard 24-hour format
- 🏷️ **IANA Standards**: Full support for IANA timezone database

## Architecture

This service follows the project's standard MCP service pattern:
- **Base**: Official `@modelcontextprotocol/server-time` npm package
- **Transport**: mcp-streamablehttp-proxy wrapping stdio to HTTP
- **Authentication**: OAuth 2.1 via Traefik ForwardAuth
- **Isolation**: Stateless operation with no persistent storage needed
- **Health Monitoring**: MCP protocol health checks via initialization

## Configuration

### Environment Variables

- `MCP_PROTOCOL_VERSION=2025-03-26` - MCP protocol version (hardcoded - the time server only supports this version)
- `MCP_CORS_ORIGINS=*` - CORS configuration
- `PORT=3000` - Service port

### No Persistent Storage

The time service is stateless and processes each request independently. No volumes are required as all time data comes from system clock and timezone databases.

## Endpoints

- **Primary**: `https://time.${BASE_DOMAIN}/mcp`
- **Health Check**: Uses MCP protocol initialization
- **OAuth Discovery**: `https://time.${BASE_DOMAIN}/.well-known/oauth-authorization-server`

## Usage

### Authentication

The service requires OAuth authentication via the gateway:
1. Register OAuth client via `/register` endpoint
2. Obtain access token through OAuth flow
3. Include `Authorization: Bearer <token>` header in requests

### MCP Tools

The time server provides two primary tools:

#### 1. get_current_time
Get the current time in a specified timezone.

**Parameters:**
- `timezone` (string): IANA timezone name (e.g., "America/New_York", "Europe/London", "Asia/Tokyo")

**Returns:**
- Current datetime in the specified timezone
- Timezone information
- Daylight saving time status

#### 2. convert_time
Convert time between different timezones.

**Parameters:**
- `source_timezone` (string): Source IANA timezone name
- `time` (string): Time in 24-hour format (HH:MM or HH:MM:SS)
- `target_timezone` (string): Target IANA timezone name

**Returns:**
- Source datetime details
- Target datetime details
- Time difference between zones

### Example Usage

```bash
# Using mcp-streamablehttp-client
mcp-streamablehttp-client --server-url https://time.yourdomain.com/mcp --command "get_current_time timezone='America/New_York'"

# Time conversion
mcp-streamablehttp-client --server-url https://time.yourdomain.com/mcp --command "convert_time source_timezone='America/New_York' time='14:30' target_timezone='Asia/Tokyo'"

# Raw protocol
mcp-streamablehttp-client --raw '{"method": "tools/call", "params": {"name": "get_current_time", "arguments": {"timezone": "Europe/London"}}}'
```

## Testing

The service is tested via the comprehensive MCP test suite:
- Protocol compliance tests
- Tool execution tests  
- Authentication flow tests
- Error handling validation
- Timezone accuracy tests

Use the standard project testing commands:
```bash
just test  # Run all tests including mcp-time
```

## Time Capabilities

The service provides comprehensive time functionality for:

### Global Time Queries
- **Current Time**: Get precise current time in any global timezone
- **System Detection**: Automatic local timezone detection and handling
- **DST Awareness**: Proper daylight saving time status and transitions
- **IANA Compliance**: Full support for official timezone database

### Timezone Conversions
- **Bi-directional**: Convert time between any two timezones
- **Precision**: Accurate handling of timezone offsets and DST
- **Format Support**: 24-hour time format with optional seconds
- **Difference Calculation**: Automatic time difference computation

### Temporal Intelligence
- **AI Integration**: Enable AI systems to understand and work with time
- **Scheduling**: Support for global scheduling and coordination
- **Event Planning**: Cross-timezone event planning capabilities
- **Business Hours**: Calculate business hours across global offices

## Integration Benefits

- **AI Enhancement**: Give AI systems accurate temporal awareness
- **Global Operations**: Support for worldwide business operations
- **Scheduling**: Precise meeting and event scheduling across timezones
- **Automation**: Time-based automation and workflow triggers
- **Compliance**: Accurate timestamps for audit and regulatory requirements

## Troubleshooting

### Common Issues

1. **Invalid timezone**: Ensure using valid IANA timezone names (e.g., "America/New_York" not "EST")
2. **Time format errors**: Use 24-hour format (14:30) not 12-hour format (2:30 PM)
3. **Authentication failures**: Verify OAuth token validity
4. **Service not responding**: Check container logs and health status

### Debugging

```bash
# Check service status
just logs mcp-time

# Test authentication
mcp-streamablehttp-client --server-url https://time.yourdomain.com/mcp --test-auth

# Health check
curl -X POST https://time.yourdomain.com/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"'"$MCP_PROTOCOL_VERSION"'","capabilities":{},"clientInfo":{"name":"healthcheck","version":"1.0"}},"id":1}'

# List available tools
mcp-streamablehttp-client --server-url https://time.yourdomain.com/mcp --list-tools
```

## Use Cases

The time service excels at:

### Business Applications
- **Global Meetings**: Schedule meetings across multiple timezones
- **Trading Systems**: Precise timestamps for financial transactions
- **Logistics**: Coordinate shipments and deliveries worldwide
- **Customer Support**: Understand customer timezone context

### Development & Operations
- **Log Analysis**: Correlate events across global infrastructure
- **Deployment Windows**: Schedule maintenance during optimal times
- **Performance Monitoring**: Time-based analysis and alerting
- **Backup Scheduling**: Coordinate backups across global systems

### AI & Automation
- **Temporal Reasoning**: Enable AI to understand time context
- **Smart Scheduling**: Intelligent meeting and event planning
- **Workflow Automation**: Time-triggered processes and workflows
- **Data Analysis**: Time-series analysis with proper timezone handling

### User Experience
- **Localization**: Display times in user's local timezone
- **Event Planning**: Cross-timezone event coordination
- **Travel Planning**: Handle timezone changes during travel
- **Communication**: Schedule calls across global teams

## Integration

The service integrates with:
- **Auth Service**: OAuth token validation
- **Traefik**: Reverse proxy and routing
- **Let's Encrypt**: Automatic HTTPS certificates
- **Other MCP Services**: Can be combined with memory, fetch, and other tools

## Performance Characteristics

- **Stateless Operation**: No persistent state between requests
- **Fast Processing**: Lightweight time calculations
- **Accurate**: Uses system clock and official timezone databases
- **Reliable**: No external dependencies for basic operations
- **Scalable**: Can handle multiple concurrent time queries

## Timezone Support

The service supports all IANA timezone identifiers including:

### Major Global Cities
- **Americas**: America/New_York, America/Los_Angeles, America/Chicago, America/Denver
- **Europe**: Europe/London, Europe/Paris, Europe/Berlin, Europe/Rome
- **Asia**: Asia/Tokyo, Asia/Shanghai, Asia/Kolkata, Asia/Dubai
- **Oceania**: Australia/Sydney, Australia/Melbourne, Pacific/Auckland
- **Africa**: Africa/Cairo, Africa/Johannesburg, Africa/Lagos

### UTC and Offsets
- **UTC**: Coordinated Universal Time
- **Fixed Offsets**: GMT+1, GMT-5, etc.
- **Military**: Z (Zulu), A (Alpha), etc.

The time service provides essential temporal functionality for any application requiring accurate time handling and timezone conversions, seamlessly integrated into the MCP OAuth gateway architecture.