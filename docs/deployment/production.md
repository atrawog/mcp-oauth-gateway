# Production Deployment

This guide covers deploying the MCP OAuth Gateway in a production environment with high availability, security, and monitoring.

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
# Production settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Domain configuration
BASE_DOMAIN=gateway.yourdomain.com
LETSENCRYPT_EMAIL=admin@yourdomain.com
LETSENCRYPT_STAGING=false

# Security
GATEWAY_JWT_SECRET=<generate-with-just-generate-jwt-secret>
ALLOWED_GITHUB_USERS=user1,user2,org:yourorg

# GitHub OAuth
GITHUB_CLIENT_ID=<your-production-client-id>
GITHUB_CLIENT_SECRET=<your-production-client-secret>

# Redis
REDIS_PASSWORD=<strong-redis-password>
REDIS_MAXMEMORY=2gb
REDIS_MAXMEMORY_POLICY=allkeys-lru

# Performance
WORKERS=4
WORKER_CONNECTIONS=1000
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
just health-check
```

### 6. SSL Certificate Setup

Let's Encrypt certificates are automatic:

```bash
# Verify certificate generation
docker logs traefik | grep -i "certificate"

# Check certificate status
just check-certs
```

## High Availability Setup

### Load Balancing

For multi-server deployment:

```yaml
# haproxy.cfg
global
    maxconn 4096
    
defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    
frontend https_front
    bind *:443 ssl crt /etc/ssl/certs/gateway.pem
    default_backend servers
    
backend servers
    balance roundrobin
    option httpchk GET /health
    server gateway1 10.0.1.10:443 check ssl verify none
    server gateway2 10.0.1.11:443 check ssl verify none
```

### Redis Clustering

For Redis HA:

```yaml
# redis-cluster.yml
services:
  redis-master:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    
  redis-replica:
    image: redis:7-alpine
    command: redis-server --replicaof redis-master 6379
    
  sentinel:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis-sentinel.conf
```

## Monitoring Setup

### Prometheus Metrics

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'gateway'
    static_configs:
      - targets: ['auth:8000', 'traefik:8080']
    metrics_path: '/metrics'
```

### Grafana Dashboards

Import dashboards:
- Traefik: Dashboard ID 12250
- Redis: Dashboard ID 763
- Custom MCP: See `monitoring/dashboards/`

### Alerts

```yaml
# alerts.yml
groups:
  - name: gateway
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        annotations:
          summary: "High error rate detected"
          
      - alert: TokenExpirationsSpiking
        expr: rate(token_expirations_total[5m]) > 10
        annotations:
          summary: "Unusual number of token expirations"
```

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

### Rolling Updates

```bash
# Update single service
just update auth

# Update all services
just update-all

# Rollback if needed
just rollback
```

### Health Monitoring

```bash
# Continuous health check
watch -n 5 'just health-check'

# Service status
just status

# Resource usage
just stats
```

## Troubleshooting Production Issues

### High Memory Usage

```bash
# Check memory consumers
just stats --memory

# Clear Redis cache if needed
just redis-cli FLUSHDB
```

### SSL Certificate Issues

```bash
# Force renewal
just renew-certs

# Check certificate validity
just check-certs --verbose
```

### Performance Issues

```bash
# Enable profiling
just profile --duration 60

# Analyze slow queries
just analyze-performance
```

## Disaster Recovery

### Backup Strategy

- **Daily**: Full Redis backup
- **Hourly**: Configuration backup
- **Real-time**: Log shipping to S3

### Recovery Time Objectives

- **RTO**: 15 minutes
- **RPO**: 1 hour
- **Testing**: Monthly DR drills

## Next Steps

1. Set up [SSL Certificates](ssl-certificates.md)
2. Configure [Monitoring](../usage/monitoring.md)
3. Plan [Scaling Strategy](scaling.md)
4. Implement [Backup & Restore](backup-restore.md)