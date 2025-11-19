# Backend - Django REST API

The backend service provides the REST API for the ELK Vision SaaS platform.

## Structure

```
backend/
├── app/                    # Application modules
│   ├── users/             # User management
│   ├── logs/              # Log search and analytics
│   ├── dashboards/        # Dashboard management
│   └── alerts/            # Alert configuration
├── config/                # Django configuration
│   ├── settings.py       # Django settings
│   ├── urls.py           # URL routing
│   └── wsgi.py           # WSGI configuration
├── requirements.txt       # Python dependencies
├── manage.py             # Django CLI
├── Dockerfile            # Docker configuration
└── .env.example          # Environment variables template
```

## Setup

### Local Development

1. **Create virtual environment**
   ```bash
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
   # Edit .env with your configuration
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

### Docker Development

```bash
docker build -t elk-backend .
docker run -p 8000:8000 elk-backend
```

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Login
- `POST /api/auth/refresh/` - Refresh token

### Users
- `GET /api/users/profile/` - Get user profile

### Logs
- `GET /api/logs/search/?q=error` - Search logs

### Dashboards
- `GET /api/dashboards/` - List dashboards
- `POST /api/dashboards/` - Create dashboard
- `GET /api/dashboards/{id}/` - Get dashboard
- `PUT /api/dashboards/{id}/` - Update dashboard
- `DELETE /api/dashboards/{id}/` - Delete dashboard

### Alerts
- `GET /api/alerts/` - List alerts
- `POST /api/alerts/` - Create alert
- `GET /api/alerts/{id}/` - Get alert
- `PUT /api/alerts/{id}/` - Update alert
- `DELETE /api/alerts/{id}/` - Delete alert

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `MONGO_HOST` - MongoDB host
- `ELASTICSEARCH_HOSTS` - Elasticsearch URL
- `REDIS_HOST` - Redis host

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest app/users/tests.py
```

## Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8
```

## Database

The backend uses:
- **MongoDB** for operational data (users, configurations)
- **Elasticsearch** for log data storage and search

## Celery Workers

Background tasks are processed by Celery workers:

```bash
# Start worker
celery -A config worker --loglevel=info

# Start with multiple workers
celery -A config worker --loglevel=info --concurrency=4
```

## Production Deployment

1. Set `DEBUG=False`
2. Configure production database credentials
3. Use proper SECRET_KEY
4. Set up SSL/HTTPS
5. Use gunicorn or uwsgi
6. Configure CORS properly

```bash
gunicorn --bind 0.0.0.0:8000 --workers 3 config.wsgi:application
```
