#!/bin/bash

# ELK Vision SaaS - Development Setup Script

set -e

echo "🚀 Starting ELK Vision SaaS Development Environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please review and update the values."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/staticfiles
mkdir -p backend/media
mkdir -p backend/logs
mkdir -p frontend/.next
mkdir -p certbot/conf
mkdir -p certbot/www

# Set permissions
echo "🔐 Setting permissions..."
chmod +x scripts/*.sh 2>/dev/null || true

# Pull latest images
echo "📥 Pulling Docker images..."
docker-compose pull

# Build services
echo "🔨 Building services..."
BUILD_TARGET=development docker-compose build

# Start services
echo "🎬 Starting services..."
BUILD_TARGET=development docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run migrations
echo "🗃️ Running database migrations..."
docker-compose exec -T backend python manage.py migrate

# Create superuser (optional)
echo ""
echo "👤 Do you want to create a Django superuser? (y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ]; then
    docker-compose exec backend python manage.py createsuperuser
fi

# Collect static files
echo "📦 Collecting static files..."
docker-compose exec -T backend python manage.py collectstatic --noinput

# Display service URLs
echo ""
echo "✅ Development environment is ready!"
echo ""
echo "📍 Service URLs:"
echo "   Frontend:     http://localhost:3000"
echo "   Backend API:  http://localhost:8000"
echo "   Django Admin: http://localhost:8000/admin"
echo "   Kibana:       http://localhost:5601"
echo "   Flower:       http://localhost:5555"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
