# Production Deployment

This guide covers deploying the MCP OAuth Gateway to production environments with security hardening, high availability, and monitoring.

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
- [ ] Monitoring infrastructure

### Configuration Complete ✅
- [ ] Production `.env` file created
- [ ] All secrets generated (not default values!)
- [ ] GitHub OAuth app configured for production
- [ ] Access control lists defined
- [ ] Rate limits configured

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
COMPOSE_PROJECT_NAME=mcp-oauth-prod
DOMAIN=mcp.yourdomain.com
ENVIRONMENT=production

# Auth Service - Production GitHub OAuth
GITHUB_CLIENT_ID=prod_github_client_id
GITHUB_CLIENT_SECRET=prod_github_client_secret

# Security - Generate strong secrets!
GATEWAY_JWT_SECRET=$(openssl rand -base64 64)
REDIS_PASSWORD=$(openssl rand -base64 64)

# Access Control - Specific users only
ALLOWED_GITHUB_USERS=admin1,admin2,admin3
# Optional: Organization restrictions
# ALLOWED_GITHUB_ORGS=mycompany
# ALLOWED_GITHUB_TEAMS=mycompany/platform-team

# Client Configuration
CLIENT_LIFETIME=2592000  # 30 days for production
JWT_EXPIRY=3600         # 1 hour tokens

# Redis - Production settings
REDIS_SAVE_INTERVALS="900 1 300 10 60 10000"
REDIS_APPENDONLY=yes
REDIS_MAXMEMORY=2gb
REDIS_MAXMEMORY_POLICY=allkeys-lru

# Traefik - Production TLS
ACME_EMAIL=admin@yourdomain.com
TRAEFIK_LOG_LEVEL=WARN
TRAEFIK_DASHBOARD=false  # Disable in production!

# Rate Limiting - Production limits
RATE_LIMIT_AVERAGE=50
RATE_LIMIT_BURST=100
OAUTH_RATE_LIMIT_REGISTER=5/hour
OAUTH_RATE_LIMIT_TOKEN=60/hour

# Monitoring
ENABLE_METRICS=true
ENABLE_TRACING=true
LOG_LEVEL=INFO
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

# Create networks and volumes
just init

# Pull all images first
just pull
```

### Step 2: Deploy Services

```bash
# Deploy with production settings
just up -d

# Monitor deployment
just logs -f

# Wait for services to be healthy
just wait-healthy
```

### Step 3: Verify Deployment

```bash
# Check all services are running
just ps

# Verify health endpoints
just health-check-all

# Test OAuth metadata
curl https://mcp.yourdomain.com/.well-known/oauth-authorization-server

# Check SSL certificate
echo | openssl s_client -connect mcp.yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

## High Availability Setup

### Redis Persistence

Ensure Redis data survives restarts:

```bash
# Verify Redis persistence
just exec redis redis-cli CONFIG GET save
just exec redis redis-cli CONFIG GET appendonly

# Create Redis backup
just backup-redis
```

### Service Health Monitoring

Configure external monitoring:

```yaml
# monitoring/docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - internal

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - internal
      - public
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
        - rate-limit@file
```

## Monitoring and Alerting

### Set Up Monitoring Stack

```bash
# Deploy monitoring
just monitoring-up

# Configure alerts
cat > monitoring/alerts.yml << 'EOF'
groups:
  - name: mcp-oauth
    rules:
      - alert: ServiceDown
        expr: up{job="mcp-oauth"} == 0
        for: 5m
        annotations:
          summary: "Service {{ $labels.instance }} is down"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes{name=~"mcp-oauth.*"} > 1e9
        for: 10m
        annotations:
          summary: "High memory usage in {{ $labels.name }}"

      - alert: HighErrorRate
        expr: rate(traefik_backend_requests_total{code=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate on {{ $labels.backend }}"
EOF
```

### Log Aggregation

```bash
# Set up centralized logging
cat > docker-compose.logging.yml << 'EOF'
services:
  loki:
    image: grafana/loki:latest
    volumes:
      - ./loki-config.yml:/etc/loki/loki-config.yml
      - loki-data:/loki
    command: -config.file=/etc/loki/loki-config.yml
    networks:
      - internal

  promtail:
    image: grafana/promtail:latest
    volumes:
      - ./promtail-config.yml:/etc/promtail/promtail-config.yml
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: -config.file=/etc/promtail/promtail-config.yml
    networks:
      - internal
EOF
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
# Weekly: Update containers
just pull
just up -d

# Monthly: Security updates
sudo apt update && sudo apt upgrade -y
docker system prune -af

# Quarterly: Certificate renewal check
just exec traefik cat /letsencrypt/acme.json | jq '.letsencrypt.Certificates[].domain'
```

### Scaling Considerations

When traffic grows:

1. **Horizontal Scaling**: Add more auth service replicas
2. **Redis Clustering**: Implement Redis Sentinel
3. **Load Balancing**: Add external load balancer
4. **CDN**: Serve static assets via CDN

## Production Checklist Summary

Before going live:

- [ ] All services healthy
- [ ] SSL certificates valid
- [ ] Backups automated
- [ ] Monitoring active
- [ ] Alerts configured
- [ ] Security scanned
- [ ] Performance tested
- [ ] Runbook created
- [ ] Team trained
- [ ] Rollback plan ready

---

*May your production deployment be blessed with uptime, may your logs be free of errors, and may your on-call nights be peaceful!* 🚀⚡
