"""
Django Prometheus Metrics Integration
=====================================
Custom metrics for the ELK Vision SaaS application.
"""

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
from prometheus_client.exposition import generate_latest
from functools import wraps
import time

# ===========================================
# Custom Metrics Registry
# ===========================================

# HTTP Metrics
http_requests_total = Counter(
    'django_http_requests_total',
    'Total HTTP requests',
    ['method', 'view', 'status']
)

http_request_duration_seconds = Histogram(
    'django_http_requests_latency_seconds',
    'HTTP request latency in seconds',
    ['method', 'view'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

http_responses_total = Counter(
    'django_http_responses_total_by_status_total',
    'Total HTTP responses by status code',
    ['status', 'method']
)

# Application Metrics
active_users = Gauge(
    'django_active_users',
    'Number of active users in the last 15 minutes'
)

websocket_connections = Gauge(
    'django_websocket_connections_active',
    'Number of active WebSocket connections',
    ['channel']
)

# Log Processing Metrics
logs_processed_total = Counter(
    'django_logs_processed_total',
    'Total number of logs processed',
    ['source', 'level']
)

log_processing_duration = Histogram(
    'django_log_processing_duration_seconds',
    'Time spent processing logs',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

logs_storage_bytes = Gauge(
    'django_logs_storage_bytes',
    'Total bytes of logs stored',
    ['database']
)

# Alert Metrics
alerts_triggered_total = Counter(
    'django_alerts_triggered_total',
    'Total number of alerts triggered',
    ['severity', 'type']
)

alerts_active = Gauge(
    'django_alerts_active',
    'Number of currently active alerts',
    ['severity']
)

# Celery Task Metrics
celery_tasks_total = Counter(
    'django_celery_tasks_total',
    'Total Celery tasks processed',
    ['task_name', 'status']
)

celery_task_duration = Histogram(
    'django_celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

celery_queue_length = Gauge(
    'celery_queue_length',
    'Number of tasks in Celery queue',
    ['queue']
)

celery_workers_active = Gauge(
    'celery_workers_active',
    'Number of active Celery workers'
)

# Database Metrics
db_query_duration = Histogram(
    'django_db_query_duration_seconds',
    'Database query duration',
    ['operation', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5)
)

db_connections_active = Gauge(
    'django_db_connections_active',
    'Number of active database connections',
    ['database']
)

# File Upload Metrics
file_uploads_total = Counter(
    'django_file_uploads_total',
    'Total number of file uploads',
    ['status', 'file_type']
)

file_upload_size_bytes = Histogram(
    'django_file_upload_size_bytes',
    'Size of uploaded files in bytes',
    ['file_type'],
    buckets=(1024, 10240, 102400, 1048576, 10485760, 104857600, 1073741824)
)

# API Rate Limiting
rate_limit_hits = Counter(
    'django_rate_limit_hits_total',
    'Number of rate limit hits',
    ['endpoint', 'user_type']
)

# Application Info
app_info = Info(
    'django_app',
    'Django application information'
)


# ===========================================
# Decorators for Metrics Collection
# ===========================================

def track_request_metrics(view_name=None):
    """Decorator to track HTTP request metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            name = view_name or func.__name__
            method = request.method
            
            start_time = time.time()
            try:
                response = func(request, *args, **kwargs)
                status = str(response.status_code)
            except Exception as e:
                status = '500'
                raise
            finally:
                duration = time.time() - start_time
                http_requests_total.labels(method=method, view=name, status=status).inc()
                http_request_duration_seconds.labels(method=method, view=name).observe(duration)
                http_responses_total.labels(status=status, method=method).inc()
            
            return response
        return wrapper
    return decorator


def track_celery_task(task_name=None):
    """Decorator to track Celery task metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = task_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                celery_tasks_total.labels(task_name=name, status='success').inc()
                return result
            except Exception as e:
                celery_tasks_total.labels(task_name=name, status='failure').inc()
                raise
            finally:
                duration = time.time() - start_time
                celery_task_duration.labels(task_name=name).observe(duration)
        
        return wrapper
    return decorator


def track_db_query(operation, table):
    """Context manager to track database query metrics."""
    class QueryTracker:
        def __init__(self, operation, table):
            self.operation = operation
            self.table = table
            self.start_time = None
        
        def __enter__(self):
            self.start_time = time.time()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            db_query_duration.labels(operation=self.operation, table=self.table).observe(duration)
    
    return QueryTracker(operation, table)


# ===========================================
# Utility Functions
# ===========================================

def increment_log_processed(source: str, level: str):
    """Increment log processed counter."""
    logs_processed_total.labels(source=source, level=level).inc()


def increment_alert_triggered(severity: str, alert_type: str):
    """Increment alert triggered counter."""
    alerts_triggered_total.labels(severity=severity, type=alert_type).inc()


def set_active_alerts(severity: str, count: int):
    """Set the number of active alerts."""
    alerts_active.labels(severity=severity).set(count)


def set_websocket_connections(channel: str, count: int):
    """Set the number of WebSocket connections."""
    websocket_connections.labels(channel=channel).set(count)


def track_file_upload(status: str, file_type: str, size_bytes: int):
    """Track file upload metrics."""
    file_uploads_total.labels(status=status, file_type=file_type).inc()
    file_upload_size_bytes.labels(file_type=file_type).observe(size_bytes)


def set_celery_queue_length(queue: str, length: int):
    """Set Celery queue length."""
    celery_queue_length.labels(queue=queue).set(length)


def set_celery_workers(count: int):
    """Set active Celery workers count."""
    celery_workers_active.set(count)


def set_app_info(version: str, environment: str, debug: bool):
    """Set application info."""
    app_info.info({
        'version': version,
        'environment': environment,
        'debug': str(debug).lower()
    })


# ===========================================
# Metrics Export
# ===========================================

def get_metrics():
    """Generate Prometheus metrics output."""
    return generate_latest()
