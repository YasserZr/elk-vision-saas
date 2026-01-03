"""
URL configuration for ELK Vision SaaS project.
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView
from app.users.views import CustomTokenObtainPairView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # API Documentation (root path)
    path("", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui-alt"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Admin
    path("admin/", admin.site.urls),
    # Health Check
    path("api/", include("app.health.urls")),
    # JWT Authentication
    path("api/auth/login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # API v1 URLs
    path("api/v1/users/", include("app.users.urls")),
    path("api/v1/logs/", include("app.logs.urls")),
    path("api/v1/dashboards/", include("app.dashboards.urls")),
    path("api/v1/alerts/", include("app.alerts.urls")),
]
