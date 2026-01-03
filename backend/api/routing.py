"""
WebSocket routing configuration for real-time notifications and streaming.
"""

from django.urls import re_path
from api.consumers import NotificationConsumer, LogStreamConsumer
from api.consumers_metrics import MetricsConsumer

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
    re_path(r'ws/logs/stream/$', LogStreamConsumer.as_asgi()),
    re_path(r'ws/metrics/$', MetricsConsumer.as_asgi()),
]
