# Deployment

This section covers deployment strategies, production configurations, and operational considerations for the MCP OAuth Gateway.

## Deployment Topics

```{toctree}
:maxdepth: 2

deployment/production
deployment/ssl-certificates
deployment/scaling
deployment/backup-restore
```

## Deployment Overview

The MCP OAuth Gateway supports various deployment scenarios:

### Production Deployment

For production environments:
- Full SSL/TLS encryption via Let's Encrypt
- High availability configuration
- Monitoring and alerting setup
- Backup and disaster recovery

### Development Deployment

For development and testing:
- Local Docker Compose setup
- Self-signed certificates
- Debug logging enabled
- Hot reload support

## Prerequisites

Before deploying:

1. **Domain Setup**
   - Valid domain name
   - DNS A records configured
   - Wildcard certificate support (*.yourdomain.com)

2. **Infrastructure**
   - Docker and Docker Compose
   - Sufficient resources (min 2GB RAM)
   - Persistent storage for data

3. **Security**
   - Secure JWT secrets
   - GitHub OAuth app configured
   - Firewall rules configured

## Deployment Checklist

- [ ] Domain and DNS configured
- [ ] Environment variables set
- [ ] GitHub OAuth app created
- [ ] JWT secrets generated
- [ ] SSL certificates ready
- [ ] Backup strategy defined
- [ ] Monitoring configured
- [ ] Health checks verified

## Quick Deploy

```bash
# Generate secrets
just generate-jwt-secret
just generate-github-token

# Deploy services
just up

# Verify deployment
just test
```

## Next Steps

1. Review [Production Deployment](deployment/production.md) for detailed setup
2. Configure [SSL Certificates](deployment/ssl-certificates.md)
3. Plan for [Scaling](deployment/scaling.md)
4. Set up [Backup & Restore](deployment/backup-restore.md)