from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.LogSearchView.as_view(), name='log-search'),
    path('upload/', views.LogUploadView.as_view(), name='log-upload'),
    path('upload/status/<str:task_id>/', views.LogUploadStatusView.as_view(), name='log-upload-status'),
]
