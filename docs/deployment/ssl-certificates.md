# SSL Certificates

This guide covers SSL/TLS certificate configuration for the MCP OAuth Gateway using Traefik's built-in Let's Encrypt integration.

```{admonition} The Sacred SSL Commandment
:class: important
🔥 **HTTPS is not optional in production!** Unencrypted traffic exposes tokens and credentials. SSL/TLS is your divine shield against packet sniffers! ⚡
```

## SSL Overview

The gateway uses Traefik v3.0 with automatic Let's Encrypt certificate management:

```{mermaid}
graph LR
    A[Client] -->|HTTPS| B[Traefik]
    B -->|ACME| C[Let's Encrypt]
    B -->|HTTP| D[Auth Service]
    B -->|HTTP| E[MCP Services]

    style B fill:#f9f,stroke:#333,stroke-width:4px
    style C fill:#9f9,stroke:#333,stroke-width:2px
```

## Certificate Types

### Automatic Let's Encrypt (Recommended)

Free, automatic SSL certificates with renewal:

**Advantages:**
- ✅ Free certificates
- ✅ Automatic renewal
- ✅ Wide browser support
- ✅ No manual management

**Requirements:**
- 📧 Valid email address
- 🌐 Public domain name
- 🚪 Port 80 accessible
- 📍 Valid DNS records

### Manual Certificates

For enterprise or special requirements:

**When to use:**
- Internal CA certificates
- Extended Validation (EV) certs
- Wildcard without DNS challenge
- Air-gapped environments

## Let's Encrypt Configuration

### Basic Setup

The gateway comes pre-configured for Let's Encrypt. Essential settings in `.env`:

```bash
# Required for Let's Encrypt
ACME_EMAIL=admin@yourdomain.com
DOMAIN=mcp.yourdomain.com

# Certificate resolver (don't change)
CERT_RESOLVER=letsencrypt

# Optional: Use staging for testing
# ACME_CA_SERVER=https://acme-staging-v02.api.letsencrypt.org/directory
```

### Traefik Static Configuration

Located in `traefik/traefik.yml`:

```yaml
certificatesResolvers:
  letsencrypt:
    acme:
      email: ${ACME_EMAIL}
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web
      # Optional: DNS challenge for wildcards
      # dnsChallenge:
      #   provider: cloudflare
      #   delayBeforeCheck: 0
```

### Service Labels for SSL

Each service must declare SSL usage via Docker labels:

```yaml
labels:
  - "traefik.http.routers.auth.tls=true"
  - "traefik.http.routers.auth.tls.certresolver=letsencrypt"
  - "traefik.http.routers.auth.tls.domains[0].main=${DOMAIN}"
  - "traefik.http.routers.auth.tls.domains[0].sans=*.${DOMAIN}"
```

## HTTP Challenge (Default)

The simplest method for single domains:

### How it Works

1. Traefik requests certificate from Let's Encrypt
2. Let's Encrypt provides a token
3. Traefik serves token at `http://yourdomain/.well-known/acme-challenge/`
4. Let's Encrypt verifies domain control
5. Certificate issued and stored

### Configuration

```yaml
# traefik/traefik.yml
certificatesResolvers:
  letsencrypt:
    acme:
      httpChallenge:
        entryPoint: web  # Port 80
```

### Requirements

```bash
# Ensure port 80 is open
sudo ufw allow 80/tcp

# Verify DNS points to your server
dig +short mcp.yourdomain.com

# Test HTTP accessibility
curl -I http://mcp.yourdomain.com
```

## DNS Challenge (For Wildcards)

Required for wildcard certificates (`*.domain.com`):

### Supported Providers

- Cloudflare (recommended)
- Route53
- DigitalOcean
- Google Cloud DNS
- Azure DNS
- Many others...

### Cloudflare Setup

1. **Get API Token**:
   - Go to Cloudflare → My Profile → API Tokens
   - Create token with "Zone:DNS:Edit" permissions
   - Copy token value

2. **Configure Traefik**:

```yaml
# traefik/traefik.yml
certificatesResolvers:
  letsencrypt:
    acme:
      email: ${ACME_EMAIL}
      storage: /letsencrypt/acme.json
      dnsChallenge:
        provider: cloudflare
        resolvers:
          - "1.1.1.1:53"
          - "8.8.8.8:53"
```

3. **Add Environment Variables**:

```bash
# .env
CF_API_EMAIL=your-email@example.com
CF_API_KEY=your-cloudflare-api-key
# Or use API token (recommended)
CF_DNS_API_TOKEN=your-cloudflare-api-token
```

### Route53 Setup

```yaml
# traefik/traefik.yml
dnsChallenge:
  provider: route53

# .env
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
```

## Certificate Storage

### Storage Location

Certificates are stored in Docker volume:

```yaml
volumes:
  letsencrypt:
    driver: local
```

Physical location:
```bash
# View certificates
docker exec mcp-oauth-traefik-1 cat /letsencrypt/acme.json | jq .

# Backup certificates
docker cp mcp-oauth-traefik-1:/letsencrypt/acme.json ./backup-acme.json
```

### Permissions

```{warning}
The acme.json file contains private keys! Protect it carefully:
```

```bash
# Inside container (automatic)
chmod 600 /letsencrypt/acme.json

# For backups
chmod 600 ./backup-acme.json
```

## Certificate Renewal

### Automatic Renewal

Traefik handles renewal automatically:
- Checks daily for expiring certificates
- Renews when < 30 days remaining
- No downtime during renewal
- No manual intervention needed

### Manual Renewal

Force renewal if needed:

```bash
# Stop Traefik
just stop traefik

# Remove certificates
docker exec mcp-oauth-traefik-1 rm /letsencrypt/acme.json

# Restart Traefik (triggers new certificate request)
just up traefik

# Monitor logs
just logs -f traefik | grep -i acme
```

## SSL Configuration

### Security Headers

Enhance SSL security with headers:

```yaml
# traefik/dynamic/security.yml
http:
  middlewares:
    ssl-headers:
      headers:
        sslRedirect: true
        stsSeconds: 31536000
        stsIncludeSubdomains: true
        stsPreload: true
        forceSTSHeader: true
        contentSecurityPolicy: "upgrade-insecure-requests"
```

### TLS Versions

Configure minimum TLS version:

```yaml
# traefik/traefik.yml
providers:
  file:
    filename: /etc/traefik/dynamic/tls.yml

# traefik/dynamic/tls.yml
tls:
  options:
    default:
      minVersion: VersionTLS12
      cipherSuites:
        - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
        - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
        - TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305
```

## Testing SSL

### Basic Tests

```bash
# Check certificate
echo | openssl s_client -connect mcp.yourdomain.com:443 2>/dev/null | openssl x509 -noout -text

# Check expiry
echo | openssl s_client -connect mcp.yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates

# Test SSL/TLS versions
nmap --script ssl-enum-ciphers -p 443 mcp.yourdomain.com
```

### Online Tools

- [SSL Labs](https://www.ssllabs.com/ssltest/) - Comprehensive SSL test
- [Security Headers](https://securityheaders.com/) - Header analysis
- [Hardenize](https://www.hardenize.com/) - Security configuration

### Expected Results

```bash
# Grade A+ on SSL Labs
# All modern browsers supported
# No SSL warnings
# HSTS enabled
# Strong ciphers only
```

## Troubleshooting SSL

### Certificate Not Issued

```bash
# Check Traefik logs
just logs traefik | grep -i "acme\|error\|challenge"

# Common issues:
# - DNS not pointing to server
# - Port 80 blocked
# - Rate limits hit
```

### Rate Limits

Let's Encrypt limits:
- 50 certificates per domain per week
- 5 duplicate certificates per week
- 5 failed validations per hour

```bash
# Use staging for testing
ACME_CA_SERVER=https://acme-staging-v02.api.letsencrypt.org/directory
```

### DNS Issues

```bash
# Verify DNS resolution
nslookup mcp.yourdomain.com
dig mcp.yourdomain.com

# Check propagation
curl -s https://dns.google/resolve?name=mcp.yourdomain.com | jq .
```

### Challenge Failures

HTTP Challenge:
```bash
# Test HTTP accessibility
curl -v http://mcp.yourdomain.com/.well-known/acme-challenge/test

# Check firewall
sudo iptables -L -n | grep 80
```

DNS Challenge:
```bash
# Verify DNS provider credentials
just exec traefik env | grep CF_

# Test DNS updates manually
# (varies by provider)
```

## Advanced SSL Configurations

### Multiple Domains

```yaml
labels:
  - "traefik.http.routers.auth.tls.domains[0].main=mcp.domain1.com"
  - "traefik.http.routers.auth.tls.domains[0].sans=*.mcp.domain1.com"
  - "traefik.http.routers.auth.tls.domains[1].main=mcp.domain2.com"
  - "traefik.http.routers.auth.tls.domains[1].sans=*.mcp.domain2.com"
```

### Certificate Per Service

```yaml
# Service-specific certificate
labels:
  - "traefik.http.routers.special-service.tls.certresolver=letsencrypt"
  - "traefik.http.routers.special-service.tls.domains[0].main=special.domain.com"
```

### Manual Certificate Import

For pre-existing certificates:

```yaml
# traefik/dynamic/certificates.yml
tls:
  stores:
    default:
      defaultCertificate:
        certFile: /certs/cert.pem
        keyFile: /certs/key.pem
  certificates:
    - certFile: /certs/cert.pem
      keyFile: /certs/key.pem
      stores:
        - default
```

## Best Practices

### Security

1. **Always use HTTPS in production** - No exceptions!
2. **Enable HSTS** - Prevent downgrade attacks
3. **Use strong ciphers** - TLS 1.2+ only
4. **Monitor expiry** - Set up alerts
5. **Backup certificates** - Include in disaster recovery

### Operations

1. **Test in staging first** - Use Let's Encrypt staging
2. **Monitor rate limits** - Avoid hitting limits
3. **Document DNS providers** - For DNS challenges
4. **Automate monitoring** - Certificate expiry alerts
5. **Plan for renewal** - Ensure automation works

### Development

1. **Use self-signed for local** - Don't waste Let's Encrypt quota
2. **Test with staging certs** - Full flow without rate limits
3. **Mock SSL in tests** - Don't depend on external CAs
4. **Document SSL requirements** - For each environment

## Next Steps

With SSL configured:

1. **Test thoroughly** → Run SSL Labs test
2. **Monitor certificates** → Set up expiry alerts
3. **Configure monitoring** → [Monitoring Guide](monitoring)
4. **Review security** → [Security Architecture](../architecture/security)

---

*Remember: Encryption is your divine shield. Configure it properly, and your data shall travel safely through the hostile lands of the internet!* 🔒⚡
