# Production Deployment Guide

Complete guide for deploying the ELK Vision SaaS platform to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Initial Configuration](#initial-configuration)
4. [Deployment Process](#deployment-process)
5. [SSL Certificate Setup](#ssl-certificate-setup)
6. [Monitoring Setup](#monitoring-setup)
7. [Post-Deployment](#post-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Minimum Server Requirements

**Production Server:**
- OS: Ubuntu 22.04 LTS or newer
- CPU: 8+ cores
- RAM: 32GB+
- Storage: 500GB+ SSD
- Network: 100Mbps+

**Component Resource Allocation:**
- Elasticsearch: 8GB RAM, 4 CPUs
- PostgreSQL: 4GB RAM, 2 CPUs
- MongoDB: 4GB RAM, 2 CPUs
- Backend: 4GB RAM, 2 CPUs
- Frontend: 2GB RAM, 1 CPU
- Monitoring: 4GB RAM, 2 CPUs
- Other services: 6GB RAM, 2 CPUs

### Software Requirements

- Docker Engine 24.0+
- Docker Compose 2.20+
- Git
- UFW (Uncomplicated Firewall)
- Fail2ban
- AWS CLI (for backups, optional)

### Domain & DNS

- Primary domain: `yourdomain.com`
- API subdomain: `api.yourdomain.com` (optional)
- Monitoring subdomain: `monitoring.yourdomain.com` (optional)

**DNS Records:**
```
A     yourdomain.com           -> YOUR_SERVER_IP
A     www.yourdomain.com       -> YOUR_SERVER_IP
A     api.yourdomain.com       -> YOUR_SERVER_IP
A     monitoring.yourdomain.com -> YOUR_SERVER_IP
```

---

## Server Setup

### 1. Initial Server Configuration

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
  curl \
  wget \
  git \
  ufw \
  fail2ban \
  htop \
  iotop \
  ncdu \
  net-tools \
  ca-certificates \
  gnupg \
  lsb-release

# Create deployment user
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG sudo deploy
sudo mkdir -p /home/deploy/.ssh
sudo cp ~/.ssh/authorized_keys /home/deploy/.ssh/
sudo chown -R deploy:deploy /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys
```

### 2. Install Docker

```bash
# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker deploy

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Verify installation
docker --version
docker compose version
```

### 3. Configure Docker

```bash
# Create Docker daemon configuration
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "live-restore": true,
  "userland-proxy": false,
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
EOF

# Restart Docker
sudo systemctl restart docker
```

### 4. Configure Firewall

```bash
# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (adjust port if needed)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow Prometheus (from specific IPs only)
# Replace with your monitoring server IP
# sudo ufw allow from 10.0.1.0/24 to any port 9090

# Enable firewall
sudo ufw --force enable

# Check status
sudo ufw status numbered
```

### 5. Configure Fail2ban

```bash
# Install fail2ban
sudo apt install -y fail2ban

# Configure fail2ban
sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
destemail = admin@yourdomain.com
sender = fail2ban@yourdomain.com

[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
port = 80,443
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = 80,443
logpath = /var/log/nginx/error.log
EOF

# Start fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 6. System Tuning

```bash
# Increase file descriptor limits
sudo tee -a /etc/security/limits.conf > /dev/null <<EOF
*               soft    nofile          65536
*               hard    nofile          65536
root            soft    nofile          65536
root            hard    nofile          65536
EOF

# Kernel parameters for Elasticsearch
sudo tee -a /etc/sysctl.conf > /dev/null <<EOF
# Elasticsearch requirements
vm.max_map_count=262144
vm.swappiness=1
net.core.somaxconn=65535
net.ipv4.tcp_max_syn_backlog=8192
EOF

# Apply sysctl settings
sudo sysctl -p
```

---

## Initial Configuration

### 1. Clone Repository

```bash
# Switch to deploy user
sudo su - deploy

# Create application directory
sudo mkdir -p /opt/elk-vision
sudo chown deploy:deploy /opt/elk-vision
cd /opt/elk-vision

# Clone repository
git clone https://github.com/yourusername/elk-vision-saas.git .

# Checkout production branch
git checkout production
```

### 2. Create Data Directories

```bash
# Create persistent data directories
sudo mkdir -p /data/elk-vision/{postgres,mongodb,redis,elasticsearch,prometheus,grafana}
sudo mkdir -p /backups/elk-vision
sudo mkdir -p /var/log/elk-vision

# Set ownership
sudo chown -R deploy:deploy /data/elk-vision
sudo chown -R deploy:deploy /backups/elk-vision
sudo chown -R deploy:deploy /var/log/elk-vision

# Set permissions
sudo chmod -R 755 /data/elk-vision
sudo chmod -R 700 /backups/elk-vision
```

### 3. Generate Secrets

```bash
# Create secrets directory
mkdir -p /opt/elk-vision/secrets
chmod 700 /opt/elk-vision/secrets

# Generate secrets
# Django secret key
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" > secrets/django_secret.txt

# PostgreSQL password
openssl rand -base64 32 > secrets/postgres_password.txt

# MongoDB password
openssl rand -base64 32 > secrets/mongo_password.txt

# Redis password
openssl rand -base64 32 > secrets/redis_password.txt

# Elasticsearch password
openssl rand -base64 32 > secrets/elastic_password.txt

# Kibana password
openssl rand -base64 32 > secrets/kibana_password.txt

# Kibana encryption key (64 chars)
openssl rand -hex 32 > secrets/kibana_encryption.txt

# JWT secret
openssl rand -base64 64 > secrets/jwt_secret.txt

# Grafana password
openssl rand -base64 32 > secrets/grafana_password.txt

# Set permissions
chmod 600 secrets/*.txt
```

### 4. Configure Environment Variables

```bash
# Copy production environment template
cp .env.production.example .env.production

# Edit environment file
nano .env.production
```

**Update the following variables:**

```bash
# Domain Configuration
DOMAIN=yourdomain.com
PRODUCTION_DOMAIN=yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# URLs
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
NEXT_PUBLIC_WS_URL=wss://yourdomain.com/ws

# Secrets (paste from secrets/*.txt files)
SECRET_KEY=<paste from secrets/django_secret.txt>
POSTGRES_PASSWORD=<paste from secrets/postgres_password.txt>
MONGO_PASSWORD=<paste from secrets/mongo_password.txt>
REDIS_PASSWORD=<paste from secrets/redis_password.txt>
ELASTICSEARCH_PASSWORD=<paste from secrets/elastic_password.txt>
KIBANA_PASSWORD=<paste from secrets/kibana_password.txt>
KIBANA_ENCRYPTION_KEY=<paste from secrets/kibana_encryption.txt>
JWT_SECRET_KEY=<paste from secrets/jwt_secret.txt>
GRAFANA_ADMIN_PASSWORD=<paste from secrets/grafana_password.txt>

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your_smtp_password

# Monitoring - Slack Webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#alerts

# SSL Configuration
SSL_CERTIFICATE_EMAIL=admin@yourdomain.com
```

**Set permissions:**
```bash
chmod 600 .env.production
```

---

## Deployment Process

### 1. Build Images

```bash
cd /opt/elk-vision

# Build all images
docker compose -f docker-compose.prod.yml build

# Verify images
docker images | grep elk-vision
```

### 2. Start Core Services

```bash
# Start databases first
docker compose -f docker-compose.prod.yml up -d postgres mongodb redis elasticsearch

# Wait for services to be healthy (may take 2-3 minutes)
docker compose -f docker-compose.prod.yml ps

# Check health
docker compose -f docker-compose.prod.yml exec postgres pg_isready
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### 3. Initialize Databases

```bash
# Run Django migrations
docker compose -f docker-compose.prod.yml run --rm backend python manage.py migrate

# Create superuser
docker compose -f docker-compose.prod.yml run --rm backend python manage.py createsuperuser

# Collect static files
docker compose -f docker-compose.prod.yml run --rm backend python manage.py collectstatic --noinput
```

### 4. Start Application Services

```bash
# Start ELK stack
docker compose -f docker-compose.prod.yml up -d logstash kibana

# Start backend and workers
docker compose -f docker-compose.prod.yml up -d backend celery_worker celery_beat

# Start frontend
docker compose -f docker-compose.prod.yml up -d frontend

# Start nginx (without SSL initially)
docker compose -f docker-compose.prod.yml up -d nginx

# Verify all services
docker compose -f docker-compose.prod.yml ps
```

---

## SSL Certificate Setup

### 1. Configure Nginx for HTTP (temporarily)

Edit `nginx/conf.d/default.conf` to initially serve HTTP for certbot validation:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://frontend:3000;
    }
}
```

Reload nginx:
```bash
docker compose -f docker-compose.prod.yml restart nginx
```

### 2. Obtain SSL Certificates

```bash
# Get certificates for main domain
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@yourdomain.com \
  --agree-tos \
  --no-eff-email \
  -d yourdomain.com \
  -d www.yourdomain.com

# Verify certificates
sudo ls -la /var/lib/docker/volumes/elk-vision-saas_certbot_conf/_data/live/yourdomain.com/
```

### 3. Configure Nginx with SSL

Now update `nginx/conf.d/default.conf` with full SSL configuration (already in the file).

Reload nginx:
```bash
docker compose -f docker-compose.prod.yml restart nginx
```

### 4. Test SSL Configuration

```bash
# Test with curl
curl -I https://yourdomain.com

# Check SSL grade
docker run --rm -it nmap --script ssl-enum-ciphers -p 443 yourdomain.com

# Online test: https://www.ssllabs.com/ssltest/
```

---

## Monitoring Setup

### 1. Start Monitoring Stack

```bash
# Start Prometheus
docker compose -f docker-compose.monitoring.yml up -d prometheus

# Start exporters
docker compose -f docker-compose.monitoring.yml up -d \
  node-exporter \
  cadvisor \
  postgres-exporter \
  mongodb-exporter \
  redis-exporter \
  elasticsearch-exporter \
  nginx-exporter \
  blackbox-exporter

# Start Alertmanager
docker compose -f docker-compose.monitoring.yml up -d alertmanager

# Start Grafana
docker compose -f docker-compose.monitoring.yml up -d grafana

# Verify all monitoring services
docker compose -f docker-compose.monitoring.yml ps
```

### 2. Access Grafana

1. Navigate to: `http://your-server-ip:3000`
2. Login with:
   - Username: `admin`
   - Password: (from `GRAFANA_ADMIN_PASSWORD` in .env.production)
3. Dashboards should auto-load from provisioning

### 3. Configure Alertmanager

Edit `monitoring/alertmanager/alertmanager.yml` with your notification channels:

```yaml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        
  - name: 'email'
    email_configs:
      - to: 'ops@yourdomain.com'
        from: 'alertmanager@yourdomain.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@yourdomain.com'
        auth_password: 'YOUR_SMTP_PASSWORD'
```

Reload Alertmanager:
```bash
docker compose -f docker-compose.monitoring.yml restart alertmanager
```

### 4. Test Alerts

```bash
# Trigger a test alert
docker compose -f docker-compose.monitoring.yml exec prometheus \
  promtool check rules monitoring/prometheus/rules/alerts.yml

# Send test alert
curl -X POST http://localhost:9093/api/v1/alerts -d '[{
  "labels": {
    "alertname": "TestAlert",
    "severity": "warning"
  },
  "annotations": {
    "summary": "Test alert from deployment"
  }
}]'
```

---

## Post-Deployment

### 1. Verify All Services

```bash
# Check all containers
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.monitoring.yml ps

# Check logs for errors
docker compose -f docker-compose.prod.yml logs --tail=50 backend
docker compose -f docker-compose.prod.yml logs --tail=50 frontend
docker compose -f docker-compose.prod.yml logs --tail=50 nginx

# Test backend health
curl http://localhost:8000/api/health/

# Test frontend
curl http://localhost:3000/

# Test through nginx
curl https://yourdomain.com/api/health/
```

### 2. Create Initial Data

```bash
# Access Django admin
# Navigate to: https://yourdomain.com/admin/

# Or create test data via shell
docker compose -f docker-compose.prod.yml exec backend python manage.py shell

# In the Python shell:
from api.models import LogFile
# Create test objects...
```

### 3. Configure Backup Automation

```bash
# Make backup script executable
chmod +x scripts/backup-databases.sh

# Test backup manually
./scripts/backup-databases.sh

# Add to crontab
crontab -e

# Add line (runs at 2 AM daily):
0 2 * * * /opt/elk-vision/scripts/backup-databases.sh >> /var/log/elk-vision/backup.log 2>&1
```

### 4. Configure Log Rotation

```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/elk-vision > /dev/null <<EOF
/var/log/elk-vision/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
    sharedscripts
    postrotate
        docker compose -f /opt/elk-vision/docker-compose.prod.yml restart backend nginx
    endscript
}
EOF
```

### 5. Enable Auto-start on Reboot

```bash
# Create systemd service
sudo tee /etc/systemd/system/elk-vision.service > /dev/null <<EOF
[Unit]
Description=ELK Vision SaaS Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/elk-vision
User=deploy
Group=deploy

# Start services
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStart=/usr/bin/docker compose -f docker-compose.monitoring.yml up -d

# Stop services
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
ExecStop=/usr/bin/docker compose -f docker-compose.monitoring.yml down

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable elk-vision.service

# Test service
sudo systemctl start elk-vision.service
sudo systemctl status elk-vision.service
```

### 6. Performance Optimization

```bash
# Enable Redis persistence
docker compose -f docker-compose.prod.yml exec redis redis-cli CONFIG SET save "900 1 300 10 60 10000"

# Optimize Elasticsearch
docker compose -f docker-compose.prod.yml exec elasticsearch curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "indices.memory.index_buffer_size": "20%",
    "indices.memory.min_index_buffer_size": "96mb"
  }
}'

# Check PostgreSQL performance
docker compose -f docker-compose.prod.yml exec postgres psql -U elk_admin elk_vision_prod -c "SELECT * FROM pg_stat_activity;"
```

---

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check container logs
docker compose -f docker-compose.prod.yml logs <service_name>

# Check container status
docker compose -f docker-compose.prod.yml ps

# Inspect container
docker inspect <container_name>

# Restart specific service
docker compose -f docker-compose.prod.yml restart <service_name>
```

#### 2. Database Connection Errors

```bash
# Check if database is healthy
docker compose -f docker-compose.prod.yml exec postgres pg_isready

# Test connection from backend
docker compose -f docker-compose.prod.yml exec backend python manage.py dbshell

# Check database logs
docker compose -f docker-compose.prod.yml logs postgres

# Verify environment variables
docker compose -f docker-compose.prod.yml exec backend env | grep POSTGRES
```

#### 3. Elasticsearch Issues

```bash
# Check cluster health
docker compose -f docker-compose.prod.yml exec elasticsearch curl -X GET "localhost:9200/_cluster/health?pretty"

# Check indices
docker compose -f docker-compose.prod.yml exec elasticsearch curl -X GET "localhost:9200/_cat/indices?v"

# Increase heap size if needed (edit .env.production)
ES_JAVA_OPTS=-Xms4g -Xmx4g
```

#### 4. SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in /var/lib/docker/volumes/elk-vision-saas_certbot_conf/_data/live/yourdomain.com/fullchain.pem -noout -dates

# Manually renew certificate
docker compose -f docker-compose.prod.yml run --rm certbot renew --force-renewal

# Check nginx SSL configuration
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```

#### 5. High Memory Usage

```bash
# Check container resource usage
docker stats

# Check system memory
free -h

# Reduce Elasticsearch heap (if too high)
# Edit .env.production: ES_JAVA_OPTS=-Xms2g -Xmx2g

# Restart services
docker compose -f docker-compose.prod.yml restart
```

#### 6. Slow Performance

```bash
# Check disk I/O
iostat -x 1

# Check disk space
df -h
du -sh /data/elk-vision/*

# Check network latency
docker compose -f docker-compose.prod.yml exec backend ping elasticsearch

# Review slow queries (PostgreSQL)
docker compose -f docker-compose.prod.yml exec postgres psql -U elk_admin elk_vision_prod -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### Debugging Commands

```bash
# View all containers
docker ps -a

# View all networks
docker network ls

# View all volumes
docker volume ls

# Enter container shell
docker compose -f docker-compose.prod.yml exec backend bash

# View real-time logs
docker compose -f docker-compose.prod.yml logs -f backend

# Check resource constraints
docker inspect <container_name> | grep -A 10 "Resources"

# Test network connectivity between containers
docker compose -f docker-compose.prod.yml exec backend ping postgres
docker compose -f docker-compose.prod.yml exec backend nc -zv elasticsearch 9200
```

### Rollback Procedure

If deployment fails:

```bash
# Stop all services
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.monitoring.yml down

# Restore from backup
./scripts/restore-databases.sh /backups/elk-vision/backup_YYYYMMDD_HHMMSS.tar.gz

# Checkout previous version
git log --oneline
git checkout <previous_commit_hash>

# Rebuild and restart
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

---

## Maintenance

### Daily Tasks

- Review monitoring dashboards
- Check alert notifications
- Verify backup completion
- Review application logs

### Weekly Tasks

- Update container images
- Review security logs
- Check disk space
- Test backup restore (monthly at minimum)

### Monthly Tasks

- Rotate credentials
- Review access logs
- Conduct security audit
- Update documentation

---

## Additional Resources

- [PRODUCTION_SECURITY.md](./PRODUCTION_SECURITY.md) - Complete security guide
- [MONITORING_GUIDE.md](./MONITORING_GUIDE.md) - Monitoring documentation
- [README.md](./README.md) - Project overview
- Docker documentation: https://docs.docker.com/
- Django documentation: https://docs.djangoproject.com/
- Next.js documentation: https://nextjs.org/docs

---

## Support

For deployment issues:

1. Check logs: `docker compose logs <service>`
2. Review documentation in this guide
3. Check GitHub Issues: https://github.com/yourusername/elk-vision-saas/issues
4. Contact: devops@yourdomain.com

---

**Last Updated**: 2025-01-XX
**Version**: 1.0.0
