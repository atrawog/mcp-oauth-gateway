# Production Deployment

This guide covers deploying the MCP OAuth Gateway in a production environment with security best practices and monitoring.

## Pre-Deployment Checklist

### Infrastructure Requirements

- [ ] Server with 4+ CPU cores, 8GB+ RAM
- [ ] Domain with DNS configured
- [ ] Firewall rules for ports 80, 443
- [ ] Backup storage configured
- [ ] Monitoring infrastructure ready

### Security Checklist

- [ ] Strong JWT secret generated
- [ ] GitHub OAuth app configured
- [ ] User whitelist defined
- [ ] SSL certificates ready
- [ ] Firewall rules configured
- [ ] Security headers enabled

### Configuration Checklist

- [ ] Production .env file created
- [ ] All required variables set
- [ ] Redis persistence configured
- [ ] Log rotation configured
- [ ] Health checks verified

## Step-by-Step Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create deployment user
sudo useradd -m -s /bin/bash mcp-gateway
sudo usermod -aG docker mcp-gateway
```

### 2. Clone and Configure

```bash
# Switch to deployment user
sudo su - mcp-gateway

# Clone repository
git clone https://github.com/your-org/mcp-oauth-gateway.git
cd mcp-oauth-gateway

# Create production config
cp .env.example .env.production
```

### 3. Configure Environment

Edit `.env.production`:

```bash
# Domain configuration
BASE_DOMAIN=gateway.yourdomain.com
ACME_EMAIL=admin@yourdomain.com

# Security
GATEWAY_JWT_SECRET=<generate-with-just-generate-jwt-secret>
ALLOWED_GITHUB_USERS=user1,user2

# GitHub OAuth
GITHUB_CLIENT_ID=<your-production-client-id>
GITHUB_CLIENT_SECRET=<your-production-client-secret>

# Redis
REDIS_PASSWORD=<strong-redis-password>
```

### 4. Generate Secrets

```bash
# Use production env
cp .env.production .env

# Generate JWT secret
just generate-jwt-secret

# Generate GitHub tokens
just generate-github-token
```

### 5. Deploy Services

```bash
# Pull images
docker-compose pull

# Start services
just up -d

# Verify health
just check-health
```

### 6. SSL Certificate Setup

Let's Encrypt certificates are automatic:

```bash
# Verify certificate generation
just logs traefik | grep -i "certificate"

# Check certificate status
just check-ssl
```

## Monitoring Setup

Monitoring is done via Docker logs and the built-in health checks. Use the monitoring commands provided in the [Monitoring Guide](../usage/monitoring.md).

## Security Hardening

### Firewall Rules

```bash
# UFW configuration
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Fail2ban Configuration

```ini
# /etc/fail2ban/jail.local
[mcp-gateway]
enabled = true
port = 443
filter = mcp-gateway
logpath = /var/log/mcp-gateway/auth.log
maxretry = 5
bantime = 3600
```

### Security Headers

Verify headers:

```bash
curl -I https://gateway.yourdomain.com | grep -E "(Strict-Transport|X-Frame|X-Content|Content-Security)"
```

## Backup and Recovery

### Automated Backups

```bash
# backup.sh
#!/bin/bash
BACKUP_DIR="/backups/mcp-gateway"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup Redis
docker exec redis redis-cli BGSAVE
docker cp redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz .env docker-compose.yml

# Backup to S3
aws s3 sync $BACKUP_DIR s3://backups/mcp-gateway/
```

### Recovery Procedure

```bash
# Restore Redis
docker cp backup.rdb redis:/data/dump.rdb
docker restart redis

# Restore configuration
tar -xzf config_backup.tar.gz
docker-compose up -d
```

## Performance Tuning

### Docker Settings

```yaml
# docker-compose.production.yml
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
```

### Redis Optimization

```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## Maintenance

### Service Updates

```bash
# Rebuild and update single service
just rebuild auth

# Rebuild all services
just rebuild

# Check logs after update
just logs -f
```

### Health Monitoring

```bash
# Continuous health check
watch -n 5 'just check-health'

# Quick health check
just health-quick

# Resource usage
docker stats
```

## Troubleshooting Production Issues

### High Memory Usage

```bash
# Check memory consumers
docker stats

# Clear Redis cache if needed
just exec redis redis-cli FLUSHDB
```

### SSL Certificate Issues

```bash
# Check certificate status
just check-ssl

# View Traefik logs for certificate issues
just logs traefik | grep -i "acme"
```

### Performance Issues

```bash
# Analyze OAuth logs
just analyze-oauth-logs

# Check service logs for slow requests
just logs | grep "duration"
```

## Next Steps

1. Review [Security Best Practices](../architecture/security.md)
2. Configure [Monitoring](../usage/monitoring.md)
3. Set up regular backups using the provided backup script
4. Test disaster recovery procedures