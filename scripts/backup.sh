#!/bin/bash

# ELK Vision SaaS - Backup Script

set -e

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

echo "💾 Creating backup in $BACKUP_DIR..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup MongoDB
echo "📦 Backing up MongoDB..."
docker-compose exec -T mongodb mongodump \
    --uri="mongodb://${MONGO_USER}:${MONGO_PASSWORD}@localhost:27017/${MONGO_DB_NAME}" \
    --archive > "$BACKUP_DIR/mongodb.archive" 2>/dev/null || echo "⚠️  MongoDB backup skipped (service not running)"

# Backup PostgreSQL
echo "📦 Backing up PostgreSQL..."
docker-compose exec -T postgres pg_dump \
    -U "${POSTGRES_USER}" "${POSTGRES_DB}" \
    > "$BACKUP_DIR/postgres.sql" 2>/dev/null || echo "⚠️  PostgreSQL backup skipped (service not running)"

# Backup Redis
echo "📦 Backing up Redis..."
docker-compose exec -T redis redis-cli \
    --no-auth-warning -a "${REDIS_PASSWORD}" \
    SAVE > /dev/null 2>&1 || echo "⚠️  Redis backup skipped (service not running)"
docker-compose exec -T redis cat /data/dump.rdb > "$BACKUP_DIR/redis.rdb" 2>/dev/null || true

# Backup media files
echo "📦 Backing up media files..."
if [ -d "./backend/media" ]; then
    tar -czf "$BACKUP_DIR/media.tar.gz" -C ./backend media/
fi

# Backup environment files
echo "📦 Backing up configuration..."
cp .env "$BACKUP_DIR/.env.backup" 2>/dev/null || true
cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml.backup" 2>/dev/null || true

# Create backup info file
cat > "$BACKUP_DIR/backup_info.txt" << EOF
Backup created: $(date)
Hostname: $(hostname)
Docker Compose Version: $(docker-compose version --short)
EOF

# Compress backup
echo "🗜️  Compressing backup..."
tar -czf "$BACKUP_DIR.tar.gz" -C ./backups "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

echo "✅ Backup completed: $BACKUP_DIR.tar.gz"
echo "📊 Backup size: $(du -h $BACKUP_DIR.tar.gz | cut -f1)"

# Clean old backups (keep last 7 days)
echo "🧹 Cleaning old backups..."
find ./backups -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup process completed!"
