# MongoDB & Redis Integration Guide

## Overview

This document describes the MongoDB and Redis integration for the ELK Vision SaaS platform. MongoDB stores user profiles and log metadata, while Redis provides session caching, query caching, and rate limiting.

## Architecture

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Django App    │─────▶│   MongoDB    │      │      Redis      │
│                 │      │              │      │                 │
│  - User Mgmt    │      │ - Profiles   │      │ - Sessions      │
│  - Log Upload   │      │ - Metadata   │      │ - Query Cache   │
│  - API Routes   │      │ - Dashboards │      │ - Rate Limit    │
└─────────────────┘      └──────────────┘      └─────────────────┘
        │                                               │
        │                                               │
        └───────────────────┬───────────────────────────┘
                           ▼
                  ┌──────────────────┐
                  │  Elasticsearch   │
                  │   (Log Storage)  │
                  └──────────────────┘
```

## MongoDB Integration

### Connection Management

**File:** `backend/app/core/mongodb.py`

```python
from app.core.mongodb import get_mongo_client, get_mongo_db, get_collection

# Get database
db = get_mongo_db()

# Get specific collection
users_collection = get_collection('user_profiles')
```

### Collections

1. **user_profiles** - Extended user information
2. **log_metadata** - Log upload tracking
3. **dashboards** - User dashboards
4. **alerts** - Alert configurations
5. **api_keys** - API key management
6. **audit_logs** - Audit trail

### User Profile Model

**File:** `backend/app/users/models_mongo.py`

**Schema:**
```python
{
    "_id": ObjectId,
    "user_id": int,              # Django User ID
    "tenant_id": str,            # Tenant identifier
    "organization": str,         # Organization name
    "role": str,                 # viewer, admin, superadmin
    "preferences": {
        "theme": str,            # light, dark
        "timezone": str,
        "notifications": {
            "email": bool,
            "browser": bool,
            "slack": bool
        },
        "default_dashboard": str
    },
    "api_quota": {
        "logs_per_day": int,
        "api_calls_per_hour": int,
        "retention_days": int,
        "usage": {
            "logs_uploaded": int,
            "api_calls": int
        }
    },
    "created_at": datetime,
    "updated_at": datetime,
    "last_login": datetime,
    "metadata": {}               # Extensible metadata
}
```

**Indexes:**
- `user_id` (unique)
- `tenant_id`
- `(tenant_id, role)`
- `created_at`

### Log Metadata Model

**File:** `backend/app/logs/models_mongo.py`

**Schema:**
```python
{
    "_id": ObjectId,
    "upload_id": str,            # Unique upload ID
    "task_id": str,              # Celery task ID
    "tenant_id": str,
    "user_id": int,
    "source": str,               # Source identifier
    "environment": str,          # production, staging, etc.
    "service_name": str,
    "file_name": str,
    "file_size": int,            # Bytes
    "format_type": str,          # json, csv, text
    "log_count": int,            # Number of log entries
    "status": str,               # pending, processing, success, failed
    "processing_time": float,    # Seconds
    "ingestion_method": str,     # logstash, elasticsearch
    "tags": [],
    "created_at": datetime,
    "updated_at": datetime,
    "indexed_at": datetime,
    "errors": [],
    "metadata": {}
}
```

**Indexes:**
- `upload_id` (unique)
- `task_id`
- `tenant_id`
- `(tenant_id, status)`
- `(tenant_id, created_at)`
- `(tenant_id, user_id, created_at)`
- `(tenant_id, source, environment)`

## Redis Integration

### Connection Management

**File:** `backend/app/core/redis_cache.py`

```python
from app.core.redis_cache import (
    SessionCache,
    QueryCache,
    RateLimiter,
    DistributedLock
)
```

### Redis Databases

- **DB 0**: Celery broker
- **DB 1**: Django cache backend
- **DB 2**: Application cache (direct Redis operations)

### Session Caching

```python
# Cache user session
SessionCache.set_user_session(user_id, session_data, ttl=3600)

# Get cached session
session = SessionCache.get_user_session(user_id)

# Delete session
SessionCache.delete_user_session(user_id)

# JWT blacklist
SessionCache.set_jwt_blacklist(token, ttl=3600)
is_blacklisted = SessionCache.is_jwt_blacklisted(token)
```

### Query Result Caching

```python
# Cache query result
QueryCache.set('user_profile:123', data, ttl=300)

# Get cached result
data = QueryCache.get('user_profile:123')

# Delete cache
QueryCache.delete('user_profile:123')

# Invalidate pattern
QueryCache.invalidate_pattern('user:123:*')
```

### Rate Limiting

```python
# Check rate limit
is_allowed = RateLimiter.is_allowed(
    key='api:user:123',
    max_requests=100,
    window=3600  # 1 hour
)

# Get remaining requests
remaining = RateLimiter.get_remaining('api:user:123', max_requests=100)
```

### Distributed Locking

```python
# Context manager
with DistributedLock('process:logs:upload123', timeout=10):
    # Critical section
    process_upload()

# Manual control
lock = DistributedLock('critical:section')
if lock.acquire():
    try:
        # Do work
        pass
    finally:
        lock.release()
```

## API Endpoints

### User Profile Routes

**Base URL:** `/api/v1/users/`

#### Get Current User Profile
```http
GET /api/v1/users/profile/
Authorization: Bearer <token>
```

**Response:**
```json
{
    "_id": "507f1f77bcf86cd799439011",
    "user_id": 1,
    "tenant_id": "acme-corp",
    "organization": "Acme Corporation",
    "role": "admin",
    "preferences": {
        "theme": "dark",
        "timezone": "America/New_York",
        "notifications": {
            "email": true,
            "browser": true,
            "slack": false
        }
    },
    "api_quota": {
        "logs_per_day": 100000,
        "api_calls_per_hour": 1000,
        "retention_days": 90
    },
    "username": "john.doe",
    "email": "john@acme.com"
}
```

#### Update User Profile
```http
PATCH /api/v1/users/profile/
Authorization: Bearer <token>
Content-Type: application/json

{
    "preferences": {
        "theme": "light",
        "notifications": {
            "email": false
        }
    }
}
```

#### Create User Profile
```http
POST /api/v1/users/profile/create/
Authorization: Bearer <token>
Content-Type: application/json

{
    "tenant_id": "acme-corp",
    "organization": "Acme Corporation",
    "role": "viewer"
}
```

#### Get API Quota
```http
GET /api/v1/users/profile/quota/
Authorization: Bearer <token>
```

#### List Tenant Users
```http
GET /api/v1/users/tenant/users/?page=1&size=20
Authorization: Bearer <token>
```

### Log Metadata Routes

**Base URL:** `/api/v1/logs/`

#### List Log Metadata
```http
GET /api/v1/logs/metadata/?page=1&size=20&status=success
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` - Page number (default: 1)
- `size` - Page size (default: 20, max: 100)
- `status` - Filter by status (pending, processing, success, failed)
- `source` - Filter by source
- `environment` - Filter by environment
- `service_name` - Filter by service name

**Response:**
```json
{
    "metadata": [
        {
            "_id": "507f1f77bcf86cd799439011",
            "upload_id": "upload_20251124_123456",
            "task_id": "abc123-def456",
            "tenant_id": "acme-corp",
            "user_id": 1,
            "source": "api-service",
            "environment": "production",
            "file_name": "app.log",
            "file_size": 1048576,
            "format_type": "json",
            "log_count": 1500,
            "status": "success",
            "processing_time": 2.5,
            "created_at": "2025-11-24T10:00:00Z",
            "indexed_at": "2025-11-24T10:00:03Z"
        }
    ],
    "page": 1,
    "size": 20,
    "count": 1
}
```

#### Get Metadata by Upload ID
```http
GET /api/v1/logs/metadata/<upload_id>/
Authorization: Bearer <token>
```

#### Get Metadata by Task ID
```http
GET /api/v1/logs/metadata/task/<task_id>/
Authorization: Bearer <token>
```

#### Get Upload Statistics
```http
GET /api/v1/logs/metadata/stats/?days=30
Authorization: Bearer <token>
```

**Response:**
```json
{
    "period_days": 30,
    "total_uploads": 150,
    "total_logs": 450000,
    "total_size_bytes": 536870912,
    "by_status": {
        "success": {
            "count": 145,
            "total_logs": 435000,
            "avg_processing_time": 2.3
        },
        "failed": {
            "count": 5,
            "total_logs": 15000,
            "avg_processing_time": null
        }
    }
}
```

#### Get Recent Uploads
```http
GET /api/v1/logs/metadata/recent/?limit=10
Authorization: Bearer <token>
```

#### Delete Metadata
```http
DELETE /api/v1/logs/metadata/<upload_id>/
Authorization: Bearer <token>
```

### Admin Routes

#### Get Any User Profile (Admin)
```http
GET /api/v1/users/admin/profile/<user_id>/
Authorization: Bearer <admin_token>
```

#### Delete User Profile (Admin)
```http
DELETE /api/v1/users/admin/profile/<user_id>/
Authorization: Bearer <admin_token>
```

#### Initialize MongoDB Indexes
```http
POST /api/v1/users/admin/initialize-indexes/
Authorization: Bearer <admin_token>
```

```http
POST /api/v1/logs/admin/initialize-metadata-indexes/
Authorization: Bearer <admin_token>
```

## Usage Examples

### Python Client

```python
import requests

API_BASE = 'http://localhost:8000/api/v1'
TOKEN = 'your_jwt_token'

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

# Get user profile
response = requests.get(f'{API_BASE}/users/profile/', headers=headers)
profile = response.json()

# Update preferences
response = requests.patch(
    f'{API_BASE}/users/profile/',
    headers=headers,
    json={
        'preferences': {
            'theme': 'dark',
            'notifications': {
                'email': True
            }
        }
    }
)

# Get log metadata
response = requests.get(
    f'{API_BASE}/logs/metadata/',
    headers=headers,
    params={'status': 'success', 'page': 1}
)
metadata_list = response.json()['metadata']

# Get statistics
response = requests.get(
    f'{API_BASE}/logs/metadata/stats/',
    headers=headers,
    params={'days': 7}
)
stats = response.json()
```

### JavaScript/Fetch

```javascript
const API_BASE = 'http://localhost:8000/api/v1';
const token = 'your_jwt_token';

// Get user profile
const response = await fetch(`${API_BASE}/users/profile/`, {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
const profile = await response.json();

// Update profile
await fetch(`${API_BASE}/users/profile/`, {
    method: 'PATCH',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        preferences: {
            theme: 'light'
        }
    })
});

// Get recent uploads
const recentResponse = await fetch(
    `${API_BASE}/logs/metadata/recent/?limit=5`,
    {
        headers: { 'Authorization': `Bearer ${token}` }
    }
);
const recent = await recentResponse.json();
```

## Configuration

### Environment Variables

Add to `.env`:

```bash
# MongoDB Configuration
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB_NAME=elk_vision
MONGO_USER=admin
MONGO_PASSWORD=password

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
```

### Django Settings

Already configured in `backend/config/settings.py`:

```python
# MongoDB
MONGODB = {
    'host': config('MONGO_HOST', default='mongodb'),
    'port': int(config('MONGO_PORT', default=27017)),
    'database': config('MONGO_DB_NAME', default='elk_vision'),
    'username': config('MONGO_USER', default='admin'),
    'password': config('MONGO_PASSWORD', default='password'),
    'authSource': 'admin',
}

# Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/1',
    }
}
```

## Initialization

### Create MongoDB Indexes

```bash
curl -X POST http://localhost:8000/api/v1/users/admin/initialize-indexes/ \
  -H "Authorization: Bearer <admin_token>"

curl -X POST http://localhost:8000/api/v1/logs/admin/initialize-metadata-indexes/ \
  -H "Authorization: Bearer <admin_token>"
```

Or use Django shell:

```python
from app.users.models_mongo import create_user_profile_indexes
from app.logs.models_mongo import create_log_metadata_indexes

create_user_profile_indexes()
create_log_metadata_indexes()
```

## Health Checks

The `/health/` endpoint now checks MongoDB and Redis:

```bash
curl http://localhost:8000/health/
```

**Response:**
```json
{
    "status": "healthy",
    "version": "v1",
    "checks": {
        "database": {
            "status": "up",
            "type": "sqlite"
        },
        "mongodb": {
            "status": "healthy",
            "connected": true,
            "response_time_ms": 5
        },
        "redis": {
            "status": "healthy",
            "connected": true,
            "used_memory_human": "1.23M",
            "connected_clients": 3
        },
        "elasticsearch": {
            "status": "up",
            "cluster_status": "green"
        }
    }
}
```

## Best Practices

1. **Always use connection utilities:**
   ```python
   from app.core.mongodb import get_collection
   from app.core.redis_cache import QueryCache
   ```

2. **Cache frequently accessed data:**
   ```python
   cached = QueryCache.get(cache_key)
   if not cached:
       cached = expensive_query()
       QueryCache.set(cache_key, cached, ttl=300)
   ```

3. **Implement rate limiting:**
   ```python
   if not RateLimiter.is_allowed(f'api:user:{user_id}', 100, 3600):
       return Response({'error': 'Rate limit exceeded'}, status=429)
   ```

4. **Use distributed locks for critical sections:**
   ```python
   with DistributedLock(f'upload:{upload_id}'):
       process_upload(upload_id)
   ```

5. **Track API usage:**
   ```python
   UserProfile.increment_api_usage(user_id, 'logs_uploaded', count)
   ```

## Troubleshooting

### MongoDB Connection Issues

```bash
# Check MongoDB is running
docker-compose ps mongodb

# Check logs
docker-compose logs mongodb

# Test connection
python manage.py shell
>>> from app.core.mongodb import get_mongo_client
>>> client = get_mongo_client()
>>> client.admin.command('ping')
```

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli -h localhost -p 6379 ping

# Python test
python manage.py shell
>>> from app.core.redis_cache import get_redis_client
>>> client = get_redis_client()
>>> client.ping()
```

### Cache Not Working

```python
# Clear all cache
from django.core.cache import cache
cache.clear()

# Or specific pattern
from app.core.redis_cache import QueryCache
QueryCache.invalidate_pattern('user:*')
```

## Performance Tips

1. **Index Optimization:** Ensure all indexes are created
2. **Cache Tuning:** Adjust TTL based on data update frequency
3. **Connection Pooling:** Use singleton pattern for connections
4. **Batch Operations:** Use MongoDB bulk operations for multiple updates
5. **Redis Pipeline:** Use Redis pipelines for multiple commands

## Security Considerations

1. **Tenant Isolation:** Always filter by tenant_id
2. **Access Control:** Verify user permissions before data access
3. **Rate Limiting:** Implement per-user and per-tenant limits
4. **Input Validation:** Validate all inputs before MongoDB queries
5. **Secure Connections:** Use SSL/TLS in production
