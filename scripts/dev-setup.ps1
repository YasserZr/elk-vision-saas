# PowerShell script for Windows - Development Setup

Write-Host "🚀 Starting ELK Vision SaaS Development Environment..." -ForegroundColor Green

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is installed
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Desktop with Compose." -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✅ .env file created. Please review and update the values." -ForegroundColor Green
}

# Create necessary directories
Write-Host "📁 Creating necessary directories..." -ForegroundColor Yellow
$directories = @(
    "backend\staticfiles",
    "backend\media",
    "backend\logs",
    "frontend\.next",
    "certbot\conf",
    "certbot\www"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Pull latest images
Write-Host "📥 Pulling Docker images..." -ForegroundColor Yellow
docker-compose pull

# Build services
Write-Host "🔨 Building services..." -ForegroundColor Yellow
$env:BUILD_TARGET = "development"
docker-compose build

# Start services
Write-Host "🎬 Starting services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Run migrations
Write-Host "🗃️ Running database migrations..." -ForegroundColor Yellow
docker-compose exec -T backend python manage.py migrate

# Create superuser (optional)
Write-Host ""
$createSuperuser = Read-Host "👤 Do you want to create a Django superuser? (y/n)"
if ($createSuperuser -eq "y") {
    docker-compose exec backend python manage.py createsuperuser
}

# Collect static files
Write-Host "📦 Collecting static files..." -ForegroundColor Yellow
docker-compose exec -T backend python manage.py collectstatic --noinput

# Display service URLs
Write-Host ""
Write-Host "✅ Development environment is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Service URLs:" -ForegroundColor Cyan
Write-Host "   Frontend:     http://localhost:3000"
Write-Host "   Backend API:  http://localhost:8000"
Write-Host "   Django Admin: http://localhost:8000/admin"
Write-Host "   Kibana:       http://localhost:5601"
Write-Host "   Flower:       http://localhost:5555"
Write-Host ""
Write-Host "📊 View logs:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f"
Write-Host ""
Write-Host "🛑 Stop services:" -ForegroundColor Cyan
Write-Host "   docker-compose down"
Write-Host ""
