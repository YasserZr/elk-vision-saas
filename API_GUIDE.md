# ELK Vision SaaS - RESTful API Service

Production-ready Django REST API following 12-factor app principles.

## 🎯 Features

### Core Features
- ✅ **JWT Authentication** - Secure token-based authentication with refresh
- ✅ **User Management** - Registration, login, profile management, password change
- ✅ **Health Checks** - Kubernetes-ready health, readiness, and liveness probes
- ✅ **API Versioning** - `/api/v1/` versioned endpoints
- ✅ **Structured Logging** - JSON logs in production, verbose in development
- ✅ **12-Factor App Compliant** - Environment-based configuration
- ✅ **CI/CD Ready** - GitHub Actions workflow included
- ✅ **Security Hardened** - CORS, HTTPS, HSTS, XSS protection

## 📋 API Endpoints

### Health Checks (No Authentication Required)
```
GET  /health/          # Comprehensive health check
GET  /health/live/     # Liveness probe (Kubernetes)
GET  /health/ready/    # Readiness probe (Kubernetes)
```

### Authentication
```
POST /api/auth/login/    # Login (get JWT tokens)
POST /api/auth/refresh/  # Refresh access token
```

### User Management (v1)
```
POST /api/v1/users/register/        # Register new user
GET  /api/v1/users/profile/         # Get user profile
PUT  /api/v1/users/profile/         # Update user profile
POST /api/v1/users/change-password/ # Change password
```

### Logs (v1)
```
GET  /api/v1/logs/search/  # Search logs
```

### Dashboards (v1)
```
GET  /api/v1/dashboards/   # List dashboards
```

### Alerts (v1)
```
GET  /api/v1/alerts/       # List alerts
```

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
cd infra
docker-compose up -d
```

The API will be available at `http://localhost:8000`

### Local Development

1. **Set up virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/users/tests.py

# Run with verbose output
pytest -v
```

## 🔐 Authentication Flow

### 1. Register a new user
```bash
curl -X POST http://localhost:8000/api/v1/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### 2. Login to get JWT tokens
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "SecurePass123!"
  }'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 3. Use access token for authenticated requests
```bash
curl -X GET http://localhost:8000/api/v1/users/profile/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### 4. Refresh token when expired
```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

## 📊 Health Check Examples

### Basic Health Check
```bash
curl http://localhost:8000/health/
```

Response:
```json
{
  "status": "healthy",
  "version": "v1",
  "checks": {
    "database": {"status": "up", "type": "mongodb"},
    "redis": {"status": "up"},
    "elasticsearch": {"status": "up", "cluster_status": "green"}
  }
}
```

### Kubernetes Probes
```yaml
# deployment.yaml
livenessProbe:
  httpGet:
    path: /health/live/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready/
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

## 🏗️ 12-Factor App Principles

### I. Codebase
- Single codebase tracked in Git
- Multiple deployment environments

### II. Dependencies
- Explicit dependencies in `requirements.txt`
- Isolated via virtual environment

### III. Config
- All configuration via environment variables
- `.env` files for local development
- No secrets in codebase

### IV. Backing Services
- MongoDB, Redis, Elasticsearch as attached resources
- Configurable via environment variables

### V. Build, Release, Run
- Separate build (Docker), release, and run stages
- Docker images tagged with commit SHA

### VI. Processes
- Stateless processes
- Session data in Redis
- No local file storage

### VII. Port Binding
- Self-contained web server (Gunicorn)
- Exports HTTP service via port binding

### VIII. Concurrency
- Horizontal scaling via process model
- Multiple workers for Gunicorn and Celery

### IX. Disposability
- Fast startup and graceful shutdown
- Health checks for orchestration

### X. Dev/Prod Parity
- Same backing services in dev and prod
- Docker ensures environment consistency

### XI. Logs
- Logs to stdout/stderr as event streams
- JSON format in production
- Aggregation via external tools

### XII. Admin Processes
- Django management commands
- Celery for background tasks

## 🔒 Security Features

- **JWT Authentication** with short-lived access tokens
- **Password Validation** with Django validators
- **HTTPS/SSL** enforcement in production
- **CORS** configuration for cross-origin requests
- **HSTS** headers for HTTPS-only access
- **XSS Protection** headers
- **CSRF Protection** for state-changing operations
- **Content Security Policy** headers

## 🌍 Environment Variables

### Required
```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost

MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_USER=admin
MONGO_PASSWORD=password
MONGO_DB_NAME=elk_vision

REDIS_HOST=redis
REDIS_PORT=6379

ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

### Optional
```env
LOG_LEVEL=INFO
DJANGO_LOG_LEVEL=INFO
APP_LOG_LEVEL=DEBUG
HEALTH_CHECK_TIMEOUT=5
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

## 🔄 CI/CD Pipeline

GitHub Actions workflow includes:

1. **Linting** - flake8, black, isort
2. **Testing** - pytest with coverage
3. **Security Scanning** - Trivy vulnerability scanner
4. **Docker Build** - Multi-stage builds
5. **Deployment** - Automated deployment on main branch

Triggered on:
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

## 📦 Project Structure

```
backend/
├── app/
│   ├── users/          # User management
│   ├── logs/           # Log search
│   ├── dashboards/     # Dashboards
│   ├── alerts/         # Alerts
│   └── health/         # Health checks
├── config/
│   ├── settings.py     # Django settings
│   ├── urls.py         # URL routing
│   └── wsgi.py         # WSGI config
├── requirements.txt    # Dependencies
├── pytest.ini         # Test configuration
├── manage.py          # Django CLI
├── Dockerfile         # Container image
└── .env.example       # Environment template
```

## 🐳 Docker Commands

```bash
# Build image
docker build -t elk-backend .

# Run container
docker run -p 8000:8000 \
  -e SECRET_KEY=your-key \
  -e DEBUG=True \
  elk-backend

# Run with docker-compose
cd ../infra
docker-compose up backend

# View logs
docker-compose logs -f backend

# Execute management commands
docker-compose exec backend python manage.py createsuperuser
```

## 🚀 Production Deployment

### Checklist
- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Enable SSL/HTTPS
- [ ] Set up SSL certificates
- [ ] Configure proper CORS
- [ ] Use production database
- [ ] Set up monitoring
- [ ] Configure logging aggregation
- [ ] Set up backup strategy
- [ ] Configure auto-scaling
- [ ] Set resource limits

### Deployment Options

1. **Kubernetes**
   - Use provided health check endpoints
   - Horizontal Pod Autoscaler
   - Rolling updates

2. **AWS ECS/Fargate**
   - Task definition with health checks
   - Application Load Balancer
   - Auto Scaling

3. **Heroku**
   - Procfile included
   - Config vars for environment
   - Heroku Postgres addon

4. **Docker Swarm**
   - Stack deployment
   - Service scaling
   - Rolling updates

## 📚 Additional Resources

- [Django REST Framework Documentation](https://www.django-rest-framework.org/)
- [JWT Authentication Guide](https://django-rest-framework-simplejwt.readthedocs.io/)
- [12-Factor App Methodology](https://12factor.net/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Health Checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details
