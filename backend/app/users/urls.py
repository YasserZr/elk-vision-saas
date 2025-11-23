from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('register/', views.RegisterView.as_view(), name='user-register'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
]
