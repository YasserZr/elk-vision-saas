# Monitoring Stack Guide for ELK Vision SaaS

Complete guide for setting up and using Prometheus and Grafana monitoring.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Components](#components)
- [Dashboards](#dashboards)
- [Alerting](#alerting)
- [Custom Metrics](#custom-metrics)
- [Troubleshooting](#troubleshooting)

---

## Overview

The monitoring stack provides comprehensive observability for the ELK Vision SaaS platform:

- **Prometheus**: Time-series database for metrics collection
- **Grafana**: Visualization and dashboarding
- **Alertmanager**: Alert management and routing
- **Exporters**: Metrics exporters for each service

### Key Features

- Real-time infrastructure and application monitoring
- Custom Django application metrics
- Database performance monitoring
- Container resource tracking
- Automated alerting with multiple notification channels
- Pre-built dashboards for common use cases

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Monitoring Stack                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   Grafana   │────▶│  Prometheus │────▶│ Alertmanager│       │
│  │   (3001)    │     │   (9090)    │     │   (9093)    │       │
│  └─────────────┘     └──────┬──────┘     └──────┬──────┘       │
│                             │                    │               │
│         ┌───────────────────┼────────────────────┘               │
│         │                   │                                    │
│         ▼                   ▼                                    │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   Email     │     │   Slack     │     │  PagerDuty  │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                         Exporters                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Node    │ │ cAdvisor │ │ Postgres │ │ MongoDB  │           │
│  │ Exporter │ │          │ │ Exporter │ │ Exporter │           │
│  │  (9100)  │ │  (8080)  │ │  (9187)  │ │  (9216)  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Redis   │ │ Elastic  │ │  Nginx   │ │ Blackbox │           │
│  │ Exporter │ │ Exporter │ │ Exporter │ │ Exporter │           │
│  │  (9121)  │ │  (9114)  │ │  (9113)  │ │  (9115)  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                    Application Services                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Django  │ │ Postgres │ │ MongoDB  │ │  Redis   │           │
│  │ Backend  │ │          │ │          │ │          │           │
│  │  (8000)  │ │  (5432)  │ │ (27017)  │ │  (6379)  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Elastic  │ │ Logstash │ │  Kibana  │ │  Nginx   │           │
│  │  search  │ │          │ │          │ │          │           │
│  │  (9200)  │ │  (5044)  │ │  (5601)  │ │   (80)   │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Start the Monitoring Stack

```powershell
# Start all services including monitoring
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Or just the monitoring stack (after main services are running)
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. Access the Dashboards

| Service      | URL                           | Default Credentials    |
|--------------|-------------------------------|------------------------|
| Grafana      | http://localhost:3001/grafana | admin / admin123       |
| Prometheus   | http://localhost:9090         | N/A                    |
| Alertmanager | http://localhost:9093         | N/A                    |

### 3. Configure Django

Add to your Django settings:

```python
# settings.py

MIDDLEWARE = [
    # ... other middleware ...
    'api.middleware.prometheus_middleware.PrometheusMetricsMiddleware',
]

# Add to requirements.txt
# prometheus-client==0.18.0
```

Add URL routes:

```python
# urls.py

from django.urls import path, include

urlpatterns = [
    # ... other urls ...
    path('', include('api.metrics_urls')),
]
```

### 4. Verify Installation

```powershell
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Check Django metrics
curl http://localhost:8000/metrics/

# Check Grafana health
curl http://localhost:3001/api/health
```

---

## Components

### Prometheus

**Purpose**: Metrics collection and storage

**Configuration**: [monitoring/prometheus/prometheus.yml](monitoring/prometheus/prometheus.yml)

**Key Settings**:
- Scrape interval: 15s
- Retention: 30 days / 10GB
- Multiple scrape targets configured

**Endpoints**:
- `/api/v1/query` - Execute PromQL queries
- `/api/v1/targets` - List scrape targets
- `/api/v1/alerts` - List active alerts
- `/-/healthy` - Health check

### Grafana

**Purpose**: Visualization and dashboarding

**Configuration**: [monitoring/grafana/grafana.ini](monitoring/grafana/grafana.ini)

**Pre-configured**:
- Prometheus data source
- Elasticsearch data source
- PostgreSQL data source
- Custom dashboards

**Plugins Installed**:
- grafana-clock-panel
- grafana-piechart-panel
- redis-datasource
- yesoreyeram-infinity-datasource

### Alertmanager

**Purpose**: Alert routing and notifications

**Configuration**: [monitoring/alertmanager/alertmanager.yml](monitoring/alertmanager/alertmanager.yml)

**Notification Channels**:
- Email (SMTP)
- Slack
- PagerDuty (optional)

**Routing**:
- Critical alerts → PagerDuty + Slack + Email
- Warning alerts → Slack + Email
- Database alerts → DBA team
- Application alerts → Dev team

### Exporters

| Exporter              | Purpose                           | Port  |
|-----------------------|-----------------------------------|-------|
| node-exporter         | Host system metrics               | 9100  |
| cadvisor              | Container metrics                 | 8080  |
| postgres-exporter     | PostgreSQL metrics                | 9187  |
| mongodb-exporter      | MongoDB metrics                   | 9216  |
| redis-exporter        | Redis metrics                     | 9121  |
| elasticsearch-exporter| Elasticsearch metrics             | 9114  |
| nginx-exporter        | Nginx metrics                     | 9113  |
| blackbox-exporter     | HTTP/TCP/DNS probes               | 9115  |

---

## Dashboards

### Pre-built Dashboards

#### 1. ELK Vision - Main Dashboard

**File**: [monitoring/grafana/dashboards/elk-vision-main.json](monitoring/grafana/dashboards/elk-vision-main.json)

**Sections**:
- Service Status Overview
- Request Rate and Latency
- Error Rate Tracking
- Celery Queue Status
- WebSocket Connections
- Infrastructure Metrics (CPU, Memory, Disk)
- Database Connections

#### 2. Import Community Dashboards

Import these popular dashboards from Grafana.com:

```
# Node Exporter Full
Dashboard ID: 1860

# Docker Container Monitoring
Dashboard ID: 893

# PostgreSQL Database
Dashboard ID: 9628

# MongoDB Overview
Dashboard ID: 2583

# Redis Dashboard
Dashboard ID: 763

# Nginx Metrics
Dashboard ID: 12708

# Elasticsearch Metrics
Dashboard ID: 4358
```

### Create Custom Dashboard

1. Go to Grafana → Create → Dashboard
2. Add a new panel
3. Select data source (Prometheus)
4. Write PromQL query:

```promql
# Request rate
sum(rate(django_http_requests_total[5m]))

# Error rate
sum(rate(django_http_responses_total_by_status_total{status=~"5.."}[5m])) 
/ sum(rate(django_http_responses_total_by_status_total[5m])) * 100

# P95 latency
histogram_quantile(0.95, sum(rate(django_http_requests_latency_seconds_bucket[5m])) by (le))

# Active WebSocket connections
sum(django_websocket_connections_active)
```

---

## Alerting

### Alert Rules

Alert rules are defined in [monitoring/prometheus/rules/alerts.yml](monitoring/prometheus/rules/alerts.yml).

**Categories**:

1. **Infrastructure Alerts**
   - High CPU usage (>80%, >95%)
   - High memory usage (>85%, >95%)
   - High disk usage (>80%, >90%)

2. **Container Alerts**
   - Container down
   - Container high CPU/memory
   - Container restarts

3. **Application Alerts**
   - Backend service down
   - High response time (>2s)
   - High error rate (>5%, >10%)
   - Celery queue backlog

4. **Database Alerts**
   - PostgreSQL/MongoDB/Redis down
   - High connection usage
   - Replication lag

5. **Elasticsearch Alerts**
   - Cluster health yellow/red
   - High heap usage
   - High disk usage

6. **SSL Alerts**
   - Certificate expiring (30 days, 7 days)

### Configure Notifications

#### Slack Integration

1. Create a Slack App: https://api.slack.com/apps
2. Enable Incoming Webhooks
3. Add webhook URL to `.env`:

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
```

4. Restart Alertmanager

#### Email (SMTP)

Add to `.env`:

```bash
SMTP_HOST=smtp.gmail.com:587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

#### PagerDuty

1. Create a PagerDuty service
2. Add integration key to `.env`:

```bash
PAGERDUTY_SERVICE_KEY=your-integration-key
```

### Test Alerts

```powershell
# Send test alert to Alertmanager
$body = @{
    alerts = @(
        @{
            labels = @{
                alertname = "TestAlert"
                severity = "warning"
            }
            annotations = @{
                summary = "This is a test alert"
                description = "Testing alert notification"
            }
        }
    )
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Method Post -Uri "http://localhost:9093/api/v2/alerts" -Body $body -ContentType "application/json"
```

---

## Custom Metrics

### Adding Custom Metrics to Django

```python
# In your Django view or service
from api.metrics import (
    increment_log_processed,
    increment_alert_triggered,
    track_file_upload,
    track_request_metrics,
    track_celery_task,
)

# Track log processing
increment_log_processed(source='api', level='error')

# Track alert
increment_alert_triggered(severity='critical', alert_type='threshold')

# Track file upload
track_file_upload(status='success', file_type='log', size_bytes=1024000)

# Use decorator for views
@track_request_metrics(view_name='upload_logs')
def upload_logs(request):
    # Your view logic
    pass

# Use decorator for Celery tasks
@track_celery_task(task_name='process_logs')
def process_logs_task():
    # Your task logic
    pass
```

### Custom PromQL Queries

```promql
# Logs processed per minute by level
sum by(level) (rate(django_logs_processed_total[1m])) * 60

# Average file upload size
avg(django_file_upload_size_bytes)

# Alert trigger rate by severity
sum by(severity) (rate(django_alerts_triggered_total[1h]))

# Celery task success rate
sum(rate(django_celery_tasks_total{status="success"}[5m])) 
/ sum(rate(django_celery_tasks_total[5m])) * 100

# Top 5 slowest endpoints
topk(5, avg by(view) (django_http_requests_latency_seconds))
```

---

## Troubleshooting

### Common Issues

#### Prometheus Target Down

```powershell
# Check target status
curl http://localhost:9090/api/v1/targets

# Check if service is running
docker-compose ps

# Check exporter logs
docker-compose logs postgres-exporter
```

#### Grafana Dashboard Not Loading

```powershell
# Check Grafana logs
docker-compose logs grafana

# Verify data source connection
curl -u admin:admin123 http://localhost:3001/api/datasources

# Test Prometheus query
curl "http://localhost:9090/api/v1/query?query=up"
```

#### Alerts Not Firing

```powershell
# Check Prometheus alerts
curl http://localhost:9090/api/v1/alerts

# Check Alertmanager status
curl http://localhost:9093/api/v1/status

# Check alert rules
curl http://localhost:9090/api/v1/rules
```

#### High Memory Usage

```powershell
# Check Prometheus memory
docker stats elk_prometheus

# Reduce retention
# Edit prometheus.yml:
# --storage.tsdb.retention.time=15d
# --storage.tsdb.retention.size=5GB
```

### Useful Commands

```powershell
# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload

# Reload Alertmanager configuration
curl -X POST http://localhost:9093/-/reload

# Check Prometheus config
docker-compose exec prometheus promtool check config /etc/prometheus/prometheus.yml

# Check alert rules syntax
docker-compose exec prometheus promtool check rules /etc/prometheus/rules/alerts.yml

# Query Prometheus
curl "http://localhost:9090/api/v1/query?query=up{job='django-backend'}"

# Silence alerts temporarily
curl -X POST http://localhost:9093/api/v1/silences -d '{
  "matchers": [{"name": "alertname", "value": "HighCPUUsage"}],
  "startsAt": "2025-01-01T00:00:00Z",
  "endsAt": "2025-01-01T01:00:00Z",
  "createdBy": "admin",
  "comment": "Scheduled maintenance"
}'
```

---

## Environment Variables

Add these to your `.env` file:

```bash
# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin123
GRAFANA_SECRET_KEY=your-secret-key

# Alertmanager - Email
SMTP_HOST=smtp.gmail.com:587
SMTP_USER=alerts@yourdomain.com
SMTP_PASSWORD=your-app-password

# Alertmanager - Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
SLACK_BOT_TOKEN=xoxb-your-token

# Alertmanager - PagerDuty (optional)
PAGERDUTY_SERVICE_KEY=your-service-key

# Database passwords for exporters
POSTGRES_PASSWORD=postgres123
MONGO_PASSWORD=password
REDIS_PASSWORD=redis123
ELASTICSEARCH_PASSWORD=changeme
```

---

## Production Checklist

- [ ] Change default Grafana admin password
- [ ] Set secure Grafana secret key
- [ ] Configure SSL/TLS for all endpoints
- [ ] Set up network policies to restrict access
- [ ] Configure appropriate retention periods
- [ ] Set up external alerting (PagerDuty, OpsGenie)
- [ ] Create on-call schedules
- [ ] Document runbooks for each alert
- [ ] Set up backup for Prometheus data
- [ ] Configure high availability (if needed)
- [ ] Review and tune alert thresholds
- [ ] Set up escalation policies
- [ ] Test disaster recovery procedures

---

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)
