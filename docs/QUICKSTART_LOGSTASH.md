# Logstash Integration - Quick Start Guide

## Prerequisites

- Docker and Docker Compose installed
- Python 3.10+ installed
- Git repository cloned

## Installation Steps

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file from example:

```bash
cp .env.example .env
```

Edit `.env` and configure:
```bash
# Minimal required settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# Logstash Configuration
LOGSTASH_HOST=logstash
LOGSTASH_PORT=5000
LOGSTASH_PROTOCOL=tcp
USE_LOGSTASH=True
```

### 3. Start Infrastructure

Start all services (Elasticsearch, Logstash, MongoDB, Redis):

```bash
cd ../infra
docker-compose up -d
```

Wait for services to be healthy (~2 minutes):
```bash
docker-compose ps
```

### 4. Run Django Migrations

```bash
cd ../backend
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Start Celery Worker

In a new terminal:
```bash
cd backend
celery -A config worker -l info
```

### 7. Start Django Development Server

In another terminal:
```bash
cd backend
python manage.py runserver
```

## Testing the Integration

### 1. Get Authentication Token

```bash
# Login to get JWT token
curl -X POST http://localhost:8000/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

Save the `access` token from the response.

### 2. Check Logstash Health

```bash
curl -X GET http://localhost:8000/api/v1/logs/logstash/monitor/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Expected response:
```json
{
  "health": {
    "status": "healthy",
    "connected": true
  },
  "statistics": {
    "total_sent": 0,
    "total_failed": 0
  }
}
```

### 3. Send Test Log

```bash
curl -X POST http://localhost:8000/api/v1/logs/logstash/monitor/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test log from API"
  }'
```

### 4. Upload Log File

Create a test log file `test-logs.json`:
```json
[
  {"message": "Application started", "level": "INFO", "timestamp": "2025-11-24T10:00:00Z"},
  {"message": "User logged in", "level": "INFO", "timestamp": "2025-11-24T10:01:00Z"},
  {"message": "Error processing request", "level": "ERROR", "timestamp": "2025-11-24T10:02:00Z"}
]
```

Upload it:
```bash
curl -X POST http://localhost:8000/api/v1/logs/upload/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@test-logs.json" \
  -F "source=test" \
  -F "environment=development"
```

Save the `task_id` from response.

### 5. Check Upload Status

```bash
curl -X GET http://localhost:8000/api/v1/logs/upload/status/TASK_ID/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 6. Verify Logs in Elasticsearch

```bash
# Check indices
curl http://localhost:9200/_cat/indices?v

# Search logs
curl http://localhost:9200/logs-default-*/_search?pretty
```

### 7. View in Kibana

Open browser: http://localhost:5601

1. Go to Management → Stack Management → Index Patterns
2. Create index pattern: `logs-*`
3. Select `@timestamp` as time field
4. Go to Discover to view logs

## Running Tests

### Unit Tests

```bash
cd backend
pytest app/logs/test_logstash_forwarder.py -v
```

### Integration Tests

```bash
pytest app/logs/test_upload.py -v
```

### All Tests

```bash
pytest --cov=app/logs
```

## Troubleshooting

### Logstash Not Connected

**Error:** `"status": "unhealthy", "connected": false`

**Solutions:**
1. Check Logstash is running: `docker-compose ps logstash`
2. Check Logstash logs: `docker-compose logs logstash`
3. Verify port mapping: `docker-compose port logstash 5000`
4. Check firewall settings

### Connection Timeout

**Error:** `socket.timeout: timed out`

**Solutions:**
1. Increase timeout in `.env`: `LOGSTASH_TIMEOUT=10`
2. Check network latency: `ping logstash`
3. Verify Logstash isn't overloaded

### Logs Not Appearing

**Solutions:**
1. Check Celery worker is running: `ps aux | grep celery`
2. Check task status: `GET /api/v1/logs/upload/status/{task_id}/`
3. Check Logstash logs: `docker-compose logs -f logstash`
4. Verify Elasticsearch health: `curl http://localhost:9200/_cluster/health`

### Import Errors

**Error:** `Import "django.conf" could not be resolved`

**Solutions:**
1. Activate virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Restart IDE/editor

## Monitoring

### Real-time Monitoring

```bash
# Watch Logstash logs
docker-compose logs -f logstash

# Watch Celery tasks
# In terminal where celery is running

# Monitor Elasticsearch
watch -n 5 'curl -s http://localhost:9200/_cat/indices?v'
```

### Statistics Dashboard

Check monitoring endpoint periodically:
```bash
watch -n 10 'curl -s -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/logs/logstash/monitor/ | jq'
```

## Performance Tips

### For High Volume

1. **Increase batch size:**
   ```bash
   LOGSTASH_BATCH_SIZE=500
   ```

2. **Use UDP for non-critical logs:**
   ```bash
   LOGSTASH_PROTOCOL=udp
   ```

3. **Scale Celery workers:**
   ```bash
   celery -A config worker -l info --concurrency=4
   ```

4. **Enable Elasticsearch bulk settings:**
   - Edit `infra/logstash/pipeline/logstash.conf`
   - Adjust `bulk_size` and `flush_size`

### For Low Latency

1. **Reduce batch size:**
   ```bash
   LOGSTASH_BATCH_SIZE=10
   ```

2. **Use TCP protocol:**
   ```bash
   LOGSTASH_PROTOCOL=tcp
   ```

3. **Decrease retry delay:**
   ```bash
   LOGSTASH_RETRY_DELAY=1
   ```

## Configuration Profiles

### Development
```bash
DEBUG=True
LOGSTASH_PROTOCOL=tcp
LOGSTASH_BATCH_SIZE=50
LOG_LEVEL=DEBUG
```

### Production
```bash
DEBUG=False
LOGSTASH_PROTOCOL=tcp
LOGSTASH_BATCH_SIZE=500
LOG_LEVEL=INFO
SECURE_SSL_REDIRECT=True
```

### Testing
```bash
DEBUG=True
USE_LOGSTASH=False  # Use direct Elasticsearch
LOGSTASH_PROTOCOL=tcp
LOG_LEVEL=DEBUG
```

## Useful Commands

```bash
# Restart Logstash
docker-compose restart logstash

# View all logs
docker-compose logs

# Stop all services
docker-compose down

# Reset everything
docker-compose down -v
docker-compose up -d

# Check service health
docker-compose ps

# Execute shell in container
docker-compose exec logstash bash

# View Elasticsearch cluster info
curl http://localhost:9200/_cluster/health?pretty
```

## Documentation

- **Integration Guide:** `docs/LOGSTASH_INTEGRATION.md`
- **API Reference:** `docs/LOG_UPLOAD_API.md`
- **Implementation Summary:** `docs/IMPLEMENTATION_SUMMARY.md`

## Support

For issues or questions:
1. Check documentation in `docs/` folder
2. Review Logstash logs: `docker-compose logs logstash`
3. Check monitoring endpoint: `GET /api/v1/logs/logstash/monitor/`
4. Run tests: `pytest app/logs/ -v`

## Next Steps

After successful setup:
1. Configure index lifecycle management in Elasticsearch
2. Set up Kibana dashboards for log visualization
3. Configure alerts for high failure rates
4. Enable SSL/TLS for production
5. Set up log retention policies
