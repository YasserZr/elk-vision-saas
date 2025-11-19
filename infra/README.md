# Infrastructure - Docker & Services

Docker Compose orchestration for all ELK Vision SaaS services.

## Services

### Core Services

1. **Elasticsearch** (Port 9200, 9300)
   - Search and analytics engine
   - Stores all log data
   - Configured for single-node development

2. **Logstash** (Ports 5000, 5044, 9600)
   - Log processing pipeline
   - Receives logs from various sources
   - Parses and enriches log data
   - Sends to Elasticsearch

3. **Kibana** (Port 5601)
   - Elasticsearch visualization
   - Optional admin interface
   - Access at http://localhost:5601

4. **MongoDB** (Port 27017)
   - Primary operational database
   - Stores users, dashboards, alerts
   - Configured with authentication

5. **Redis** (Port 6379)
   - Caching layer
   - Celery message broker
   - Session storage

### Application Services

6. **Backend** (Port 8000)
   - Django REST API
   - Auto-migrates on startup
   - Connected to all data stores

7. **Celery Worker**
   - Background task processing
   - Alert notifications
   - Report generation

8. **Frontend** (Port 3000)
   - Next.js React application
   - Development mode with hot reload

9. **Nginx** (Port 80)
   - Reverse proxy
   - Load balancer
   - Routes traffic to services

## Quick Start

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Service Management

```bash
# Start specific service
docker-compose up -d elasticsearch

# Restart service
docker-compose restart backend

# View service logs
docker-compose logs -f backend

# Scale service
docker-compose up -d --scale celery-worker=3

# Execute command in service
docker-compose exec backend python manage.py createsuperuser
```

## Health Checks

All critical services have health checks:

```bash
# Check service status
docker-compose ps

# View specific service health
docker inspect elk-elasticsearch | grep Health -A 10
```

## Volumes

Persistent data is stored in Docker volumes:

- `elasticsearch-data` - Elasticsearch indices
- `mongodb-data` - MongoDB database files
- `redis-data` - Redis persistence

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect elk-vision-saas_elasticsearch-data

# Remove all volumes (WARNING: data loss)
docker-compose down -v
```

## Networking

All services communicate over the `elk-network` bridge network.

```bash
# Inspect network
docker network inspect elk-vision-saas_elk-network

# View connected containers
docker network inspect elk-vision-saas_elk-network | grep Name
```

## Configuration Files

### Logstash Pipeline

`logstash/pipeline/logstash.conf` - Log processing configuration
- Input: TCP (5000), Beats (5044)
- Filter: JSON parsing, timestamp, GeoIP
- Output: Elasticsearch

### Nginx

`nginx/nginx.conf` - Reverse proxy configuration
- Frontend traffic -> Next.js (3000)
- API traffic -> Django (8000)
- Kibana access -> Kibana (5601)

## Environment Variables

Services can be configured via environment variables in `docker-compose.yaml` or separate `.env` file.

### Critical Variables

```env
# MongoDB
MONGO_USER=admin
MONGO_PASSWORD=password
MONGO_DB_NAME=elk_vision

# Backend
SECRET_KEY=your-secret-key
DEBUG=True

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs service-name

# Rebuild container
docker-compose build --no-cache service-name
docker-compose up -d service-name
```

### Elasticsearch Issues

```bash
# Check memory
docker stats elk-elasticsearch

# Increase memory in docker-compose.yaml
# ES_JAVA_OPTS=-Xms1g -Xmx1g
```

### MongoDB Connection Issues

```bash
# Test MongoDB connection
docker-compose exec mongodb mongosh -u admin -p password

# Check if database exists
docker-compose exec mongodb mongosh -u admin -p password --eval "show dbs"
```

### Backend Migration Issues

```bash
# Run migrations manually
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

## Production Deployment

For production, consider:

1. **Use Kubernetes** instead of Docker Compose
2. **External managed services** for databases
3. **Load balancers** with SSL termination
4. **Monitoring** with Prometheus/Grafana
5. **Backup strategies** for all data stores

### Production Checklist

- [ ] Remove development volumes
- [ ] Set proper resource limits
- [ ] Configure SSL certificates
- [ ] Use secrets management
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Implement logging aggregation
- [ ] Set up alerts for service health

## Monitoring

Add monitoring stack:

```yaml
# Add to docker-compose.yaml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana
  ports:
    - "3001:3000"
```

## Scaling Considerations

### Horizontal Scaling

```bash
# Scale backend API
docker-compose up -d --scale backend=3

# Scale Celery workers
docker-compose up -d --scale celery-worker=5
```

### Elasticsearch Cluster

For production, convert to multi-node cluster:
- 3 master-eligible nodes
- 2+ data nodes
- 1+ coordinating node
