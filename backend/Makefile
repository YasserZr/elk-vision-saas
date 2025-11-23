# Makefile for ELK Vision SaaS Backend

.PHONY: help install test lint format run migrate shell clean docker-build docker-run

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt

test:  ## Run tests
	pytest --cov=app --cov-report=term-missing

test-verbose:  ## Run tests with verbose output
	pytest -v --cov=app --cov-report=html

lint:  ## Run linters
	flake8 app config
	black --check app config
	isort --check-only app config

format:  ## Format code
	black app config
	isort app config

run:  ## Run development server
	python manage.py runserver

migrate:  ## Run database migrations
	python manage.py migrate

makemigrations:  ## Create new migrations
	python manage.py makemigrations

shell:  ## Open Django shell
	python manage.py shell

superuser:  ## Create superuser
	python manage.py createsuperuser

collectstatic:  ## Collect static files
	python manage.py collectstatic --noinput

clean:  ## Clean up Python artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/

docker-build:  ## Build Docker image
	docker build -t elk-backend .

docker-run:  ## Run Docker container
	docker run -p 8000:8000 elk-backend

check-health:  ## Check application health
	curl http://localhost:8000/health/

check-ready:  ## Check application readiness
	curl http://localhost:8000/health/ready/

check-live:  ## Check application liveness
	curl http://localhost:8000/health/live/
