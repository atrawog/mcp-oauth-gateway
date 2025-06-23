# Requirements

This page outlines the system requirements and prerequisites for running the MCP OAuth Gateway.

## System Requirements

### Minimum Hardware

- **CPU**: 2 cores (x86_64 or ARM64)
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 10GB available space
- **Network**: Stable internet connection

### Recommended Hardware

- **CPU**: 4+ cores
- **RAM**: 8GB or more
- **Storage**: 20GB+ SSD storage
- **Network**: Dedicated server with static IP

## Software Requirements

### Required Software

1. **Docker** (20.10.0 or later)
   ```bash
   docker --version
   ```

2. **Docker Compose** (2.0.0 or later)
   ```bash
   docker compose version
   ```

3. **Git** (for cloning repository)
   ```bash
   git --version
   ```

### Operating System

Supported platforms:
- Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+)
- macOS (11.0 Big Sur or later)
- Windows with WSL2

## Domain Requirements

### DNS Configuration

You need a domain with:
- A valid domain name (e.g., `gateway.example.com`)
- DNS A records pointing to your server
- Wildcard subdomain support for services

Example DNS setup:
```
gateway.example.com     A     1.2.3.4
*.gateway.example.com   A     1.2.3.4
```

### SSL Certificates

For production:
- Let's Encrypt support (automatic)
- Or bring your own certificates
- Port 80 and 443 accessible

## External Service Requirements

### GitHub OAuth Application

Required for user authentication:

1. GitHub account with organization access
2. OAuth App created at https://github.com/settings/applications/new
3. Callback URL: `https://auth.yourdomain.com/callback`

### Network Ports

Required open ports:
- **80** - HTTP (for Let's Encrypt challenge)
- **443** - HTTPS (main traffic)
- **6379** - Redis (internal only)
- **8000** - Auth service (internal only)
- **3000** - MCP services (internal only)

## Development Requirements

For development environments:

### Development Tools

1. **just** - Command runner
   ```bash
   cargo install just
   ```

2. **pixi** - Python package manager
   ```bash
   curl -fsSL https://pixi.sh/install.sh | bash
   ```

3. **Python 3.11+** - For local development
   ```bash
   python --version
   ```

### Optional Tools

- **VS Code** with Docker extension
- **Postman** or similar for API testing
- **Redis CLI** for debugging

## Pre-Installation Checklist

Before proceeding with installation:

- [ ] Docker and Docker Compose installed
- [ ] Domain name configured with DNS
- [ ] Ports 80 and 443 accessible
- [ ] GitHub OAuth app created
- [ ] At least 2GB RAM available
- [ ] 10GB disk space available

## Verification Commands

Run these commands to verify your environment:

```bash
# Check Docker
docker run hello-world

# Check Docker Compose
docker compose version

# Check network connectivity
curl -I https://github.com

# Check DNS resolution (replace with your domain)
nslookup gateway.yourdomain.com
```

## Next Steps

Once all requirements are met:
1. Proceed to [Quick Start Guide](quick-start.md)
2. Or review [Configuration Reference](configuration.md)