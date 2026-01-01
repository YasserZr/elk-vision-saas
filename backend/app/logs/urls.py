from django.urls import path

from . import views
from .views_metadata import (
    InitializeLogMetadataIndexesView,
    LogMetadataByTaskView,
    LogMetadataDetailView,
    LogMetadataListView,
    LogMetadataRecentView,
    LogMetadataStatsView,
)
from .views_search_history import (
    SearchHistoryDetailView,
    SearchHistoryListView,
)

urlpatterns = [
    # Existing routes
    path("search/", views.LogSearchView.as_view(), name="log-search"),
    path("upload/", views.LogUploadView.as_view(), name="log-upload"),
    path(
        "upload/status/<str:task_id>/",
        views.LogUploadStatusView.as_view(),
        name="log-upload-status",
    ),
    path(
        "logstash/monitor/",
        views.LogstashMonitorView.as_view(),
        name="logstash-monitor",
    ),
    # Search history routes
    path("search/history/", SearchHistoryListView.as_view(), name="search-history-list"),
    path(
        "search/history/<str:search_id>/",
        SearchHistoryDetailView.as_view(),
        name="search-history-detail",
    ),
    # MongoDB metadata routes
    path("metadata/", LogMetadataListView.as_view(), name="log-metadata-list"),
    # Static routes MUST come before dynamic <str:upload_id> route
    path("metadata/stats/", LogMetadataStatsView.as_view(), name="log-metadata-stats"),
    path(
        "metadata/recent/", LogMetadataRecentView.as_view(), name="log-metadata-recent"
    ),
    path(
        "metadata/task/<str:task_id>/",
        LogMetadataByTaskView.as_view(),
        name="log-metadata-by-task",
    ),
    # Dynamic route must be LAST to avoid matching "stats", "recent", "task" as upload_id
    path(
        "metadata/<str:upload_id>/",
        LogMetadataDetailView.as_view(),
        name="log-metadata-detail",
    ),
    # Admin routes
    path(
        "admin/initialize-metadata-indexes/",
        InitializeLogMetadataIndexesView.as_view(),
        name="initialize-metadata-indexes",
    ),
]
