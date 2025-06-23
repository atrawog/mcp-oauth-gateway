# Getting Started

Welcome to the MCP OAuth Gateway! This guide will help you get up and running quickly with a fully functional OAuth 2.1 authenticated MCP service ecosystem.

```{warning}
**Reference Implementation Notice**

This is a reference implementation and test platform for the MCP protocol:
- Intended for development and testing, not production use
- Likely contains security vulnerabilities
- Requires thorough security review before any production deployment
- Subject to significant changes as the MCP protocol evolves

**Use at your own risk**, especially in production environments.
```

## Prerequisites

Before you begin, ensure you have:

- **Docker & Docker Compose** - For containerized services
- **Python 3.12+** - For development and tooling
- **Git** - For source code management
- **GitHub Account** - For OAuth integration (optional but recommended)

## Quick Installation

### 1. Clone the Repository

```bash
git clone https://github.com/atrawog/mcp-oauth-gateway.git
cd mcp-oauth-gateway
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (add your GitHub OAuth credentials)
# See installation guide for detailed configuration
```

### 3. Start Services

```bash
# Install dependencies and start all services
just up

# Verify services are running
just check-health
```

### 4. Run Tests

```bash
# Run comprehensive test suite
just test

# Check service status
just logs
```

That's it! You now have a fully functional MCP OAuth Gateway with all services running.

## What's Next?

- {doc}`installation` - Detailed installation and configuration
- {doc}`first-setup` - Complete setup walkthrough
- {doc}`basic-usage` - Using the services and APIs
- {doc}`../services/index` - Explore available MCP services
- {doc}`../integration/claude-ai` - Integrate with Claude.ai