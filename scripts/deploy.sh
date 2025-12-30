#!/bin/bash

# ELK Vision SaaS - Production Deployment Script

set -e

echo "🚀 Deploying ELK Vision SaaS to Production..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Source environment variables
source .env

# Verify critical environment variables
if [ "$DEBUG" = "True" ]; then
    echo "⚠️  WARNING: DEBUG mode is enabled. This should be False in production!"
    echo "Continue anyway? (y/n)"
    read -r continue
    if [ "$continue" != "y" ]; then
        exit 1
    fi
fi

# Backup databases before deployment
echo "💾 Creating database backups..."
./scripts/backup.sh

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Build production images
echo "🔨 Building production images..."
BUILD_TARGET=production docker-compose build --no-cache

# Stop services gracefully
echo "🛑 Stopping services..."
docker-compose down

# Start services
echo "🎬 Starting services..."
BUILD_TARGET=production docker-compose up -d

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 15

# Run migrations
echo "🗃️ Running database migrations..."
docker-compose exec -T backend python manage.py migrate --noinput

# Collect static files
echo "📦 Collecting static files..."
docker-compose exec -T backend python manage.py collectstatic --noinput

# Clear cache
echo "🧹 Clearing cache..."
docker-compose exec -T backend python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Restart services to ensure clean state
echo "🔄 Restarting services..."
docker-compose restart

# Health checks
echo "🏥 Running health checks..."
sleep 10

# Check backend health
if curl -f http://localhost:8000/api/health/ > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose logs --tail=50 backend
    exit 1
fi

# Check frontend health
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    docker-compose logs --tail=50 frontend
    exit 1
fi

# Display status
echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "📍 Service Status:"
docker-compose ps
echo ""
