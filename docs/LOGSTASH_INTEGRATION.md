# Logstash Integration Guide

## Overview

This guide covers the Logstash integration for forwarding validated log data to the ELK stack. The implementation includes:

- **Dual-Path Ingestion**: Logstash forwarding (primary) with Elasticsearch direct ingestion (fallback)
- **Connection Management**: Automatic reconnection with configurable retry logic
- **Protocol Support**: TCP (reliable) and UDP (fast) options
- **Monitoring**: Real-time statistics and health checks
- **Batch Processing**: Efficient bulk sending with configurable batch sizes

## Architecture

```
┌──────────────┐      ┌─────────────────┐      ┌───────────────┐      ┌──────────────┐
│   Backend    │─────▶│ Logstash        │─────▶│ Elasticsearch │◀────▶│   Kibana     │
│   (Django)   │ TCP  │ Forwarder       │ HTTP │   Cluster     │      │  Dashboard   │
└──────────────┘      └─────────────────┘      └───────────────┘      └──────────────┘
       │                      │
       │ Fallback             │ Filters & Enrichment
       │ (Direct ES)          │ - Normalization
       ▼                      │ - GeoIP
┌──────────────┐              │ - Tagging
│ Elasticsearch│              │ - Tenant routing
└──────────────┘              ▼
                      Monthly Indices per Tenant
                      logs-{tenant}-YYYY.MM
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Logstash Connection
LOGSTASH_HOST=logstash
LOGSTASH_PORT=5000
LOGSTASH_PROTOCOL=tcp  # tcp or udp

# Connection Settings
LOGSTASH_TIMEOUT=5
LOGSTASH_MAX_RETRIES=3
LOGSTASH_RETRY_DELAY=2

# Batch Settings
LOGSTASH_BATCH_SIZE=100

# Ingestion Method
USE_LOGSTASH=True  # True: Use Logstash, False: Direct Elasticsearch
```

### Django Settings

Settings are automatically loaded in `backend/config/settings.py`:

```python
# Logstash Configuration
LOGSTASH_HOST = config('LOGSTASH_HOST', default='logstash')
LOGSTASH_PORT = config('LOGSTASH_PORT', default=5000, cast=int)
LOGSTASH_PROTOCOL = config('LOGSTASH_PROTOCOL', default='tcp')
LOGSTASH_TIMEOUT = config('LOGSTASH_TIMEOUT', default=5, cast=int)
LOGSTASH_MAX_RETRIES = config('LOGSTASH_MAX_RETRIES', default=3, cast=int)
LOGSTASH_RETRY_DELAY = config('LOGSTASH_RETRY_DELAY', default=2, cast=int)
LOGSTASH_BATCH_SIZE = config('LOGSTASH_BATCH_SIZE', default=100, cast=int)
USE_LOGSTASH = config('USE_LOGSTASH', default=True, cast=bool)
```

## Usage

### Automatic Log Forwarding

Log uploads are automatically forwarded to Logstash via the Celery task:

```python
# Upload a log file
POST /api/v1/logs/upload/
Content-Type: multipart/form-data

file: logs.json
source: myapp
environment: production
service_name: api-service
```

The system will:
1. Validate the file
2. Parse the logs
3. Forward to Logstash (or direct ES if configured)
4. Return task ID for status tracking

### Programmatic Usage

#### Using the Logstash Forwarder

```python
from app.logs.logstash_forwarder import get_logstash_forwarder

# Get singleton instance
forwarder = get_logstash_forwarder()

# Send single log
log_entry = {
    '@timestamp': '2025-11-24T10:30:00Z',
    'message': 'User login successful',
    'level': 'INFO',
    'service_name': 'auth-service',
    'tenant_id': 'acme-corp',
    'user_id': 12345
}

success = forwarder.send_log(log_entry)

# Send multiple logs
logs = [...]
success = forwarder.send_logs(logs)

# Send in batches
result = forwarder.send_batch(logs, batch_size=100)
print(f"Sent: {result['sent']}, Failed: {result['failed']}")
```

#### Context Manager

```python
from app.logs.logstash_forwarder import LogstashForwarder

with LogstashForwarder(host='logstash', port=5000) as forwarder:
    forwarder.send_log({
        'message': 'Important event',
        'level': 'ERROR'
    })
# Connection automatically closed
```

## Monitoring

### Health Check Endpoint

Check Logstash connection health:

```bash
GET /api/v1/logs/logstash/monitor/
Authorization: Bearer <token>
```

**Response:**

```json
{
  "health": {
    "status": "healthy",
    "connected": true,
    "host": "logstash",
    "port": 5000,
    "protocol": "tcp"
  },
  "statistics": {
    "total_sent": 15234,
    "total_failed": 12,
    "total_retries": 8,
    "success_rate": 0.9992,
    "last_error": null,
    "last_success": "2025-11-24 14:30:45"
  },
  "configuration": {
    "host": "logstash",
    "port": 5000,
    "protocol": "tcp",
    "timeout": 5,
    "max_retries": 3,
    "retry_delay": 2,
    "enabled": true
  }
}
```

### Send Test Message

```bash
POST /api/v1/logs/logstash/monitor/
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Test from monitoring",
  "timestamp": "2025-11-24T10:30:00Z"
}
```

### Reset Statistics

```bash
DELETE /api/v1/logs/logstash/monitor/
Authorization: Bearer <token>
```

## Logstash Pipeline Configuration

### Input Configuration

The pipeline accepts logs via multiple inputs:

```properties
input {
  # TCP (reliable, primary)
  tcp {
    port => 5000
    codec => json_lines
    type => "backend"
  }
  
  # UDP (fast, alternative)
  udp {
    port => 5001
    codec => json_lines
    type => "backend_udp"
  }
  
  # Beats (for external shippers)
  beats {
    port => 5044
    type => "beats"
  }
}
```

### Filter Pipeline

Logs are enriched and normalized:

1. **Timestamp Parsing**: ISO8601 format
2. **Level Normalization**: Uppercase conversion
3. **Tenant Routing**: Dynamic index creation
4. **Service Tagging**: Tag by service name
5. **Environment Tagging**: Tag by environment
6. **JSON Parsing**: Extract structured data
7. **GeoIP Enrichment**: Add location data
8. **Metadata Addition**: Processing timestamps

### Output Configuration

Logs are indexed in Elasticsearch:

```properties
output {
  elasticsearch {
    hosts => ["http://elasticsearch:9200"]
    index => "logs-%{[@metadata][tenant]}-%{+YYYY.MM}"
    http_compression => true
  }
}
```

**Index Naming:**
- Pattern: `logs-{tenant_id}-YYYY.MM`
- Examples:
  - `logs-acme-corp-2025.11`
  - `logs-default-2025.11`
  - `logs-beta-customer-2025.12`

## Retry Logic

### Automatic Retries

The forwarder implements exponential backoff:

```
Attempt 1: Immediate
Attempt 2: Wait 2 seconds
Attempt 3: Wait 2 seconds
Attempt 4: Wait 2 seconds
```

### Configuration

```python
forwarder = LogstashForwarder(
    host='logstash',
    port=5000,
    max_retries=3,        # Number of retry attempts
    retry_delay=2         # Delay between retries (seconds)
)
```

### Celery Task Retries

Tasks also have their own retry mechanism:

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_and_ingest_logs(self, content, format_type, metadata):
    # If forwarding fails, Celery will retry
    pass
```

## Error Handling

### Connection Errors

```python
try:
    forwarder.send_log(log_entry)
except ConnectionError:
    # Automatic retry triggered
    # Falls back to Elasticsearch if all retries fail
    pass
```

### Failed Logs

Failed logs are tracked in statistics:

```python
stats = forwarder.get_statistics()
print(f"Failed: {stats['total_failed']}")
print(f"Last error: {stats['last_error']}")
```

## Performance Tuning

### Batch Sizing

Adjust batch size based on your needs:

```bash
# Small batches (better for real-time)
LOGSTASH_BATCH_SIZE=50

# Medium batches (balanced)
LOGSTASH_BATCH_SIZE=100

# Large batches (better throughput)
LOGSTASH_BATCH_SIZE=500
```

### Protocol Selection

**TCP (Default):**
- ✅ Reliable delivery
- ✅ Error detection
- ❌ Slightly slower

**UDP:**
- ✅ Faster
- ✅ Lower overhead
- ❌ No delivery guarantee

```bash
# Use TCP for critical logs
LOGSTASH_PROTOCOL=tcp

# Use UDP for high-volume, non-critical logs
LOGSTASH_PROTOCOL=udp
```

### Connection Pooling

For high throughput, consider connection reuse:

```python
# Singleton pattern (default)
forwarder = get_logstash_forwarder()

# Multiple sends reuse the same connection
forwarder.send_logs(batch1)
forwarder.send_logs(batch2)
forwarder.send_logs(batch3)
```

## Troubleshooting

### Connection Refused

**Problem:** `ConnectionRefusedError: [Errno 111] Connection refused`

**Solutions:**
1. Check Logstash is running: `docker-compose ps logstash`
2. Verify port mapping: `docker-compose port logstash 5000`
3. Check firewall rules
4. Verify LOGSTASH_HOST and LOGSTASH_PORT settings

### Timeout Errors

**Problem:** `socket.timeout: timed out`

**Solutions:**
1. Increase timeout: `LOGSTASH_TIMEOUT=10`
2. Check network latency
3. Verify Logstash isn't overloaded
4. Consider switching to UDP for non-critical logs

### Logs Not Appearing in Elasticsearch

**Problem:** Logs sent successfully but not in Elasticsearch

**Solutions:**
1. Check Logstash logs: `docker-compose logs logstash`
2. Verify Elasticsearch is running: `curl http://localhost:9200/_cluster/health`
3. Check pipeline configuration in `infra/logstash/pipeline/logstash.conf`
4. Look for parsing errors in Logstash output

### High Failure Rate

**Problem:** `success_rate` is low in statistics

**Solutions:**
1. Check Logstash health: `GET /api/v1/logs/logstash/monitor/`
2. Review last_error in statistics
3. Increase retry attempts: `LOGSTASH_MAX_RETRIES=5`
4. Consider switching to direct Elasticsearch: `USE_LOGSTASH=False`

## Fallback Strategy

If Logstash is unavailable, the system automatically falls back to direct Elasticsearch ingestion:

```python
# In tasks.py
use_logstash = getattr(settings, 'USE_LOGSTASH', True)

if use_logstash:
    result = forward_to_logstash(task_id, parsed_entries, metadata)
else:
    result = ingest_to_elasticsearch(task_id, parsed_entries, metadata)
```

### Manual Fallback

```bash
# Temporarily disable Logstash
USE_LOGSTASH=False

# System will use direct Elasticsearch ingestion
```

## Integration Examples

### Python Application

```python
import requests

# Upload logs via API
files = {'file': open('app.log', 'rb')}
data = {
    'source': 'python-app',
    'environment': 'production',
    'service_name': 'worker'
}

response = requests.post(
    'http://localhost:8000/api/v1/logs/upload/',
    headers={'Authorization': 'Bearer <token>'},
    files=files,
    data=data
)

task_id = response.json()['task_id']
```

### Real-time Streaming

```python
from app.logs.logstash_forwarder import get_logstash_forwarder
import time

forwarder = get_logstash_forwarder()

# Stream logs in real-time
for log_line in tail_log_file('/var/log/app.log'):
    forwarder.send_log({
        '@timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'message': log_line,
        'source': 'app-server',
        'level': 'INFO'
    })
```

## Security Considerations

### Network Security

1. **TLS/SSL**: Enable in production
2. **Firewall Rules**: Restrict Logstash port access
3. **VPC Isolation**: Keep Logstash in private network

### Authentication

```properties
# Logstash output with auth
output {
  elasticsearch {
    hosts => ["https://elasticsearch:9200"]
    user => "logstash_writer"
    password => "${LOGSTASH_ES_PASSWORD}"
    ssl => true
    cacert => "/path/to/ca.crt"
  }
}
```

### Data Validation

All logs are validated before forwarding:
- File size limits (50MB)
- Format validation
- UTF-8 encoding check
- Structure validation

## Best Practices

1. **Use TCP for production**: Reliable delivery for critical logs
2. **Monitor statistics**: Check success rate regularly
3. **Set up alerts**: Alert on high failure rates
4. **Batch appropriately**: Balance throughput vs. latency
5. **Use tenant isolation**: Ensure proper multi-tenancy
6. **Enable compression**: Use `http_compression => true` in Logstash output
7. **Configure retention**: Set up index lifecycle management
8. **Test failover**: Verify fallback to Elasticsearch works

## API Reference

See [LOG_UPLOAD_API.md](./LOG_UPLOAD_API.md) for complete API documentation.

## Support

For issues or questions:
1. Check Logstash logs: `docker-compose logs logstash`
2. Review monitoring endpoint: `GET /api/v1/logs/logstash/monitor/`
3. Check system logs: `backend/logs/app.log`
4. Verify configuration: Review `.env` file
