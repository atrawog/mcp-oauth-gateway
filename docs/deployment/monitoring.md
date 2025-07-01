# Monitoring and Observability

This guide covers setting up comprehensive monitoring for the MCP OAuth Gateway, including metrics, logging, tracing, and alerting.

```{admonition} The Divine Law of Observability
:class: important
🔥 **You cannot fix what you cannot see!** Production without monitoring is like sailing blind in a storm. Implement observability or face debugging darkness! ⚡
```

## Monitoring Architecture

The gateway supports a complete observability stack:

```{mermaid}
graph TB
    subgraph "MCP OAuth Gateway"
        A[Auth Service] --> M[Metrics]
        A --> L[Logs]
        A --> T[Traces]
        B[MCP Services] --> M
        B --> L
        B --> T
        C[Traefik] --> M
        C --> L
    end

    subgraph "Monitoring Stack"
        M --> P[Prometheus]
        L --> K[Loki]
        T --> J[Jaeger]
        P --> G[Grafana]
        K --> G
        J --> G
    end

    G --> AL[Alerts]

    style G fill:#f9f,stroke:#333,stroke-width:4px
```

## Built-in Monitoring

### Health Checks

Every service exposes health endpoints:

```bash
# Check all service health
just health-check

# Individual service health
curl http://auth.localhost/health
curl http://mcp-fetch.localhost/health

# Traefik health
curl http://localhost:8080/ping
```

### Service Logs

Centralized logging via Docker:

```bash
# View all logs
just logs

# Follow specific service
just logs -f auth

# Filter by time
just logs --since 1h

# Search logs
just logs | grep ERROR
just logs auth | jq '. | select(.level=="error")'
```

### Docker Stats

Real-time resource usage:

```bash
# Monitor all services
just stats

# Or directly
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## Prometheus Metrics

### Deploy Prometheus

Create `monitoring/prometheus-compose.yml`:

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.45.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--web.enable-lifecycle'
    networks:
      - internal
    ports:
      - "9090:9090"
    restart: unless-stopped

volumes:
  prometheus-data:
```

### Prometheus Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'traefik'
    static_configs:
      - targets: ['traefik:8080']
    metrics_path: '/metrics'

  - job_name: 'auth-service'
    static_configs:
      - targets: ['auth:8000']
    metrics_path: '/metrics'

  - job_name: 'mcp-services'
    static_configs:
      - targets:
        - 'mcp-fetch:3000'
        - 'mcp-filesystem:3000'
        - 'mcp-memory:3000'
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Service Metrics

Auth service exposes metrics at `/metrics`:

```python
# Example metrics exposed
mcp_oauth_requests_total{method="POST",endpoint="/token",status="200"} 1234
mcp_oauth_active_sessions{service="auth"} 45
mcp_oauth_token_validations_total{result="success"} 5678
mcp_oauth_client_registrations_total 89
```

## Grafana Dashboards

### Deploy Grafana

Add to monitoring stack:

```yaml
services:
  grafana:
    image: grafana/grafana:10.0.0
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    networks:
      - internal
      - public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.grafana.rule=Host(`grafana.${DOMAIN}`)"
      - "traefik.http.routers.grafana.tls=true"
      - "traefik.http.routers.grafana.tls.certresolver=letsencrypt"
    restart: unless-stopped

volumes:
  grafana-data:
```

### Dashboard Provisioning

Create `monitoring/grafana/provisioning/dashboards/mcp-oauth.json`:

```json
{
  "dashboard": {
    "title": "MCP OAuth Gateway",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(mcp_oauth_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Active Sessions",
        "targets": [
          {
            "expr": "mcp_oauth_active_sessions"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(mcp_oauth_requests_total{status=~\"4..|5..\"}[5m])"
          }
        ]
      }
    ]
  }
}
```

## Log Aggregation with Loki

### Deploy Loki

```yaml
services:
  loki:
    image: grafana/loki:2.9.0
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yaml:ro
      - loki-data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - internal
    ports:
      - "3100:3100"
    restart: unless-stopped

  promtail:
    image: grafana/promtail:2.9.0
    volumes:
      - ./promtail-config.yml:/etc/promtail/config.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock
    command: -config.file=/etc/promtail/config.yml
    networks:
      - internal
    restart: unless-stopped

volumes:
  loki-data:
```

### Loki Configuration

Create `monitoring/loki-config.yml`:

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1

schema_config:
  configs:
    - from: 2023-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h
```

### Promtail Configuration

Create `monitoring/promtail-config.yml`:

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: containers
    static_configs:
      - targets:
          - localhost
        labels:
          job: containerlogs
          __path__: /var/lib/docker/containers/*/*log

    pipeline_stages:
      - json:
          expressions:
            output: log
            stream: stream
            attrs:
      - json:
          expressions:
            tag:
          source: attrs
      - regex:
          expression: (?P<container_name>(?:[^|]*))\|(?P<image_tag>(?:[^|]*))
          source: tag
      - timestamp:
          format: RFC3339Nano
          source: time
      - labels:
          stream:
          container_name:
          image_tag:
      - output:
          source: output
```

## Distributed Tracing

### Deploy Jaeger

```yaml
services:
  jaeger:
    image: jaegertracing/all-in-one:1.47
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "16686:16686"  # Jaeger UI
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
    networks:
      - internal
      - public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.jaeger.rule=Host(`jaeger.${DOMAIN}`)"
      - "traefik.http.routers.jaeger.tls=true"
      - "traefik.http.services.jaeger.loadbalancer.server.port=16686"
    restart: unless-stopped
```

### Enable Tracing in Services

Configure services for OpenTelemetry:

```yaml
# docker-compose.override.yml
services:
  auth:
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
      - OTEL_SERVICE_NAME=auth-service
      - OTEL_TRACES_EXPORTER=otlp
      - ENABLE_TRACING=true
```

## Alerting

### Alert Rules

Create `monitoring/alerts/rules.yml`:

```yaml
groups:
  - name: mcp-oauth-alerts
    interval: 30s
    rules:
      # Service availability
      - alert: ServiceDown
        expr: up{job=~"auth-service|mcp-services"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"
          description: "{{ $labels.job }} has been down for more than 5 minutes"

      # High error rate
      - alert: HighErrorRate
        expr: |
          rate(mcp_oauth_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.service }}"
          description: "Error rate is {{ $value | humanizePercentage }} over last 5 minutes"

      # Token validation failures
      - alert: TokenValidationFailures
        expr: |
          rate(mcp_oauth_token_validations_total{result="failure"}[5m]) > 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High token validation failure rate"
          description: "{{ $value | humanizePercentage }} of tokens are failing validation"

      # Redis connection issues
      - alert: RedisConnectionFailure
        expr: |
          redis_up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Redis connection failure"
          description: "Cannot connect to Redis instance"

      # Certificate expiry
      - alert: CertificateExpiringSoon
        expr: |
          traefik_tls_certs_not_after - time() < 7 * 24 * 3600
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Certificate expiring soon"
          description: "Certificate for {{ $labels.domain }} expires in {{ $value | humanizeDuration }}"

      # High memory usage
      - alert: HighMemoryUsage
        expr: |
          container_memory_usage_bytes{name=~"mcp-oauth.*"}
          / container_spec_memory_limit_bytes > 0.9
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage in {{ $labels.name }}"
          description: "Memory usage is {{ $value | humanizePercentage }} of limit"
```

### AlertManager Configuration

Deploy AlertManager:

```yaml
services:
  alertmanager:
    image: prom/alertmanager:v0.25.0
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager-data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    networks:
      - internal
    ports:
      - "9093:9093"
    restart: unless-stopped

volumes:
  alertmanager-data:
```

Configure `monitoring/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'team-notifications'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'team-notifications'
    email_configs:
      - to: 'platform-team@company.com'
        from: 'alerts@company.com'
        smarthost: 'smtp.company.com:587'
        auth_username: 'alerts@company.com'
        auth_password: '${SMTP_PASSWORD}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_SERVICE_KEY}'

  - name: 'slack'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#mcp-oauth-alerts'
```

## Monitoring Commands

### Just Commands

```bash
# Deploy monitoring stack
just monitoring-up

# View metrics
just metrics

# View logs
just logs -f

# Check alerts
just alerts

# Monitoring dashboard
just monitoring-dashboard
```

### Direct Access

```bash
# Prometheus
open http://localhost:9090

# Grafana
open https://grafana.${DOMAIN}

# Jaeger
open https://jaeger.${DOMAIN}

# AlertManager
open http://localhost:9093
```

## Custom Metrics

### Adding Service Metrics

Example Python metrics:

```python
from prometheus_client import Counter, Histogram, Gauge

# Request counter
request_counter = Counter(
    'mcp_oauth_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

# Request duration
request_duration = Histogram(
    'mcp_oauth_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

# Active sessions
active_sessions = Gauge(
    'mcp_oauth_active_sessions',
    'Number of active sessions',
    ['service']
)
```

### Traefik Metrics

Traefik exposes built-in metrics:

```
traefik_service_requests_total
traefik_service_request_duration_seconds
traefik_service_open_connections
traefik_entrypoint_requests_total
traefik_tls_certs_not_after
```

## Monitoring Best Practices

### Metrics

1. **Use standard naming** - Follow Prometheus conventions
2. **Add meaningful labels** - But not too many (cardinality)
3. **Track business metrics** - Not just technical ones
4. **Set up recording rules** - For expensive queries
5. **Export custom metrics** - From your services

### Logging

1. **Structure logs as JSON** - For better parsing
2. **Include correlation IDs** - For request tracing
3. **Log at appropriate levels** - INFO for production
4. **Centralize all logs** - No local log files
5. **Set retention policies** - Balance cost vs history

### Alerting

1. **Alert on symptoms** - Not causes
2. **Avoid alert fatigue** - Only actionable alerts
3. **Include runbook links** - In alert descriptions
4. **Test alerts regularly** - Ensure they work
5. **Have escalation paths** - For critical issues

## Troubleshooting Monitoring

### Metrics Not Appearing

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify service metrics endpoint
just exec auth curl http://localhost:8000/metrics

# Check Prometheus logs
just logs prometheus | grep error
```

### High Cardinality Issues

```bash
# Find high cardinality metrics
curl -G http://localhost:9090/api/v1/label/__name__/values | jq '. | length'

# Check series count
curl http://localhost:9090/api/v1/query?query=prometheus_tsdb_symbol_table_size_bytes
```

### Log Volume Issues

```bash
# Check log volume
just exec promtail du -sh /var/lib/docker/containers

# Adjust log rotation
# In docker-compose.yml:
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## Next Steps

With monitoring configured:

1. **Create dashboards** → Visualize your metrics
2. **Set up alerts** → Get notified of issues
3. **Review regularly** → Improve based on data
4. **Troubleshoot issues** → [Troubleshooting Guide](troubleshooting)

---

*Remember: In production, you are blind without monitoring. Set it up properly, and you shall see all, know all, and fix issues before users notice!* 📊⚡
