from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
    path('health/ready/', views.ReadinessCheckView.as_view(), name='readiness-check'),
    path('health/live/', views.LivenessCheckView.as_view(), name='liveness-check'),
]
