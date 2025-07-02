# Production Deployment

This guide covers deploying the MCP OAuth Gateway to production environments with security hardening and high availability.

```{admonition} Production Sacred Laws
:class: important
🔥 **Production demands perfection!** Every shortcut taken here will haunt you at 3 AM. Follow these divine patterns or face eternal debugging! ⚡
```

## Pre-Production Checklist

Before deploying to production, ensure:

### Infrastructure Ready ✅
- [ ] Linux server with Docker Engine 20.10+
- [ ] Domain with DNS control
- [ ] SSL certificates (Let's Encrypt)
- [ ] Firewall configured
- [ ] Backup storage available

### Configuration Complete ✅
- [ ] Production `.env` file created
- [ ] All secrets generated (not default values!)
- [ ] GitHub OAuth app configured for production
- [ ] Access control lists defined

### Security Hardened ✅
- [ ] No default passwords
- [ ] Firewall rules restrictive
- [ ] SSH key-only access
- [ ] SELinux/AppArmor enabled
- [ ] Audit logging configured

## Production Environment Setup

### Step 1: Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    fail2ban \
    ufw

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Install Docker (official method)
curl -fsSL https://get.docker.com | sudo bash

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Step 2: Security Hardening

```bash
# Secure SSH
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Configure fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Set up automatic updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Step 3: Deploy MCP OAuth Gateway

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/yourusername/mcp-oauth-gateway.git
cd mcp-oauth-gateway
sudo chown -R $USER:$USER .

# Install Just command runner
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash

# Install Pixi package manager
curl -fsSL https://pixi.sh/install.sh | bash
```

## Production Configuration

### Create Production .env

```bash
# Create production configuration
cp .env.example .env.production
nano .env.production
```

Production `.env` template:

```bash
# Core Settings
BASE_DOMAIN=mcp.yourdomain.com

# Auth Service - Production GitHub OAuth
GITHUB_CLIENT_ID=prod_github_client_id
GITHUB_CLIENT_SECRET=prod_github_client_secret

# Security - Generate strong secrets!
GATEWAY_JWT_SECRET=$(openssl rand -base64 64)
REDIS_PASSWORD=$(openssl rand -base64 64)

# Access Control - Specific users only
ALLOWED_GITHUB_USERS=admin1,admin2,admin3
# Or allow any authenticated GitHub user with:
# ALLOWED_GITHUB_USERS=*

# Client Configuration
CLIENT_LIFETIME=7776000  # 90 days (0 = eternal)

# Token Lifetimes (defaults from .env.example)
ACCESS_TOKEN_LIFETIME=86400      # 24 hours
REFRESH_TOKEN_LIFETIME=2592000   # 30 days
SESSION_TIMEOUT=3600             # 1 hour

# Email for Let's Encrypt certificates
ACME_EMAIL=admin@yourdomain.com

# MCP Protocol Version
MCP_PROTOCOL_VERSION=2025-06-18

# Enable production MCP services as needed
MCP_FETCH_ENABLED=true
MCP_FILESYSTEM_ENABLED=true
MCP_MEMORY_ENABLED=true
MCP_TIME_ENABLED=true
# Add other MCP_*_ENABLED as required
```

### Security Configuration

Create additional security configurations:

```bash
# Create secrets directory
mkdir -p secrets
chmod 700 secrets

# Generate JWT RSA keys for production
openssl genrsa -out secrets/jwt-private.pem 4096
openssl rsa -in secrets/jwt-private.pem -pubout -out secrets/jwt-public.pem
chmod 600 secrets/jwt-*.pem

# Create Traefik dynamic configuration
cat > traefik/dynamic/security.yml << 'EOF'
http:
  middlewares:
    security-headers:
      headers:
        customResponseHeaders:
          X-Frame-Options: "DENY"
          X-Content-Type-Options: "nosniff"
          X-XSS-Protection: "1; mode=block"
          Referrer-Policy: "strict-origin-when-cross-origin"
          Permissions-Policy: "geolocation=(), microphone=(), camera=()"
        sslRedirect: true
        sslProxyHeaders:
          X-Forwarded-Proto: "https"
        contentSecurityPolicy: |
          default-src 'self';
          script-src 'self' 'unsafe-inline';
          style-src 'self' 'unsafe-inline';
          img-src 'self' data: https:;
          font-src 'self';
          connect-src 'self' https://api.github.com;
          frame-ancestors 'none';
          base-uri 'self';
          form-action 'self'
EOF
```

## Production Deployment

### Step 1: Initialize Infrastructure

```bash
# Use production env file
cp .env.production .env

# Initial setup (creates networks and volumes)
just setup

# Install Python dependencies via Pixi
pixi install

# Generate all required secrets
just generate-jwt-secret
just generate-rsa-keys
just generate-redis-password
```

### Step 2: Deploy Services

```bash
# Deploy with production settings
just up -d

# Monitor deployment
just logs -f

# Check service health
just check-health
```

### Step 3: Verify Deployment

```bash
# Check service status
just status

# Verify health endpoints
just check-health

# Test OAuth metadata
curl https://mcp.yourdomain.com/.well-known/oauth-authorization-server

# Check SSL certificate
echo | openssl s_client -connect mcp.yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

## High Availability Setup

### Redis Persistence

Ensure Redis data survives restarts:

```bash
# Create OAuth data backup
just oauth-backup

# List available backups
just oauth-backup-list

# Restore from backup if needed
just oauth-restore
```

### Service Health Monitoring

The gateway provides built-in health checks:

```bash
# Check all services
just check-health

# Monitor service status
just status

# View logs
just logs -f
```


### Backup Strategy

Create automated backups:

```bash
# Create backup script
cat > scripts/backup-production.sh << 'EOF'
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/backups/mcp-oauth/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup Redis
just exec redis redis-cli BGSAVE
sleep 5
docker cp mcp-oauth-redis-1:/data/dump.rdb "$BACKUP_DIR/redis-dump.rdb"

# Backup configuration
cp .env "$BACKUP_DIR/.env"
cp -r traefik/dynamic "$BACKUP_DIR/traefik-dynamic"

# Backup certificates
docker cp mcp-oauth-traefik-1:/letsencrypt "$BACKUP_DIR/letsencrypt"

# Compress backup
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"
rm -rf "$BACKUP_DIR"

# Keep only last 30 days of backups
find /backups/mcp-oauth -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR.tar.gz"
EOF

chmod +x scripts/backup-production.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/mcp-oauth-gateway/scripts/backup-production.sh") | crontab -
```

## Performance Optimization

### Docker Optimization

```yaml
# docker-compose.override.yml for production
services:
  auth:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"

  redis:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
    sysctls:
      - net.core.somaxconn=1024
    restart: unless-stopped
```

### Traefik Optimization

```yaml
# traefik/traefik.yml additions
global:
  checkNewVersion: false
  sendAnonymousUsage: false

serversTransport:
  maxIdleConnsPerHost: 200

providers:
  docker:
    exposedByDefault: false
    network: public
    watch: true
    endpoint: "unix:///var/run/docker.sock"

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          priority: 1000
  websecure:
    address: ":443"
    http:
      middlewares:
        - security-headers@file
```


## Post-Deployment Tasks

### 1. Verify Security

```bash
# Security scan
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image mcp-oauth-auth:latest

# Check exposed ports
sudo netstat -tlnp | grep -E ':(80|443)'

# Verify SSL configuration
nmap --script ssl-enum-ciphers -p 443 mcp.yourdomain.com
```

### 2. Performance Testing

```bash
# Basic load test
ab -n 1000 -c 10 -H "Authorization: Bearer YOUR_TOKEN" \
  https://mcp.yourdomain.com/mcp

# Monitor during load
just logs -f traefik
docker stats
```

### 3. Create Runbook

Document operational procedures:

```markdown
# MCP OAuth Gateway Runbook

## Emergency Contacts
- Platform Team: platform@company.com
- On-call: +1-555-0123

## Common Operations

### Restart Service
just restart auth

### View Logs
just logs auth -n 1000

### Emergency Shutdown
just down

### Restore from Backup
./scripts/restore-backup.sh /backups/mcp-oauth/20240101_020000.tar.gz

## Troubleshooting

### High Memory Usage
1. Check for memory leaks: `just exec auth ps aux`
2. Restart affected service: `just restart auth`
3. Check Redis memory: `just exec redis redis-cli INFO memory`

### OAuth Failures
1. Check auth logs: `just logs auth | grep ERROR`
2. Verify GitHub connectivity: `curl -I https://api.github.com`
3. Check Redis connectivity: `just exec auth redis-cli PING`
```

## Maintenance

### Regular Tasks

```bash
# Weekly: Rebuild and update containers
just rebuild

# Or update specific services
just rebuild auth mcp-fetch

# Monthly: Security updates
sudo apt update && sudo apt upgrade -y
docker system prune -af

# Quarterly: Certificate renewal check
just exec traefik cat /letsencrypt/acme.json | jq '.letsencrypt.Certificates[].domain'
```

### Scaling Considerations

When traffic grows:

```{admonition} Future Considerations
:class: note
The following are potential scaling strategies not currently implemented:
```

1. **Horizontal Scaling**: Would require adding service replicas and load balancing
2. **Redis Clustering**: Would require implementing Redis Sentinel or Cluster
3. **Load Balancing**: Would require external load balancer configuration
4. **CDN**: Would require serving static assets through a CDN

## Production Checklist Summary

Before going live:

- [ ] All services healthy
- [ ] SSL certificates valid
- [ ] Backups automated
- [ ] Health checks passing
- [ ] Logs being collected
- [ ] Security scanned
- [ ] Performance tested
- [ ] Runbook created
- [ ] Team trained
- [ ] Rollback plan ready

---

*May your production deployment be blessed with uptime, may your logs be free of errors, and may your on-call nights be peaceful!* 🚀⚡
