# ELK Vision SaaS

Enterprise-grade log monitoring and analytics platform powered by the ELK Stack, designed for real-time log ingestion, search, visualization, and alerting.

## Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Environment Configuration](#environment-configuration)
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)
- [Development Guidelines](#development-guidelines)
- [Deployment Notes](#deployment-notes)
- [Contribution Guide](#contribution-guide)
- [License & Credits](#license--credits)

---

## Project Overview

ELK Vision SaaS is a comprehensive log management platform that enables organizations to centralize, monitor, and analyze logs from multiple sources in real-time. Built on the proven ELK Stack (Elasticsearch, Logstash, Kibana) with modern web technologies, it provides a scalable solution for log aggregation, search, visualization, and alerting.

### Key Features

- **Real-Time Log Streaming**: Sub-second latency log delivery via WebSocket with Redis Pub/Sub
- **Multi-Source Ingestion**: Support for TCP, UDP, HTTP, and file uploads
- **Advanced Search & Filtering**: Full-text search with Elasticsearch-powered queries
- **Interactive Dashboards**: Built-in analytics and Kibana integration for custom visualizations
- **User Isolation**: Secure multi-tenant architecture with user-specific log segregation
- **Live Monitoring**: Real-time metrics (logs/sec, errors/min, connected users)
- **Visual Alerts**: Browser notifications, sound alerts, and severity-based warnings
- **RESTful API**: Complete REST API with token-based authentication
- **Search History**: Track and replay previous search queries
- **Metadata Management**: Tag and categorize logs with custom metadata

### Architecture Overview

```
┌─────────────────┐
│   Log Sources   │
│ (Apps, Files)   │
└────────┬────────┘
         │
         v
┌─────────────────┐      ┌──────────────┐
│    Logstash     │─────>│ Elasticsearch│
│  (Ingestion)    │      │   (Storage)  │
└────────┬────────┘      └──────────────┘
         │
         v
┌─────────────────┐      ┌──────────────┐
│      Redis      │<────>│    Django    │
│  (Pub/Sub)      │      │   Backend    │
└─────────────────┘      └──────┬───────┘
                                │
         ┌──────────────────────┼──────────────────┐
         v                      v                  v
┌─────────────────┐    ┌──────────────┐   ┌─────────────┐
│   PostgreSQL    │    │   MongoDB    │   │   Next.js   │
│  (Auth/Meta)    │    │  (Logs DB)   │   │  Frontend   │
└─────────────────┘    └──────────────┘   └─────────────┘
```

**Components**:
- **Frontend**: Next.js 14 with React, TypeScript, and Tailwind CSS
- **Backend**: Django 4.x with Django REST Framework and Channels
- **Search Engine**: Elasticsearch 8.x for log indexing and search
- **Log Pipeline**: Logstash for data ingestion and transformation
- **Visualization**: Kibana 8.x for advanced analytics and custom dashboards
- **Databases**: PostgreSQL (metadata), MongoDB (logs), Redis (cache/pubsub)
- **WebSocket**: Django Channels with Redis channel layer
- **Monitoring**: Prometheus for metrics collection, Grafana for visualization
- **Reverse Proxy**: Nginx for routing and load balancing

---

## Tech Stack

### Backend
- **Python 3.11+** - Core backend language
- **Django 4.2** - Web framework
- **Django REST Framework 3.14** - RESTful API
- **Django Channels 4.0** - WebSocket support
- **Celery 5.3** - Asynchronous task processing
- **PyMongo 4.5** - MongoDB driver
- **Psycopg2 2.9** - PostgreSQL adapter

### Frontend
- **Node.js 20+** - JavaScript runtime
- **Next.js 14.0** - React framework
- **React 18** - UI library
- **TypeScript 5** - Type-safe JavaScript
- **Tailwind CSS 3** - Utility-first CSS
- **Recharts 2.8** - Data visualization

### Databases & Storage
- **Elasticsearch 8.11** - Log storage and search
- **PostgreSQL 15** - Relational database (auth, sessions)
- **MongoDB 7.0** - Document database (logs)
- **Redis 7** - Cache and message broker

### Infrastructure
- **Docker 24+** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx 1.25** - Reverse proxy
- **Logstash 8.11** - Log pipeline
- **Kibana 8.11** - Analytics platform

### Monitoring & Observability
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization
- **Alertmanager** - Alert management
- **Blackbox Exporter** - Endpoint monitoring

---

## Prerequisites

### Required Software

| Software | Minimum Version | Purpose |
|----------|----------------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Multi-container management |
| Git | 2.40+ | Version control |

### Optional (for local development without Docker)

| Software | Version | Purpose |
|----------|---------|---------|
| Node.js | 20.x | Frontend development |
| Python | 3.11+ | Backend development |
| PostgreSQL | 15+ | Database |
| MongoDB | 7.0+ | Document store |
| Redis | 7+ | Cache/message broker |

### System Requirements

**Minimum**:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB free space
- OS: Linux, macOS, Windows 10/11 with WSL2

**Recommended**:
- CPU: 8+ cores
- RAM: 16 GB
- Disk: 100 GB SSD
- OS: Linux (Ubuntu 22.04+)

### Platform-Specific Notes

**Windows**:
- Install Docker Desktop with WSL2 backend
- Run PowerShell as Administrator for Docker commands
- Git line endings: configure `core.autocrlf=input`

**macOS**:
- Install Docker Desktop for Mac
- Increase Docker memory allocation to 8GB minimum

**Linux**:
- Install Docker Engine and Docker Compose plugin
- Add user to `docker` group: `sudo usermod -aG docker $USER`

---

## Project Structure

```
elk-vision-saas/
├── backend/                    # Django backend application
│   ├── api/                    # Real-time API and WebSocket
│   │   ├── consumers.py        # WebSocket consumers (logs, notifications)
│   │   ├── consumers_metrics.py # Metrics WebSocket consumer
│   │   ├── realtime.py         # Redis Pub/Sub bridge
│   │   ├── routing.py          # WebSocket URL routing
│   │   └── management/         # Django management commands
│   │       └── commands/
│   │           └── start_realtime_listener.py
│   ├── app/                    # Django apps
│   │   ├── alerts/             # Alert management
│   │   ├── dashboards/         # Dashboard API
│   │   ├── logs/               # Log ingestion and search
│   │   └── users/              # User management
│   ├── config/                 # Django configuration
│   │   ├── settings.py         # Main settings
│   │   ├── urls.py             # URL routing
│   │   ├── asgi.py             # ASGI config (WebSocket)
│   │   └── celery.py           # Celery configuration
│   ├── requirements.txt        # Python dependencies
│   └── manage.py               # Django management script
│
├── frontend/                   # Next.js frontend application
│   ├── src/
│   │   ├── app/                # Next.js App Router
│   │   │   ├── (dashboard)/    # Authenticated routes
│   │   │   │   ├── dashboard/  # Main dashboard
│   │   │   │   ├── live-logs/  # Real-time log monitoring
│   │   │   │   └── layout.tsx  # Dashboard layout
│   │   │   ├── login/          # Login page
│   │   │   └── register/       # Registration page
│   │   ├── components/         # React components
│   │   │   ├── analytics/      # Charts and analytics
│   │   │   ├── auth/           # Authentication forms
│   │   │   ├── dashboard/      # Dashboard widgets
│   │   │   ├── notifications/  # Notification system
│   │   │   ├── realtime/       # Real-time components
│   │   │   └── ui/             # Reusable UI components
│   │   ├── hooks/              # React custom hooks
│   │   │   ├── useWebSocket.ts # WebSocket hook
│   │   │   ├── useMetrics.ts   # Metrics streaming
│   │   │   └── useVisualAlerts.ts # Visual alerts
│   │   ├── lib/                # Utility libraries
│   │   │   ├── api.ts          # API client
│   │   │   └── websocket.ts    # WebSocket service
│   │   └── types/              # TypeScript types
│   ├── package.json            # Node dependencies
│   └── next.config.js          # Next.js configuration
│
├── logstash/                   # Logstash configuration
│   ├── config/
│   │   └── logstash.yml        # Logstash settings
│   └── pipeline/
│       └── logstash.conf       # Input/filter/output pipeline
│
├── kibana/                     # Kibana configuration
│   └── config/
│       └── kibana.yml          # Kibana settings
│
├── nginx/                      # Nginx reverse proxy
│   ├── nginx.conf              # Main Nginx config
│   └── conf.d/
│       ├── default.conf        # Frontend/backend routing
│       └── status.conf         # Status endpoint
│
├── monitoring/                 # Prometheus & Grafana
│   ├── prometheus/
│   │   ├── prometheus.yml      # Prometheus config
│   │   └── rules/              # Alert rules
│   ├── grafana/
│   │   ├── grafana.ini         # Grafana settings
│   │   └── dashboards/         # Pre-built dashboards
│   └── alertmanager/
│       └── alertmanager.yml    # Alert routing
│
├── docs/                       # Documentation
│   ├── API_GUIDE.md            # API documentation
│   ├── ARCHITECTURE.md         # Architecture details
│   ├── DEVELOPER_GUIDE.md      # Development guide
│   └── MONITORING_GUIDE.md     # Monitoring setup
│
├── scripts/                    # Utility scripts
│   ├── dev-setup.sh            # Development setup (Linux/Mac)
│   ├── dev-setup.ps1           # Development setup (Windows)
│   └── deploy.sh               # Deployment script
│
├── docker-compose.yml          # Development environment
├── docker-compose.prod.yml     # Production overrides
├── .env                        # Environment variables (gitignored)
├── .env.example                # Example environment file
└── README.md                   # This file
```

### Key Configuration Files

- **backend/config/settings.py**: Django settings (databases, middleware, apps)
- **frontend/next.config.js**: Next.js configuration (API routes, environment)
- **logstash/pipeline/logstash.conf**: Log processing pipeline
- **docker-compose.yml**: Container orchestration
- **.env**: Environment variables (create from .env.example)

---

## Environment Configuration

### Required Environment Files

Create a `.env` file in the project root by copying `.env.example`:

```bash
cp .env.example .env
```

### Core Environment Variables

#### Django Backend
```bash
# Django
SECRET_KEY=your-secret-key-min-50-chars
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,backend

# Database - PostgreSQL
POSTGRES_DB=elk_vision
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/elk_vision

# Database - MongoDB
MONGO_USER=admin
MONGO_PASSWORD=password
MONGO_DB_NAME=elk_vision
MONGO_HOST=mongodb
MONGO_PORT=27017

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis123
REDIS_URL=redis://:redis123@redis:6379/0

# Elasticsearch
ELASTICSEARCH_HOSTS=http://elasticsearch:9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=elastic123

# Celery
CELERY_BROKER_URL=redis://:redis123@redis:6379/1
CELERY_RESULT_BACKEND=redis://:redis123@redis:6379/2
```

#### Next.js Frontend
```bash
# API URLs
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Kibana Integration (optional)
NEXT_PUBLIC_KIBANA_URL=http://localhost:5601
NEXT_PUBLIC_KIBANA_DASHBOARD_ID=your-dashboard-id
```

#### ELK Stack
```bash
# Elasticsearch
ELASTIC_PASSWORD=elastic123
ES_JAVA_OPTS=-Xms2g -Xmx2g

# Kibana
KIBANA_PASSWORD=kibana_password_dev
KIBANA_ENCRYPTION_KEY=32-char-encryption-key-here

# Logstash
LOGSTASH_INTERNAL_PASSWORD=logstash123
```

### Security Notes

**Never commit sensitive data**:
- `.env` is in `.gitignore`
- Use `.env.example` as a template
- Rotate secrets in production
- Use strong passwords (minimum 16 characters)
- Generate SECRET_KEY: `python -c "import secrets; print(secrets.token_urlsafe(50))"`

**Production Considerations**:
- Use environment-specific configs (`.env.production`)
- Store secrets in vault services (AWS Secrets Manager, HashiCorp Vault)
- Enable HTTPS/TLS for all services
- Restrict database access to internal networks
- Use Docker secrets for sensitive values

---

## Installation & Setup

### Quick Start (Recommended)

The easiest way to run the entire stack is with Docker Compose:

```bash
# 1. Clone the repository
git clone https://github.com/YasserZr/elk-vision-saas.git
cd elk-vision-saas

# 2. Create environment file
cp .env.example .env

# 3. Edit .env with your configuration
# (Use your preferred editor)
nano .env

# 4. Build and start all services
docker compose up -d

# 5. Wait for services to be healthy (2-3 minutes)
docker compose ps

# 6. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Kibana: http://localhost:5601
```

### Detailed Setup Steps

#### Step 1: Clone and Navigate

```bash
git clone https://github.com/YasserZr/elk-vision-saas.git
cd elk-vision-saas
```

#### Step 2: Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Generate a secure Django secret key
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(50))" >> .env

# Edit other variables as needed
```

#### Step 3: Build Docker Images

```bash
# Build all services
docker compose build

# Build specific service
docker compose build backend
docker compose build frontend
```

#### Step 4: Initialize Databases

```bash
# Start database services only
docker compose up -d postgres mongodb redis elasticsearch

# Wait for databases to be ready (check health)
docker compose ps

# Run Django migrations
docker compose run --rm backend python manage.py migrate

# Create Django superuser
docker compose run --rm backend python manage.py createsuperuser

# Initialize Elasticsearch indices
docker compose run --rm backend python manage.py create_indices
```

#### Step 5: Start All Services

```bash
# Start all services in detached mode
docker compose up -d

# View logs
docker compose logs -f

# View logs for specific service
docker compose logs -f backend
docker compose logs -f frontend
```

#### Step 6: Verify Installation

```bash
# Check service health
docker compose ps

# All services should show "healthy" or "running"
```

Expected output:
```
NAME                STATUS
elk_backend         Up (healthy)
elk_frontend        Up (healthy)
elk_postgres        Up (healthy)
elk_mongodb         Up (healthy)
elk_redis           Up (healthy)
elk_elasticsearch   Up (healthy)
elk_logstash        Up (running)
elk_kibana          Up (healthy)
```

### Local Development Setup (Without Docker)

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver 0.0.0.0:8000

# In another terminal, start Celery worker
celery -A config worker -l info

# Start real-time listener (optional)
python manage.py start_realtime_listener
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
npm start
```

---

## Running the Application

### Development Mode

Start all services with hot-reload enabled:

```bash
# Start all services
docker compose up -d

# Follow logs
docker compose logs -f

# Restart a specific service
docker compose restart backend
docker compose restart frontend
```

**Access URLs**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Django Admin: http://localhost:8000/admin
- Kibana: http://localhost:5601 (log analytics & visualizations)
- Elasticsearch: http://localhost:9200
- Prometheus: http://localhost:9090 (metrics collection)
- Grafana: http://localhost:3001 (monitoring dashboards)
- Alertmanager: http://localhost:9093 (alert management)

### Production Mode

```bash
# Build production images
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start in production mode
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services
docker compose up -d --scale backend=3
```

### Service Management

```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v

# Restart specific service
docker compose restart backend

# View service logs
docker compose logs -f backend

# Execute command in running container
docker compose exec backend python manage.py shell

# Run one-off command
docker compose run --rm backend python manage.py migrate
```

### Health Checks

```bash
# Check all services
docker compose ps

# Check specific endpoints
curl http://localhost:8000/api/health
curl http://localhost:3000/api/health
curl http://localhost:9200/_cluster/health
```

---

## Usage Guide

### First-Time Access

1. **Register Account**
   - Navigate to http://localhost:3000/register
   - Fill in username, email, and password
   - Click "Sign Up"

2. **Login**
   - Go to http://localhost:3000/login
   - Enter credentials
   - Access dashboard at http://localhost:3000/dashboard

### Default Credentials

**Django Admin**:
- URL: http://localhost:8000/admin
- Username: (created during setup)
- Password: (created during setup)

**Kibana** (no authentication in development):
- URL: http://localhost:5601
- Username: (none - security disabled for development)
- Password: (none - security disabled for development)

**Grafana**:
- URL: http://localhost:3001
- Username: admin
- Password: admin (from .env GRAFANA_ADMIN_PASSWORD)

### Key Workflows

#### 1. Uploading Logs

**Via Web Interface**:
```
1. Navigate to Dashboard > Upload Logs
2. Select log file (JSON, CSV, or TXT)
3. Configure parsing options (delimiter, timestamp format)
4. Click "Upload"
5. View upload progress and results
```

**Via API**:
```bash
# Get authentication token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"your_user","password":"your_pass"}' \
  | jq -r '.token')

# Upload log file
curl -X POST http://localhost:8000/api/logs/upload/ \
  -H "Authorization: Token $TOKEN" \
  -F "file=@/path/to/logs.json" \
  -F "source=my-application" \
  -F "environment=production"
```

**Via TCP** (Logstash):
```bash
# Send single log entry
echo '{"level":"info","message":"Test log","timestamp":"2026-01-03T12:00:00Z"}' \
  | nc localhost 5000

# Stream logs from file
cat logs.json | nc localhost 5000
```

#### 2. Searching Logs

**Web Interface**:
```
1. Go to Dashboard > Search Logs
2. Enter search query in search bar
3. Apply filters:
   - Level: debug, info, warning, error, critical
   - Source: application name
   - Date Range: last hour, day, week, custom
4. Click "Search"
5. Export results if needed
```

**API Search**:
```bash
# Basic search
curl "http://localhost:8000/api/logs/search/?query=error&level=error" \
  -H "Authorization: Token $TOKEN"

# Advanced search with filters
curl "http://localhost:8000/api/logs/search/" \
  -H "Authorization: Token $TOKEN" \
  -G \
  --data-urlencode "query=database connection" \
  --data-urlencode "level=error" \
  --data-urlencode "source=backend-api" \
  --data-urlencode "start_date=2026-01-01" \
  --data-urlencode "end_date=2026-01-03" \
  --data-urlencode "page=1" \
  --data-urlencode "page_size=50"
```

#### 3. Real-Time Log Monitoring

**Live Logs Page**:
```
1. Navigate to Dashboard > Live Logs
2. Logs stream in real-time (<1 second latency)
3. Use filters to narrow results:
   - Level filter (dropdown)
   - Source filter (dropdown)
   - Text search (Ctrl/Cmd + K)
4. Pause/resume auto-scroll with Spacebar
5. View live metrics:
   - Logs per second
   - Errors per minute
   - Connected users
```

**WebSocket Connection** (programmatic):
```javascript
// Connect to log stream
const ws = new WebSocket('ws://localhost:8000/ws/logs/stream/');

ws.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log('New log:', log);
};

// Send filters
ws.send(JSON.stringify({
  type: 'set_filters',
  filters: {
    level: 'error',
    source: 'backend-api'
  }
}));
```

#### 4. Creating Alerts

```
1. Go to Dashboard > Alerts
2. Click "Create Alert"
3. Configure alert:
   - Name: "High Error Rate"
   - Condition: "error count > 10 in 5 minutes"
   - Severity: Critical
   - Notification: Browser + Email
4. Save alert
5. Receive notifications when triggered
```

#### 5. Analytics Dashboard

```
1. Navigate to Dashboard > Analytics
2. View tabs:
   - Overview: KPIs, charts, trends
   - Log Explorer: Detailed log table
   - Kibana: Embedded Kibana dashboards
3. Adjust time range (1h, 6h, 24h, 7d)
4. Export data or create reports
```

#### 6. Kibana Integration

```
1. Open Kibana at http://localhost:5601
2. Create a dashboard in Kibana
3. Copy dashboard ID from URL:
   http://localhost:5601/app/dashboards#/view/DASHBOARD-ID
4. Add to .env:
   NEXT_PUBLIC_KIBANA_DASHBOARD_ID=DASHBOARD-ID
5. Restart frontend:
   docker compose restart frontend
6. View embedded dashboard in Analytics > Kibana tab
```

---

## API Documentation

### Authentication

All API endpoints except `/api/auth/login/` and `/api/auth/register/` require authentication.

**Obtain Token**:
```bash
POST /api/auth/login/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}

Response:
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "username": "your_username",
    "email": "user@example.com"
  }
}
```

**Use Token in Requests**:
```bash
GET /api/logs/search/
Authorization: Token abc123...
```

### Core Endpoints

#### Authentication
```
POST   /api/auth/register/     - Create new user account
POST   /api/auth/login/        - Obtain authentication token
POST   /api/auth/logout/       - Invalidate token
GET    /api/auth/user/         - Get current user info
```

#### Logs
```
GET    /api/logs/              - List logs (paginated)
POST   /api/logs/              - Create single log entry
GET    /api/logs/{id}/         - Get log details
POST   /api/logs/upload/       - Upload log file
POST   /api/logs/bulk/         - Create multiple logs
GET    /api/logs/search/       - Search logs with filters
GET    /api/logs/stats/        - Get log statistics
```

#### Search History
```
GET    /api/logs/search-history/           - List saved searches
POST   /api/logs/search-history/           - Save search
GET    /api/logs/search-history/{id}/      - Get search details
DELETE /api/logs/search-history/{id}/      - Delete search
```

#### Dashboards
```
GET    /api/dashboards/        - List dashboards
POST   /api/dashboards/        - Create dashboard
GET    /api/dashboards/{id}/   - Get dashboard config
PUT    /api/dashboards/{id}/   - Update dashboard
DELETE /api/dashboards/{id}/   - Delete dashboard
```

#### Alerts
```
GET    /api/alerts/            - List alerts
POST   /api/alerts/            - Create alert rule
GET    /api/alerts/{id}/       - Get alert details
PUT    /api/alerts/{id}/       - Update alert
DELETE /api/alerts/{id}/       - Delete alert
GET    /api/alerts/history/    - Alert trigger history
```

### API Examples

#### Search Logs
```bash
curl -X GET "http://localhost:8000/api/logs/search/" \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -G \
  --data-urlencode "query=database error" \
  --data-urlencode "level=error" \
  --data-urlencode "start_date=2026-01-01T00:00:00Z" \
  --data-urlencode "end_date=2026-01-03T23:59:59Z"
```

#### Upload Logs
```bash
curl -X POST "http://localhost:8000/api/logs/upload/" \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "file=@logs.json" \
  -F "source=web-server" \
  -F "environment=production"
```

#### Create Alert
```bash
curl -X POST "http://localhost:8000/api/alerts/" \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High Error Rate",
    "description": "Alert when error count exceeds threshold",
    "query": "level:error",
    "condition": {
      "threshold": 10,
      "window": "5m",
      "operator": ">"
    },
    "severity": "critical",
    "enabled": true
  }'
```

### WebSocket API

#### Log Stream
```
ws://localhost:8000/ws/logs/stream/

Messages (client -> server):
{
  "type": "set_filters",
  "filters": {
    "level": "error",
    "source": "backend-api",
    "query": "database"
  }
}

Messages (server -> client):
{
  "type": "log",
  "data": {
    "id": "123",
    "timestamp": "2026-01-03T12:00:00Z",
    "level": "error",
    "message": "Database connection failed",
    "source": "backend-api"
  }
}
```

#### Metrics Stream
```
ws://localhost:8000/ws/metrics/

Messages (server -> client):
{
  "type": "metrics_update",
  "data": {
    "logs_per_second": 42.5,
    "errors_per_minute": 3,
    "connected_users": 8,
    "timestamp": "2026-01-03T12:00:00Z"
  }
}
```

### Interactive API Documentation

Access interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

---

## Troubleshooting

### Common Issues

#### Issue: Services fail to start

**Symptoms**:
```
Error: Cannot start service backend: connection refused
```

**Solutions**:
```bash
# Check Docker daemon is running
docker info

# Check ports are not in use
netstat -an | grep -E '3000|8000|5432|27017|6379|9200'

# Restart Docker
sudo systemctl restart docker  # Linux
# Or restart Docker Desktop on Windows/Mac

# Clear Docker cache
docker system prune -a --volumes
```

#### Issue: Database connection errors

**Symptoms**:
```
django.db.utils.OperationalError: could not connect to server
```

**Solutions**:
```bash
# Check database container is healthy
docker compose ps postgres

# View database logs
docker compose logs postgres

# Verify environment variables
docker compose exec backend env | grep DATABASE

# Reset database
docker compose down -v
docker compose up -d postgres
docker compose run --rm backend python manage.py migrate
```

#### Issue: Elasticsearch unhealthy

**Symptoms**:
```
cluster_health_status: red
```

**Solutions**:
```bash
# Check Elasticsearch logs
docker compose logs elasticsearch

# Increase memory allocation in docker-compose.yml
# ES_JAVA_OPTS=-Xms4g -Xmx4g

# Check cluster health
curl http://localhost:9200/_cluster/health?pretty

# Reset Elasticsearch
docker compose stop elasticsearch
docker volume rm elk-vision-saas_elasticsearch_data
docker compose up -d elasticsearch
```

#### Issue: Frontend build errors

**Symptoms**:
```
Error: Cannot find module '@/components/...'
```

**Solutions**:
```bash
# Clear Next.js cache
docker compose exec frontend rm -rf .next

# Rebuild node_modules
docker compose exec frontend rm -rf node_modules
docker compose exec frontend npm install

# Restart frontend
docker compose restart frontend

# Check TypeScript errors
docker compose exec frontend npm run type-check
```

#### Issue: WebSocket connection fails

**Symptoms**:
```
WebSocket connection to 'ws://localhost:8000/ws/logs/stream/' failed
```

**Solutions**:
```bash
# Check backend is running
docker compose ps backend

# Check Redis is healthy
docker compose ps redis

# Verify WebSocket routing
docker compose logs backend | grep -i websocket

# Test WebSocket connection
wscat -c ws://localhost:8000/ws/logs/stream/

# Check Nginx WebSocket proxy settings
docker compose exec nginx cat /etc/nginx/conf.d/default.conf
```

#### Issue: Logs not appearing in real-time

**Symptoms**:
- Live Logs page shows no logs
- Logs visible in Elasticsearch but not streaming

**Solutions**:
```bash
# Check realtime_listener service
docker compose ps realtime_listener
docker compose logs realtime_listener

# Verify Redis Pub/Sub
docker compose exec redis redis-cli
> SUBSCRIBE logs:realtime
# Send test log via Logstash, should see message

# Check Logstash Redis output
docker compose logs logstash | grep -i redis

# Restart real-time components
docker compose restart realtime_listener
docker compose restart redis
```

### Debugging Tips

#### View Service Logs
```bash
# All services
docker compose logs -f

# Specific service with timestamps
docker compose logs -f --timestamps backend

# Last 100 lines
docker compose logs --tail=100 frontend

# Since specific time
docker compose logs --since 2026-01-03T12:00:00
```

#### Execute Commands in Containers
```bash
# Django shell
docker compose exec backend python manage.py shell

# Database shell
docker compose exec postgres psql -U postgres -d elk_vision
docker compose exec mongodb mongosh -u admin -p password

# Redis CLI
docker compose exec redis redis-cli -a redis123

# Check Elasticsearch indices
curl http://localhost:9200/_cat/indices?v

# Frontend shell
docker compose exec frontend sh
```

#### Health Checks
```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend health
curl http://localhost:3000/api/health

# Elasticsearch cluster
curl http://localhost:9200/_cluster/health?pretty

# Kibana status
curl http://localhost:5601/api/status

# Redis ping
docker compose exec redis redis-cli -a redis123 ping
```

#### Performance Monitoring
```bash
# Container resource usage
docker stats

# Elasticsearch cluster stats
curl http://localhost:9200/_cluster/stats?pretty

# Check slow queries
docker compose exec backend python manage.py check

# Frontend bundle analysis
docker compose exec frontend npm run analyze
```

### Getting Help

If issues persist:

1. Check documentation in `docs/` folder
2. Review logs: `docker compose logs -f`
3. Search existing GitHub issues
4. Create new issue with:
   - Docker version: `docker --version`
   - OS and version
   - Full error message
   - Steps to reproduce
   - Relevant logs

---

## Development Guidelines

### Code Standards

#### Python (Backend)
- Follow PEP 8 style guide
- Use Black formatter (line length: 100)
- Type hints for functions
- Docstrings for classes and methods
- Run linters before commit:
```bash
black backend/
flake8 backend/
mypy backend/
```

#### TypeScript (Frontend)
- Follow Airbnb style guide
- Use ESLint and Prettier
- Strict type checking enabled
- React functional components with hooks
- Run linters:
```bash
npm run lint
npm run type-check
npm run format
```

### Git Workflow

#### Branch Strategy
```
main          - Production-ready code
develop       - Integration branch
feature/*     - New features
bugfix/*      - Bug fixes
hotfix/*      - Urgent production fixes
```

#### Commit Messages
Follow Conventional Commits:
```
feat: Add real-time log streaming
fix: Resolve WebSocket connection timeout
docs: Update API documentation
refactor: Simplify authentication middleware
test: Add unit tests for log ingestion
chore: Update dependencies
```

#### Pull Request Process
```
1. Create feature branch from develop
2. Make changes and commit
3. Write/update tests
4. Update documentation
5. Push branch and create PR
6. Request code review
7. Address review comments
8. Merge after approval
```

### Adding New Features

#### Backend Feature
```bash
# 1. Create Django app
docker compose exec backend python manage.py startapp new_feature

# 2. Add to INSTALLED_APPS in config/settings.py

# 3. Create models in new_feature/models.py

# 4. Create migrations
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate

# 5. Create serializers in new_feature/serializers.py

# 6. Create views in new_feature/views.py

# 7. Add URLs in new_feature/urls.py

# 8. Include in config/urls.py

# 9. Write tests in new_feature/tests.py

# 10. Run tests
docker compose exec backend python manage.py test
```

#### Frontend Feature
```bash
# 1. Create component
frontend/src/components/feature/NewComponent.tsx

# 2. Create page (if needed)
frontend/src/app/feature/page.tsx

# 3. Add route to layout.tsx

# 4. Create API client methods in lib/api.ts

# 5. Create custom hooks if needed
frontend/src/hooks/useNewFeature.ts

# 6. Write tests
frontend/src/components/feature/NewComponent.test.tsx

# 7. Run tests
npm test
```

### Testing

#### Backend Tests
```bash
# Run all tests
docker compose exec backend python manage.py test

# Run specific app
docker compose exec backend python manage.py test app.logs

# With coverage
docker compose exec backend coverage run --source='.' manage.py test
docker compose exec backend coverage report
```

#### Frontend Tests
```bash
# Run all tests
npm test

# Watch mode
npm test -- --watch

# Coverage report
npm test -- --coverage

# E2E tests
npm run test:e2e
```

### Database Migrations

```bash
# Create migration
docker compose exec backend python manage.py makemigrations

# Apply migration
docker compose exec backend python manage.py migrate

# Rollback migration
docker compose exec backend python manage.py migrate app_name previous_migration

# Show migrations
docker compose exec backend python manage.py showmigrations
```

---

## Deployment Notes

### Docker Images

#### Building Production Images
```bash
# Build all images
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Build with custom tag
docker build -t elk-vision-backend:v1.0.0 ./backend
docker build -t elk-vision-frontend:v1.0.0 ./frontend

# Push to registry
docker tag elk-vision-backend:v1.0.0 registry.example.com/elk-vision-backend:v1.0.0
docker push registry.example.com/elk-vision-backend:v1.0.0
```

#### Image Optimization
- Multi-stage builds reduce image size
- Backend image: ~200 MB
- Frontend image: ~150 MB
- Use `.dockerignore` to exclude unnecessary files

### Cloud Deployment

#### AWS (Example)

**Prerequisites**:
- AWS account with ECS/EKS
- RDS for PostgreSQL
- DocumentDB for MongoDB
- ElastiCache for Redis
- OpenSearch for Elasticsearch

**Deployment Steps**:
```bash
# 1. Push images to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker tag elk-vision-backend:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/elk-vision-backend:latest
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/elk-vision-backend:latest

# 2. Update ECS task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 3. Update service
aws ecs update-service --cluster elk-vision --service backend --task-definition elk-vision-backend:latest
```

#### Google Cloud Platform

Use Cloud Run, Cloud SQL, and Memorystore:
```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/elk-vision-backend

# Deploy to Cloud Run
gcloud run deploy elk-vision-backend \
  --image gcr.io/PROJECT_ID/elk-vision-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Scaling Strategies

#### Horizontal Scaling
```bash
# Scale backend workers
docker compose up -d --scale backend=5

# Scale with Kubernetes
kubectl scale deployment elk-vision-backend --replicas=10
```

#### Vertical Scaling
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Monitoring in Production

#### Prometheus Metrics
- Backend exposes `/metrics` endpoint
- Scrape interval: 15s
- Retention: 15 days

#### Grafana Dashboards
- Pre-built dashboards in `monitoring/grafana/dashboards/`
- Import to Grafana: http://localhost:3001

#### Alerting Rules
```yaml
# monitoring/prometheus/rules/alerts.yml
groups:
  - name: elk_vision
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
```

### Backup & Recovery

#### Database Backups
```bash
# PostgreSQL backup
docker compose exec postgres pg_dump -U postgres elk_vision > backup.sql

# MongoDB backup
docker compose exec mongodb mongodump --out /backup

# Restore PostgreSQL
docker compose exec -T postgres psql -U postgres elk_vision < backup.sql

# Restore MongoDB
docker compose exec mongodb mongorestore /backup
```

#### Elasticsearch Snapshots
```bash
# Create snapshot repository
curl -X PUT "http://localhost:9200/_snapshot/backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/usr/share/elasticsearch/backup"
  }
}'

# Create snapshot
curl -X PUT "http://localhost:9200/_snapshot/backup/snapshot_1?wait_for_completion=true"

# Restore snapshot
curl -X POST "http://localhost:9200/_snapshot/backup/snapshot_1/_restore"
```

---

## Contribution Guide

We welcome contributions from the community! Please follow these guidelines:

### How to Contribute

1. **Fork the repository**
   ```bash
   git clone https://github.com/YasserZr/elk-vision-saas.git
   cd elk-vision-saas
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes**
   - Write code following style guidelines
   - Add tests for new functionality
   - Update documentation

4. **Test your changes**
   ```bash
   # Backend tests
   docker compose exec backend python manage.py test
   
   # Frontend tests
   docker compose exec frontend npm test
   
   # Linting
   docker compose exec backend black . && flake8
   docker compose exec frontend npm run lint
   ```

5. **Commit with conventional commits**
   ```bash
   git add .
   git commit -m "feat: add new log export feature"
   ```

6. **Push and create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create PR on GitHub**
   - Provide clear description
   - Link related issues
   - Add screenshots if UI changes

### Code Review Process

- All PRs require at least one approval
- CI/CD checks must pass
- Code coverage must not decrease
- Documentation must be updated

### Reporting Bugs

Use GitHub Issues with template:
```
**Bug Description**
Clear description of the bug

**Steps to Reproduce**
1. Go to...
2. Click on...
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: Ubuntu 22.04
- Docker: 24.0.5
- Browser: Chrome 120

**Logs**
Paste relevant logs
```

### Suggesting Features

Create GitHub Issue with:
- Clear use case
- Expected behavior
- Mockups if applicable
- Technical considerations

---

## License & Credits

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 ELK Vision SaaS Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Third-Party Licenses

This project uses open-source software:

- **Django** - BSD License
- **Next.js** - MIT License
- **Elasticsearch** - Elastic License 2.0
- **React** - MIT License
- **PostgreSQL** - PostgreSQL License
- **MongoDB** - Server Side Public License (SSPL)
- **Redis** - BSD License

See `LICENSE-THIRD-PARTY.md` for full details.

### Contributors

- **Core Team**: See [CONTRIBUTORS.md](CONTRIBUTORS.md)
- **Community Contributors**: Thank you to everyone who has submitted PRs, reported bugs, and provided feedback

### Acknowledgements

- ELK Stack team for powerful log management tools
- Django and Django REST Framework communities
- Next.js and Vercel for excellent React framework
- All open-source contributors

### Support

- Documentation: [docs/](docs/)
- GitHub Issues: https://github.com/YasserZr/elk-vision-saas/issues
- Discussions: https://github.com/YasserZr/elk-vision-saas/discussions

---

**Built with Django, Next.js, and the ELK Stack**
