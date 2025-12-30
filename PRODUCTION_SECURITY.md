# Production Security Best Practices

This document outlines critical security configurations and best practices for deploying the ELK Vision SaaS platform in production.

## Table of Contents

1. [Environment Variables & Secrets Management](#environment-variables--secrets-management)
2. [Container Security](#container-security)
3. [Network Security](#network-security)
4. [Database Security](#database-security)
5. [SSL/TLS Configuration](#ssltls-configuration)
6. [Authentication & Authorization](#authentication--authorization)
7. [Monitoring & Alerting](#monitoring--alerting)
8. [Backup & Disaster Recovery](#backup--disaster-recovery)
9. [Security Hardening Checklist](#security-hardening-checklist)
10. [Incident Response](#incident-response)

---

## Environment Variables & Secrets Management

### Critical Secrets to Rotate

**NEVER use default values in production!** Generate strong, unique secrets for:

#### 1. Generate Django Secret Key
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### 2. Generate Random Passwords (32+ characters)
```bash
# For databases, Redis, etc.
openssl rand -base64 32
```

#### 3. Generate Hex Keys (64 characters for Kibana)
```bash
openssl rand -hex 32
```

#### 4. Generate JWT Secret
```bash
openssl rand -base64 64
```

### Secrets Management Options

#### Option 1: Docker Secrets (Recommended for Docker Swarm)

```yaml
# docker-compose.prod.yml
secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
  django_secret:
    file: ./secrets/django_secret.txt

services:
  backend:
    secrets:
      - postgres_password
      - django_secret
```

Create secrets directory:
```bash
mkdir -p secrets
chmod 700 secrets
echo "your-strong-password" > secrets/postgres_password.txt
chmod 600 secrets/*.txt
```

#### Option 2: HashiCorp Vault

```python
# backend/config/vault.py
import hvac

client = hvac.Client(url='https://vault.yourdomain.com')
client.token = os.environ['VAULT_TOKEN']

# Read secrets
secret = client.secrets.kv.v2.read_secret_version(
    path='elk-vision/production'
)
DATABASE_PASSWORD = secret['data']['data']['postgres_password']
```

#### Option 3: AWS Secrets Manager

```python
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name='us-east-1'
    )
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except ClientError as e:
        raise e
```

#### Option 4: Kubernetes Secrets (for K8s deployments)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: elk-vision-secrets
type: Opaque
data:
  postgres-password: <base64-encoded>
  django-secret: <base64-encoded>
```

### Environment File Security

```bash
# Set proper permissions
chmod 600 .env.production
chown root:root .env.production

# Add to .gitignore
echo ".env.production" >> .gitignore
echo ".env" >> .gitignore
echo "secrets/" >> .gitignore
```

---

## Container Security

### 1. Security Options

All containers should include:

```yaml
services:
  backend:
    security_opt:
      - no-new-privileges:true  # Prevent privilege escalation
    cap_drop:
      - ALL                      # Drop all capabilities
    cap_add:
      - NET_BIND_SERVICE        # Only add needed capabilities
    read_only: true              # Read-only filesystem
    tmpfs:
      - /tmp                     # Writable temp directory
```

### 2. User Permissions

**Never run containers as root!**

```dockerfile
# In Dockerfile
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set ownership
COPY --chown=appuser:appuser . /app

# Switch to non-root user
USER appuser

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
```

### 3. Image Security Scanning

```yaml
# .github/workflows/security-scan.yml
name: Container Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build image
        run: docker build -t elk-vision/backend:${{ github.sha }} ./backend
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'elk-vision/backend:${{ github.sha }}'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
      
      - name: Upload Trivy results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

### 4. Regular Updates

```bash
# Update base images regularly
docker pull python:3.11-slim
docker pull node:20-alpine
docker pull postgres:15-alpine

# Rebuild images
docker-compose -f docker-compose.prod.yml build --no-cache

# Update Python dependencies
pip list --outdated
pip install --upgrade -r requirements.txt

# Update Node dependencies
npm outdated
npm update
```

---

## Network Security

### 1. Network Segmentation

```yaml
networks:
  # Public-facing network
  frontend_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
  
  # Internal backend network
  backend_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/24
  
  # Database network (internal only - no internet access)
  database_network:
    driver: bridge
    internal: true  # Cannot reach external networks
    ipam:
      config:
        - subnet: 172.22.0.0/24
```

### 2. Firewall Rules (UFW)

```bash
# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (change port if using non-standard)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow Prometheus (only from specific IPs)
sudo ufw allow from 10.0.1.0/24 to any port 9090

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status numbered
```

### 3. Nginx Rate Limiting

```nginx
# /nginx/conf.d/rate-limiting.conf
# Define rate limit zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=upload_limit:10m rate=2r/m;

# Connection limits
limit_conn_zone $binary_remote_addr zone=addr:10m;

server {
    # Apply rate limits
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        limit_conn addr 10;
        proxy_pass http://backend:8000;
    }
    
    location /api/auth/ {
        limit_req zone=auth_limit burst=5 nodelay;
        proxy_pass http://backend:8000;
    }
    
    location /api/logs/upload/ {
        limit_req zone=upload_limit burst=3 nodelay;
        client_max_body_size 100M;
        proxy_pass http://backend:8000;
    }
}
```

### 4. IP Whitelisting for Admin

```nginx
# /nginx/conf.d/admin-whitelist.conf
geo $admin_allowed {
    default 0;
    10.0.0.0/8 1;           # Internal network
    203.0.113.0/24 1;       # Office network
    YOUR_IP_ADDRESS 1;      # Your IP
}

server {
    location /admin/ {
        if ($admin_allowed = 0) {
            return 403;
        }
        proxy_pass http://backend:8000;
    }
    
    location /grafana/ {
        if ($admin_allowed = 0) {
            return 403;
        }
        proxy_pass http://grafana:3000;
    }
}
```

---

## Database Security

### 1. PostgreSQL Hardening

```bash
# /data/elk-vision/postgres/postgresql.conf
# Connection settings
listen_addresses = 'localhost,172.22.0.0/24'  # Only internal network
max_connections = 100
password_encryption = scram-sha-256

# SSL settings (recommended)
ssl = on
ssl_cert_file = '/var/lib/postgresql/server.crt'
ssl_key_file = '/var/lib/postgresql/server.key'
ssl_min_protocol_version = 'TLSv1.2'

# Security settings
log_connections = on
log_disconnections = on
log_duration = on
log_statement = 'ddl'
```

```bash
# /data/elk-vision/postgres/pg_hba.conf
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
host    all             all             172.22.0.0/24          scram-sha-256
host    all             all             127.0.0.1/32           scram-sha-256
```

### 2. MongoDB Hardening

```yaml
# MongoDB configuration
security:
  authorization: enabled
  
net:
  bindIp: localhost,172.22.0.0/24
  ssl:
    mode: requireSSL
    PEMKeyFile: /etc/ssl/mongodb.pem
    CAFile: /etc/ssl/ca.pem

operationProfiling:
  mode: slowOp
  slowOpThresholdMs: 100

storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1
```

### 3. Redis Security

```bash
# redis.conf
# Network
bind 127.0.0.1 172.22.0.0/24
protected-mode yes

# Authentication
requirepass YOUR_STRONG_REDIS_PASSWORD

# Security
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG "CONFIG_HIDDEN_NAME"

# TLS/SSL
port 0
tls-port 6379
tls-cert-file /etc/ssl/redis.crt
tls-key-file /etc/ssl/redis.key
tls-ca-cert-file /etc/ssl/ca.crt
```

### 4. Elasticsearch Security

```yaml
# elasticsearch.yml
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.http.ssl.enabled: true

xpack.security.transport.ssl.verification_mode: certificate
xpack.security.transport.ssl.keystore.path: elastic-certificates.p12
xpack.security.transport.ssl.truststore.path: elastic-certificates.p12

# Enable audit logging
xpack.security.audit.enabled: true
xpack.security.audit.logfile.events.include: 
  - access_denied
  - authentication_failed
  - connection_denied
```

---

## SSL/TLS Configuration

### 1. Let's Encrypt with Certbot

```bash
# Initial certificate generation
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@yourdomain.com \
  --agree-tos \
  --no-eff-email \
  -d yourdomain.com \
  -d www.yourdomain.com \
  -d api.yourdomain.com

# Certificate renewal (automated via container)
# The certbot container will auto-renew every 12 hours

# Force renewal
docker-compose -f docker-compose.prod.yml run --rm certbot renew --force-renewal
```

### 2. Nginx SSL Configuration

```nginx
# /nginx/conf.d/ssl.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# SSL session cache
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

# Certificate paths
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### 3. SSL Certificate Monitoring

```yaml
# monitoring/prometheus/rules/ssl-alerts.yml
groups:
  - name: ssl_certificates
    interval: 1h
    rules:
      - alert: SSLCertificateExpiringSoon
        expr: probe_ssl_earliest_cert_expiry - time() < 86400 * 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "SSL certificate expiring soon ({{ $labels.instance }})"
          description: "SSL certificate for {{ $labels.instance }} expires in {{ $value | humanizeDuration }}"
      
      - alert: SSLCertificateExpired
        expr: probe_ssl_earliest_cert_expiry - time() < 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "SSL certificate expired ({{ $labels.instance }})"
          description: "SSL certificate for {{ $labels.instance }} has expired!"
```

---

## Authentication & Authorization

### 1. JWT Configuration

```python
# backend/config/settings/production.py
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),  # Short-lived
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': env('JWT_SECRET_KEY'),
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': 'elk-vision',
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
}
```

### 2. Password Policy

```python
# backend/config/settings/base.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Minimum 12 characters
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom password validator
from django.core.exceptions import ValidationError
import re

class ComplexityValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter.')
        if not re.search(r'[0-9]', password):
            raise ValidationError('Password must contain at least one digit.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Password must contain at least one special character.')
    
    def get_help_text(self):
        return 'Password must contain uppercase, lowercase, digits, and special characters.'
```

### 3. Multi-Factor Authentication (MFA)

```python
# Install: pip install django-otp pyotp qrcode

# backend/api/views/auth_views.py
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp import user_has_device

class MFAEnableView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Create TOTP device
        device = TOTPDevice.objects.create(
            user=user,
            name='default',
            confirmed=False
        )
        
        # Generate QR code
        url = device.config_url
        return Response({
            'secret': device.key,
            'qr_url': url
        })

class MFAVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        token = request.data.get('token')
        
        device = TOTPDevice.objects.get(user=user, name='default')
        
        if device.verify_token(token):
            device.confirmed = True
            device.save()
            return Response({'status': 'MFA enabled'})
        
        return Response({'error': 'Invalid token'}, status=400)
```

### 4. Session Security

```python
# backend/config/settings/production.py

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True  # Extend on activity
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF protection
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_USE_SESSIONS = True
CSRF_COOKIE_AGE = 31449600  # 1 year

# Security middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.middleware.security_headers.SecurityHeadersMiddleware',
]
```

---

## Monitoring & Alerting

### 1. Security Event Logging

```python
# backend/api/middleware/security_logging.py
import logging
from django.utils.deprecation import MiddlewareMixin

security_logger = logging.getLogger('security')

class SecurityLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Log authentication attempts
        if request.path.startswith('/api/auth/'):
            security_logger.info(
                f"Auth attempt: {request.method} {request.path} "
                f"from {self.get_client_ip(request)}"
            )
    
    def process_response(self, request, response):
        # Log failed authentication
        if (request.path.startswith('/api/auth/') and 
            response.status_code in [401, 403]):
            security_logger.warning(
                f"Failed auth: {request.method} {request.path} "
                f"from {self.get_client_ip(request)} "
                f"status={response.status_code}"
            )
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
```

### 2. Failed Login Detection

```python
# backend/api/utils/security.py
from django.core.cache import cache
from django.conf import settings

class LoginAttemptTracker:
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minutes
    
    @classmethod
    def record_attempt(cls, username, ip_address):
        key = f"login_attempt:{ip_address}:{username}"
        attempts = cache.get(key, 0)
        cache.set(key, attempts + 1, cls.LOCKOUT_DURATION)
        return attempts + 1
    
    @classmethod
    def is_locked_out(cls, username, ip_address):
        key = f"login_attempt:{ip_address}:{username}"
        attempts = cache.get(key, 0)
        return attempts >= cls.MAX_ATTEMPTS
    
    @classmethod
    def reset_attempts(cls, username, ip_address):
        key = f"login_attempt:{ip_address}:{username}"
        cache.delete(key)

# Usage in login view
class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        ip = self.get_client_ip(request)
        
        if LoginAttemptTracker.is_locked_out(username, ip):
            return Response(
                {'error': 'Account locked due to multiple failed attempts'},
                status=429
            )
        
        # Authenticate user
        user = authenticate(
            username=username,
            password=request.data.get('password')
        )
        
        if user:
            LoginAttemptTracker.reset_attempts(username, ip)
            # Login success
        else:
            LoginAttemptTracker.record_attempt(username, ip)
            # Login failed
```

### 3. Security Alerts Configuration

```yaml
# monitoring/prometheus/rules/security-alerts.yml
groups:
  - name: security
    interval: 1m
    rules:
      - alert: HighFailedLoginRate
        expr: rate(http_requests_total{path=~"/api/auth/.*", status="401"}[5m]) > 5
        for: 2m
        labels:
          severity: warning
          category: security
        annotations:
          summary: "High rate of failed login attempts"
          description: "{{ $value }} failed logins per second detected"
      
      - alert: UnauthorizedAccessAttempt
        expr: rate(http_requests_total{status="403"}[5m]) > 10
        for: 1m
        labels:
          severity: warning
          category: security
        annotations:
          summary: "High rate of unauthorized access attempts"
          description: "{{ $value }} 403 errors per second"
      
      - alert: PotentialSQLInjection
        expr: increase(django_errors_total{type="DatabaseError"}[5m]) > 20
        for: 1m
        labels:
          severity: critical
          category: security
        annotations:
          summary: "Potential SQL injection attack detected"
          description: "Unusual spike in database errors"
      
      - alert: SuspiciousFileUpload
        expr: rate(file_upload_rejected_total[5m]) > 5
        for: 2m
        labels:
          severity: warning
          category: security
        annotations:
          summary: "High rate of rejected file uploads"
          description: "Potential malicious file upload attempts"
```

---

## Backup & Disaster Recovery

### 1. Database Backup Scripts

```bash
#!/bin/bash
# /scripts/backup-databases.sh

set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="${BACKUP_S3_BUCKET}"

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker exec elk_postgres pg_dump \
  -U ${POSTGRES_USER} \
  -d ${POSTGRES_DB} \
  -F c \
  -f /tmp/postgres_backup_${DATE}.dump

docker cp elk_postgres:/tmp/postgres_backup_${DATE}.dump \
  ${BACKUP_DIR}/postgres_backup_${DATE}.dump

# Backup MongoDB
echo "Backing up MongoDB..."
docker exec elk_mongodb mongodump \
  --username=${MONGO_USER} \
  --password=${MONGO_PASSWORD} \
  --authenticationDatabase=admin \
  --out=/tmp/mongo_backup_${DATE}

docker cp elk_mongodb:/tmp/mongo_backup_${DATE} \
  ${BACKUP_DIR}/mongo_backup_${DATE}

# Backup Elasticsearch indices
echo "Backing up Elasticsearch..."
docker exec elk_elasticsearch \
  curl -X PUT "localhost:9200/_snapshot/backup/snapshot_${DATE}?wait_for_completion=true"

# Compress backups
echo "Compressing backups..."
tar -czf ${BACKUP_DIR}/backup_${DATE}.tar.gz \
  ${BACKUP_DIR}/postgres_backup_${DATE}.dump \
  ${BACKUP_DIR}/mongo_backup_${DATE}

# Upload to S3
if [ -n "$S3_BUCKET" ]; then
  echo "Uploading to S3..."
  aws s3 cp ${BACKUP_DIR}/backup_${DATE}.tar.gz \
    s3://${S3_BUCKET}/backups/
fi

# Cleanup old backups (keep last 30 days)
find ${BACKUP_DIR} -name "backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed: backup_${DATE}.tar.gz"
```

### 2. Automated Backup Schedule

```yaml
# Add to docker-compose.prod.yml
services:
  backup:
    image: alpine:latest
    container_name: elk_backup
    restart: always
    volumes:
      - /backups:/backups
      - ./scripts/backup-databases.sh:/scripts/backup.sh:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_DB=${POSTGRES_DB}
      - MONGO_USER=${MONGO_USER}
      - MONGO_PASSWORD=${MONGO_PASSWORD}
      - BACKUP_S3_BUCKET=${BACKUP_S3_BUCKET}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    command: >
      sh -c "apk add --no-cache docker-cli aws-cli &&
             while true; do
               /scripts/backup.sh;
               sleep 86400;
             done"
```

### 3. Restore Procedures

```bash
#!/bin/bash
# /scripts/restore-databases.sh

set -e

BACKUP_FILE=$1
DATE=$(date +%Y%m%d_%H%M%S)

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: ./restore-databases.sh <backup_file.tar.gz>"
  exit 1
fi

# Extract backup
tar -xzf ${BACKUP_FILE}

# Stop services
docker-compose -f docker-compose.prod.yml stop backend celery_worker

# Restore PostgreSQL
echo "Restoring PostgreSQL..."
docker exec elk_postgres dropdb -U ${POSTGRES_USER} ${POSTGRES_DB}
docker exec elk_postgres createdb -U ${POSTGRES_USER} ${POSTGRES_DB}
docker exec -i elk_postgres pg_restore \
  -U ${POSTGRES_USER} \
  -d ${POSTGRES_DB} \
  < postgres_backup.dump

# Restore MongoDB
echo "Restoring MongoDB..."
docker exec -i elk_mongodb mongorestore \
  --username=${MONGO_USER} \
  --password=${MONGO_PASSWORD} \
  --authenticationDatabase=admin \
  --drop \
  /tmp/mongo_backup

# Restore Elasticsearch
echo "Restoring Elasticsearch..."
docker exec elk_elasticsearch \
  curl -X POST "localhost:9200/_snapshot/backup/snapshot_${DATE}/_restore"

# Restart services
docker-compose -f docker-compose.prod.yml start backend celery_worker

echo "Restore completed!"
```

---

## Security Hardening Checklist

### Pre-Deployment Checklist

- [ ] **Environment Variables**
  - [ ] All secrets generated with strong random values
  - [ ] No default passwords in use
  - [ ] .env.production file permissions set to 600
  - [ ] Environment files added to .gitignore
  - [ ] Secrets stored in vault/secrets manager

- [ ] **Container Security**
  - [ ] All containers run as non-root users
  - [ ] Security options enabled (no-new-privileges)
  - [ ] Read-only filesystems where possible
  - [ ] Resource limits configured
  - [ ] Health checks implemented

- [ ] **Network Security**
  - [ ] Network segmentation configured
  - [ ] Database network set to internal only
  - [ ] Firewall rules configured (UFW/iptables)
  - [ ] Rate limiting enabled in Nginx
  - [ ] IP whitelisting for admin interfaces

- [ ] **Database Security**
  - [ ] Strong passwords for all databases
  - [ ] SSL/TLS enabled for database connections
  - [ ] Audit logging enabled
  - [ ] Regular backup schedule configured
  - [ ] Database networks isolated

- [ ] **SSL/TLS**
  - [ ] Valid SSL certificates installed
  - [ ] TLSv1.2 or higher enforced
  - [ ] HSTS headers configured
  - [ ] Certificate auto-renewal working
  - [ ] OCSP stapling enabled

- [ ] **Application Security**
  - [ ] DEBUG=False in production
  - [ ] Django SECRET_KEY unique and strong
  - [ ] ALLOWED_HOSTS properly configured
  - [ ] CSRF protection enabled
  - [ ] Session security configured
  - [ ] JWT secrets rotated from defaults
  - [ ] Password policy enforced (12+ chars, complexity)
  - [ ] MFA enabled for admin accounts

- [ ] **Monitoring & Logging**
  - [ ] Prometheus metrics collecting
  - [ ] Grafana dashboards configured
  - [ ] Security alerts configured
  - [ ] Failed login detection enabled
  - [ ] Audit logs enabled for all databases
  - [ ] Log retention policy configured

- [ ] **Backup & Recovery**
  - [ ] Automated backup schedule running
  - [ ] Backups encrypted
  - [ ] Backup retention policy configured
  - [ ] Restore procedures tested
  - [ ] Off-site backup storage configured

- [ ] **Compliance**
  - [ ] Data encryption at rest
  - [ ] Data encryption in transit
  - [ ] Privacy policy in place
  - [ ] Terms of service in place
  - [ ] GDPR compliance reviewed (if applicable)
  - [ ] Data retention policies defined

### Post-Deployment Checklist

- [ ] **Verification**
  - [ ] All services healthy
  - [ ] SSL certificate valid
  - [ ] Monitoring dashboards accessible
  - [ ] Alerts configured and tested
  - [ ] Backup jobs running successfully
  - [ ] Log aggregation working

- [ ] **Security Testing**
  - [ ] Penetration testing completed
  - [ ] Vulnerability scanning completed
  - [ ] OWASP Top 10 review completed
  - [ ] Security headers verified (Mozilla Observatory)
  - [ ] SSL/TLS configuration tested (SSL Labs)

- [ ] **Documentation**
  - [ ] Incident response plan documented
  - [ ] On-call procedures documented
  - [ ] Runbook created
  - [ ] Architecture diagram updated
  - [ ] Security contacts documented

---

## Incident Response

### 1. Incident Response Plan

```markdown
# Security Incident Response Procedure

## Severity Levels

**Critical (P0)**: Data breach, complete system compromise
**High (P1)**: Partial system compromise, DDoS attack
**Medium (P2)**: Suspicious activity, failed intrusion attempt
**Low (P3)**: Policy violation, minor security issue

## Response Steps

### 1. Detection & Assessment (0-15 minutes)
- Identify the incident type and severity
- Determine affected systems and data
- Assess the scope and impact
- Activate incident response team

### 2. Containment (15-60 minutes)
- Isolate affected systems
- Block malicious IPs
- Disable compromised accounts
- Take system snapshots for forensics

### 3. Investigation (1-4 hours)
- Review logs and metrics
- Identify attack vectors
- Determine data exposure
- Document all findings

### 4. Remediation (4-24 hours)
- Patch vulnerabilities
- Rotate compromised credentials
- Restore from clean backups
- Apply additional security controls

### 5. Recovery (24-48 hours)
- Restore services gradually
- Monitor for recurrence
- Verify system integrity
- Update security measures

### 6. Post-Incident (48+ hours)
- Complete incident report
- Update security policies
- Conduct lessons learned
- Implement preventive measures
```

### 2. Emergency Contacts

```yaml
# incident-contacts.yml (store securely, not in Git)
incident_response_team:
  primary_contact:
    name: "Security Lead"
    phone: "+1-XXX-XXX-XXXX"
    email: "security@yourdomain.com"
    pagerduty: "https://yourdomain.pagerduty.com"
  
  escalation:
    - name: "CTO"
      phone: "+1-XXX-XXX-XXXX"
      email: "cto@yourdomain.com"
    
    - name: "CEO"
      phone: "+1-XXX-XXX-XXXX"
      email: "ceo@yourdomain.com"
  
  external:
    hosting_provider: "support@hosting.com"
    security_firm: "incidents@security-firm.com"
    legal_counsel: "legal@lawfirm.com"
    law_enforcement: "cybercrime@police.gov"
```

### 3. Emergency Procedures

```bash
#!/bin/bash
# /scripts/emergency-lockdown.sh
# Use in case of active security incident

echo "=== EMERGENCY LOCKDOWN INITIATED ==="

# 1. Take system snapshot
docker-compose -f docker-compose.prod.yml pause

# 2. Block all incoming traffic except admin IPs
sudo ufw default deny incoming
sudo ufw allow from <ADMIN_IP> to any

# 3. Dump current logs
docker-compose -f docker-compose.prod.yml logs > /forensics/incident-logs-$(date +%s).log

# 4. Export current metrics
curl http://prometheus:9090/api/v1/query?query=up > /forensics/metrics-$(date +%s).json

# 5. Rotate all credentials
# (Manual process - use password manager)

# 6. Send alert
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK \
  -H 'Content-Type: application/json' \
  -d '{"text":"SECURITY INCIDENT: Emergency lockdown initiated"}'

echo "=== LOCKDOWN COMPLETE - SYSTEM PAUSED ==="
echo "Review logs in /forensics/"
echo "Contact security team immediately"
```

---

## Regular Security Maintenance

### Daily Tasks
- Review security alerts from monitoring
- Check failed login attempts
- Verify backup completion
- Monitor resource usage for anomalies

### Weekly Tasks
- Review access logs for suspicious activity
- Update container images
- Check SSL certificate expiry dates
- Test alert notifications

### Monthly Tasks
- Rotate credentials and API keys
- Review and update firewall rules
- Conduct security audit
- Test backup restore procedures
- Review user access permissions
- Update security documentation

### Quarterly Tasks
- Perform penetration testing
- Conduct security training
- Review and update security policies
- Audit third-party integrations
- Review compliance requirements

---

## Additional Resources

### Security Tools

- **Container Scanning**: Trivy, Clair, Anchore
- **Secrets Management**: HashiCorp Vault, AWS Secrets Manager, Azure Key Vault
- **WAF**: ModSecurity, AWS WAF, Cloudflare
- **DDoS Protection**: Cloudflare, AWS Shield, Fastly
- **SIEM**: ELK Stack, Splunk, Sumo Logic
- **Vulnerability Scanning**: Nessus, OpenVAS, Qualys

### Security Standards

- OWASP Top 10
- CIS Docker Benchmarks
- NIST Cybersecurity Framework
- ISO 27001
- SOC 2
- GDPR (if applicable)
- HIPAA (if handling health data)

### Useful Commands

```bash
# Check SSL certificate
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates

# Test SSL configuration
docker run --rm -it nmap --script ssl-enum-ciphers -p 443 yourdomain.com

# Scan for vulnerabilities
docker run --rm aquasec/trivy image elk-vision/backend:latest

# Check for exposed secrets
docker run --rm -v $(pwd):/src trufflesecurity/trufflehog filesystem /src

# Security headers check
curl -I https://yourdomain.com | grep -i "security\|strict\|content"
```

---

## Support & Questions

For security concerns or questions about this deployment:

1. **Internal**: Contact your security team
2. **Urgent**: Use emergency procedures above
3. **Non-urgent**: Create a security ticket in your issue tracker
4. **External**: security@yourdomain.com (PGP key: [link])

**Remember**: Security is an ongoing process, not a one-time setup. Stay vigilant!
