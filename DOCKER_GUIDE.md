# Docker Compose Management Scripts

This directory contains scripts for managing the Docker Compose stack.

## Quick Start

### 1. Initial Setup

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 2. Service Management

```bash
# Start specific services
docker-compose up -d backend frontend

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v

# Restart a service
docker-compose restart backend

# View service status
docker-compose ps
```

### 3. Development vs Production

```bash
# Development mode (with hot reload)
BUILD_TARGET=development docker-compose up -d

# Production mode (optimized builds)
BUILD_TARGET=production docker-compose up -d
```

## Service URLs

After starting the stack, access services at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **Kibana**: http://localhost:5601
- **Elasticsearch**: http://localhost:9200
- **Flower (Celery Monitor)**: http://localhost:5555
- **Nginx (Reverse Proxy)**: http://localhost:80

## Common Tasks

### Run Database Migrations

```bash
docker-compose exec backend python manage.py migrate
```

### Create Django Superuser

```bash
docker-compose exec backend python manage.py createsuperuser
```

### Access Django Shell

```bash
docker-compose exec backend python manage.py shell
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Execute Commands

```bash
# Backend
docker-compose exec backend python manage.py <command>

# Frontend
docker-compose exec frontend npm run <command>

# MongoDB
docker-compose exec mongodb mongosh -u admin -p password

# Redis
docker-compose exec redis redis-cli -a redis123
```

### Backup & Restore

#### MongoDB Backup

```bash
# Backup
docker-compose exec mongodb mongodump --uri="mongodb://admin:password@localhost:27017/elk_vision" --out=/data/backup

# Restore
docker-compose exec mongodb mongorestore --uri="mongodb://admin:password@localhost:27017/elk_vision" /data/backup/elk_vision
```

#### PostgreSQL Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U postgres elk_vision > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres elk_vision < backup.sql
```

#### Elasticsearch Backup

```bash
# Create snapshot repository
curl -X PUT "localhost:9200/_snapshot/backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/usr/share/elasticsearch/backup"
  }
}'

# Create snapshot
curl -X PUT "localhost:9200/_snapshot/backup/snapshot_1?wait_for_completion=true"

# Restore snapshot
curl -X POST "localhost:9200/_snapshot/backup/snapshot_1/_restore"
```

## Troubleshooting

### Service Won't Start

1. Check logs: `docker-compose logs <service>`
2. Check if port is already in use: `netstat -tuln | grep <port>`
3. Verify environment variables: `docker-compose config`

### Permission Issues

```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix volume permissions
docker-compose exec backend chown -R www-data:www-data /app/media /app/staticfiles
```

### Clear Everything and Start Fresh

```bash
# Stop and remove everything
docker-compose down -v --remove-orphans

# Remove all images
docker-compose down --rmi all

# Rebuild and start
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Issues

```bash
# Check if databases are healthy
docker-compose ps

# Test MongoDB connection
docker-compose exec backend python -c "from pymongo import MongoClient; client = MongoClient('mongodb://admin:password@mongodb:27017/'); print(client.server_info())"

# Test PostgreSQL connection
docker-compose exec backend python manage.py dbshell
```

### WebSocket Issues

1. Check if Redis is running: `docker-compose ps redis`
2. Verify channel layers: `docker-compose exec backend python manage.py shell -c "from channels.layers import get_channel_layer; print(get_channel_layer())"`
3. Check Daphne logs: `docker-compose logs -f backend`

## Production Deployment

### Enable SSL with Let's Encrypt

1. Update `nginx/conf.d/default.conf` - uncomment HTTPS section
2. Set your domain name
3. Run Certbot:

```bash
# Install Certbot
docker run -it --rm -v ./certbot/conf:/etc/letsencrypt -v ./certbot/www:/var/www/certbot certbot/certbot certonly --webroot -w /var/www/certbot -d yourdomain.com -d www.yourdomain.com

# Reload Nginx
docker-compose exec nginx nginx -s reload
```

4. Set up auto-renewal:

```bash
# Add to crontab
0 0 * * * docker run --rm -v ./certbot/conf:/etc/letsencrypt -v ./certbot/www:/var/www/certbot certbot/certbot renew --quiet && docker-compose exec nginx nginx -s reload
```

### Performance Tuning

1. **Increase Elasticsearch heap size** (in `.env`):
   ```
   ES_JAVA_OPTS=-Xms2g -Xmx2g
   ```

2. **Scale services**:
   ```bash
   docker-compose up -d --scale celery_worker=4
   ```

3. **Enable Redis persistence**:
   ```bash
   # Edit docker-compose.yml redis command
   command: redis-server --appendonly yes --requirepass redis123
   ```

### Monitoring

1. **Container stats**:
   ```bash
   docker stats
   ```

2. **Resource usage**:
   ```bash
   docker-compose top
   ```

3. **Health checks**:
   ```bash
   docker-compose ps
   ```

## Network Architecture

```
┌─────────────┐
│   Nginx     │ :80, :443
│ (Reverse    │
│  Proxy)     │
└──────┬──────┘
       │
       ├─────────────────┬──────────────┬─────────────┐
       │                 │              │             │
┌──────▼──────┐  ┌───────▼─────┐ ┌─────▼─────┐ ┌────▼─────┐
│  Frontend   │  │   Backend   │ │  Kibana   │ │  Flower  │
│  (Next.js)  │  │  (Django)   │ │           │ │          │
│    :3000    │  │    :8000    │ │   :5601   │ │  :5555   │
└─────────────┘  └──────┬──────┘ └─────┬─────┘ └──────────┘
                        │              │
                        │              │
       ┌────────────────┼──────────────┼────────────┐
       │                │              │            │
┌──────▼──────┐  ┌──────▼──────┐ ┌────▼────┐ ┌────▼─────┐
│  PostgreSQL │  │   MongoDB   │ │  Redis  │ │  Elastic │
│    :5432    │  │   :27017    │ │  :6379  │ │   :9200  │
└─────────────┘  └─────────────┘ └─────────┘ └────┬─────┘
                                                    │
                                             ┌──────▼──────┐
                                             │  Logstash   │
                                             │    :5000    │
                                             └─────────────┘
```

## Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Generate strong `SECRET_KEY` for Django
- [ ] Enable HTTPS with SSL certificates
- [ ] Configure firewall rules
- [ ] Set up backup strategy
- [ ] Enable monitoring and alerting
- [ ] Review and restrict CORS settings
- [ ] Enable rate limiting
- [ ] Set up log rotation
- [ ] Regular security updates
