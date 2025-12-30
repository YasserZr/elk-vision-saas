"""
Prometheus Metrics URL Configuration
=====================================
"""

from django.urls import path
from .views.metrics_views import (
    MetricsView,
    HealthCheckView,
    ReadinessCheckView,
    LivenessCheckView,
)

urlpatterns = [
    # Prometheus metrics endpoint
    path('metrics/', MetricsView.as_view(), name='prometheus-metrics'),
    
    # Health check endpoints
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('ready/', ReadinessCheckView.as_view(), name='readiness-check'),
    path('live/', LivenessCheckView.as_view(), name='liveness-check'),
]
