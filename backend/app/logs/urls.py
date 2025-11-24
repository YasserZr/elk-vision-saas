from django.urls import path
from . import views
from .views_metadata import (
    LogMetadataListView,
    LogMetadataDetailView,
    LogMetadataStatsView,
    LogMetadataRecentView,
    LogMetadataByTaskView,
    InitializeLogMetadataIndexesView
)

urlpatterns = [
    # Existing routes
    path('search/', views.LogSearchView.as_view(), name='log-search'),
    path('upload/', views.LogUploadView.as_view(), name='log-upload'),
    path('upload/status/<str:task_id>/', views.LogUploadStatusView.as_view(), name='log-upload-status'),
    path('logstash/monitor/', views.LogstashMonitorView.as_view(), name='logstash-monitor'),
    
    # MongoDB metadata routes
    path('metadata/', LogMetadataListView.as_view(), name='log-metadata-list'),
    path('metadata/<str:upload_id>/', LogMetadataDetailView.as_view(), name='log-metadata-detail'),
    path('metadata/task/<str:task_id>/', LogMetadataByTaskView.as_view(), name='log-metadata-by-task'),
    path('metadata/stats/', LogMetadataStatsView.as_view(), name='log-metadata-stats'),
    path('metadata/recent/', LogMetadataRecentView.as_view(), name='log-metadata-recent'),
    
    # Admin routes
    path('admin/initialize-metadata-indexes/', InitializeLogMetadataIndexesView.as_view(), name='initialize-metadata-indexes'),
]
