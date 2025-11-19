"""
URL configuration for ELK Vision SaaS project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # JWT Authentication
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # App URLs
    path('api/users/', include('app.users.urls')),
    path('api/logs/', include('app.logs.urls')),
    path('api/dashboards/', include('app.dashboards.urls')),
    path('api/alerts/', include('app.alerts.urls')),
]
