from django.urls import path

from . import views
from .views_profile import (InitializeIndexesView, TenantUsersView,
                            UserProfileAdminView, UserProfileCreateView,
                            UserProfileView, UserQuotaView)

urlpatterns = [
    # Existing routes
    path("register/", views.RegisterView.as_view(), name="user-register"),
    path(
        "change-password/", views.ChangePasswordView.as_view(), name="change-password"
    ),
    # MongoDB profile routes
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path(
        "profile/create/", UserProfileCreateView.as_view(), name="user-profile-create"
    ),
    path("profile/quota/", UserQuotaView.as_view(), name="user-quota"),
    path("tenant/users/", TenantUsersView.as_view(), name="tenant-users"),
    # Admin routes
    path(
        "admin/profile/<int:user_id>/",
        UserProfileAdminView.as_view(),
        name="admin-user-profile",
    ),
    path(
        "admin/initialize-indexes/",
        InitializeIndexesView.as_view(),
        name="initialize-indexes",
    ),
]
