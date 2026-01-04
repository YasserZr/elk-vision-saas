"""
Prometheus Metrics Views
========================
Django views for exposing Prometheus metrics.
"""

from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from prometheus_client.core import CollectorRegistry

from api.metrics import (
    active_users,
    websocket_connections,
    celery_queue_length,
    celery_workers_active,
    db_connections_active,
    logs_storage_bytes,
    alerts_active,
    mongodb_connections_active,
    set_app_info,
)


@method_decorator(csrf_exempt, name='dispatch')
class MetricsView(View):
    """
    Prometheus metrics endpoint.
    
    Exposes all application metrics in Prometheus format.
    Should be protected in production (IP whitelist or authentication).
    """
    
    def get(self, request):
        """Return Prometheus metrics."""
        # Update dynamic metrics before export
        self._update_dynamic_metrics()
        
        # Generate metrics
        metrics = generate_latest(REGISTRY)
        
        return HttpResponse(
            metrics,
            content_type=CONTENT_TYPE_LATEST
        )
    
    def _update_dynamic_metrics(self):
        """Update metrics that need to be calculated on-demand."""
        try:
            # Update active users count
            from django.contrib.auth import get_user_model
            from django.utils import timezone
            from datetime import timedelta
            
            User = get_user_model()
            fifteen_minutes_ago = timezone.now() - timedelta(minutes=15)
            active_count = User.objects.filter(
                last_login__gte=fifteen_minutes_ago
            ).count()
            active_users.set(active_count)
        except Exception:
            pass
        
        try:
            # Update Celery queue lengths
            from celery import current_app
            
            inspect = current_app.control.inspect()
            
            # Get queue lengths
            reserved = inspect.reserved() or {}
            for worker, tasks in reserved.items():
                celery_queue_length.labels(queue='default').set(len(tasks))
            
            # Get active workers
            active = inspect.active() or {}
            celery_workers_active.set(len(active))
        except Exception:
            pass
        
        try:
            # Update database connections
            from django.db import connections
            
            for alias in connections:
                conn = connections[alias]
                if conn.connection:
                    db_connections_active.labels(database=alias).set(1)
                else:
                    db_connections_active.labels(database=alias).set(0)
        except Exception:
            pass
        
        try:
            # Update MongoDB connection count
            from app.core.mongodb import get_mongo_client
            
            client = get_mongo_client()
            # Get server status to check connection
            server_status = client.admin.command('serverStatus')
            current_connections = server_status.get('connections', {}).get('current', 0)
            mongodb_connections_active.set(current_connections)
        except Exception:
            pass
        
        try:
            # Update alert counts
            from apps.alerts.models import Alert
            
            for severity in ['critical', 'warning', 'info']:
                count = Alert.objects.filter(
                    severity=severity,
                    is_active=True
                ).count()
                alerts_active.labels(severity=severity).set(count)
        except Exception:
            pass
        
        try:
            # Set application info
            from django.conf import settings
            import os
            
            set_app_info(
                version=getattr(settings, 'APP_VERSION', '1.0.0'),
                environment=os.getenv('ENVIRONMENT', 'development'),
                debug=settings.DEBUG
            )
        except Exception:
            pass


class HealthCheckView(View):
    """
    Health check endpoint for monitoring.
    
    Returns 200 if the application is healthy.
    Used by Prometheus blackbox exporter and load balancers.
    """
    
    def get(self, request):
        """Return health status."""
        health_status = self._check_health()
        
        if health_status['healthy']:
            return HttpResponse(
                'healthy',
                content_type='text/plain',
                status=200
            )
        else:
            return HttpResponse(
                f"unhealthy: {health_status['reason']}",
                content_type='text/plain',
                status=503
            )
    
    def _check_health(self):
        """Perform health checks."""
        checks = []
        
        # Database check
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            checks.append(('database', True, None))
        except Exception as e:
            checks.append(('database', False, str(e)))
        
        # Redis check
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                checks.append(('redis', True, None))
            else:
                checks.append(('redis', False, 'Cache read failed'))
        except Exception as e:
            checks.append(('redis', False, str(e)))
        
        # Check results
        failed = [c for c in checks if not c[1]]
        
        if failed:
            reasons = [f"{c[0]}: {c[2]}" for c in failed]
            return {
                'healthy': False,
                'reason': '; '.join(reasons),
                'checks': checks
            }
        
        return {
            'healthy': True,
            'reason': None,
            'checks': checks
        }


class ReadinessCheckView(View):
    """
    Readiness check endpoint.
    
    Returns 200 if the application is ready to receive traffic.
    Used by Kubernetes readiness probes.
    """
    
    def get(self, request):
        """Return readiness status."""
        # Check if all dependencies are ready
        ready = self._check_readiness()
        
        if ready['ready']:
            return HttpResponse(
                'ready',
                content_type='text/plain',
                status=200
            )
        else:
            return HttpResponse(
                f"not ready: {ready['reason']}",
                content_type='text/plain',
                status=503
            )
    
    def _check_readiness(self):
        """Check if application is ready."""
        # Add your readiness checks here
        # For example: database migrations complete, cache warmed, etc.
        
        try:
            # Check database migrations
            from django.db import connection
            from django.db.migrations.executor import MigrationExecutor
            
            executor = MigrationExecutor(connection)
            targets = executor.loader.graph.leaf_nodes()
            
            # Check if all migrations are applied
            plan = executor.migration_plan(targets)
            if plan:
                return {
                    'ready': False,
                    'reason': 'Pending migrations'
                }
        except Exception as e:
            return {
                'ready': False,
                'reason': f'Migration check failed: {str(e)}'
            }
        
        return {
            'ready': True,
            'reason': None
        }


class LivenessCheckView(View):
    """
    Liveness check endpoint.
    
    Returns 200 if the application is running.
    Used by Kubernetes liveness probes.
    """
    
    def get(self, request):
        """Return liveness status."""
        return HttpResponse(
            'alive',
            content_type='text/plain',
            status=200
        )
