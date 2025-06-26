# Installation & Setup

This section provides comprehensive guidance for installing and setting up the MCP OAuth Gateway.

## Prerequisites

Before you begin, ensure you have:

- Docker and Docker Compose installed
- A domain name with DNS configured
- Basic understanding of OAuth 2.1 and MCP protocols

## Quick Start

For a rapid deployment, see our [Quick Start Guide](installation/quick-start.md).

## Topics in this Section

```{toctree}
:maxdepth: 2

installation/requirements
installation/quick-start
installation/configuration
installation/github-oauth
```

## Overview

The MCP OAuth Gateway can be deployed in various configurations:

1. **Development Setup** - For local testing and development
2. **Production Deployment** - For serving real MCP clients
3. **Multi-Service Configuration** - Running multiple MCP services

Each setup type has specific requirements and configuration steps detailed in the subsections.

## Support

If you encounter issues during installation:

1. Check the [Monitoring & Troubleshooting](usage/monitoring.md) guide
2. Review service logs with `just logs`
3. Verify your configuration with `just test`
