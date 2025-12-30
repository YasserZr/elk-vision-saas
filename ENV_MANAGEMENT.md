# Environment Variables Management Guide

This guide explains how to properly manage environment variables for the ELK Vision SaaS platform across different environments.

## Overview

The application uses environment-specific configuration files:

- `.env.development.example` - Development template with safe defaults
- `.env.production.example` - Production template requiring secure secrets
- `.env` - Active environment file (git-ignored)
- `.env.production` - Active production file (git-ignored)

## Quick Start

### Development Setup

```bash
# Copy development template
cp .env.development.example .env

# Start development environment
docker-compose up -d
```

### Production Setup

```bash
# Copy production template
cp .env.production.example .env.production

# Generate secure secrets (see Secrets Generation section)
./scripts/generate-secrets.sh

# Edit configuration
nano .env.production

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

---

## Environment File Structure

### 1. Environment Configuration

```bash
# Determines application behavior
ENVIRONMENT=production  # or development, staging
BUILD_TARGET=production # Docker build target
NODE_ENV=production     # Node.js environment
DEBUG=False            # Django debug mode
```

### 2. Domain & URLs

```bash
# Primary domain
DOMAIN=yourdomain.com
PRODUCTION_DOMAIN=yourdomain.com

# Django allowed hosts (comma-separated)
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# Frontend API endpoints
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
NEXT_PUBLIC_WS_URL=wss://yourdomain.com/ws
NEXT_PUBLIC_KIBANA_URL=https://yourdomain.com/kibana
```

### 3. Security Settings

```bash
# Django secret key (50+ characters)
SECRET_KEY=your-secret-key-here

# CSRF settings
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

# Cookie security
SESSION_COOKIE_SECURE=True    # HTTPS only
CSRF_COOKIE_SECURE=True       # HTTPS only
SESSION_COOKIE_HTTPONLY=True  # No JavaScript access
CSRF_COOKIE_HTTPONLY=True

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS=31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_SSL_REDIRECT=True
```

### 4. Database Configuration

```bash
# PostgreSQL
POSTGRES_DB=elk_vision_prod
POSTGRES_USER=elk_admin
POSTGRES_PASSWORD=strong-password-here
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_MAX_CONNECTIONS=100

# MongoDB
MONGO_DB_NAME=elk_vision_prod
MONGO_USER=elk_mongo_admin
MONGO_PASSWORD=strong-password-here
MONGO_HOST=mongodb
MONGO_PORT=27017

# Redis
REDIS_PASSWORD=strong-password-here
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
```

### 5. Elasticsearch Configuration

```bash
# Authentication
ELASTICSEARCH_PASSWORD=strong-password-here
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_HOST=elasticsearch:9200
ELASTICSEARCH_SCHEME=http

# Cluster settings
ELASTICSEARCH_CLUSTER_NAME=elk-vision-cluster
ELASTICSEARCH_NODE_NAME=node-1

# Java heap size
ES_JAVA_OPTS=-Xms2g -Xmx2g

# Security
ELASTIC_SECURITY_ENABLED=true
```

### 6. Monitoring Configuration

```bash
# Prometheus
PROMETHEUS_RETENTION_DAYS=30
PROMETHEUS_RETENTION_SIZE=10GB

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=strong-password-here
GRAFANA_SECRET_KEY=random-secret-key-here

# Alertmanager - Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#alerts

# Alertmanager - Email
SMTP_HOST=smtp.gmail.com:587
SMTP_USER=alerts@yourdomain.com
SMTP_PASSWORD=smtp-app-password-here
```

---

## Secrets Generation

### Automated Script

Create `scripts/generate-secrets.sh`:

```bash
#!/bin/bash
# Generate all required secrets for production

set -e

SECRETS_DIR="secrets"
mkdir -p $SECRETS_DIR
chmod 700 $SECRETS_DIR

echo "Generating secrets..."

# Django secret key
echo "Generating Django secret key..."
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" > $SECRETS_DIR/django_secret.txt

# Database passwords (32 characters)
echo "Generating database passwords..."
openssl rand -base64 32 > $SECRETS_DIR/postgres_password.txt
openssl rand -base64 32 > $SECRETS_DIR/mongo_password.txt
openssl rand -base64 32 > $SECRETS_DIR/redis_password.txt
openssl rand -base64 32 > $SECRETS_DIR/elastic_password.txt
openssl rand -base64 32 > $SECRETS_DIR/kibana_password.txt

# Kibana encryption key (64 hex characters)
echo "Generating Kibana encryption key..."
openssl rand -hex 32 > $SECRETS_DIR/kibana_encryption.txt

# JWT secret (base64, 64 characters)
echo "Generating JWT secret..."
openssl rand -base64 64 > $SECRETS_DIR/jwt_secret.txt

# Grafana admin password
echo "Generating Grafana password..."
openssl rand -base64 32 > $SECRETS_DIR/grafana_password.txt

# Set secure permissions
chmod 600 $SECRETS_DIR/*.txt

echo "✅ Secrets generated in $SECRETS_DIR/"
echo ""
echo "⚠️  IMPORTANT:"
echo "1. Copy secrets to .env.production"
echo "2. Store secrets in password manager"
echo "3. Delete secrets/ directory after copying"
echo "4. Never commit secrets to version control"

# Display secrets
echo ""
echo "Generated secrets:"
echo "=================="
for file in $SECRETS_DIR/*.txt; do
    name=$(basename $file .txt)
    value=$(cat $file)
    echo "$name: $value"
done
```

Make executable and run:

```bash
chmod +x scripts/generate-secrets.sh
./scripts/generate-secrets.sh
```

### Manual Generation

If you prefer manual generation:

```bash
# Django secret key
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Random password (32 characters)
openssl rand -base64 32

# Hex key for Kibana (64 characters)
openssl rand -hex 32

# JWT secret (base64, 64 characters)
openssl rand -base64 64
```

---

## Environment-Specific Configurations

### Development Environment

**Characteristics:**
- Debug mode enabled
- Relaxed security settings
- Console email backend
- Smaller resource limits
- More verbose logging

**Example `.env`:**

```bash
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=dev-secret-key-not-for-production

# Simple passwords OK for dev
POSTGRES_PASSWORD=dev_password
MONGO_PASSWORD=dev_password
REDIS_PASSWORD=dev_password

# Relaxed security
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Console email (no SMTP needed)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Smaller resources
ES_JAVA_OPTS=-Xms1g -Xmx1g
BACKEND_MEM_LIMIT=1024m
```

### Staging Environment

**Characteristics:**
- Production-like configuration
- Test with real integrations
- Separate databases
- Lower resource allocation

**Example `.env.staging`:**

```bash
ENVIRONMENT=staging
DEBUG=False
SECRET_KEY=<unique-secret-key>

# Staging domain
DOMAIN=staging.yourdomain.com
ALLOWED_HOSTS=staging.yourdomain.com

# Separate databases
POSTGRES_DB=elk_vision_staging
MONGO_DB_NAME=elk_vision_staging

# Strong passwords (different from prod)
POSTGRES_PASSWORD=<staging-password>

# Test SMTP
EMAIL_HOST=smtp.mailtrap.io
EMAIL_HOST_USER=<mailtrap-user>
EMAIL_HOST_PASSWORD=<mailtrap-password>

# Reduced resources
ES_JAVA_OPTS=-Xms2g -Xmx2g
```

### Production Environment

**Characteristics:**
- Maximum security
- Strong passwords
- SSL/TLS enforced
- Full resource allocation
- Production monitoring

**Example `.env.production`:**

```bash
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<extremely-strong-secret-key>

# Production domain
DOMAIN=yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Production databases
POSTGRES_DB=elk_vision_prod
POSTGRES_PASSWORD=<very-strong-password>

# Maximum security
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_SSL_REDIRECT=True

# Production SMTP
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<sendgrid-api-key>

# Full resources
ES_JAVA_OPTS=-Xms4g -Xmx4g
BACKEND_MEM_LIMIT=2048m
```

---

## Using Environment Variables in Code

### Django Settings

```python
# backend/config/settings/base.py
import os
from environ import Env

env = Env()

# Read .env file
env_file = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_file):
    env.read_env(env_file)

# Use environment variables
DEBUG = env.bool('DEBUG', default=False)
SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRES_DB'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('POSTGRES_HOST'),
        'PORT': env('POSTGRES_PORT'),
    }
}
```

### Next.js Frontend

```typescript
// frontend/lib/config.ts
export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
  kibanaUrl: process.env.NEXT_PUBLIC_KIBANA_URL || 'http://localhost:5601',
  environment: process.env.NODE_ENV || 'development',
};

// Usage
import { config } from '@/lib/config';

const response = await fetch(`${config.apiUrl}/logs/`);
```

### Docker Compose

```yaml
services:
  backend:
    environment:
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    # Or use env_file
    env_file:
      - .env.production
```

---

## Security Best Practices

### 1. Never Commit Secrets

```bash
# .gitignore
.env
.env.local
.env.production
.env.staging
.env.*.local
secrets/
*.pem
*.key
*.crt
```

### 2. Use Strong Passwords

**Minimum Requirements:**
- Length: 32+ characters
- Complexity: Uppercase, lowercase, numbers, special chars
- Randomness: Use cryptographic random generators

### 3. Rotate Credentials Regularly

```bash
# Quarterly credential rotation
./scripts/generate-secrets.sh

# Update .env.production with new secrets
nano .env.production

# Restart services with new credentials
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Use Secrets Management Tools

#### Option 1: Docker Secrets

```yaml
secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt

services:
  postgres:
    secrets:
      - postgres_password
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
```

#### Option 2: HashiCorp Vault

```python
import hvac

client = hvac.Client(url='https://vault.yourdomain.com')
client.token = os.environ['VAULT_TOKEN']

secret = client.secrets.kv.v2.read_secret_version(
    path='elk-vision/production'
)

POSTGRES_PASSWORD = secret['data']['data']['postgres_password']
```

#### Option 3: AWS Secrets Manager

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

secrets = get_secret('elk-vision/production')
POSTGRES_PASSWORD = secrets['postgres_password']
```

### 5. Encrypt Sensitive Files

```bash
# Encrypt .env.production
gpg --symmetric --cipher-algo AES256 .env.production

# Decrypt when needed
gpg --decrypt .env.production.gpg > .env.production

# Store encrypted version in secure location
```

### 6. Limit Access

```bash
# Set restrictive permissions
chmod 600 .env.production
chown deploy:deploy .env.production

# Only deploy user can read
ls -la .env.production
# -rw------- 1 deploy deploy 12345 Jan 01 12:00 .env.production
```

---

## Validation & Testing

### Validate Environment File

Create `scripts/validate-env.sh`:

```bash
#!/bin/bash
# Validate environment file has all required variables

ENV_FILE=${1:-.env.production}

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: $ENV_FILE not found"
    exit 1
fi

echo "Validating $ENV_FILE..."

# Required variables
REQUIRED_VARS=(
    "SECRET_KEY"
    "POSTGRES_PASSWORD"
    "MONGO_PASSWORD"
    "REDIS_PASSWORD"
    "ELASTICSEARCH_PASSWORD"
    "JWT_SECRET_KEY"
    "GRAFANA_ADMIN_PASSWORD"
    "DOMAIN"
)

# Check each required variable
MISSING=0
for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" "$ENV_FILE"; then
        echo "❌ Missing: $var"
        MISSING=$((MISSING + 1))
    else
        value=$(grep "^${var}=" "$ENV_FILE" | cut -d'=' -f2-)
        if [[ $value == *"CHANGE_THIS"* ]] || [[ -z "$value" ]]; then
            echo "⚠️  Warning: $var not configured properly"
        else
            echo "✅ $var configured"
        fi
    fi
done

if [ $MISSING -gt 0 ]; then
    echo ""
    echo "❌ Validation failed: $MISSING required variables missing"
    exit 1
fi

echo ""
echo "✅ All required variables present"
```

Run validation:

```bash
chmod +x scripts/validate-env.sh
./scripts/validate-env.sh .env.production
```

### Test Configuration

```bash
# Test if services can read environment variables
docker-compose -f docker-compose.prod.yml config

# Verify Django can load settings
docker-compose -f docker-compose.prod.yml run --rm backend python manage.py check

# Test database connection
docker-compose -f docker-compose.prod.yml run --rm backend python manage.py dbshell --command="SELECT 1;"

# Test Redis connection
docker-compose -f docker-compose.prod.yml run --rm backend python -c "
from django.core.cache import cache
cache.set('test', 'value')
print(cache.get('test'))
"
```

---

## Migration Between Environments

### From Development to Production

1. **Review all variables:**
   ```bash
   diff .env .env.production.example
   ```

2. **Generate new secrets:**
   ```bash
   ./scripts/generate-secrets.sh
   ```

3. **Update production config:**
   ```bash
   cp .env.production.example .env.production
   # Edit and add secrets
   nano .env.production
   ```

4. **Validate:**
   ```bash
   ./scripts/validate-env.sh .env.production
   ```

5. **Deploy:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### From Staging to Production

1. **Copy staging config:**
   ```bash
   cp .env.staging .env.production
   ```

2. **Update domain:**
   ```bash
   sed -i 's/staging.yourdomain.com/yourdomain.com/g' .env.production
   ```

3. **Generate new production secrets:**
   ```bash
   ./scripts/generate-secrets.sh
   # Update .env.production with new secrets
   ```

4. **Update database names:**
   ```bash
   sed -i 's/_staging/_prod/g' .env.production
   ```

---

## Troubleshooting

### Variable Not Loading

```bash
# Check if variable is in file
grep "SECRET_KEY" .env.production

# Check if Docker can see it
docker-compose -f docker-compose.prod.yml exec backend env | grep SECRET_KEY

# Verify Django can read it
docker-compose -f docker-compose.prod.yml exec backend python -c "
from django.conf import settings
print(settings.SECRET_KEY[:10] + '...')
"
```

### Permission Denied

```bash
# Fix file permissions
chmod 600 .env.production
chown $USER:$USER .env.production

# Verify
ls -la .env.production
```

### Syntax Errors

```bash
# Check for syntax errors (no spaces around =)
# ✅ Correct:
KEY=value

# ❌ Incorrect:
KEY = value
KEY= value
KEY =value
```

---

## Reference

### Complete Variable List

See `.env.production.example` for complete list with descriptions.

### Related Documentation

- [PRODUCTION_SECURITY.md](./PRODUCTION_SECURITY.md) - Security best practices
- [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md) - Deployment guide
- Django Environ: https://django-environ.readthedocs.io/
- Docker Secrets: https://docs.docker.com/engine/swarm/secrets/

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0.0
