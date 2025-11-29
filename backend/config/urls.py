"""
URL configuration for ELK Vision SaaS project.
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Health Check (No versioning)
    path("", include("app.health.urls")),
    # JWT Authentication
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # API v1 URLs
    path("api/v1/users/", include("app.users.urls")),
    path("api/v1/logs/", include("app.logs.urls")),
    path("api/v1/dashboards/", include("app.dashboards.urls")),
    path("api/v1/alerts/", include("app.alerts.urls")),
]
