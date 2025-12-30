# Developer Guide

Complete guide for developers working on the ELK Vision SaaS platform.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Development Environment Setup](#development-environment-setup)
3. [Project Structure](#project-structure)
4. [Backend Development](#backend-development)
5. [Frontend Development](#frontend-development)
6. [Database Operations](#database-operations)
7. [Testing](#testing)
8. [Code Style & Standards](#code-style--standards)
9. [Git Workflow](#git-workflow)
10. [Debugging](#debugging)
11. [Common Tasks](#common-tasks)
12. [Troubleshooting](#troubleshooting)

---

## Quick Start

Get the application running in 5 minutes:

```bash
# Clone repository
git clone https://github.com/yourusername/elk-vision-saas.git
cd elk-vision-saas

# Copy environment file
cp .env.development.example .env

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api
# Admin: http://localhost:8000/admin
# Kibana: http://localhost:5601
# Grafana: http://localhost:3001
```

---

## Development Environment Setup

### Prerequisites

**Required Software:**
- Docker Desktop 24.0+ (Windows/Mac) or Docker Engine (Linux)
- Docker Compose 2.20+
- Git
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)
- VS Code or PyCharm (recommended)

**Optional:**
- PostgreSQL 15+ (for local development without Docker)
- Redis 7+ (for local development without Docker)
- MongoDB 7+ (for local development without Docker)

### Installation Steps

#### Windows (PowerShell)

```powershell
# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# Or use Chocolatey
choco install docker-desktop
choco install git
choco install nodejs
choco install python311

# Verify installations
docker --version
docker-compose --version
git --version
node --version
python --version
```

#### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install docker
brew install git
brew install node@20
brew install python@3.11

# Verify installations
docker --version
docker-compose --version
git --version
node --version
python3 --version
```

#### Linux (Ubuntu/Debian)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install other dependencies
sudo apt update
sudo apt install -y git nodejs npm python3.11 python3.11-venv python3-pip

# Verify installations
docker --version
docker-compose --version
git --version
node --version
python3 --version
```

### IDE Setup

#### VS Code Extensions

Install these recommended extensions:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-azuretools.vscode-docker",
    "humao.rest-client",
    "redhat.vscode-yaml",
    "mikestead.dotenv",
    "formulahendry.auto-rename-tag",
    "naumovs.color-highlight"
  ]
}
```

Save as `.vscode/extensions.json` in project root.

#### VS Code Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.path": "isort",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.pytest_cache": true,
    "**/node_modules": true,
    "**/.next": true
  },
  "editor.rulers": [88, 120],
  "editor.tabSize": 4,
  "[javascript]": {
    "editor.tabSize": 2
  },
  "[typescript]": {
    "editor.tabSize": 2
  }
}
```

---

## Project Structure

```
elk-vision-saas/
├── backend/                    # Django backend
│   ├── api/                   # Main API application
│   │   ├── migrations/        # Database migrations
│   │   ├── models/            # Database models
│   │   │   ├── __init__.py
│   │   │   ├── log_file.py
│   │   │   ├── alert.py
│   │   │   └── user_profile.py
│   │   ├── serializers/       # DRF serializers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── log.py
│   │   │   └── analytics.py
│   │   ├── views/             # API views
│   │   │   ├── __init__.py
│   │   │   ├── auth_views.py
│   │   │   ├── log_views.py
│   │   │   ├── analytics_views.py
│   │   │   └── metrics_views.py
│   │   ├── middleware/        # Custom middleware
│   │   │   ├── prometheus_middleware.py
│   │   │   └── security_headers.py
│   │   ├── tasks.py           # Celery tasks
│   │   ├── consumers.py       # WebSocket consumers
│   │   ├── routing.py         # WebSocket routing
│   │   ├── metrics.py         # Prometheus metrics
│   │   └── urls.py           # URL configuration
│   ├── config/                # Django configuration
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── asgi.py
│   │   ├── wsgi.py
│   │   └── urls.py
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   ├── tests/                 # Test suite
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── Dockerfile
│   └── manage.py
│
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # App router pages
│   │   │   ├── (auth)/
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   ├── dashboard/
│   │   │   ├── logs/
│   │   │   └── analytics/
│   │   ├── components/        # React components
│   │   │   ├── auth/
│   │   │   ├── dashboard/
│   │   │   ├── logs/
│   │   │   └── common/
│   │   ├── lib/              # Utility libraries
│   │   │   ├── api.ts
│   │   │   ├── websocket.ts
│   │   │   └── utils.ts
│   │   └── types/            # TypeScript types
│   ├── public/               # Static assets
│   ├── tests/                # Frontend tests
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── nginx/                     # Nginx configuration
│   ├── nginx.conf
│   └── conf.d/
│       ├── default.conf
│       └── status.conf
│
├── logstash/                  # Logstash configuration
│   ├── config/
│   │   └── logstash.yml
│   └── pipeline/
│       └── logstash.conf
│
├── kibana/                    # Kibana configuration
│   └── config/
│       └── kibana.yml
│
├── monitoring/                # Monitoring stack
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── rules/
│   │       ├── alerts.yml
│   │       └── recording.yml
│   ├── grafana/
│   │   ├── grafana.ini
│   │   ├── provisioning/
│   │   └── dashboards/
│   └── alertmanager/
│       └── alertmanager.yml
│
├── k8s/                       # Kubernetes manifests
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── configmap.yaml
│   └── ingress.yaml
│
├── scripts/                   # Utility scripts
│   ├── backup-databases.sh
│   ├── restore-databases.sh
│   └── generate-secrets.sh
│
├── .github/                   # GitHub Actions workflows
│   └── workflows/
│       ├── backend-ci.yml
│       ├── frontend-ci.yml
│       └── deploy-production.yml
│
├── docs/                      # Documentation
│   ├── api/
│   │   └── openapi.yaml
│   └── architecture/
│
├── docker-compose.yml         # Development compose
├── docker-compose.prod.yml    # Production compose
├── docker-compose.monitoring.yml
├── .env.development.example
├── .env.production.example
├── .gitignore
├── README.md
└── DEVELOPER_GUIDE.md
```

### Key Directories

- **backend/api/**: Core Django REST API application
- **frontend/src/**: Next.js application source code
- **monitoring/**: Prometheus, Grafana, Alertmanager configs
- **k8s/**: Kubernetes deployment manifests
- **tests/**: All test files (unit, integration, e2e)

---

## Backend Development

### Local Setup (Without Docker)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements/development.txt

# Set up environment variables
cp ../.env.development.example ../.env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Run development server
python manage.py runserver

# In another terminal, run Celery worker
celery -A config worker --loglevel=INFO

# In another terminal, run Celery beat
celery -A config beat --loglevel=INFO
```

### Django Project Structure

```python
# config/settings/base.py
"""
Base settings shared across all environments
"""

# config/settings/development.py
"""
Development-specific settings
DEBUG=True, relaxed security
"""

# config/settings/production.py
"""
Production settings
DEBUG=False, strict security
"""
```

### Creating a New API Endpoint

1. **Define Model** (if needed):

```python
# backend/api/models/example.py
from django.db import models

class Example(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Examples'
    
    def __str__(self):
        return self.name
```

2. **Create Serializer**:

```python
# backend/api/serializers/example.py
from rest_framework import serializers
from api.models import Example

class ExampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Example
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
```

3. **Create ViewSet**:

```python
# backend/api/views/example_views.py
from rest_framework import viewsets, permissions
from api.models import Example
from api.serializers import ExampleSerializer

class ExampleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Example model.
    Provides CRUD operations.
    """
    queryset = Example.objects.all()
    serializer_class = ExampleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset by user"""
        return self.queryset.filter(user=self.request.user)
```

4. **Register URLs**:

```python
# backend/api/urls.py
from rest_framework.routers import DefaultRouter
from api.views import ExampleViewSet

router = DefaultRouter()
router.register(r'examples', ExampleViewSet, basename='example')

urlpatterns = router.urls
```

5. **Create Migration**:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Adding Celery Tasks

```python
# backend/api/tasks.py
from celery import shared_task
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_log_file(self, file_id):
    """
    Process uploaded log file asynchronously
    """
    try:
        from api.models import LogFile
        
        log_file = LogFile.objects.get(id=file_id)
        log_file.status = 'processing'
        log_file.save()
        
        # Process file
        # ... processing logic ...
        
        log_file.status = 'completed'
        log_file.save()
        
        logger.info(f"Successfully processed log file {file_id}")
        return {'status': 'success', 'file_id': file_id}
        
    except Exception as exc:
        logger.error(f"Error processing log file {file_id}: {str(exc)}")
        log_file.status = 'failed'
        log_file.save()
        
        # Retry task
        raise self.retry(exc=exc, countdown=60)
```

### WebSocket Consumers

```python
# backend/api/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
        
        # Join user-specific group
        self.group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive_json(self, content):
        """Handle incoming messages"""
        message_type = content.get('type')
        
        if message_type == 'ping':
            await self.send_json({'type': 'pong'})
    
    async def notification_message(self, event):
        """Send notification to WebSocket"""
        await self.send_json({
            'type': 'notification',
            'data': event['data']
        })
```

### Custom Management Commands

```python
# backend/api/management/commands/seed_data.py
from django.core.management.base import BaseCommand
from api.models import LogFile

class Command(BaseCommand):
    help = 'Seed database with sample data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of records to create'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        
        for i in range(count):
            LogFile.objects.create(
                filename=f'sample_{i}.log',
                file_size=1024 * i
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {count} log files')
        )
```

Run with:
```bash
python manage.py seed_data --count=20
```

---

## Frontend Development

### Local Setup (Without Docker)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Set up environment variables
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
echo "NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws" >> .env.local

# Run development server
npm run dev

# Access at http://localhost:3000
```

### Project Structure

```
frontend/src/
├── app/                    # App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   ├── (auth)/           # Auth group
│   │   ├── login/
│   │   │   └── page.tsx
│   │   └── register/
│   │       └── page.tsx
│   ├── dashboard/         # Dashboard pages
│   │   └── page.tsx
│   └── logs/             # Logs pages
│       ├── page.tsx
│       └── [id]/
│           └── page.tsx
├── components/            # React components
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   └── RegisterForm.tsx
│   ├── dashboard/
│   │   ├── StatsCard.tsx
│   │   └── ActivityChart.tsx
│   └── common/
│       ├── Button.tsx
│       ├── Input.tsx
│       └── Modal.tsx
├── lib/                  # Utilities
│   ├── api.ts           # API client
│   ├── websocket.ts     # WebSocket client
│   └── utils.ts         # Utility functions
└── types/               # TypeScript types
    ├── api.ts
    └── models.ts
```

### Creating a New Component

```typescript
// frontend/src/components/example/ExampleCard.tsx
import React from 'react';

interface ExampleCardProps {
  title: string;
  description: string;
  onAction?: () => void;
}

export const ExampleCard: React.FC<ExampleCardProps> = ({ 
  title, 
  description, 
  onAction 
}) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-bold mb-2">{title}</h3>
      <p className="text-gray-600 mb-4">{description}</p>
      {onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Action
        </button>
      )}
    </div>
  );
};
```

### Creating a New Page

```typescript
// frontend/src/app/example/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { ExampleCard } from '@/components/example/ExampleCard';
import { api } from '@/lib/api';

export default function ExamplePage() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.get('/examples/');
        setData(response.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Examples</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {data.map((item: any) => (
          <ExampleCard
            key={item.id}
            title={item.title}
            description={item.description}
          />
        ))}
      </div>
    </div>
  );
}
```

### API Client Usage

```typescript
// frontend/src/lib/api.ts usage
import { api } from '@/lib/api';

// GET request
const logs = await api.get('/logs/');

// POST request
const newLog = await api.post('/logs/', {
  filename: 'example.log',
  content: 'log content'
});

// PUT request
const updated = await api.put(`/logs/${id}/`, {
  status: 'processed'
});

// DELETE request
await api.delete(`/logs/${id}/`);

// With authentication
api.setAuthToken('your-jwt-token');
```

### WebSocket Client Usage

```typescript
// frontend/src/lib/websocket.ts usage
import { WebSocketClient } from '@/lib/websocket';

const wsClient = new WebSocketClient('ws://localhost:8000/ws/notifications/');

// Connect
wsClient.connect();

// Listen for messages
wsClient.on('notification', (data) => {
  console.log('Received notification:', data);
});

// Send message
wsClient.send({
  type: 'subscribe',
  channel: 'alerts'
});

// Disconnect
wsClient.disconnect();
```

---

## Database Operations

### Running Migrations

```bash
# Create migrations
docker-compose exec backend python manage.py makemigrations

# Apply migrations
docker-compose exec backend python manage.py migrate

# Show migration status
docker-compose exec backend python manage.py showmigrations

# Rollback migration
docker-compose exec backend python manage.py migrate api 0001_initial
```

### Database Shell Access

```bash
# PostgreSQL
docker-compose exec postgres psql -U elk_user -d elk_vision_dev

# MongoDB
docker-compose exec mongodb mongosh -u elk_mongo -p mongo_password_dev

# Redis
docker-compose exec redis redis-cli -a redis_password_dev

# Django ORM shell
docker-compose exec backend python manage.py shell
```

### Common Database Queries

```python
# Django shell
from api.models import LogFile, Alert, User

# Get all log files
logs = LogFile.objects.all()

# Filter logs by user
user_logs = LogFile.objects.filter(user=request.user)

# Get logs from last 24 hours
from django.utils import timezone
from datetime import timedelta
recent_logs = LogFile.objects.filter(
    created_at__gte=timezone.now() - timedelta(hours=24)
)

# Count logs by status
from django.db.models import Count
status_counts = LogFile.objects.values('status').annotate(
    count=Count('id')
)

# Get logs with related alerts
logs_with_alerts = LogFile.objects.prefetch_related('alerts')

# Bulk create
LogFile.objects.bulk_create([
    LogFile(filename=f'log_{i}.log') for i in range(100)
])

# Update multiple records
LogFile.objects.filter(status='pending').update(status='processing')

# Delete old records
old_date = timezone.now() - timedelta(days=90)
LogFile.objects.filter(created_at__lt=old_date).delete()
```

### Database Backup & Restore

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U elk_user elk_vision_dev > backup.sql

# Restore PostgreSQL
docker-compose exec -T postgres psql -U elk_user elk_vision_dev < backup.sql

# Backup MongoDB
docker-compose exec mongodb mongodump --out /tmp/backup

# Restore MongoDB
docker-compose exec mongodb mongorestore /tmp/backup
```

---

## Testing

### Backend Testing

```bash
# Run all tests
docker-compose exec backend pytest

# Run specific test file
docker-compose exec backend pytest tests/unit/test_models.py

# Run with coverage
docker-compose exec backend pytest --cov=api --cov-report=html

# Run specific test
docker-compose exec backend pytest tests/unit/test_models.py::TestLogFile::test_create

# Run tests in parallel
docker-compose exec backend pytest -n auto
```

### Writing Backend Tests

```python
# tests/unit/test_models.py
import pytest
from api.models import LogFile

@pytest.mark.django_db
class TestLogFile:
    def test_create_log_file(self):
        log = LogFile.objects.create(
            filename='test.log',
            file_size=1024
        )
        assert log.filename == 'test.log'
        assert log.file_size == 1024
    
    def test_log_file_str(self):
        log = LogFile.objects.create(filename='test.log')
        assert str(log) == 'test.log'

# tests/integration/test_api.py
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestLogAPI:
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_list_logs(self, api_client, user):
        api_client.force_authenticate(user=user)
        response = api_client.get('/api/logs/')
        assert response.status_code == 200
    
    def test_create_log(self, api_client, user):
        api_client.force_authenticate(user=user)
        data = {
            'filename': 'new.log',
            'content': 'log content'
        }
        response = api_client.post('/api/logs/', data)
        assert response.status_code == 201
```

### Frontend Testing

```bash
# Run all tests
cd frontend
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test -- LoginForm.test.tsx

# Run in watch mode
npm test -- --watch
```

### Writing Frontend Tests

```typescript
// frontend/tests/components/ExampleCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ExampleCard } from '@/components/example/ExampleCard';

describe('ExampleCard', () => {
  it('renders title and description', () => {
    render(
      <ExampleCard 
        title="Test Title" 
        description="Test Description" 
      />
    );
    
    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
  });

  it('calls onAction when button clicked', () => {
    const mockAction = jest.fn();
    render(
      <ExampleCard 
        title="Test" 
        description="Test" 
        onAction={mockAction}
      />
    );
    
    const button = screen.getByRole('button', { name: /action/i });
    fireEvent.click(button);
    
    expect(mockAction).toHaveBeenCalledTimes(1);
  });
});
```

### E2E Testing

```bash
# Install Playwright
cd frontend
npm install -D @playwright/test

# Run E2E tests
npx playwright test

# Run in UI mode
npx playwright test --ui

# Run specific test
npx playwright test tests/e2e/login.spec.ts
```

```typescript
// frontend/tests/e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test('should login successfully', async ({ page }) => {
    await page.goto('http://localhost:3000/login');
    
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL('http://localhost:3000/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('http://localhost:3000/login');
    
    await page.fill('input[name="username"]', 'invalid');
    await page.fill('input[name="password"]', 'wrong');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('.error')).toContainText('Invalid credentials');
  });
});
```

---

## Code Style & Standards

### Python (Backend)

**Style Guide:** PEP 8

```bash
# Format with Black
black backend/

# Sort imports with isort
isort backend/

# Lint with Flake8
flake8 backend/

# Type checking with mypy
mypy backend/
```

**Configuration:**

```ini
# setup.cfg
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = migrations, .venv, venv

[isort]
profile = black
line_length = 88
skip = migrations

[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

### TypeScript (Frontend)

**Style Guide:** Airbnb/Prettier

```bash
# Format with Prettier
npm run format

# Lint with ESLint
npm run lint

# Type check
npm run type-check
```

**Configuration:**

```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
```

```json
// .eslintrc.json
{
  "extends": [
    "next/core-web-vitals",
    "prettier"
  ],
  "rules": {
    "no-console": "warn",
    "prefer-const": "error"
  }
}
```

### Commit Messages

Follow Conventional Commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```
feat(api): add log file upload endpoint

Implement multipart file upload with validation
and async processing via Celery

Closes #123
```

```
fix(frontend): resolve websocket reconnection issue

WebSocket client now properly handles connection drops
and implements exponential backoff retry strategy
```

---

## Git Workflow

### Branch Strategy

```
main                    # Production-ready code
├── develop            # Development branch
│   ├── feature/xyz   # Feature branches
│   ├── bugfix/abc    # Bug fix branches
│   └── hotfix/urgent # Urgent fixes
└── release/v1.0.0    # Release branches
```

### Workflow

1. **Create Feature Branch:**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/add-export-functionality
```

2. **Make Changes:**
```bash
# Make changes
git add .
git commit -m "feat(api): add log export endpoint"
```

3. **Push and Create PR:**
```bash
git push origin feature/add-export-functionality
# Create Pull Request on GitHub
```

4. **Code Review:**
- Address review comments
- Update branch if needed

5. **Merge:**
```bash
# After approval, merge via GitHub
# Or rebase and merge
git checkout develop
git pull origin develop
git merge --no-ff feature/add-export-functionality
git push origin develop
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

---

## Debugging

### Backend Debugging

```python
# Use Django Debug Toolbar (installed in development)
# Access at: http://localhost:8000/__debug__/

# Use pdb for debugging
import pdb; pdb.set_trace()

# Or use ipdb (better interface)
import ipdb; ipdb.set_trace()

# Print debug info
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

**VS Code Debug Configuration:**

`.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Django",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/backend/manage.py",
      "args": ["runserver", "--noreload"],
      "django": true,
      "justMyCode": false
    }
  ]
}
```

### Frontend Debugging

```typescript
// Use React DevTools (browser extension)

// Console debugging
console.log('Debug:', data);
console.table(data);
console.error('Error:', error);

// Debugger statement
debugger;

// Chrome DevTools
// Sources tab -> Add breakpoints
// Network tab -> Inspect API calls
// React tab -> Inspect component state
```

**VS Code Debug Configuration:**

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Next.js: debug server-side",
      "type": "node-terminal",
      "request": "launch",
      "command": "npm run dev"
    },
    {
      "name": "Next.js: debug client-side",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:3000"
    }
  ]
}
```

### Docker Debugging

```bash
# View container logs
docker-compose logs backend
docker-compose logs -f backend  # Follow logs

# Execute command in container
docker-compose exec backend bash
docker-compose exec backend python manage.py shell

# Inspect container
docker inspect elk_backend

# Check resource usage
docker stats

# View networks
docker network ls
docker network inspect elk-vision-saas_backend_network
```

---

## Common Tasks

### Add New Python Dependency

```bash
# Activate virtual environment
cd backend
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install package
pip install package-name

# Update requirements
pip freeze > requirements/base.txt

# Or add manually to requirements/base.txt
# Then install
pip install -r requirements/base.txt
```

### Add New npm Package

```bash
cd frontend

# Install production dependency
npm install package-name

# Install dev dependency
npm install -D package-name

# Update all packages
npm update

# Check for outdated packages
npm outdated
```

### Reset Database

```bash
# Stop containers
docker-compose down

# Remove volumes
docker volume rm elk-vision-saas_postgres_data

# Start containers
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

### Clear Cache

```bash
# Redis
docker-compose exec redis redis-cli -a redis_password_dev FLUSHALL

# Django cache
docker-compose exec backend python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### Generate API Documentation

```bash
# Generate OpenAPI schema
docker-compose exec backend python manage.py spectacular --file schema.yml

# Serve API docs
# Access at: http://localhost:8000/api/docs/
```

---

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# macOS/Linux
lsof -i :8000
kill -9 <pid>

# Or use different port
docker-compose -p elk-vision-alt up -d
```

#### Permission Denied (Linux)

```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker

# Fix file permissions
sudo chown -R $USER:$USER .
```

#### Module Not Found

```bash
# Rebuild containers
docker-compose build --no-cache

# Reinstall dependencies
docker-compose exec backend pip install -r requirements/development.txt
docker-compose exec frontend npm install
```

#### Database Connection Error

```bash
# Check database container
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
docker-compose exec backend python manage.py dbshell
```

#### WebSocket Connection Failed

```bash
# Check Daphne is running
docker-compose logs backend | grep daphne

# Verify WebSocket URL
echo $NEXT_PUBLIC_WS_URL

# Check nginx config
docker-compose exec nginx nginx -t
```

---

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev/)
- [Docker Documentation](https://docs.docker.com/)
- [Elasticsearch Documentation](https://www.elastic.co/guide/)

---

## Getting Help

1. **Check Documentation:** Review relevant guides first
2. **Search Issues:** Check GitHub issues for similar problems
3. **Ask Team:** Use team chat/Slack for quick questions
4. **Create Issue:** Open detailed GitHub issue for bugs/features
5. **Code Review:** Request PR review for implementation guidance

---

**Last Updated:** December 30, 2025  
**Version:** 1.0.0  
**Maintainer:** Development Team
