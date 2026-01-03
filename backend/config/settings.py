"""
Django settings for ELK Vision SaaS project.
"""

import os
from pathlib import Path

from decouple import config

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-this-in-production")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

# Application definition
INSTALLED_APPS = [
    "daphne",  # Must be first for WebSocket support
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "channels",
    "drf_spectacular",
    # Local apps
    "app.users",
    "app.logs",
    "app.dashboards",
    "app.alerts",
    "app.health",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

ASGI_APPLICATION = "config.asgi.application"

# Channel Layers (Redis backend for WebSocket communication)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                {
                    "host": config("REDIS_HOST", default="redis"),
                    "port": int(config("REDIS_PORT", default=6379)),
                    "password": config("REDIS_PASSWORD", default=""),
                }
            ],
        },
    },
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database - SQLite for Django internal tables (auth, sessions, admin)
# MongoDB will be used directly via pymongo for application data
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# MongoDB Configuration (accessed via pymongo directly, not through Django ORM)
MONGODB = {
    "host": config("MONGO_HOST", default="mongodb"),
    "port": int(config("MONGO_PORT", default=27017)),
    "database": config("MONGO_DB_NAME", default="elk_vision"),
    "username": config("MONGO_USER", default="admin"),
    "password": config("MONGO_PASSWORD", default="password"),
    "authSource": "admin",
}

# Elasticsearch Configuration
ELASTICSEARCH_SCHEME = config("ELASTICSEARCH_SCHEME", default="http")
ELASTICSEARCH_HOST = config("ELASTICSEARCH_HOST", default="elasticsearch:9200")

# Build full Elasticsearch URL with scheme
ES_HOST_URL = f"{ELASTICSEARCH_SCHEME}://{ELASTICSEARCH_HOST}"

ELASTICSEARCH_DSL = {
    "default": {
        "hosts": [ES_HOST_URL],
        "http_auth": (
            config("ELASTICSEARCH_USER", default="elastic"),
            config("ELASTICSEARCH_PASSWORD", default="changeme"),
        ),
    },
}

# Logstash Configuration
LOGSTASH_HOST = config("LOGSTASH_HOST", default="logstash")
LOGSTASH_PORT = config("LOGSTASH_PORT", default=5000, cast=int)
LOGSTASH_PROTOCOL = config("LOGSTASH_PROTOCOL", default="tcp")  # tcp or udp
LOGSTASH_TIMEOUT = config("LOGSTASH_TIMEOUT", default=5, cast=int)
LOGSTASH_MAX_RETRIES = config("LOGSTASH_MAX_RETRIES", default=3, cast=int)
LOGSTASH_RETRY_DELAY = config("LOGSTASH_RETRY_DELAY", default=2, cast=int)
LOGSTASH_BATCH_SIZE = config("LOGSTASH_BATCH_SIZE", default=100, cast=int)
USE_LOGSTASH = config(
    "USE_LOGSTASH", default=True, cast=bool
)  # True: Logstash, False: Direct ES

# Redis Configuration
REDIS_HOST = config("REDIS_HOST", default="redis")
REDIS_PORT = int(config("REDIS_PORT", default=6379))
REDIS_PASSWORD = config("REDIS_PASSWORD", default="")

# Build Redis URL with password if provided
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# Celery Configuration
CELERY_BROKER_URL = f"{REDIS_URL}/0"
CELERY_RESULT_BACKEND = f"{REDIS_URL}/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# API Documentation Settings
SPECTACULAR_SETTINGS = {
    "TITLE": "ELK Vision SaaS API",
    "DESCRIPTION": "Centralized log management and monitoring platform with Elasticsearch, multi-tenant isolation, and real-time WebSocket notifications",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/v1/",
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

# CORS Settings
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS", default="http://localhost:3000,http://127.0.0.1:3000"
).split(",")
CORS_ALLOW_CREDENTIALS = True

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging Configuration (12-Factor: Logs as event streams)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "json": {
            "format": '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose" if DEBUG else "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": config("LOG_LEVEL", default="INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": config("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        "app": {
            "handlers": ["console"],
            "level": config("APP_LOG_LEVEL", default="DEBUG"),
            "propagate": False,
        },
    },
}

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

# Production Security (enable when not in DEBUG)
if not DEBUG:
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# API Versioning
API_VERSION = "v1"

# Health Check Settings
HEALTH_CHECK_TIMEOUT = config("HEALTH_CHECK_TIMEOUT", default=5, cast=int)
