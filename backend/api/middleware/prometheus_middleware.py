"""
Django Prometheus Middleware
============================
Middleware for automatic HTTP metrics collection.
"""

import time
import re
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

try:
    from api.metrics import (
        http_requests_total,
        http_request_duration_seconds,
        http_responses_total,
        rate_limit_hits,
        http_errors_total,
        exceptions_total,
    )
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


class PrometheusMetricsMiddleware(MiddlewareMixin):
    """
    Middleware to collect HTTP request metrics for Prometheus.
    
    Automatically tracks:
    - Request count by method, view, and status
    - Request duration by method and view
    - Response status codes
    """
    
    # URL patterns to exclude from metrics
    EXCLUDE_PATHS = [
        r'^/metrics/?$',
        r'^/health/?$',
        r'^/static/',
        r'^/media/',
        r'^/__debug__/',
    ]
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        self.exclude_patterns = [re.compile(p) for p in self.EXCLUDE_PATHS]
        super().__init__(get_response)
    
    def should_exclude(self, path):
        """Check if path should be excluded from metrics."""
        return any(pattern.match(path) for pattern in self.exclude_patterns)
    
    def get_view_name(self, request):
        """Extract view name from request."""
        if hasattr(request, 'resolver_match') and request.resolver_match:
            if request.resolver_match.view_name:
                return request.resolver_match.view_name
            if request.resolver_match.func:
                return request.resolver_match.func.__name__
        return 'unknown'
    
    def process_request(self, request):
        """Record request start time."""
        request._prometheus_start_time = time.time()
    
    def process_response(self, request, response):
        """Record metrics after request processing."""
        if not METRICS_AVAILABLE:
            return response
        
        # Skip excluded paths
        if self.should_exclude(request.path):
            return response
        
        # Calculate duration
        start_time = getattr(request, '_prometheus_start_time', None)
        if start_time:
            duration = time.time() - start_time
        else:
            duration = 0
        
        # Get view name and method
        view_name = self.get_view_name(request)
        method = request.method
        status = str(response.status_code)
        
        # Record metrics
        http_requests_total.labels(
            method=method,
            view=view_name,
            status=status
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            view=view_name
        ).observe(duration)
        
        http_responses_total.labels(
            status=status,
            method=method
        ).inc()
        
        # Track HTTP errors (4xx and 5xx)
        if response.status_code >= 400:
            http_errors_total.labels(
                status_code=status,
                method=method,
                view=view_name
            ).inc()
        
        # Track rate limit hits (429 status)
        if response.status_code == 429:
            user_type = 'authenticated' if request.user.is_authenticated else 'anonymous'
            rate_limit_hits.labels(
                endpoint=view_name,
                user_type=user_type
            ).inc()
        
        return response


class PrometheusExceptionMiddleware(MiddlewareMixin):
    """
    Middleware to track unhandled exceptions.
    """
    
    def process_exception(self, request, exception):
        """Record exception metrics."""
        if not METRICS_AVAILABLE:
            return None
        
        view_name = self.get_view_name(request)
        method = request.method
        exception_type = type(exception).__name__
        
        # Record exception
        exceptions_total.labels(
            exception_type=exception_type,
            view=view_name
        ).inc()
        
        # Record as 500 error
        http_requests_total.labels(
            method=method,
            view=view_name,
            status='500'
        ).inc()
        
        http_responses_total.labels(
            status='500',
            method=method
        ).inc()
        
        http_errors_total.labels(
            status_code='500',
            method=method,
            view=view_name
        ).inc()
        
        return None
    
    def get_view_name(self, request):
        """Extract view name from request."""
        if hasattr(request, 'resolver_match') and request.resolver_match:
            if request.resolver_match.view_name:
                return request.resolver_match.view_name
        return 'unknown'
