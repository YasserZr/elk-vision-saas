"""
WebSocket routing configuration for real-time notifications.
"""

from django.urls import re_path
from api.consumers import NotificationConsumer, LogStreamConsumer

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
    re_path(r'ws/logs/stream/$', LogStreamConsumer.as_asgi()),
]
